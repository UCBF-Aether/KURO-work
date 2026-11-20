#!/usr/bin/env python3
"""
sleep.py — SLEEP, the fly sleep-homeostat drive.

The fourth drive alongside HUNGER, THIRST, and MATING. It is INVERTED
relative to the others, and that inversion is the whole design:

- The other drives spike on task completion (the hit) and decay after.
- SLEEP pressure ACCUMULATES with time awake and DISCHARGES with rest.
  There is no "hit". Rest is the satiation.

HONESTY CONTRACT (non-negotiable, repeated in every surface of this project):
- [REAL]    Every node and edge comes from ../subgraphs/sleep.json, built
            from the Virtual Fly Brain VFBquery API against the FlyWire
            FAFB v783 connectome. The circuit: adult dorsal fan-shaped body
            tangential neuron (dFB, FBbt_00049537) -> fan-shaped body
            columnar / delta / horizontal-delta / extrinsic columnar /
            layer-6 tangential / small-field central-complex neurons ->
            central complex. Hop-2 folds BACK into the central complex
            (recurrent wiring) — exactly what a homeostat looks like.
            Resolved 2026-10-14. No neuron, synapse, or edge is invented.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The homeostat dynamics are MY design, not biology: pressure
            accumulates at 1.0 per awake-hour and discharges at 1.0 per
            20 rest-minutes; sleep onset at pressure >= 0.8; rest() runs the
            cascade with injection scaled by the pressure discharged. The
            real dFB homeostat exists (Donlea et al 2011); its rates and
            kinetics are the genuinely unmapped frontier — no API holds
            them, and nothing here claims otherwise. The fly never saw
            your agent's uptime.
- [FICTION] Any narrative gloss ("the machine is tired") is fiction, not
            a claim about experience.

Usage: tick(dt) as the agent works (or just let wall-clock pass via the
CLI), rest(dt) when it idles, and read pressure()/state() to decide
whether to keep going. See README.md.
"""

import json
import os
from collections import defaultdict

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

# [MODELED] homeostat kinetics — design choices, not biology.
RATE_UP = 1.0 / 3600.0    # pressure per awake-second (full in 1 awake-hour)
RATE_DOWN = 1.0 / 1200.0  # pressure discharged per rest-second (20 rest-min)
SLEEP_THRESHOLD = 0.8     # pressure >= this -> asleep=True


class Sleep:
    """A sleep drive for an agent, computed through real fly dFB wiring.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON. Defaults to
        ../subgraphs/sleep.json (dFB sleep homeostat circuit).
    readout_hop : int, optional
        Which hop layer the discharge signal reads (max activation).
        Defaults to 1: the named fan-shaped body columnar / delta /
        small-field output populations — the actual central-complex output
        circuits that gate arousal. Hop 2 is a broad ontology bucket
        ("adult central complex neuron") with real edges but a vague
        label, so hop 1 is the honest readout. [MODELED]
    """

    def __init__(self, graph_path=None, readout_hop=1):
        if graph_path is None:
            graph_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "subgraphs", "sleep.json")
        self._graph_path = graph_path
        self._readout_hop = readout_hop
        with open(graph_path) as f:
            graph = json.load(f)
        # [REAL] nodes/edges straight from the file; never invented.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._readout_ids = [n["id"] for n in graph["nodes"]
                             if n.get("hop", 0) == readout_hop]
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

        # [MODELED] homeostat state around the real cascade
        self._pressure = 0.0  # 0..1; the sleep drive itself
        self.awake = True     # the agent's claim; pressure has the last word
        self.debt = 0.0       # wake-seconds since pressure last hit 0
        self.last_discharge = 0.0  # cascade activation of the last rest()

    # ---- internal machinery ----

    def _cascade(self, injection):
        """[MODEL] Port of flysim.run(): inject at hop 0, spread 4 steps."""
        act = {nid: 0.0 for nid in self._nodes}
        for nid in self._inject_ids:
            act[nid] = injection
        snaps = [{nid: a for nid, a in act.items() if a >= THRESHOLD}]
        for _ in range(STEPS):
            incoming = defaultdict(float)
            fired = {nid for nid, a in act.items() if a >= THRESHOLD}
            for pre, post, w in self._norm:
                if pre in fired:
                    incoming[post] += act[pre] * w
            act = {nid: incoming.get(nid, 0.0) for nid in self._nodes}
            snaps.append({nid: a for nid, a in act.items()
                          if a >= THRESHOLD})
        return snaps

    def _terminal(self, snaps):
        """[REAL/TOY] Max activation over the readout-hop nodes, all steps."""
        peak = 0.0
        for snap in snaps:
            for nid in self._readout_ids:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    # ---- public API ----

    def tick(self, dt):
        """[MODELED] Advance pressure by dt seconds of wakefulness.

        Pressure accumulates only while awake. dt is explicit (seconds),
        so the harness and track CLI are deterministic without a clock.
        """
        dt = max(0.0, dt)
        if self.awake and dt > 0:
            self._pressure = min(1.0, self._pressure + RATE_UP * dt)
            self.debt += dt
        return self.state()

    def rest(self, dt):
        """[MODELED] Rest for dt seconds: discharge pressure, run the cascade.

        The injection into dFB is scaled by the pressure actually
        discharged this call (0..1). Returns {activation, depth, pressure}:
        activation is the cascade readout on the REAL wiring, depth is how
        much pressure left. While resting, awake=False.
        """
        dt = max(0.0, dt)
        self.awake = False
        discharged = min(self._pressure, RATE_DOWN * dt)
        self._pressure = max(0.0, self._pressure - discharged)
        if self._pressure <= 0.0:
            self.debt = 0.0  # fully rested: the ledger clears [MODELED]
        activation = self._terminal(self._cascade(discharged))
        self.last_discharge = activation
        return {
            "activation": round(activation, 4),
            "depth": round(discharged, 4),
            "pressure": round(self._pressure, 4),
            "asleep": self.asleep(),
        }

    def wake(self):
        """[MODELED] The agent declares itself awake.

        Note: this does NOT clear pressure. If pressure >= threshold the
        module still reports asleep=True — the homeostat overrides the
        agent's claim. That override is the point of a sleep drive.
        """
        self.awake = True
        return self.state()

    def pressure(self):
        """Current sleep pressure, 0..1."""
        return round(self._pressure, 4)

    def asleep(self):
        """[MODELED] True when pressure crosses the onset threshold."""
        return self._pressure >= SLEEP_THRESHOLD

    def state(self):
        """Current drive state."""
        return {
            "pressure": round(self._pressure, 4),
            "asleep": self.asleep(),
            "awake_claim": self.awake,
            "debt_secs": round(self.debt, 1),
            "last_discharge": round(self.last_discharge, 4),
            "sleep_threshold": SLEEP_THRESHOLD,
        }
