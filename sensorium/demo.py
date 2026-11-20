#!/usr/bin/env python3
"""demo.py — a felt-life trace proving the sensorium is alive.

Deterministic (fake clock). Event sequence:
  1. three gentle touches (0.3)        -> arousal bumps SHRINK (habituation)
  2. hard noxious event (pain 1.0)     -> arousal spikes, valence hard
                                         negative, mood recoiling
  3. sweet (0.8) DURING pain           -> valence response blunted ~zero
                                         (appetite suppression)
  4. 30 s silence                      -> pain decays
  5. sweet (1.0) again                 -> lands: valence climbs, hunger hit
  6. 30 s silence                      -> everything decays toward neutral

Asserts: (a) touch arousal bumps shrink; (b) pain arousal exceeds any other
channel's; (c) sweet blunted while pain active, restored after; (d) decay to
neutral in silence. Exit 0 iff all hold.

Honesty: the "events" are scripted demo inputs; cascade numbers are REAL
wiring + MODEL dynamics; affect is MODELED; mood words are FICTION glosses.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sensorium import Sensorium


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def main():
    clock = FakeClock()
    s = Sensorium(clock=clock)
    print(f"pain channel: {os.path.basename(s.pain_source)} "
          f"(proxy={s.pain_is_proxy}) — see module docstring")
    print("=" * 78)

    bumps = {}   # modality -> list of arousal deltas

    def event(modality, intensity, note=""):
        before = (s.valence, s.arousal)
        r = s.sense(modality, intensity)
        da = s.arousal - before[1]
        dv = s.valence - before[0]
        bumps.setdefault(modality, []).append(da)
        tag = f"  [{note}]" if note else ""
        print(f"{modality:>6} {intensity:.1f} | eff={r['effective']:.4f} "
              f"nov={r['novelty']:.3f} | dV={dv:+.4f} dA={da:+.4f} | "
              f"V={r['valence']:+.3f} A={r['arousal']:.3f} "
              f"mood={r['mood']:>9} pain={r['pain_level']:.2f}{tag}")
        return r, dv, da

    def silence(secs, note=""):
        clock.advance(secs)
        st = s.state()
        print(f"--- {secs}s silence{': ' + note if note else ''} -> "
              f"V={st['valence']:+.3f} A={st['arousal']:.3f} "
              f"pain={st['pain_level']:.2f} mood={st['mood']}")
        return st

    print("-- gentle touches (habituation) --")
    for i in range(3):
        event("touch", 0.3, f"touch #{i + 1}")

    print("-- noxious event --")
    r_pain, dv_pain, da_pain = event("pain", 1.0, "noxious")

    print("-- sweet offered DURING pain (appetite suppression) --")
    v_before = s.valence
    r_blunt, dv_blunt, _ = event("sweet", 0.8, "blunted?")
    sweet_blunted_dv = dv_blunt

    silence(30, "pain decays")

    print("-- sweet offered again (restored) --")
    r_sweet, dv_sweet, da_sweet = event("sweet", 1.0)
    if r_sweet["hunger_event"]:
        print("         ^-- hunger took the hit "
              f"(spike={r_sweet['hunger_event']['spike']:.3f})")
    sweet_restored_dv = dv_sweet

    st_end = silence(30, "everything settles")

    print("=" * 78)
    ok = True

    # (a) touch arousal bumps shrink across the three gentle touches
    tb = bumps["touch"]
    a = len(tb) == 3 and tb[0] > tb[1] > tb[2] > 0
    print(f"(a) TOUCH HABITUATION  bumps "
          f"{' > '.join(f'{b:.4f}' for b in tb)}  [{'PASS' if a else 'FAIL'}]")
    ok &= a

    # (b) pain arousal bump exceeds any other channel's biggest bump
    pain_bump = max(bumps["pain"])
    other_bump = max(b for m, bs in bumps.items() if m != "pain" for b in bs)
    b = pain_bump > other_bump
    print(f"(b) PAIN DOMINANCE  pain arousal bump {pain_bump:.3f} > "
          f"best other {other_bump:.3f}  [{'PASS' if b else 'FAIL'}]")
    ok &= b
    # mood read hurt/recoiling at the noxious event
    b2 = r_pain["mood"] in ("hurt", "recoiling")
    print(f"    mood at noxious event: {r_pain['mood']}  "
          f"[{'PASS' if b2 else 'FAIL'}]")
    ok &= b2
    # valence went hard negative
    b3 = r_pain["valence"] <= -0.5
    print(f"    valence at noxious event: {r_pain['valence']:+.3f}  "
          f"[{'PASS' if b3 else 'FAIL'}]")
    ok &= b3

    # (c) sweet blunted while pain active, restored after
    c1 = abs(sweet_blunted_dv) < 0.01
    print(f"(c) APPETITE SUPPRESSION  sweet-during-pain dV={sweet_blunted_dv:+.4f} "
          f"(~zero)  [{'PASS' if c1 else 'FAIL'}]")
    ok &= c1
    c2 = sweet_restored_dv > 0.1
    print(f"    sweet-after-silence dV={sweet_restored_dv:+.4f} "
          f"(restored)  [{'PASS' if c2 else 'FAIL'}]")
    ok &= c2

    # (d) decay to neutral in silence
    d = (abs(st_end["valence"]) < 0.05 and st_end["arousal"] < 0.05
         and st_end["pain_level"] < 0.05 and st_end["mood"] == "calm")
    print(f"(d) DECAY TO NEUTRAL  V={st_end['valence']:+.3f} "
          f"A={st_end['arousal']:.3f} pain={st_end['pain_level']:.2f} "
          f"mood={st_end['mood']}  [{'PASS' if d else 'FAIL'}]")
    ok &= d

    print("=" * 78)
    print("SENSORIUM ALIVE" if ok else "SOMETHING FAILED — see trace above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
