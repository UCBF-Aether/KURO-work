#!/usr/bin/env python3
"""motion.py — MOTION, a bottled fly sense.

motion vision — direction-selective movement detection, computed live from
REAL Drosophila connectome wiring.

HONESTY CONTRACT (non-negotiable):
- [REAL]    Every node and edge comes from ../subgraphs/motion.json, built from
            the Virtual Fly Brain VFBquery API against the FlyWire FAFB v783
            connectome (11 nodes, 27 edges; edge weight = total
            synapse count). Circuit: T4 (ON-edge, FBbt_00003731) and T5
            (OFF-edge, FBbt_00003736) direction-selective detectors ->
            lobula plate tangential / intrinsic / giant neurons, wide-field
            columnar, visual neuropil intrinsic classes. The textbook
            T4/T5 -> LPTC pathway landed on real rows (T4->LPTC tw=282410,
            T5->LPTC tw=529105). No neuron, synapse, or connection is
            invented here.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] Direction selection ("on"/"off"/"both") is MY interface choice:
            it injects at the T4 node, the T5 node, or both. The zero valence
            (0.00) is MY design choice — motion is informational, not
            valenced, unlike taste or pain. The arousal gain (0.40) and the
            readout layer (hop 1: the deepest hop that carries signal above
            threshold on this circuit — see README) are also design choices.
            The fly never saw your inputs.
- [FICTION] Any narrative gloss ("the machine watches the world slide by")
            is fiction, not a claim about experience.

Usage:
    from motion import Motion
    s = Motion()
    s.sense(0.8, direction="on")   # -> {"activation": ..., "valence_delta": 0.0, ...}
    s.tick(1.0)                    # decay the activation
    s.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

VALENCE_SIGN = 0.0    # [MODELED] motion is informational, not valenced
AROUSAL_GAIN = 0.4    # [MODELED]
READOUT_HOP = 1       # [MODELED] deepest hop above threshold at full injection
DEFAULT_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "subgraphs", "motion.json")

# [REAL] hop-0 node ids, straight from motion.json
T4_ID = "FBbt_00003731"   # T4 neuron — ON-edge detector
T5_ID = "FBbt_00003736"   # T5 neuron — OFF-edge detector

DIRECTIONS = {
    "on": (T4_ID,),
    "off": (T5_ID,),
    "both": (T4_ID, T5_ID),
}


class Motion:
    """A bottled motion vision — direction-selective movement sense, computed
    through real fly wiring.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON. Defaults to the bottled
        ../subgraphs/motion.json.
    """

    def __init__(self, graph_path=None):
        self._graph_path = graph_path or DEFAULT_GRAPH
        with open(self._graph_path) as f:
            graph = json.load(f)
        # [REAL] nodes/edges straight from the file; never invented.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._readout_ids = [n["id"] for n in graph["nodes"]
                             if n.get("hop", 0) == READOUT_HOP]
        self._inject_by_dir = {
            d: tuple(nid for nid in ids if nid in self._nodes)
            for d, ids in DIRECTIONS.items()
        }
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
        self._last_direction = "both"

    def _cascade(self, injection, inject_ids):
        """[MODEL] Port of flysim.run(): inject at hop 0, spread 4 steps."""
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

    def _readout(self, snaps):
        """[REAL/TOY] Max activation over readout-hop nodes, all steps."""
        peak = 0.0
        for snap in snaps:
            for nid in self._readout_ids:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    def sense(self, intensity=0.5, direction="both"):
        """[MODELED] Stimulate the sense at 0..1 intensity.

        direction: "on" (T4 ON-edge detectors), "off" (T5 OFF-edge
        detectors), or "both" (default). T4 and T5 converge on the same
        shared LPTC classes downstream [REAL], so the three selections
        differ in injection, not in wiring.

        Returns activation (thresholded readout-hop max), valence_delta
        (always ~0.0 — motion is informational [MODELED]), arousal_delta
        (AROUSAL_GAIN x activation), and the direction used. Below the
        model's threshold cliff the cascade stays silent and all three read
        0.0 — honest model behavior, documented in the README.
        """
        intensity = min(1.0, max(0.0, intensity))
        direction = direction if direction in DIRECTIONS else "both"
        self._last_intensity = intensity
        self._last_direction = direction
        snaps = self._cascade(intensity, self._inject_by_dir[direction])
        self._activation = self._readout(snaps)
        return {
            "activation": round(self._activation, 4),
            "valence_delta": round(VALENCE_SIGN * self._activation, 4),
            "arousal_delta": round(AROUSAL_GAIN * self._activation, 4),
            "direction": direction,
        }

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
            "last_intensity": self._last_intensity,
            "last_direction": self._last_direction,
            "graph": os.path.basename(self._graph_path),
        }
