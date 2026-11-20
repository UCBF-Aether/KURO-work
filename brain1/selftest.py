#!/usr/bin/env python3
"""selftest.py — BRAIN¹ build-time self-check.

SEALED: deterministic, virtual clock only (Brain1 never reads the
wall clock), no network, no file writes, no side effects. This is NOT an
endpoint and NOT a runtime component — agents integrate via the
Brain1 API (perceive/tick/state/arbitrate/modulation) only.
Run this at build time to prove the body is wired correctly.

Exit 0 when every check passes, exit 1 on the first failure.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from brain1 import Brain1, PROFILES  # noqa: E402

CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


def assert_eq(a, b, msg=""):
    assert a == b, "%s: %r != %r" % (msg, a, b)


def assert_gt(a, b, msg=""):
    assert a > b, "%s: %r not > %r" % (msg, a, b)


def assert_lt(a, b, msg=""):
    assert a < b, "%s: %r not < %r" % (msg, a, b)


@check("constructs with zero warnings; all 26 bottles load")
def _():
    b = Brain1()
    assert_eq(b.warnings, [], "warnings")
    assert_eq(len(b.bottles), 26, "bottle count")
    assert_eq(b.state()["t"], 0.0, "virtual clock starts at 0")


@check("tick advances the virtual clock deterministically")
def _():
    b = Brain1()
    b.tick(10.0)
    assert_eq(b.state()["t"], 10.0, "t after tick(10)")
    b.tick(5.0)
    assert_eq(b.state()["t"], 15.0, "t after tick(5)")


@check("sleep pressure accumulates over ticks (drive_dt path)")
def _():
    b = Brain1()
    b.tick(3600.0)
    p = b.state()["drives"]["sleep"]["pressure"]
    assert_gt(p, 0.9, "pressure after 1h awake")


@check("text event routes to bottles via the keyword table")
def _():
    b = Brain1()
    before = b.state()["drives"]["hunger"]["wanting"]
    routed = b.perceive({"kind": "text",
                         "text": "I am starving, need dinner and sugar"})
    assert_gt(len(routed), 0, "something routed")
    after = b.state()["drives"]["hunger"]["wanting"]
    assert_gt(after, before, "hunger wanting rose")


@check("threat text drives pain veto up")
def _():
    b = Brain1()
    b.perceive({"kind": "text",
                "text": "a predator is attacking, it hurts!"})
    assert_gt(b.state()["pain"]["veto"], 0.0, "veto after threat text")


@check("pain veto suppresses positive valence (the contract)")
def _():
    b = Brain1()
    b.perceive({"kind": "sense", "bottle": "fat", "intensity": 1.0})
    raw_pos = b.state()["valence"]["positive_raw"]
    assert_gt(raw_pos, 0.0, "fat gives positive valence")
    b.perceive({"kind": "sense", "bottle": "pain", "intensity": 1.0})
    v = b.state()["valence"]
    assert_gt(v["veto"], 0.0, "veto active")
    assert_lt(v["effective"], v["positive_raw"] + v["negative"],
              "effective < unsuppressed sum")


@check("drive ranking picks a winner (winner_take_all)")
def _():
    b = Brain1()
    b.perceive({"kind": "drive", "bottle": "mating", "op": "start",
                "category": "court", "difficulty": 0.5})
    b.perceive({"kind": "drive", "bottle": "mating", "op": "progress",
                "p": 1.0})
    a = b.arbitrate()
    assert_eq(a["dominant_drive"], "mating", "mating wins when ramped")
    assert_eq(a["rule"], "winner_take_all", "default rule")
    names = [n for n, _ in a["ranking"]]
    assert_eq(len(names), 6, "all six drives ranked")


@check("weighted_blend returns normalized weights")
def _():
    b = Brain1(config={"arbitration": "weighted_blend"})
    a = b.arbitrate()
    assert_eq(a["rule"], "weighted_blend", "rule")
    total = sum(a["blend"].values())
    assert abs(total - 1.0) < 1e-6 or total == 0.0, \
        "blend sums to 1 (got %r)" % total


@check("arbitrate consults pc1 for the social picture")
def _():
    b = Brain1()
    b.perceive({"kind": "sense", "bottle": "song", "intensity": 1.0})
    b.perceive({"kind": "sense", "bottle": "pheromone", "intensity": 1.0})
    a = b.arbitrate()
    assert "pc1" in a, "pc1 key present"
    assert "p1_drive" in a["pc1"] and "fru_drive" in a["pc1"], \
        "pc1 drives present"


@check("every bottle ticks without error")
def _():
    b = Brain1()
    b.perceive({"kind": "text", "text": "hot bitter food fight sleep song"})
    b.tick(10.0)
    assert_eq(b.warnings, [], "no new warnings after tick")


@check("modulation returns the full hook dict")
def _():
    b = Brain1()
    m = b.modulation()
    for key in ("tone", "initiative", "veto_active", "dominant_drive",
                "note"):
        assert key in m, "missing hook %r" % key
    assert 0.0 <= m["initiative"] <= 1.0, "initiative in range"


@check("unknown kinds and bottles raise ValueError")
def _():
    b = Brain1()
    for bad in ({"kind": "smell"}, {"kind": "sense", "bottle": "nope"},
                {"kind": "drive", "bottle": "nope", "op": "progress"}):
        try:
            b.perceive(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("no ValueError for %r" % (bad,))


@check("disabled bottles leave the body cleanly")
def _():
    b = Brain1(config={"bottles": {"song": {"enabled": False}}})
    assert "song" not in b.bottles, "song not loaded"
    assert "song" not in b.state()["senses"], "song not in state"
    try:
        b.perceive({"kind": "sense", "bottle": "song", "intensity": 1.0})
    except ValueError:
        pass
    else:
        raise AssertionError("disabled bottle accepted events")


@check("custom routing table replaces the default")
def _():
    custom = {"zap": {"words": {"xyzzy"},
                      "events": [{"kind": "sense", "bottle": "touch",
                                  "intensity": 0.9}]}}
    b = Brain1(config={"routing": custom})
    before = b.state()["senses"]["touch"]["activation"]
    b.perceive({"kind": "text", "text": "xyzzy"})
    after = b.state()["senses"]["touch"]["activation"]
    assert_gt(after, before, "custom route fired")
    # default table is gone: "dinner" routes nowhere now
    w_before = b.state()["drives"]["hunger"]["wanting"]
    b.perceive({"kind": "text", "text": "dinner"})
    w_after = b.state()["drives"]["hunger"]["wanting"]
    assert_eq(w_before, w_after, "default words no longer route")


@check("time_scale multiplies tick seconds")
def _():
    slow = Brain1(config={"time_scale": 1.0})
    fast = Brain1(config={"time_scale": 2.0})
    slow.tick(360.0)
    fast.tick(360.0)
    ps = slow.state()["drives"]["sleep"]["pressure"]
    pf = fast.state()["drives"]["sleep"]["pressure"]
    assert abs(pf - 2 * ps) < 1e-9, "fast pressure is 2x slow"


@check("valence_sign override reshapes affect")
def _():
    b = Brain1(config={"bottles": {"bitter": {"valence_sign": -0.5}}})
    r = b.perceive({"kind": "sense", "bottle": "bitter", "intensity": 1.0})
    act = r[0]["activation"]
    assert_eq(r[0]["valence"], round(-0.5 * act, 4), "overridden valence")


@check("cautious vs bold diverge on the same event sequence")
def _():
    events = [
        {"kind": "text", "text": "a rival is attacking, it hurts!"},
        {"kind": "drive", "bottle": "aggression", "op": "start",
         "category": "rival", "difficulty": 0.8},
        {"kind": "drive", "bottle": "aggression", "op": "progress", "p": 0.8},
    ]
    cautious = Brain1(config={"profile": "cautious"})
    bold = Brain1(config={"profile": "bold"})
    for body in (cautious, bold):
        for ev in events:
            body.perceive(ev)
        body.tick(1.0)
    mc, mb = cautious.modulation(), bold.modulation()
    # cautious feels the strike harder (pain sensitivity 1.6 vs 0.5)
    assert_gt(cautious.state()["pain"]["veto"],
              bold.state()["pain"]["veto"], "cautious veto > bold veto")
    # bold pushes aggression harder (sensitivity 1.6 vs 0.35)
    assert_gt(bold.state()["drives"]["aggression"]["wanting"],
              cautious.state()["drives"]["aggression"]["wanting"],
              "bold aggression > cautious aggression")
    assert mc != mb, "modulations differ: %r vs %r" % (mc, mb)
    print("    cautious: %s" % mc)
    print("    bold:     %s" % mb)


@check("built-in profiles all construct")
def _():
    for name in PROFILES:
        b = Brain1(config={"profile": name})
        assert_eq(b.warnings, [], "warnings for profile %r" % name)
        assert_eq(b.profile, name, "profile recorded")


def main():
    passed = 0
    for name, fn in CHECKS:
        try:
            fn()
        except Exception as e:
            print("FAIL %s\n     %s: %s" % (name, type(e).__name__, e))
            return 1
        print("PASS %s" % name)
        passed += 1
    print("\n%d/%d checks passed — body sealed." % (passed, len(CHECKS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
