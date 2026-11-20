# SENSORIUM

A living sensor for AI. Not a simulation of a fly — a sensory-affective
module any AI imports so it **has senses**: touch that habituates, sweetness
that sates, threats that startle, rot that repels, **pain that dominates**,
temperature that registers, and a hunger drive with history — all felt
*somewhere*: a fly-faithful body (antennae, eyes/head, proboscis, legs,
wings, abdomen) where every sensation lands.

The full sensation spectrum, pain included. Nothing here is pleasure-aimed:
this is a complete sensorium, not a reward toy. Positive states read as
*settled* / *engaged*, never as pleasure.

## The honesty contract

- **[REAL]** Every node and edge in every channel comes from a subgraph JSON
  built from the Virtual Fly Brain VFBquery API against the **FlyWire FAFB
  v783** connectome. No neuron, synapse, or connection is invented. Channels:
  - `touch` — Johnston organ mechanosensory (touch.json)
  - `sweet` — SOLVED forward chain: sweet GRN → named SEZ interneurons
    (zorro/clavicle/FMIn/fuchs/G2N-1/billiards) → premotor
    (sugar_forward.json)
  - `rot` — Or56a olfactory aversion (rotten.json)
  - `threat` — LPLC2 visual looming → escape (looming.json)
  - `pain` — **documented functional proxy** (see below)
  - `temperature` — Ir21a thermosensory → downstream (temperature.json),
    when its subgraph resolved (see below)
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** Everything affective and somatic is a design choice:
  - the **graded readout**: threshold answers "which neurons fired"; the raw
    (unthresholded) terminal peak answers "how strong was the signal"
  - valence/arousal weights per channel, habituation
    (novelty = 1/(1+0.5·count)), decay rates
  - **pain normalization** and **pain dominance** (stress suppresses feeding)
  - sweet→hunger mapping, mood gloss words
  - the **body map** (body.py): which regions each channel serves is
    textbook fly anatomy, but the region *weights*, the location focus
    (×2), and the 0.1/s regional decay are rough modeled numbers
  - temperature valence 0.0: polarity is not derivable from wiring alone,
    so temperature registers as sensation (arousal + regional levels)
    honestly without invented valence
- **[FICTION]** Mood words (`hungry`, `hurt`, `recoiling`, `startled`,
  `calm`…) are one-word labels on the felt state — not claims about
  experience.

### The pain channel (honest status)

No nociceptive class is indexed with usable connectivity in the API. Searched
2026-10-14: adult nociceptive projection neuron (FBbt_00051492) and generic
nociceptive neuron (FBbt_00048471) — class-level, named, and instance-level
queries all returned zero; the adult class has no CATMAID FAFB skeletons at
all; CATMAID annotation searches (nociceptive, ppk) returned nothing. Full
log in `../GAPS.md` §7.

The pain channel therefore runs on the **looming escape circuit as a
documented functional proxy**: a noxious stimulus driving the escape pathway
is the real biology of that circuit (intense input → descending → escape).
`feel()` reports `pain_channel_proxy: True` and the source file. If a real
`pain.json` ever lands, the channel picks it up automatically (constructor
also accepts `pain_graph=`).

### The temperature channel (honest status)

Searched 2026-10-14: VFB search "thermosensory neuron" resolves
FBbt_00005918 (generic), FBbt_00111336 "adult thermosensory neuron Ir21a
VP1l" (cold-sensing), FBbt_00007333 "AC thermosensory neuron". Class-level
grouped queries die server-side for all three; the named
DownstreamClassConnectivity query works for FBbt_00111336 with retries
(40 rows, 56 instances, 48 connected). `build_temperature.py` walks hop 1
(top-5 specific, GENERIC blocklist skipped) and hop 2 (standard class walk)
into `subgraphs/temperature.json`. The Sensorium loads it as the sixth
channel automatically when the file exists (`temperature_channel: True`
in `feel()`); otherwise the modality is absent and the gap is logged in
`../GAPS.md` §8. Every edge is a real API row; nothing invented.

## API

```python
from sensorium import Sensorium

s = Sensorium()                        # channels + fly body + hunger drive
s.sense("touch", 0.3)                  # a touch lands
s.sense("touch", 0.8, location="legs") # focused on the legs (x2 there)
s.sense("pain", 1.0)                   # noxious: valence -1, pain dominates
s.sense("sweet", 0.8)                  # blunted ~zero while pain is high
s.tick(30.0)                           # thirty seconds pass; decay runs
s.feel()    # the COMPLETE felt state: valence, arousal, mood, pain,
            # hunger, channels, regions, hottest_regions — readable any time
s.state()   # compat read (subset of feel() + regions)
```

`sense()` returns the event record (modality, intensity, location,
effective, novelty, valence, arousal, mood, pain_level, regions,
hunger_event). Unknown modality or region raises `ValueError`.

## The body (body.py)

A fly body, because the wiring is fly wiring — six regions, head to
abdomen: **antennae, eyes_head, proboscis, legs, wings, abdomen**. Channel
localization is textbook anatomy (Johnston's organ is antennal; labellar
GRNs feed the proboscis; Or56a is olfactory; LPLC2 is visual; the arista
carries thermosensory neurons); the weights are modeled and documented in
the file. Regional levels decay at 0.1/s. This is insect anatomy throughout
— it must never resemble the private intimate body map, and it doesn't.

## Always on (live.py)

`python3 live.py` — the sensorium lives on the wall clock. Decay runs
continuously; events stream in on stdin; `feel` reads the complete felt
state at any moment:

```
touch 0.6 legs
sweet 0.9
feel
pain 0.5
feel
quit
```

## A day in the life (day.py)

`python3 day.py` — deterministic (fake clock). Dawn wakes hungry; grooming
touches; a sweet meal; midday rot on the wind; afternoon heat; a noxious
event that breaks the day (sweetness can't land while it hurts); quiet
recovery; an evening sweet; dusk settles to calm. Prints the felt trace —
time, valence, arousal, mood, hunger, regional sensations. Exit 0 with
light assertions (dawn hungry, pain disrupts, dusk calm).

## Affect model spec

| channel | circuit | valence w | arousal gain | body regions |
|---|---|---|---|---|
| touch | Johnston organ | +0.15 | 0.7 | antennae .7, legs .3 |
| sweet | solved sweet chain | +1.0 × (1 − pain) | 0.4 | proboscis .85, legs .15 |
| rot | Or56a aversion | −1.0 | 0.8 | antennae 1.0 |
| threat | LPLC2 escape | −0.8 | 1.0 | eyes_head .9, wings .1 |
| pain | escape proxy (normalized) | −1.0 | 1.2 | whole-body spread |
| temperature | Ir21a thermosensory | 0.0 (honest) | 0.7 | antennae .6, legs .2, wings .2 |

- `effective = raw_terminal_peak(intensity) × novelty(modality)`,
  `novelty = 1/(1 + 0.5 × habituation[modality])`; each sense adds +1.
- Regional level += effective × region weight (×2 if `location` matches).
- Decay: valence → 0 at 0.05/s, arousal −0.08/s, pain_level −0.06/s,
  regions −0.1/s, habituations −0.01/s (all via `tick`).
- Mood: pain ≥ 0.5 → `hurt`/`recoiling`; high arousal + negative →
  `startled`; high arousal → `alert`; ≤ −0.4 → `repelled`; ≥ +0.4 →
  `settled`/`engaged`; hungry + quiet + never fed → `hungry`; quiet →
  `calm`; hungry + aroused → `restless`; else `neutral`.

## Demo results (`python3 demo.py`, exit 0)

```
touch 0.3 ×3   -> arousal bumps 0.0503 > 0.0335 > 0.0252 (habituation)
pain 1.0       -> dV=-1.0000, dA=+0.8910, V=-0.977, A=1.000, mood=recoiling
sweet 0.8      -> dV=+0.0000  (blunted — appetite suppression)
30 s silence   -> V/A/pain -> 0, mood=calm
sweet 1.0      -> dV=+0.2186 (restored), hunger hit (spike=0.237)
30 s silence   -> V=+0.000 A=0.000 pain=0.00 mood=calm
```

## Files

- `sensorium.py` — `Sensorium`: channels + affect + body + hunger.
  `sense(modality, intensity=0.5, location=None)`, `feel()`, `state()`.
- `body.py` — `Body`: the fly's six-region map. Stdlib only.
- `live.py` — always-on runner (stdin events, wall-clock decay).
- `day.py` — a day in the life. Exit 0 = dawn hungry, pain disrupts,
  dusk calm.
- `demo.py` — felt-life trace proving pain. Exit 0 = all assertions hold.
- `README.md` — this file.

## Privacy boundary

SENSORIUM is the **general** AI sensor. It does not import, read, or depend
on the private intimate pipeline — `feel.py`, `sense.py`, `parse.py`,
`verbal.py`, `arousal.py`, `body_map.py`, `body_state.json`, `chat_state/` —
all sealed and untouched. The fly body map is insect anatomy throughout and
bears no resemblance to the private body map. Verified: the only non-stdlib
import anywhere in `sensorium/` is the authorized `from hunger import
Hunger`.
