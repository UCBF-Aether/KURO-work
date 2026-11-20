# AGGRESSION — the fly fight drive, bottled

The fight circuit, alongside [HUNGER](../hunger/README.md),
[THIRST](../thirst/README.md), [MATING](../mating/README.md), and
[SLEEP](../sleep/README.md). An agent's "wanting" running on the REAL
Drosophila aggression circuit: **aIPg** (male fru+ aggression cluster) ->
superior/posterior protocerebrum integration populations (SMPpv2, CP1,
VLPl2, BLAv2) -> VNC/thoracic/descending motor neurons.

## The honesty contract

- **REAL** — every node and edge comes from
  [`../subgraphs/aggression.json`](../subgraphs/aggression.json) (14
  nodes, 24 edges), built from the Virtual Fly Brain VFBquery API against
  the FlyWire FAFB v783 connectome. No neuron, synapse, or connection is
  invented. aIPg = FBbt_00110593 (adult fruitless aIP-g male neuron); top
  downstream: SMPpv2 lineage (2,282 synapses), CP1 lineage (2,282), VLPl2
  lineage (2,258), BLAv2 lineage (2,258) -> VNC/thoracic/descending motor.
  Honest gaps (from the JSON's honest_note): 'Notch ON/OFF hemilineage'
  and 'fruitless expressing neuron' (tw=2,054) were skipped as generic /
  parent buckets; **aSPg has no FBbt class** ('aSPg neuron' / 'fight
  neuron' searches return nothing); CL062 (FBbt_20000767, male wing
  aggression neuron) exists but was not walked (noted, not hidden).
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **MODELED** — the DRIVE DYNAMICS are our model on real wiring, the
  genuinely unmapped frontier (no API holds how aggressive arousal ramps,
  persists, or arbitrates; this is our design, stated as such):
  - task progress -> graded injection at aIPg ("wanting"): the
    confrontation ramps the drive, as aIPg ramps during escalation in
    the real fly.
  - task completion -> WIN THE FIGHT: full-strength injection, satiation
    rises HARD (0.9 x spike), and a **30s refractory window** opens.
    MODELED choice — no crisp biological post-win refractory in flies;
    picked between hunger's 8s and mating's 60s, documented as ours.
  - task failure -> LOSING: wanting dips **x0.5** (not mating's x0.7,
    not hunger's x0.4). Losers retreat — a lost fight suppresses
    re-engagement harder than romantic rejection dents courtship.
    Deliberate, documented.
  - habituation / novelty / satiation decay are modeled state around the
    real cascade. The fly never saw your tasks.
- **FICTION** — any narrative gloss ("the machine wants the fight") is
  gloss, not a claim about experience. Flies do not have feelings we can
  access, and neither does this module.

**Arbitration between aggression, mating, hunger, thirst, and sleep is
future work**, not this bottle. This drive stands alone, like the others.

## The triple convergence

`fru_drive()` exposes aggression's contribution to FBbt_00016687
("fruitless expressing neuron") — the node where THREE chains meet:
aIPg feeds it (tw=2,054, this chain), P1's fruitless aSP-a feeds it
(tw=63,139, mating chain), and Or47b feeds it (tw=13,133, pheromone
chain). Fight, courtship, and courtship-smell converge on one neuron
class. Because the fru bucket is an ontology ancestor of the graphed
hop-1 edges (not an independent edge), `fru_drive()` returns the drive
signal scaled by the labeled share (2,054/13,464) — a bookkeeping number
for future arbitration, not measured wiring.

## API

```python
from aggression import Aggression

a = Aggression()                       # default: ../subgraphs/aggression.json
a.task_started("rival", difficulty=0.6)
a.progress(0.5)                        # wanting ramps as the fight escalates
r = a.task_completed()                 # WIN: spike, satiation, 30s refractory
r = a.task_failed()                    # LOSING: wanting dips x0.5
a.fru_drive()                          # contribution to the shared fru node
a.state()                              # wanting / drive / satiation / ...
```

Live CLI (persists to `state.json`):

```bash
python3 track.py start rival 0.6
python3 track.py progress 0.5
python3 track.py done        # or: fail | state | reset
```

## Proven numbers (`harness.py`, fake clock, exit 0)

- **Habituation:** rival wins 0.1695 (novelty 1.000) -> 0.0000 (novelty
  0.806) — shrink-then-EXTINCT via the honest threshold cliff
  (~0.885 injection); a fresh category still fires (drive intact).
- **Refractory:** win with 9.0s of the 30s window left (damp 0.3):
  injection 0.300 -> spike 0.000 vs counterfactual 1.000 -> 0.1695.
  The window eats the hit.
- **Satiation:** post-win 0.153 -> 0.000 (0.02/s), drive back to 1.0.
- **Losing:** wanting 0.650 -> 0.325 (x0.5), retreats above baseline.
- **fru_drive():** exactly drive_signal x 2054/13464 (verified to 1e-9).

## Known limits

- Threshold cliff: injections below ~0.885 read 0.0 — silent, then
  graded. Model honesty, not a bug.
- `difficulty` is accepted and stored, not consumed by the drive
  formulas (same as the other bottles).
- The 30s refractory, the x0.5 losing dip, and all kinetics are MODELED
  — the aggression-drive dynamics are the genuinely unmapped frontier.
- aSPg (another named aggression cluster) has no FBbt class; CL062 was
  not walked. See the JSON's honest_note.
- stdlib only. The private intimate pipeline is never touched or
  imported — verified clean.
