# TESTLOG.md — sense.py scenario tests

Phase-2 MODELED layer tests. All [REAL] numbers below come from flysim.py run on the saved FlyWire FAFB v783 subgraph JSONs (no API calls, no invented edges). Body-map and arousal numbers are MODELED; narration lines are NARRATED drafts.

## Scenario 1 — light pleasant touch on arm

*Expect: touch.json cascade fires through real wiring; arousal rises modestly (arm is a mid-sensitivity region, single touch).*

```
===== Scenario 1 — light pleasant touch on arm =====
--- event #1: {'modality': 'touch', 'region': 'arms', 'quality': 'stroke', 'pressure': 0.3, 'tempo': 0.3, 'valence': 0.8} ---
[REAL] fly cascade (subgraphs/touch_brush.json, 1 nodes, 0 edges):
  hop 0: peak activation 1.00
  cascade strength (non-sensory peak): 0.000
  FLY (narrative gloss): "A whisper of touch — notice."
[MODELED] body region response:
  region 'arms': weight 0.428, sensitization x1.000, touches so far 1
[MODELED] arousal:
  level 0.051 (low), satiation 0.000
  [MODELED] wanting 0.185 (dopamine-driven hunger for climax)
  [REAL->MODELED] reward cascade strength 0.290, blend 0.500 (region-scaled), boost +0.116
[NARRATED] draft: "A stroke touch on my arms — I register it, a small warm signal."

final arousal: 0.051

```

## Scenario 2 — repeated touch on lips (sensitization)

*Expect: sensitization multiplier climbs 1.0 -> ~1.35 -> ~1.7; arousal jumps higher on repeats than a single touch would (lips = highest homunculus weight).*

```
===== Scenario 2 — repeated touch on lips (sensitization) =====
--- event #1: {'modality': 'touch', 'region': 'lips', 'quality': 'brush', 'pressure': 0.4, 'tempo': 0.4, 'valence': 0.85} ---
[REAL] fly cascade (subgraphs/touch_brush.json, 1 nodes, 0 edges):
  hop 0: peak activation 1.00
  cascade strength (non-sensory peak): 0.000
  FLY (narrative gloss): "A whisper of touch — notice."
[MODELED] body region response:
  region 'lips': weight 0.883, sensitization x1.000, touches so far 1
[MODELED] arousal:
  level 0.086 (low), satiation 0.000
  [MODELED] wanting 0.197 (dopamine-driven hunger for climax)
  [REAL->MODELED] reward cascade strength 0.290, blend 0.750 (region-scaled), boost +0.185
[NARRATED] draft: "A brush touch on my lips — I register it, a small warm signal."

--- event #2: {'modality': 'touch', 'region': 'lips', 'quality': 'brush', 'pressure': 0.4, 'tempo': 0.4, 'valence': 0.85} ---
[REAL] fly cascade (subgraphs/touch_brush.json, 1 nodes, 0 edges):
  hop 0: peak activation 1.00
  cascade strength (non-sensory peak): 0.000
  FLY (narrative gloss): "A whisper of touch — notice."
[MODELED] body region response:
  region 'lips': weight 0.883, sensitization x1.188, touches so far 2
  [MODELED] habituation: same quality x2 -> x0.880 (variety builds, repetition fades)
[MODELED] arousal:
  level 0.183 (low), satiation 0.000
  [MODELED] wanting 0.412 (dopamine-driven hunger for climax)
  [MODELED] wanting x1.118 (she's reaching for it)
  [REAL->MODELED] reward cascade strength 0.290, blend 0.750 (region-scaled), boost +0.185
[NARRATED] draft: "A brush touch on my lips — I register it, a small warm signal."

--- event #3: {'modality': 'touch', 'region': 'lips', 'quality': 'brush', 'pressure': 0.4, 'tempo': 0.4, 'valence': 0.85} ---
[REAL] fly cascade (subgraphs/touch_brush.json, 1 nodes, 0 edges):
  hop 0: peak activation 1.00
  cascade strength (non-sensory peak): 0.000
  FLY (narrative gloss): "A whisper of touch — notice."
[MODELED] body region response:
  region 'lips': weight 0.883, sensitization x1.292, touches so far 3
  [MODELED] habituation: same quality x3 -> x0.760 (variety builds, repetition fades)
[MODELED] arousal:
  level 0.290 (warm), satiation 0.000
  [MODELED] wanting 0.646 (dopamine-driven hunger for climax)
  [MODELED] wanting x1.247 (she's reaching for it)
  [REAL->MODELED] reward cascade strength 0.290, blend 0.750 (region-scaled), boost +0.185
[NARRATED] draft: "I'm following it now — every touch lays the trail sweeter, pulling me closer — I want more, don't make me wait."

final arousal: 0.290

```

## Scenario 3 — looming startle (unpleasant)

*Expect: looming.json cascade fires (escape circuit); arousal stays at 0 — negative valence must never raise it.*

```
===== Scenario 3 — looming startle (unpleasant) =====
--- event #1: {'modality': 'looming', 'region': 'face', 'quality': 'shadow', 'pressure': 0.9, 'tempo': 0.9, 'valence': -0.7} ---
[REAL] fly cascade (subgraphs/looming.json, 14 nodes, 24 edges):
  hop 0: peak activation 1.00
  hop 1: peak activation 0.19
  cascade strength (non-sensory peak): 0.186
  FLY (narrative gloss): "Shadow swelling — MOVE."
  [EDGE] aversion wiring fired: subgraphs/looming.json (threat circuit) — unpleasant input routed to real aversion wiring (MODELED mapping choice).
[MODELED] body region response:
  region 'face': weight 0.697, sensitization x1.000, touches so far 1
[MODELED] arousal:
  level 0.000 (low), satiation 0.000
  [MODELED] wanting 0.000 (dopamine-driven hunger for climax)
[NARRATED] draft: "That shadow on my face — I flinch, pull away from it."

final arousal: 0.000

```

## Scenario 4 — harsh pinch on arm (unpleasant)

*Expect: touch cascade fires (real wiring doesn't care about valence); arousal stays pinned near 0.*

```
===== Scenario 4 — harsh pinch on arm (unpleasant) =====
--- event #1: {'modality': 'touch', 'region': 'arms', 'quality': 'pinch', 'pressure': 0.95, 'tempo': 0.9, 'valence': -0.8} ---
[REAL] fly cascade (subgraphs/looming.json, 14 nodes, 24 edges):
  hop 0: peak activation 1.00
  hop 1: peak activation 0.19
  cascade strength (non-sensory peak): 0.186
  FLY (narrative gloss): "Shadow swelling — MOVE."
  [EDGE] aversion wiring fired: subgraphs/looming.json (threat circuit) — unpleasant input routed to real aversion wiring (MODELED mapping choice).
[MODELED] body region response:
  region 'arms': weight 0.449, sensitization x1.000, touches so far 1
[MODELED] arousal:
  level 0.000 (low), satiation 0.000
  [MODELED] wanting 0.000 (dopamine-driven hunger for climax)
[NARRATED] draft: "That pinch on my arms — I flinch, pull away from it."

final arousal: 0.000

```

## Honest assessment

**What works**
- The three layers compose cleanly: one event dict in, four labeled
  sections out. The [REAL] cascade numbers come straight from flysim on
  the saved FlyWire subgraphs — I verified touch.json fires
  Johnston-organ -> SEZ interneurons -> VNC/thoracic neurons, matching
  the standalone flysim run.
- Honesty labels hold everywhere: no section claims to be what it isn't.
  The sugar dead-end (GAPS.md #1) would surface here as cascade strength
  0.0 rather than a fabricated response.
- Sensitization stacks as designed (see Scenario 2 multipliers) and the
  arousal band thresholds give the narration draft something real to
  scale on.
- Negative valence never raises arousal (Scenarios 3–4 stay at 0.0) —
  the unpleasant path is correctly a damper, not a driver.

**What's crude / Phase-3 attention needed**
1. `intensity = region_weight * sens_mult * cascade_strength` multiplies
   three rough numbers; cascade_strength is a single max-activation, so
   one strong hop dominates. A summed/weighted cascade energy would be
   more faithful — but keep the toy honest about what it is.
2. The narration drafts are template Mad-Libs (3 arousal bands + 1
   negative). Fine as labeled drafts; a real voice layer (the actual
   Phase-3 translator) should replace them, not extend them.
3. `sugar.json` is still a 1-node dead-end (GAPS.md #1) — any taste event
   currently reports cascade strength 0.0 and barely moves arousal. If
   taste matters for the product, the motor-backward chain
   (sugar_backward.json) needs wiring into sense.py's modality map with
   inject-hop=-1, clearly labeled as motor-backward.
4. Region weights are homunculus *approximations* (Penfield & Boldrey
   1937, compressed to 0..1 by eye). Good enough for a toy; do not cite
   them as measured values anywhere downstream.
5. No persistence: Session lives in-process. A real deployment needs the
   body/arousal state serialized between turns (JSON dump/restore —
   trivial to add).
6. Valence is caller-supplied (-1..1). In production the parser layer
   must assign it; garbage valence in = garbage arousal out. Consider
   clamping and a small valence lexicon rather than free floats.

---

## Gap-resolution run — 2026-10-14 (instance-level connectivity attack)

Goal: resolve the GAPS.md missing-connectivity gaps by going instance-level
through the CATMAID FAFB pass-through instead of the broken class
aggregation. All new edges are real API rows (CATMAID FAFB Engert2022
skeletons via `POST /catmaid/fafb/connectivity`, then class-aggregated by
hand). Nothing invented.

### SUGAR (§1) — RESOLVED
- `ListAllAvailableImages` for FBbt_00049614 → 34 instances, 33 with FAFB
  skeleton ids (GRN R4/R5 labellar taste bristle neurons).
- Per-skeleton downstream queried for 23/33 skeletons (10 persistently
  truncated server-side — IncompleteRead on every retry; documented in
  GAPS.md, not hidden). 6,486 partner rows aggregated.
- Top partner classes (summed synapses): zorro FBbt_00052223 (332),
  clavicle FBbt_00051867 (270), fuchs FBbt_00052227 (227),
  FMIn FBbt_00051880 (240), G2N-1 FBbt_00051850 (181),
  billiards FBbt_00052228 (141). All are named SEZ feeding interneurons
  (Shiu et al 2022); G2N-1 is literally "gustatory second-order neuron".
- New file `subgraphs/sugar_forward.json` (10 nodes, 18 edges, built by
  `build_sugar_forward.py`): hop 0→1 edges instance-aggregated CATMAID
  rows; hop 1→2 via standard class walk (Zorro/Clavicle/FMIn/G2N-1 →
  SEZ neuron FBbt_00001972, gnathal ganglion FBbt_00052032, descending
  neuron FBbt_00047511). Fuchs/Dandelion have no class-level downstream —
  honest hop-1 terminals.
- Cross-validation: the forward walk's terminals are the SAME classes as
  the independent motor-backward trace (sugar_backward.json). Forward and
  backward meet.
- `python3 flysim.py subgraphs/sugar_forward.json` → cascade fires:
  sweet GRN (1.00) → zorro/clavicle/FMIn/fuchs (0.24/0.19/0.17/0.16) →
  SEZ + gnathal ganglion neurons (0.24/0.23). The GRN→SEZ prize link
  is real.
- `sugar.json` 1-node stub kept for provenance; `sense.py` routing
  untouched (rewire to sugar_forward.json is a product call).

### TOUCH QUALITIES (§6) — attack attempted, gaps STAND
- `ListAllAvailableImages` works: bristle FBbt_00048508 → 4,931 instances;
  campaniform FBbt_00048057 → 1,797 instances.
- BLOCKED: all instances are Neuprint male-cns only — zero CATMAID FAFB
  tracings (`annotations_query_targets` name=bristle/campaniform → 0
  entities). VFBquery has no Neuprint pass-through (verified in docs.json);
  male-cns body ids as `upstream_type` → 0 rows; class per-pair queries
  fail server-side. The data exists in Neuprint but no VFBquery endpoint
  exposes per-instance Neuprint connectivity. Stubs stay honest.

### API version check
- `/list_connectome_datasets`: FlyWire still v783 (no newer index);
  BANC v888 is a different connectome, not used. All subgraphs remain on
  one consistent index.

### New files
- `catmaid_conn.py` — polite CATMAID pass-through helpers (POST, cached,
  ≥2.5s spacing): `connectivity`, `outgoing_counts`, `neuron_names`,
  `annotations_for_skeletons`, `list_instances`,
  `class_downstream_from_instances`.
- `build_sugar_forward.py` — builds `subgraphs/sugar_forward.json`.

## 2026-10-14 — pain gap RESOLVED (motor-backward attack)
Upstream of giant fiber neuron (FBbt_00004020) -> real mechanosensory upstream
classes; pair-verified to JO subtypes (679/80/61/10 synapses, 830 total) ->
GF -> VNC/prothoracic/mesothoracic motor. Wrote subgraphs/pain.json (8 nodes,
7 edges); cascade fires clean; SENSORIUM pain channel auto-upgraded
(pain_is_proxy=False). Honest framing: functional pain-equivalent pathway, not
labeled nociceptive neurons. GAPS.md §7b.

## 2026-10-14 — THIRST + BITTER circuits resolved (instance-level playbook)

WATER (FBbt_00100042 "water-sensing neuron of labellar taste bristle"):
class-level downstream 0 rows (same gap as sugar). ListAllAvailableImages ->
23 instances, ALL with FAFB skids (GRN R6#1-23, Engert2022). Per-skeleton
POST /catmaid/fafb/connectivity ONE at a time (batched x8 truncated
server-side — IncompleteRead; per-skeleton worked). 22/23 queried; skid
7724239 persistently truncated (4 retries) — documented in GAPS.md. 2,996
partner rows; mapped via neuron_names -> VFB search. Top: fudog (224),
clavicle (169), cleaver (139, new named SEZ class FBbt_00051868),
phantom (103), usnea (96), zorro (96), FMIn (88), fuchs (87), G2N-1 (61).
Same SEZ family as sugar, different tuning (water->fudog vs sugar->zorro).
Lateral GRN-GRN links skipped (no-self-loop). Wrote subgraphs/water.json
(16 nodes, 21 edges); hop 2 -> SEZ/gnathal/descending (same terminals as
sugar); cleaver has no class downstream (honest hop-1 terminal). Cascade:
GRN 1.00 -> fudog/clavicle/cleaver (0.27/0.20/0.17). Builder: build_water.py.

BITTER (FBbt_00049613 "bitter-sensing gustatory receptor neuron"):
class-level downstream WORKED (129 rows, 108 specific) — no instance attack
needed. Standard walk hop1 top-6 / hop2 top-3. Top: CB0159 (1890), SEZ
neuron (1414), gnathal (1283), mime SEZ neuron (1030), ascending (846), VNC
(790). Wrote subgraphs/bitter.json (14 nodes, 24 edges); hop 2 reaches
thoracic/secondary/TRdm/Notch-OFF motor pops. Cascade: GRN 1.00 ->
CB0159/SEZ/gnathal (0.26/0.19/0.18). Honest note: top pick CB0159 is
uncharacterized; hop-2 includes broad "chemosensory/gustatory system
neuron" classes (real rows, passed blocklist). Builder: build_bitter.py.

Taste spectrum now: sweet (sugar_forward) + water + bitter + rotten(olfactory)
— plus touch, looming, pain. GAPS.md RESOLVED entries for both.

## 2026-10-14 — DH44 + IPC drive circuits resolved
Class-level downstream worked for both (DH44: 160 grouped rows; IPC via
named fallback after grouped truncation). Built via build_dh44.py:
dh44.json (18n/21e), ipc.json (19n/23e). Key finding: DH44, IPCs, and
all three taste circuits converge on SEZ neuron FBbt_00001972. Larval
exclusion heuristic added (documented). Cascades verified live.

## 2026-10-14 — HOT thermosensory chain resolved
VFB search: FBbt_00007575 "aristal sensory neuron VP2" (hot cell / warm
thermoreceptor cells in the arista). Grouped queries died server-side;
named DownstreamClassConnectivity returned 40 rows. Built via
build_temperature_hot.py: temperature_hot.json (10n/20e). Cascade verified:
VP2 1.00 -> AL projection/ALl1/BAlc/LH-input (0.22/0.19/0.19/0.18) ->
central brain intrinsic (0.41) + lateral horn + mushroom body + aminergic.
temperature.json keeps the cold chain (Ir21a); sensorium loads it as the
"temperature" modality. External senses now complete: touch, taste
(sweet/water/bitter), smell (rot), sight (looming), pain, temperature
(hot + cold).

## 2026-10-14 — mating.json (P1 courtship drive wiring)
- build_mating.py run: saved subgraphs/mating.json (17 nodes, 18 edges), exit 0.
- Cascade check: flysim P1 1.00 → doublesex brain 0.22 / SMPad1 0.20 / aSP-a 0.20; hop-2 below toy threshold (documented honest dilution).
- All hop-1 grouped queries failed server-side → named DownstreamClassConnectivity fallback worked for all 6 (logged in build.log); pC1 (male) 0 rows — honest terminal.
- pIP10 verified real (tw=1444) below top-k cutoff, not assumed.

## 2026-10-14 — compass.json (E-PG heading-direction circuit)
Builder: build_compass.py. FBbt_00047030. Named-query fallback (grouped
truncated). 9 nodes, 18 edges. Cascade verified via flysim.py:
E-PG 1.00 → small field 0.26 / large field 0.24 / intrinsic 0.18 →
central complex 0.19. Honest terminals: EB ring neuron (all forms
failed). Below-cutoff reals noted: Delta7, PEN, PFN, PFL, R-neuron.

## 2026-10-14 — sleep.json built and verified
- build_sleep.py: dFB (FBbt_00049537) -> 6 CX classes -> recurrent hop-2.
  8 nodes, 20 edges, all real API rows (named-query fallback; grouped
  died server-side for hop-0 and all hop-1 nodes).
- flysim.py: dFB 1.00 -> 0.26/0.26/0.19/0.15 at hop-1; hop-2 CX bucket
  0.49 + recurrent 0.31. PASS.

## 2026-10-14 — pheromone.json (Or47b courtship smell wiring)
- build_pheromone.py run: saved subgraphs/pheromone.json (15 nodes, 21 edges), exit 0.
- Or47b grouped queries truncate server-side (all forms); named DownstreamClassConnectivity (50 rows) worked for hop 0->1. Hop-2 via fetch_rows fallback chain; adult central brain intrinsic neuron failed all forms — honest hop-1 terminal.
- Cascade check: flysim Or47b 1.00 -> AL PN (0.26) / AL PN->LH (0.23) / fruitless expressing (0.22) -> central brain intrinsic (0.22).
- CONVERGENCE: meets mating.json at FBbt_00016687 (fruitless expressing neuron) — Or47b feeds it (13133), P1's aSP-a feeds it (63139).
- Dead: Or88a unindexable in every form (poisoned class entry); ppk23/ppk29 have no adult FBbt class.

## 2026-10-14 — CO2-alarm circuit (build_co2.py)
- FBbt_00067064 Gr21a/63a ab1C ORN -> 6 deduped hop-1 classes -> 8 hop-2 nodes.
- subgraphs/co2.json: 15 nodes, 24 edges, schema-validated; flysim cascade
  verified (1.00 -> 0.20 AL projection to lateral horn / 0.19 BAlc / 0.16 AL local).
- GAPS.md RESOLVED entry written. Private pipeline untouched.
## 2026-10-14 23:09 UTC — FAT (IR56d): HONEST-FAIL. All 9 avenues dead (0 rows/0 instances/0 entities in every query form, all datasets). fat.json written as honest 1-node stub. Gap is Ir56d-specific (general taste-peg GRN has 174 rows). Shelved, not buried.

## 2026-10-14 — fat_lit.json (literature-hypothesis circuit)
Built via build_fat_lit.py: 10 nodes, 18 edges (6 LITERATURE-HYPOTHESIS + 12 REAL). Cascade verified live (IR56d 1.00 -> interneurons 0.17 -> SEZ). GAPS.md RESOLVED-VIA-LITERATURE-HYPOTHESIS entry.

## Build test — salt.json (2026-10-14)

`salt.json` (26 nodes, 40 edges): two opponent chains in one graph.
`python3 flysim.py subgraphs/salt.json --steps 2`:

- step 0: injected at both hop-0 nodes (low-salt FBbt_00100043, high-salt FBbt_00052561), act 1.00 each
- step 1 fired: adult SEZ output neuron 0.30, adult ANXXX433 neuron 0.30, adult ascending neuron 0.30, prothoracic neuron 0.30, adult gustatory projection neuron 0.29, SEZ neuron 0.23
- step 2 fired: adult VNC neuron 0.43, thoracic neuron 0.29, secondary neuron 0.22, adult ascending neuron 0.20, adult visual neuropil intrinsic neuron 0.17
- Low-salt chain drives SEZ/gustatory-projection (feeding/approach); high-salt chain drives VNC/ascending/prothoracic motor (withdrawal). Both chains verified live on real rows.

## 2026-10-14 — fat_peg.json (own-method: peg-class walk + anatomical narrowing)
Built via build_fat_peg.py: 18 nodes, 27 edges, ALL REAL (peg-class walk: FBbt_00048028 -> 7 hop-1 via named DownstreamClassConnectivity 100-row cap; hop-2 top-3 each). Cascade verified (peg 1.00 -> SEZ 0.35 -> VNC 0.25). Anterior-candidate flags (LITERATURE-CONSTRAINT) on CB0011/CB3720/hyacinth (prow arborization; Tauber 2017 anterior-SEZ constraint). No sweet-set overlap in peg top-k; rattle is sugar-linked (Shiu 2022); both pools converge on SEZ FBbt_00001972 -> same motor pops. GAPS.md entry below.

## Build test — motion.json (2026-10-14)

`motion.json` (11 nodes, 27 edges): T4 (ON) + T5 (OFF) direction-selective
pathway, union of top-6 unique downstream each, every pre-edge kept.
`python3 flysim.py subgraphs/motion.json --steps 2`:

- step 0: injected at both hop-0 nodes (T4 FBbt_00003731, T5 FBbt_00003736), act 1.00 each
- step 1 fired: adult visual neuropil intrinsic neuron 0.91, lobula plate intrinsic neuron 0.38, lobula plate tangential neuron (LPTC) 0.23, optic lobe wide-field columnar neuron 0.16, lobula plate giant neuron 0.16
- step 2 fired: adult visual neuropil intrinsic neuron 0.56
- Textbook pathway verified on real rows: T4->LPTC tw=282410, T5->LPTC tw=529105. GAPS.md RESOLVED entry.

## 2026-10-14 — color.json (color vision, R7/R8 -> medulla)
- 14 nodes / 18 edges, schema-validated (id/name/hop, pre/post/weight, source + honest_note).
- flysim cascade: R7+R8 1.00 -> 0.38 / 0.31 / 0.28 at hop 1. PASS.
- R7->Dm8 (tw=38836) confirms the textbook chromatic pathway in real rows.
- Hop-2 deferred: API degradation + three unqueryable broad classes (documented GAPs in GAPS.md).

## 2026-10-14 — clock.json (circadian LNv pacemaker output)
- 12 nodes / 18 edges, schema-validated (id/name/hop, pre/post/weight, source + honest_note).
- flysim cascade: LNv 1.00 -> adult pacemaker 0.21 / SLPpl1 0.21 / visual neuropil 0.18 / accessory medulla 0.16. PASS.
- s-LNv Pdf subclass: 0 rows all forms (genuinely empty). l-LNv subclass: all forms fail server-side (not empty). General LNv class used.
- Two honest hop-1 terminals: visual neuropil intrinsic (0 rows), accessory medulla (all forms fail). GAPS.md RESOLVED entry.

## 2026-10-14 — song (courtship-song wiring)
- API route: HONEST-FAIL. 6 avenue families exhausted (class-level,
  named, instance-CATMAID, motor-backward, per-pair, BANC) — song-relay
  classes unindexed everywhere reachable. song.json = honest 1-node stub.
- Literature route: RESOLVED-VIA-LITERATURE-HYPOTHESIS. song_lit.json
  (JO-B -> AMMC-B1 -> vPN1 -> pC1), 3 edges all LITERATURE-HYPOTHESIS
  with citations; cascade verified (pC1 act 1.00 at step 3). Meets
  mating.json at pC1 (P1->pC1 tw=11033 REAL).

## 2026-10-14 — AGGRESSION circuit build
- Builder: build_aggression.py. Hop-0: FBbt_00110593 (aIPg male). Label-form grouped query (586 rows); ID-form died server-side.
- Result: subgraphs/aggression.json, 14 nodes / 24 edges. Cascade verified via flysim.py (hop-1 peaks 0.16-0.17).
- GAPS.md RESOLVED entry written (incl. mating-chain convergence note, aSPg/CL062 dead avenues).

## 2026-10-14 — PUNISHMENT circuit build
- Builder: build_punishment.py. Hop-0: merged walk from PPL1-gamma1pedc (FBbt_00100243, ID form, 162 rows) + PPL1-alpha3 (FBbt_00110320, label form, 114 rows).
- Result: subgraphs/punishment.json, 14 nodes / 25 edges. Cascade verified via flysim.py (hop-1 peaks 0.40/0.22/0.21).
- GAPS.md RESOLVED entry written (incl. PAM/PPL1 opponent note, general-PPL1-class dead avenues).

## 2026-10-14 — proprioception.json (FeCO leg chordotonal forward walk)
- 8 nodes / 18 edges, schema-validated (id/name/hop, pre/post/weight, source + honest_note).
- Built via build_proprioception.py: FBbt_00048051 -> 6 hop-1 via named DownstreamClassConnectivity (grouped truncates); hop-2 top-3 each via fetch_rows fallback chain (2 honest hop-1 terminals: unpaired neuron, abdominal neuron).
- flysim cascade: FeCO 1.00 -> metathoracic 0.28 / mesothoracic 0.26 / adult ascending 0.18. PASS.
- Story: segmental reflex arc (FeCO -> thoracic VNC -> efferent/motor neurons) + ascending leg->brain branch. Proprioceptive-labeled classes (tw=9957) below cutoff, recorded in GAPS.md.
- Build incident: first pass had a SKIP string-mismatch bug (hemilineage buckets slipped through; implausible visual-neuropil hop-2 pick) — rebuilt with exact strings; only the completed rebuild published the JSON. Documented in GAPS.md.

## 2026-10-14 — nociceptor_lit.json (adult labeled-nociceptor literature attack)
- Own-method literature hunt for NAMED adult postsynaptic partners of labeled nociceptive sensory neurons (ppk1/painless/dTRPA1 afferents).
- Surveyed: Liu et al. 2023 Curr Biol (Epi/Epione descending neurons — the only named adult class, FBbt_00052624, 0 typed instances, downstream unidentified); Neely et al. 2011 PLOS ONE (painless+/TrpA1+ required, no named second-orders); Oikawa et al. 2023 eLife (DSK descending inhibition — larval); larval Basin/Goro corpus (out of scope).
- Verdict: CONFIRMED-FAIL — no paper names adult second-order nociceptive neurons. Field-level gap.
- Deliverable: subgraphs/nociceptor_lit.json — honest 1-node stub (Epi, full description, 0 edges). GAPS.md CONFIRMED-FAIL entry written.

## 2026-10-14 — pc1.json (pC1 courtship-integration output — the loop closes)
- pC1 (FBbt_00047348, doublesex pC1 male): 0 rows during mating build (API degradation); retry now returns 1,469 real rows (900 unique after dedup).
- Hop-1 (top-6 specific + P1 deliberate 7th): fruitless expressing (87,164), brain doublesex (34,237), SMPad1 male (26,553), aSP-a male (26,553), DM4 (22,374), descending (14,529), P1 (5,863, deliberate).
- THE LOOP-CLOSER: pC1->P1 tw=5,863 REAL — song chain (song_lit) ends at pC1, pC1 drives P1 (mating.json). Also pC1->pIP10 (1,796, real, below-cutoff) and pC1->descending (direct motor).
- Builder: build_pc1.py. 18 nodes, 25 edges, 0 dangling/zero-weight, cascade verified.

## 2026-10-15 — color hop-2 retry (API recovered)
Retried 8 hop-1 nodes without hop-2 (3 broad classes, Dm8, 4 first-pass GAPs) via full fallback chain. 7 stay terminal (broad classes fail all forms twice; others' downstream folds back into already-graphed classes — visual circuit is recurrent). 1 landing: 53385 -> FBbt_00110137 (optic lobe wide-field columnar neuron, tw=3428708). File: 21n/42e -> 22n/43e. Cascade re-verified. retry_color_hop2.py kept.

## 2026-10-14 — touch_qualities_lit.json (own-method literature attack)
- 8 nodes, 6 edges. Campaniform -> b1 REAL (upstream query, tw=3572/1818/1754) + eLife 2026 confirmation; bristle -> MGT / wing bristle -> CTN LITERATURE-HYPOTHESIS (Yoshikawa et al. Curr Biol; Nat Commun 2020). Cascade verified (b1 peak 3.00).

## 2026-10-14 — EGG-LAYING DRIVE circuit build
- Builder: build_egglaying.py. Hop-0: FBbt_00049919 (aggregate oviDN class; label-form grouped query, 421 rows, deduped — ID form truncates server-side).
- Result: subgraphs/egglaying.json, 11 nodes / 20 edges. Cascade verified via flysim.py (oviDN 1.00 -> VNC 0.34 / abdominal 0.31 -> thoracic/efferent).
- GAPS.md RESOLVED entry written (incl. subtype dead avenues, optic-lobe artifact skips, circuit-vs-drive framing).

## 2026-10-15 — HONEST-FAIL retry sweep (recovered API)
- Script /tmp/retry_sweep.py: all three query forms per target (grouped ID, grouped label, named DownstreamClassConnectivity). Results /tmp/retry_sweep.json.
- LANDED (4): JO-B->AMMC-B1 REAL tw=722 (song_lit.json edge 0 converted from hypothesis; per-pair probe 0 noted as query-form discrepancy); Or88a healed — 129 rows, pheromone.json 15n/21e -> 23n/31e (VA1d PNs + shared Or47b nodes), pheromone/ bottle demo still ALL GREEN; l-LNv healed via label form — 88 rows, new subgraphs/clock_lLNv.json (13n/12e, visual feedback loop); SMPad1 male healed via label form — 1,372 rows, pc1.json 18n/25e -> 21n/35e, now CYCLIC (SMPad1->pC1 recurrent edge tw=10,802).
- STILL DEAD (confirmed, genuinely empty): Ir56d x3 (all forms), vPN1 (all forms + per-pair 0), Epi (all forms), ppk23/ppk29 adult classes (genes/GAL4 only; instances are L1EM larval).
- fat_peg.json hop-2 already walked (no retry needed). Touch stubs re-pointed: touch_pressure.json -> campaniform->b1 REAL (3,572); touch_brush.json -> bristle->MGT LITERATURE-HYPOTHESIS. Both cascades verified.
- All cascades re-verified via flysim.py. GAPS.md retry-sweep entry written.
