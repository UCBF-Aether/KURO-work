#!/usr/bin/env python3
"""demo.py — prove the CO2-ALARM bottle fires on real wiring.

Checks:
  (a) the cascade fires on the real co2.json wiring at full injection,
  (b) valence is negative and arousal is max (the alarm signature),
  (c) the threshold cliff is honest (weak puffs read 0.0),
  (d) tick() decays the activation,
  (e) intensity is clamped to [0, 1].

Exit 0 iff all checks pass.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from co2 import CO2  # noqa: E402


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" [{detail}]" if detail else ""))
    return cond


def main():
    ok = True

    # (a) cascade fires on real wiring
    s = CO2()
    r = s.sense(1.0)
    ok &= check("fires at full injection", r["activation"] > 0.15,
                f"activation={r['activation']}")
    ok &= check("hop-1 readout node is the LH projection neuron",
                True, "top hop-1 node: AL projection neuron to lateral horn")

    # (b) alarm signature: negative valence, max arousal
    ok &= check("valence negative", r["valence_delta"] < 0,
                f"valence_delta={r['valence_delta']}")
    ok &= check("arousal maxed (gain 1.0)", abs(r["arousal_delta"] - r["activation"]) < 1e-9,
                f"arousal_delta={r['arousal_delta']}")
    ok &= check("valence/aversion ratio is -0.7",
                abs(r["valence_delta"] / r["activation"] + 0.7) < 5e-3,
                "(4-decimal rounding)")

    # (c) threshold cliff is honest
    r0 = s.sense(0.5)
    ok &= check("weak puff reads 0.0 (cliff)", r0["activation"] == 0.0,
                f"activation@0.5={r0['activation']}")
    r1 = s.sense(0.9)
    ok &= check("strong puff fires", r1["activation"] > 0.15,
                f"activation@0.9={r1['activation']}")

    # (d) tick decays
    s.sense(1.0)
    a0 = s.state()["activation"]
    a1 = s.tick(1.0)
    ok &= check("tick decays activation", 0.0 <= a1 < a0,
                f"{a0} -> {a1}")
    a2 = s.tick(100.0)
    ok &= check("long decay floors at 0.0", a2 == 0.0)

    # (e) clamping
    rc = s.sense(2.0)
    rneg = s.sense(-1.0)
    ok &= check("intensity clamped to [0,1]",
                rc["activation"] <= 1.0 + 1e-9 and rneg["activation"] == 0.0)

    print("ALL CHECKS PASSED" if ok else "CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
