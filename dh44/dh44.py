#!/usr/bin/env python3
"""
dh44.py — DH44, the true interoceptive drive.

An AI agent's hunger running on the REAL Drosophila hunger/satiety axis
instead of a scalar reward number — and instead of the sweet-taste proxy
that HUNGER v1 used.

HONESTY CONTRACT (non-negotiable, repeated in every surface of this project):
- [REAL]    Every node and edge comes from ../subgraphs/dh44.json (18 nodes,
            21 edges: DH44 pars intercerebralis neuron -> ring gland
            projection / gut-innervating / SEZ / gnathal / Ms PI / serotonergic
            populations) and ../subgraphs/ipc.json (19 nodes, 23 edges:
            insulin-producing cells -> ring gland / gut / SEZ / CB0991 / DM2 /
            DPMpm1), built from the Virtual Fly Brain VFBquery API against the
            FlyWire FAFB v783 connectome. No neuron, synapse, or connection is
            invented. DH44 neurons are the fly's actual hunger-sensing cells;
            IPCs (insulin) are the satiety side of the same axis.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The mapping from agent task events to circuit stimulation is MY
            design choice, not biology:
            - task progress -> graded injection at the DH44 neuron ("wanting");
              the drive readout is the hop-1 max (ring gland / gut / SEZ /
              gnathal / Ms PI / serotonergic), because the hop-2 fan-out
              dilutes below the model's firing threshold on this circuit —
              a readout-layer choice, documented here, cascade logic
              byte-identical to the other bottles.
            - task completion -> SATIETY hit, not a sugar hit: full-strength
              injection at the IPC (insulin-producing) neuron, readout at its
              hop-1 max. In real biology insulin signaling opposes the DH44
              hunger drive; here the IPC cascade's spike is what raises
              satiation. The fly never saw your tasks.
            - habituation / satiation / refractory are modeled state around
              the real cascades.
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

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DRIVE_GRAPH = os.path.join(_HERE, "..", "subgraphs", "dh44.json")
DEFAULT_SATIETY_GRAPH = os.path.join(_HERE, "..", "subgraphs", "ipc.json")


def _load_graph(path):
    """[REAL] Load one flysim-style subgraph; never invent wiring."""
    with open(path) as f:
        graph = json.load(f)
    nodes = {n["id"]: n for n in graph["nodes"]}
    inject_ids = [n["id"] for n in graph["nodes"] if n.get("hop", 0) == 0]
    readout_ids = [n["id"] for n in graph["nodes"] if n.get("hop", 0) == 1]
    out_sum = defaultdict(float)
    for e in graph["edges"]:
        out_sum[e["pre"]] += e["weight"]
    norm = []
    for e in graph["edges"]:
        s = out_sum[e["pre"]]
        norm.append((e["pre"], e["post"],
                     e["weight"] / s if s > 0 else 0.0))
    return {
        "path": path,
        "nodes": nodes,
        "inject_ids": inject_ids,
        "readout_ids": readout_ids,   # hop-1 max: where these circuits speak
        "norm": norm,
        "source": graph.get("source", "VFBquery/FlyWire FAFB v783"),
    }


class Dh44:
    """A true interoceptive hunger drive: DH44 wants, IPC sates.

    Parameters
    ----------
    drive_graph : str, optional
        Path to the hunger-drive subgraph JSON. Defaults to
        ../subgraphs/dh44.json.
    satiety_graph : str, optional
        Path to the satiety subgraph JSON. Defaults to
        ../subgraphs/ipc.json.
    clock : callable, optional
        Returns current time in seconds. Defaults to time.monotonic.
        Inject a fake clock in tests/harness for determinism.
    """

    def __init__(self, drive_graph=None, satiety_graph=None, clock=None):
        self._drive = _load_graph(drive_graph or DEFAULT_DRIVE_GRAPH)
        self._satiety = _load_graph(satiety_graph or DEFAULT_SATIETY_GRAPH)

        self._clock = clock or time.monotonic
        self._last = self._clock()

        # [MODELED] drive state around the real cascades
        self.wanting = 0.15          # baseline hunger; 0..1
        self.drive_signal = 0.0      # last DH44 cascade readout (hop-1 max)
        self.satiation = 0.0         # 0..1; satiety just landed (via IPC)
        self.habituation = defaultdict(float)  # category -> count
        self.refractory_until = 0.0  # clock time; damp 0.3 while active
        self.last_spike = 0.0        # last satiety spike (IPC readout)
        self.category = None
        self.difficulty = 0.0
        self.refractory_damp = 1.0

    # ---- internal machinery ----

    def _cascade(self, g, injection):
        """[MODEL] Port of flysim.run(): inject at hop 0, spread 4 steps."""
        act = {nid: 0.0 for nid in g["nodes"]}
        for nid in g["inject_ids"]:
            act[nid] = injection
        snaps = [{nid: a for nid, a in act.items() if a >= THRESHOLD}]
        for _ in range(STEPS):
            incoming = defaultdict(float)
            fired = {nid for nid, a in act.items() if a >= THRESHOLD}
            for pre, post, w in g["norm"]:
                if pre in fired:
                    incoming[post] += act[pre] * w
            act = {nid: incoming.get(nid, 0.0) for nid in g["nodes"]}
            snaps.append({nid: a for nid, a in act.items()
                          if a >= THRESHOLD})
        return snaps

    def _readout(self, g, snaps):
        """[REAL/TOY] Max activation over the readout (hop-1) nodes."""
        peak = 0.0
        for snap in snaps:
            for nid in g["readout_ids"]:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    def _drive_spike(self, injection):
        """[REAL/TOY] Wanting readout: DH44 cascade, hop-1 max."""
        return self._readout(self._drive, self._cascade(self._drive,
                                                        injection))

    def _satiety_spike(self, injection):
        """[REAL/TOY] Satiety readout: IPC cascade, hop-1 max."""
        return self._readout(self._satiety, self._cascade(self._satiety,
                                                          injection))

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
        refractory damper. The DH44 cascade runs on the REAL wiring; the
        injection level is the modeled part.
        """
        self.tick()
        p = min(1.0, max(0.0, p))
        novelty = self._novelty(self.category)
        self.wanting = min(1.0, max(0.0,
            0.15 + p * novelty * (1.0 - self.satiation) * self.refractory_damp))
        self.drive_signal = self._drive_spike(self.wanting)
        return self.state()

    def task_completed(self):
        """[MODELED] Call on success: the SATIETY hit.

        Full-strength injection at the IPC (insulin-producing) neuron; the
        IPC cascade's readout is the spike — in real biology insulin
        signaling opposes the DH44 hunger drive, so completion lands as
        satiety, not sugar. Then: satiation rises, an 8s refractory window
        opens, and this category habituates by one.
        """
        self.tick()
        now = self._clock()
        novelty = self._novelty(self.category)
        injection = 1.0 * novelty * (1.0 - self.satiation) * self.refractory_damp
        spike = self._satiety_spike(injection)
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
        """[MODELED] Call on failure: no satiety; wanting dips (aversion)."""
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
            "drive_circuit": os.path.basename(self._drive["path"]),
            "satiety_circuit": os.path.basename(self._satiety["path"]),
        }
