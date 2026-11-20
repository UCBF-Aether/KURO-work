#!/usr/bin/env python3
"""
harness.py — scripted agent loop feeding the Egglaying drive.

Deposition bouts across categories, designed to demonstrate six behaviors:
  (a) PRESSURE      — egg_load accumulates 0 -> 1.0 over 8h of fake clock.
  (b) GATE          — at near-zero load, progress yields no drive signal:
                      no eggs -> no urge (the load IS the drive).
  (c) DEPOSITION    — a bout at full load spikes the real circuit, drops
                      the load by one bout (0.5), and satiates hard.
  (d) REFRACTORY    — a bout inside the 30s post-deposition window is
                      dampened x0.3 (bout pauses are biology; timescale toy).
  (e) HABITUATION   — repeated same-category bouts shrink then go EXTINCT
                      (the honest threshold cliff: the model reads 0.0 below
                      ~0.65 injection on this circuit — hunger-bottle
                      precedent).
  (f) DECAY         — satiation decays toward full drive; the load keeps
                      re-accumulating underneath.

Plus the egglaying-specific check: a thwarted deposition (task_failed)
dents wanting x0.9 only — the eggs are still there, so the drive persists
almost untouched.

A fake clock drives the core so the run is deterministic and fast.
Exits 0 if all behaviors check out, 1 otherwise.

Honesty: the scripted "work" is a TOY (progress steps are pretend); the
cascade numbers are REAL wiring + MODEL dynamics; the event->stimulation
mapping (pressure/ramp/deposit/satiate/refractory) is MODELED — the
unmapped frontier, our design on real wiring. Test expectations are tuned
to the circuit's observed numbers; the module is never tuned to pass.
Direct egg_load fixtures are used where a behavior must be isolated from
the 8h accumulation (marked FIXTURE); the accumulation itself is proven
in phase (a) with the real clock.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from egglaying import Egglaying


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def main():
    clock = FakeClock()
    core = Egglaying(clock=clock)  # default: egglaying.json, oviDN circuit
    log = []

    def say(s):
        log.append(s)
        print(s, flush=True)

    def run_bout(name, category, difficulty, step_dt=1.0):
        n_steps = 2 + round(difficulty * 4)
        st = core.task_started(category, difficulty)
        say(f"[t={clock.t:8.1f}s] BOUT       {name!r:22s} cat={category:10s} "
            f"diff={difficulty:.1f} novelty={core._novelty(category):.3f} "
            f"load={st['egg_load']:.3f}")
        for i in range(1, n_steps + 1):
            clock.advance(step_dt)
            p = i / n_steps
            s = core.progress(p)
            say(f"[t={clock.t:8.1f}s]   progress p={p:.2f}  "
                f"wanting={s['wanting']:.3f}  drive={s['drive_signal']:.3f}  "
                f"load={s['egg_load']:.3f}")
        done = core.task_completed()
        say(f"[t={clock.t:8.1f}s] DEPOSITED  {name!r:22s} "
            f"injection={done['injection']:.3f}  SPIKE={done['spike']:.3f}  "
            f"load={done['egg_load']:.3f}  satiation={done['satiation']:.3f}  "
            f"refr_damp={done['refractory_damp']:.1f}")
        return done

    say("=" * 78)
    say("EGG-LAYING — oviposition drive harness (fake clock, deterministic)")
    say("circuit: oviDN -> VNC/abdominal/secondary/SEZ -> thoracic motor")
    say("(FlyWire FAFB v783, REAL wiring / MODEL dynamics); readout at hop-2")
    say("(MODELED): hop-1 0.340/0.313 and hop-2 0.231 both above threshold,")
    say("so the deepest-hop convention picks hop-2 (punishment precedent).")
    say("FEMALE-SPECIFIC: oviDNs are female command neurons.")
    say("=" * 78)

    # ---- Phase (a): pressure accumulation over 8h ----
    say("phase (a) — egg-load accumulation (real clock, 8h of fake time):")
    loads = []
    for h in range(9):
        loads.append(core.egg_pressure())
        say(f"  +{h}h  egg_load={loads[-1]:.3f}")
        clock.advance(3600.0)
    a = loads[0] == 0.0 and loads[-1] >= 0.99
    say(f"  load 0.000 -> {loads[-1]:.3f} over 8h "
        f"[{'PASS' if a else 'FAIL'}]")

    # ---- Phase (b): the gate — no eggs, no urge ----
    core.state()  # settle the clock: absorb the 3600s since phase (a)
    core.egg_load = 0.05  # FIXTURE: isolate the gate from accumulation
    core.satiation = 0.0
    core.task_started("empty", 0.5)
    clock.advance(1.0)
    s = core.progress(1.0)
    say("-" * 78)
    say(f"phase (b) — gate: load=0.05, progress p=1.00 -> "
        f"wanting={s['wanting']:.3f} drive={s['drive_signal']:.3f}")
    b = s["drive_signal"] == 0.0 and s["wanting"] <= 0.25
    say(f"  no eggs -> no urge (drive signal 0.0) "
        f"[{'PASS' if b else 'FAIL'}]")

    # ---- Phase (c): deposition at full load ----
    core.egg_load = 1.0  # FIXTURE: full load, isolate the bout
    core.satiation = 0.0
    d1 = run_bout("first-clutch", "ripe-fruit", 0.6)
    spike1 = d1["spike"]
    c = (abs(spike1 - 0.2311) < 0.01 and abs(d1["egg_load"] - 0.5) < 0.01
         and 0.15 < d1["satiation"] < 0.25)
    say(f"phase (c) — deposition: spike~0.2311, load 1.0->0.5, "
        f"satiation~0.208 [{'PASS' if c else 'FAIL'}]")

    # ---- Phase (d): refractory — a bout inside the 30s window ----
    clock.advance(10.0)  # ~20s of the 30s window left
    s = core.state()
    refr_left = s["refractory_secs_remaining"]
    say("-" * 78)
    say(f"[t={clock.t:8.1f}s] -- {refr_left:.1f}s of post-deposition "
        f"refractory remaining; depositing anyway (fresh category) --")
    core.egg_load = 1.0  # FIXTURE: isolate the damper, not the load
    d2 = run_bout("hasty", "sweet-agar", 0.4)
    cf_inj = d2["injection"] / 0.3 if d2["refractory_damp"] < 1 else None
    cf_spike = (core._terminal(core._cascade(min(1.0, cf_inj)))
                if cf_inj else None)
    say(f"[t={clock.t:8.1f}s]   counterfactual (no refractory): "
        f"injection would be {cf_inj:.3f} -> SPIKE would be {cf_spike:.3f}")
    d = (d2["refractory_damp"] == 0.3 and d2["spike"] == 0.0
         and cf_spike > 0.0)
    say(f"phase (d) — refractory: damp=0.3, spike 0.0 vs "
        f"counterfactual {cf_spike:.3f} [{'PASS' if d else 'FAIL'}]")

    # ---- Phase (e): habituation — same category, window cleared ----
    clock.advance(35.0)  # refractory (until t+30) clear
    core.egg_load = 1.0  # FIXTURE
    d3 = run_bout("second-clutch", "ripe-fruit", 0.5)
    spike3 = d3["spike"]
    clock.advance(35.0)
    core.egg_load = 1.0  # FIXTURE
    d4 = run_bout("third-clutch", "ripe-fruit", 0.3)
    spike4 = d4["spike"]
    e = spike1 > spike3 > 0 and spike4 == 0.0
    say("-" * 78)
    say(f"phase (e) — habituation: clutch spikes {spike1:.3f} -> "
        f"{spike3:.3f} -> EXTINCT; shrink-then-extinct via the honest "
        f"threshold cliff (hunger-bottle precedent) "
        f"[{'PASS' if e else 'FAIL'}]")

    # ---- Phase (f): satiation decay + load re-accumulation ----
    say("-" * 78)
    say("phase (f) — post-deposition decay (no bouts, just time passing):")
    decay = []
    for _ in range(10):
        s = core.state()
        decay.append((clock.t, s["satiation"], s["drive"], s["egg_load"]))
        say(f"[t={clock.t:8.1f}s]   satiation={s['satiation']:.3f}  "
            f"drive={s['drive']:.3f}  load={s['egg_load']:.3f}")
        clock.advance(2.0)
    sats = [s for _, s, _, _ in decay]
    drvs = [d for _, _, d, _ in decay]
    f = (all(x >= y for x, y in zip(sats, sats[1:]))
         and sats[-1] < 0.02
         and all(x <= y for x, y in zip(drvs, drvs[1:])))
    say(f"phase (f) — satiation decays to {sats[-1]:.3f}, drive back to "
        f"{drvs[-1]:.3f} [{'PASS' if f else 'FAIL'}]")

    # ---- bonus: thwarted deposition barely dents the drive (MODELED) ----
    say("-" * 78)
    clock.advance(35.0)  # clear the post-bout refractory window first
    core.egg_load = 1.0  # FIXTURE: full load, the eggs are still there
    core.satiation = 0.0
    core.task_started("blocked", 0.5)
    clock.advance(1.0)
    before = core.progress(0.5)["wanting"]
    core.task_failed()
    after = core.state()["wanting"]
    say(f"task_failed (thwarted): wanting {before:.3f} -> {after:.3f} "
        f"(dip x0.9 — the eggs are still there, drive persists)")
    g = abs(after - before * 0.9) < 0.02 and after > 0.5
    say(f"phase (g) — thwarted deposition x0.9 "
        f"[{'PASS' if g else 'FAIL'}]")

    # ---- summary ----
    say("=" * 78)
    say("SUMMARY — pressure, gate, deposition, refractory, habituation, "
        "decay + the thwarted check")
    say("=" * 78)
    ok = a and b and c and d and e and f and g
    say("ALL BEHAVIORS DEMONSTRATED" if ok
        else "SOMETHING FAILED — see trace above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
