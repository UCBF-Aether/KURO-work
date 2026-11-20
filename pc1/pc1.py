#!/usr/bin/env python3
"""pc1.py — pC1 INTEGRATION, a bottled fly social hub.

pC1 (adult doublesex pC1 male neuron, FBbt_00047348) as a courtship
integrator: song + pheromone + internal drive feed its activation, and it
drives P1 (the mating-drive command neuron) through REAL measured
synapses — while feeding 40% of its output back into the fru system it
came from.

HONESTY CONTRACT (non-negotiable):
- [REAL]    Every node and edge comes from ../subgraphs/pc1.json, built from
            the Virtual Fly Brain VFBquery API against the FlyWire FAFB v783
            connectome (21 nodes, 35 edges; edge weight = total synapse
            count). Circuit: pC1 -> fru triple-convergence node (87,164),
            brain doublesex (34,237), SMPad1 (26,553), aSP-a (26,553), DM4
            (22,374), descending motor (14,529), P1 (5,863, the loop-closer).
            No neuron, synapse, or connection is invented here.
- [REAL]    pC1->P1 (tw=5,863) is measured wiring: the song chain
            (../subgraphs/song_lit.json) ends AT pC1, and pC1 drives P1
            (../subgraphs/mating.json) — courtship hearing feeds the mating
            drive through real synapses.
- [REAL]    The graph is CYCLIC: SMPad1->pC1 (tw=10,802) is a true
            recurrent edge (hop-1 -> hop-0). See "CYCLES" below.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The integration function — how pC1 combines song, pheromone
            and internal drive into one activation — is MY design choice
            (equal-weighted mean). How a real pC1 neuron integrates inputs
            is the unmapped frontier; no API holds it.
- [MODELED] The p1_drive / fru_drive readouts are the injection level
            scaled by the REAL measured edge fractions (P1: 0.0270,
            fru: 0.4012 of pC1's total out-weight 217,273) — bookkeeping
            along real synapses, not a measured firing rate.
- [FICTION] Any narrative gloss ("the fly decides she is worth courting")
            is fiction, not a claim about experience.

CYCLES — how the recurrent graph is handled:
    The cascade is a line-for-line port of ../flysim.py's run(): each step
    recomputes activation FRESH from the previous step's fired nodes
    (incoming sums replace, never accumulate; there is no visited set).
    A cycle therefore cannot infinite-loop: each step is a single finite
    pass, and the recurrent edge simply means pC1 may re-receive signal
    at step >= 2. In practice the recurrent edge SMPad1->pC1 carries
    0.1222 of pC1's output — below the model's 0.15 threshold at full
    injection — so the loop does not re-close in model dynamics. This is
    documented honest model behavior, not a wiring claim: the cycle is
    REAL wiring, the sub-threshold recurrency is the model's verdict.

Usage:
    from pc1 import PC1
    p = PC1()
    p.integrate(song_input=1.0, pheromone_input=0.8, drive_input=0.5)
    # -> {"activation": ..., "p1_drive": ..., "fru_drive": ...}
    p.tick(1.0)
    p.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

PC1_ID = "FBbt_00047348"     # adult doublesex pC1 (male) neuron [REAL]
P1_ID = "FBbt_00110621"      # adult fruitless P1 (male) neuron [REAL]
FRU_ID = "FBbt_00016687"     # fruitless expressing neuron: the triple-
                             # convergence node (mating + pheromone +
                             # aggression all feed it) [REAL]
SMPAD1_ID = "FBbt_00050245"  # SMPad1: pC1's recurrent partner [REAL]

READOUT_HOP = 1   # [MODELED] deepest hop above threshold at full injection
DEFAULT_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "subgraphs", "pc1.json")


class PC1:
    """A bottled pC1 social hub — courtship integrator, computed through
    real fly wiring.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON. Defaults to the bottled
        ../subgraphs/pc1.json.
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
        if PC1_ID not in self._nodes:
            raise ValueError("graph has no pC1 hop-0 node; "
                             "wrong graph for the PC1 module")
        out_sum = {}
        for e in graph["edges"]:
            out_sum[e["pre"]] = out_sum.get(e["pre"], 0.0) + e["weight"]
        self._norm = []
        for e in graph["edges"]:
            s = out_sum[e["pre"]]
            self._norm.append((e["pre"], e["post"],
                               e["weight"] / s if s > 0 else 0.0))
        # [REAL] measured edge fractions out of pC1's total out-weight.
        tot = out_sum.get(PC1_ID, 0.0)
        self._frac_to = {}
        for e in graph["edges"]:
            if e["pre"] == PC1_ID and tot > 0:
                self._frac_to[e["post"]] = e["weight"] / tot
        self.p1_frac = self._frac_to.get(P1_ID, 0.0)    # ~0.0270 [REAL]
        self.fru_frac = self._frac_to.get(FRU_ID, 0.0)  # ~0.4012 [REAL]
        self.smpad1_frac = self._frac_to.get(SMPAD1_ID, 0.0)  # ~0.1222
        self.source = graph.get("source", "VFBquery/FlyWire FAFB v783")
        self._activation = 0.0
        self._p1_drive = 0.0
        self._fru_drive = 0.0
        self._last = {"song": 0.0, "pheromone": 0.0, "drive": 0.0,
                      "injection": 0.0}

    def _cascade(self, injection):
        """[MODEL] Port of flysim.run(): inject at hop 0, spread 4 steps.

        Cycle-safe by construction: activation is recomputed fresh every
        step (no accumulation, no visited set), so the SMPad1->pC1
        recurrent edge is just another edge — it cannot infinite-loop.
        """
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

    def integrate(self, song_input=0.0, pheromone_input=0.0,
                  drive_input=0.0):
        """[MODELED/REAL] Integrate the three courtship streams.

        song_input:      courtship song sensed (the song chain's output).
        pheromone_input: pheromone sensed (the pheromone chain's output).
        drive_input:     internal social drive (e.g. from the mating drive).

        [MODELED] Integration is an equal-weighted mean of the three
        inputs — the unmapped frontier, my design choice, documented.
        The combined level is injected at pC1 and the real circuit is
        run. Returns:

          activation: overall hop-1 readout peak (model cascade).
          p1_drive:   the drive passed to P1 along the REAL pC1->P1 edge
                      (injection x 0.0270 measured edge fraction).
          fru_drive:  pC1's recurrent contribution to the fru
                      triple-convergence node (injection x 0.4012).

        Below the model's threshold cliff the cascade stays silent and all
        three read 0.0 — honest model behavior.
        """
        s = min(1.0, max(0.0, song_input))
        p = min(1.0, max(0.0, pheromone_input))
        d = min(1.0, max(0.0, drive_input))
        # [MODELED] how pC1 combines its inputs: equal-weighted mean.
        injection = (s + p + d) / 3.0
        self._last = {"song": s, "pheromone": p, "drive": d,
                      "injection": round(injection, 4)}
        snaps = self._cascade(injection)
        self._activation = self._readout(snaps)
        if injection >= THRESHOLD:
            # [REAL edge fractions] drive passed along measured synapses.
            self._p1_drive = injection * self.p1_frac
            self._fru_drive = injection * self.fru_frac
        else:
            self._p1_drive = 0.0
            self._fru_drive = 0.0
        return {
            "activation": round(self._activation, 4),
            "p1_drive": round(self._p1_drive, 4),
            "fru_drive": round(self._fru_drive, 4),
        }

    def tick(self, dt):
        """[MODELED] Decay activation and drives by dt seconds."""
        decay = 0.2 * dt
        self._activation = max(0.0, self._activation - decay)
        self._p1_drive = max(0.0, self._p1_drive - decay * 0.1)
        self._fru_drive = max(0.0, self._fru_drive - decay * 0.1)
        return round(self._activation, 4)

    def state(self):
        """Current hub state."""
        return {
            "activation": round(self._activation, 4),
            "p1_drive": round(self._p1_drive, 4),
            "fru_drive": round(self._fru_drive, 4),
            "p1_edge_fraction": round(self.p1_frac, 4),
            "fru_edge_fraction": round(self.fru_frac, 4),
            "recurrent_edge_fraction_smpad1": round(self.smpad1_frac, 4),
            "cyclic": True,
            "readout_hop": READOUT_HOP,
            "last_inputs": self._last,
            "graph": os.path.basename(self._graph_path),
        }
