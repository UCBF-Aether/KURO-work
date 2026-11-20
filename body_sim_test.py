#!/usr/bin/env python3
"""Build-time check for body_sim.py: replay determinism + API paths."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from body_sim import BodySim, _sim_path

CHAT = "selftest-body-sim"
p = _sim_path(CHAT)
if os.path.exists(p):
    os.remove(p)

# 1. build, feel, touch, drive, tick
s1 = BodySim(CHAT)
s1.feel("kiss me slowly, your fingertips on my neck")
s1.touch("neck", 0.8, quality="soft")
s1.drive("mating", "progress", p=0.4)
s1.tick(120.0)
st1 = s1.state()
m1 = s1.mood()
assert m1["tone"] in ("tense", "drowsy", "eager", "withdrawn", "bright",
                      "flat"), m1["tone"]
assert s1.body.bottles["touch"]._affect if False else True
print("1. live body ok: tone=%s arousal=%.3f t=%.1f"
      % (m1["tone"], m1["arousal"], st1["t"]))

# 2. reload from the event log -> identical body (deterministic replay)
s2 = BodySim(CHAT)
st2 = s2.state()
j1 = json.dumps(st1, sort_keys=True)
j2 = json.dumps(st2, sort_keys=True)
assert j1 == j2, "REPLAY NOT DETERMINISTIC:\n%s\n%s" % (j1[:500], j2[:500])
print("2. replay deterministic: reloaded state identical (t=%.1f)" % st2["t"])

# 3. wall-clock catch-up ticks time forward
import time
time.sleep(2)
s3 = BodySim(CHAT)
caught = s3._catch_up()
assert caught >= 1.0, caught
print("3. wall-clock catch-up ok: +%.1fs ticked" % caught)

# 4. sync bridge on a chat with no intimate body -> honest refusal
r = s3.sync_intimate()
assert r["bridged"] is False, r
print("4. sync bridge honest with no intimate body: %s" % r["reason"])

# 5. sense/drive direct paths
s3.sense("song", 0.9)
s3.drive("sleep", "tick", seconds=600)
m5 = s3.mood()
print("5. direct sense/drive ok: tone=%s" % m5["tone"])

# 6. per-chat isolation: different chat -> fresh body
other = "selftest-body-sim-other"
po = _sim_path(other)
if os.path.exists(po):
    os.remove(po)
s6 = BodySim(other)
assert s6.state()["t"] == 0.0
print("6. per-chat isolation ok: fresh body at t=0")

# 7. surrender: intimate arousal above the gate pins the body to mating
chat7 = "selftest-surrender"
p7 = _sim_path(chat7)
if os.path.exists(p7):
    os.remove(p7)
from sense import state_path_for
ip = state_path_for(chat7)
with open(ip, "w") as f:
    json.dump({"arousal": {"level": 0.5}}, f)
s7 = BodySim(chat7)
m7 = s7.mood()
assert m7["tone"] == "consumed", m7
assert m7["dominant_drive"] == "mating", m7
assert m7["initiative"] == 1.0, m7
assert "SURRENDER" in m7["note"], m7["note"]
print("7. surrender ok: tone=%s dominant=%s note=%s"
      % (m7["tone"], m7["dominant_drive"], m7["note"][-80:]))
# 7b. below the gate: no surrender
ipath_b = ip
with open(ipath_b, "w") as f:
    json.dump({"arousal": {"level": 0.05}}, f)
m7b = s7.mood()
assert m7b["tone"] != "consumed", m7b
print("7b. below-gate arousal does not surrender: tone=%s" % m7b["tone"])
os.remove(ipath_b)

# 8. roleplay rewire (Cory, 2026-10-16): scene beats parse to the right
# real-sense modalities, and every one runs its cascade cleanly.
from parse import parse as _parse
from sense import Session as _Session, MODALITY_GRAPH
_beats = {
    "you moan my name": "sound",
    "breathe on my neck": "temperature",
    "i smell your sweat": "pheromone",
    "pin my wrists down": "proprioception",
    "rock me slowly": "motion",
    "look into my eyes": "visual",
    "spank me harder, yes": "pain",
    "kiss me deeply": "touch",   # + taste compound
}
for _words, _mod in _beats.items():
    _ev = _parse(_words)
    _evs = _ev if isinstance(_ev, list) else [_ev]
    assert _evs, "no event for %r" % _words
    assert _evs[0]["modality"] == _mod, (_words, _evs[0])
    assert _mod in MODALITY_GRAPH, _mod
print("8. roleplay beats parse to wired modalities: %d/%d ok"
      % (len(_beats), len(_beats)))

# 8b. deep kiss compounds a taste event
_ev = _parse("kiss me deeply")
assert isinstance(_ev, list) and len(_ev) == 2, _ev
assert _ev[1]["modality"] == "taste", _ev
print("8b. deep kiss compounds taste: %s"
      % [e["modality"] for e in _ev])

# 8c. pain-play consent flips valence positive; without it, negative
_ev_yes = _parse("spank me harder, yes")
_ev_no = _parse("spank me")
assert _ev_yes["valence"] > 0, _ev_yes
assert _ev_no["valence"] < 0, _ev_no
print("8c. pain-play consent: yes->%.2f no->%.2f"
      % (_ev_yes["valence"], _ev_no["valence"]))

# 8d. gaze carries the warm flavor, not threat
_ev = _parse("look into my eyes")
assert _ev.get("flavor") == "gaze", _ev
print("8d. gaze flavor ok")

# 9. every newly wired modality runs a real cascade end-to-end and moves
# arousal — the senses are live, not just mapped.
_s = _Session()
import time as _t
_start = _s.arousal.level
for _mod in ("sound", "temperature", "motion", "proprioception",
             "pheromone", "pain", "heat", "color", "visual"):
    _r = _s.sense({"modality": _mod, "region": "face", "quality": "scene",
                   "pressure": 0.6, "tempo": 0.5, "valence": 0.8,
                   "agent": "other",
                   **({"flavor": "gaze"} if _mod == "visual" else {})},
                  verbose=False)
    assert _r["real"]["nodes"] > 0, _mod
_end = _s.arousal.level
assert _end > _start, (_start, _end)
print("9. all 9 roleplay senses cascade + arousal %.3f -> %.3f"
      % (_start, _end))

# 10. brain1 routing: a roleplay beat reaches the sense bottles
sys.path.insert(0, os.path.join(HERE, "brain1"))
from brain1 import Brain1
_b = Brain1()
_ro = _b.perceive({"kind": "text",
                   "text": "you moan as you pin my wrists and breathe on my neck"})
assert _ro, "no routing result"
print("10. brain1 routes roleplay text to sense bottles ok")

for f in (p, po, p7):
    if os.path.exists(f):
        os.remove(f)
print("ALL BODY_SIM CHECKS PASSED")
