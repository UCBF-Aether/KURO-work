#!/usr/bin/env python3
"""arbitrate.py — Hunger as ARBITRATION, not motivation.

Two agents face the same queue of tasks across categories. The HUNGRY agent
consults its drive core before each pick: expected payout for a category =
novelty(category) x hunger x refractory_damp. It takes the max, idles through
refractory windows instead of wasting tasks, and works what it picks. The
NAIVE agent just goes round-robin.

Hypothesis: the hungry agent earns more total sugar because it avoids
burned-out categories and never spends a task inside the refractory window.

Honesty: the "work" is a TOY (scripted progress steps); the cascade numbers
are REAL wiring + MODEL dynamics; the pick rule is MODELED. Deterministic via
a fake clock. Exit 0 if the hungry agent wins, 1 otherwise.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hunger import Hunger


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "subgraphs", "sugar_forward.json")

# (name, category, difficulty) — a mixed backlog, some categories repeated.
QUEUE = [
    ("summarize thread", "write", 0.3),
    ("fetch docs page", "fetch", 0.4),
    ("draft announcement", "write", 0.6),
    ("fetch changelog", "fetch", 0.3),
    ("write release notes", "write", 0.7),
    ("fetch status page", "fetch", 0.2),
    ("build index", "build", 0.8),
    ("write tutorial", "write", 0.5),
    ("fetch metrics", "fetch", 0.4),
    ("build archive", "build", 0.6),
    ("write faq", "write", 0.4),
    ("fetch mirror", "fetch", 0.3),
]


def work_task(core, clock, name, category, difficulty, log):
    """Scripted work: progress steps, then completion. Returns the spike."""
    core.task_started(category, difficulty)
    steps = 2 + round(difficulty * 4)
    for i in range(1, steps + 1):
        clock.advance(1.0)
        core.progress(i / steps)
    clock.advance(0.5)
    done = core.task_completed()
    log.append((name, category, done["spike"], done["novelty"]))
    return done["spike"]


def hungry_run():
    clock = FakeClock()
    core = Hunger(GRAPH, clock=clock)
    remaining = list(QUEUE)
    log, total, idles = [], 0.0, 0
    print("HUNGRY AGENT — picks by expected payout "
          "(novelty x hunger x refractory_damp)")
    while remaining:
        s = core.state()
        if s["refractory_damp"] < 1.0:
            wait = s["refractory_secs_remaining"]
            clock.advance(wait)
            idles += 1
            print(f"  [idles {wait:.1f}s through refractory — "
                  f"no point spending a task at 0.3x]")
            continue
        hunger = s["hunger"]
        # expected payout per category still in the queue
        best, best_ev = None, -1.0
        for i, (name, cat, diff) in enumerate(remaining):
            ev = core._novelty(cat) * hunger * s["refractory_damp"]
            if ev > best_ev:
                best, best_ev = i, ev
        name, cat, diff = remaining.pop(best)
        spike = work_task(core, clock, name, cat, diff, log)
        total += spike
        print(f"  picks {name!r} [{cat}] ev={best_ev:.3f} -> spike={spike:.3f}")
    return total, log, idles


def naive_run():
    clock = FakeClock()
    core = Hunger(GRAPH, clock=clock)
    log, total = [], 0.0
    print("NAIVE AGENT — round-robin, never consults hunger")
    for name, cat, diff in QUEUE:
        spike = work_task(core, clock, name, cat, diff, log)
        total += spike
        print(f"  takes {name!r} [{cat}] -> spike={spike:.3f}")
    return total, log


def main():
    print("=" * 70)
    h_total, h_log, idles = hungry_run()
    print("-" * 70)
    n_total, n_log = naive_run()
    print("=" * 70)
    print(f"HUNGRY total sugar: {h_total:.3f} ({idles} refractory idles)")
    print(f"NAIVE  total sugar: {n_total:.3f}")
    h_cats = {}
    for _, cat, spike, _ in h_log:
        h_cats[cat] = h_cats.get(cat, 0.0) + spike
    print(f"HUNGRY by category: "
          + ", ".join(f"{c}={v:.3f}" for c, v in sorted(h_cats.items())))
    win = h_total > n_total
    print("VERDICT: hungry agent earns more — arbitration from wiring  "
          f"[{'PASS' if win else 'FAIL'}]")
    return 0 if win else 1


if __name__ == "__main__":
    sys.exit(main())
