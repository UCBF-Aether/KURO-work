#!/usr/bin/env python3
"""punishment/demo.py — proves the PUNISHMENT bottle fires on real wiring,
carries negative valence, and reaches the mushroom body. Exit 0 iff all
checks pass.

Honesty: the cascade numbers are REAL wiring + MODEL dynamics; the sign
conventions and the opponent note are MODELED.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from punishment import Punishment

ok = True

def check(name, cond, detail=""):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    ok = ok and cond

print("PUNISHMENT bottle — live fire on real wiring")
p = Punishment()

# 1. full-strength stimulus fires the cascade on real wiring
r = p.sense(1.0)
print(f"  sense(1.0) -> {r}")
check("cascade fires at full injection", r["activation"] > 0,
      f"(activation={r['activation']})")

# 2. valence sign is correct: punishment is the negative teaching signal
check("valence sign correct (negative)",
      r["valence_delta"] < 0,
      f"(valence_delta={r['valence_delta']})")

# 3. arousal is non-negative and scales with activation
check("arousal non-negative and proportional",
      r["arousal_delta"] >= 0 and
      abs(r["arousal_delta"] - 0.8 * r["activation"]) < 1e-3,
      f"(arousal_delta={r['arousal_delta']}, gain=0.8)")

# 4. MB compartments reached: hop-1 readout carries real signal
from punishment import READOUT_HOP
import json
g = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "subgraphs", "punishment.json")))
hop1_ids = [n["id"] for n in g["nodes"] if n.get("hop") == 1]
snaps = p._cascade(1.0)
peak1 = max((s.get(nid, 0.0) for s in snaps for nid in hop1_ids), default=0.0)
mb_ids = [n["id"] for n in g["nodes"]
          if "mushroom body" in n.get("name", "").lower()]
peak_mb = max((s.get(nid, 0.0) for s in snaps for nid in mb_ids), default=0.0)
check("MB compartments reached (hop 1 carries signal)",
      peak1 > 0 and peak_mb > 0,
      f"(hop1 peak={round(peak1, 4)}, MB peak={round(peak_mb, 4)})")

# 5. graded response: a stronger stimulus never reads weaker
r_half = p.sense(0.5)
check("monotonic with intensity",
      r_half["activation"] <= r["activation"],
      f"(0.5 -> {r_half['activation']}, 1.0 -> {r['activation']})")

# 6. activation decays with tick()
p.sense(1.0)
d0 = p.state()["activation"]
p.tick(10.0)
d1 = p.state()["activation"]
check("tick() decays activation", d1 < d0,
      "(" + str(d0) + " -> " + str(d1) + ")")

# 7. opponent() documents the PAM/PPL1 contrast
o = p.opponent()
check("opponent() carries the contrast note",
      o["note"].startswith("PAM (reward) and PPL1 (punishment)"),
      f"({o['note'][:40]}...)")

# 8. silence is silence: zero stimulus, zero readout
r0 = p.sense(0.0)
check("zero stimulus reads zero", r0["activation"] == 0.0)

print("ALL CHECKS PASS" if ok else "SOMETHING FAILED")
sys.exit(0 if ok else 1)
