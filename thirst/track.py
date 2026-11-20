#!/usr/bin/env python3
"""track.py — CLI wrapper so any agent (or human) can run Thirst live.

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
from thirst import Thirst  # noqa: E402

DEFAULT_GRAPH = os.path.join(HERE, "..", "subgraphs", "water.json")


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            d = json.load(f)
        h = Thirst(d["graph"], clock=None)
        h.wanting = d["wanting"]
        h.drive_signal = d["drive_signal"]
        h.satiation = d["satiation"]
        h.habituation = defaultdict(float,
            {k: float(v) for k, v in d["habituation"].items()})
        h.refractory_until = d["refractory_until"]
        h.last_spike = d["last_spike"]
        h.category = d["category"]
        h.difficulty = d["difficulty"]
        # re-anchor the wall clock: refractory windows are wall-clock based;
        # on reload, keep remaining time, not absolute timestamps.
        import time
        now = time.monotonic()
        h._clock = time.monotonic
        h._last = now
        # refractory_until was stored as remaining seconds
        h.refractory_until = now + d["refractory_until"]
        return h
    return Thirst(DEFAULT_GRAPH)


def save(h):
    import time
    now = time.monotonic()
    with open(STATE, "w") as f:
        json.dump({
            "graph": getattr(h, "_graph_path", DEFAULT_GRAPH),
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
        print("thirst state cleared")
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
