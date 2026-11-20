#!/usr/bin/env python3
"""salt.py — SALT, a bottled fly sense with TWO opponent channels.

Salt taste is an opponent system: LOW salt attracts (feeding/approach),
HIGH salt repels (withdrawal). Both chains live in one bottle, computed
live from REAL Drosophila connectome wiring.

HONESTY CONTRACT (non-negotiable):
- [REAL]    Every node and edge comes from ../subgraphs/salt.json, built from
            the Virtual Fly Brain VFBquery API against the FlyWire FAFB v783
            connectome (26 nodes, 40 edges; edge weight = total synapse
            count; the "chain" field on nodes/edges separates the two
            opponent chains). No neuron, synapse, or connection is invented
            here.
            - LOW chain (FBbt_00100043, low salt-sensing GRN): real named-query
              rows, standard top-k walk.
            - HIGH chain (FBbt_00052561, high salt-sensing GRN): every direct
              query form was dead, so its hop-1 is derived by SUBTRACTION —
              parent class FBbt_00049615 (salt-sensing neuron, 50 real named
              rows) minus the resolved low-salt child's rows. All underlying
              rows are real API rows; the ATTRIBUTION to high-salt is the
              documented method, not a measured label (see ../GAPS.md).
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The valence signs (+0.40 low / -0.60 high) and arousal gain
            (0.50) are MY design choices, not biology, as is the readout
            layer (hop 1 for BOTH chains — see README for why) and the
            chain-selection parameter itself. The fly never saw your inputs.
- [FICTION] Any narrative gloss ("the machine leans in / pulls back") is
            fiction, not a claim about experience.

Usage:
    from salt import Salt
    s = Salt()
    s.sense(0.8, chain="low")   # -> {activation, valence_delta (+), arousal_delta, chain}
    s.sense(0.8, chain="high")  # -> {activation, valence_delta (-), arousal_delta, chain}
    s.tick(1.0)
    s.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]
DECAY = 0.2        # activation decay per second [MODELED]

CHAINS = ("low", "high")
# [MODELED] low salt is attractive, high salt is aversive.
VALENCE_SIGN = {"low": 0.40, "high": -0.60}
AROUSAL_GAIN = 0.50
# [MODELED] readout at hop 1 for both chains: low's feeding/approach
# populations (SEZ output, gustatory projection, SLP GPN) and high's
# motor/withdrawal populations (prothoracic, ascending, DNg103) both sit
# at hop 1. Low's hop 2 carries signal (0.20) but includes optic-lobe
# classes from a broad hop-1 node — noise for a feeding readout.
READOUT_HOP = 1
DEFAULT_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "subgraphs", "salt.json")


class Salt:
    """A bottled salt taste — two opponent channels, one bottle.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON with a "chain" field on
        nodes/edges. Defaults to the bottled ../subgraphs/salt.json.
    """

    def __init__(self, graph_path=None):
        self._graph_path = graph_path or DEFAULT_GRAPH
        with open(self._graph_path) as f:
            graph = json.load(f)
        # [REAL] nodes/edges straight from the file, filtered by chain;
        # never invented.
        self._chains = {}
        for chain in CHAINS:
            nodes = {n["id"]: n for n in graph["nodes"]
                     if n.get("chain") == chain}
            edges = [e for e in graph["edges"]
                     if e.get("chain") == chain]
            inject_ids = [nid for nid, n in nodes.items()
                          if n.get("hop", 0) == 0]
            readout_ids = [nid for nid, n in nodes.items()
                           if n.get("hop", 0) == READOUT_HOP]
            out_sum = {}
            for e in edges:
                out_sum[e["pre"]] = out_sum.get(e["pre"], 0.0) + e["weight"]
            norm = [(e["pre"], e["post"],
                     e["weight"] / out_sum[e["pre"]] if out_sum[e["pre"]] > 0 else 0.0)
                    for e in edges]
            self._chains[chain] = {
                "nodes": nodes, "norm": norm,
                "inject_ids": inject_ids, "readout_ids": readout_ids,
            }
        self.source = graph.get("source", "VFBquery/FlyWire FAFB v783")
        self._activation = 0.0
        self._last_intensity = 0.0
        self._last_chain = None

    def _cascade(self, chain, injection):
        """[MODEL] Port of flysim.run(): inject at hop 0, spread 4 steps,
        on that chain's subgraph only."""
        ch = self._chains[chain]
        act = {nid: 0.0 for nid in ch["nodes"]}
        for nid in ch["inject_ids"]:
            act[nid] = injection
        snaps = [{nid: a for nid, a in act.items() if a >= THRESHOLD}]
        for _ in range(STEPS):
            fired = {nid for nid, a in act.items() if a >= THRESHOLD}
            incoming = {}
            for pre, post, w in ch["norm"]:
                if pre in fired:
                    incoming[post] = incoming.get(post, 0.0) + act[pre] * w
            act = {nid: incoming.get(nid, 0.0) for nid in ch["nodes"]}
            snaps.append({nid: a for nid, a in act.items()
                          if a >= THRESHOLD})
        return snaps

    def _readout(self, chain, snaps):
        """[REAL/TOY] Max activation over the chain's readout-hop nodes,
        all steps."""
        peak = 0.0
        for nid in self._chains[chain]["readout_ids"]:
            for snap in snaps:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    def sense(self, intensity=0.5, chain="low"):
        """[MODELED] Stimulate one opponent channel at 0..1 intensity.

        chain="low"  -> attractive salt (valence +0.40 x activation)
        chain="high" -> aversive salt  (valence -0.60 x activation)
        arousal_delta = 0.50 x activation for both.

        Returns {activation, valence_delta, arousal_delta, chain}.
        Below the model's threshold cliff the cascade stays silent and all
        three read 0.0 — honest model behavior, documented in the README.
        """
        if chain not in CHAINS:
            raise ValueError("chain must be one of %r, got %r"
                             % (CHAINS, chain))
        intensity = min(1.0, max(0.0, intensity))
        self._last_intensity = intensity
        self._last_chain = chain
        snaps = self._cascade(chain, intensity)
        self._activation = self._readout(chain, snaps)
        return {
            "activation": round(self._activation, 4),
            "valence_delta": round(VALENCE_SIGN[chain] * self._activation, 4),
            "arousal_delta": round(AROUSAL_GAIN * self._activation, 4),
            "chain": chain,
        }

    def tick(self, dt):
        """[MODELED] Decay the activation by dt seconds. Returns new level."""
        self._activation = max(0.0, self._activation - DECAY * dt)
        return round(self._activation, 4)

    def state(self):
        """Current sense state."""
        return {
            "activation": round(self._activation, 4),
            "last_chain": self._last_chain,
            "valence_sign": dict(VALENCE_SIGN),
            "arousal_gain": AROUSAL_GAIN,
            "readout_hop": READOUT_HOP,
            "last_intensity": self._last_intensity,
            "graph": os.path.basename(self._graph_path),
        }
