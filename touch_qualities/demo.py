#!/usr/bin/env python3
"""demo.py — TouchQualities bottle acceptance demo. Exit 0 = all checks pass."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from touch_qualities import TouchQualities

checks = []


def check(name, cond, detail=""):
    checks.append(cond)
    print(("PASS" if cond else "FAIL"), name, detail)
    return cond


q = TouchQualities()

# (a) campaniform path fires on real wiring to b1
r = q.sense(1.0, quality="campaniform")
check("campaniform sense(1.0): activation 3.0",
      r["activation"] == 3.0, f"(got {r['activation']})")
check("campaniform valence 0.0 (informational)", r["valence_delta"] == 0.0)
check("campaniform arousal 0.9 (0.3 x 3.0)", r["arousal_delta"] == 0.9)
check("motor_drive() reads b1: 3.0", q.motor_drive() == 3.0,
      f"(got {q.motor_drive()})")

# (b) bristle path fires (hypothesis edges)
r = q.sense(1.0, quality="bristle")
check("bristle sense(1.0): activation 1.0", r["activation"] == 1.0,
      f"(got {r['activation']})")
check("bristle does not reach b1", q.motor_drive() == 0.0)

# (c) both sum across the two disjoint pathways
camp = q.sense(1.0, quality="campaniform")["activation"]
bristle = q.sense(1.0, quality="bristle")["activation"]
both = q.sense(1.0, quality="both")["activation"]
check("both = campaniform + bristle", both == camp + bristle,
      f"({both} = {camp} + {bristle})")
check("motor_drive() still reads b1 under both", q.motor_drive() == camp)

# threshold cliff + linearity + decay
check("silent below threshold (0.1)", q.sense(0.1, "campaniform")["activation"] == 0.0)
check("linear at 0.5 (1.5)", q.sense(0.5, "campaniform")["activation"] == 1.5)
q.sense(1.0, "campaniform")
check("tick(10) decays 3.0 -> 1.0", q.tick(10.0) == 1.0)

# bad quality rejected
try:
    q.sense(1.0, "nonsense")
    check("invalid quality rejected", False)
except ValueError:
    check("invalid quality rejected", True)

# provenance sanity: LITERATURE-CONFIRMED edge never double-counted
import json
_this = os.path.dirname(os.path.abspath(__file__))
g = json.load(open(os.path.join(_this, "..", "subgraphs",
                                "touch_qualities_lit.json")))
confirmed = [e for e in g["edges"] if e.get("provenance") == "LITERATURE-CONFIRMED"]
check("confirmed edge exists but excluded from cascade",
      len(confirmed) == 1 and q.motor_drive() == 3.0)

if all(checks):
    print(f"\nALL {len(checks)} CHECKS PASS")
    sys.exit(0)
print(f"\n{sum(1 for c in checks if not c)} CHECKS FAILED")
sys.exit(1)
