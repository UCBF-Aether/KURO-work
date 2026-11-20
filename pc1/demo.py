#!/usr/bin/env python3
"""demo.py — prove the pC1 integration bottle works.

Checks (all must pass, exit 0):
  (a) cascade fires on real wiring (full integration lights hop 1)
  (b) integrate() genuinely combines all three inputs
  (c) p1_drive is nonzero (the measured pC1->P1 edge carries signal)
  (d) threshold cliff: sub-threshold inputs stay silent
  (e) fru_drive follows the measured pC1->fru edge fraction
  (f) the graph is cyclic (SMPad1->pC1 recurrent edge present) and the
      cascade terminates on it
  (g) tick() decays
  (h) pC1 hop-0 identity is correct
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pc1 import PC1, PC1_ID, P1_ID, FRU_ID, SMPAD1_ID  # noqa: E402

passed = []


def check(name, cond, detail=""):
    assert cond, "FAIL: %s %s" % (name, detail)
    passed.append(name)
    print("ok  %s  %s" % (name, detail))


p = PC1()

# (h) identity: pC1 is hop 0
check("pc1_identity", p._inject_ids == [PC1_ID], PC1_ID)

# (f) cyclic: the recurrent edge is in the graph; cascade terminates
rec = [(pre, post) for pre, post, _ in p._norm
       if pre == SMPAD1_ID and post == PC1_ID]
check("cyclic_recurrent_edge", len(rec) == 1, "SMPad1->pC1 present")
snaps = p._cascade(1.0)
check("cycle_terminates", len(snaps) == 5, "4 steps + step 0, no loop")

# (a) cascade fires on real wiring at full integration
r = p.integrate(song_input=1.0, pheromone_input=1.0, drive_input=1.0)
check("cascade_fires", r["activation"] > 0, "activation=%s" % r["activation"])
step1 = snaps[1]
fru1 = step1.get(FRU_ID, 0.0)
check("fru_hop1_fires", fru1 >= 0.15, "fru step-1=%.4f" % fru1)

# (b) integration combines all three inputs.
#     Note the honest model cliff: integrate(1,0,0) -> injection 0.333, and
#     fru gets 0.333 x 0.4012 = 0.1336 < 0.15, so the CASCADE stays silent
#     while the measured-edge drive readouts still carry signal. Both are
#     honest behavior: cascade thresholded, edges measured.
r_none = p.integrate(0.0, 0.0, 0.0)
r_song = p.integrate(1.0, 0.0, 0.0)
song_p1, song_fru = p._p1_drive, p._fru_drive   # unrounded internals
r_all = p.integrate(1.0, 1.0, 1.0)
all_p1, all_fru = p._p1_drive, p._fru_drive
check("drives_combine",
      abs(all_p1 - 3 * song_p1) < 1e-9
      and abs(all_fru - 3 * song_fru) < 1e-9
      and song_p1 > 0,
      "song p1=%.4f fru=%.4f -> all p1=%.4f fru=%.4f"
      % (r_song["p1_drive"], r_song["fru_drive"],
         r_all["p1_drive"], r_all["fru_drive"]))
r_two = p.integrate(1.0, 1.0, 0.0)
check("cascade_combine", r_all["activation"] > r_two["activation"] > 0,
      "two=%.4f all=%.4f"
      % (r_two["activation"], r_all["activation"]))
check("silent_when_empty", r_none["activation"] == 0.0
      and r_none["p1_drive"] == 0.0 and r_none["fru_drive"] == 0.0)

# (c) p1_drive nonzero at full integration: injection x measured edge frac
check("p1_drive_nonzero", r_all["p1_drive"] > 0,
      "p1_drive=%.4f (frac=%.4f)" % (r_all["p1_drive"], p.p1_frac))
check("p1_drive_is_edge", abs(all_p1 - p.p1_frac) < 1e-9,
      "equals measured pC1->P1 fraction at full injection")

# (d) threshold cliff
r_low = p.integrate(0.1, 0.1, 0.1)
check("threshold_cliff", r_low["activation"] == 0.0
      and r_low["p1_drive"] == 0.0, "injection=0.1 silent")

# (e) fru_drive follows the measured edge fraction
check("fru_drive_is_edge", abs(all_fru - p.fru_frac) < 1e-9,
      "fru_drive=%.4f (frac=%.4f)" % (r_all["fru_drive"], p.fru_frac))

# (g) tick decays
p.integrate(1.0, 1.0, 1.0)
a0 = p._activation
p.tick(100.0)
check("tick_decays", p._activation == 0.0 < a0, "decayed to 0.0")

print("\n%d/%d checks passed" % (len(passed), len(passed)))
