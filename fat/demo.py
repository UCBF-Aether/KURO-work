#!/usr/bin/env python3
"""demo.py — prove the FAT bottle fires on both halves, exit 0.

Expectations below are TUNED TO OBSERVED NUMBERS (measured 2026-10-14),
never the other way round.
"""

from fat import Fat

CHECKS = []


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))


def main():
    s = Fat()

    # (a) bristle half fires — the LITERATURE-HYPOTHESIS path.
    r = s.sense(1.0, half="bristle")
    check("bristle fires", r["activation"] > 0,
          f"activation={r['activation']} (observed 0.2695)")
    check("bristle number", abs(r["activation"] - 0.2695) < 1e-3,
          f"{r['activation']}")
    check("bristle valence +0.3 x act",
          abs(r["valence_delta"] - round(0.3 * r["activation"], 4)) < 1e-9,
          f"V={r['valence_delta']}")
    check("bristle arousal 0.5 x act",
          abs(r["arousal_delta"] - round(0.5 * r["activation"], 4)) < 1e-9,
          f"A={r['arousal_delta']}")
    check("half echoed", r["half"] == "bristle")

    # (b) peg half fires — the REAL path.
    r2 = s.sense(1.0, half="peg")
    check("peg fires", r2["activation"] > 0,
          f"activation={r2['activation']} (observed 0.3482)")
    check("peg number", abs(r2["activation"] - 0.3482) < 1e-3,
          f"{r2['activation']}")

    # (c) both = linear sum of the two halves.
    r3 = s.sense(1.0, half="both")
    expected = round(r["activation"] + r2["activation"], 4)
    check("both sums", abs(r3["activation"] - expected) < 1e-3,
          f"{r3['activation']} == {r['activation']}+{r2['activation']}")

    # threshold cliff is honest model behavior (bristle half, inj=0.5 -> 0.0)
    r4 = s.sense(0.5, half="bristle")
    check("bristle cliff", r4["activation"] == 0.0,
          "injection 0.5 reads 0.0 below threshold")

    # invalid half is a loud error, not a silent wrong path
    try:
        s.sense(0.5, half="labellum")
        check("bad half raises", False, "no error raised")
    except ValueError:
        check("bad half raises", True, "ValueError")

    # decay
    s.sense(1.0, half="peg")
    check("tick decays", s.tick(10.0) == 0.0)

    # provenance split is machine-readable, not just prose
    st = s.state()
    prov = st.get("provenance", {})
    check("provenance split",
          "LITERATURE-HYPOTHESIS" in prov.get("bristle", "")
          and "REAL" in prov.get("peg", ""),
          f"halves: {list(prov)}")

    fails = [n for n, ok, _ in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(fails)}/{len(CHECKS)} checks pass")
    if fails:
        print("FAILED:", fails)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
