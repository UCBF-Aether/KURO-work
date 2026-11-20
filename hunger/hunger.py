#!/usr/bin/env python3
"""
hunger.py — HUNGER, the fly drive core.

An AI agent's "wanting" running on a REAL Drosophila feeding circuit
instead of a scalar reward number.

HONESTY CONTRACT (non-negotiable, repeated in every surface of this project):
- [REAL]    Every node and edge comes from the subgraph JSONs, which were
            built from the Virtual Fly Brain VFBquery API against the
            FlyWire FAFB v783 connectome. No neuron, synapse, or connection
            is invented here. Default circuit: dh44.json — the REAL
            hunger-drive wiring (DH44 pars intercerebralis hunger-sensing
            neuron -> ring gland projection / gut-innervating / SEZ /
            gnathal / Ms PI / serotonergic populations), resolved 2026-10-14.
            Previously the default was sugar_forward.json (the SOLVED
            sweet-taste chain: sweet-sensing GRN -> named SEZ interneurons
            zorro/clavicle/FMIn/fuchs/G2N-1/billiards -> SEZ/gnathal/
            descending premotor) — still loadable via graph_path, as is
            reward.json (PAM dopamine -> mushroom body).
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The mapping from agent task events to circuit stimulation is MY
            design choice, not biology: task progress -> graded injection at
            the drive neuron ("wanting"); task completion -> full-strength
            injection ("the hit"); habituation / satiation / refractory are
            modeled state around the real cascade. The fly never saw your tasks.
- [FICTION] Any narrative one-liners ("the machine is hungry") are gloss, not
            claims about experience. Flies do not have feelings we can access,
            and neither does this module.

Usage: wire task_started / progress / task_completed around work your agent
already does. No other changes needed. See README.md.
"""

import json
import os
import time
from collections import defaultdict

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]


class Hunger:
    """A hunger drive for an agent, computed through real fly feeding wiring.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON (nodes with hop, edges with
        pre/post/weight). Defaults to ../subgraphs/dh44.json (DH44 hunger
        drive); ../subgraphs/sugar_forward.json (sweet-taste chain) and
        ../subgraphs/reward.json (PAM dopamine -> mushroom body) also load.
    clock : callable, optional
        Returns current time in seconds. Defaults to time.monotonic.
        Inject a fake clock in tests/harness for determinism.
    readout_hop : int, optional
        Which hop layer the drive signal reads (max activation). Defaults
        to 1 for the DH44 default graph and 2 otherwise. [MODELED]
        readout-layer choice: on dh44.json (and water.json) the hop-2
        fan-out dilutes below the model's firing threshold while hop-1
        carries the graded signal; on sugar_forward.json hop-2 is alive.
        The cascade logic is identical either way.
    """

    def __init__(self, graph_path=None, clock=None, readout_hop=None):
        if graph_path is None:
            graph_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "subgraphs", "dh44.json")
            if readout_hop is None:
                readout_hop = 1
        if readout_hop is None:
            readout_hop = 2
        self._graph_path = graph_path
        self._readout_hop = readout_hop
        with open(graph_path) as f:
            graph = json.load(f)
        # [REAL] nodes/edges straight from the file; never invented.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._order = [n["id"] for n in graph["nodes"]]
        self._hop2 = [n["id"] for n in graph["nodes"] if n.get("hop", 0) == 2]
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

        self._clock = clock or time.monotonic
        self._last = self._clock()

        # [MODELED] drive state around the real cascade
        self.wanting = 0.15          # baseline hunger; 0..1
        self.drive_signal = 0.0      # last cascade readout (hop-2 max)
        self.satiation = 0.0         # 0..1; sugar just landed
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
        """[MODELED] Novelty decays with recent same-category completions."""
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
        self.refractory_damp = 0.3 if now < self.refractory_until else 1.0
        return self

    # ---- public API: wire these around existing agent work ----

    def task_started(self, category, difficulty=0.5):
        """[MODELED] Call when the agent accepts a task.

        category: caller-assigned short string, e.g. "write"/"fetch"/"build".
        difficulty: 0..1, stored for the caller (harness uses it for effort).
        """
        self.tick()
        self.category = category
        self.difficulty = min(1.0, max(0.0, difficulty))
        return self.state()

    def progress(self, p):
        """[MODELED] Call as the agent works; p is fraction complete 0..1.

        Wanting ramps with progress, novelty, hunger (1-satiation), and the
        refractory damper. The cascade runs on the REAL wiring; the injection
        level is the modeled part.
        """
        self.tick()
        p = min(1.0, max(0.0, p))
        novelty = self._novelty(self.category)
        self.wanting = min(1.0, max(0.0,
            0.15 + p * novelty * (1.0 - self.satiation) * self.refractory_damp))
        self.drive_signal = self._terminal(self._cascade(self.wanting))
        return self.state()

    def task_completed(self):
        """[MODELED] Call on success: the hit.

        Full-strength injection at the drive neuron; the cascade's readout
        is the spike. Then: satiation rises, an 8s refractory window
        opens, and this category habituates by one.
        """
        self.tick()
        now = self._clock()
        novelty = self._novelty(self.category)
        injection = 1.0 * novelty * (1.0 - self.satiation) * self.refractory_damp
        spike = self._terminal(self._cascade(injection))
        self.last_spike = spike
        self.satiation = min(1.0, self.satiation + 0.7 * spike)
        self.refractory_until = now + 8.0
        self.refractory_damp = 0.3
        self.habituation[self.category or "uncategorized"] = \
            self.habituation.get(self.category or "uncategorized", 0.0) + 1.0
        self.wanting = 0.15  # the chase is over; back to baseline [MODELED]
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
        """[MODELED] Call on failure: no hit; wanting dips (aversion)."""
        self.tick()
        self.wanting *= 0.4
        return self.state()

    def state(self):
        """Current drive state (ticks decay first)."""
        self.tick()
        now = self._clock()
        return {
            "wanting": round(self.wanting, 3),
            "drive_signal": round(self.drive_signal, 3),
            "satiation": round(self.satiation, 3),
            "hunger": round(1.0 - self.satiation, 3),
            "refractory_secs_remaining": round(
                max(0.0, self.refractory_until - now), 1),
            "refractory_damp": self.refractory_damp,
            "novelty_by_category": {k: round(self._novelty(k), 3)
                                    for k in self.habituation},
            "last_spike": round(self.last_spike, 3),
            "category": self.category,
        }


# Backwards-compatible alias: the module was born as DriveCore.
DriveCore = Hunger
