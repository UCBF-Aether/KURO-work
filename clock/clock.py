#!/usr/bin/env python3
"""
clock.py — CLOCK, the fly's sense of time.

A circadian state module running on REAL Drosophila clock wiring: the LNv
pacemaker neurons (PDF master pacemaker) -> pacemaker, SLPpl1, visual
neuropil, accessory medulla, DN period, and lateral-horn populations.

HONESTY CONTRACT (non-negotiable, repeated in every surface of this project):
- [REAL]    Every node and edge comes from ../subgraphs/clock.json, built
            from the Virtual Fly Brain VFBquery API against the FlyWire
            FAFB v783 connectome (LNv FBbt_00004046 -> 6 hop-1 classes by
            synapse weight; s-LNv/l-LNv subclasses unindexed — recorded in
            the JSON's honest_note, not hidden). No neuron, synapse, or
            connection is invented here.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The circadian phase is MY model, not biology. The REAL 24-hour
            molecular oscillator (per/tim feedback loops, PDF cycling,
            phase-response) is the genuinely unmapped frontier; no API
            holds it. Here: phase is continuous state in [0, 1), advancing
            dt/86400 per tick (phase 0 = dawn, 0.5 = dusk); the PDF-output
            curve pdf = max(0, sin(2*pi*phase)) is a stand-in — real PDF
            peaks near dawn and is driven by the molecular clock, whereas
            this curve peaks at mid-day and is just a smooth day/night
            envelope; night is DEFINED as phase in [0.5, 1.0), a convention,
            not a finding. The cascade injection scales with pdf, so the
            LNv wiring fires hardest at mid-day and goes quiet at night —
            the coupling of phase to wiring is modeled; the wiring it
            drives is real.
- [FICTION] Any narrative one-liners ("dawn lives here") are gloss, not
            claims about experience.

This is a STATE module, not a drive or a sense: it holds time, the way the
compass holds heading and the other bottles hold wanting or activation.
Combine: tick() the clock alongside everything else; read is_night() to
gate sleep pressure, time_of_day() to schedule feeding.
"""

import json
import math
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]
SECONDS_PER_DAY = 86400.0  # [MODELED] the period we pin phase to


class Clock:
    """A circadian state module on real LNv clock wiring.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON (nodes with hop, edges with
        pre/post/weight). Defaults to ../subgraphs/clock.json.
    """

    def __init__(self, graph_path=None):
        if graph_path is None:
            graph_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "subgraphs", "clock.json")
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

        # [MODELED] circadian state; phase 0 = dawn.
        self._phase = 0.0        # in [0, 1)
        self.activation = 0.0    # last cascade readout (hop-1 peak)
        self.pdf = 0.0           # last PDF-output value [MODELED]

    # ---- internal machinery ----

    def _cascade(self, injection):
        """[MODEL] Port of flysim.run(): inject at hop 0 (LNv), spread 4 steps."""
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
        as the compass and pain bottles.
        """
        peak = 0.0
        for snap in snaps:
            for nid in self._readout_ids:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    @staticmethod
    def _pdf_curve(phase):
        """[MODELED] PDF-output envelope: max(0, sin(2*pi*phase)).

        0 at dawn, 1 at mid-day (phase 0.25), 0 at dusk, 0 through the
        night half. A smooth day/night envelope — NOT the real PDF
        cycle, which peaks near dawn under molecular-clock control.
        """
        return max(0.0, math.sin(2.0 * math.pi * phase))

    # ---- public API ----

    def tick(self, dt_seconds):
        """[MODELED] Advance the circadian phase by dt/86400 of a day.

        Runs the model cascade on the REAL LNv wiring with injection scaled
        by the modeled PDF-output curve at the new phase — the LNv chain
        fires hardest at mid-day and goes quiet at night.
        """
        self._phase = (self._phase + dt_seconds / SECONDS_PER_DAY) % 1.0
        self.pdf = self._pdf_curve(self._phase)
        self.activation = self._readout(self._cascade(self.pdf))
        return {
            "activation": round(self.activation, 4),
            "phase": round(self._phase, 4),
            "pdf": round(self.pdf, 4),
        }

    def phase(self):
        """Current circadian phase in [0, 1). Phase 0 = dawn, 0.5 = dusk."""
        return self._phase

    def time_of_day(self):
        """Hours since dawn [0, 24). 6.0 = mid-day, 12.0 = dusk."""
        return self._phase * 24.0

    def is_night(self):
        """True when phase is in the night half [0.5, 1.0). [MODELED]."""
        return self._phase >= 0.5

    def state(self):
        """Current clock state: phase, pdf, last cascade activation."""
        return {
            "phase": round(self._phase, 4),
            "pdf": round(self.pdf, 4),
            "activation": round(self.activation, 4),
        }
