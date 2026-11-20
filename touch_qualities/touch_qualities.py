#!/usr/bin/env python3
"""touch_qualities.py — TOUCH QUALITIES, a bottled fly sense.

Campaniform + bristle mechanosensation — computed live from REAL
Drosophila connectome wiring plus LITERATURE-HYPOTHESIS bristle pathways.

HONESTY CONTRACT (non-negotiable):
- [REAL]    The campaniform half: 3 measured edges from
            ../subgraphs/touch_qualities_lit.json — campaniform sensory
            classes -> b1 wing motor neuron (tw=3572/1818/1754, resolved by
            UpstreamClassConnectivity of b1 on FlyWire FAFB v783 via the
            VFBquery API). One extra edge in the file carries provenance
            LITERATURE-CONFIRMED (independent eLife 2026 FANC EM
            confirmation of wing campaniform -> b1): it is the SAME synapse
            set, never double-counted — this module EXCLUDES it from the
            cascade normalization. No neuron, synapse, or connection is
            invented here.
- [LITERATURE-HYPOTHESIS] The bristle half: bristle BMN -> Mago-no-Te
            (MGT) grooming command and wing bristle -> CTN defensive
            neuron, each with its paper citation, placeholder weight 1.
            MGT and CTN have NO FBbt classes (too new for the ontology);
            the API holds zero rows for bristle downstream in any reachable
            form (GAPS.md section 6/6b). These edges are the literature's
            best current guess, run through the same model dynamics.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] Valence 0.00 (touch quality is informational), arousal gain
            0.30, the quality selector, and the readout layers are MY
            design choices. The fly never saw your inputs.
- [FICTION] Any narrative gloss ("the wing stiffens") is fiction.

Usage:
    from touch_qualities import TouchQualities
    q = TouchQualities()
    q.sense(1.0, quality="campaniform")  # -> {"activation": ..., "valence_delta": ..., ...}
    q.motor_drive()   # activation at the b1 motor neuron (reflex readout)
    q.tick(1.0)
    q.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

VALENCE_SIGN = 0.0   # [MODELED] touch quality is informational, not valenced
AROUSAL_GAIN = 0.3   # [MODELED]
B1_ID = "FBbt_00004066"  # [REAL] b1 motor neuron (wing basalar muscle b1)

CAMPANIFORM_IDS = [   # [REAL] hop-0 campaniform sensory classes
    "FBbt_00048057",  # sensory neuron of campaniform sensillum (tw 3572)
    "FBbt_00048279",  # sensory neuron of wing campaniform sensillum (tw 1818)
    "FBbt_00048296",  # sensory neuron of haltere campaniform sensillum (tw 1754)
]
BRISTLE_IDS = [       # [REAL node, LITERATURE-HYPOTHESIS edges] hop-0 bristle classes
    "FBbt_00048508",  # bristle mechanosensory neuron -> MGT (hypothesis)
    "FBbt_00048273",  # sensory neuron of wing bristle -> CTN (hypothesis)
]
BRISTLE_READOUT_IDS = ["MGT_literature", "CTN_literature"]  # [LITERATURE-HYPOTHESIS]

DEFAULT_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "subgraphs", "touch_qualities_lit.json")


class TouchQualities:
    """Bottled touch qualities — campaniform + bristle mechanosensation.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON. Defaults to the bottled
        ../subgraphs/touch_qualities_lit.json.
    """

    def __init__(self, graph_path=None):
        self._graph_path = graph_path or DEFAULT_GRAPH
        with open(self._graph_path) as f:
            graph = json.load(f)
        # [REAL+HYPOTHESIS] nodes straight from the file; never invented.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._prov = {n["id"]: n.get("provenance") for n in graph["nodes"]}
        out_sum = {}
        self._norm = []
        for e in graph["edges"]:
            if e.get("provenance") == "LITERATURE-CONFIRMED":
                # [REAL] Independent EM confirmation of an already-counted
                # edge — same synapse set, never double-counted.
                continue
            out_sum[e["pre"]] = out_sum.get(e["pre"], 0.0) + e["weight"]
        for e in graph["edges"]:
            if e.get("provenance") == "LITERATURE-CONFIRMED":
                continue
            s = out_sum[e["pre"]]
            self._norm.append((e["pre"], e["post"],
                               e["weight"] / s if s > 0 else 0.0))
        self.source = graph.get("source", "VFBquery/FlyWire FAFB v783 + literature")
        self._activation = 0.0
        self._last_intensity = 0.0
        self._last_quality = "campaniform"
        self._snaps = []

    def _cascade(self, injection, inject_ids):
        """[MODEL] Port of flysim.run(): inject at the selected hop-0 nodes,
        spread 4 steps."""
        act = {nid: 0.0 for nid in self._nodes}
        for nid in inject_ids:
            act[nid] = injection
        snaps = [{nid: a for nid, a in act.items() if a >= THRESHOLD}]
        for _ in range(STEPS):
            incoming = {}
            fired = {nid for nid, a in act.items() if a >= THRESHOLD}
            for pre, post, w in self._norm:
                if pre in fired:
                    incoming[post] = incoming.get(post, 0.0) + act[pre] * w
            act = {nid: incoming.get(nid, 0.0) for nid in self._nodes}
            snaps.append({nid: a for nid, a in act.items()
                           if a >= THRESHOLD})
        return snaps

    def _readout(self, snaps, readout_ids):
        """[REAL/TOY] Max activation over the readout nodes, all steps."""
        peak = 0.0
        for snap in snaps:
            for nid in readout_ids:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    def sense(self, intensity=0.5, quality="campaniform"):
        """[MODELED] Stimulate at 0..1 intensity, selecting the quality.

        quality: "campaniform" (strain/vibration -> b1 motor neuron, REAL
        wiring), "bristle" (touch -> MGT/CTN, LITERATURE-HYPOTHESIS edges),
        or "both" (all five sensory classes; activation = campaniform peak
        at b1 PLUS bristle peak at MGT/CTN — a sum across two disjoint
        pathways).

        Returns activation (thresholded readout max), valence_delta
        (0.00 x activation — informational) and arousal_delta (0.30 x
        activation). Below the model's threshold cliff the cascade stays
        silent and all three read 0.0 — honest model behavior, documented
        in the README.
        """
        if quality not in ("campaniform", "bristle", "both"):
            raise ValueError("quality must be 'campaniform', 'bristle' or 'both'")
        intensity = min(1.0, max(0.0, intensity))
        self._last_intensity = intensity
        self._last_quality = quality
        if quality == "campaniform":
            inject, readout = CAMPANIFORM_IDS, [B1_ID]
        elif quality == "bristle":
            inject, readout = BRISTLE_IDS, BRISTLE_READOUT_IDS
        else:
            # [MODELED] The two pathways are disjoint (different hop-1
            # nodes), so "both" sums the per-pathway peaks — a real sum
            # across pathways, not a max.
            inject = CAMPANIFORM_IDS + BRISTLE_IDS
            readout = None  # handled below: sum of the two path peaks
        self._snaps = self._cascade(intensity, inject)
        if readout is None:
            self._activation = (self._readout(self._snaps, [B1_ID])
                                + self._readout(self._snaps, BRISTLE_READOUT_IDS))
        else:
            self._activation = self._readout(self._snaps, readout)
        return {
            "activation": round(self._activation, 4),
            "valence_delta": round(VALENCE_SIGN * self._activation, 4),
            "arousal_delta": round(AROUSAL_GAIN * self._activation, 4),
            "quality": quality,
        }

    def motor_drive(self):
        """[REAL/TOY] Activation at the b1 motor neuron from the last
        sense() call — the campaniform reflex readout. Reads 0.0 when the
        last sense was bristle (that pathway does not reach b1) or when
        the drive is quiet."""
        peak = self._readout(self._snaps, [B1_ID])
        return round(peak, 4)

    def tick(self, dt):
        """[MODELED] Decay the activation by dt seconds. Returns new level."""
        self._activation = max(0.0, self._activation - 0.2 * dt)
        return round(self._activation, 4)

    def state(self):
        """Current sense state."""
        return {
            "activation": round(self._activation, 4),
            "valence_sign": VALENCE_SIGN,
            "arousal_gain": AROUSAL_GAIN,
            "last_intensity": self._last_intensity,
            "last_quality": self._last_quality,
            "provenance_note": "campaniform path REAL (API); bristle path "
                               "LITERATURE-HYPOTHESIS (see README)",
            "graph": os.path.basename(self._graph_path),
        }
