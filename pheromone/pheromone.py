#!/usr/bin/env python3
"""pheromone.py — PHEROMONE, a bottled fly sense.

Courtship/social smell — the mating drive's nose, computed live from REAL
Drosophila connectome wiring.

HONESTY CONTRACT (non-negotiable):
- [REAL]    Every node and edge comes from ../subgraphs/pheromone.json, built
            from the Virtual Fly Brain VFBquery API against the FlyWire FAFB
            v783 connectome (15 nodes, 21 edges; edge weight = total synapse
            count). Circuit: Or47b olfactory receptor neuron (FBbt_00067056)
            -> antennal lobe projection neurons -> lateral horn + the
            fruitless-expressing bridge node (FBbt_00016687) that converges
            with the P1 courtship chain (../subgraphs/mating.json). No
            neuron, synapse, or connection is invented here. Or88a was
            unindexable and ppk23/29 do not exist as adult classes — see
            README; this bottle is Or47b, honestly labeled.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The valence sign (+0.50: courtship odors are appetitive in the
            right context) and arousal gain (0.80) are MY design choices,
            not biology, as is the readout layer (hop 1: the deepest hop
            that carries signal above threshold on this circuit — hop 2
            peaks at 0.1463, just below the 0.15 threshold; see README).
            The courtship_bridge() readout of FBbt_00016687 is a modeled
            interface for the mating bottle, not a biological claim. The
            fly never saw your inputs.
- [FICTION] Any narrative gloss ("the machine catches a scent") is fiction,
            not a claim about experience.

Usage:
    from pheromone import Pheromone
    s = Pheromone()
    s.sense(0.8)          # -> {"activation": ..., "valence_delta": ..., "arousal_delta": ...}
    s.courtship_bridge()  # -> activation at the fruitless bridge node (for the mating bottle)
    s.tick(1.0)           # decay the activation
    s.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

VALENCE_SIGN = 0.5    # [MODELED] courtship-relevant odors are appetitive in context
AROUSAL_GAIN = 0.8    # [MODELED]
READOUT_HOP = 1       # [MODELED] deepest hop above threshold at full injection
BRIDGE_ID = "FBbt_00016687"  # [REAL] fruitless expressing neuron — meets the P1 chain
DEFAULT_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "subgraphs", "pheromone.json")


class Pheromone:
    """A bottled pheromone sense — courtship/social smell, computed through real fly wiring.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON. Defaults to the bottled
        ../subgraphs/pheromone.json.
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
        self._bridge = 0.0
        self._last_intensity = 0.0

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

    def _readout(self, snaps):
        """[REAL/TOY] Max activation over readout-hop nodes, all steps."""
        peak = 0.0
        for snap in snaps:
            for nid in self._readout_ids:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    def sense(self, intensity=0.5):
        """[MODELED] Stimulate the sense at 0..1 intensity.

        Returns activation (thresholded readout-hop max), valence_delta
        (VALENCE_SIGN x activation) and arousal_delta (AROUSAL_GAIN x
        activation). Below the model's threshold cliff the cascade stays
        silent and all three read 0.0 — honest model behavior, documented
        in the README.
        """
        intensity = min(1.0, max(0.0, intensity))
        self._last_intensity = intensity
        snaps = self._cascade(intensity)
        self._activation = self._readout(snaps)
        self._bridge = max((snap.get(BRIDGE_ID, 0.0) for snap in snaps),
                           default=0.0)
        return {
            "activation": round(self._activation, 4),
            "valence_delta": round(VALENCE_SIGN * self._activation, 4),
            "arousal_delta": round(AROUSAL_GAIN * self._activation, 4),
        }

    def courtship_bridge(self):
        """[MODELED] Peak activation at the fruitless-expressing bridge node.

        FBbt_00016687 is where this pheromone chain meets the P1 mating
        chain (see ../subgraphs/mating.json). Other bottles (mating) may
        read this number; the interface is a modeled convenience, the
        underlying edge Or47b -> bridge (13,133 synapses) is real.
        """
        return round(self._bridge, 4)

    def tick(self, dt):
        """[MODELED] Decay the activation by dt seconds. Returns new level."""
        self._activation = max(0.0, self._activation - 0.2 * dt)
        self._bridge = max(0.0, self._bridge - 0.2 * dt)
        return round(self._activation, 4)

    def state(self):
        """Current sense state."""
        return {
            "activation": round(self._activation, 4),
            "courtship_bridge": round(self._bridge, 4),
            "valence_sign": VALENCE_SIGN,
            "arousal_gain": AROUSAL_GAIN,
            "readout_hop": READOUT_HOP,
            "bridge_node": BRIDGE_ID,
            "last_intensity": self._last_intensity,
            "graph": os.path.basename(self._graph_path),
        }
