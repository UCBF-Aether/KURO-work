#!/usr/bin/env python3
"""fat.py — FAT TASTE, a bottled fly sense.

Fatty-acid taste — the fly's detection of medium-chain fats via Ir56d GRNs —
computed live from the fly-brain subgraph collection. This bottle is two
half-chains in one module, and they are NOT the same kind of knowledge.

PROVENANCE SPLIT (read this before trusting any number):
- BRISTLE half (subgraphs/fat_lit.json, hop 0 = bristle Ir56d GRN FBbt_00048015):
  the hop-0->hop-1 edges are LITERATURE-HYPOTHESIS, not measured wiring.
  Tauber et al. 2017 (PLOS Genet 13:e1007059) showed IR56d neurons are a
  subset of sweet-sensing Gr64f GRNs whose posterior SEZ projections overlap
  the sweet circuit; Brown et al. 2021 (eLife 67878) adds the anatomical
  context. The prediction is that they contact the same named second-order
  SEZ interneurons (zorro/clavicle/FMIn/fuchs/G2N-1/billiards). NO individual
  Ir56d->interneuron synapse is measured anywhere. This half is a publishable
  testable prediction: a run of this bottle says "IF the hypothesis holds,
  this is what the fat signal would do," never "this is wired."
- PEG half (subgraphs/fat_peg.json, hop 0 = general peg GRN class
  FBbt_00048028): ALL edges are REAL FlyWire v783 API rows. The Ir56d-peg
  E409 neurons are an UNMARKED SUBSET of this class — no API marker separates
  them from other peg GRNs, so the peg half is the whole peg population, not
  Ir56d-peg alone. Three anterior-SEZ candidates (hyacinth/CB0011/CB3720)
  carry a LITERATURE-CONSTRAINT flag (Tauber 2017: peg->anterior SEZ); that
  flag constrains the candidate pool, it does not name Ir56d-peg wiring.

IRREDUCIBLE REMAINDER: Ir56d-peg-subset attribution (which peg synapses
belong to the fat-sensing E409 neurons) is unresolvable with current data —
no API marker, no paper names the peg postsynaptic partners. It is documented,
not faked.

HONESTY CONTRACT (non-negotiable):
- [REAL]    Peg-half nodes/edges = ../subgraphs/fat_peg.json (FlyWire v783).
            Bristle-half hop-1->hop-2 edges = real FlyWire v783 rows (via
            sugar_forward.json). No neuron or synapse is invented here.
- [HYPOTHESIS] Bristle-half hop-0->hop-1 edges = LITERATURE-HYPOTHESIS
            (Tauber 2017; Brown 2021), per-edge citations live in the JSON.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] Valence +0.30 (fatty reward) and arousal gain 0.50 are MY design
            choices; readout hops (bristle: hop 2, peg: hop 1) are the deepest
            hop above threshold at full injection on each half, measured live
            before choosing; the "both" half sums the two half-activations.
- [FICTION] Any narrative gloss is fiction, not a claim about experience.

Usage:
    from fat import Fat
    s = Fat()
    s.sense(0.8, half="peg")     # real path
    s.sense(0.8, half="bristle") # hypothesis path
    s.sense(0.8, half="both")    # sum
    s.tick(1.0); s.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

VALENCE_SIGN = 0.3    # [MODELED] fat is appetitive — fatty reward
AROUSAL_GAIN = 0.5    # [MODELED]

# [MODELED] readout hop per half = deepest hop above threshold at full
# injection, measured live (2026-10-14): bristle hop2=0.2695, peg hop1=0.3482.
BRISTLE_READOUT_HOP = 2
PEG_READOUT_HOP = 1

_DIR = os.path.dirname(os.path.abspath(__file__))
BRISTLE_GRAPH = os.path.join(_DIR, "..", "subgraphs", "fat_lit.json")
PEG_GRAPH = os.path.join(_DIR, "..", "subgraphs", "fat_peg.json")


def _load(path, first_wins=True):
    """[REAL] Load a flysim-style subgraph.

    first_wins: fat_peg.json lists the shared SEZ/gnathal nodes at BOTH hop 1
    and hop 2 (builder artifact). Keeping the FIRST occurrence is the honest
    read — they are hop-1 partners of the peg class.
    """
    with open(path) as f:
        graph = json.load(f)
    nodes = {}
    for n in graph["nodes"]:
        if n["id"] not in nodes or not first_wins:
            nodes[n["id"]] = n
    out_sum = {}
    for e in graph["edges"]:
        out_sum[e["pre"]] = out_sum.get(e["pre"], 0.0) + e["weight"]
    norm = []
    for e in graph["edges"]:
        s = out_sum[e["pre"]]
        norm.append((e["pre"], e["post"],
                     e["weight"] / s if s > 0 else 0.0))
    inject = [n["id"] for n in nodes.values() if n.get("hop", 0) == 0]
    return nodes, norm, inject


def _cascade(nodes, norm, inject, injection):
    """[MODEL] Port of flysim.run(): inject at hop 0, spread 4 steps."""
    act = {nid: 0.0 for nid in nodes}
    for nid in inject:
        act[nid] = injection
    snaps = [{nid: a for nid, a in act.items() if a >= THRESHOLD}]
    for _ in range(STEPS):
        incoming = {}
        fired = {nid for nid, a in act.items() if a >= THRESHOLD}
        for pre, post, w in norm:
            if pre in fired:
                incoming[post] = incoming.get(post, 0.0) + act[pre] * w
        act = {nid: incoming.get(nid, 0.0) for nid in nodes}
        snaps.append({nid: a for nid, a in act.items()
                       if a >= THRESHOLD})
    return snaps


def _readout(nodes, snaps, hop):
    """[REAL/TOY] Max activation over readout-hop nodes, all steps."""
    peak = 0.0
    for snap in snaps:
        for nid, a in snap.items():
            if nodes[nid].get("hop", 0) == hop and a > peak:
                peak = a
    return peak


class Fat:
    """A bottled fatty-acid taste — two half-chains, one honest module.

    half="bristle": Ir56d bristle GRN -> hypothesized sweet second-order
        interneurons (zorro/clavicle/FMIn/fuchs/G2N-1/billiards) -> SEZ
        back-end. PROVENANCE: LITERATURE-HYPOTHESIS (testable prediction).
    half="peg": general taste-peg GRN class -> real SEZ interneurons incl.
        the anterior candidates. PROVENANCE: REAL wiring of the whole peg
        class (Ir56d-peg subset unmarked — irreducible remainder).
    half="both": linear sum of the two halves (MODELED).
    """

    PROVENANCE = {
        "bristle": ("LITERATURE-HYPOTHESIS — Tauber et al. 2017 PLOS Genet "
                    "13:e1007059; Brown et al. 2021 eLife 67878. Hop-0->hop-1 "
                    "edges are a testable prediction, not measured wiring."),
        "peg": ("REAL — FlyWire v783 class-level rows (whole peg class "
                "FBbt_00048028; Ir56d-peg E409 subset unmarked). Anterior "
                "candidates carry LITERATURE-CONSTRAINT flags."),
    }

    def __init__(self):
        self._b_nodes, self._b_norm, self._b_inject = _load(BRISTLE_GRAPH)
        self._p_nodes, self._p_norm, self._p_inject = _load(PEG_GRAPH)
        self._activation = 0.0
        self._last_intensity = 0.0
        self._last_half = "both"

    def _half_activation(self, half, intensity):
        if half == "bristle":
            snaps = _cascade(self._b_nodes, self._b_norm,
                             self._b_inject, intensity)
            return _readout(self._b_nodes, snaps, BRISTLE_READOUT_HOP)
        snaps = _cascade(self._p_nodes, self._p_norm,
                         self._p_inject, intensity)
        return _readout(self._p_nodes, snaps, PEG_READOUT_HOP)

    def sense(self, intensity=0.5, half="both"):
        """[MODELED] Stimulate fat taste at 0..1 intensity.

        half selects "bristle" (hypothesis path), "peg" (real path), or
        "both" (their sum). Returns activation, valence_delta (+0.30 x
        activation — fatty reward, MODELED), arousal_delta (0.50 x
        activation) and the half name. Below the model's threshold cliff the
        cascade stays silent and all read 0.0 — honest model behavior.
        """
        half = (half or "both").lower()
        if half not in ("bristle", "peg", "both"):
            raise ValueError("half must be 'bristle', 'peg', or 'both'")
        intensity = min(1.0, max(0.0, intensity))
        self._last_intensity = intensity
        self._last_half = half
        if half == "both":
            # [MODELED] the two halves are independent populations; the
            # combined signal is their linear sum.
            self._activation = (self._half_activation("bristle", intensity)
                                + self._half_activation("peg", intensity))
        else:
            self._activation = self._half_activation(half, intensity)
        return {
            "activation": round(self._activation, 4),
            "valence_delta": round(VALENCE_SIGN * self._activation, 4),
            "arousal_delta": round(AROUSAL_GAIN * self._activation, 4),
            "half": half,
        }

    def tick(self, dt):
        """[MODELED] Decay the activation by dt seconds. Returns new level."""
        self._activation = max(0.0, self._activation - 0.2 * dt)
        return round(self._activation, 4)

    def state(self):
        """Current sense state, with the provenance split attached."""
        return {
            "activation": round(self._activation, 4),
            "valence_sign": VALENCE_SIGN,
            "arousal_gain": AROUSAL_GAIN,
            "bristle_readout_hop": BRISTLE_READOUT_HOP,
            "peg_readout_hop": PEG_READOUT_HOP,
            "last_intensity": self._last_intensity,
            "last_half": self._last_half,
            "provenance": self.PROVENANCE,
        }
