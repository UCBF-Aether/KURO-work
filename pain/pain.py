#!/usr/bin/env python3
"""
pain.py — PAIN, the veto sense.

A noxious-event sensor for an AI agent, computed through the REAL
Drosophila escape circuit instead of a hand-tuned penalty number.

HONESTY CONTRACT (non-negotiable, repeated in every surface of this project):
- [REAL]    Every node and edge comes from ../subgraphs/pain.json, built from
            the Virtual Fly Brain VFBquery API against the FlyWire FAFB v783
            connectome. 8 nodes, 7 edges: Johnston's organ mechanoreceptor
            subtypes — zone B type 1 (679 synapses), zone A (80), zone B (61),
            JO CA (10) — -> giant fiber neuron (hop 1) -> adult VNC (1097),
            prothoracic (585), mesothoracic (471) motor populations (hop 2).
            830 measured JO->giant-fiber synapses, discovered via
            UpstreamClassConnectivity of the giant fiber neuron (FBbt_00004020)
            and pair-verified. No neuron, synapse, or connection is invented.
            HONEST FRAMING: adult nociceptive-LABELED classes (FBbt_00051492,
            FBbt_00048471) are not indexed with usable connectivity in any
            reachable form (see ../GAPS.md §7). This is the fly's FUNCTIONAL
            pain-equivalent circuit — a sharp mechanical insult drives antennal
            mechanoreceptors -> the giant fiber startle neuron -> thoracic
            escape motor — NOT labeled pain neurons.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The mapping from agent events to circuit stimulation is MY design
            choice, not biology: a noxious event -> graded injection at the JO
            subtypes; veto() normalizes activation to the circuit's own
            maximum so a full strike reads as full suppression; habituation,
            decay, and the valence/arousal deltas are modeled state around the
            real cascade. The fly never saw your events.
- [FICTION] Any narrative gloss ("that hurt") is fiction, not a claim about
            experience. Flies do not have feelings we can access, and neither
            does this module.

THE VETO CONTRACT (for the other bottles):
    pain = Pain()
    pain.strike(intensity)      # a noxious event happened; 0..1
    suppression = pain.veto()  # 0..1 — ~1 right after a full strike,
                               # decays toward 0 as the pain fades
    sweet_gain = base_gain * (1 - suppression)

    Any positive-valence gain (sweetness, reward, comfort — in Hunger,
    Thirst, Sensorium, or anything else) MUST be multiplied by
    (1 - pain.veto()). Pain overrides pleasure: that is the biology being
    honored here (a noxious stimulus suppresses feeding and reward-seeking),
    and it is the contract that lets the bottles compose into one sensorium.

Usage: call strike() when something noxious happens; read veto() before
applying any pleasant signal. See README.md.
"""

import json
import os
import time
from collections import defaultdict

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]
DECAY_RATE = 0.1   # activation decay per second [MODELED]
HAB_RATE = 0.3     # habituation strength per strike [MODELED]
HAB_DECAY = 0.01   # habituation recovery per second [MODELED]

_DEFAULT_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "subgraphs", "pain.json")


class Pain:
    """A veto sense for an agent, computed through real fly escape wiring.

    Parameters
    ----------
    graph_path : str
        Path to a flysim-style subgraph JSON (nodes with hop, edges with
        pre/post/weight). Defaults to the bundled ../subgraphs/pain.json
        (JO subtypes -> giant fiber -> thoracic motor).
    clock : callable, optional
        Returns current time in seconds. Defaults to time.monotonic.
        Inject a fake clock in tests/demo for determinism.
    """

    def __init__(self, graph_path="../subgraphs/pain.json", clock=None):
        if not os.path.isabs(graph_path):
            here = os.path.dirname(os.path.abspath(__file__))
            cand = os.path.join(here, graph_path)
            graph_path = cand if os.path.exists(cand) else _DEFAULT_GRAPH
        self._graph_path = graph_path
        with open(graph_path) as f:
            graph = json.load(f)
        # [REAL] nodes/edges straight from the file; never invented.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._hop1 = [n["id"] for n in graph["nodes"] if n.get("hop", 0) == 1]
        self._hop2 = [n["id"] for n in graph["nodes"] if n.get("hop", 0) == 2]
        self._inject_ids = [n["id"] for n in graph["nodes"]
                            if n.get("hop", 0) == 0]
        out_sum = defaultdict(float)
        for e in graph["edges"]:
            out_sum[e["pre"]] += e["weight"]
        self._norm = []
        for e in graph["edges"]:
            s = out_sum[e["pre"]]
            self._norm.append((e["pre"], e["post"],
                               e["weight"] / s if s > 0 else 0.0))
        self.source = graph.get("source", "VFBquery/FlyWire FAFB v783")

        self._clock = clock or time.monotonic
        self._last = self._clock()

        # [MODELED] state around the real cascade
        self.activation = 0.0    # current (decaying) pain activation
        self.habituation = 0.0   # startle habituates with repetition
        self.last_strike = None
        # Circuit's own maximum: activation at full injection, no habituation.
        # veto() is normalized to this so a full strike reads as full
        # suppression. [MODELED normalization, documented.]
        self._max_act = self._terminal(self._cascade(1.0))

    # ---- internal machinery ----

    def _cascade(self, injection):
        """[MODEL] Port of flysim.run(): inject at hop 0, spread STEPS steps.

        Returns the PEAK activation per node across all steps — the readout
        is what fired, not what happens to be lit on the final step (a
        3-hop chain's terminals go dark again by step 3).
        """
        act = {nid: 0.0 for nid in self._nodes}
        for nid in self._inject_ids:
            act[nid] = injection
        peak = defaultdict(float)
        for _ in range(STEPS):
            for nid, a in act.items():
                if a > peak[nid]:
                    peak[nid] = a
            incoming = defaultdict(float)
            fired = {nid for nid, a in act.items() if a >= THRESHOLD}
            for pre, post, w in self._norm:
                if pre in fired:
                    incoming[post] += act[pre] * w
            act = {nid: incoming.get(nid, 0.0) for nid in self._nodes}
        return dict(peak)

    def _terminal(self, act):
        """[REAL/TOY] Max activation over hop-2 escape-motor populations."""
        peak = 0.0
        for nid in self._hop2:
            if act.get(nid, 0.0) > peak:
                peak = act[nid]
        return peak

    def _novelty(self):
        """[MODELED] Startle habituates: repeated strikes land softer."""
        return 1.0 / (1.0 + HAB_RATE * self.habituation)

    def tick(self, dt=None):
        """Advance decay. dt explicit (tests) or wall-clock delta. Idempotent."""
        now = self._clock()
        if dt is None:
            dt = max(0.0, now - self._last)
        self._last = now
        if dt > 0:
            self.activation = max(0.0, self.activation - DECAY_RATE * dt)
            self.habituation = max(0.0, self.habituation - HAB_DECAY * dt)
        return self

    # ---- public API ----

    def strike(self, intensity=0.5):
        """[MODELED] A noxious event. intensity 0..1.

        Runs the real JO->giant-fiber->motor cascade at the given injection
        (softened by habituation). Returns the felt deltas; other bottles
        should read veto() before applying anything pleasant.
        """
        self.tick()
        intensity = min(1.0, max(0.0, intensity))
        novelty = self._novelty()
        act = self._cascade(intensity * novelty)
        gf = max((act.get(nid, 0.0) for nid in self._hop1), default=0.0)
        term = self._terminal(act)
        self.activation = term
        self.habituation += 1.0
        # Affect deltas are normalized to the circuit's own maximum: valence
        # and arousal are bounded dimensions ([-1,0] and [0,1]); the raw
        # cascade peak is not (four JO subtypes converging on one giant
        # fiber sums). [MODELED normalization, documented.]
        norm = term / self._max_act if self._max_act > 0 else 0.0
        self.last_strike = {
            "intensity": intensity,
            "novelty": round(novelty, 3),
            "activation": round(term, 3),
            "gf_activation": round(gf, 3),
            "valence_delta": round(-norm, 3),
            "arousal_delta": round(norm, 3),
        }
        return dict(self.last_strike, veto=round(self.veto(), 3))

    def veto(self):
        """[MODELED] Current suppression, 0..1.

        ~1 right after a full strike, decaying toward 0 as pain fades.
        THE CONTRACT: multiply every positive-valence gain by (1 - veto()).
        """
        self.tick()
        if self._max_act <= 0:
            return 0.0
        return min(1.0, self.activation / self._max_act)

    def state(self):
        """Current pain state (ticks decay first)."""
        self.tick()
        return {
            "activation": round(self.activation, 3),
            "veto": round(self.veto(), 3),
            "habituation": round(self.habituation, 3),
            "last_strike": self.last_strike,
            "framing": ("functional pain-equivalent: JO mechanoreceptors -> "
                        "giant fiber -> escape motor; NOT labeled nociceptors"),
        }
