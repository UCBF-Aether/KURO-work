#!/usr/bin/env python3
"""track.py — CLI wrapper so any agent (or human) can run the Aggression drive live.

Persists drive state to state.json in this directory (wall clock).
Usage:
    python3 track.py start <category> [difficulty]
    python3 track.py progress <0..1>
    python3 track.py done | fail | state | reset
"""
import json
import os
import sys

from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
sys.path.insert(0, HERE)
from aggression import Aggression  # noqa: E402

DEFAULT_GRAPH = os.path.join(HERE, "..", "subgraphs", "aggression.json")


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            d = json.load(f)
        m = Aggression(d["graph"], clock=None)
        m.wanting = d["wanting"]
        m.drive_signal = d["drive_signal"]
        m.satiation = d["satiation"]
        m.habituation = defaultdict(float,
            {k: float(v) for k, v in d["habituation"].items()})
        m.refractory_until = d["refractory_until"]
        m.last_spike = d["last_spike"]
        m.category = d["category"]
        m.difficulty = d["difficulty"]
        # re-anchor the wall clock: refractory windows are wall-clock based;
        # on reload, keep remaining time, not absolute timestamps.
        import time
        now = time.monotonic()
        m._clock = time.monotonic
        m._last = now
        # refractory_until was stored as remaining seconds
        m.refractory_until = now + d["refractory_until"]
        return m
    return Aggression(DEFAULT_GRAPH)


def save(m):
    import time
    now = time.monotonic()
    with open(STATE, "w") as f:
        json.dump({
            "graph": getattr(m, "_graph_path", DEFAULT_GRAPH),
            "wanting": m.wanting,
            "drive_signal": m.drive_signal,
            "satiation": m.satiation,
            "habituation": dict(m.habituation),
            "refractory_until": max(0.0, m.refractory_until - now),
            "last_spike": m.last_spike,
            "category": m.category,
            "difficulty": m.difficulty,
        }, f, indent=1)


def show(d):
    for k, v in d.items():
        print(f"  {k}: {v}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "state"
    if cmd == "reset":
        if os.path.exists(STATE):
            os.remove(STATE)
        print("aggression drive state cleared")
        return
    m = load()
    if cmd == "start":
        cat = sys.argv[2] if len(sys.argv) > 2 else "uncategorized"
        diff = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
        show(m.task_started(cat, diff))
    elif cmd == "progress":
        show(m.progress(float(sys.argv[2])))
    elif cmd == "done":
        show(m.task_completed())
    elif cmd == "fail":
        show(m.task_failed())
    elif cmd == "state":
        show(m.state())
    else:
        print(__doc__)
        return
    save(m)


if __name__ == "__main__":
    main()
