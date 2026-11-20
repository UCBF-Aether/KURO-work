#!/usr/bin/env python3
"""demo.py — proves the COMPASS bottle: real cascade, ring closure, tracking.

Deterministic. Exit 0 iff all checks pass.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compass import Compass

failures = []


def check(name, cond, detail=""):
    status = "ok " if cond else "FAIL"
    print(f"[{status}] {name} {detail}")
    if not cond:
        failures.append(name)


# (a) The cascade fires on real E-PG wiring.
c = Compass()
r = c.turn(90)
check("cascade fires on real wiring", r["activation"] > 0.15,
      f"(turn(90) -> activation {r['activation']})")

# (b) Ring closure: four 90-degree turns return to ~0 heading.
c2 = Compass()
for _ in range(4):
    c2.turn(90)
check("ring closure: 4x turn(90) -> ~0", abs(c2.heading() - 0.0) < 1e-9,
      f"(heading {c2.heading()})")

# (c) Heading tracks a sequence of turns.
c3 = Compass()
c3.turn(30)
c3.turn(-15)
c3.turn(200)
expected = (30 - 15 + 200) % 360  # = 215
check("heading tracks turn sequence", abs(c3.heading() - expected) < 1e-9,
      f"(heading {c3.heading()}, expected {expected})")

# (d) Bump shape: 16 units, peak 1.0, peak index matches heading.
c4 = Compass()
c4.turn(45)
st = c4.state()
peak_idx = max(range(16), key=lambda i: st["bump"][i])
check("bump: 16 units, peak 1.0 at heading",
      len(st["bump"]) == 16 and abs(max(st["bump"]) - 1.0) < 1e-9
      and abs(peak_idx * 22.5 - st["heading"]) < 11.3,
      f"(peak idx {peak_idx}, heading {st['heading']})")

# (e) Threshold cliff (documented model honesty): tiny turns stay silent.
c5 = Compass()
r5 = c5.turn(5)
check("threshold cliff: turn(5) stays silent", r5["activation"] == 0.0,
      f"(activation {r5['activation']}, heading still tracks: {c5.heading()})")

print()
if failures:
    print(f"FAILED: {failures}")
    sys.exit(1)
print("All compass checks passed.")
