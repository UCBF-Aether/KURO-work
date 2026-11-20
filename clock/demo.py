#!/usr/bin/env python3
"""demo.py — prove the CLOCK bottle works. Deterministic; exit 0 iff all pass."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clock import Clock


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        sys.exit(1)


c = Clock()

# (a) cascade fires on real wiring: drive to mid-day, pdf ~1, check activation
c.tick(21600)          # 6h -> phase 0.25, mid-day, pdf = 1
r = c.tick(1)          # 1s more; pdf still ~1.0
check("cascade fires on real wiring", r["activation"] > 0.0)
print("      activation at mid-day:", r["activation"])

# (b) phase advances 1.0 per 86400s
c2 = Clock()
c2.tick(43200)
check("phase = 0.5 after 43200s", abs(c2.phase() - 0.5) < 1e-9)
c2.tick(43200)
check("phase wraps to 0 after 86400s", abs(c2.phase() - 0.0) < 1e-9)

# (c) pdf peaks mid-day
c3 = Clock()
c3.tick(21600)  # phase 0.25
check("pdf == 1.0 at mid-day", abs(c3.pdf - 1.0) < 1e-9)
c4 = Clock()
c4.tick(64800)  # phase 0.75, mid-night
check("pdf == 0.0 at mid-night", abs(c4.pdf - 0.0) < 1e-9)

# (d) time_of_day sane
check("time_of_day 6.0 at phase 0.25", abs(c3.time_of_day() - 6.0) < 1e-9)
check("time_of_day 18.0 at phase 0.75", abs(c4.time_of_day() - 18.0) < 1e-9)

# night definition
check("is_night False at mid-day", c3.is_night() is False)
check("is_night True at mid-night", c4.is_night() is True)
c5 = Clock()
check("is_night False at dawn", c5.is_night() is False)

# state schema
s = c3.state()
check("state has phase/pdf/activation",
      set(s.keys()) == {"phase", "pdf", "activation"})

print("ALL CLOCK CHECKS PASSED")
