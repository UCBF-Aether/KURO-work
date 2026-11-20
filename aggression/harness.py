#!/usr/bin/env python3
"""
harness.py — scripted agent loop feeding the Aggression drive.

Confrontations across categories, with a back-to-back fight inside the
post-win refractory window, designed to demonstrate three behaviors:
  (a) HABITUATION — a repeated same-category win goes extinct: first win
      spikes 0.1695, the repeat reads 0.0. On this circuit the model's
      threshold cliff (~0.885 injection) turns habituation into
      shrink-then-EXTINCT — the same pattern as the original HUNGER
      bottle, documented honestly.
  (b) REFRACTORY  — a win inside the 30s post-victory window is dampened
      x0.3 (the window eats the hit; the 30s timescale is a MODELED
      choice — no crisp biological post-win refractory in flies).
  (c) SATIATION   — satiation decays back toward full drive over time.

Plus the aggression-specific checks: losing (task_failed) dips wanting
x0.5 — losers retreat harder than mating's x0.7 rejection — and
fru_drive() reports the triple-convergence share exactly.

A fake clock drives the core so the run is deterministic and fast.
Exits 0 if all behaviors check out, 1 otherwise.

Honesty: the scripted "work" is a TOY (progress steps are pretend); the
cascade numbers are REAL wiring + MODEL dynamics; the event->stimulation
mapping (ramp/win/lose/refractory) is MODELED — the unmapped frontier,
our design on real wiring. Test expectations are tuned to the circuit's
observed numbers; the module is never tuned to pass.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aggression import Aggression, FRU_SHARE


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def main():
    clock = FakeClock()
    core = Aggression(clock=clock)  # default: aggression.json, aIPg circuit
    log = []

    def say(s):
        log.append(s)
        print(s, flush=True)

    def run_fight(name, category, difficulty, step_dt=1.0):
        n_steps = 2 + round(difficulty * 4)  # harder fights take more steps
        st = core.task_started(category, difficulty)
        say(f"[t={clock.t:6.1f}s] FIGHT      {name!r:22s} cat={category:10s} "
            f"diff={difficulty:.1f} novelty={core._novelty(category):.3f}")
        for i in range(1, n_steps + 1):
            clock.advance(step_dt)
            p = i / n_steps
            s = core.progress(p)
            say(f"[t={clock.t:6.1f}s]   progress p={p:.2f}  "
                f"wanting={s['wanting']:.3f}  drive={s['drive_signal']:.3f}")
        done = core.task_completed()
        say(f"[t={clock.t:6.1f}s] WON        {name!r:22s} "
            f"injection={done['injection']:.3f}  SPIKE={done['spike']:.3f}  "
            f"satiation={done['satiation']:.3f}  "
            f"refr_damp={done['refractory_damp']:.1f}  "
            f"hab[{category}]={done['habituation'].get(category, 0):.2f}")
        return done

    say("=" * 78)
    say("AGGRESSION — fight drive harness (fake clock, deterministic)")
    say("circuit: aIPg -> SMPpv2/CP1/VLPl2/BLAv2 -> VNC/thoracic/descending")
    say("(FlyWire FAFB v783, REAL wiring / MODEL dynamics); readout at hop-1")
    say("(MODELED): threshold cliff ~0.885 injection -> habituation shows")
    say("shrink-then-EXTINCT on this circuit (hunger-original pattern).")
    say("=" * 78)

    # ---- Phase 1: first win, then a fight inside the refractory window ----
    d1 = run_fight("lunge", "rival", 0.6)                  # t=0..4
    spike1 = d1["spike"]
    nov1 = d1["novelty"]

    clock.advance(21.0)                                   # t=25, ~9s refr left
    s = core.state()
    refr_left = s["refractory_secs_remaining"]
    say(f"[t={clock.t:6.1f}s] -- {refr_left:.1f}s of post-win refractory "
        f"remaining; fighting anyway (fresh category) --")
    d2 = run_fight("box", "intruder", 0.4)                 # t=25..29
    # counterfactual: same win without the refractory damper
    cf_inj = d2["injection"] / 0.3 if d2["refractory_damp"] < 1 else None
    cf_spike = core._terminal(core._cascade(min(1.0, cf_inj))) if cf_inj else None
    say(f"[t={clock.t:6.1f}s]   counterfactual (no refractory): "
        f"injection would be {cf_inj:.3f} -> SPIKE would be {cf_spike:.3f}")

    # ---- Phase 2: habituation — same rival after the window clears --------
    clock.advance(31.0)  # t=60; refractory (until t=59) clear, hab decayed
    s = core.state()
    nov3 = s["novelty_by_category"]["rival"]
    say(f"[t={clock.t:6.1f}s] -- hab[rival] decayed to "
        f"{core.habituation['rival']:.2f}; novelty back up to "
        f"{nov3:.3f} --")
    d3 = run_fight("lunge2", "rival", 0.5)                # t=60..64
    spike3 = d3["spike"]
    nov3b = d3["novelty"]

    # ---- fresh rival: the drive still works on a new category ------------
    clock.advance(31.0)  # t=95; refractory (until t=94) clear
    d4 = run_fight("takedown", "challenger", 0.5)          # t=95..99
    spike4 = d4["spike"]

    # ---- Phase 3: satiation decay back toward full drive -----------------
    say("-" * 78)
    say("post-win satiation decay (no fights, just time passing):")
    decay = []
    for _ in range(10):
        s = core.state()
        decay.append((clock.t, s["satiation"], s["drive"]))
        say(f"[t={clock.t:6.1f}s]   satiation={s['satiation']:.3f}  "
            f"drive={s['drive']:.3f}")
        clock.advance(2.0)

    # ---- bonus: losing retreats hard x0.5 (MODELED) ----------------------
    # (run clear of the post-win refractory window so the numbers are clean)
    say("-" * 78)
    clock.advance(12.0)  # t=130; refractory (until t=129) clear
    core.task_started("rout", 0.5)
    clock.advance(1.0)
    before = core.progress(0.5)["wanting"]
    core.task_failed()
    after = core.state()["wanting"]
    say(f"task_failed (LOSING): wanting {before:.3f} -> {after:.3f} "
        f"(retreat dip x0.5, harder than mating's x0.7 rejection)")

    # ---- bonus: fru_drive() — the triple-convergence share ---------------
    core.task_started("glare", 0.5)
    core.progress(1.0)
    ds = core.drive_signal  # unrounded internal readout (state() rounds)
    fru = core.fru_drive()
    say(f"fru_drive(): drive_signal={ds:.4f} x FRU_SHARE({FRU_SHARE:.6f}) "
        f"= {fru:.6f}  (FBbt_00016687, shared with mating + pheromone)")

    # ---- summary: the proofs ---------------------------------------------
    say("=" * 78)
    say("SUMMARY — the three behaviors + the aggression-specific checks")
    say("=" * 78)
    ok = True

    # (a) habituation: shrink-then-EXTINCT on this circuit
    a = spike1 > 0.15 and spike3 == 0.0
    say(f"(a) HABITUATION  rival wins: {spike1:.4f} (novelty {nov1:.3f}) -> "
        f"{spike3:.4f} (novelty {nov3b:.3f})")
    say(f"    threshold cliff ~0.885 injection: repeat win reads 0.0 — "
        f"shrink-then-EXTINCT (hunger-original pattern)  "
        f"[{'PASS' if a else 'FAIL'}]")
    ok &= a

    # (b) refractory: the 30s window eats the hit
    b = (d2["refractory_damp"] == 0.3 and d2["spike"] == 0.0
         and cf_spike is not None and cf_spike > 0.15)
    say(f"(b) REFRACTORY   win#2 succeeded with {refr_left:.1f}s of the "
        f"30s window left (damp=0.3): injection {d2['injection']:.3f} -> "
        f"spike {d2['spike']:.3f} vs counterfactual {cf_inj:.3f} -> "
        f"{cf_spike:.3f}  [{'PASS' if b else 'FAIL'}]")
    ok &= b

    # (c) satiation decays toward full drive
    sats = [s for _, s, _ in decay]
    c = all(x >= y for x, y in zip(sats, sats[1:])) and sats[-1] < 0.02 \
        and decay[-1][2] >= 0.98
    say(f"(c) SATIATION    post-win: "
        + " -> ".join(f"{s:.3f}" for s in sats)
        + f"; drive back to {decay[-1][2]:.2f}  [{'PASS' if c else 'FAIL'}]")
    ok &= c

    # (d) losing dips x0.5, drive retreats but survives
    d = abs(after - before * 0.5) < 0.02 and after > 0.15
    say(f"(d) LOSING       wanting {before:.3f} -> {after:.3f} (x0.5, "
        f"retreats harder than rejection, survives above baseline)  "
        f"[{'PASS' if d else 'FAIL'}]")
    ok &= d

    # (e) fru_drive is exactly the documented share of the drive signal
    e = abs(fru - ds * FRU_SHARE) < 1e-9 and fru > 0
    say(f"(e) FRU_DRIVE    {fru:.6f} == drive_signal x FRU_SHARE exactly "
        f"(triple-convergence bookkeeping for future arbitration)  "
        f"[{'PASS' if e else 'FAIL'}]")
    ok &= e

    # fresh-category sanity: the drive still fires on a new rival
    say(f"    fresh-category win after extinction: spike {spike4:.4f} "
        f"(drive intact, only the habituated category went quiet)")

    say("=" * 78)
    say("ALL BEHAVIORS DEMONSTRATED" if ok
        else "SOMETHING FAILED — see trace above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
