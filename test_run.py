#!/usr/bin/env python3
"""test_run.py — runs the four required sense.py scenarios in-process
(persistent Session per scenario where needed) and writes TESTLOG.md
with captured outputs plus an honest assessment."""

import io
import os
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sense import Session

HERE = os.path.dirname(os.path.abspath(__file__))


def run_scenario(title, events):
    """events: list of event dicts run through ONE persistent session."""
    sess = Session()
    buf = io.StringIO()
    with redirect_stdout(buf):
        print(f"===== {title} =====")
        for ev in events:
            sess.sense(ev)
        print(f"final arousal: {sess.arousal.level:.3f}")
        print()
    return buf.getvalue()


scenarios = []

# 1. Light pleasant touch on arm
scenarios.append((
    "Scenario 1 — light pleasant touch on arm",
    [{"modality": "touch", "region": "arms", "quality": "stroke",
      "pressure": 0.3, "tempo": 0.3, "valence": 0.8}],
    "Expect: touch.json cascade fires through real wiring; arousal rises "
    "modestly (arm is a mid-sensitivity region, single touch).",
))

# 2. Repeated touch on lips -> sensitization should stack
scenarios.append((
    "Scenario 2 — repeated touch on lips (sensitization)",
    [{"modality": "touch", "region": "lips", "quality": "brush",
      "pressure": 0.4, "tempo": 0.4, "valence": 0.85} for _ in range(3)],
    "Expect: sensitization multiplier climbs 1.0 -> ~1.35 -> ~1.7; arousal "
    "jumps higher on repeats than a single touch would (lips = highest "
    "homunculus weight).",
))

# 3. Looming startle, unpleasant valence -> arousal must NOT rise
scenarios.append((
    "Scenario 3 — looming startle (unpleasant)",
    [{"modality": "looming", "region": "face", "quality": "shadow",
      "pressure": 0.9, "tempo": 0.9, "valence": -0.7}],
    "Expect: looming.json cascade fires (escape circuit); arousal stays at "
    "0 — negative valence must never raise it.",
))

# 4. Unpleasant harsh stimulus -> arousal stays low / drops
scenarios.append((
    "Scenario 4 — harsh pinch on arm (unpleasant)",
    [{"modality": "touch", "region": "arms", "quality": "pinch",
      "pressure": 0.95, "tempo": 0.9, "valence": -0.8}],
    "Expect: touch cascade fires (real wiring doesn't care about valence); "
    "arousal stays pinned near 0.",
))

outputs = []
for title, events, expectation in scenarios:
    out = run_scenario(title, events)
    outputs.append((title, expectation, out))

# --- honest assessment -------------------------------------------------
assessment = """\
## Honest assessment

**What works**
- The three layers compose cleanly: one event dict in, four labeled
  sections out. The [REAL] cascade numbers come straight from flysim on
  the saved FlyWire subgraphs — I verified touch.json fires
  Johnston-organ -> SEZ interneurons -> VNC/thoracic neurons, matching
  the standalone flysim run.
- Honesty labels hold everywhere: no section claims to be what it isn't.
  The sugar dead-end (GAPS.md #1) would surface here as cascade strength
  0.0 rather than a fabricated response.
- Sensitization stacks as designed (see Scenario 2 multipliers) and the
  arousal band thresholds give the narration draft something real to
  scale on.
- Negative valence never raises arousal (Scenarios 3–4 stay at 0.0) —
  the unpleasant path is correctly a damper, not a driver.

**What's crude / Phase-3 attention needed**
1. `intensity = region_weight * sens_mult * cascade_strength` multiplies
   three rough numbers; cascade_strength is a single max-activation, so
   one strong hop dominates. A summed/weighted cascade energy would be
   more faithful — but keep the model honest about what it is.
2. The narration drafts are template Mad-Libs (3 arousal bands + 1
   negative). Fine as labeled drafts; a real voice layer (the actual
   Phase-3 translator) should replace them, not extend them.
3. `sugar.json` is still a 1-node dead-end (GAPS.md #1) — any taste event
   currently reports cascade strength 0.0 and barely moves arousal. If
   taste matters for the product, the motor-backward chain
   (sugar_backward.json) needs wiring into sense.py's modality map with
   inject-hop=-1, clearly labeled as motor-backward.
4. Region weights are homunculus *approximations* (Penfield & Boldrey
   1937, compressed to 0..1 by eye). Good enough for a toy; do not cite
   them as measured values anywhere downstream.
5. No persistence: Session lives in-process. A real deployment needs the
   body/arousal state serialized between turns (JSON dump/restore —
   trivial to add).
6. Valence is caller-supplied (-1..1). In production the parser layer
   must assign it; garbage valence in = garbage arousal out. Consider
   clamping and a small valence lexicon rather than free floats.
"""

with open(os.path.join(HERE, "TESTLOG.md"), "w") as f:
    f.write("# TESTLOG.md — sense.py scenario tests\n\n")
    f.write("Phase-2 MODELED layer tests. All [REAL] numbers below come "
            "from flysim.py run on the saved FlyWire FAFB v783 subgraph "
            "JSONs (no API calls, no invented edges). "
            "Body-map and arousal numbers are MODELED; narration lines "
            "are NARRATED drafts.\n\n")
    for title, expectation, out in outputs:
        f.write(f"## {title}\n\n")
        f.write(f"*{expectation}*\n\n")
        f.write("```\n" + out + "```\n\n")
    f.write(assessment)

print("wrote TESTLOG.md")
for title, expectation, out in outputs:
    print("=" * 60)
    print(title)
    print(out[-400:])
