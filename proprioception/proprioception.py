#!/usr/bin/env python3
"""proprioception.py — PROPRIOCEPTION, a bottled fly sense.

The fly's sense of leg position — computed live from REAL Drosophila
connectome wiring.

HONESTY CONTRACT (non-negotiable):
- [REAL]    Every node and edge comes from ../subgraphs/proprioception.json,
            built from the Virtual Fly Brain VFBquery API against the FlyWire
            FAFB v783 connectome (8 nodes, 18 edges; edge weight = total
            synapse count). Circuit: femoral chordotonal organ (FeCO)
            mechanosensory neuron -> metathoracic / mesothoracic / prothoracic
            segmental neurons + ascending leg-to-brain branch ->
            efferent motor neuron (segmental reflex arc). No neuron, synapse,
            or connection is invented here.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] Leg selection, the zero valence, the 0.2 arousal gain, and the
            readout layers are MY design choices, not biology. The graph holds
            ONE FeCO class for all legs, so the leg selects which segmental
            neuromere the readout follows (front=prothoracic, mid=mesothoracic,
            hind=metathoracic — real segmental anatomy). The fly never saw
            your inputs.
- [FICTION] Any narrative gloss ("the leg knows where it is") is fiction,
            not a claim about experience.

Usage:
    from proprioception import Proprioception
    p = Proprioception()
    p.sense(0.8, leg="front")  # -> {"activation", "valence_delta", "arousal_delta", "leg"}
    p.reflex_arc()             # -> activation at the efferent motor node
    p.tick(1.0)                # decay the activation
    p.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

VALENCE_SIGN = 0.0    # [MODELED] proprioception is informational, not valenced
AROUSAL_GAIN = 0.2    # [MODELED] position sense is low-arousal
READOUT_HOP = 1       # [MODELED] deepest hop with robust signal above threshold
REFLEX_NODE_ID = "FBbt_00051963"   # [REAL] efferent neuron, hop 2 — the reflex-arc end
# [MODELED] the graph holds one FeCO class for all legs, so injection is the
# whole FeCO array; the LEG instead selects the segmental readout node —
# real segmental anatomy: front/mid/hind legs report to the
# pro-/meso-/metathoracic neuromeres respectively.
LEG_READOUT = {
    "all": ["FBbt_00001986", "FBbt_00001985", "FBbt_00001984"],  # meta/meso/pro
    "front": ["FBbt_00001984"],   # prothoracic neuromere
    "mid": ["FBbt_00001985"],     # mesothoracic neuromere
    "hind": ["FBbt_00001986"],    # metathoracic neuromere
}
DEFAULT_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "subgraphs", "proprioception.json")


class Proprioception:
    """A bottled proprioceptive sense — leg position, computed through real fly wiring.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON. Defaults to the bottled
        ../subgraphs/proprioception.json.
    """

    def __init__(self, graph_path=None):
        self._graph_path = graph_path or DEFAULT_GRAPH
        with open(self._graph_path) as f:
            graph = json.load(f)
        # [REAL] nodes/edges straight from the file; never invented.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._order = [n["id"] for n in graph["nodes"]]
        self._readout_ids = [n["id"] for n in graph["nodes"]
                             if n.get("hop", 0) == READOUT_HOP]
        self._inject_ids = [n["id"] for n in graph["nodes"]
                            if n.get("hop", 0) == 0]
        if REFLEX_NODE_ID not in self._nodes:
            raise ValueError("reflex-arc node %s missing from graph"
                             % REFLEX_NODE_ID)
        out_sum = {}
        for e in graph["edges"]:
            out_sum[e["pre"]] = out_sum.get(e["pre"], 0.0) + e["weight"]
        self._norm = []
        for e in graph["edges"]:
            s = out_sum[e["pre"]]
            self._norm.append((e["pre"], e["post"],
                               e["weight"] / s if s > 0 else 0.0))
        self.source = graph.get("source", "VFBquery/FlyWire FAFB v783")
        self._activation = 0.0
        self._last_intensity = 0.0
        self._last_leg = "all"

    def _cascade(self, injection):
        """[MODEL] Port of flysim.run(): inject at hop 0, spread 4 steps."""
        act = {nid: 0.0 for nid in self._nodes}
        for nid in self._inject_ids:
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

    def _readout(self, snaps, node_ids):
        """[REAL/TOY] Max activation over given nodes, all steps."""
        peak = 0.0
        for snap in snaps:
            for nid in node_ids:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    def sense(self, intensity=0.5, leg="all"):
        """[MODELED] Stimulate the sense at 0..1 intensity for one leg or all.

        leg: "front" / "mid" / "hind" / "all". The graph holds a single FeCO
        class, so the leg selects the segmental readout: front reads the
        prothoracic neuromere, mid the mesothoracic, hind the metathoracic
        (real segmental anatomy); "all" reads the max over all three — a
        modeling choice, documented in the README.

        Returns activation (thresholded readout-hop max), valence_delta
        (0.0 x activation — position is informational), arousal_delta
        (0.2 x activation), and the leg used. Below the model's threshold
        cliff the cascade stays silent and all read 0.0 — honest model
        behavior, documented in the README.
        """
        if leg not in LEG_READOUT:
            raise ValueError("leg must be one of %s, got %r"
                             % (sorted(LEG_READOUT), leg))
        intensity = min(1.0, max(0.0, intensity))
        self._last_intensity = intensity
        self._last_leg = leg
        snaps = self._cascade(intensity)
        self._activation = self._readout(snaps, LEG_READOUT[leg])
        return {
            "activation": round(self._activation, 4),
            "valence_delta": round(VALENCE_SIGN * self._activation, 4),
            "arousal_delta": round(AROUSAL_GAIN * self._activation, 4),
            "leg": leg,
        }

    def reflex_arc(self):
        """[REAL/TOY] Activation at the efferent motor node (hop 2) — the
        reflex-arc readout: FeCO -> segmental neurons -> efferent motor.
        Peak across all cascade steps, from the last sense() call. 0.0 if
        sense() has not been called yet."""
        if self._last_intensity == 0.0 and self._activation == 0.0:
            return 0.0
        snaps = self._cascade(self._last_intensity)
        return round(self._readout(snaps, [REFLEX_NODE_ID]), 4)

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
            "readout_hop": READOUT_HOP,
            "reflex_node": REFLEX_NODE_ID,
            "last_intensity": self._last_intensity,
            "last_leg": self._last_leg,
            "graph": os.path.basename(self._graph_path),
        }
