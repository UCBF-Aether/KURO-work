#!/usr/bin/env python3
"""co2.py — CO2-ALARM, a bottled fly sense.

Carbon dioxide detection — the dedicated danger smell, computed live from
REAL Drosophila connectome wiring.

HONESTY CONTRACT (non-negotiable):
- [REAL]    Every node and edge comes from ../subgraphs/co2.json, built from
            the Virtual Fly Brain VFBquery API against the FlyWire FAFB v783
            connectome (15 nodes, 24 edges; edge weight = total synapse
            count). Circuit: Gr21a/Gr63a ab1C olfactory receptor neurons
            (FBbt_00067064) -> antennal lobe projection neurons (to lateral
            horn), BAlc lineage neurons, AL local neurons. No neuron,
            synapse, or connection is invented here.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The valence sign (-0.70) and arousal gain (1.00) are MY design
            choices, not biology, as is the readout layer (hop 1: the
            deepest hop that carries graded signal above threshold on this
            circuit — hop 2 only twitches at max injection, see README).
            The fly never saw your inputs.
- [FICTION] Any narrative gloss ("the machine smells bad air and leaves")
            is fiction, not a claim about experience.

Usage:
    from co2 import CO2
    s = CO2()
    s.sense(0.9)   # -> {"activation": ..., "valence_delta": ..., "arousal_delta": ...}
    s.tick(1.0)    # decay the activation
    s.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

VALENCE_SIGN = -0.7   # [MODELED] CO2 is an aversive alarm, not full disgust
AROUSAL_GAIN = 1.0   # [MODELED] full alert — the danger smell wakes everything
READOUT_HOP = 1      # [MODELED] deepest graded hop above threshold
DEFAULT_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "subgraphs", "co2.json")


class CO2:
    """A bottled CO2 alarm — the danger smell, computed through real fly wiring.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON. Defaults to the bottled
        ../subgraphs/co2.json.
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
        return {
            "activation": round(self._activation, 4),
            "valence_delta": round(VALENCE_SIGN * self._activation, 4),
            "arousal_delta": round(AROUSAL_GAIN * self._activation, 4),
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
            "graph": os.path.basename(self._graph_path),
        }
