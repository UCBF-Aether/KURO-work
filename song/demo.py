#!/usr/bin/env python3
"""song/demo.py — proves the SONG bottle runs the hypothesized JO-B ->
AMMC-B1 -> vPN1 -> pC1 chain end to end. Exit 0 iff all checks pass.

Honesty: the chain is LITERATURE-HYPOTHESIS (no API rows exist for it —
see song.py contract); the cascade numbers are hypothesis edges + TOY
dynamics; the sign conventions are MODELED.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from song import Song

ok = True

def check(name, cond, detail=""):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    ok = ok and cond

print("SONG bottle — live fire on the literature chain")
s = Song()

# 1. the chain runs end to end: full stimulus reaches pC1 (hop 3)
r = s.sense(1.0)
print(f"  sense(1.0) -> {r}")
check("chain runs end to end (JO-B..pC1)",
      r["activation"] == 1.0,
      f"(activation={r['activation']})")

# 2. pC1_drive() reads the meeting point with the mating chain
check("pC1_drive() nonzero at full intensity",
      s.pC1_drive() == 1.0,
      f"(pC1_drive={s.pC1_drive()})")

# 3. valence sign is positive (courtship song is appetitive in context)
check("valence sign positive",
      r["valence_delta"] > 0,
      f"(valence_delta={r['valence_delta']}, sign=+0.40)")

# 4. arousal scales with activation at the documented gain
check("arousal proportional at gain 0.7",
      abs(r["arousal_delta"] - 0.7 * r["activation"]) < 1e-3,
      f"(arousal_delta={r['arousal_delta']})")

# 5. graded response: stronger stimulus never reads weaker
r_half = s.sense(0.5)
check("monotonic with intensity",
      r_half["activation"] <= r["activation"] and r_half["activation"] > 0,
      f"(0.5 -> {r_half['activation']}, 1.0 -> {r['activation']})")

# 6. threshold cliff is honest: below 0.15 the model stays silent
r_low = s.sense(0.1)
check("threshold cliff (silent below 0.15)",
      r_low["activation"] == 0.0,
      f"(0.1 -> {r_low['activation']})")

# 7. activation decays with tick()
s.sense(1.0)
d0 = s.state()["activation"]
s.tick(10.0)
d1 = s.state()["activation"]
check("tick() decays activation", d1 < d0,
      "(" + str(d0) + " -> " + str(d1) + ")")

# 8. every edge in the graph carries its provenance label and citation —
#    the honesty contract is enforced in code, not just in prose
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "subgraphs", "song_lit.json")) as f:
    graph = json.load(f)
edges = graph["edges"]
check("all edges carry provenance + citation",
      len(edges) > 0 and
      all(e.get("provenance") and e.get("citation") for e in edges),
      f"({len(edges)} edges)")

print("ALL CHECKS PASS" if ok else "SOMETHING FAILED")
sys.exit(0 if ok else 1)
