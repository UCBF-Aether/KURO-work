#!/usr/bin/env python3
"""demo.py — prove the PHEROMONE bottle fires on real wiring. Exit 0 iff all pass."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pheromone import Pheromone

fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (" — " + detail if detail else ""))
    if not cond:
        fails.append(name)


# (a) the cascade fires on real wiring
s = Pheromone()
r = s.sense(1.0)
check("cascade fires", r["activation"] > 0,
      "activation=%.4f" % r["activation"])

# (b) courtship_bridge() reads nonzero at full intensity
b = s.courtship_bridge()
check("bridge nonzero", b > 0, "bridge=%.4f" % b)

# (c) valence sign positive (appetitive-in-context)
check("valence positive", r["valence_delta"] > 0,
      "valence_delta=%.4f" % r["valence_delta"])
check("arousal positive", r["arousal_delta"] > 0,
      "arousal_delta=%.4f" % r["arousal_delta"])

# (d) silence is silent — below the cliff nothing fires
r0 = s.sense(0.1)
check("cliff honest", r0["activation"] == 0.0,
      "activation@0.1=%.4f" % r0["activation"])

# (e) decay works
s.sense(1.0)
a1 = s.tick(30.0)
check("decay", a1 == 0.0, "after 30s=%.4f" % a1)

# (f) bridge decays too
s.sense(1.0)
s.tick(30.0)
check("bridge decays", s.courtship_bridge() == 0.0)

print()
if fails:
    print("FAILED:", fails)
    sys.exit(1)
print("ALL GREEN — pheromone bottle sealed.")
