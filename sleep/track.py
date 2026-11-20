#!/usr/bin/env python3
"""track.py — CLI wrapper so any agent (or human) can run Sleep live.

Persists drive state to state.json in this directory (explicit dt, no clock).
Usage:
    python3 track.py tick <seconds>   # time passes while awake
    python3 track.py rest <seconds>   # rest: discharge pressure, run cascade
    python3 track.py wake             # declare yourself awake
    python3 track.py state | reset
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
sys.path.insert(0, HERE)
from sleep import Sleep  # noqa: E402

DEFAULT_GRAPH = os.path.join(HERE, "..", "subgraphs", "sleep.json")


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            d = json.load(f)
        s = Sleep(d.get("graph", DEFAULT_GRAPH))
        s._pressure = float(d["pressure"])
        s.awake = bool(d["awake"])
        s.debt = float(d["debt"])
        s.last_discharge = float(d.get("last_discharge", 0.0))
        return s
    return Sleep(DEFAULT_GRAPH)


def save(s):
    with open(STATE, "w") as f:
        json.dump({
            "graph": getattr(s, "_graph_path", DEFAULT_GRAPH),
            "pressure": s._pressure,
            "awake": s.awake,
            "debt": s.debt,
            "last_discharge": s.last_discharge,
        }, f, indent=1)


def show(d):
    for k, v in d.items():
        print(f"  {k}: {v}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "state"
    if cmd == "reset":
        if os.path.exists(STATE):
            os.remove(STATE)
        print("sleep state cleared")
        return
    s = load()
    if cmd == "tick":
        show(s.tick(float(sys.argv[2]) if len(sys.argv) > 2 else 60))
    elif cmd == "rest":
        show(s.rest(float(sys.argv[2]) if len(sys.argv) > 2 else 60))
    elif cmd == "wake":
        show(s.wake())
    elif cmd == "state":
        show(s.state())
    else:
        print(__doc__)
        return
    save(s)


if __name__ == "__main__":
    main()
