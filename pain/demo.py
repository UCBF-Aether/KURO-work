#!/usr/bin/env python3
"""demo.py — prove PAIN behaves like a veto sense.

Deterministic (fake clock). Proves:
  (a) strike(1.0) -> high activation + negative valence + arousal spike.
  (b) veto() ~1 right after a full strike, ~0 after decay.
  (c) repeated strikes habituate: activations shrink monotonically.

Honesty: the strikes are scripted (TOY events); the cascade numbers are REAL
wiring + MODEL dynamics; the strike->injection mapping and veto normalization
are MODELED. Exit 0 iff all proofs hold.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pain import Pain


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def main():
    clock = FakeClock()
    graph = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "subgraphs", "pain.json")
    p = Pain(graph, clock=clock)
    ok = True
    print("=" * 70)
    print("PAIN — the veto sense")
    print("=" * 70)

    # (a) full strike: high activation, negative valence, arousal spike
    r = p.strike(1.0)
    print(f"(a) strike(1.0): activation={r['activation']:.3f} "
          f"valence_delta={r['valence_delta']:.3f} "
          f"arousal_delta={r['arousal_delta']:.3f} "
          f"gf={r['gf_activation']:.3f}")
    a = r["activation"] > 0.2 and r["valence_delta"] < 0 \
        and r["arousal_delta"] > 0
    print(f"    high activation + negative valence + arousal  "
          f"[{'PASS' if a else 'FAIL'}]")
    ok &= a

    # (b) veto ~1 after full strike, ~0 after decay
    v_full = p.veto()
    clock.advance(30.0)
    v_decayed = p.veto()
    print(f"(b) veto after full strike: {v_full:.3f}; after 30s decay: "
          f"{v_decayed:.3f}")
    b = v_full >= 0.99 and v_decayed < 0.01
    print(f"    veto ~1 fresh, ~0 decayed  [{'PASS' if b else 'FAIL'}]")
    ok &= b

    # (c) habituation: three fresh full strikes shrink monotonically
    clock2 = FakeClock()
    q = Pain(graph, clock=clock2)
    acts = [q.strike(1.0)["activation"] for _ in range(3)]
    print(f"(c) three strikes: "
          + " -> ".join(f"{x:.3f}" for x in acts))
    c = acts[0] > acts[1] > acts[2] > 0
    print(f"    startle habituates, never silenced outright  "
          f"[{'PASS' if c else 'FAIL'}]")
    ok &= c

    # veto contract demonstration: sweet gain suppressed by pain
    clock3 = FakeClock()
    s = Pain(graph, clock=clock3)
    s.strike(1.0)
    suppressed_gain = 1.0 * (1 - s.veto())
    print(f"    veto contract: sweet_gain x (1 - veto) = {suppressed_gain:.3f} "
          f"right after a full strike (appetite fully suppressed)")
    ok &= suppressed_gain < 0.01

    print("=" * 70)
    print("PAIN BOTTLED" if ok else "SOMETHING FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
