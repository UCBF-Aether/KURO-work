#!/usr/bin/env python3
"""
egglaying.py — EGG-LAYING, the fly oviposition drive.

An AI agent's "wanting" running on the REAL Drosophila egg-laying circuit:
oviDN (oviposition descending neurons) -> VNC/abdominal motor populations
+ ascending feedback + SEZ output -> thoracic/efferent motor neurons.
The sixth drive, alongside HUNGER, THIRST, MATING, SLEEP, and AGGRESSION.
FEMALE-SPECIFIC: oviDNs are female command neurons (males don't lay eggs).

HONESTY CONTRACT (non-negotiable, repeated in every surface of this project):
- [REAL]    Every node and edge comes from ../subgraphs/egglaying.json (11
            nodes, 20 edges), built from the Virtual Fly Brain VFBquery API
            against the FlyWire FAFB v783 connectome. No neuron, synapse, or
            connection is invented. oviDN = FBbt_00049919 (the 12-instance
            aggregate class of oviDNa/b/d/v/x); top downstream: adult VNC
            neuron (hop-1 peak 0.3401), abdominal neuron (0.3131), secondary
            neuron (0.1788). Per the JSON's honest_note: ID-form grouped
            queries truncate server-side (label form returned 421 real rows);
            oviDNa/b subtype queries are weak — the aggregate class carries
            the real signal; optic-lobe classes appearing as downstream of
            SEZ/brain classes are class-aggregation artifacts (skipped with
            documented reason, same family as the proprioception-build
            incident); INXXX052/INXXX257 are uncharacterized but real;
            secondary neuron FBbt_00047096 is an honest hop-1 terminal.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The DRIVE DYNAMICS are our model on real wiring — the genuinely
            unmapped frontier (no API holds egg-load-dependent ramping or the
            temporal patterning of deposition; the JSON's honest_note says so
            outright; this module is our design, stated as such):
            - egg load -> pressure: egg_load accumulates at 1.0 per 8 hours
              (a female matures a few egg loads per day; the timescale is our
              choice, documented). The load IS the drive — at zero load there
              is no urge, no matter how much "progress" is made.
            - progress -> deposition bouts: wanting = 0.15 + p x novelty x
              egg_load x (1-satiation) x refractory damper. A full load with
              no satiation and no damper yields wanting 1.0 at p=1.
            - task completion -> EGG DEPOSITED: full-strength injection at
              oviDN, satiation rises HARD (0.9 x spike), egg_load drops by
              one bout (0.5 of a full load), and a 30s refractory window
              opens (between hunger's 8s and mating's 60s — egg-laying
              happens in bouts with natural pauses; the timescale is toy).
            - task failure -> THWARTED DEPOSITION: wanting dips x0.9 (not
              hunger's x0.4, not mating's x0.7) — the eggs are still there,
              so the drive persists almost untouched. Deliberate, documented.
            - arbitration against the other drives is FUTURE WORK, not this
              bottle.
- [FICTION] Any narrative one-liners ("the machine wants to lay eggs") are
            gloss, not claims about experience. Flies do not have feelings we
            can access, and neither does this module.

Usage: wire task_started / progress / task_completed around work your agent
already does. No other changes needed. See README.md.
"""

import json
import os
import time
from collections import defaultdict

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

# [MODELED] Post-deposition refractory: egg-laying happens in bouts with
# natural pauses (biology). The 30s timescale is toy — hunger's 8s is too
# short for bouts, mating's 60s too long; this one sits between.
REFRACTORY_WINDOW = 30.0
REFRACTORY_DAMP = 0.3
# [MODELED] A deposition bout satiates hard; a thwarted one barely dents
# (the eggs are still there — the drive persists almost untouched).
SATIATION_GAIN = 0.9
FAILURE_DIP = 0.9
# [MODELED] Egg-load accumulation: a full load (1.0) matures per 8 hours.
# A female fly lays on the order of tens of eggs per day; the timescale is
# our choice, stated as such. Pressure gates the whole drive.
EGG_LOAD_RATE = 1.0 / (8 * 3600)   # per second
# [MODELED] One deposition bout empties half a full load.
DEPOSITION_SIZE = 0.5


class Egglaying:
    """An egg-laying drive for an agent, computed through real fly wiring.

    Female-specific: oviDNs are female oviposition command neurons.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON (nodes with hop, edges with
        pre/post/weight). Defaults to ../subgraphs/egglaying.json.
    clock : callable, optional
        Returns current time in seconds. Defaults to time.monotonic.
        Inject a fake clock in tests/harness for determinism.
    """

    def __init__(self, graph_path=None, clock=None):
        if graph_path is None:
            graph_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "subgraphs", "egglaying.json")
        self._graph_path = graph_path
        with open(graph_path) as f:
            graph = json.load(f)
        # [REAL] nodes/edges straight from the file; never invented.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._order = [n["id"] for n in graph["nodes"]]
        # [MODELED] readout at hop-2 (deepest-hop convention): the thoracic
        # neuron peak 0.2311 at full injection carries the graded signal.
        self._readout_ids = [n["id"] for n in graph["nodes"]
                             if n.get("hop", 0) == 2]
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

        # [MODELED] drive state around the real cascade
        self.egg_load = 0.0          # 0..1; the pressure that IS the drive
        self.wanting = 0.15          # baseline; 0..1
        self.drive_signal = 0.0      # last cascade readout (hop-2 max)
        self.satiation = 0.0         # 0..1; just deposited
        self.habituation = defaultdict(float)  # category -> count
        self.refractory_until = 0.0  # clock time; damp 0.3 while active
        self.last_spike = 0.0
        self.category = None
        self.difficulty = 0.0
        self.refractory_damp = 1.0

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

    def _novelty(self, category):
        """[MODELED] Novelty decays with recent same-category depositions."""
        return 1.0 / (1.0 + 0.5 * self.habituation.get(
            category or "uncategorized", 0.0))

    def tick(self):
        """Advance modeled decay and egg-load accumulation. Idempotent."""
        now = self._clock()
        dt = max(0.0, now - self._last)
        self._last = now
        if dt > 0:
            self.satiation = max(0.0, self.satiation - 0.02 * dt)
            for cat in list(self.habituation.keys()):
                self.habituation[cat] = max(0.0,
                                            self.habituation[cat] - 0.01 * dt)
            # [MODELED] Eggs mature: the load accumulates and gates the
            # whole drive. No eggs -> no urge.
            self.egg_load = min(1.0, self.egg_load + EGG_LOAD_RATE * dt)
        self.refractory_damp = (REFRACTORY_DAMP
                                if now < self.refractory_until else 1.0)
        return self

    # ---- public API: wire these around existing agent work ----

    def egg_pressure(self):
        """[MODELED] Current egg load (0..1) — the pressure that IS the drive."""
        self.tick()
        return self.egg_load

    def task_started(self, category, difficulty=0.5):
        """[MODELED] Call when the agent begins a deposition effort.

        category: caller-assigned short string, e.g. "ripe-fruit".
        difficulty: 0..1, stored for the caller.
        """
        self.tick()
        self.category = category
        self.difficulty = min(1.0, max(0.0, difficulty))
        return self.state()

    def progress(self, p):
        """[MODELED] Call as the agent works; p is fraction complete 0..1.

        Wanting ramps with progress, novelty, EGG LOAD, (1-satiation), and
        the refractory damper. The load is the gate: no eggs -> no urge.
        The cascade runs on the REAL wiring; the injection level is modeled.
        """
        self.tick()
        p = min(1.0, max(0.0, p))
        novelty = self._novelty(self.category)
        self.wanting = min(1.0, max(0.0,
            0.15 + p * novelty * self.egg_load * (1.0 - self.satiation)
            * self.refractory_damp))
        self.drive_signal = self._terminal(self._cascade(self.wanting))
        return self.state()

    def task_completed(self):
        """[MODELED] Call on a deposition bout: EGG DEPOSITED.

        Full-strength injection at oviDN; the hop-2 readout is the spike.
        Then: satiation rises HARD (0.9 x spike), egg_load drops by one bout
        (0.5 of a full load), a 30s refractory window opens (bout pauses are
        biology; the timescale is toy), and this category habituates by one.
        """
        self.tick()
        now = self._clock()
        novelty = self._novelty(self.category)
        injection = 1.0 * novelty * (1.0 - self.satiation) * self.refractory_damp
        spike = self._terminal(self._cascade(injection))
        self.last_spike = spike
        self.satiation = min(1.0, self.satiation + SATIATION_GAIN * spike)
        self.egg_load = max(0.0, self.egg_load - DEPOSITION_SIZE)
        self.refractory_until = now + REFRACTORY_WINDOW
        self.refractory_damp = REFRACTORY_DAMP
        self.habituation[self.category or "uncategorized"] = \
            self.habituation.get(self.category or "uncategorized", 0.0) + 1.0
        self.wanting = 0.15  # the bout is over; back to baseline [MODELED]
        self.drive_signal = 0.0
        return {
            "spike": spike,
            "injection": injection,
            "novelty": novelty,
            "satiation": self.satiation,
            "egg_load": self.egg_load,
            "refractory_damp": self.refractory_damp,
            "habituation": dict(self.habituation),
        }

    def task_failed(self):
        """[MODELED] Call on a thwarted deposition.

        Wanting dips x0.9 — the eggs are still there, so the drive persists
        almost untouched. Deliberate, documented.
        """
        self.tick()
        self.wanting *= FAILURE_DIP
        return self.state()

    def state(self):
        """Current drive state (ticks decay and load accumulation first)."""
        self.tick()
        now = self._clock()
        return {
            "drive_name": "egglaying",
            "sex": "female",  # oviDNs are female command neurons [REAL]
            "wanting": round(self.wanting, 3),
            "drive_signal": round(self.drive_signal, 3),
            "egg_load": round(self.egg_load, 3),
            "satiation": round(self.satiation, 3),
            "drive": round(self.egg_load * (1.0 - self.satiation), 3),
            "refractory_secs_remaining": round(
                max(0.0, self.refractory_until - now), 1),
            "refractory_damp": self.refractory_damp,
            "novelty_by_category": {k: round(self._novelty(k), 3)
                                    for k in self.habituation},
            "last_spike": round(self.last_spike, 3),
            "category": self.category,
        }
