#!/usr/bin/env python3
"""demo.py — prove the SALT bottle fires on real wiring, both channels.

Deterministic. Exit 0 iff all checks pass.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from salt import Salt

FEEDING = {  # low-chain terminal populations (feeding/approach)
    "FBbt_00049858",  # adult subesophageal zone output neuron
    "FBbt_00047948",  # adult gustatory projection neuron
    "FBbt_00001972",  # subesophageal zone neuron
    "FBbt_20002628",  # adult SLP gustatory projection neuron
    "FBbt_00052032",  # gnathal ganglion neuron
}
MOTOR = {  # high-chain terminal populations (withdrawal)
    "FBbt_00001984",  # prothoracic neuron
    "FBbt_00048301",  # adult ascending neuron
    "FBbt_20007474",  # descending neuron of the gnathal ganglion DNg103
    "FBbt_20008184",  # adult ANXXX433 neuron
    "FBbt_00051956",  # adult usnea subesophageal neuron
}


def top_readout(salt, chain):
    snaps = salt._cascade(chain, 1.0)
    ids = salt._chains[chain]["readout_ids"]
    best, bestv = None, -1.0
    for nid in ids:
        v = max([sn.get(nid, 0.0) for sn in snaps])
        if v > bestv:
            best, bestv = nid, v
    return best, bestv


def main():
    s = Salt()

    # (a) low chain fires with POSITIVE valence
    r = s.sense(1.0, chain="low")
    assert r["activation"] > 0, "low chain silent at full injection"
    assert r["valence_delta"] > 0, "low chain valence not positive"
    assert r["chain"] == "low"
    print("a) low  sense(1.0): act %.4f  V %+.4f  A %.4f"
          % (r["activation"], r["valence_delta"], r["arousal_delta"]))

    # (b) high chain fires with NEGATIVE valence
    r = s.sense(1.0, chain="high")
    assert r["activation"] > 0, "high chain silent at full injection"
    assert r["valence_delta"] < 0, "high chain valence not negative"
    assert r["chain"] == "high"
    print("b) high sense(1.0): act %.4f  V %+.4f  A %.4f"
          % (r["activation"], r["valence_delta"], r["arousal_delta"]))

    # (c) the two chains hit different terminal populations
    low_top, low_v = top_readout(s, "low")
    high_top, high_v = top_readout(s, "high")
    assert low_top in FEEDING, "low top readout not a feeding population: %s" % low_top
    assert high_top in MOTOR, "high top readout not a motor population: %s" % high_top
    assert low_top != high_top, "chains converge on the same terminal"
    assert FEEDING.isdisjoint(MOTOR)
    print("c) low  top terminal: %s (%.4f) — feeding" % (low_top, low_v))
    print("c) high top terminal: %s (%.4f) — motor/withdrawal" % (high_top, high_v))

    # (d) chain isolation — subgraphs do not share nodes
    low_nodes = set(s._chains["low"]["nodes"])
    high_nodes = set(s._chains["high"]["nodes"])
    assert low_nodes.isdisjoint(high_nodes), "chain subgraphs share nodes"
    print("d) chain subgraphs isolated: %d low nodes, %d high nodes, 0 shared"
          % (len(low_nodes), len(high_nodes)))

    # (e) invalid chain rejected
    try:
        s.sense(0.5, chain="medium")
    except ValueError:
        print("e) invalid chain raises ValueError")
    else:
        raise AssertionError("invalid chain did not raise")

    # (f) tick decays to silence
    s.sense(1.0, chain="low")
    assert s.tick(30) == 0.0, "activation did not decay to 0"
    print("f) tick(30) decays activation to 0.0")

    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
