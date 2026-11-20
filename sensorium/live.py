#!/usr/bin/env python3
"""live.py — the sensorium, always on.

The sensor is never "called" — it lives. Decay runs continuously on the
wall clock; events stream in on stdin; anyone can read the felt state at
any time with `feel`.

Commands (one per line):
    <modality> [intensity] [location]   e.g.  touch 0.5 antennae
    feel                                print the complete felt state
    quit
Modalities: touch sweet rot threat pain (+ temperature if its subgraph
resolved). Locations: antennae eyes_head proboscis legs wings abdomen.

Honesty: stdin events are TOY inputs; cascade numbers are REAL wiring +
MODEL dynamics; affect/body mapping is MODELED; mood words are FICTION.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sensorium import Sensorium
from body import REGIONS


def fmt_feel(f):
    h = f["hunger"]
    regs = " ".join(f"{r}:{v:.2f}" for r, v in f["regions"].items()
                    if v > 0.01) or "—"
    return (f"V={f['valence']:+.2f} A={f['arousal']:.2f} "
            f"mood={f['mood']:>9} hunger={h['hunger']:.2f} "
            f"pain={f['pain_level']:.2f} | {regs}")


def main():
    s = Sensorium()
    print("SENSORIUM live — decay always running. "
          f"modalities: {', '.join(sorted(s.channels))}")
    print("type '<modality> [intensity] [location]', 'feel', or 'quit'.")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        s.tick()  # wall-clock decay catches up before every input
        parts = line.split()
        cmd = parts[0].lower()
        if cmd in ("quit", "exit"):
            break
        if cmd == "feel":
            f = s.feel()
            print(fmt_feel(f))
            print(f"  channels: " + ", ".join(
                f"{m}={c['activation']:.3f}"
                for m, c in f["channels"].items() if c["activation"] > 0.001)
                or "quiet")
            continue
        try:
            modality = cmd
            intensity = float(parts[1]) if len(parts) > 1 else 0.5
            location = parts[2].lower() if len(parts) > 2 else None
            r = s.sense(modality, intensity, location)
            loc = f" @ {location}" if location else ""
            print(f"{modality} {intensity}{loc} -> "
                  f"dV={r['valence']:+.3f} A={r['arousal']:.3f} "
                  f"mood={r['mood']} | " +
                  " ".join(f"{rg}:{v:.2f}" for rg, v in r["regions"].items()
                           if v > 0.01) or "—")
        except ValueError as e:
            print(f"  ! {e}")
        except (IndexError, TypeError):
            print("  ! usage: <modality> [intensity 0..1] [location]")
    print("sensorium sleeps.")


if __name__ == "__main__":
    main()
