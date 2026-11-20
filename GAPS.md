# GAPS.md — honest record of what the API could NOT resolve

Every edge in the subgraph JSONs is a real VFBquery/FlyWire row. This file
records where the data ran out, so no one mistakes absence for wiring.

## RESOLVED — 2026-10-14: BITTER forward walk via class-level queries

**Gap closed:** bitter-sensing GRN downstream connectivity. Unlike
sweet/water, the class FBbt_00049613 "bitter-sensing gustatory receptor
neuron" (bitter-sensing neuron) HAS indexed class-level downstream
connectivity — `/query_connectivity` returned 129 rows (108 specific
candidates after the documented GENERIC-superclass blocklist), so no
instance-level attack was needed. Standard top-k walk: hop 1 top-6,
hop 2 top-3 per node.

**Yield — hop-1 picks by total synapse weight:**
- adult CB0159 neuron FBbt_20003990 — 1890
- subesophageal zone neuron FBbt_00001972 — 1414
- gnathal ganglion neuron FBbt_00052032 — 1283
- adult mime subesophageal neuron FBbt_00051914 — 1030 (another named SEZ
  interneuron in the Shiu-style whimsical series)
- adult ascending neuron FBbt_00048301 — 846
- adult VNC neuron FBbt_00059289 — 790

**Result:** `subgraphs/bitter.json` — 14 nodes, 24 edges. Hop-2 walk
reaches thoracic/secondary/TRdm/Notch-OFF motor populations (via VNC
neuron, whose grouped query failed and fell back to the named
DownstreamClassConnectivity query — logged in the build output).
Cascade verified: GRN 1.00 → CB0159/SEZ/gnathal (0.26/0.19/0.18).
Builder: `build_bitter.py`.

**Honest note:** bitter's hop-1 fans out less specifically than
sweet/water — top pick is the uncharacterized CB0159 class rather than a
named second-order neuron, and hop-2 includes broad classes
("chemosensory system neuron", "gustatory system neuron") that passed the
GENERIC blocklist. All are real rows; the walk's selection heuristic is
documented in build_graphs.py.

## RESOLVED — 2026-10-14: WATER (thirst) forward walk via instance-level aggregation

**Gap closed:** water-sensing GRN downstream connectivity. Class-level
`/query_connectivity` for FBbt_00100042 "water-sensing neuron of labellar
taste bristle" (W cell, type C GRN of labellum) returned 0 rows — same
failure mode as sugar. Instance-level attack worked.

**Method:** `ListAllAvailableImages` for FBbt_00100042 → 23 instances, ALL
with CATMAID FAFB skeleton ids (GRN R6#1–23, Engert2022). Per-skeleton
downstream via `POST /catmaid/fafb/connectivity`, ONE skeleton per request
(batched queries of 8 truncated server-side — IncompleteRead; the batch
failure is what forced per-skeleton queries). 22/23 skeletons queried;
skid 7724239 persistently truncated on every retry (4 attempts) — its
synapses are missing from the sums, noted not hidden. 2,996 partner rows
aggregated. Partners mapped via `neuron_names` → VFB search → FBbt class.

**Yield — top partner classes by summed synapses:**
- adult fudog subesophageal neuron FBbt_00051883 — 224
- adult clavicle subesophageal neuron FBbt_00051867 — 169
- adult cleaver subesophageal neuron FBbt_00051868 — 139 (new named SEZ
  interneuron in our walks; VFB search confirms the class)
- adult phantom subesophageal neuron FBbt_00051927 — 103
- adult usnea subesophageal neuron FBbt_00051956 — 96
- adult zorro subesophageal neuron FBbt_00052223 — 96
- adult FMIn subesophageal neuron FBbt_00051880 — 88
- adult fuchs subesophageal neuron FBbt_00052227 — 87
- G2N-1 (adult gustatory second-order neuron type 1) FBbt_00051850 — 61
- adult quasimodo subesophageal neuron FBbt_00052229 — 47
- adult dandelion subesophageal neuron FBbt_00052232 — 40
- adult billiards subesophageal neuron FBbt_00052228 — 29

Notable: water feeds the SAME named SEZ interneuron family as sugar
(fudog/clavicle/zorro/FMIn/fuchs/G2N-1/…) but with different tuning —
water's top partner is FUDOG (224) where sugar's was ZORRO (332). Lateral
GRN→GRN links (same class as hop 0) skipped per the no-self-loop
convention. One real cross-modal partner below the top-6 cutoff: skid
14003783 "Uniglomerular mALT VP5 + SEZ adPN" (olfactory projection neuron,
51 synapses) — noted in water.json's honest_note, not hidden.

**Result:** `subgraphs/water.json` — 16 nodes, 21 edges. Hop 0→1 edges are
instance-aggregated CATMAID FAFB rows; hop 1→2 via the standard
class-level walk, converging on SEZ neuron FBbt_00001972, gnathal ganglion
neuron FBbt_00052032, and adult descending neuron FBbt_00047511 — the SAME
terminal classes as sugar. Adult cleaver subesophageal neuron has no
class-level downstream (0 rows) — honest hop-1 terminal. Builder:
`build_water.py`.

## RESOLVED — 2026-10-14: SUGAR forward walk via instance-level aggregation

**Gap closed:** §1 (sweet-GRN downstream connectivity). The class-level
queries were broken, but the data existed at instance level — exactly as the
`/run_query` error hinted ("its instances have downstream connectivity").

**Method:**
1. `ListAllAvailableImages` for FBbt_00049614 → 34 instances, 33 with
   CATMAID FAFB skeleton ids (GRN R4#1–17 / R5#1–16 labellar taste bristle
   neurons, Engert2022) + 1 McKellar_Gr64f (no FAFB skid).
2. Per-skeleton downstream partners via the CATMAID pass-through
   `POST /catmaid/fafb/connectivity` (new helper `catmaid_conn.py`, same
   politeness as vfb.py: disk cache, ≥2.5s spacing, backoff). The command
   was found in the instance's dynamic command registry
   (`GET /catmaid/fafb` → `commands`); it is POST-only.
3. Synapse counts summed per partner skeleton across instances, partners
   mapped to neuron names (`neuron_names`), then to FBbt classes (VFB
   search), aggregated by class.
4. Hop 2 via the standard class-level walk (build_graphs.pick_downstream).

**Yield:** 23/33 skeletons queried successfully (10 skeletons' responses
persistently truncated server-side — IncompleteRead on every retry:
7179579, 7349219, 7349285, 7432034, 7451040, 7456677, 7468835, 7471728,
7471829, 7789606; their data is missing from the sums, noted not hidden).
6,486 partner rows aggregated. Top partner classes by summed synapses:
- adult zorro subesophageal neuron FBbt_00052223 — 332
- adult clavicle subesophageal neuron FBbt_00051867 — 270
- adult FMIn subesophageal neuron FBbt_00051880 — 240
- adult fuchs subesophageal neuron FBbt_00052227 — 227
- G2N-1 (adult gustatory second-order neuron type 1) FBbt_00051850 — 181
- adult billiards subesophageal neuron FBbt_00052228 — 141
- (also: dandelion 138, fudog 115, specter 109, quasimodo 78, usnea 74,
  rattle 70, phantom 52; plus lateral GRN→GRN links, same class as hop 0,
  skipped per the no-self-loop convention)

**Result:** `subgraphs/sugar_forward.json` — 10 nodes, 18 edges. Hop 0→1
edges are instance-aggregated CATMAID FAFB rows (documented in the file's
`source` field); hop 1→2 edges are class-aggregated FlyWire v783 rows
(Zorro/Clavicle/FMIn/G2N-1 → SEZ neuron FBbt_00001972, gnathal ganglion
neuron FBbt_00052032, adult descending neuron FBbt_00047511). Fuchs and
Billiards have no class-level downstream (0 rows) — honest hop-1
terminals. The forward walk converges on the SAME terminal classes as the
independent motor-backward trace (sugar_backward.json) — forward and
backward meet, which cross-validates both. Builder:
`build_sugar_forward.py`. The old 1-node `sugar.json`
stub is kept as-is for provenance; `sense.py` still routes taste/sugar/
sweet to it (rewiring to sugar_forward.json is a product decision, not
made here).

**Honest limits of this resolution:**
- 11/33 skeletons unqueried (server-side truncation, not our choice).
- Partner→class mapping is via neuron name search; the named SEZ
  interneurons (Zorro, Clavicle, …) are paper-level (Shiu et al 2022)
  tracings with clean FBbt classes, but the mapping step is documented
  method, not API ground truth.
- Fuchs and Dandelion have no class-level downstream (0 rows) — they sit
  as honest hop-1 terminals. G2N-1's class downstream resolved on retry
  (transient 0-row earlier).

---

## 1. SUGAR — sweet-sensing GRN downstream connectivity is not indexed
Hop-0 class: FBbt_00049614 "sweet-sensing gustatory receptor neuron"
(synonym: sugar-sensing neuron). The class resolves in the API (33 instances
found), but **zero downstream connections** are returned.

Attempts made (all against https://v3-cached.virtualflybrain.org/, no login):
1. `/query_connectivity?upstream_type=FBbt_00049614&group_by_class=true` → 0 rows
2. `/run_query` DownstreamClassConnectivity for FBbt_00049614 → HTTP 500:
   "No partner classes resolved for FBbt_00049614 although its instances
   have downstream connectivity"
3. `/query_connectivity?upstream_type=FBbt_00049614&weight=3` (per-pair) → 0 rows
4. `/query_connectivity?upstream_type=FBbt_00049614` (per-pair, no weight) → 0 rows
5. CATMAID `annotations_query_targets` name="sugar" → 0 entities
6. CATMAID `annotations_query_targets` annotated_with="gustatory" → HTTP 500
7. `/query_connectivity` for generic class FBbt_00005927 "gustatory receptor
   neuron" → response (~1.1 MB) repeatedly truncated the connection
   (IncompleteRead); not pursued further to avoid hammering the service
8. Upstream-walk probe: UpstreamClassConnectivity of SEZ interneuron class
   FBbt_00004037, grepping for gustatory upstream classes → FAILED after 4
   retries (remote closed connection without response; named upstream queries
   are server-side heavy and this one never completed)
9. (related) The generic GRN class FBbt_00005927 query also never completed
   (response ~1.1 MB, connection truncated on every attempt)

10. Motor-backward trace: UpstreamClassConnectivity of proboscis MN mn1
    (FBbt_00051181) → WORKS (40 rows). Top specific upstream: adult
    descending neuron (tw 377), **subesophageal zone neuron (tw 370)**,
    gnathal ganglion neuron (310), DN gnathal ganglion (266), CB0859 (227).
11. Upstream of SEZ neuron class FBbt_00001972 → WORKS (40 rows) but top
    upstream are broad classes; NO gustatory/sweet/sugar class appears.
    The GRN→SEZ link is confirmed absent from the index in both directions.

Result: `sugar.json` contains the hop-0 sensory node with **no outgoing
edges** (forward walk). Separately, `sugar_backward.json` contains a REAL
motor-backward chain (7 nodes, 17 edges): SEZ / gnathal / descending
pre-motor neurons → proboscis MN mn1, plus one further upstream layer.
The simulator injects at hop -1 (pre-motor) via `--inject-hop -1` and the
proboscis MN fires strongly. The sweet-GRN → SEZ sensory link remains the
single missing piece — documented here, not invented. The textbook pathway
(sweet GRNs → SEZ interneurons → proboscis motor neurons → proboscis
extension) is stated in the graphs' `behavior` fields as *known biology*,
NOT as simulated wiring.

## 1b. LOOMING — giant fiber below the top-k cutoff (not a gap, a method note)
The LPLC2 → giant fiber neuron edge is REAL and API-verified
(/query_connectivity upstream_type=LPLC2 downstream_type="giant fiber
neuron": 275 pairs, total_weight=5680, avg 20.7 synapses/pair, 48% of
LPLC2s connected; class FBbt_00004020). It ranks 48th by total weight, so
the strict top-k walk does not include it. The walk instead follows
LPLC2 → descending-neuron classes (also real, stronger by total weight),
which is the genuine parallel escape pathway. No edge was invented;
the GF edge is recorded here for Phase-2 anchor use.

## 2. Generic-superclass filtering (documented heuristic, not a data gap)
`/query_connectivity … group_by_class=true` returns ontology superclasses
("adult neuron", "interneuron", "cholinergic neuron", …) that aggregate tens
of thousands of weak pairs. The walk skips a documented blocklist of these
(see GENERIC in build_graphs.py) and follows the strongest *specific* classes
instead. The skipped edges are real; branching into them would drown the
circuit in generic buckets. This is a selection choice, logged per-hop in
build.log.

## 3. Simplified dynamics (not a data gap, but a modeling choice)
flysim.py uses normalized spread-of-activation with a firing threshold — a
simplified dynamics model, NOT a biophysical one. It ignores
inhibition/excitation signs, neurotransmitters, timing, and recurrence. It
answers "which named populations light up, in what order" — nothing more.
But this is real, working infrastructure: real measured wiring in, coherent
body-state out. Agents run on it. The FLY: narration line is a labeled
narrative gloss, not a claim about experience.

## 4. Build-time API reliability notes (method, not data)
- `/query_connectivity … group_by_class=true` is fast (~6s) for specific
  classes but its response stream TRUNCATES for broad classes
  (IncompleteRead), e.g. FBbt_00111763 by id, FBbt_00005927 (generic GRN).
  Fallback chain used: id → label → named DownstreamClassConnectivity via
  `/run_query` (slow ~60–120s, but reliable). All fallbacks logged in
  build.log with per-hop candidate lists.
- A few very broad classes never resolved in any form and are logged as GAPs
  (e.g. "optic lobe wide-field columnar neuron" as an upstream).
- `vfb.py` caches every response on disk (`cache/`) and spaces queries ≥2.5s
  apart with exponential-backoff retries, to stay polite to the free service.
- Dataset versions (checked 2026-10-14 via `/list_connectome_datasets`):
  FlyWire is still served at **v783** — no newer FlyWire index exists, so
  all subgraphs stay on v783. (BANC v888 is also served but is a different
  connectome — whole brain + nerve cord — not a newer FlyWire; not used,
  to keep every subgraph on one consistent index.)
- NEW: `catmaid_conn.py` adds a polite POST helper for the CATMAID
  pass-through (`/catmaid/fafb/<command>`), same politeness contract as
  vfb.py. The `connectivity` command is POST-only and its responses
  truncate server-side above ~30KB — query one skeleton per call.

## 5. What was approximated (nothing invented)
- Node granularity is CELL CLASS (FBbt id), not individual neurons; edge
  weight = summed synapse count across the class (total_weight from the API).
- The walk follows top-k by total_weight per hop (k=6/5 at hop 1, k=3 at
  hop 2); generic ontology superclasses are skipped via a documented
  blocklist (GENERIC in build_graphs.py). See build.log for every candidate
  considered.
- `behavior` text in each JSON is textbook biology for the identified
  circuit, labeled as known biology with its basis — NOT a simulation result.
- `fly_narration` is a one-line narrative gloss, labeled as such.
- flysim.py dynamics (normalized spread, threshold 0.15) are a simplified
  model, not biophysics. Normalization is over the subgraph's edges, so activations are
  relative within the subgraph, not absolute probabilities.

## 6. TOUCH QUALITIES — only Johnston's organ is indexed (2026-10-14)
For differentiated touch qualities, every mechanosensory class EXCEPT
Johnston's organ returned ZERO downstream rows in every query form tried
(all against https://v3-cached.virtualflybrain.org/, no login):

  0-row classes (grouped by id, grouped by label, and per-pair where tried):
  - bristle mechanosensory neuron FBbt_00048508 (general) + subclasses
    leg bristle FBbt_00048084, wing bristle FBbt_00048273, taste bristle
  - campaniform sensillum neuron FBbt_00048057 + leg/wing primaries
    FBbt_00048058, FBbt_00048279
  - neck chordotonal organ neuron FBbt_00053163, medial/lateral neck
    chordotonal FBbt_00053171/70, femoral/leg chordotonal organ neuron,
    Johnston organ neuron a1 (subtype)
  - aristal neuron, leg mechanosensory neuron, proprioceptive neuron,
    stretch receptor neuron
  - general "mechanosensory neuron": response truncates (IncompleteRead,
    class too broad) — same failure mode as other generic classes.

Result: `touch_brush.json` and `touch_pressure.json` are honest 1-node
stubs (same pattern as `sugar.json`); their cascades honestly die at hop 0
and the session loop reports "no firing recorded" rather than borrowing
another class's wiring. `touch_vibration.json` is a REAL Johnston's-organ
walk (rebuilt under the quality name). The quality map in sense.py
(TOUCH_QUALITY_GRAPH) routes each touch quality to its own class's file,
so the REAL layer differentiates where the database allows it, and is
honestly silent where it doesn't. Re-running build_touch_qualities.py
will fill the stubs in automatically if the API ever indexes those
classes.

### 6b. Instance-level attack on §6 classes — attempted 2026-10-14, BLOCKED
Tried the same instance-level method that resolved §1 (sugar):
1. `ListAllAvailableImages` WORKS for these classes: FBbt_00048508
   (bristle) → 4,931 instances; FBbt_00048057 (campaniform) → 1,797
   instances.
2. **Blocker:** every instance is Neuprint male-cns (body ids like
   872719710) — there are NO CATMAID FAFB tracings for bristle or
   campaniform neurons. `annotations_query_targets` (name="bristle" /
   "campaniform", types=["neuron"]) → 0 entities on the FAFB instance.
3. VFBquery offers NO per-instance Neuprint path: docs.json contains no
   neuprint pass-through (unlike the CATMAID one), and
   `/query_connectivity?upstream_type=<male-cns body id>` → 0 rows
   (upstream_type only accepts labels/synonyms/FBbt ids).
4. Class-level per-pair queries with weight threshold also fail
   server-side for both classes (stream dies after retries).

Conclusion: the §6 gaps stand — not for lack of data existing (the
male-cns instances have connectivity in Neuprint), but because no
VFBquery endpoint exposes per-instance Neuprint connectivity and the
class aggregation is broken for these classes exactly as for sugar.
A future attack would need the Neuprint API directly (requires auth
token; out of scope here). Nothing was faked; the stubs remain honest.

## 7. PAIN — no nociceptive class indexed with usable connectivity (2026-10-14)
Searched for an adult nociceptive class to wire as the SENSORIUM pain channel.
All against https://v3-cached.virtualflybrain.org/, no login:

1. VFB search "nociceptive neuron" → FBbt_00048471 (generic), FBbt_00051492
   "adult nociceptive projection neuron" (= adult nociceptive second-order
   neuron), FBbt_00051304, plus larval classes (out of scope — we want adult).
2. `/query_connectivity?upstream_type=FBbt_00051492&group_by_class=true`
   (id and label forms) → 0 rows.
3. `/run_query` DownstreamClassConnectivity for FBbt_00051492 → 0 rows
   (no error this time — genuinely empty).
4. Instance enumeration (ListAllAvailableImages): FBbt_00051492 → 0
   instances; FBbt_00048471 → 30 instances but ZERO with CATMAID FAFB
   skeleton ids (image-only, no tracings to query).
5. CATMAID `annotations_query_targets` name="nociceptive" → 0 entities;
   name="ppk" → 0 entities; annotated_with="nociceptive" → HTTP 500.
6. FBbt_00051304 instance query → IncompleteRead (broad-class truncation).

Result: the instance-level attack that solved the sugar gap cannot run here
— there are no skeletons to query. The API simply does not index adult
nociceptive connectivity in any reachable form.

Resolution: SENSORIUM's pain channel runs on the looming escape circuit
(looming.json) as a DOCUMENTED functional proxy — a noxious stimulus driving
the escape pathway is the real biology of that circuit. sensorium.py reports
pain_channel_proxy=True and the source file; nothing is presented as
nociceptive wiring. If a real pain.json ever lands, the channel picks it up
automatically (constructor takes pain_graph=).

## 7b. PAIN — RESOLVED via motor-backward attack (2026-10-14)
Cory: "solve the pain part yourself — we will have our own method." The method:
instead of hunting nociceptive classes downstream (all dead, §7), query UPSTREAM
of the giant fiber escape neuron (FBbt_00004020) — the neuron that MUST receive
noxious input for the fly to flinch.

Avenue 1 (upstream of GF) — WORKED. `/run_query` UpstreamClassConnectivity of
FBbt_00004020 returned real mechanosensory classes upstream: adult chordotonal
neuron, adult mechanosensory neuron, Johnston organ neuron, adult antennal
sensory neuron, auditory sensory neuron (tw 1125–2532). The identical tw=2428
across several classes = ontology-ancestor duplication of one underlying
synapse set (documented, not double-counted).

Avenue 3 (pair verification) — WORKED. Per-pair `/query_connectivity`
(upstream_type=<class>, downstream_type="giant fiber neuron") resolved the
TRUE leaf classes, all Johnston's organ subtypes -> giant fiber:
- zone B Johnston organ neuron type 1 [FBbt_00049548]: 679 synapses
- zone A Johnston organ neuron [FBbt_00100008]: 80 synapses
- zone B Johnston organ neuron [FBbt_00100009]: 61 synapses
- Johnston organ neuron CA [FBbt_00049968]: 10 synapses
Total 830 measured synapses. Pair rows carry named neurons + FlyWire
accessions (e.g. AMMC.110 -> PVLP.44, 7 synapses). GF downstream (motor end):
adult VNC neuron (1097), prothoracic neuron (585), mesothoracic neuron (471).

Avenue 4 (BANC) — datasets listed (BANC888, fw783, Neuprint hemibrain/male-cns/
MANC/optic-lobe, CATMAID FAFB/L1); not needed, Avenue 1 already yielded real
FlyWire rows. Avenue 2 (upstream of descending neurons) — not needed.
Avenue 5 (direct CATMAID) — not needed.

Result: `subgraphs/pain.json` (8 nodes, 7 edges) — the REAL noxious-
mechanosensory -> giant-fiber escape pathway. Presented honestly as the
fly's functional pain-equivalent circuit (a sharp mechanical insult driving
antennal JO mechanoreceptors -> the giant fiber startle neuron -> thoracic
escape motor), NOT as labeled nociceptive neurons — adult nociceptive-labeled
classes remain unindexed. Cascade verified: JO subtypes -> GF (fires) ->
VNC/prothoracic/mesothoracic. SENSORIUM's pain channel auto-upgraded
(pain_is_proxy=False on load).

## RESOLVED — 2026-10-14: DH44 hunger neurons + IPC satiety cells (true interoceptive drive)

**Gap closed:** the actual hunger/satiety drive wiring — DH44 neurons
(FBbt_00047132 "DH44 neuron of pars intercerebralis") and adult
insulin-producing cells (FBbt_00110107). Unlike the GRN gaps, BOTH
classes had class-level downstream connectivity — no instance-level
attack needed. (IPC's grouped query truncates like other broad classes;
the named DownstreamClassConnectivity fallback worked.)

**Method:** standard walk with one documented addition. Both classes'
top weight tier is an ontology-duplicated synapse set (DH44: tw=252
across 11 ancestor labels; IPC: tw=206 across 14) — one underlying
connectivity counted under many labels. Taking top-k blindly would fill
hop 1 with arbitrary ancestors, so hop 1 takes the most specific member
of the duplicated tier (ring gland projection = the hormonal output)
plus the following weight-ranked specific classes. Builder:
`build_dh44.py`. A second documented heuristic: larval classes
("larval neuron" etc. — real rows, wrong life stage) are excluded from
these adult walks, same spirit as the GENERIC blocklist; the one case
hit (ipc gut-innervating hop-2) is logged in build.log.

**Yield — DH44 hop 1 (FBbt_00047132):**
- adult ring gland projection neuron FBbt_00059246 — 252 (hormonal output)
- gut-innervating neuron FBbt_00052149 — 235 (gut-brain axis; DH44
  regulates gut motility in the literature)
- subesophageal zone neuron FBbt_00001972 — 72
- gnathal ganglion neuron FBbt_00052032 — 58
- adult Ms cell of pars intercerebralis FBbt_00058024 — 17 (PI cross-talk)
- serotonergic neuron FBbt_00005133 — 13 (modulatory)

**Yield — IPC hop 1 (FBbt_00110107):**
- adult ring gland projection neuron FBbt_00059246 — 206
- gut-innervating neuron FBbt_00052149 — 206
- subesophageal zone neuron FBbt_00001972 — 7
- adult CB0991 neuron FBbt_20004678 — 7
- adult DM2 lineage neuron FBbt_00050123 — 4
- DPMpm1 lineage neuron FBbt_00052205 — 4

**The convergence result (the prize):** DH44, IPCs, AND the sweet/water/
bitter taste circuits all drive the SAME node class — subesophageal
zone neuron FBbt_00001972 — which fans out to the same motor populations
(VNC/thoracic/secondary/descending). Hunger, satiety, and taste meet on
shared wiring. The Hunger module can now be re-grounded from the
sweet-taste proxy (sugar_forward.json) to true interoception
(dh44.json). Verified: `subgraphs/dh44.json` (18 nodes, 21 edges),
`subgraphs/ipc.json` (19 nodes, 23 edges); cascades fire (DH44 1.00 →
ring gland 0.39 / gut 0.36; IPC 1.00 → ring gland 0.47 / gut 0.47 →
SEZ 0.27).

**Honest notes:** the tw=252/206 tiers are duplicated ancestor labels
(documented above, not double-counted as independent findings);
gut-innervating's DH44 hop-2 walk failed all query forms (honest hop-1
terminal, logged); IPC hop-2 via named fallback; dh44 hop-2 dies below
the toy threshold at step 2 for some branches (threshold cliff,
documented toy behavior — hop-1 drive signal is intact).

## RESOLVED — 2026-10-14: HOT thermosensory chain (aristal VP2 hot cells)

**Gap closed:** hot-temperature downstream connectivity. Hot and cold are
separate senses with separate wiring: the cold chain (Ir21a VP1l,
FBbt_00111336) was already bottled in subgraphs/temperature.json. This
resolves the hot chain.

**Method:** VFB search found FBbt_00007575 "aristal sensory neuron VP2"
(the hot cell / warm thermoreceptor cells in the arista, TRN_VP2). Class-level
grouped /query_connectivity died server-side (same failure mode as Ir21a);
named DownstreamClassConnectivity worked (40 rows). Standard top-k walk:
hop 1 top-5 specific (GENERIC blocklist skipped), hop 2 top-3 each
(grouped queries for hop-1 nodes failed and fell back to named queries —
logged in build output). Builder: build_temperature_hot.py.

**Yield — hot chain:** aristal sensory neuron VP2 (hot cell) ->
antennal lobe projection neuron (0.22), adult antennal lobe projection
neuron (0.22), adult ALl1 lineage neuron (0.19), BAlc lineage neuron (0.19),
adult lateral horn input neuron (0.18) -> adult central brain intrinsic
neuron (0.41), adult lateral horn neuron, mushroom body intrinsic neuron,
aminergic neuron, Kenyon cell. 10 nodes, 20 edges. Cascade verified live.

**File layout decision:** temperature.json keeps the COLD chain (it is what
sensorium.py already loads as the "temperature" modality); the HOT chain
lives in subgraphs/temperature_hot.json. Each file's honest_note names the
other. A future sensorium rewire can split them into hot/cold modalities.

**Honest note:** hot and cold converge on the same downstream territory
(posterior antennal lobe -> lateral horn / mushroom body), which matches
textbook thermosensation; the hop-1 picks are broad projection classes
rather than named second-order thermosensory neurons. All edges are real
API rows; selection heuristic documented in build_graphs.py.

## RESOLVED — 2026-10-14: MATING DRIVE (P1 courtship command) wiring

**Gap closed:** the male courtship command circuit — P1's downstream
connectivity. No dead avenues at all on this one.

**Method:** VFB search "male P1 neuron" → FBbt_00110621 "adult fruitless
P1 (male) neuron" (synonyms: fru-P, fru-P1, adult male fruitless pMP-e /
pMP4 neuron). Class-level grouped /query_connectivity returned 568 REAL
rows on the FIRST try — no instance-level attack, no motor-backward, no
BANC needed. Hop-2: every hop-1 node's grouped query failed server-side
and fell back to the named DownstreamClassConnectivity query (the
documented playbook path); all named queries worked except doublesex
pC1 (male), which returned 0 rows — honest hop-1 terminal, logged.
Builder: build_mating.py.

**Yield — P1 hop 1 by total synapse weight** (duplicated ancestor/child
tiers represented by most specific member; two high-weight ontology
superclasses skipped as generic parent buckets — 'fruitless expressing
neuron' tw=51702, 'sexually-dimorphic neuron' tw=25724 — same spirit as
the GENERIC blocklist):
- adult brain doublesex neuron FBbt_00053229 — 17786
- adult SMPad1 (male) lineage neuron FBbt_00050245 — 15897
- adult fruitless aSP-a (male) neuron FBbt_00110595 — 15897
- adult DM4 lineage neuron FBbt_00050254 — 11373
- adult doublesex pC1 (male) neuron FBbt_00047348 — 11033
- adult descending neuron FBbt_00047511 — 8215

Hop 2 reaches: VNC/thoracic/secondary/abdominal motor populations (via
doublesex brain and descending neurons — the motor end of courtship),
central complex neurons (via DM4 — courtship steering), and fru/aSP
recurrent classes. pIP10 (FBbt_00110854) IS a real P1 downstream partner
(tw=1444, verified from the data, not assumed) but ranks below the
top-k cutoff — same pattern as the giant fiber in the looming walk.

**Result:** `subgraphs/mating.json` — 17 nodes, 18 edges. Cascade
verified: P1 1.00 → doublesex brain (0.22) / SMPad1 (0.20) / aSP-a
(0.20); hop-2 dies below the toy's 0.15 threshold after per-source
normalization (documented toy behavior — the edges are real API rows,
the cascade readout is the honest dilution).

**pC1 note:** the doublesex pC1 (male) neuron — the courtship integration
center — landed cleanly at hop 1 (tw=11033), so no separate query was
needed. Its own downstream is unindexed (0 rows all forms) — an honest
terminal, not a missing step we faked.

**CIRCUIT vs DRIVE (the honest framing):** every edge here is REAL
measured wiring of P1's downstream command chain. The DRIVE DYNAMICS —
how P1 activity ramps, persists, and satiates; how it arbitrates against
hunger and thirst — are the genuinely unmapped frontier. No API holds
them; this graph models none of them. A future mating-drive bottle will
have to build those dynamics as MODELED, the way Hunger's wanting math
is modeled on real wiring.

## RESOLVED — 2026-10-14: COMPASS (E-PG heading-direction) wiring

**Gap closed:** the fly's internal GPS — E-PG ring neurons' downstream
connectivity. Zero dead avenues on the core target.

**Method:** VFB search "E-PG neuron" → FBbt_00047030 "E-PG neuron (adult
ellipsoid body-protocerebral bridge 1 glomerulus-dorsal/ventral gall
neuron)". Class-level grouped /query_connectivity TRUNCATED server-side
(IncompleteRead, 4 retries — same failure mode as the thermo classes);
the named DownstreamClassConnectivity fallback returned 50 real rows
(documented playbook path). No instance-level attack, no motor-backward,
no BANC needed. Builder: build_compass.py.

**Yield — E-PG hop 1 by total synapse weight** (duplicated ancestor/child
tiers represented by most specific member; generic ontology buckets
skipped — neuron/adult neuron/CNS/interneuron/input-output/transmitter
classes, 'adult central complex neuron' tw=194278 as parent bucket,
'supraesophageal ganglion neuron'; E-PG->E-PG tw=14614 skipped per the
no-self-loop convention — REAL recurrence, recorded not hidden):
- small field neuron of the central complex FBbt_00007514 — 99914
- large field neuron of the central complex FBbt_00007515 — 91386
- intrinsic neuron of the central complex FBbt_00053387 — 70552
- adult ellipsoid body ring neuron FBbt_00003649 — 54362
- adult ellipsoid body extrinsic ring neuron FBbt_00003654 — 36116
- adult PBp1 lineage neuron FBbt_00050171 — 31578

**Hop 2:** top-3 specific per hop-1 node via pick_downstream (grouped
first, named fallback — every hop-1 node's grouped query failed and
fell back except 'adult ellipsoid body extrinsic ring neuron', which
resolved via the label form). One honest hop-1 terminal: 'adult
ellipsoid body ring neuron' failed ALL query forms (grouped id, grouped
label, named) — sits as a hop-1 terminal, logged in build.log.

**Result:** `subgraphs/compass.json` — 9 nodes, 18 edges. Cascade
verified: E-PG 1.00 → small field (0.26) / large field (0.24) /
intrinsic (0.18) → adult central complex neuron (0.19).

**Real below-cutoff partners (same pattern as pIP10 / giant fiber):**
Delta7 'adult intrinsic protocerebral bridge 18 glomeruli-delta7
neuron' tw=30232 (the ring's global inhibition), PEN 'adult
protocerebral bridge 1 glomerulus-ellipsoid body tile-nodulus 1
neuron' tw=26851, 'adult ellipsoid body R-neuron' tw=18246 (R-neurons,
the ring's recurrent feedback), PFN 'adult protocerebral bridge 1
glomerulus-fan-shaped body-nodulus neuron' tw=12306, PFL 'adult
protocerebral bridge 1 glomerulus-fan-shaped body-lateral accessory
lobe neuron' tw=12066. All real rows, recorded in compass.json's
honest_note, not graphed. P-FN/P-EN were NOT separately hunted per
spec — they showed up in the walk (PFN/PEN/PFL above), which satisfies
the "secondary if cheap" clause.

**Honest notes:** hop-2 contains some ontology-duplication noise
('adult central complex neuron' as a parent-bucket node; 'small field
neuron' alongside 'small field neuron of the central complex' — the
duplicated tier); documented, not hidden — same treatment as the
DH44/mating tiers. Hop-2 fires weakly (0.19) and dies at step 3 —
documented toy dilution, edges are real API rows.

**CIRCUIT VS DYNAMICS (the honest framing):** every edge is REAL
measured wiring of E-PG's downstream chain. The RING-ATTRACTOR DYNAMICS
— how the activity bump moves, holds, and updates heading — are the
genuinely unmapped frontier; no API holds them and this graph models
none of them.

## RESOLVED — 2026-10-14: SLEEP (dFB homeostat) wiring

**Gap closed:** the dorsal fan-shaped body sleep-homeostat downstream
connectivity. VFB search found FBbt_00049537 "adult dorsal fan-shaped
body tangential neuron" (the dFB sleep neurons).

**Method:** class-level grouped /query_connectivity DIED server-side
(IncompleteRead, ~1.4MB response truncated after 4 retries — dFB is a
broad class). The named DownstreamClassConnectivity fallback returned 50
real rows (limit=50). Hop-1 = top-6 most-specific classes (307745 down
to 70267), skipping ontology parents, transmitter buckets
(dopaminergic/aminergic/cholinergic tiers), and self (FBbt_00049537
tw=135378) per the documented heuristic; duplicated tiers represented
by the most specific member. Hop-2 = top-3 per node via the standard
fallback chain (grouped failed for all 6 hop-1 nodes, named worked for
all 6). Builder: build_sleep.py.

**Yield — dFB hop 1 by total synapse weight:**
- small field neuron of the central complex FBbt_00007514 — 307745
- fan-shaped body columnar neuron FBbt_00049820 — 307486
- adult fan-shaped body delta neuron FBbt_00003636 — 217252
- adult fan-shaped body horizontal delta neuron FBbt_00007523 — 176242
- fan-shaped body extrinsic columnar neuron FBbt_00049822 — 90232
  (the FB output channel)
- adult fan-shaped body layer 6 tangential neuron FBbt_00007536 — 70267

**Result:** `subgraphs/sleep.json` — 8 nodes, 20 edges. Hop-2 folds
back into the central complex (recurrent edges into hop-1 classes plus
the broad bucket "adult central complex neuron" FBbt_00049819) — the
circuit is recurrent within the CX, which is what a homeostat should
look like. One hop-2 pick ("small field neuron" FBbt_00003633) was the
ontology parent of a hop-1 node; its edges were redirected to the
specific child rather than adding the parent (documented in builder).
Cascade verified: dFB 1.00 → small-field-of-CX (0.26) / FB columnar
(0.26) / delta (0.19) / horizontal delta (0.15) → CX bucket (0.49) +
recurrent small-field (0.31).

**CIRCUIT VS HOMEOSTAT (the honest framing):** every edge is REAL
measured wiring of dFB's downstream command chain within the central
complex. The HOMEOSTAT DYNAMICS — pressure accumulation rate,
discharge kinetics, arousal gating — are the genuinely unmapped
frontier; no API holds them, and this graph models none of them. A
future sleep-drive bottle will build those as MODELED, the way
Hunger's wanting math is modeled on real wiring.

## RESOLVED — 2026-10-14: PHEROMONE (Or47b courtship smell) forward walk

**Gap closed:** pheromone-sensing ORN downstream connectivity. Or47b =
FBbt_00067056 "adult olfactory receptor neuron Or47b" (male courtship
pheromone receptor, VA1v glomerulus). Class-level grouped
/query_connectivity truncates server-side in every form (label, id —
IncompleteRead); the named DownstreamClassConnectivity query returned
50 real rows (392 Or47b neurons, 260 connected). Standard top-k walk:
hop 1 top-6 (most specific member per ontology-duplicated tier), hop 2
top-3 each via the fetch_rows fallback chain (grouped -> named).
Builder: build_pheromone.py.

**Yield — Or47b hop 1 by total synapse weight:**
- adult antennal lobe projection neuron FBbt_00067123 — 15332
- adult antennal lobe projection neuron to lateral horn FBbt_00053398
  — 13811 (most specific of the PN->LH tier)
- fruitless expressing neuron FBbt_00016687 — 13133 (broad but kept
  deliberately: the pheromone -> courtship-system bridge)
- adult antennal lobe local neuron FBbt_00007390 — 6500
- adult central brain intrinsic neuron FBbt_00059245 — 6500
- BAlc lineage neuron FBbt_00100660 — 3839

Hop 2 reaches lateral horn neurons, mushroom body intrinsic neurons,
VNC/thoracic/secondary motor populations, and ALl1/Notch-OFF lineage
classes. Adult central brain intrinsic neuron failed ALL query forms
(honest hop-1 terminal, logged).

**CONVERGENCE WITH MATING (the prize):** this chain MEETS the P1 chain
(mating.json) at FBbt_00016687 "fruitless expressing neuron" — Or47b
feeds it (tw=13133) and P1's fruitless aSP-a feeds it (tw=63139). The
pheromone sense and the mating drive share a node: courtship smell
enters the fru courtship system here, upstream of P1's command chain.

**Dead avenues (documented, not hidden):**
- Or88a (FBbt_00067057, VA1d glomerulus ORN): grouped (label + id),
  named DownstreamClassConnectivity, instance enumeration
  (ListAllAvailableImages), and CATMAID annotation search (0 entities)
  ALL fail server-side (IncompleteRead / connection closed). The class
  index entry appears poisoned; nothing reachable exposes its
  connectivity.
- ppk23/ppk29 gustatory pheromone neurons: no adult FBbt neuron class
  exists — VFB search returns only the gene and L1EM larval instances
  labeled "gustatory pheromone neuron".

**Result:** `subgraphs/pheromone.json` — 15 nodes, 21 edges. Cascade
verified: Or47b 1.00 -> AL projection neuron (0.26) / AL PN->lateral
horn (0.23) / fruitless expressing neuron (0.22) -> central brain
intrinsic (0.22). Hop-1 local/central-brain/BAlc branches dilute below
the toy's 0.15 threshold (documented toy behavior — edges are real).

## RESOLVED — 2026-10-14: CO2-ALARM forward walk via class-level queries

**Gap closed:** CO2-sensing ORN downstream connectivity — the fly's
dedicated danger smell. The class FBbt_00067064 "adult olfactory
receptor neuron Gr21a/63a" (ab1C, Gr21a+Gr63a co-expressing) HAS indexed
class-level downstream: grouped `/query_connectivity` via the FBbt ID
died server-side (RuntimeError, 2 attempts); the LABEL form returned
126 real rows (105 specific candidates after the GENERIC blocklist) —
same failure mode as the temperature-hot class. No instance-level
attack, no motor-backward, no BANC needed.

**Hop-1 dedup (documented, not hidden):** the grouped rows carry
duplicated ancestor/child tiers of identical synapse sets; following the
mating-walk precedent each tier is represented by its most specific
member — projection tier tw=15822 (07422/49427/67123) -> 53398 "adult
antennal lobe projection neuron to lateral horn"; lineage tier tw=15248
(50025) -> 00100660 "BAlc lineage neuron"; local tier tw=13155
(51493/52874) -> 07390 "adult antennal lobe local neuron"; Notch ON tier
tw=12220 (49539) -> 49912 "BAlc Notch ON hemilineage neuron"; l2LN tier
tw=11032 (07394) -> 51501 "adult antennal lobe local neuron l2LN".
59245 "adult central brain intrinsic neuron" (tw=13155) is a distinct
class. Full mapping in build_co2.py docstring.

**Yield — hop-1 picks by total synapse weight:**
- adult antennal lobe projection neuron to lateral horn FBbt_00053398 — 15822
- BAlc lineage neuron FBbt_00100660 — 15248
- adult antennal lobe local neuron FBbt_00007390 — 13155
- adult central brain intrinsic neuron FBbt_00059245 — 13155
- BAlc Notch ON hemilineage neuron FBbt_00049912 — 12220
- adult antennal lobe local neuron l2LN FBbt_00051501 — 11032

**Hop-2 notes:** standard top-3 walk with larval exclusion; grouped
queries failed server-side for 49912 (named DownstreamClassConnectivity
fallback worked, 40 rows); 51501's grouped query returned 1364 rows
(1242 specific) on the first try. Hop-2 reaches lateral-horn and
mushroom-body territory plus recurrent AL local circuitry.

**Result:** `subgraphs/co2.json` — 15 nodes, 24 edges. Cascade verified:
CO2 ORN 1.00 → AL projection neuron to lateral horn 0.20 / BAlc 0.19 /
AL local 0.16. Builder: `build_co2.py`. Sibling circuit: rotten.json
(Or56a aversion) shares the AL->lateral-horn architecture from a
different glomerular origin.

**Dead avenues:** grouped query via FBbt ID (server-side death, logged);
nothing else died — class-level sufficed throughout.

## HONEST-FAIL — 2026-10-14: FAT TASTE (IR56d) — no indexed connectivity in any form

**Target:** fatty-acid-sensing GRNs — the sixth taste (Tauber et al 2017).
Classes found via VFB search:
- FBbt_00048013 "adult ionotropic receptor neuron Ir56d" (general class)
- FBbt_00048015 "adult Ir56d neuron of labellar taste bristle"
- FBbt_00048014 "E409 neuron (adult Ir56d neuron of labellar taste peg)"

**Every avenue tried (all against https://v3-cached.virtualflybrain.org/, no login):**
1. Class-level grouped /query_connectivity (FBbt id form) → 0 rows, all three classes (resolved classes, genuinely empty — not truncation)
2. Class-level grouped (label form "adult ionotropic receptor neuron Ir56d") → 0 rows
3. Named DownstreamClassConnectivity via /run_query (the DH44/temperature-hot fallback) → 0 rows, all three (genuinely empty, not failed)
4. Instance enumeration (ListAllAvailableImages) → 0 instances, all three — NO skeletons exist anywhere, so the sugar/water instance-level attack cannot run
5. CATMAID FAFB annotations_query_targets name="Ir56d" → 0 entities; name="E409" → 0 entities; annotated_with="Ir56d" → connection closed server-side (same mode as nociceptive)
6. Per-dataset isolation via exclude_dbs (fw-only, BANC-only, hemibrain-only, male-cns-only) → 0 rows each — no dataset holds it
7. Motor-backward: UpstreamClassConnectivity of SEZ neuron FBbt_00001972 (the sweet/water/bitter/DH44/IPC convergence node) → 50 rows, ALL generic ontology buckets (neuron, cholinergic, GABAergic…), zero Ir56d/fat classes
8. Per-pair probe upstream_type=FBbt_00048013 downstream_type="subesophageal zone neuron" → 0 rows
9. VFB search for other fat classes ("fatty acid sensory neuron", "fat taste neuron", "lipid sensing neuron") → genes only, no neuron classes; E409 hits are GAL4 driver lines, not neurons

**Diagnostic (why this gap is Ir56d-specific):** the general "labellar taste peg
chemosensory neuron" FBbt_00048028 returns 174 downstream rows — peg GRNs ARE
indexed in general. Sibling classes Ir94e (FBbt_00052186) and high-salt
(FBbt_00052561) also return 0 rows, so several recently-described GRN classes
share the gap. Using the general peg class for fat.json would be dishonest
(not fat-specific) — not done.

**Result:** `subgraphs/fat.json` is an honest 1-node stub (same pattern as
touch_brush.json/touch_pressure.json): hop-0 IR56d node, no edges, honest_note
documents the gap. The cascade honestly dies at hop 0. Re-run if the API ever
indexes these classes.

**Cory's rule honored:** "nothing is dead" — this is shelved, not buried. The
stub auto-fills if the index ever lands.

## RESOLVED-VIA-LITERATURE-HYPOTHESIS — 2026-10-14: FAT TASTE (IR56d) convergent circuit

**Status:** NOT API-resolved (the HONEST-FAIL above stands — zero Ir56d rows in
any query form). This is a literature-grounded, testable HYPOTHESIS circuit,
built because Cory asked "can you solve it? if so we add to the literature."

**Literature surveyed:**
1. Tauber et al. 2017, PLOS Genet 13:e1007059 (CC-BY): IR56d neurons are a
   SUBSET of sweet-sensing (Gr64f-overlapping) GRNs, necessary and sufficient
   for medium-chain fatty-acid PER. Two projection populations: posterior SEZ
   (labellar bristles, OVERLAPPING the sweet-sensing region) and anterior SEZ
   (taste pegs, E409). Explicitly: "higher order neurons responsive to FA taste
   have not been identified."
2. Brown et al. 2021, eLife 67878: IR56dGAL4 required for 6C-8C FA Ca2+
   responses in the posterior (bristle) projections.
3. "Connectomic analysis of taste circuits in Drosophila," Sci Rep 2025
   (s41598-025-89088-9): whole-brain 2N/3N taste architecture for
   sugar/water/bitter/IR94e — does NOT cover IR56d.
4. Chen & Dahanukar 2020 review: E409-GAL4 labels taste-peg GRNs (Fischler et
   al. 2007); Ir56d/Ir25a/Ir76b required for carbonated-water sensing in pegs.
   No named peg downstream neurons anywhere in the surveyed literature.

**The bridge (the hypothesis):** the bristle IR56d population (FBbt_00048015)
ARE sweet-sensing GRNs projecting to the same posterior SEZ region as sweet
GRNs (Tauber). The named second-order SEZ interneurons that sweet GRNs drive
(zorro, clavicle, FMIn, fuchs, G2N-1, billiards — REAL FlyWire rows in
sugar_forward.json, Shiu et al. 2022 series) are therefore the
literature-grounded candidate downstream of IR56d.

**Deliverable:** `subgraphs/fat_lit.json` — 10 nodes, 18 edges. EVERY edge
carries "provenance": 6× "LITERATURE-HYPOTHESIS" (Ir56d->interneuron, uniform
placeholder weight 1, with citation + per-edge note) and 12× "REAL"
(interneuron->SEZ/gnathal/descending, API rows copied verbatim from
sugar_forward.json). Cascade verified: IR56d 1.00 -> 6 interneurons (0.17
each) -> SEZ terminals. Builder: `build_fat_lit.py`.

**What this is:** a testable prediction for future connectomic verification
(confirm/refute Ir56d->zorro etc. synapses), honestly labeled at the edge
level. It is NOT measured wiring and must never be presented as such.

**Remaining gap (unmapped in BOTH literature and API):** the taste-peg E409
IR56d population (FBbt_00048014, anterior SEZ projections) — no named
downstream in any surveyed paper, zero API rows. That half of fat taste is
still dark.

## RESOLVED — 2026-10-14: SALT-TASTE (low attractive + high aversive) opponent chains

**Gap closed:** salt-sensing GRN downstream connectivity — and salt splits
into TWO opponent chains, bottled in one graph.

**Low salt (attractive):** FBbt_00100043 "low salt-sensing neuron of
labellar taste bristle" (L1 GRN, the classical salt neuron). Class-level
grouped /query_connectivity returned 0 rows in ID and label forms (the
sugar/water failure mode); the named DownstreamClassConnectivity fallback
returned 43 real rows. Standard top-k walk on the specific classes.

**High salt (aversive):** FBbt_00052561 "cation-sensing gustatory receptor
neuron of labellum" (type D GRN). EVERYTHING died: grouped ID 0 rows,
grouped label 0 rows, named 0 rows; ListAllAvailableImages returns 0
instances (no FAFB skeletons — instance-level attack impossible); sibling
class FBbt_00058229 (DL, L-type sensillum) 0 rows in every form.

**High-salt subtraction method (documented, not hidden):** the parent
class FBbt_00049615 "salt-sensing neuron" HAS indexed connectivity (named
query, 50 real rows), aggregating its indexed subclasses. The low-salt
child is fully resolved, so the parent's rows NOT explained by the
low-salt chain are the high-salt siblings' signal: parent minus low-salt
leaves the tw=93 tier (adult VNC / adult ascending / prothoracic /
thoracic / adult ANXXX433 neurons), adult usnea subesophageal neuron
(tw=17), and descending neuron of the gnathal ganglion DNg103 (tw=15).
Each tier is represented by its most specific member (mating-walk
precedent): ANXXX433 FBbt_20008184, ascending FBbt_00048301, prothoracic
FBbt_00001984, usnea FBbt_00051956, DNg103 FBbt_20007474. The hop-0 node
is the TRUE high-salt class FBbt_00052561; its edges are the
subtraction-derived real rows. All underlying rows are real API rows;
the attribution to high-salt is the documented method, not a measured
label.

**Yield — low-salt hop 1:** adult SEZ output neuron (132), adult gustatory
projection neuron (126), SEZ neuron FBbt_00001972 (100 — the convergence
node again), SLP gustatory projection neuron 1 (52), gnathal ganglion
neuron (29). **High-salt hop 1:** ANXXX433 (93), ascending (93),
prothoracic (93), usnea (17), DNg103 (15).

**Result:** `subgraphs/salt.json` — 26 nodes, 40 edges, both chains in
one graph (chain field on nodes/edges). Cascade verified: low-salt 1.00 →
SEZ output (0.30) / GPN (0.29) / SEZ (0.23); high-salt 1.00 →
ANXXX433/ascending/prothoracic (0.30) → VNC (0.43) / thoracic (0.29) /
secondary (0.22). Builder: `build_salt.py`.

**Opponent organization (biological sanity):** low-salt feeds
SEZ/gustatory-projection feeding circuitry (attraction → approach/
feeding); high-salt feeds VNC/ascending/prothoracic motor + descending
(aversion → withdrawal). Textbook-plausible.

**Build incident (honest):** the first build_salt.py run died silently
after 7 of 10 hop-2 nodes (no traceback captured — the background
session was reaped). All completed queries were disk-cached, so the
re-run replayed them and finished the remaining 3 nodes. salt.json was
only written by the completed run; no partial file was ever published.

**Dead avenues (documented, not hidden):** all direct query forms for
FBbt_00052561 (grouped ID/label, named); instance enumeration (0
instances); sibling FBbt_00058229 in every form. FBbt_00100044
(high salt/bitter-sensing) has connectivity but is the bitter-neuron
class (synonym: "bitter neuron") — its chain overlaps bitter.json, not
the type-D high-salt chain.

## RESOLVED-VIA-OWN-METHOD — 2026-10-14: FAT TASTE, TASTE-PEG (E409) HALF — peg-class walk + anatomical narrowing

**Gap attacked:** the E409/Ir56d taste-peg population (FBbt_00048014) — dark in
BOTH literature (no named downstream anywhere) and API (0 rows/0 instances in
all 9 first-pass avenues). Own method: Ir56d peg neurons are an unmarked
SUBSET of the general taste-peg GRN class (FBbt_00048028), which HAS indexed
downstream. Walk the general class, then narrow by Tauber et al. 2017's
anatomical constraint (peg projections -> ANTERIOR SEZ; prow = anterior SEZ
neuropil).

**Method:** named DownstreamClassConnectivity for FBbt_00048028 (grouped query
returned only 5 rows; named returned 100-row cap). Hop 1 = top-6 by weight +
hyacinth as documented 7th (49 synapses below cutoff, strongest anterior-arbor
claim). Hop 2 = top-3 per hop-1 node (grouped where it worked, named fallback
otherwise). VFB term descriptions checked for all hop-1 candidates
(Sterne et al. 2021; Schlegel et al. 2024; Dorkenwald et al. 2024).
Builder: `build_fat_peg.py`.

**Yield — peg GRN hop 1 by synapse weight:**
- subesophageal zone neuron FBbt_00001972 — 3545 (the shared convergence node)
- gnathal ganglion neuron FBbt_00052032 — 2926
- adult CB0011 neuron FBbt_20003871 — 1534 [ANTERIOR: prow postsynapses]
- adult rattle subesophageal neuron FBbt_00051932 — 636 (sugar-linked: receives
  sugar-GRN input per Shiu et al. 2022; gnathal arborization)
- adult CB0137 neuron FBbt_20003973 — 616 (gnathal postsynapses)
- adult CB3720 neuron FBbt_20007145 — 486 [ANTERIOR: prow postsynapses]
- adult hyacinth subesophageal neuron FBbt_00051898 — 437 [ANTERIOR, strongest:
  dendritic+axonal arborization in prow AND flange, bilateral]

Hop 2: rattle/CB0137 feed back into SEZ1972+gnathal+descending; hyacinth ->
SEZ1972 (2567, API returned the class twice tw 2567/1775 — deduped to max) +
TRdm lineage; CB3720 -> TRdm + SEZ1972 + gnathal; CB0011 hop-2 is bucket-heavy
(system-level classes, documented same as bitter); SEZ1972/gnathal ->
VNC/thoracic/secondary motor (960507/846534/668777 — identical motor pops as
the sweet/water/bitter walks).

**Result:** `subgraphs/fat_peg.json` — 18 nodes, 27 edges, every edge REAL.
Cascade verified: peg 1.00 -> SEZ node 0.35 -> VNC motor 0.25.

**Anterior-candidate verdict:** CB0011, CB3720, hyacinth form the Ir56d-peg
candidate pool — flagged LITERATURE-CONSTRAINT (Tauber 2017 + prow
arborization), NOT measured Ir56d wiring.

**Sweet-overlap verdict:** zorro/clavicle/FMIn/fuchs/G2N-1/billiards do NOT
appear in the peg top-k — the peg pool is a DIFFERENT interneuron set than
the bristle sweet set. The fat_lit hypothesis is therefore NOT extended to
the peg half by overlap. BUT: rattle is sugar-linked (Shiu 2022), and both
pools converge on SEZ FBbt_00001972 -> identical motor populations. The peg
half's story is "different interneurons, same SEZ node, same motor end."

**What remains unresolvable:** Ir56d-peg-SUBSET attribution. No API marker
distinguishes Ir56d peg GRNs from other peg GRNs — the candidate pool is a
constrained hypothesis, and the file's honest_note states this outright.

## RESOLVED — 2026-10-14: MOTION VISION (T4/T5 direction-selective pathway)

**Gap closed:** T4/T5 motion-detector downstream connectivity — the optic-lobe
motion pathway. VFB search found T4 = FBbt_00003731 "T4 neuron" (ON-edge
detector) and T5 = FBbt_00003736 "T5 neuron" (OFF-edge detector).

**Method:** class-level walk, two hop-0 nodes, union of top-6 unique each.
T4's grouped queries (id and label forms) died server-side after retries —
the named DownstreamClassConnectivity fallback returned 40 real rows
(documented playbook path). T5's grouped label query returned 915 rows
(232 unique specific candidates after GENERIC filtering). Builder:
build_motion.py.

**Two honest method fixes during the build (documented, not hidden):**
1. Duplicate-row dedup: T5's grouped response lists "adult visual
   neuropil intrinsic neuron" as 5 separate rows, eating 4 of the 6
   top-k slots. The builder requests 12, dedupes by class keeping max
   weight, then takes top-6 unique. Without this, T5's real partners
   (giant neuron, wide-field columnar, translobula plate) would have been
   silently dropped.
2. Pre-edge preservation: T4 and T5 both synapse onto the shared hop-1
   classes; the first draft kept only the stronger edge. The final graph
   keeps every real pre-edge (12 hop-0->1 edges).

**Yield — hop 1 (textbook pathway landed on real rows):**
- T4 -> lobula plate tangential neuron FBbt_00003907 (LPTC) — 282,410
- T5 -> lobula plate tangential neuron FBbt_00003907 (LPTC) — 529,105
- T4 -> lobula plate intrinsic neuron FBbt_00003910 — 471,436
- T5 -> lobula plate intrinsic neuron FBbt_00003910 — 835,144
- T4 -> lobula plate giant neuron FBbt_00003906 — 181,003
- T5 -> lobula plate giant neuron FBbt_00003906 — 366,422
- T4/T5 -> adult visual neuropil intrinsic neuron FBbt_00059247 —
  1,281,507 / 1,775,618 (broadest target; honest hop-1 terminal, 0
  downstream rows in all forms)
- T4 -> secondary neuron FBbt_00047096 — 261,305 (failed ALL query forms
  downstream — honest hop-1 terminal)
- T4/T5 -> optic lobe wide-field columnar neuron FBbt_00110137 —
  245,773 / 285,363
- T5 -> translobula plate neuron FBbt_00003890 — 254,081

Hop 2 reaches secondary/columnar/narrow-field classes and T neuron
(giant neuron -> T neuron tw=24,883). LPTC's own downstream: visual
neuropil intrinsic (230,834), wide-field columnar (65,416), secondary
(60,227), lobula plate intrinsic (48,690) — the wide-field tangential
system talking back to columnar channels.

**Result:** `subgraphs/motion.json` — 11 nodes, 27 edges. Cascade
verified: T4/T5 1.00 -> visual neuropil intrinsic (0.91) / LP intrinsic
(0.38) / LPTC (0.23) / wide-field columnar (0.16) / LP giant (0.16) ->
hop-2 (0.56). The classic T4/T5 -> LPTC motion pathway is real wiring,
not a textbook diagram.

**Honest notes:** hop-2 fires weakly and the narrow-field/T branches
dilute below the toy's threshold (documented toy dilution — edges are
real API rows). No BANC, no instance-level attack, no motor-backward
needed. LPTCs as a separate upstream attack (the spec's fallback) was
not needed — they landed at hop 1 directly.

## RESOLVED — 2026-10-14: COLOR-VISION forward walk (hop-0 + hop-1; hop-2 deferred to API degradation)

**Gap closed:** R7/R8 chromatic photoreceptor downstream connectivity — actual
sight, not the looming alarm. R7 = FBbt_00004225 "photoreceptor cell R7",
R8 = FBbt_00004227 "photoreceptor cell R8", run as parallel hop-0 sources
(hot/cold temperature precedent). Class-level grouped /query_connectivity
died server-side for BOTH classes via ID form AND label form (same failure
mode as CO2, temperature-hot, mating hop-2); the named
DownstreamClassConnectivity fallback worked for both (R7: 40 rows /
18 specific; R8: 566 rows / 445 specific). No instance-level attack,
no motor-backward, no BANC needed.

**THE COLOR PATH IS REAL:** R7 -> Dm8 (FBbt_00013774 "distal medullary
amacrine neuron Dm8", tw=38836) plus Dm8a (19865), Dm8b (18537), Dm9
(15733) — the textbook chromatic-opponency circuit, present in the measured
rows, not assumed.

**Hop-1 (12 nodes, weights = total synapse count, R7 / R8):**
- adult visual neuropil intrinsic neuron FBbt_00059247 — 91690 / 235944
- secondary neuron FBbt_00047096 — 73349 / 202161
- medulla intrinsic neuron FBbt_00053385 — 71918 / 169659
- Notch OFF hemilineage secondary neuron FBbt_00049542 — 66607 / 156700
- optic lobe amacrine neuron FBbt_00005127 — 66169 / 89291
- distal medullary amacrine neuron FBbt_00003767 — 66110 / 89291
- distal medullary amacrine neuron Dm8 FBbt_00013774 — 38836 / —
- distal medullary amacrine neuron Dm8a FBbt_00053638 — 19865 / —
- distal medullary amacrine neuron Dm8b FBbt_00053639 — 18537 / —
- distal medullary amacrine neuron Dm9 FBbt_00111271 — 15733 / —
- optic lobe narrow field columnar neuron FBbt_00110136 — — / 131323
- aminergic neuron FBbt_00007368 — — / 82066

**Dedup decisions (documented, not hidden):**
- R8's named rows split into subtype rows (yellow/pale/dorsal-margin R8);
  only the main-class aggregate row is used per downstream class (e.g.
  59247: 235944, not 88452/75270/12407) — summing would double-count
  against the class aggregate. R7's rows had no subtype split.
- 49542/49540 duplicated ancestor/child tier -> most specific (49542).

**Dead / deferred avenues (documented, not hidden):**
- Dm8's own downstream: ALL query forms failed (grouped x2, named x1) —
  honest hop-1 terminal.
- Hop-2 walk: ABANDONED mid-build — the VFB API degraded (even cheap
  /get_term_info fails after 4 retries); the three broadest hop-1 classes
  (59247, 47096, 53385) are unqueryable downstream (grouped label returns
  0 rows; grouped ID and named hang through all retries). A hop-2 pass can
  be re-run when the API recovers; the hop-0->hop-1 graph stands on its own.
- BANC not needed (FlyWire v783 yielded everything).

**Result:** `subgraphs/color.json` — 14 nodes, 18 edges. Cascade verified:
R7+R8 1.00 -> visual neuropil intrinsic (0.38) / secondary (0.31) /
medulla intrinsic (0.28). Builder: `build_color.py` (hop-2 section kept,
skips the three unqueryable broad classes; re-runnable).


### HOP-2 RETRY 2026-10-15 (API recovered) — appended, history above untouched
Retried the 8 hop-1 nodes that had no hop-2 edges (3 broad classes +
Dm8 downstream + 4 first-pass GAPs), full fallback chain each.
Result: 7 of 8 stay terminal. The 3 broad classes (59247, 47096, 53385)
still fail grouped in all forms; 59247/47096 also fail named — honest
hop-1 terminals, confirmed twice. Dm8's own downstream fails ALL forms
again (grouped x2, named x1, now a third full pass) — confirmed terminal.
The 4 first-pass GAPs (05127, 03767, 53639/Dm8b, 00110136) resolve in
grouped or named, but their top specific downstream are all classes
already in the graph (59247, 47096, 53385, 49542, 05127, 03767) —
the visual circuit is recurrent within this set, so no new nodes.
ONE landing: medulla intrinsic neuron 53385 -> optic lobe wide-field
columnar neuron FBbt_00110137 (tw=3428708, named query) — new hop-2 node.
File: 21 nodes/42 edges -> 22 nodes/43 edges. Cascade re-verified.
Retry script: retry_color_hop2.py (kept re-runnable).

## RESOLVED — 2026-10-14: CLOCK (LNv circadian pacemaker) output wiring

**Gap closed:** the fly's circadian clock output — LNv pacemaker neurons'
downstream connectivity. Hop-0: FBbt_00004046 "LNv neuron" (lateral
neurons ventral, the PDF pigment-dispersing-factor pacemaker cells).
Class-level grouped /query_connectivity returned 657 rows on the first
try — no fallback needed at hop 0.

**Subclass note (documented, not hidden):** the specific subclasses
s-LNv Pdf neuron (FBbt_00003764) returned 0 rows in every form
(grouped id/label, named — genuinely empty, not truncated), and l-LNv
(FBbt_00003763) failed in EVERY form (grouped id, grouped label, named
DownstreamClassConnectivity — all server-side RuntimeError/
IncompleteRead deaths, not empty). The general LNv class is where the
indexed connectivity lives, so the walk uses it.

**Hop-1 selection (documented):** raw rows carry per-dataset duplicates;
weights deduped (summed) per FBbt id → 232 specific candidates. Paired
identical-weight classes (pacemaker/adult pacemaker 3307/3307,
SLPpl1/DPLl1 3294/3294) treated as duplicated tiers of one synapse set
— most specific member kept, same spirit as the mating/CO2 walks.
'secondary neuron' and Notch hemilineage tiers skipped as non-specific;
self skipped per no-self-loop. Top-6:
- adult pacemaker neuron FBbt_00100163 — 3307 (clock-to-clock)
- adult SLPpl1 lineage neuron FBbt_00050230 — 3294 (SLP output)
- adult visual neuropil intrinsic neuron FBbt_00059247 — 2804
- accessory medulla neuron FBbt_00053404 — 2559 (clock hub)
- adult DN period neuron FBbt_00003628 — 1907 (dorsal clock neurons)
- adult LHd2 lineage neuron FBbt_00050117 — 1838

**Hop-2:** top-3 specific per node (larval excluded). adult pacemaker →
pacemaker/DN period/DN3/SLPpl1 (clock-to-clock recurrence, real
biology); adult SLPpl1 → worked via named fallback; adult DN period →
pacemaker (14055), DN3, DN1 (4116), lateral horn (4965); adult LHd2 →
lateral horn (28831), LH output, MB extrinsic. Two honest hop-1
terminals: adult visual neuropil intrinsic neuron (0 rows all forms)
and accessory medulla neuron (all forms failed server-side) — logged,
not faked. Builder: build_clock.py.

**Result:** `subgraphs/clock.json` — 12 nodes, 18 edges. Cascade
verified: LNv 1.00 → adult pacemaker (0.21) / SLPpl1 (0.21) / visual
neuropil (0.18) / accessory medulla (0.16).

**CIRCUIT VS OSCILLATOR (the honest framing):** every edge is REAL
measured wiring of the LNv output chain. The OSCILLATOR DYNAMICS — the
24h molecular clock, PDF cycling, phase — are the genuinely unmapped
frontier; no API holds them, and this graph models none of them.

## HONEST-FAIL — 2026-10-14: COURTSHIP-SONG relay classes unindexed in every dataset
Searched for the auditory song pathway (JO -> AMMC -> pC1 -> P1). Every
VFBquery-reachable avenue died — all against
https://v3-cached.virtualflybrain.org/, no login:

1. Class-level downstream (grouped): intrinsic AMMC neuron FBbt_00111352
   -> 0 rows; AMMC-B1 FBbt_00110120 -> 0 rows (id AND label forms);
   AVLP_pr01 FBbt_00052102 -> 0 rows; vPN1 FBbt_00111295 -> 0 rows;
   JO-B label form -> 0 rows; JO-A/JO-B grouped id forms die server-side
   (broad-class truncation).
2. Named DownstreamClassConnectivity: AMMC-B1 -> server-side death
   (RuntimeError after retries); JO-B -> client timeout (>110s).
3. Instance-level CATMAID attack: ListAllAvailableImages for AMMC-B1 ->
   60 instances, 5 with FAFB skeletons (AMMC-B1-1..5, skids 3278280,
   3760675, 3760679, 3760683, 3750066) — but the tracings are ~empty:
   48 partner skeletons / 75 total synapses across all 5, mostly
   "Placeholder Neuron" and unannotated entries. No usable downstream.
4. Motor-backward (UpstreamClassConnectivity): pC1-male FBbt_00047348 ->
   0 rows; P1 FBbt_00110621 -> 0 rows; pC1-general FBbt_00053230 ->
   50 rows ALL generic ontology buckets; AMMC-intrinsic -> 0 rows;
   vPN1 -> 0 rows.
5. Per-pair probes (pain-avenu-3 style): AMMC-B1->pC1 (male+general),
   AVLP_pr01->pC1, AMMC-VLP2->pC1, vPN1->pC1male, JO-B->AMMC-B1,
   JO-B->AMMC-intrinsic -> ALL 0 pairs.
6. BANC v888 (exclude_dbs scoping): AMMC-B1 -> 0 rows.

Result: `subgraphs/song.json` is an honest 1-node stub (AMMC-B1 hop-0,
no edges), same pattern as fat.json / touch-quality stubs. The song
relay is the second sense (after fat taste) that no reachable dataset
indexes. Builder: `build_song.py`.

## RESOLVED-VIA-LITERATURE-HYPOTHESIS — 2026-10-14: COURTSHIP-SONG chain
**Gap worked around (not closed):** the API holds none of the song-relay
links, but the circuit is among the best-described in the literature —
so a convergent hypothesis graph was built, every edge labeled
LITERATURE-HYPOTHESIS with its citation, none presented as an API row
(fat_lit precedent).

**Chain (paraphrased claims, per-edge citations in the JSON):**
- JO-B -> AMMC-B1: JO subgroup-B neurons are the primary auditory input;
  AMMC-B1 are the major secondary auditory neurons; JO-B->AMMC-B1 is the
  first step of IPI processing (Ishikawa et al., Sci Rep 2023,
  s41598-022-27349-7; Kamikouchi lab).
- AMMC-B1 -> vPN1: second-order aPN1 -> third-order vPN1 (male-specific,
  fru+); aPN1-vPN1 synaptic connection confirmed by GRASP (Zhou et al.
  2015, eLife 4:e08477). VFB synonym check: AMMC-B1 IS aPN1a,b — same
  FBbt ID (FBbt_00110120), same population, found during this solve.
- vPN1 -> pC1: vPN1 axons overlap dsx+ pC1 arbors in the LPC region;
  vPN1 activation drives pC1 calcium responses; both manipulations
  induce/block song-evoked male chaining (Zhou et al. 2015). Authors'
  own caveat included: GRASP barely detectable, monosynapticity NOT
  proven.
- vPN1 itself resolved to a real FBbt class during this solve:
  FBbt_00111295 "vPN1 (ventrolateral protocerebrum projection neuron 1)".

**Result:** `subgraphs/song_lit.json` — 4 nodes, 3 edges, all
LITERATURE-HYPOTHESIS (uniform placeholder weight 1). Cascade verified:
JO-B 1.00 -> AMMC-B1 -> vPN1 -> pC1 (1.00 at step 3).

**MEETING POINT WITH MATING (the prize):** pC1 (FBbt_00047348) is hop-1
in mating.json — P1->pC1 tw=11033 are REAL API rows. The song chain
feeds INTO pC1; pC1's own downstream is unindexed (0 rows all forms —
honest terminal), so no pC1->P1 edge is drawn. The fly hears its mate's
song through pC1, the same node its mating drive passes through.

## RESOLVED — 2026-10-14: AGGRESSION (aIPg fight circuit) wiring

**Gap closed:** male fru+ aggression command circuit — aIPg downstream
connectivity. VFB search found FBbt_00110593 "aIPg (adult fruitless aIP-g
(male) neuron)". Class-level grouped /query_connectivity via FBbt ID died
server-side (IncompleteRead, broad-class truncation — same failure mode as
dFB/thermo); the LABEL form returned 586 real rows (561 specific
candidates) on the first try. No instance-level attack, no motor-backward,
no BANC needed. Hop-2: all 6 hop-1 nodes' grouped queries failed and fell
back to the named DownstreamClassConnectivity query (documented playbook
path); all 6 worked. Builder: build_aggression.py.

**Hop-1 selection (documented, not hidden):** the walk skips
"Notch OFF hemilineage neuron" (tw=3434) and "Notch ON hemilineage neuron"
(tw=2024) as generic developmental buckets, and "fruitless expressing
neuron" (tw=2054) as the fru parent bucket — same spirit as the GENERIC
blocklist. Top-6 specific picks:
- adult SMPpv2 lineage neuron FBbt_00050114 — 2282
- CP1 lineage neuron FBbt_00100706 — 2282
- adult VLPl2 lineage neuron FBbt_00050227 — 2258
- BLAv2 lineage neuron FBbt_00100711 — 2258
- adult superior medial protocerebrum neuron 054 FBbt_20002916 — 2202
- adult posterior ventrolateral protocerebrum neuron 016 FBbt_20002074 — 2182

Hop-2 reaches the motor end: adult VNC neuron, thoracic neuron, adult
descending neuron (via SMPpv2 — tw 79625/57013/51378), plus SEZ
(FBbt_00001972) and gnathal convergence.

**CONVERGENCE WITH MATING (the prize):** the aggression chain MEETS the
P1 mating chain at FBbt_00016687 "fruitless expressing neuron" — aIPg
feeds it (tw=2054) and P1's fruitless aSP-a feeds it (tw=63139,
mating.json). The fru+ fight and fru+ courtship systems share this node —
the same node where the pheromone chain also converges. Recorded in
aggression.json's honest_note, not graphed (parent bucket, per the
mating-walk convention).

**Dead avenues (documented, not hidden):**
- aSPg: no FBbt class found ("aSPg neuron" / "fight neuron" searches
  return nothing) — the secondary target doesn't exist in the ontology.
- CL062 (FBbt_20000767, adult clamp neuron 062 / AIP male wing aggression
  neuron) exists as a related aggression class but was not walked —
  wing-threat specific, noted not hidden.
- Grouped ID-form query for the hop-0 class (server-side truncation);
  grouped queries for all hop-1 nodes (named fallback covered all).

**Result:** `subgraphs/aggression.json` — 14 nodes, 24 edges. Cascade
verified: aIPg 1.00 → SMPpv2/CP1/VLPl2/BLAv2 (0.17 each) at hop 1.

**CIRCUIT VS DRIVE (the honest framing):** every edge is REAL measured
wiring of aIPg's downstream command chain. The AGGRESSION-DRIVE DYNAMICS
— how aggressive arousal ramps, persists, and arbitrates against
mating/hunger — are the genuinely unmapped frontier; no API holds them,
and this graph models none of them.

## RESOLVED — 2026-10-14: PUNISHMENT (PPL1 aversive dopamine) wiring

**Gap closed:** PPL1 cluster dopaminergic neurons' downstream connectivity — the
dark twin of the PAM reward circuit (reward.json).

**Method:** VFB search found the general class FBbt_00100219 "dopaminergic
PPL1 neuron" plus compartment-specific subclasses. The general class fails
server-side in every query form (grouped id + label, named); "dopaminergic
PPL1 neuron 2" fails; MB-SV (FBbt_00110323) returns 0 rows. Two canonical
aversive PPL1 DANs ARE indexed, so hop-0 is a documented merge (pheromone
precedent):
- PPL1-gamma1pedc FBbt_00100243 (aka PPL101/MB-MP1): ID-form grouped query,
  162 rows (label form returns 0 rows)
- PPL1-alpha3 FBbt_00110320 ("MB-alpha neuron of the dopaminergic PPL1
  cluster"): label-form grouped query, 114 rows
Standard top-k walk: hop 1 top-5 each, hop 2 top-3 each (named fallback where
grouped died). Builder: build_punishment.py.

**Yield — hop 1 (merged):** mushroom body intrinsic neuron (4189), mushroom
body extrinsic neuron (4091), aminergic/dopaminergic tiers (~3985), mushroom
body dopaminergic neuron (3952), mushroom body output neuron (3726) from
gamma1pedc; MBONs (1344), MB extrinsic (1344), MBON 14 (1325), SEZ neuron
FBbt_00001972 (1325), gnathal (1325) from alpha3. Hop 2 reaches descending/
VNC/thoracic motor populations and recurrent MB circuitry.

**Result:** `subgraphs/punishment.json` — 14 nodes, 25 edges. Cascade
verified: PPL1 1.00 → MB extrinsic (0.40) / secondary (0.22) / MB intrinsic
(0.21).

**PAM/PPL1 OPPONENT ORGANIZATION (in honest_note):** the mushroom body is
tiled into compartments, each co-innervated by DANs and MBONs. PAM-cluster
DANs (reward.json) innervate appetitive compartments → approach learning;
PPL1-cluster DANs (this file) innervate aversive compartments → avoidance
learning. Same MB architecture, opponent valence — reward and punishment are
the two halves of one teaching signal.

**Dead avenues:** general FBbt_00100219 (all forms, server-side death);
"dopaminergic PPL1 neuron 2" (server-side death); MB-SV FBbt_00110323
(genuinely 0 rows); gamma1pedc label form (0 rows, ID form works).

## RESOLVED — 2026-10-14: PROPRIOCEPTION (FeCO leg chordotonal) forward walk

**Gap closed:** femoral chordotonal organ proprioceptive downstream
connectivity — the fly's sense of leg position/movement. Hop 0:
FBbt_00048051 "mechanosensory neuron of femoral chordotonal organ"
(FeCO neuron; VFB synonyms: "FeCO neuron", "FeCO").

**Method:** class-level grouped /query_connectivity truncates server-side
for this broad class (IncompleteRead ~800KB after 4 retries — same
failure mode as dFB/thermo classes); the named
DownstreamClassConnectivity fallback returned 50 real rows
(1313 FeCO neurons, 950 connected). Hop-1 = top-6 specific classes,
skipping ontology parents, transmitter buckets, and developmental
lineage/hemilineage groupings (documented heuristic, same spirit as the
GENERIC blocklist). Hop-2 = top-3 specific per hop-1 node via the
fetch_rows fallback chain (grouped failed for all 6 hop-1 nodes; named
worked for 4, "unpaired neuron" and "abdominal neuron" failed all forms
— honest hop-1 terminals). Builder: `build_proprioception.py`.

**Yield — FeCO hop 1 by synapse weight:**
- metathoracic neuron FBbt_00001986 — 81476
- mesothoracic neuron FBbt_00001985 — 75066
- adult ascending neuron FBbt_00048301 — 52445 (leg->brain pathway)
- prothoracic neuron FBbt_00001984 — 35516
- unpaired neuron FBbt_00052749 — 23788 (midline neurons, e.g.
  DUM/VUM-type; somas on the midline, symmetrical projections)
- abdominal neuron FBbt_00001987 — 20708

**Hop 2:** efferent neuron FBbt_00051963 (the motor output — the reflex
arc: proprioception -> thoracic interneurons -> motor neurons), plus
recurrent links among the segmental/ascending classes (meta<->meso<->
prothoracic<->ascending). The circuit reads as a segmental reflex arc
with an ascending leg-to-brain branch — textbook-plausible.

**Result:** `subgraphs/proprioception.json` — 8 nodes, 18 edges.
Cascade verified: FeCO 1.00 -> metathoracic (0.28) / mesothoracic
(0.26) / adult ascending (0.18).

**Build incident (honest):** the first build's SKIP strings
("Notch ON/OFF hemilineage neuron") did not match the actual row
labels ("... hemilineage secondary neuron"), so developmental buckets
slipped into hop-1 and hop-2 degraded into bucket-hopping — including
a biologically implausible top pick ("adult visual neuropil intrinsic
neuron", synapses restricted to the optic lobes per its term
description, as top downstream of a VNC hemilineage class at tw=5.7M
— almost certainly a class-aggregation artifact). Rebuilt with exact
strings; the artifact class is skipped with this documented reason.
No partial file was published (only the completed rebuild wrote
proprioception.json).

**Below-cutoff proprioceptive classes (same pattern as pIP10 / giant
fiber):** "proprioceptive system neuron" FBbt_00052132 (tw=9957) and
"proprioceptive sensory neuron" FBbt_00051439 (tw=9957) ARE real FeCO
downstream but rank below the top-6 cutoff — recorded here, not
graphed.

**Dead avenues (documented, not hidden):**
- FBbt_00048275 "femoral chordotonal club ascending neuron": 0 rows in
  named, grouped-ID, and grouped-label forms — the ascending FeCO
  subclass is unindexed as a connectivity class.
- UpstreamClassConnectivity of FBbt_00052033 "adult proprioceptive
  projection neuron" (= adult proprioceptive second-order neuron):
  0 rows — its inputs are unindexed.
- Per-pair FeCO -> FBbt_00052033: 0 pairs — the second-order
  proprioceptive neuron is NOT a direct FeCO target in the index.
- Per-pair FeCO -> "adult ascending neuron": ~2.7MB response,
  truncates server-side; the named grouped edge (tw=52445) stands.
- The functional club/claw/hook FeCO subtypes (Mamiya et al.: club =
  position, claw = movement direction, hook = vibration) are not
  separately indexed as connectivity classes (only claw/club/hook
  neuron CLASSES exist: FBbt_00049557/5556/5558 — unqueried here);
  this walk is at the whole-FeCO level.

## CONFIRMED-FAIL — 2026-10-14: LABELED NOCICEPTORS (adult) — literature own-method attack

**Target:** named adult postsynaptic partners of labeled nociceptive sensory
neurons (ppk1/painless/dTRPA1 afferents) — the labeled-nociceptor complement
to pain.json (the functional JO->giant-fiber circuit, §7b, which stands
regardless).

**Literature surveyed:**
1. Liu et al. 2023, Curr Biol 33(12):2397-2406.e6 (DOI
   10.1016/j.cub.2023.04.055, PMID 37201520) — Epi (Epione) neurons: a single
   descending neuron pair per hemisphere, AstC+, Painless+, DIRECT noxious-heat
   sensors that suppress thermal nociception via AstC. Downstream AstC-R1
   targets explicitly UNIDENTIFIED (authors' stated future work).
2. Neely et al. 2011, PLOS ONE 6(8):e24343 (DOI 10.1371/journal.pone.0024343,
   CC-BY) — adult thermal nociception requires painless+ nerves
   (antenna/proboscis) and TrpA1 in multidendritic sensory neurons. No named
   central second-order neurons.
3. Oikawa et al. 2023, eLife (DOI 10.7554/eLife.85760) — DSK descending
   inhibition of nociception via MP1/Sv -> Goro. LARVAL (reviewers confirm).
4. Larval circuit corpus (Basin/Goro/A05q/A08n/DnB/Wave — Ohyama, Jovanic,
   and the Frontiers in Pain Research 2023 review 10.3389/fpain.2023.1076017):
   fully circuit-mapped, but LARVAL — out of scope for the adult collection.

**API checks:** FBbt_00052624 "adult Epi descending neuron" EXISTS in the
ontology (VFB term info confirms the Liu 2023 description, incl. VNC-wide
arborization) but has 0 typed instances in any connectome dataset — "no
neurons from a connectome dataset are typed to it" — so no API connectivity
in any form. ppk1: gene only (FBgn0020258), no adult neuron class. painless:
no neuron class. FBbt_00051492/00048471: 0 rows, 0 instances (§7).

**Verdict:** CONFIRMED-FAIL. No paper names adult second-order nociceptive
neurons. The adult field works at the genetic/behavioral level; the
circuit-mapped work is all larval. This is a field-level gap, not a
method failure — documented, not hidden.

**Deliverable:** `subgraphs/nociceptor_lit.json` — honest 1-node stub (Epi
neuron, full VFB description, zero edges). Publishable as a negative result:
the adult nociceptive circuit is unmapped, and here is exactly what is known.

## RESOLVED — 2026-10-14 (pC1 retry): pC1 OUTPUT WIRING — THE LOOP CLOSES

**Gap closed:** pC1's own downstream. During the mating build, pC1
(FBbt_00047348 "adult doublesex pC1 (male) neuron") returned 0 rows in
all API forms — logged as an honest terminal. On retry (API recovered),
grouped /query_connectivity via FBbt ID returned **1,469 real rows**
(900 unique classes after dedup). The 0-row result was API degradation,
not absence.

**Method:** class-level grouped via FBbt ID — worked on retry, no
fallback needed. Standard top-k walk: hop-1 = top-6 specific +
**P1 as a deliberate 7th** (pheromone-walk precedent: kept deliberately
because it is the prize edge). Duplicated tiers by most specific member;
'sexually-dimorphic neuron' (47,894) skipped as parent bucket (mating
precedent). Hop-2 = top-3 per hop-1 node (grouped first, named fallback;
SMPad1 male: grouped failed + named 0 rows — honest hop-1 terminal).
Builder: build_pc1.py.

**Yield — pC1 hop 1:**
- fruitless expressing neuron FBbt_00016687 — 87,164 (kept deliberately:
  the triple-convergence node; pC1 feeds BACK into the fru system —
  recurrent within the fru courtship system)
- adult brain doublesex neuron FBbt_00053229 — 34,237
- adult SMPad1 (male) lineage neuron FBbt_00050245 — 26,553
- adult fruitless aSP-a (male) neuron FBbt_00110595 — 26,553
- adult DM4 lineage neuron FBbt_00050254 — 22,374
- adult descending neuron FBbt_00047511 — 14,529 (pC1's direct motor output)
- adult fruitless P1 (male) neuron FBbt_00110621 — 5,863 (DELIBERATE 7th)

**THE LOOP-CLOSER:** pC1->P1 (tw=5,863) is REAL measured wiring. The
courtship-song chain (song_lit.json: JO-B->AMMC-B1->vPN1->pC1) ends at
pC1, and pC1 drives P1 (mating.json) — courtship hearing feeds the
mating drive through measured synapses, closing the loop that was
literature-only on the song side. Also real: pC1->pIP10 (tw=1,796,
below-cutoff, recorded not graphed — same pattern as pIP10 in mating).
pC1's hop-2 reaches central-complex and descending/motor populations.

**Result:** `subgraphs/pc1.json` — 18 nodes, 25 edges, 0 dangling /
0 zero-weight edges. Cascade verified: pC1 1.00 -> fruitless expressing
(0.40) / brain doublesex (0.16).

**Honest framing:** every edge is REAL measured wiring of pC1's output
chain. How pC1 integrates song + pheromone + internal state into a
courtship decision is the unmapped frontier; no API holds it and this
graph models none of it.
## RESOLVED-VIA-OWN-METHOD — 2026-10-14: TOUCH QUALITIES (bristle + campaniform) literature + motor-backward attack

**Gap:** GAPS.md §6/§6b — bristle (FBbt_00048508) and campaniform
(FBbt_00048057) classes return 0 API rows downstream in every form and
have no CATMAID skeletons (Neuprint-only instances). The API route is
exhausted.

**CAMPANIFORM — RESOLVED with REAL rows (motor-backward):** instead of
querying campaniform downstream (broken), query UPSTREAM of the b1 wing
motor neuron (FBbt_00004066) via /run_query UpstreamClassConnectivity.
Result — real measured rows:
- FBbt_00048057 "sensory neuron of campaniform sensillum" -> b1, tw=3572
- FBbt_00048279 "sensory neuron of wing campaniform sensillum" -> b1, tw=1818
- FBbt_00048296 "sensory neuron of haltere campaniform sensillum" -> b1, tw=1754
(The tw=3572 tier is ontology-duplicated across "mechanosensory neuron"
etc. labels — one synapse set, represented by the most specific member,
not double-counted.) Independently CONFIRMED by Lesser, Moussa & Tuthill,
eLife 2026 (bioRxiv 2025.05.29.656810): "campaniform sensilla on the
tegula synapse directly onto the tonic wing b1 motor neuron" (FANC EM).

**BRISTLE — LITERATURE-HYPOTHESIS (no FBbt classes exist):** two papers
name adult bristle second-order neurons, both too new for the ontology:
- MGT ("Mago-no-Te", thoracic grooming command): posterior macrochaete
  bristle BMNs synapse onto MGT (t-GRASP + FANC/MANC EM) — Yoshikawa,
  Tang & Simpson, Curr Biol (bioRxiv 2023.11.19.567707; PMC10690200).
- CTN (central Tmc-L neurons): wing-margin bristle mechanoreceptors drive
  CTNs (ATP/P2X2 + GCaMP), bidirectionally controlling defensive behavior
  — Nat Commun 2020 s41467-020-17771-8.
Neither MGT nor CTN has an FBbt class; the API holds zero bristle rows in
any reachable form (class-level 0 rows, per-pair server death, upstream
of the adult mechanosensory projection neuron FBbt_00052607 dies
server-side on every attempt).

**Result:** `subgraphs/touch_qualities_lit.json` — 8 nodes, 6 edges:
3 REAL (campaniform -> b1) + 1 LITERATURE-CONFIRMED (same edge, independent
EM; not double-counted) + 2 LITERATURE-HYPOTHESIS (bristle -> MGT,
wing bristle -> CTN; placeholder weight 1, per-edge citations).
Cascade verified: campaniform hop-0 -> b1 fires at peak 3.00.
Builder: `build_touch_qualities_lit.py`.

**What remains:** bristle subset attribution is literature-only until MGT/
CTN enter the ontology or bristle classes gain indexed connectivity; the
touch_brush.json / touch_pressure.json stubs stay honest and can be
re-pointed when that happens.

## RESOLVED — 2026-10-14: EGG-LAYING DRIVE (oviDN) wiring

**Gap closed:** ovipositor descending neuron downstream connectivity — the
female egg-laying command circuit. Hop 0: FBbt_00049919 "oviposition
descending neuron oviDN" (the 12-instance aggregate class of
oviDNa/b/d/v/x; VFB search also finds oviDNa FBbt_00049920, oviDNb
FBbt_00049921, oviDNd FBbt_20003341, oviDNv FBbt_00053597, oviDNx
FBbt_00053277, oviDNb' FBbt_20002804).

**Method:** class-level walk. ID-form grouped /query_connectivity truncates
server-side (IncompleteRead — same failure mode as dFB/thermo classes);
the LABEL form returned 421 real rows (with exact-duplicate rows, deduped
by class keeping max weight — motion-build precedent). No instance-level
attack, no motor-backward, no BANC, no literature needed.

**Subtype dead avenues:** oviDNa label form dies server-side (4 retries);
oviDNb label form returns 29 rows, all weak (CB0584 tw=54, foxglove/SEZ/
gnathal tw=24, serotonergic tw=6) — the aggregate class carries the real
signal, per the most-informative-class convention.

**Yield — oviDN hop 1 (deduped, specific):**
- adult VNC neuron FBbt_00059289 — 1132
- abdominal neuron FBbt_00001987 — 1042
- secondary neuron FBbt_00047096 — 360 (honest hop-1 terminal, 0 rows)
- adult subesophageal zone output neuron FBbt_00049858 — 350
- adult ascending neuron FBbt_00048301 — 235
- adult INXXX052 neuron FBbt_20010849 — 209 (uncharacterized; hop-2 via
  named fallback: VNC 22079, abdominal 21896, efferent 9287, motor 6937)

**Hop 2:** thoracic (19M), mesothoracic, secondary (via VNC); efferent
neuron FBbt_00051963 (725868) + adult efferent + motor neuron (via
abdominal); lateral horn (via SEZ output). The motor end of the graph is
the abdominal/efferent command chain — the ovipositor muscle drive.

**Result:** `subgraphs/egglaying.json` — 11 nodes, 20 edges. Cascade
verified: oviDN 1.00 → VNC (0.34) / abdominal (0.31) → thoracic/efferent.
Builder: `build_egglaying.py`.

**Skips (documented, not hidden):** ontology/transmitter/Notch-hemilineage
developmental buckets (GENERIC + SKIP_IDS); optic-lobe-restricted classes
as downstream of SEZ-output/brain classes — the same class-aggregation
artifact family as the proprioception build (visual neuropil intrinsic
FBbt_00059247 skipped on its term description: synapses restricted to
optic lobes/ocellar ganglia; wide-field/narrow-field columnar, medulla
intrinsic/columnar, transmedullary skipped as optic-lobe-intrinsic by
definition). One build iteration was killed mid-walk by a service restart;
the rebuild from disk cache completed cleanly.

**CIRCUIT VS DRIVE (the honest framing):** every edge is REAL measured
wiring of oviDN's downstream command chain. The DRIVE DYNAMICS —
egg-load-dependent ramping, the temporal patterning of egg deposition —
are the genuinely unmapped frontier; no API holds them, and this graph
models none of them. Same honest split as mating/sleep/compass/clock/
aggression.

## RETRY SWEEP — 2026-10-15: systematic HONEST-FAIL re-probe against the recovered API

**Premise:** the pC1 build proved "0 rows in all forms" can mean API degradation,
not absence. Every shelved gap was re-probed in all three forms (grouped ID,
grouped label, named DownstreamClassConnectivity) before being declared dead.
Script: `/tmp/retry_sweep.py` (results: `/tmp/retry_sweep.json`).

**Per-target verdicts:**

1. **Ir56d fat-bristle (FBbt_00048013/48015/48014): STILL DEAD.** 0 rows in all
   three forms, all three classes (genuinely empty, fast responses — not
   truncation). The HONEST-FAIL (this file, 2026-10-14) stands; fat.json stays
   a 1-node stub; fat_lit.json remains the literature hypothesis.

2. **Song relay: JO-B (FBbt_00100009) + AMMC-B1 (FBbt_00110120) — LANDED.**
   JO-B: grouped ID dies server-side, grouped label 0, **named limit=200 returns
   200 rows including JO-B->AMMC-B1 (FBbt_00110120) tw=722 — REAL**. AMMC-B1:
   grouped 0/0, named limit=50 returns 50 rows (no vPN1); named limit=200 dies
   server-side (IncompleteRead, broad-class truncation). vPN1 (FBbt_00111295):
   **STILL DEAD** — 0 rows all three forms; per-pair vPN1->pC1 probe 0.
   **song_lit.json edge 0 (JO-B->AMMC-B1) converted LITERATURE-HYPOTHESIS -> REAL
   (tw=722).** Honest caveat recorded per-edge: the pairwise probe
   (upstream_type+downstream_type) returns 0 — a query-form discrepancy, not a
   biological contradiction (Ishikawa 2023 confirms the synapse). AMMC-B1->vPN1
   and vPN1->pC1 stay hypothesis. The song chain now OPENS with a real synapse
   set — the biggest single win of the sweep.

3. **Or88a (FBbt_00067057): HEALED.** Grouped ID form returns **129 real rows**
   (was: every form failed server-side — the "poisoned" index entry). **The
   pheromone graph is now two-ORN:** `subgraphs/pheromone.json` 15n/21e ->
   23n/31e. Or88a half: VA1d uniglomerular PNs (FBbt_00059283 tw=13,168;
   VA1d-adPN FBbt_00067357 tw=11,444 — VA1d is Or88a's glomerulus), MB-projecting
   PN (FBbt_00053397), multiglomerular vPN type 63 (FBbt_20003838), lALT4
   (FBbt_00047724), subesophageal sensory interneuron (FBbt_00004037), VA1d vPN
   (FBbt_00049766); plus shared nodes with the Or47b half (AL PN->LH FBbt_00053398,
   AL local FBbt_00007390, fru FBbt_00016687). The two pheromone channels converge
   on the same lateral-horn/fru readout. Cascade re-verified; the pheromone/
   bottle demo still exits 0 (ALL GREEN) with both ORNs as hop-0.

4. **l-LNv (FBbt_00003763): HEALED via label form.** Grouped ID and named still
   die server-side; **label form ('l-LNv neuron') returns 88 real rows.**
   New companion graph `subgraphs/clock_lLNv.json` (13n/12e): l-LNv talks back
   to the visual system (Tm3, MeVPMe12, lamina L1/L2/L5), accessory medulla
   (incl. aMe30), octopaminergic AL2b2, SEZ output, plus recurrent l-LNv and
   LN-period links. The clock's large cells close a visual feedback loop the
   general LNv walk (clock.json) doesn't show. The clock/ bottle is untouched.

5. **SMPad1 male (FBbt_00050245): HEALED via label form.** Grouped ID still dies
   server-side; **label form returns 1,372 real rows.** Merged into pc1.json
   (21n/35e): SMPad1->pC1 (tw=10,802) is a TRUE RECURRENT edge (hop-1 -> hop-0);
   SMPad1 also feeds the fru triple-convergence node (63,139), aSP-a, descending
   motor, and three new nodes (fru aDT-b, posterior-brain descending, fru pMP-e).
   **pc1.json is now CYCLIC — the pC1 loop is a recurrent social circuit, not a
   chain.** Cascade re-verified (toy handles the cycle; dies out by step 3).

6. **Epi (FBbt_00052624): STILL DEAD.** 0 rows all three forms (fast, genuinely
   empty). The CONFIRMED-FAIL (nociceptor literature attack, this file) stands;
   nociceptor_lit.json stays a 1-node stub.

7. **ppk23/ppk29 adult: STILL NO ADULT CLASS.** VFB search returns genes and GAL4
   lines only; "adult pickpocket 23/29 neuron" 0 hits. The two "gustatory
   pheromone neuron" instances (VFB_00101710/1763) are L1EM larval (skids
   5186461/9853425) — not adult, not usable for the adult graph.

8. **fat_peg.json hop-2: ALREADY WALKED** (10 nodes at hop 2) — no retry needed.

**Touch stubs re-pointed (2026-10-15):** touch_pressure.json and touch_brush.json
were honest 1-node stubs; the touch-qualities own-method solve (this file,
2026-10-14) resolved real wiring behind them. touch_pressure.json now carries
campaniform->b1 (REAL, tw=3,572); touch_brush.json carries bristle->MGT
(LITERATURE-HYPOTHESIS, cited). Both cascades fire; behavior/narration text
preserved; provenance updated.

**Remaining gaps after this sweep (the irreducible remainder):**
- Ir56d API rows (fat.json stub; fat_lit.json hypothesis stands)
- vPN1 connectivity (song middle link stays literature)
- Epi descending connectivity (nociceptor_lit.json stub)
- ppk23/ppk29 adult classes (don't exist in the ontology)
- Ir56d-peg subset attribution (no API marker distinguishes E409 within the peg class)
- Drive dynamics for all drives (unmapped in principle — no API holds them)
