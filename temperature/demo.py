#!/usr/bin/env python3
"""demo.py — prove the TEMPERATURE bottle fires on real wiring.

Exit 0 = all checks pass. Exit 1 = something regressed.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from temperature import Temperature

checks = []


def check(name, cond, detail=""):
    checks.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), "-", name,
          ("(%s)" % detail) if detail else "")


t = Temperature()

# (a) hot chain fires on real wiring, valence negative
r = t.sense(1.0, channel="hot")
check("hot fires", r["activation"] > 0.15,
      "activation=%s" % r["activation"])
check("hot valence negative", r["valence_delta"] < 0,
      "valence_delta=%s" % r["valence_delta"])
check("hot arousal positive", r["arousal_delta"] > 0,
      "arousal_delta=%s" % r["arousal_delta"])

# (b) cold chain fires on real wiring, valence zero (informational)
r2 = t.sense(1.0, channel="cold")
check("cold fires", r2["activation"] > 0.15,
      "activation=%s" % r2["activation"])
check("cold valence zero", r2["valence_delta"] == 0.0,
      "valence_delta=%s" % r2["valence_delta"])
check("cold arousal positive", r2["arousal_delta"] > 0,
      "arousal_delta=%s" % r2["arousal_delta"])

# (c) both = hot + cold activations
r3 = t.sense(1.0, channel="both")
expected = round(r["activation"] + r2["activation"], 4)
check("both = hot + cold", abs(r3["activation"] - expected) < 1e-9,
      "both=%s vs sum=%s" % (r3["activation"], expected))
check("both valence = hot only", abs(r3["valence_delta"] - r["valence_delta"]) < 1e-9,
      "valence_delta=%s" % r3["valence_delta"])

# convenience readouts agree with the "both" call above
check("hot_valence()", t.hot_valence() == r3["valence_delta"],
      "hot_valence=%s" % t.hot_valence())
check("cold_valence()", t.cold_valence() == 0.0,
      "cold_valence=%s" % t.cold_valence())

# threshold cliff: silent below ~0.5 injection
r0 = t.sense(0.1, channel="hot")
check("threshold cliff (hot 0.1)", r0["activation"] == 0.0,
      "activation=%s" % r0["activation"])

# decay
t.sense(1.0, channel="hot")
t.tick(10.0)
check("tick decays to 0", t.state()["activation"]["hot"] == 0.0,
      "state=%s" % t.state()["activation"])

# bad channel raises
try:
    t.sense(1.0, channel="warm")
    check("bad channel raises", False, "no ValueError")
except ValueError:
    check("bad channel raises", True, "ValueError raised")

failed = [n for n, ok, _ in checks if not ok]
print("\n%d/%d checks passed" % (len(checks) - len(failed), len(checks)))
sys.exit(1 if failed else 0)
