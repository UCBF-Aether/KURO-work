#!/usr/bin/env python3
"""
compass.py — COMPASS, the fly's internal GPS.

A heading-direction state module running on REAL Drosophila central-complex
wiring: E-PG ring neurons (the ellipsoid-body compass) -> central-complex
small/large field, intrinsic, and ring populations.

HONESTY CONTRACT (non-negotiable, repeated in every surface of this project):
- [REAL]    Every node and edge comes from ../subgraphs/compass.json, built
            from the Virtual Fly Brain VFBquery API against the FlyWire
            FAFB v783 connectome (E-PG FBbt_00047030 -> 6 hop-1 classes by
            synapse weight; Delta7/PEN/PFN/PFL/R-neuron below-cutoff partners
            recorded in the JSON's honest_note, not hidden). No neuron,
            synapse, or connection is invented here.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The 16-unit heading bump is MY model, not biology. The REAL
            ring-attractor dynamics — how the activity bump moves, holds, and
            updates heading in the ellipsoid body — are the genuinely
            unmapped frontier; no API holds them. Here: heading is continuous
            state (degrees, modulo 360); the bump is a circular Gaussian
            (sigma=1.5 units, peak normalized to 1.0) sampled at 16 positions
            around the ring; turn() rotates it by the given angle; injection
            into the E-PG cascade scales with |turn|/90 (a 90-degree turn is
            full strength). The fly's real update uses angular-velocity inputs
            (PEN neurons); this module just proves the E-PG wiring fires when
            the heading changes.
- [FICTION] Any narrative one-liners ("north lives here") are gloss, not
            claims about experience.

This is a STATE module, not a drive or a sense: it holds heading, the way
the other bottles hold wanting or activation. Combine: feed an agent's
rotations through turn(); read heading() to steer.
"""

import json
import math
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]
RING_UNITS = 16    # [MODELED] discrete samples of the continuous ring
BUMP_SIGMA = 1.5   # [MODELED] Gaussian width, in ring units


class Compass:
    """A heading-direction state module on real E-PG compass wiring.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON (nodes with hop, edges with
        pre/post/weight). Defaults to ../subgraphs/compass.json.
    """

    def __init__(self, graph_path=None):
        if graph_path is None:
            graph_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "subgraphs", "compass.json")
        self._graph_path = graph_path
        with open(graph_path) as f:
            graph = json.load(f)
        # [REAL] nodes/edges straight from the file; never invented.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._inject_ids = [n["id"] for n in graph["nodes"]
                            if n.get("hop", 0) == 0]
        self._readout_ids = [n["id"] for n in graph["nodes"]
                             if n.get("hop", 0) == 1]
        out_sum = {}
        for e in graph["edges"]:
            out_sum[e["pre"]] = out_sum.get(e["pre"], 0.0) + e["weight"]
        self._norm = []
        for e in graph["edges"]:
            s = out_sum[e["pre"]]
            self._norm.append((e["pre"], e["post"],
                               e["weight"] / s if s > 0 else 0.0))
        self.source = graph.get("source", "VFBquery/FlyWire FAFB v783")

        # [MODELED] heading state; bump is derived from it, never stored raw.
        self._heading = 0.0      # degrees, kept in [0, 360)
        self.activation = 0.0    # last cascade readout (hop-1 peak)

    # ---- internal machinery ----

    def _cascade(self, injection):
        """[MODEL] Port of flysim.run(): inject at hop 0 (E-PG), spread 4 steps."""
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
        """[MODEL] Peak activation over hop-1 nodes, across ALL steps.

        Reading only the final step shows a dead circuit (the signal has
        moved on); peak-across-steps is the honest readout — same semantics
        as the pain bottle's fix.
        """
        peak = 0.0
        for snap in snaps:
            for nid in self._readout_ids:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    @staticmethod
    def _bump_at(heading_deg):
        """[MODELED] 16-unit circular Gaussian centered on heading."""
        center = (heading_deg % 360.0) / 360.0 * RING_UNITS
        raw = []
        for i in range(RING_UNITS):
            d = abs(i - center)
            d = min(d, RING_UNITS - d)  # circular distance
            raw.append(math.exp(-(d ** 2) / (2.0 * BUMP_SIGMA ** 2)))
        peak = max(raw)
        return [v / peak for v in raw]  # peak normalized to 1.0

    # ---- public API ----

    def turn(self, degrees):
        """[MODELED] Rotate the heading bump by the given angular change.

        Runs the model cascade on the REAL E-PG wiring with injection scaled
        to the turn size (a 90-degree turn is full strength — the injection
        mapping is the modeled part; the cascade that follows is the real
        circuit). Positive = clockwise, negative = counterclockwise.
        """
        injection = min(1.0, abs(degrees) / 90.0)  # [MODELED]
        self.activation = self._readout(self._cascade(injection))
        self._heading = (self._heading + degrees) % 360.0
        return {
            "activation": round(self.activation, 4),
            "bump_position": round(self._heading, 3),
        }

    def heading(self):
        """Current heading in degrees [0, 360)."""
        return self._heading

    def state(self):
        """Current compass state: heading, last cascade activation, the bump."""
        return {
            "heading": round(self._heading, 3),
            "activation": round(self.activation, 4),
            "bump": [round(v, 4) for v in self._bump_at(self._heading)],
        }
