#!/usr/bin/env python3
"""harness.py — proves the SLEEP bottle behaves like a homeostat.

Deterministic (explicit dt, no clock). Exit 0 iff all checks pass.
Tune expectations to the circuit's observed numbers, never the module.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sleep import Sleep, RATE_UP, RATE_DOWN, SLEEP_THRESHOLD  # noqa: E402


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    return cond


def main():
    ok = True
    s = Sleep()

    # (a) pressure accumulates 0 -> ~1 over simulated wake time
    s.tick(1800)
    p1 = s.pressure()
    s.tick(1800)
    p2 = s.pressure()
    ok &= check("accumulates while awake", p2 > p1 > 0,
                f"0 -> {p1:.3f} -> {p2:.3f}")
    ok &= check("rate is 1/hr", abs(p2 - 3600 * RATE_UP) < 1e-9,
                f"p={p2:.4f}")
    s.tick(3600)
    ok &= check("saturates at 1.0", s.pressure() == 1.0,
                f"p={s.pressure():.3f}")

    # debt ledger grows while unrested
    ok &= check("debt accrues", s.state()["debt_secs"] == 7200.0,
                f"debt={s.state()['debt_secs']}")

    # (c) crossing 0.8 flips asleep=True
    s2 = Sleep()
    s2.tick(0.79 * 3600)
    ok &= check("below threshold: awake", not s2.asleep(),
                f"p={s2.pressure():.3f}")
    s2.tick(0.02 * 3600)
    ok &= check("crossing 0.8 -> asleep", s2.asleep(),
                f"p={s2.pressure():.3f}")
    # the homeostat overrides the agent's claim
    s2.wake()
    ok &= check("wake() cannot clear pressure",
                s2.asleep() and s2.pressure() >= SLEEP_THRESHOLD,
                f"asleep={s2.asleep()}")

    # (b) rest() discharges back toward 0
    r = s.rest(600)  # 10 rest-min from full pressure
    ok &= check("rest discharges", r["pressure"] < 1.0,
                f"1.0 -> {r['pressure']:.3f}, depth={r['depth']:.3f}")
    ok &= check("discharge rate 1/20min",
                abs(r["depth"] - 600 * RATE_DOWN) < 1e-9,
                f"depth={r['depth']:.4f}")
    s.rest(600)
    ok &= check("full rest -> 0", s.pressure() == 0.0,
                f"p={s.pressure():.3f}")
    ok &= check("debt clears on full rest",
                s.state()["debt_secs"] == 0.0)
    ok &= check("below threshold after rest", not s.asleep())

    # (d) the cascade fires on REAL wiring during discharge
    s3 = Sleep()
    s3.tick(3600)  # pressure = 1.0
    r3 = s3.rest(1200)  # full discharge: injection 1.0
    ok &= check("cascade fires on discharge", r3["activation"] > 0,
                f"activation={r3['activation']:.4f} (expect ~0.31)")
    ok &= check("graded with discharge",
                r3["activation"] > Sleep().rest(0)["activation"],
                "full rest > zero rest")
    # threshold cliff: a tiny rest reads 0 (toy honest, not a bug)
    s4 = Sleep()
    s4.tick(3600)
    r4 = s4.rest(60)  # discharges 0.05 -> below cascade threshold
    ok &= check("micro-rest below threshold reads 0",
                r4["activation"] == 0.0,
                f"activation={r4['activation']}")

    # no accumulation while resting
    s5 = Sleep()
    s5.rest(100)
    p_before = s5.pressure()
    s5.tick(3600)
    ok &= check("tick() idle while resting", s5.pressure() == p_before,
                f"p={p_before:.3f}")
    s5.wake()
    s5.tick(3600)
    ok &= check("wake() resumes accumulation", s5.pressure() > p_before,
                f"p={s5.pressure():.3f}")

    print("HARNESS " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
