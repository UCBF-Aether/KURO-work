#!/usr/bin/env python3
"""build_touch_qualities.py — walk downstream from DISTINCT mechanosensory
classes, one per touch quality, using ONLY real VFBquery/FlyWire connectivity.

  touch_brush.json     light brush  -> bristle mechanoreceptors
  touch_pressure.json  deep pressure -> campaniform sensilla (strain sensors)
  touch_vibration.json vibration    -> Johnston's organ (as in touch.json)

Every kept edge is a real API row. Where the API indexes no downstream
wiring for a class, the walk honestly saves a 0-edge stub (same pattern as
sugar.json) and the gap is documented in GAPS.md. Nothing is invented.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_graphs import build

STIMULI = {
    "touch_brush": {
        # FBbt_00048508 "bristle mechanosensory neuron" verified: API
        # returns 0 downstream rows in every query form (see GAPS.md).
        "hop0": [("FBbt_00048508",
                  "bristle mechanosensory neuron",
                  "bristle mechanosensory neuron")],
        "branch": [5, 3],
        "behavior": {
            "text": "Light touch: bristle deflection drives bristle "
                    "mechanoreceptors; the fly registers gentle contact.",
            "basis": "textbook Drosophila bristle mechanosensation; stated "
                     "as known biology — the API indexes no downstream "
                     "wiring for this class (see GAPS.md), so no circuit "
                     "is simulated",
        },
        "fly_narration": "A whisper of touch \u2014 notice.",
    },
    "touch_pressure": {
        # FBbt_00048057 "campaniform sensillum neuron" verified: API
        # returns 0 downstream rows in every query form (see GAPS.md).
        # Campaniform sensilla are cuticular strain (pressure/load) sensors.
        "hop0": [("FBbt_00048057",
                  "campaniform sensillum neuron",
                  "campaniform sensillum neuron")],
        "branch": [5, 3],
        "behavior": {
            "text": "Firm pressure: cuticular strain drives campaniform "
                    "sensilla; the fly registers load and pressure.",
            "basis": "textbook Drosophila campaniform strain sensing; "
                     "stated as known biology \u2014 the API indexes no "
                     "downstream wiring for this class (see GAPS.md), so "
                     "no circuit is simulated",
        },
        "fly_narration": "Weight pressing \u2014 bear it.",
    },
    "touch_vibration": {
        # Johnston's organ: the API-indexed antennal vibration sensor
        # (same walk as touch.json, rebuilt under the quality name).
        "hop0": [("FBbt_00100000",
                  "Johnston organ neuron",
                  "FBbt_00100000")],
        "branch": [6, 3],
        "behavior": {
            "text": "Vibration: antennal oscillation drives Johnston's "
                    "organ; the fly registers buzzing movement and braces.",
            "basis": "textbook Johnston's organ -> AMMC/AVLP -> descending "
                     "pathway",
        },
        "fly_narration": "The world jolts \u2014 brace.",
    },
}

if __name__ == "__main__":
    which = sys.argv[1:] or list(STIMULI)
    for stim in which:
        try:
            build(stim, STIMULI[stim])
        except Exception as e:
            print(f"== {stim} == FAILED: {e}", flush=True)
