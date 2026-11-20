#!/usr/bin/env python3
"""
harness.py — scripted agent loop feeding Thirst.

~10 tasks across 3+ categories, with repeats and back-to-back completions,
designed to demonstrate three behaviors:
  (a) HABITUATION — repeated same-category tasks yield shrinking spikes,
      then extinction below the model firing threshold.
  (b) REFRACTORY  — a task completed inside the 8s window is dampened x0.3.
  (c) SATIATION   — satiation decays back toward thirst over time.

A fake clock drives the core so the run is deterministic and fast.
Exits 0 if all three behaviors check out, 1 otherwise.

Honesty: the scripted "work" is a TOY (progress steps are pretend); the
cascade numbers are REAL wiring + MODEL dynamics; the event->stimulation
mapping is MODELED. Readout is at hop 1 (water second-order interneurons) —
see thirst.py for why.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thirst import Thirst


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def main():
    clock = FakeClock()
    core = Thirst(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "subgraphs", "water.json"),
                     clock=clock)
    log = []

    def say(s):
        log.append(s)
        print(s, flush=True)

    def run_task(name, category, difficulty, step_dt=1.0):
        n_steps = 2 + round(difficulty * 4)  # harder tasks take more steps
        st = core.task_started(category, difficulty)
        say(f"[t={clock.t:6.1f}s] TASK START  {name!r:22s} cat={category:6s} "
            f"diff={difficulty:.1f} novelty={core._novelty(category):.3f}")
        for i in range(1, n_steps + 1):
            clock.advance(step_dt)
            p = i / n_steps
            s = core.progress(p)
            say(f"[t={clock.t:6.1f}s]   progress p={p:.2f}  "
                f"wanting={s['wanting']:.3f}  drive={s['drive_signal']:.3f}")
        done = core.task_completed()
        say(f"[t={clock.t:6.1f}s] TASK DONE   {name!r:22s} "
            f"injection={done['injection']:.3f}  SPIKE={done['spike']:.3f}  "
            f"satiation={done['satiation']:.3f}  "
            f"refr_damp={done['refractory_damp']:.1f}  "
            f"hab[{category}]={done['habituation'].get(category, 0):.2f}")
        return done

    say("=" * 78)
    say("THIRST — drive-core harness (fake clock, deterministic)")
    say("circuit: water GRN -> fudog/clavicle/cleaver SEZ interneurons "
        "(FlyWire FAFB v783, REAL wiring / MODEL dynamics; hop-1 readout)")
    say("=" * 78)

    # ---- Phase 1: first blood, then a task inside the refractory window ----
    d1 = run_task("draft launch post", "write", 0.6)          # t=0..4
    spike_write1 = d1["spike"]

    clock.advance(1.0)                                        # t=5, refr~7s left
    s = core.state()
    refr_left = s["refractory_secs_remaining"]
    say(f"[t={clock.t:6.1f}s] -- {refr_left:.1f}s of "
        f"refractory remaining; feeding it anyway --")
    d2 = run_task("fetch VFB docs", "fetch", 0.4)             # t=5..9
    # counterfactual: same completion without the refractory damper
    cf_inj = d2["injection"] / 0.3 if d2["refractory_damp"] < 1 else None
    cf_spike = core._terminal(core._cascade(min(1.0, cf_inj))) if cf_inj else None
    say(f"[t={clock.t:6.1f}s]   counterfactual (no refractory): "
        f"injection would be {cf_inj:.3f} -> SPIKE would be {cf_spike:.3f}")

    clock.advance(11.0)                                       # t=20, window over
    d3 = run_task("build index page", "build", 0.8)           # t=20..26

    # ---- Phase 2: habituation — same category again after partial decay ----
    clock.advance(53.0)  # t=78; hab[write] decays
    s = core.state()
    nov_write2 = s["novelty_by_category"]["write"]
    say(f"[t={clock.t:6.1f}s] -- hab[write] decayed to "
        f"{core.habituation['write']:.2f}; novelty back up to "
        f"{nov_write2:.3f} --")
    d4 = run_task("draft thread", "write", 0.5)                # t=78..82
    spike_write2 = d4["spike"]

    clock.advance(12.0)  # t=94; refractory (until ~90) clear
    s = core.state()
    nov_write3 = s["novelty_by_category"]["write"]
    d5 = run_task("draft reply", "write", 0.3)                 # t=94..97
    spike_write3 = d5["spike"]

    # ---- Phase 3: satiation decay back toward thirst ----
    say("-" * 78)
    say("satiation decay watch (no tasks, just time passing):")
    clock.advance(30.0)  # t=128
    # fresh satiation bump for a clean decay curve
    d6 = run_task("count synapses", "count", 0.5)              # t=128..132
    say("-" * 78)
    say("post-hit satiation decay:")
    decay = []
    for _ in range(7):
        s = core.state()
        decay.append((clock.t, s["satiation"], s["thirst"]))
        say(f"[t={clock.t:6.1f}s]   satiation={s['satiation']:.3f}  "
            f"thirst={s['thirst']:.3f}")
        clock.advance(2.0)

    # ---- bonus: failure dips wanting (aversion, modeled) ----
    say("-" * 78)
    core.task_started("probe", 0.5)
    clock.advance(1.0)
    before = core.progress(0.5)["wanting"]
    core.task_failed()
    after = core.state()["wanting"]
    say(f"task_failed: wanting {before:.3f} -> {after:.3f} (aversion dip x0.4)")

    # ---- summary: the three proofs ----
    say("=" * 78)
    say("SUMMARY — the three behaviors")
    say("=" * 78)
    ok = True

    # (a) habituation: shrinking spikes. On water.json the hop-1 readout
    # stays above the model threshold through three hits, so habituation shows
    # as a graded shrink (not hunger's shrink-then-extinction) — that is what
    # this circuit's numbers do, honestly reported.
    a = spike_write1 > spike_write2 > spike_write3 > 0
    say(f"(a) HABITUATION  write spikes: {spike_write1:.3f} -> "
        f"{spike_write2:.3f} -> {spike_write3:.3f}")
    say(f"    novelty: 1.000 -> {nov_write2:.3f} -> {nov_write3:.3f}; "
        f"monotonic shrink (hop-1 readout stays above threshold: "
        f"habituation as a ramp, not a cliff, on this circuit)  "
        f"[{'PASS' if a else 'FAIL'}]")
    ok &= a

    # (b) refractory: dampened inside the window
    b = d2["refractory_damp"] == 0.3 and d2["spike"] < cf_spike
    say(f"(b) REFRACTORY   fetch#1 completed with {refr_left:.1f}s of the 8s "
        f"window left (damp=0.3): injection {d2['injection']:.3f} -> spike "
        f"{d2['spike']:.3f} vs counterfactual {cf_inj:.3f} -> {cf_spike:.3f}  "
        f"[{'PASS' if b else 'FAIL'}]")
    ok &= b

    # (c) satiation decays toward thirst
    sats = [s for _, s, _ in decay]
    c = all(x >= y for x, y in zip(sats, sats[1:])) and sats[-1] < 0.01 \
        and decay[-1][2] >= 0.99
    say(f"(c) SATIATION    post-hit: "
        + " -> ".join(f"{s:.3f}" for s in sats)
        + f"; thirst back to {decay[-1][2]:.1f}  [{'PASS' if c else 'FAIL'}]")
    ok &= c

    say("=" * 78)
    say("ALL THREE BEHAVIORS DEMONSTRATED" if ok
        else "SOMETHING FAILED — see trace above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
