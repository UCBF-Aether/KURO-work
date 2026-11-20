#!/usr/bin/env python3
"""
harness.py — scripted agent loop feeding the Mating drive.

Courtship pursuits across categories, with a back-to-back pursuit inside
the post-mating refractory window, designed to demonstrate three behaviors:
  (a) HABITUATION — repeated same-category pursuits yield shrinking spikes
      (graded shrink; the model's threshold cliff is documented honestly).
  (b) REFRACTORY  — a pursuit completed inside the 60s post-mating window
      is dampened x0.3 (the window eats the hit; male flies genuinely go
      refractory post-mating — biology; the timescale is toy).
  (c) SATIATION   — satiation decays back toward full drive over time.

Plus the mating-specific check: rejection (task_failed) dents wanting x0.7,
not x0.4 — the courtship drive persists.

A fake clock drives the core so the run is deterministic and fast.
Exits 0 if all behaviors check out, 1 otherwise.

Honesty: the scripted "work" is a TOY (progress steps are pretend); the
cascade numbers are REAL wiring + MODEL dynamics; the event->stimulation
mapping (ramp/persist/satiate/refractory) is MODELED — the unmapped
frontier, our design on real wiring. Test expectations are tuned to the
circuit's observed numbers; the module is never tuned to pass.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mating import Mating


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def main():
    clock = FakeClock()
    core = Mating(clock=clock)  # default: mating.json, P1 courtship circuit
    log = []

    def say(s):
        log.append(s)
        print(s, flush=True)

    def run_pursuit(name, category, difficulty, step_dt=1.0):
        n_steps = 2 + round(difficulty * 4)  # harder pursuits take more steps
        st = core.task_started(category, difficulty)
        say(f"[t={clock.t:6.1f}s] PURSUIT    {name!r:22s} cat={category:6s} "
            f"diff={difficulty:.1f} novelty={core._novelty(category):.3f}")
        for i in range(1, n_steps + 1):
            clock.advance(step_dt)
            p = i / n_steps
            s = core.progress(p)
            say(f"[t={clock.t:6.1f}s]   progress p={p:.2f}  "
                f"wanting={s['wanting']:.3f}  drive={s['drive_signal']:.3f}")
        done = core.task_completed()
        say(f"[t={clock.t:6.1f}s] SUCCESS    {name!r:22s} "
            f"injection={done['injection']:.3f}  SPIKE={done['spike']:.3f}  "
            f"satiation={done['satiation']:.3f}  "
            f"refr_damp={done['refractory_damp']:.1f}  "
            f"hab[{category}]={done['habituation'].get(category, 0):.2f}")
        return done

    say("=" * 78)
    say("MATING — courtship drive harness (fake clock, deterministic)")
    say("circuit: P1 -> doublesex/aSP-a/SMPad1/DM4/pC1/descending")
    say("(FlyWire FAFB v783, REAL wiring / MODEL dynamics); readout at hop-1")
    say("(MODELED): hop-2 fan-out dies below the model's firing threshold.")
    say("=" * 78)

    # ---- Phase 1: first success, then a pursuit inside the refractory window
    d1 = run_pursuit("serenade", "court", 0.6)              # t=0..4
    spike1 = d1["spike"]

    clock.advance(5.0)                                       # t=9, ~64s refr left
    s = core.state()
    refr_left = s["refractory_secs_remaining"]
    say(f"[t={clock.t:6.1f}s] -- {refr_left:.1f}s of post-mating refractory "
        f"remaining; courting anyway (fresh category) --")
    d2 = run_pursuit("follow", "dance", 0.4)                 # t=9..13
    # counterfactual: same success without the refractory damper
    cf_inj = d2["injection"] / 0.3 if d2["refractory_damp"] < 1 else None
    cf_spike = core._terminal(core._cascade(min(1.0, cf_inj))) if cf_inj else None
    say(f"[t={clock.t:6.1f}s]   counterfactual (no refractory): "
        f"injection would be {cf_inj:.3f} -> SPIKE would be {cf_spike:.3f}")

    # ---- Phase 2: habituation — same category after the window clears ----
    clock.advance(61.0)  # t=74; refractory (until t=73) clear, hab decayed
    s = core.state()
    nov3 = s["novelty_by_category"]["court"]
    say(f"[t={clock.t:6.1f}s] -- hab[court] decayed to "
        f"{core.habituation['court']:.2f}; novelty back up to "
        f"{nov3:.3f} --")
    d3 = run_pursuit("sing", "court", 0.5)                   # t=74..78
    spike3 = d3["spike"]

    clock.advance(61.0)  # t=139; refractory (until t=138) clear
    s = core.state()
    nov4 = s["novelty_by_category"]["court"]
    d4 = run_pursuit("chase", "court", 0.3)                  # t=139..142
    spike4 = d4["spike"]

    # ---- Phase 3: satiation decay back toward full drive ----
    say("-" * 78)
    say("post-success satiation decay (no pursuits, just time passing):")
    decay = []
    for _ in range(10):
        s = core.state()
        decay.append((clock.t, s["satiation"], s["drive"]))
        say(f"[t={clock.t:6.1f}s]   satiation={s['satiation']:.3f}  "
            f"drive={s['drive']:.3f}")
        clock.advance(2.0)

    # ---- bonus: rejection dents but does not kill the drive (MODELED) ----
    say("-" * 78)
    core.task_started("rebuff", 0.5)
    clock.advance(1.0)
    before = core.progress(0.5)["wanting"]
    core.task_failed()
    after = core.state()["wanting"]
    say(f"task_failed (rejection): wanting {before:.3f} -> {after:.3f} "
        f"(persistent dip x0.7, drive survives)")

    # ---- summary: the proofs ----
    say("=" * 78)
    say("SUMMARY — the three behaviors + the mating-specific check")
    say("=" * 78)
    ok = True

    # (a) habituation: graded shrinking spikes (no extinction on this circuit
    #     at these habituation levels — same as the THIRST bottle)
    a = spike1 > spike3 > spike4 > 0
    say(f"(a) HABITUATION  court spikes: {spike1:.3f} -> "
        f"{spike3:.3f} -> {spike4:.3f}")
    say(f"    novelty: 1.000 -> {nov3:.3f} -> {nov4:.3f}; graded shrink, "
        f"no extinction (hop-1 readout stays graded)  "
        f"[{'PASS' if a else 'FAIL'}]")
    ok &= a

    # (b) refractory: the 60s window eats the hit
    b = d2["refractory_damp"] == 0.3 and d2["spike"] < cf_spike
    say(f"(b) REFRACTORY   pursuit#2 succeeded with {refr_left:.1f}s of the "
        f"60s window left (damp=0.3): injection {d2['injection']:.3f} -> "
        f"spike {d2['spike']:.3f} vs counterfactual {cf_inj:.3f} -> "
        f"{cf_spike:.3f}  [{'PASS' if b else 'FAIL'}]")
    ok &= b

    # (c) satiation decays toward full drive
    sats = [s for _, s, _ in decay]
    c = all(x >= y for x, y in zip(sats, sats[1:])) and sats[-1] < 0.02 \
        and decay[-1][2] >= 0.98
    say(f"(c) SATIATION    post-success: "
        + " -> ".join(f"{s:.3f}" for s in sats)
        + f"; drive back to {decay[-1][2]:.2f}  [{'PASS' if c else 'FAIL'}]")
    ok &= c

    # (d) rejection dents x0.7, drive persists
    d = abs(after - before * 0.7) < 0.02 and after > 0.15
    say(f"(d) REJECTION    wanting {before:.3f} -> {after:.3f} (x0.7, "
        f"survives above baseline)  [{'PASS' if d else 'FAIL'}]")
    ok &= d

    say("=" * 78)
    say("ALL BEHAVIORS DEMONSTRATED" if ok
        else "SOMETHING FAILED — see trace above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
