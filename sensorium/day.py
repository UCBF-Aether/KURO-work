#!/usr/bin/env python3
"""day.py — a day in the life of the sensorium.

Deterministic (fake clock). Not a test suite: an organism's day, printed
as a felt trace — time, valence, arousal, mood, hunger, and where on the
body the day lands.

  06:00  dawn. never fed: hunger high, mood hungry.
  06:05  grooming touches.
  08:00  a sweet meal: valence climbs, hunger takes the hit, settles.
  10:00  touches on the legs.
  12:00  bad air (rot): valence dips, repelled.
  14:00  afternoon heat (temperature, if its channel resolved).
  15:30  a noxious event: pain disrupts the day; sweetness can't land.
  17:00  quiet recovery.
  18:00  a small sweet: the day is edible again.
  20:00  dusk: long silence, everything settles to calm.

Light assertions: dawn mood is hungry/restless with high hunger; the pain
event disrupts (valence negative, mood recoiling); evening ends calm.
Exit 0 iff all hold.

Honesty: scripted demo inputs; REAL wiring + MODEL dynamics; MODELED affect;
FICTION mood words.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sensorium import Sensorium


class FakeClock:
    def __init__(self):
        self.t = 0.0  # seconds since 06:00

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt

    def hhmm(self):
        m = 360 + int(self.t // 60)
        return f"{m // 60:02d}:{m % 60:02d}"


def main():
    clock = FakeClock()
    s = Sensorium(clock=clock)
    print("a day in the life — "
          f"temperature channel: {'REAL' if s.has_temperature else 'absent'}")
    print("=" * 78)

    marks = {}

    def note(text):
        print(f"-- {text} --")

    def event(modality, intensity=0.5, location=None, mark=None):
        r = s.sense(modality, intensity, location)
        loc = f" @ {location}" if location else ""
        regs = " ".join(f"{rg}:{v:.2f}"
                        for rg, v in r["regions"].items() if v > 0.005)
        print(f"{clock.hhmm()}  {modality:>6} {intensity:.1f}{loc:<10} | "
              f"V={r['valence']:+.3f} A={r['arousal']:.3f} "
              f"mood={r['mood']:>9} hunger={s.hunger.state()['hunger']:.2f} "
              f"| {regs or '—'}")
        if mark:
            marks[mark] = r
        return r

    def wait(secs, mark=None):
        clock.advance(secs)
        f = s.feel()
        regs = " ".join(f"{rg}:{v:.2f}"
                        for rg, v in f["regions"].items() if v > 0.005)
        print(f"{clock.hhmm()}  {'···':>6} {'':<14} | "
              f"V={f['valence']:+.3f} A={f['arousal']:.3f} "
              f"mood={f['mood']:>9} hunger={f['hunger']['hunger']:.2f} "
              f"| {regs or '—'}")
        if mark:
            marks[mark] = f
        return f

    # 06:00 dawn — never fed
    note("dawn. the fly wakes. it has never eaten.")
    f0 = s.feel()
    marks["dawn"] = {"mood": f0["mood"],
                     "hunger": f0["hunger"]["hunger"]}
    print(f"{clock.hhmm()}  wake | V={f0['valence']:+.3f} A={f0['arousal']:.3f} "
          f"mood={f0['mood']:>9} hunger={f0['hunger']['hunger']:.2f}")
    wait(300)  # -> 06:05

    # 06:05 grooming
    note("morning grooming — antennae brushed clean")
    event("touch", 0.2, location="antennae")
    wait(6900)  # -> 08:00

    # 08:00 a sweet meal
    note("a sweet meal")
    event("sweet", 1.0, mark="meal")
    wait(7200)  # -> 10:00

    # 10:00 touches on the legs
    note("mid-morning — brushed legs on a leaf edge")
    event("touch", 0.4, location="legs")
    wait(7200)  # -> 12:00

    # 12:00 bad air
    note("midday — rot on the wind")
    event("rot", 0.7, mark="rot")
    wait(7200)  # -> 14:00

    # 14:00 afternoon heat (only if the channel resolved from real wiring)
    if s.has_temperature:
        note("afternoon heat on the arista")
        event("temperature", 0.6, mark="heat")
    wait(5400)  # -> 15:30

    # 15:30 a noxious event — the day breaks
    note("a noxious event — the day breaks")
    event("pain", 1.0, mark="pain")
    note("sweetness offered while it hurts — nothing lands")
    event("sweet", 0.8, mark="blunted")
    wait(5400)  # -> 17:00

    # 17:00 quiet recovery
    note("quiet recovery")
    wait(3600)  # -> 18:00

    # 18:00 a small sweet — the day is edible again
    note("evening — a small sweet. the day is edible again.")
    event("sweet", 0.7, mark="evening_sweet")
    wait(7200)  # -> 20:00

    # 20:00 dusk — long silence
    note("dusk")
    wait(0, mark="dusk")

    print("=" * 78)
    ok = True

    a = (marks["dawn"]["mood"] in ("hungry", "restless")
         and marks["dawn"]["hunger"] >= 0.7)
    print(f"(a) DAWN HUNGRY  mood={marks['dawn']['mood']} "
          f"hunger={marks['dawn']['hunger']:.2f}  [{'PASS' if a else 'FAIL'}]")
    ok &= a

    p = marks["pain"]
    b = p["valence"] <= -0.5 and p["mood"] == "recoiling"
    print(f"(b) PAIN DISRUPTS  V={p['valence']:+.3f} mood={p['mood']}  "
          f"[{'PASS' if b else 'FAIL'}]")
    ok &= b
    bl = marks["blunted"]
    b2 = abs(bl["valence"] - p["valence"]) < 0.05
    print(f"    sweet-during-pain blunted  "
          f"[{'PASS' if b2 else 'FAIL'}]")
    ok &= b2

    d = marks["dusk"]
    c = d["mood"] == "calm" and abs(d["valence"]) < 0.05 and d["arousal"] < 0.05
    print(f"(c) DUSK CALM  mood={d['mood']} V={d['valence']:+.3f} "
          f"A={d['arousal']:.3f}  [{'PASS' if c else 'FAIL'}]")
    ok &= c

    print("=" * 78)
    print("A DAY LIVED" if ok else "SOMETHING FAILED — see trace above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
