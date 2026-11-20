# RETINA — the fly eye front end (v5: direction removed)

A camera-style frame feed driving the REAL visual bottles (motion, color,
looming) through a MODELED retina. The eye, not the brain, is what we
rebuild here. v5 is **binocular and biofaithful** (BRAIN¹): two compound
eyes, frontal overlap, acute zone — no finer-than-fly grids, no invented
color. **Direction is gone by design** (Cory's call, 2026-10-16): the eyes
SEE and DETECT motion; they don't find its direction. Motion is a scalar
unsigned energy — how much, not which way.

## What it is

`retina.py` — `Retina` class. One frame in (split internally into the two
eyes with frontal overlap), fused intensities out:

```python
from retina import Retina
r = Retina()                       # two hex eyes, 805 facets each
out = r.frame(rgb_uint8_frame)     # {"motion","color","looming","contraction"}
r.eye_outputs()                    # {"L": {...}, "R": {...}} per-eye
motion_bottle.sense(out["motion"])
color_bottle.sense(out["color"], channel="both")
looming_bottle.sense(out["looming"])
```

Pipeline per frame, per eye: window the frame (left [0, 57%), right
[43%, 100%], ~25% frontal overlap) → bilinear sampling onto a 23×35
hexagonal ommatidia lattice (805 facets ~= one fly eye; 6 equidistant
neighbors, the real packing) → per-facet luminance (R1-6 broadband proxy)
and saturation (R7/R8 color proxy) → Hassenstein-Reichardt
delay-and-compare motion vs the previous frame, weighted by the eye's
acute-zone gain map, read out as UNSIGNED energy (mean of |local motion|
across the eye — opposing traffic adds instead of canceling) →
LPLC2-style radial motion opponency for looming: per-template
outward-vs-inward motion energy from the local flow field, opponent
subtraction, angular-spread gate (radial, not clustered), sustained
over frames. Contraction (inward-dominant radial flow) is its own
reported signal. Fuse: motion = stronger eye, color/looming/
contraction = max. ~13 ms/frame on CPU (measured 13.4 ms mean on
320×240 traffic footage; the cascade it feeds is microseconds).

## Honesty contract (non-negotiable)

- [REAL] Two compound eyes, ~800 ommatidia each, in hexagonal
  packing (6 equidistant neighbors — the real ommatidial lattice).
  Frontal binocular overlap (~20-30% of each eye's facets). A frontal
  acute zone (fovea-like enlarged ommatidia). The motion-detection
  *algorithm* is the fly's own: the Hassenstein-Reichardt correlator
  (1956), the mechanism implemented by the T4/T5 direction-selective
  cells our motion bottle is wired from — on the hex lattice it runs
  as 3-axis (0/60/120 deg) opponent correlators, the natural axes of
  the packing. The looming *architecture* is the fly's own as well: LPLC2-style
  radial motion opponency — outward-vs-inward motion energy computed
  per tiled receptive-field template from the local direction-
  selective flow (Klapoetke et al.: LPLC2 is selective for radial
  expansion; [LITERATURE-CONSTRAINT]). Downstream, the motion / color
  / looming bottles run on measured FlyWire FAFB v783 connectome wiring.
  No neuron, synapse, or edge is invented anywhere in this chain.
- [MODEL] The neural dynamics inside those bottles are the standard
  simplified model (0.15 threshold, 4 steps).
- [MODELED] Everything about transduction: pixels → facet luminance
  (fractional block averaging), R1-6 as luma, RGB → fly color (RGB has
  no UV channel; blue/green proxies only), the radial-opponency pooling
  (3x3 tiled templates per eye, uniform weights, 3x3 dipole-merging
  smooth, dominance/growth thresholds, streak length, angular-spread
  gate), the exact overlap fraction (0.25), the acute-zone gain ramp
  shape and peak (1.5x, mean-normalized so calibration holds), facet
  layout, 1-frame delay, and all gains/thresholds (`MOTION_FLOOR`,
  `MOTION_GAIN`, `LOOM_DOM_MIN`, `LOOM_R_MAX`, `LOOM_MAG_GAIN`,
  `LOOM_STREAK_MIN`, `LOOM_CONTRACTION_GAIN`). The motion readout —
  mean of |local HR response| across the eye — is a deliberate design
  simplification (Cory, 2026-10-16: the eyes detect motion, they don't
  find its direction); the v3 HS/VS-style wide-field pooling and every
  direction field (`motion_dir`, `flow_dir`, `flow_vx/vy`, band arrows)
  are retired. `MOTION_GAIN` was recalibrated for the unsigned readout
  (120, was 800: incoherent local flicker no longer cancels, so the
  gain comes down ~7x to keep real-world dynamic range; the synthetic
  gates were re-verified green). Calibrated on synthetic scenes,
  verified against real footage (see below). The fly never saw your
  camera.
- [FICTION] Any gloss ("the machine opens its eyes") is fiction, not a
  claim about experience.

## What was proven (v2, 2026-10-16)

Synthetic gate suite (`_work/eyeloop_v2.py`), 15/15 pass:
1. Fused motion_dir sign flips (+1 / −1); per-eye directions agree;
   motion bottle fired (0.91) on both.
2. Looming bottle fired on the expanding disc (0.19), exactly 0.0 on
   translation (both directions) and static — including the
   entry-transient case (dot crossing an eye-window boundary), vetoed
   by centroid stability.
3. Zero events on the static control; change channels exactly silent.
4. 4.8 ms/frame mean (30fps budget: 33ms).
5. Binocular: frontal-zone motion seen by BOTH eyes (L=0.55, R=0.55,
   symmetric); far-left-edge motion seen ONLY by the left eye
   (L=0.97, R=0.0).

Live run (`_work/live_run_v2.py`): 60 s of the I-95 traffic cam,
600 frames at 9.8 fps effective, pipeline 13.8 ms mean / 32.4 ms p95,
72 motion events on the first run (34 on a quieter re-run; v1: 28 —
two eyes see at least as much), zero crashes. Annotated recording:
`_work/flyvision_demo_v2.mp4` (H.264, 60 s, 5 fps, 1.1 MB, three
panels: camera | left eye | right eye).

Calibration honesty: the binocular entry transient (object crossing an
eye-window boundary) initially faked looming via area growth. Fixed
with the centroid-stability veto (new-dark centroid shift > 1.5 facets
= one-sided entry, not expansion) — a cheap proxy for LPLC2's radial
motion opponency, documented above. Synthetic gates re-run green after
the fix. (v4 SUPERSEDES this: the looming detector is now true LPLC2-
style radial opponency; the area proxy and centroid veto are retired.)

## What was proven (v3, 2026-10-16) — the motion-arrow fix

Cory spotted it in the v2 video: per-facet motion arrows don't all
point the right way on real traffic. Quantified on textured synthetic
ground truth (seeded, two cars on a static correlated-noise road):
per-facet arrows only 41% within 90 deg of true direction — the
aperture problem at object edges plus texture aliasing, physics not a
bug. The fix is the fly's own: wide-field pooling (HS/VS tangential
cells). Pooled `flow_dir` scores 97.5% on the same scenes; per-band
arrows 80.8% on opposing traffic (global pooled honestly cancels to
~0 when lanes oppose — HS cells are opponent too).

Hex lattice (Cory's call): facets now sampled on the real ommatidial
packing — 23x35 offset rows, 805 facets/eye, 6 equidistant neighbors
(gated in the sealed selftest). Square-vs-hex accuracy matrix: tied
(per-facet ~41% both, pooled 97.5% vs 95.0%, band 80.8% vs 80.1%) —
kept hex for the anatomy. 3-axis HR (0/60/120 deg) replaces the 2-axis
version; the demo video renders true hexagonal facets.

Sealed selftest: 17/17 (added hex-equidistance gate + pooled
`flow_dir` gates on deterministic textured cars, +/-1 both ways).
Live I-95 re-run + `flyvision_demo_v3.mp4` (hex facets, faint
per-facet arrows under pooled band arrows). Honest residual:
per-facet arrows stay noisy on high-frequency texture — that is the
aperture problem, and the pooled arrows are the answer.

Spot-check honesty: motion events were correlated with pixel-level
frame change (elevated near events); vehicle identities were NOT
visually verified.

## What was proven (v4, 2026-10-16) — LPLC2 radial opponency

The looming detector is now the fly's real mechanism, not a proxy:
per-template (3x3 tiled, cf. LPLC2 RF tiling) outward-vs-inward motion
energy from the existing per-facet HR flow field, opponent subtraction,
plus an angular-spread gate (R ≤ 0.55: true expansion is radial in all
directions; a partially-visible translating edge is clustered),
sustained over 3 frames. Intensity scales with outward energy magnitude
(calibrated: the looming bottle's real wiring needs intensity ≥ 0.806
to fire). Contraction (sustained inward-dominant radial flow) is its own
reported signal.

What the old proxy got wrong: dark-area growth could not distinguish a
translating edge from expansion without the centroid hack, and it missed
slow approaches (per-frame growth below threshold). Radial opponency
kills translation structurally (opponent cancellation), and the angular-
spread gate kills partial-visibility entry (which faked a 0.52 loom
under the old system at slow entry speeds).

Synthetic gates (sealed selftest 20/20; eyeloop solve-gate SOLVED):
- Expanding disc → looming 0.26 (sealed) / bottle fires 0.1861 (eyeloop)
- Translating disc → exactly 0.0; static → 0.0; contracting → 0.0 loom
- Edge-entry (fast, slow, and window-boundary) → 0.0
- Two expanding discs → both eyes fire independently (L 0.78 / R 0.83)
- Contraction → own signal 0.28 (not a loom)
- 9.3 ms/frame (30fps budget: 33ms)

Honest residual: the 1-frame HR produces opponent dipole pairs at sharp
edges (merged by 3x3 smoothing into net regional flow); the angular-
spread threshold (0.55) is empirical with a thin margin on slow entry
(R 0.53 vs 0.55) — validated on the gate scenes, not proven in general.
On harsh synthetic correlated-noise texture, a fast translating car can
produce a single-frame 0.19 blip (below the bottle's 0.806 fire
threshold; the bottle stays silent) and a textured approach is weaker
than on clean scenes — the local flow is chaotic at texture scale.
Per-facet flow stays noisy (aperture problem); the template pooling is
the answer, same as motion. Live I-95 re-run was network-blocked
(YouTube HLS 429/SSL/proxy failures); the v1-v3 runs had zero looming
events on real traffic and the synthetic selectivity gates above are
the verified record.

## What was proven (v5, 2026-10-16) — direction removed

Cory's call: the eyes don't need to find direction — they need to SEE
and DETECT motion. The direction machinery (`motion_dir`, `flow_dir`,
`flow_vx/vy`, band arrows, HS/VS-style wide-field pooling) was
over-engineering and is stripped. Motion is now a scalar unsigned
energy: mean of |local HR response| across the eye. The
Hassenstein-Reichardt correlator stays (the detection mechanism);
opposing traffic now ADDS instead of canceling. Output contract is
exactly `{"motion", "color", "looming", "contraction"}` — zero direction
code remains in the output path (gated in the sealed selftest).

Recalibration honesty: the first unsigned run pegged motion at ~1.0 for
the entire I-95 minute — incoherent local flicker (headlight bloom,
compression shimmer) no longer cancels, so every frame summed to
saturation. `MOTION_GAIN` 800 → 120, measured on real footage:
traffic p10/p90 now 0.30/0.88 (real dynamic range, mean 0.50),
synthetic bar still 1.0 (clip), textured car 0.74, static exactly 0.0.
The sealed synthetic gates re-verified green after the change.

Sealed selftest: 20/20 (direction gates converted to detection gates:
left-moving and right-moving targets both read as motion, no sign;
exact output-keys gate added). Looming/color/contraction gates
unchanged. Live I-95 re-annotation (same 300 saved raw frames, new
retina): 1 continuous motion bout (rush-hour traffic never stopped —
honest; the v4 "21 bouts" were pooled-vector cancellation artifacts),
1 color, 0 looming, 0 contraction. `flyvision_demo_v5.mp4`: camera |
LEFT eye | RIGHT eye, hexagonal facets with motion heat-glow (firing
facets brighten), red LOOMING / blue CONTRACTION flash markers, NO
arrows anywhere, timestamped event log. 13.4 ms mean / 28.7 ms p95 per
frame.

Honest residual: the unsigned readout sits higher on noisy feeds than
the old pooled one by construction; `MOTION_FLOOR` (0.0002) was kept,
and a frozen-feed noise check would be needed to validate it against
real camera noise (the sealed static gate uses identical frames).

## BrainSquared integration

Registers as kind `"static"` (like compass — stateful, no tick):

```python
"retina": ("retina", "retina", "Retina", "static", {}),
```

Standard toggle: `BrainSquared(config={"bottles": {"retina":
{"enabled": False}}})` removes it. Note (honest limitation): the
per-bottle `sensitivity` multiplier in `perceive()` only applies to
direct `sense()` events; the retina is driven by `frame()`, so a caller
scales its output intensities if tuning is needed. The eyeloop pattern:

```python
ret = body.bottles["retina"]
out = ret.frame(camera_frame)   # fused binocular output
body.perceive({"kind": "sense", "bottle": "motion",
               "intensity": out["motion"]})
body.perceive({"kind": "sense", "bottle": "looming",
               "intensity": out["looming"]})
```

`selftest.py` is SEALED (deterministic, no clock, no network, no writes,
exit 0 — 14/14 checks) — run at build time. It is not an endpoint.

## v1 record

v1 (monocular, 30×26 single eye) is superseded by v2. Its test scripts
(`_work/eyeloop.py`, `_work/live_run.py`) and recording
(`_work/flyvision_demo.mp4`) are kept as the historical record.
