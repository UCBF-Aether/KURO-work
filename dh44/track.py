#!/usr/bin/env python3
"""track.py — CLI wrapper so any agent (or human) can run the DH44 drive live.

Persists drive state to state.json in this directory (wall clock).
Usage:
    python3 track.py start <category> [difficulty]
    python3 track.py progress <0..1>
    python3 track.py done | fail | state | reset
"""
import json
import os
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
sys.path.insert(0, HERE)
from dh44 import Dh44  # noqa: E402


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            d = json.load(f)
        h = Dh44()
        h.wanting = d["wanting"]
        h.drive_signal = d["drive_signal"]
        h.satiation = d["satiation"]
        h.habituation = defaultdict(float,
                                    {k: float(v) for k, v in
                                     d["habituation"].items()})
        h.last_spike = d["last_spike"]
        h.category = d["category"]
        h.difficulty = d["difficulty"]
        now = time.monotonic()
        h._clock = time.monotonic
        h._last = now
        h.refractory_until = now + d["refractory_until"]
        return h
    return Dh44()


def save(h):
    now = time.monotonic()
    with open(STATE, "w") as f:
        json.dump({
            "wanting": h.wanting,
            "drive_signal": h.drive_signal,
            "satiation": h.satiation,
            "habituation": dict(h.habituation),
            "refractory_until": max(0.0, h.refractory_until - now),
            "last_spike": h.last_spike,
            "category": h.category,
            "difficulty": h.difficulty,
        }, f, indent=1)


def show(d):
    for k, v in d.items():
        print(f"  {k}: {v}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "state"
    if cmd == "reset":
        if os.path.exists(STATE):
            os.remove(STATE)
        print("dh44 drive state cleared")
        return
    h = load()
    if cmd == "start":
        cat = sys.argv[2] if len(sys.argv) > 2 else "uncategorized"
        diff = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
        show(h.task_started(cat, diff))
    elif cmd == "progress":
        show(h.progress(float(sys.argv[2])))
    elif cmd == "done":
        show(h.task_completed())
    elif cmd == "fail":
        show(h.task_failed())
    elif cmd == "state":
        show(h.state())
    else:
        print(__doc__)
        return
    save(h)


if __name__ == "__main__":
    main()
