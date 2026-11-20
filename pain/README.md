# PAIN

The **veto sense** — a noxious-event sensor for an AI agent, computed through
the real *Drosophila* escape circuit instead of a hand-tuned penalty number.
One of the bottled drives/senses; sibling to HUNGER and THIRST.

A strike runs the cascade: Johnston's organ mechanoreceptor subtypes → giant
fiber neuron → thoracic escape motor, live from real connectome wiring. The
readout that matters is `veto()` — every pleasant signal in every other
bottle gets multiplied by `(1 - veto())`. Pain overrides pleasure.

## The honesty contract

- **[REAL]** Every node and edge comes from `../subgraphs/pain.json`, built
  from the Virtual Fly Brain VFBquery API against the **FlyWire FAFB v783**
  connectome. 8 nodes, 7 edges: JO subtypes zone B type 1 (679 synapses),
  zone A (80), zone B (61), JO CA (10) → giant fiber neuron → adult VNC
  (1097), prothoracic (585), mesothoracic (471). 830 measured JO→giant-fiber
  synapses, discovered via UpstreamClassConnectivity of the giant fiber
  neuron (FBbt_00004020) — our own motor-backward method — and pair-verified.
  No neuron, synapse, or connection is invented.
  **Honest framing:** adult nociceptive-LABELED classes (FBbt_00051492,
  FBbt_00048471) are not indexed with usable connectivity in any reachable
  form (see `../GAPS.md` §7). This is the fly's FUNCTIONAL pain-equivalent
  circuit — sharp mechanical insult → startle → escape — NOT labeled pain
  neurons.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** The strike→injection mapping is a design choice, not biology.
  So are: veto normalization (activation ÷ the circuit's own maximum, so a
  full strike reads as full suppression); affect deltas normalized to
  bounded dimensions (valence [-1,0], arousal [0,1]) while the raw cascade
  peak is unnormalized (four JO subtypes converging on one giant fiber
  genuinely sums — that fan-in is the biology); habituation (startle
  softens with repetition, 1/(1+0.3·n)); decay (0.1/s). The fly never saw
  your events.
- **[FICTION]** Any narrative gloss ("that hurt") is fiction, not a claim
  about experience.

## API

```python
from pain import Pain

pain = Pain()                      # loads ../subgraphs/pain.json

pain.strike(1.0)                   # a noxious event happened; 0..1
# -> {"activation": 2.038, "valence_delta": -1.0, "arousal_delta": 1.0,
#     "gf_activation": 4.0, "novelty": 1.0, "veto": 1.0}

pain.veto()                        # 0..1 — ~1 right after a full strike,
                                   # decays toward 0 as pain fades
pain.tick()                        # advance decay (or tick(dt) explicitly)
pain.state()                       # activation, veto, habituation, last strike
```

**The veto contract** — the reason this bottle exists:

```python
sweet_gain = base_gain * (1 - pain.veto())
```

Every positive-valence gain (sweetness in Hunger, water in Thirst, reward,
comfort — in any bottle) MUST be multiplied by `(1 - pain.veto())`.
A noxious stimulus suppresses feeding and reward-seeking; that is the
biology being honored, and the contract that lets the bottles compose into
one sensorium.

## Proven behaviors (`python3 demo.py`)

Deterministic, fake clock. All hold:

**(a) A full strike hits hard and negative.**
`strike(1.0)` → activation 2.038, valence_delta −1.000, arousal_delta +1.000,
giant fiber peak 4.000. The startle lands at full scale with the valence
fully negative.

**(b) Veto is ~1 fresh, ~0 decayed.**
`veto()` = 1.000 immediately after a full strike; 0.000 after 30 s of decay.
Right after a full strike, `sweet_gain × (1 − veto)` = 0.000 — appetite
fully suppressed, exactly the contract.

**(c) Startle habituates but never silences.**
Three back-to-back full strikes: 2.038 → 1.568 → 1.274. Repeated blows land
softer — but unlike taste habituation (which can extinguish to zero), pain
never goes silent. That asymmetry is deliberate: a sense that exists to
override must not habituate itself away. [MODELED choice, documented.]

## Files

- `pain.py` — `Pain`. Stdlib only. Importable: `from pain import Pain`.
- `demo.py` — proves (a)(b)(c). Exit 0 = all pass.
- `README.md` — this file.

## What's deliberately not here

No learned aversion, no penalty shaping, no "pain" scalar to tune. The
startle runs on 830 measured synapses, the veto is the circuit's own
maximum talking, and the one behavioral law that matters — pain overrides
pleasure — is a one-line contract every other bottle honors.

## Known limits

- Functional pain-equivalent, not labeled nociceptors (above).
- The 0.15 threshold cliffs weak strikes: injections below ~0.3 never reach
  the giant fiber, so a gentle tap reads as nothing — the fly agrees.
- `strike()` takes no location; the whole antennal array fires at once.
  (Sensorium's body map localizes it; this bottle is the raw sense.)
- Habituation never extinguishes (deliberate, above).
