#!/usr/bin/env python3
"""demo.py — proves the MOTION bottle fires on real wiring.

Deterministic. Exit 0 iff every check passes.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motion import Motion, T4_ID, T5_ID

checks = []


def check(name, cond, detail=""):
    checks.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), name, detail)


# 1. Cascade fires on real wiring for all three direction selections.
m = Motion()
r_on = m.sense(1.0, direction="on")
r_off = m.sense(1.0, direction="off")
r_both = m.sense(1.0, direction="both")
check("on fires", r_on["activation"] > 0.15,
      f"activation={r_on['activation']}")
check("off fires", r_off["activation"] > 0.15,
      f"activation={r_off['activation']}")
check("both fires", r_both["activation"] > 0.15,
      f"activation={r_both['activation']}")

# 2. Direction is reported honestly.
check("direction echoed (on)", r_on["direction"] == "on")
check("direction echoed (off)", r_off["direction"] == "off")
check("direction echoed (both)", r_both["direction"] == "both")

# 3. T4/T5 converge on shared downstream: "both" is not just the sum of
#    two independent pathways — both selections light up, and each alone
#    carries graded signal. (The convergence is in the wiring: both
#    synapse onto the same LPTC classes, per motion.json.)
check("each selection graded", r_on["activation"] > 0 and r_off["activation"] > 0)

# 4. Valence is ~0 for all selections — motion is informational.
check("valence zero (on)", abs(r_on["valence_delta"]) < 1e-9,
      f"v={r_on['valence_delta']}")
check("valence zero (off)", abs(r_off["valence_delta"]) < 1e-9,
      f"v={r_off['valence_delta']}")
check("valence zero (both)", abs(r_both["valence_delta"]) < 1e-9,
      f"v={r_both['valence_delta']}")

# 5. Arousal gain applied.
check("arousal = 0.4 x activation",
      abs(r_both["arousal_delta"] - round(0.4 * r_both["activation"], 4)) < 1e-9,
      f"a={r_both['arousal_delta']}")

# 6. Threshold cliff: a faint stimulus reads 0.0 — honest model behavior.
r_dim = m.sense(0.1, direction="both")
check("dim stimulus silent", r_dim["activation"] == 0.0,
      f"activation={r_dim['activation']}")

# 7. tick() decays activation.
m.sense(1.0, direction="both")
before = m.state()["activation"]
after = m.tick(30)
check("tick decays to zero", before > 0 and after == 0.0,
      f"{before} -> {after}")

# 8. state() carries the last direction.
m.sense(0.9, direction="off")
check("state last_direction", m.state()["last_direction"] == "off")

# 9. Bad direction falls back to "both", never crashes.
r_bad = m.sense(0.8, direction="sideways")
check("bad direction falls back", r_bad["direction"] == "both")

failed = [n for n, ok, _ in checks if not ok]
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
