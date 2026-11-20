#!/usr/bin/env python3
"""color/demo.py — proves the COLOR bottle fires on real wiring with the
correct informational (zero-valence) convention, and that the Dm8-family
branch readout behaves. Exit 0 iff all checks pass.

Honesty: the cascade numbers are REAL wiring + MODEL dynamics; the valence
convention, channel selection, and opponency() readout are MODELED.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from color import Color, R7_ID, R8_ID, DM8_IDS

ok = True

def check(name, cond, detail=""):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    ok = ok and cond

print("COLOR bottle — live fire on real wiring")
c = Color()

# 1. full-strength stimulus fires the cascade on real wiring, all channels
for ch in ("r7", "r8", "both"):
    r = c.sense(1.0, channel=ch)
    print(f"  sense(1.0, channel={ch!r}) -> {r}")
    check(f"cascade fires at full injection ({ch})", r["activation"] > 0,
          f"(activation={r['activation']})")
    check(f"channel echoed back ({ch})", r["channel"] == ch)

# 2. the textbook R7->Dm8 pathway is present in the real rows
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "subgraphs", "color.json")) as f:
    graph = json.load(f)
r7_dm8 = [e for e in graph["edges"]
          if e["pre"] == R7_ID and e["post"] in DM8_IDS]
check("R7->Dm8-family edges present in real rows", len(r7_dm8) >= 4,
      f"({len(r7_dm8)} edges: " +
      ", ".join(f"{e['post'].split()[-1]}={e['weight']}" for e in r7_dm8) + ")")

# 3. opponency() reads nonzero when the channels differ at Dm8
c.sense(1.0, channel="r7")
opp = c.opponency()
check("opponency() nonzero when channels differ", opp > 0,
      f"(opponency={opp})")

# 4. color is informational: valence stays 0.0 even at full activation
r = c.sense(1.0, channel="both")
check("valence is 0.0 (informational)", r["valence_delta"] == 0.0,
      f"(valence_delta={r['valence_delta']})")

# 5. arousal is non-negative and proportional
check("arousal non-negative and proportional",
      r["arousal_delta"] >= 0 and
      abs(r["arousal_delta"] - 0.3 * r["activation"]) < 1e-3,
      f"(arousal_delta={r['arousal_delta']}, gain=0.3)")

# 6. graded response: a stronger stimulus never reads weaker
r_half = c.sense(0.5, channel="both")
check("monotonic with intensity",
      r_half["activation"] <= r["activation"],
      f"(0.5 -> {r_half['activation']}, 1.0 -> {r['activation']})")

# 7. invalid channel is rejected, not silently mapped
try:
    c.sense(0.5, channel="r9")
    check("invalid channel raises ValueError", False)
except ValueError:
    check("invalid channel raises ValueError", True)

# 8. activation decays with tick()
c.sense(1.0)
d0 = c.state()["activation"]
c.tick(10.0)
d1 = c.state()["activation"]
check("tick() decays activation", d1 < d0,
      "(" + str(d0) + " -> " + str(d1) + ")")

# 9. silence is silence: zero stimulus, zero readout
r0 = c.sense(0.0)
check("zero stimulus reads zero", r0["activation"] == 0.0)

print("ALL CHECKS PASS" if ok else "SOMETHING FAILED")
sys.exit(0 if ok else 1)
