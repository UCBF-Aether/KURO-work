#!/usr/bin/env python3
"""proprioception/demo.py — proves the PROPRIOCEPTION bottle fires on real
wiring, that leg selection follows the segmental neuromeres, and that the
reflex arc reads out at the efferent motor node. Exit 0 iff all checks pass.

Honesty: the cascade numbers are REAL wiring + MODEL dynamics; the leg model,
zero valence, and arousal gain are MODELED.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proprioception import Proprioception

ok = True

def check(name, cond, detail=""):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    ok = ok and cond

print("PROPRIOCEPTION bottle — live fire on real wiring")
p = Proprioception()

# 1. full-strength stimulus fires the cascade on real wiring
r = p.sense(1.0)
print(f"  sense(1.0) -> {r}")
check("cascade fires at full injection", r["activation"] > 0,
      f"(activation={r['activation']})")

# 2. leg selection works: each leg reads its own segmental neuromere,
#    and the activations differ by real wiring weights
rf = p.sense(1.0, leg="front")
rm = p.sense(1.0, leg="mid")
rh = p.sense(1.0, leg="hind")
print(f"  front -> {rf['activation']}, mid -> {rm['activation']}, "
      f"hind -> {rh['activation']}")
check("leg selection differentiates by neuromere",
      rf["activation"] > 0 and rm["activation"] > 0 and rh["activation"] > 0
      and not (rf["activation"] == rm["activation"] == rh["activation"]),
      "(front/pro-, mid/meso-, hind/metathoracic)")
check("leg label echoed", rf["leg"] == "front" and r["leg"] == "all")
try:
    p.sense(1.0, leg="wing")
    check("invalid leg rejected", False)
except ValueError:
    check("invalid leg rejected", True)

# 3. reflex_arc() reads the efferent motor node (hop 2) — nonzero at full hit
p.sense(1.0)
ra = p.reflex_arc()
check("reflex_arc() nonzero at full intensity", ra > 0,
      f"(efferent={ra})")

# 4. valence is zero: proprioception is informational, not valenced
check("valence is zero", r["valence_delta"] == 0.0,
      f"(valence_delta={r['valence_delta']})")

# 5. arousal is non-negative and proportional (gain 0.2)
check("arousal non-negative and proportional",
      r["arousal_delta"] >= 0 and
      abs(r["arousal_delta"] - 0.2 * r["activation"]) < 1e-3,
      f"(arousal_delta={r['arousal_delta']}, gain=0.2)")

# 6. graded response: a stronger stimulus never reads weaker
r_half = p.sense(0.5)
check("monotonic with intensity",
      r_half["activation"] <= r["activation"],
      f"(0.5 -> {r_half['activation']}, 1.0 -> {r['activation']})")

# 7. activation decays with tick()
p.sense(1.0)
d0 = p.state()["activation"]
p.tick(10.0)
d1 = p.state()["activation"]
check("tick() decays activation", d1 < d0,
      "(" + str(d0) + " -> " + str(d1) + ")")

# 8. silence is silence: zero stimulus, zero readout
r0 = p.sense(0.0)
check("zero stimulus reads zero", r0["activation"] == 0.0)

print("ALL CHECKS PASS" if ok else "SOMETHING FAILED")
sys.exit(0 if ok else 1)
