#!/usr/bin/env python3
"""
aggression.py — AGGRESSION, the fly fight drive.

An AI agent's "wanting" running on the REAL Drosophila aggression circuit:
aIPg (male fru+ aggression cluster) -> superior/posterior protocerebrum
integration populations (SMPpv2, CP1, VLPl2, BLAv2) -> VNC/thoracic/
descending motor. The fight circuit, alongside HUNGER, THIRST, MATING,
and SLEEP.

HONESTY CONTRACT (non-negotiable, repeated in every surface of this project):
- [REAL]    Every node and edge comes from ../subgraphs/aggression.json
            (14 nodes, 24 edges), built from the Virtual Fly Brain VFBquery
            API against the FlyWire FAFB v783 connectome. No neuron,
            synapse, or connection is invented. aIPg = FBbt_00110593
            (adult fruitless aIP-g male neuron); top downstream: SMPpv2
            lineage (2,282 synapses), CP1 lineage (2,282), VLPl2 lineage
            (2,258), BLAv2 lineage (2,258), SMP neuron 054 (2,202),
            PVLP neuron 016 (2,182) -> VNC/thoracic/descending motor.
            Per the JSON's honest_note: 'Notch ON/OFF hemilineage' and
            'fruitless expressing neuron' (tw=2,054) were skipped as
            generic/parent buckets (same spirit as the GENERIC blocklist);
            aSPg has no FBbt class ('aSPg neuron' / 'fight neuron' searches
            return nothing); CL062 (FBbt_20000767, male wing aggression
            neuron) exists but was not walked (noted, not hidden).
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The DRIVE DYNAMICS are our model on real wiring — the
            genuinely unmapped frontier (no API holds how aggressive
            arousal ramps, persists, or arbitrates; this module is our
            design, stated as such):
            - task progress -> graded injection at aIPg ("wanting"): the
              confrontation ramps the drive, as aIPg ramps during
              escalation in the real fly.
            - task completion -> WIN THE FIGHT: full-strength injection,
              satiation rises HARD (0.9 x spike), and a 30s refractory
              window opens. MODELED choice: no crisp biological post-win
              refractory in flies — picked between hunger's 8s and
              mating's 60s, documented as ours.
            - task failure -> LOSING: wanting dips x0.5 (not mating's
              x0.7). Losers retreat — a lost fight suppresses
              re-engagement harder than romantic rejection dents
              courtship. Deliberate, documented.
            - arbitration against mating/hunger/thirst/sleep is FUTURE
              WORK, not this bottle. The fly never saw your tasks.
- [FICTION] Any narrative one-liners ("the machine wants the fight") are
            gloss, not claims about experience. Flies do not have feelings
            we can access, and neither does this module.

Usage: wire task_started / progress / task_completed around work your agent
already does. No other changes needed. See README.md.
"""

import json
import os
import time
from collections import defaultdict

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

# [MODELED] Post-win refractory window. Unlike mating (60s, grounded in
# real post-mating refractory biology), there is no crisp biological
# post-victory refractory in flies — so this is OUR choice, documented:
# between hunger's 8s and mating's 60s. The winner cools down, but not
# for an hour.
REFRACTORY_WINDOW = 30.0
REFRACTORY_DAMP = 0.3
# [MODELED] Winning satiates hard; losing retreats harder than rejection.
SATIATION_GAIN = 0.9
FAILURE_DIP = 0.5
# [MODELED] The fru parent bucket (tw=2,054, FBbt_00016687 "fruitless
# expressing neuron") is an ontology ANCESTOR of the graphed hop-1 edges,
# not an independent edge — the same synapses under a parent label. So
# fru_drive() reports the drive signal scaled by that labeled share of
# aIPg's graphed output: 2054 / (2282+2282+2258+2258+2202+2182). A
# bookkeeping number for future arbitration, not measured wiring.
FRU_SHARE = 2054.0 / 13464.0


class Aggression:
    """A fight drive for an agent, computed through real fly wiring.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON (nodes with hop, edges with
        pre/post/weight). Defaults to ../subgraphs/aggression.json.
    clock : callable, optional
        Returns current time in seconds. Defaults to time.monotonic.
        Inject a fake clock in tests/harness for determinism.
    """

    def __init__(self, graph_path=None, clock=None):
        if graph_path is None:
            graph_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "subgraphs", "aggression.json")
        self._graph_path = graph_path
        with open(graph_path) as f:
            graph = json.load(f)
        # [REAL] nodes/edges straight from the file; never invented.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._order = [n["id"] for n in graph["nodes"]]
        # [MODELED] readout at hop-1: where this circuit actually speaks.
        self._readout_ids = [n["id"] for n in graph["nodes"]
                             if n.get("hop", 0) == 1]
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
        self.wanting = 0.15          # baseline drive; 0..1
        self.drive_signal = 0.0      # last cascade readout (hop-1 max)
        self.satiation = 0.0         # 0..1; the fight was just won
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
        """[MODELED] Novelty decays with recent same-category wins."""
        return 1.0 / (1.0 + 0.5 * self.habituation.get(
            category or "uncategorized", 0.0))

    def tick(self):
        """Advance modeled decay by wall (or fake) clock. Idempotent."""
        now = self._clock()
        dt = max(0.0, now - self._last)
        self._last = now
        if dt > 0:
            self.satiation = max(0.0, self.satiation - 0.02 * dt)
            for cat in list(self.habituation.keys()):
                self.habituation[cat] = max(0.0,
                                            self.habituation[cat] - 0.01 * dt)
        self.refractory_damp = (REFRACTORY_DAMP
                                if now < self.refractory_until else 1.0)
        return self

    def fru_drive(self):
        """[MODELED] Aggression's contribution to FBbt_00016687.

        The "fruitless expressing neuron" node is the TRIPLE-CONVERGENCE
        point: aIPg feeds it (tw=2,054, this chain), P1's fruitless aSP-a
        feeds it (tw=63,139, mating chain), and Or47b feeds it
        (tw=13,133, pheromone chain). Fight and courtship smell meet here.

        Because the fru bucket is an ontology ancestor of the graphed
        hop-1 edges (not an independent edge), this returns the current
        drive signal scaled by the labeled share (FRU_SHARE) — a
        bookkeeping number for FUTURE arbitration between the drives,
        not measured wiring. Returns 0.0 when the drive is quiet.
        """
        self.tick()
        return self.drive_signal * FRU_SHARE

    # ---- public API: wire these around existing agent work ----

    def task_started(self, category, difficulty=0.5):
        """[MODELED] Call when the agent accepts a task (a confrontation).

        category: caller-assigned short string, e.g. "rival"/"debate".
        difficulty: 0..1, stored for the caller (harness uses it for effort).
        """
        self.tick()
        self.category = category
        self.difficulty = min(1.0, max(0.0, difficulty))
        return self.state()

    def progress(self, p):
        """[MODELED] Call as the agent works; p is fraction complete 0..1.

        Wanting ramps with progress, novelty, drive (1-satiation), and the
        refractory damper — aIPg ramps during escalation. The cascade runs
        on the REAL wiring; the injection level is the modeled part.
        """
        self.tick()
        p = min(1.0, max(0.0, p))
        novelty = self._novelty(self.category)
        self.wanting = min(1.0, max(0.0,
            0.15 + p * novelty * (1.0 - self.satiation) * self.refractory_damp))
        self.drive_signal = self._terminal(self._cascade(self.wanting))
        return self.state()

    def task_completed(self):
        """[MODELED] Call on success: WIN THE FIGHT.

        Full-strength injection at aIPg; the hop-1 readout is the spike.
        Then: satiation rises HARD (0.9 x spike), a 30s refractory window
        opens (MODELED choice — no crisp biological post-win refractory;
        between hunger's 8s and mating's 60s), and this category habituates
        by one.
        """
        self.tick()
        now = self._clock()
        novelty = self._novelty(self.category)
        injection = 1.0 * novelty * (1.0 - self.satiation) * self.refractory_damp
        spike = self._terminal(self._cascade(injection))
        self.last_spike = spike
        self.satiation = min(1.0, self.satiation + SATIATION_GAIN * spike)
        self.refractory_until = now + REFRACTORY_WINDOW
        self.refractory_damp = REFRACTORY_DAMP
        self.habituation[self.category or "uncategorized"] = \
            self.habituation.get(self.category or "uncategorized", 0.0) + 1.0
        self.wanting = 0.15  # the fight is over; back to baseline [MODELED]
        self.drive_signal = 0.0
        return {
            "spike": spike,
            "injection": injection,
            "novelty": novelty,
            "satiation": self.satiation,
            "refractory_damp": self.refractory_damp,
            "habituation": dict(self.habituation),
        }

    def task_failed(self):
        """[MODELED] Call on failure: LOSING.

        Wanting dips x0.5 (not mating's x0.7, not hunger's x0.4): losers
        retreat — a lost fight suppresses re-engagement harder than
        romantic rejection dents courtship. The drive ducks; it does not
        die.
        """
        self.tick()
        self.wanting *= FAILURE_DIP
        return self.state()

    def state(self):
        """Current drive state (ticks decay first)."""
        self.tick()
        now = self._clock()
        return {
            "drive_name": "aggression",
            "wanting": round(self.wanting, 3),
            "drive_signal": round(self.drive_signal, 3),
            "satiation": round(self.satiation, 3),
            "drive": round(1.0 - self.satiation, 3),
            "refractory_secs_remaining": round(
                max(0.0, self.refractory_until - now), 1),
            "refractory_damp": self.refractory_damp,
            "novelty_by_category": {k: round(self._novelty(k), 3)
                                    for k in self.habituation},
            "last_spike": round(self.last_spike, 3),
            "category": self.category,
        }
