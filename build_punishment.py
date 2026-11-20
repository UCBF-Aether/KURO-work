#!/usr/bin/env python3
"""build_punishment.py — walk downstream from PPL1 dopaminergic neurons using
ONLY real VFBquery/FlyWire connectivity. Saves subgraphs/punishment.json.

PPL1 (posterior superior lateral protocerebrum 1) dopaminergic neurons signal
punishment TO the mushroom body — the dark twin of the PAM reward circuit
(reward.json). Walking downstream follows the aversive signal into MB targets.
Every kept edge is a real API row. Nothing is invented.

hop0 = merged walk from two canonical aversive PPL1 DANs (documented merge,
like the pheromone build):
  - PPL1-gamma1pedc (FBbt_00100243, aka PPL101/MB-MP1) — ID form query works
    (162 rows); label form returns 0 rows.
  - PPL1-alpha3 (FBbt_00110320, "MB-alpha neuron of the dopaminergic PPL1
    cluster") — label form works (114 rows).
The general "dopaminergic PPL1 neuron" class (FBbt_00100219) fails server-side
in every form; "dopaminergic PPL1 neuron 2" fails; MB-SV (FBbt_00110323)
returns 0 rows (see GAPS.md).
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_graphs import build

CFG = {
    "hop0": [
        ("FBbt_00100243",
         "PPL1-gamma1pedc (dopaminergic PPL1 neuron)",
         "FBbt_00100243"),
        ("FBbt_00110320",
         "MB-alpha neuron of the dopaminergic PPL1 cluster",
         "MB-alpha neuron of the dopaminergic PPL1 cluster"),
    ],
    "branch": [5, 3],
    "behavior": {
        "text": "Punishment learning: PPL1 cluster dopaminergic neurons convey "
                "aversive reinforcement to the mushroom body, depressing the "
                "associated stimulus/context.",
        "basis": "textbook Drosophila aversive circuit (PPL1 DANs -> mushroom "
                 "body Kenyon cells / MBONs of the aversive compartments); "
                 "stated as known biology",
    },
    "fly_narration": "Bad \u2014 never again.",
}

HONEST_NOTE = (
    "PAM/PPL1 OPPONENT ORGANIZATION: the mushroom body is tiled into "
    "compartments, each co-innervated by dopaminergic neurons (DANs) and "
    "mushroom body output neurons (MBONs). PAM-cluster DANs (reward.json: "
    "'dopaminergic PAM neuron 1') innervate APPETITIVE compartments and drive "
    "approach learning; PPL1-cluster DANs (this file: PPL1-gamma1pedc + "
    "PPL1-alpha3) innervate AVERSIVE compartments and drive avoidance "
    "learning. Same MB architecture, opponent valence — reward and "
    "punishment are the two halves of one teaching signal. "
    "Query notes: general 'dopaminergic PPL1 neuron' (FBbt_00100219) fails "
    "server-side in all forms; 'dopaminergic PPL1 neuron 2' fails; MB-SV "
    "(FBbt_00110323) returns 0 rows — all logged in GAPS.md. hop0 is a "
    "documented merge of the two canonical aversive PPL1 DANs whose "
    "connectivity is indexed."
)

if __name__ == "__main__":
    build("punishment", CFG)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "subgraphs", "punishment.json")
    with open(path) as f:
        g = json.load(f)
    g["honest_note"] = HONEST_NOTE
    with open(path, "w") as f:
        json.dump(g, f, indent=1)
    print("honest_note injected")
