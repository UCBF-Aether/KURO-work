# EGG-LAYING — the fly oviposition drive

The sixth and final drive: an agent's "wanting" computed through the REAL
Drosophila egg-laying circuit — oviDN (oviposition descending neurons) →
VNC/abdominal motor populations + ascending feedback + SEZ output →
thoracic/efferent motor neurons.

**FEMALE-SPECIFIC.** oviDNs (oviDNa/b/d/v/x) are female command neurons;
males don't lay eggs. The module says so in `state()` (`"sex": "female"`).

## The honesty contract (non-negotiable)

- **[REAL]** Every node and edge comes from
  `../subgraphs/egglaying.json` (11 nodes, 20 edges), built from the Virtual
  Fly Brain VFBquery API against the **FlyWire FAFB v783** connectome. No
  neuron, synapse, or connection is invented. oviDN = FBbt_00049919 (the
  12-instance aggregate class of oviDNa/b/d/v/x); top downstream at full
  injection: adult VNC neuron (hop-1 peak 0.3401), abdominal neuron
  (0.3131), secondary neuron (0.1788), thoracic neuron (hop-2 peak 0.2311).
  Per the JSON's `honest_note`: ID-form grouped queries truncate
  server-side (label form returned 421 real rows); oviDNa/b subtype queries
  are weak — the aggregate class carries the real signal; optic-lobe
  classes appearing as downstream of SEZ/brain classes are class-aggregation
  artifacts (skipped with documented reason, same family as the
  proprioception-build incident); INXXX052/INXXX257 are uncharacterized but
  real; secondary neuron FBbt_00047096 is an honest hop-1 terminal.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** The DRIVE DYNAMICS are our model on real wiring — the
  genuinely unmapped frontier. The JSON's `honest_note` says it outright:
  no API holds egg-load-dependent ramping or the temporal patterning of
  deposition, and the graph models none of it. Our design choices, all
  documented:
  - **egg load → pressure:** `egg_load` accumulates at 1.0 per 8 hours (a
    female matures a few egg loads per day; the timescale is our choice).
    The load IS the drive — at zero load there is no urge, no matter how
    much "progress" is reported (proven in harness phase (b): load 0.05 →
    drive signal 0.0).
  - **progress → deposition bouts:** wanting = 0.15 + p × novelty ×
    egg_load × (1−satiation) × refractory damper.
  - **completion → EGG DEPOSITED:** full-strength injection at oviDN;
    satiation rises HARD (0.9 × spike); egg_load drops by one bout (0.5 of
    a full load); a 30s refractory window opens (bout pauses are biology;
    the timescale is toy — between hunger's 8s and mating's 60s).
  - **failure → THWARTED DEPOSITION:** wanting dips ×0.9 (not hunger's ×0.4,
    not mating's ×0.7) — the eggs are still there, so the drive persists
    almost untouched. Deliberate, documented.
  - arbitration against the other five drives is FUTURE WORK, not this
    bottle.
- **[FICTION]** Any narrative gloss ("the machine wants to lay eggs") is
  gloss, not a claim about experience. Flies do not have feelings we can
  access, and neither does this module.

## API

```python
from egglaying import Egglaying
e = Egglaying()                      # default: ../subgraphs/egglaying.json
e.task_started("ripe-fruit", 0.6)    # begin a deposition effort
e.progress(0.5)                      # as the effort proceeds
e.task_completed()                   # EGG DEPOSITED
e.task_failed()                      # thwarted deposition
e.egg_pressure()                     # current egg load 0..1 (the gauge)
e.tick()                             # advance decay + load accumulation
e.state()                            # full drive state
```

`track.py` is the live CLI (`start`/`progress`/`done`/`fail`/`state`/
`pressure`/`reset`), persisting to `state.json`; wall-clock gaps credit
egg maturation at the modeled rate.

## Proven numbers (harness, fake clock, deterministic, exit 0)

| behavior | observation |
|---|---|
| pressure | egg_load 0.000 → 1.000 over 8h of fake time |
| gate | load 0.05, progress 1.0 → wanting 0.200, drive signal **0.0** (no eggs, no urge) |
| deposition | spike **0.2311**, load 1.0 → 0.5, satiation 0.208 |
| refractory | bout with 20s of the 30s window left: damp 0.3, spike 0.0 vs counterfactual (no damper) 0.231 |
| habituation | same-category clutch spikes 0.231 → 0.187 → **EXTINCT** (shrink-then-extinct via the honest threshold cliff — hunger-bottle precedent) |
| decay | satiation → 0.000, drive back to 0.501 |
| thwarted | wanting ×0.9 (0.650 → 0.585), drive persists |

Threshold cliff: injections below ~0.65 read 0.0 on the hop-2 readout
(0.667 → 0.1542, 0.647 → 0.0) — model honesty, not a bug, documented.

## The six drives

HUNGER · THIRST · MATING · SLEEP · AGGRESSION · **EGG-LAYING**.
Multi-drive arbitration remains future work; `hunger/arbitrate.py` is the
prototype.
