#!/usr/bin/env python3
"""build_reward.py — walk downstream from PAM dopaminergic neurons using ONLY
real VFBquery/FlyWire connectivity. Saves subgraphs/reward.json.

PAM (protocerebral anterior medial) dopaminergic neurons signal reward TO the
mushroom body; walking downstream follows the reward signal into MB targets.
Every kept edge is a real API row. Nothing is invented.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_graphs import build

# "dopaminergic PAM neuron 1" (label form) verified: 93 grouped rows.
# (The general "adult dopaminergic PAM neuron" class truncates the API
# response — see GAPS.md.)
CFG = {
    "hop0": [("dopaminergic PAM neuron 1",
              "dopaminergic PAM neuron 1",
              "dopaminergic PAM neuron 1")],
    "branch": [5, 3],
    "behavior": {
        "text": "Reward signaling: PAM cluster dopaminergic neurons convey "
                "reward to the mushroom body, reinforcing the associated "
                "stimulus/context.",
        "basis": "textbook Drosophila reward circuit (PAM DANs -> mushroom "
                 "body Kenyon cells / MBONs); stated as known biology",
    },
    "fly_narration": "Good \u2014 remember this.",
}

if __name__ == "__main__":
    build("reward", CFG)
