#!/usr/bin/env python3
"""looming/demo.py — proves the LOOMING bottle fires on real wiring with the
correct valence/arousal signs. Exit 0 iff all checks pass.

Honesty: the cascade numbers are REAL wiring + MODEL dynamics; the sign
conventions are MODELED.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from looming import Looming

ok = True

def check(name, cond, detail=""):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    ok = ok and cond

print("LOOMING bottle — live fire on real wiring")
s = Looming()

# 1. full-strength stimulus fires the cascade on real wiring
r = s.sense(1.0)
print(f"  sense(1.0) -> {r}")
check("cascade fires at full injection", r["activation"] > 0,
      f"(activation={r['activation']})")

# 2. valence sign is correct for this sense
vs = -0.6
check("valence sign correct",
      (r["valence_delta"] < 0) if vs < 0 else (r["valence_delta"] > 0),
      f"(valence_delta={r['valence_delta']}, sign={vs:+.2f})")

# 3. arousal is non-negative and scales with activation
check("arousal non-negative and proportional",
      r["arousal_delta"] >= 0 and
      abs(r["arousal_delta"] - 1.0 * r["activation"]) < 1e-3,
      f"(arousal_delta={r['arousal_delta']}, gain=1.0)")

# 4. graded response: a stronger stimulus never reads weaker
r_half = s.sense(0.5)
check("monotonic with intensity",
      r_half["activation"] <= r["activation"],
      f"(0.5 -> {r_half['activation']}, 1.0 -> {r['activation']})")

# 5. activation decays with tick()
s.sense(1.0)
d0 = s.state()["activation"]
s.tick(10.0)
d1 = s.state()["activation"]
check("tick() decays activation", d1 < d0,
      "(" + str(d0) + " -> " + str(d1) + ")")

# 6. silence is silence: zero stimulus, zero readout
r0 = s.sense(0.0)
check("zero stimulus reads zero", r0["activation"] == 0.0)

print("ALL CHECKS PASS" if ok else "SOMETHING FAILED")
sys.exit(0 if ok else 1)
