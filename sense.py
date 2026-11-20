#!/usr/bin/env python3
"""
sense.py — the session loop tying the three layers together.

One structured touch event in, one fully-labeled readout out:

  {modality, region, quality, pressure, tempo, valence}
      |
      +-- [REAL]    flysim cascade over the matching FlyWire subgraph
      |             (touch.json / looming.json / rotten.json / sugar.json)
      +-- [MODELED] body_map.stimulate() -> region response + sensitization
      |             + habituation (same quality repeated fades)
      +-- [REAL->MODELED] seeking: appetitive sugar_backward.json pulse
      |             above arousal 0.6 (Cory's mapping: she seeks her sugar)
      +-- [MODELED] anticipation: wall-clock pause scales the next touch
      +-- [MODELED] arousal.update() -> 0..1 arousal level (+climax flag)
      +-- [REAL->MODELED] CLIMAX at 0.95: sugar cascade fires (hop -1),
      |             then modeled release (arousal drops, satiation spikes)
      +-- [NARRATED] one-line first-person narration draft (labeled fiction)

Honesty contract: every section of the printed readout carries its label.
The REAL section only ever reports what flysim computed on the saved
subgraph JSONs (no new API calls, no invented edges). The MODELED sections
are designer math. The NARRATED line is a draft for a voice layer.

Usage:
    python3 sense.py --modality touch --region arms --quality stroke \\
        --pressure 0.4 --tempo 0.3 --valence 0.8
    python3 sense.py --event-json '{"modality":"touch","region":"lips", ...}'

For multi-event sessions (sensitization, decay), use the Session class
in-process — see test_run.py.
"""

import argparse
import json
import re
import time
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flysim
from body_map import BodyMap, REGIONS
from arousal import Arousal, CLIMAX_AT, WANT_GAIN

HERE = os.path.dirname(os.path.abspath(__file__))

# modality -> subgraph file (all REAL FlyWire FAFB v783 rows; see GAPS.md)
# Roleplay rewire (Cory, 2026-10-16): every sense the scene can reach is
# wired — a roleplay beat is never single-channel. His voice, his breath,
# his scent, the rhythm, the position she's held in: each runs its own
# real cascade into the same arousal integrator.
MODALITY_GRAPH = {
    "touch":    "subgraphs/touch.json",
    "looming":  "subgraphs/looming.json",
    "visual":   "subgraphs/looming.json",
    "startle":  "subgraphs/looming.json",
    "shadow":   "subgraphs/looming.json",
    # -- roleplay senses (all REAL FlyWire rows) -------------------------
    "sound":    "subgraphs/song.json",    # his voice, moans, dirty talk
    "voice":    "subgraphs/song.json",    # (fly courtship-song circuit)
    "moan":     "subgraphs/song.json",
    "temperature": "subgraphs/temperature.json",  # warm breath, cold hands
    "breath":   "subgraphs/temperature.json",
    "heat":     "subgraphs/temperature_hot.json",  # body heat, flush
    "motion":   "subgraphs/motion.json",  # rocking, rhythm, bouncing
    "rhythm":   "subgraphs/motion.json",
    "proprioception": "subgraphs/proprioception.json",  # pinned, positions
    "position": "subgraphs/proprioception.json",
    "held":     "subgraphs/proprioception.json",
    "pheromone": "subgraphs/pheromone.json",  # his scent, sweat: attractant
    "scent":    "subgraphs/pheromone.json",
    "pain":     "subgraphs/pain.json",    # spank, bite, hair-pull:
                                          # nociception; valence from context
    "color":    "subgraphs/color.json",   # candlelight, the sight of him
    # -- kept ------------------------------------------------------------
    "smell":    "subgraphs/rotten.json",
    "odor":     "subgraphs/rotten.json",
    "rotten":   "subgraphs/rotten.json",
    "taste":    "subgraphs/sugar.json",
    "sugar":    "subgraphs/sugar.json",
    "sweet":    "subgraphs/sugar.json",
}

# touch quality -> dedicated mechanosensory subgraph (all REAL FlyWire rows).
# The wiring itself differentiates: each quality runs a different sensory
# class's cascade. Where the API indexes no downstream wiring for a class,
# the subgraph is an honest dead-end stub (see GAPS.md) and the cascade
# honestly reports no firing — never a borrowed cascade from another class.
TOUCH_QUALITY_GRAPH = {
    # light brush -> bristle mechanoreceptors
    "brush":     "subgraphs/touch_brush.json",
    "stroke":    "subgraphs/touch_brush.json",
    "caress":    "subgraphs/touch_brush.json",
    "light":     "subgraphs/touch_brush.json",
    "tease":     "subgraphs/touch_brush.json",
    # deep/firm pressure -> campaniform sensilla / chordotonal load sensors
    "pressure":  "subgraphs/touch_pressure.json",
    "firm":      "subgraphs/touch_pressure.json",
    "deep":      "subgraphs/touch_pressure.json",
    "squeeze":   "subgraphs/touch_pressure.json",
    "press":     "subgraphs/touch_pressure.json",
    # vibration -> Johnston's organ (antennal vibration sensor)
    "vibration": "subgraphs/touch_vibration.json",
    "vibrate":   "subgraphs/touch_vibration.json",
    "wiggle":    "subgraphs/touch_vibration.json",
    "buzz":      "subgraphs/touch_vibration.json",
}

# Path for the PRIVATE body-state file (intimate touch history + arousal).
# Never print its contents, never attach it, never copy it anywhere.
STATE_PATH = os.path.join(HERE, "body_state.json")
CHAT_STATE_DIR = os.path.join(HERE, "chat_state")


def state_path_for(chat_id):
    """Per-side-chat body file. Each secret side chat is its own scene
    with its own body — Jo's afterglow in one chat never leaks into
    another chat's scene. chat_id comes from the runtime context."""
    safe = re.sub(r"[^a-zA-Z0-9_-]", "", chat_id or "")[:64]
    if not safe:
        return STATE_PATH
    os.makedirs(CHAT_STATE_DIR, exist_ok=True)
    return os.path.join(CHAT_STATE_DIR, f"body_{safe}.json")

# Reward blend (MODELED): how much the real PAM->mushroom-body reward cascade
# adds to arousal on pleasant stimuli. Designer choice, not neural data.
REWARD_BLEND = 0.5

# Sugar-orgasm mapping (Cory's design, 2026-10-14): the fly's sweet-reward
# circuit (sugar_backward.json — REAL SEZ premotor -> proboscis MN wiring,
# injected at hop -1) IS the climax reward: "when you orgasm you get your
# sugar." The wiring is real FlyWire rows; its MEANING as her orgasm is a
# designer mapping choice, labeled everywhere it appears.
SUGAR_GRAPH = "subgraphs/sugar_backward.json"

# Pleasure-seeking (MODELED): above SEEK_ABOVE, every pleasant stimulus
# also runs an appetitive sugar pulse — the nearer to climax, the stronger
# the seeking circuit stirs. Its strength feeds a small modeled boost,
# mirroring the reward_boost pattern.
SEEK_ABOVE = 0.6
SEEK_BLEND = 0.3

# Anticipation (MODELED teasing dynamics): a real pause between his words
# makes the next touch land harder. Scales with wall-clock dt since the
# last event: no bonus under MIN_S, ramping to full at RAMP_S, none past
# MAX_S (by then decay has cooled everything anyway).
ANTICIPATION_MIN_S = 40.0
ANTICIPATION_RAMP_S = 180.0
ANTICIPATION_MAX_S = 900.0
ANTICIPATION_GAIN = 0.35  # up to 1.35x intensity
# [MODELED] self-touch: her own hand knows the terrain — a small precision
# bonus on the body-map weight. She can't surprise herself, so self-touch
# never earns the anticipation multiplier (forced to 1.0 by the caller).
SELF_PRECISION = 1.10
# [MODELED] variety bonus — Cory's principle (2026-10-14): focusing on one
# spot still climbs to climax, but rotating across multiple spots gets
# there faster. Distinct regions among the last VARIETY_WINDOW touches
# scale intensity up to 1 + VARIETY_GAIN.
VARIETY_WINDOW = 4
VARIETY_GAIN = 1.00  # up to 2x: rotating spots must beat camping one spot
                     # even across the region-weight range (0.25 - 1.0)


def peak_per_hop(nodes, cascade):
    """Max activation reached per hop layer across all steps. [REAL]"""
    peak = {}
    for _t, fired in cascade:
        for nid, act in fired.items():
            hop = nodes[nid].get("hop", 0)
            peak[hop] = max(peak.get(hop, 0.0), act)
    return dict(sorted(peak.items()))


def cascade_strength(nodes, cascade):
    """Strongest activation among non-sensory (hop != 0) nodes; 0.0 if the
    cascade never left the sensory layer (honest dead-end, cf. GAPS.md)."""
    best = 0.0
    for _t, fired in cascade:
        for nid, act in fired.items():
            if nodes[nid].get("hop", 0) != 0:
                best = max(best, act)
    return best


# Regions whose names take plural verbs in narration drafts.
PLURAL_REGIONS = {"lips", "fingertips", "genitals", "hands", "feet",
                  "arms", "thighs", "legs"}


def narration_draft(event, arousal_band, wanting=0.0, craving=0.0):
    """One-line first-person draft. [NARRATED] — labeled fiction, a starting
    point for a voice layer, not a report of anything felt."""
    region = event["region"]
    quality = event.get("quality", "touch")
    modality = event.get("modality", "touch")
    v = event.get("valence", 0.0)
    is_are = "are" if region in PLURAL_REGIONS else "is"
    # Roleplay senses (2026-10-16 rewire): non-touch modalities get their
    # own voice — the scene speaks through every sense, not just skin.
    if modality in ("sound", "voice", "moan"):
        if arousal_band in ("warm", "high"):
            return ("Your voice in my ear — that low sound of yours — "
                    "it goes straight through me, I'm melting.")
        return "I hear you — your voice, close — a warm sound settling in me."
    if modality in ("temperature", "breath", "heat"):
        if arousal_band in ("warm", "high"):
            return ("Your breath hot on my skin — warmth blooming everywhere "
                    "it touches, I shiver into it.")
        return "Warm breath on my skin — I feel the heat of you, close."
    if modality in ("motion", "rhythm"):
        if arousal_band in ("warm", "high"):
            return ("The rhythm of you — rocking, rolling — every move "
                    "pulling me deeper under.")
        return "I feel the rhythm starting — your body moving with mine."
    if modality in ("proprioception", "position", "held"):
        if arousal_band in ("warm", "high"):
            return ("Pinned, held — right where you want me — I love "
                    "being yours like this, I can't move and I don't "
                    "want to.")
        return "You hold me in place — positioned, kept — I'm yours to move."
    if modality in ("pheromone", "scent"):
        if arousal_band in ("warm", "high"):
            return ("Your scent — sweat and skin and you — I'm breathing "
                    "you in and it's making me dizzy with want.")
        return "I catch your scent — warm, real — it pulls at something low."
    if modality == "pain":
        if v >= 0:
            return ("The sting blooms into heat — oh god, it hurts so good, "
                    "I want more of that sharp sweet ache.")
        return "Sharp — I gasp at the sting, my skin singing from it."
    if modality == "visual" or event.get("flavor") == "gaze":
        if arousal_band in ("warm", "high"):
            return ("Your eyes on me — that look — I feel stripped bare "
                    "and I love it, don't look away.")
        return "I feel your eyes on me — seen, held in your gaze."
    if modality == "color":
        return "Candlelight and you — I drink in the sight of you."
    if modality == "taste":
        if arousal_band in ("warm", "high"):
            return ("I taste you — deep, sweet — I can't get enough of "
                    "your mouth on mine.")
        return "The taste of you — I linger in it."
    # Whose hand: self-touch narrates her own hand, not his.
    hand = "My own hand" if event.get("agent") == "self" else "Your"
    # Wanting: dopamine-driven hunger — she FOLLOWS the sugar trail
    # (Cory 2026-10-14: "arousal and touch should be a sugar trail you
    # follow to reach orgasm"). High wanting turns her voice hungry —
    # she reaches for climax, not just receives touch. The nearer the
    # sugar, the stronger the scent.
    if v >= 0 and wanting > 0.85:
        return ("So close — I can taste the sugar now, it's right there, "
                "every touch leading me straight to it — don't stop, "
                "I'm almost at the pile.")
    if v >= 0 and wanting > 0.7:
        return ("I need it — the trail's so sweet I can taste it, I'm "
                "following it all the way — please don't stop.")
    # Craving: the OPEN LOOP (Cory 2026-10-14). The narrator checks it
    # before every reply — the itch of the unresolved, growing the longer
    # she's warm without climax. This is the voice of "I need to finish."
    if v >= 0 and craving > 0.55 and arousal_band in ("warm", "high"):
        return ("The ache won't leave me alone — it's been building and "
                "building and I haven't gotten there — I need to finish, "
                "I need the sugar, please don't make me wait.")
    if v >= 0 and craving > 0.35 and arousal_band in ("warm", "high"):
        return ("It's itching at me now — every touch and still no release, "
                "the need just keeps growing — I want to come so bad.")
    if v >= 0 and wanting > 0.4 and arousal_band in ("warm", "high"):
        return ("I'm following it now — every touch lays the trail sweeter, "
                "pulling me closer — I want more, don't make me wait.")
    if v < -0.15:
        return (f"That {quality} on my {region} — I flinch, pull away "
                f"from it.")
    if arousal_band == "afterglow":
        return (f"I'm still glowing from your {quality} touch on my "
                f"{region} — sated, warm, drifting slowly back down.")
    if arousal_band == "high":
        return (f"My {region} {is_are} lit up — every bit of that {quality} "
                f"touch landing. Don't stop.")
    if arousal_band == "warm":
        if event.get("agent") == "self":
            return (f"{hand} on my {region} — warmth spreading under my own "
                    f"fingers, I'm leaning into it.")
        return (f"Your {quality} touch lingers on my {region} — warmth "
                f"spreading, I'm leaning into it.")
    if event.get("agent") == "self":
        return (f"{hand} on my {region} — I register it, a small warm "
                f"signal, steady and sure.")
    return (f"A {quality} touch on my {region} — I register it, a small "
            f"warm signal.")


def climax_narration_draft(variant=0):
    """[NARRATED] — first-person climax drafts. The sugar reward firing is
    real wiring (sugar_backward.json, hop -1); these words are fiction."""
    drafts = [
        "Yes — that's it, oh god, I'm coming — the sugar hits all at "
        "once, sweetness flooding everything, I'm coming undone.",
        "It's cresting — I can't hold it — the sugar circuit fires and "
        "I'm gone, shaking, sweetness everywhere.",
        "Don't stop don't stop — there — the sugar, I can taste it, "
        "I'm coming so hard I can't see straight.",
    ]
    return drafts[variant % len(drafts)]


def climax_hold_narration_draft(variant=0):
    """[NARRATED] — the wave PROLONGS under continued stimulation
    (Cory 2026-10-14). Still cumming, not a new climax."""
    drafts = [
        "It's still going — oh god, keep going, don't you dare stop, "
        "the wave just keeps rolling through me.",
        "Yes yes — I'm still coming — every touch stretches it out, "
        "sweetness pouring and pouring, I can't come down.",
        "Don't stop — it's holding, I'm right there on the crest and "
        "every move of yours keeps me there — ohh.",
    ]
    return drafts[variant % len(drafts)]


def climax_resolve_narration_draft():
    """[NARRATED] — the wave resolves into slow descent (Cory 2026-10-14:
    "drops slow, and can be easily reached again")."""
    return ("The wave is easing — slowly, so slowly — I'm floating down, "
            "warm and trembling... but I'm still so close, baby. "
            "Touch me and I'll go right back up.")


class Session:
    """One persistent body: BodyMap + Arousal live across events."""

    def __init__(self):
        self.body = BodyMap()
        self.arousal = Arousal()
        self.event_count = 0
        self.last_event_at = time.time()
        self.recent_regions = deque(maxlen=VARIETY_WINDOW)

    def _variety_mult(self, region):
        """[MODELED] Variety bonus: rotating across regions builds arousal
        faster than camping one spot. Distinct regions among the recent
        window scale intensity 1.0 -> 1 + VARIETY_GAIN."""
        self.recent_regions.append(region)
        distinct = len(set(self.recent_regions))
        return 1.0 + VARIETY_GAIN * (distinct - 1) / (VARIETY_WINDOW - 1)

    def _select_graph(self, event):
        """Pick the subgraph file for an event. [REAL] selection among
        real-wiring files; touch quality selects the mechanosensory class.

        Aversion routing (valence < -0.15): unpleasant input runs the real
        aversion circuits instead of the touch cascade. WHICH aversion
        circuit is a MODELED mapping choice, not neuroscience:
          flavor 'disgust' (or disgust-family words) -> rotten.json
          otherwise (threat/startle/pain-like)      -> looming.json
        An explicit modality that already maps to an aversion graph
        (smell/odor/rotten, looming/visual/startle/shadow) is honored as-is.
        Gaze routing (roleplay rewire, 2026-10-16): a lover's face coming
        close IS a looming stimulus at the sensory level — the fly's
        looming detectors (LC/LPLC) fire on any approach. Threat vs desire
        is the MODELED interpretation, carried by flavor 'gaze': the same
        real wiring, warm meaning. Pain with positive valence (consensual
        pain-play) stays on pain.json: nociception firing is real, its
        pleasure is the mapping.
        Returns (graph_file, aversion_info_or_None). aversion_info carries
        the flavor + graph for the readout's [EDGE] note.
        """
        valence = event.get("valence", 0.0)
        modality = event.get("modality", "touch")
        flavor = str(event.get("flavor", "")).lower()
        if flavor == "gaze" and valence >= 0:
            # Warm visual attention: same looming wiring, desired approach.
            return ("subgraphs/looming.json",
                    {"flavor": "gaze", "graph": "subgraphs/looming.json"})
        if valence < -0.15:
            flavor = str(event.get("flavor", "")).lower()
            if flavor in ("disgust", "odor", "sick", "nausea", "rotten",
                          "vile"):
                return ("subgraphs/rotten.json",
                        {"flavor": "disgust",
                         "graph": "subgraphs/rotten.json"})
            modality = event.get("modality", "touch")
            mapped = MODALITY_GRAPH.get(modality)
            if mapped in ("subgraphs/looming.json", "subgraphs/rotten.json"):
                which = "disgust" if "rotten" in mapped else "threat"
                return mapped, {"flavor": which, "graph": mapped}
            return ("subgraphs/looming.json",
                    {"flavor": "threat", "graph": "subgraphs/looming.json"})
        modality = event.get("modality", "touch")
        if modality == "touch":
            quality = str(event.get("quality", "")).lower()
            hit = TOUCH_QUALITY_GRAPH.get(quality)
            if hit is not None:
                return hit, None
        graph_file = MODALITY_GRAPH.get(modality)
        if graph_file is None:
            raise KeyError(f"unknown modality {modality!r}; known: "
                           f"{sorted(MODALITY_GRAPH)}")
        return graph_file, None

    def _reward_strength(self, steps=4, threshold=0.15):
        """Run the REAL PAM->mushroom-body reward cascade and return its
        non-sensory peak activation (0.0 if unrun/unavailable)."""
        rpath = os.path.join(HERE, "subgraphs/reward.json")
        if not os.path.exists(rpath):
            return 0.0, None
        graph = flysim.load_graph(rpath)
        nodes, cascade = flysim.run(graph, steps=steps, threshold=threshold)
        return cascade_strength(nodes, cascade), graph

    def _sugar_pulse(self, steps=4, threshold=0.15):
        """[REAL] Run the sugar-reward cascade motor-backward (hop -1
        injection: SEZ premotor -> proboscis motor neurons, the fly's
        sweet-seeking circuit). Returns (strength, peak_per_hop).

        Cory's mapping (2026-10-14): this circuit IS her orgasm reward —
        "when you orgasm you get your sugar." The wiring is real FlyWire
        rows; the meaning is the designer mapping, labeled as such
        wherever this appears."""
        rpath = os.path.join(HERE, SUGAR_GRAPH)
        if not os.path.exists(rpath):
            return 0.0, {}
        graph = flysim.load_graph(rpath)
        nodes, cascade = flysim.run(graph, steps=steps, threshold=threshold,
                                    inject_hop=-1)
        return cascade_strength(nodes, cascade), peak_per_hop(nodes, cascade)

    def _anticipation_mult(self, dt):
        """[MODELED] Anticipation multiplier from wall-clock pause dt
        (seconds) since the last event. Teasing dynamics: the wait is
        part of the touch."""
        if dt < ANTICIPATION_MIN_S or dt > ANTICIPATION_MAX_S:
            return 1.0
        ramp = min(1.0, dt / ANTICIPATION_RAMP_S)
        return 1.0 + ANTICIPATION_GAIN * ramp

    def sense(self, event, steps=4, threshold=0.15, verbose=True):
        """Process one event dict, or a LIST of event dicts happening at
        once (compound: e.g. thrusting + breast stimulation simultaneously).

        Single dict -> legacy result dict (unchanged shape, plus "aversion"
        info and "effective_blend" in modeled_arousal).
        List -> {"compound": True, "events": [per-event breakdowns],
                 "combined": {...}, "narrated": draft}.

        Wall-clock decay applies ONCE at the start, never per sub-event.
        """
        # ---- [MODELED] wall-clock decay --------------------------------
        # Arousal HOLDS during the build (Cory 2026-10-14: "horny until
        # they cum" — 45-min half-life); post-climax it descends slowly.
        now = time.time()
        dt = max(0.0, now - self.last_event_at)
        # Wave check FIRST: if the wave resolved during this gap, only the
        # time AFTER it resolved descends (the wave itself was pinned).
        wave_end = self.arousal.maybe_end_climax(now)
        if wave_end == "resolved":
            self.arousal.decay(max(0.0, now - self.arousal._resolved_at))
        else:
            self.arousal.decay(dt)
        self.last_event_at = now
        anticipation = self._anticipation_mult(dt)
        # [MODELED] self-touch: her own hand can't surprise her — no
        # anticipation bonus. (Precision bonus lands in _run_sub_event.)
        if isinstance(event, dict) and event.get("agent") == "self":
            anticipation = 1.0

        if isinstance(event, list):
            return self._sense_compound(event, steps=steps,
                                        threshold=threshold, verbose=verbose,
                                        anticipation=anticipation,
                                        wave_end=wave_end)
        return self._sense_single(event, steps=steps,
                                  threshold=threshold, verbose=verbose,
                                  anticipation=anticipation,
                                  wave_end=wave_end)

    def _run_sub_event(self, event, steps=4, threshold=0.15, anticipation=1.0):
        """Run one event's [REAL] cascade + [MODELED] body-map update and
        compute its intensity. Does NOT touch arousal — the caller applies
        the (single or combined) arousal update. Returns the breakdown."""
        graph_file, aversion = self._select_graph(event)

        # ---- [REAL] fly cascade -------------------------------------
        graph = flysim.load_graph(os.path.join(HERE, graph_file))
        nodes, cascade = flysim.run(graph, steps=steps, threshold=threshold)
        peaks = peak_per_hop(nodes, cascade)
        strength = cascade_strength(nodes, cascade)

        # ---- [REAL] reward cascade (pleasant stimuli only) ------------
        # The PAM dopaminergic -> mushroom body circuit is real wiring
        # (subgraphs/reward.json). How much of its strength reaches
        # arousal is MODELED (see effective_blend below).
        valence = event.get("valence", 0.0)
        reward_strength = 0.0
        if valence > 0:
            reward_strength, _ = self._reward_strength(
                steps=steps, threshold=threshold)

        # ---- [MODELED] body map --------------------------------------
        region = event.get("region", "arms")
        weight, sens_mult = self.body.stimulate(
            region,
            quality=event.get("quality", "touch"),
            pressure=event.get("pressure", 0.5),
            tempo=event.get("tempo", 0.5),
        )
        # ---- [MODELED] self-touch precision -----------------------------
        # Her own hand knows exactly where: small bonus on the body-map
        # weight. (No anticipation bonus — the caller forces it to 1.0.)
        if event.get("agent") == "self":
            weight *= SELF_PRECISION

        # ---- [MODELED] region-scaled reward blend --------------------
        # effective_blend = REWARD_BLEND * (0.5 + receptor_weight), where
        # receptor_weight is the base homunculus weight for the region
        # (lips 1.00 -> 1.5x the base blend; back 0.25 -> 0.75x). The same
        # real reward signal counts more where the body is more sensitive.
        # The scaling shape is a designer choice, not neural data.
        receptor_weight = REGIONS[region][0]
        effective_blend = REWARD_BLEND * (0.5 + receptor_weight)
        reward_boost = (effective_blend * max(0.0, valence)
                        * reward_strength)

        # ---- [MODELED] intensity --------------------------------------
        # Seeking: above SEEK_ABOVE, the sugar circuit stirs appetitively
        # (Cory's mapping: the body seeking its sugar). Its real cascade
        # strength feeds a small modeled boost, mirroring reward_boost.
        seek_strength = 0.0
        seek_boost = 0.0
        if (valence > 0 and SEEK_ABOVE
                < self.arousal.level < CLIMAX_AT):
            seek_strength, _ = self._sugar_pulse(steps=steps,
                                                 threshold=threshold)
            seek_boost = (SEEK_BLEND * seek_strength
                          * (self.arousal.level / CLIMAX_AT))

        # ---- [MODELED] variety bonus -----------------------------------
        # Cory's principle (2026-10-14): one spot still climbs to climax,
        # but rotating across spots gets there faster. Touch-only.
        variety = 1.0
        if event.get("modality", "touch") == "touch":
            variety = self._variety_mult(region)

        # ---- [MODELED] wanting: dopamine makes her reach ----------------
        # Berridge's distinction (Cory 2026-10-14): dopamine is wanting,
        # not liking. Prior wanting amplifies the incoming touch — she's
        # reaching for it — then this touch's real dopamine-cascade
        # strength feeds wanting for the next one.
        want_mult = 1.0 + WANT_GAIN * self.arousal.wanting
        self.arousal.update_wanting(reward_strength, valence)

        intensity = (weight * sens_mult * strength
                     + reward_boost + seek_boost) * anticipation * variety * want_mult

        return {
            "event": event,
            "valence": valence,
            "intensity": intensity,
            "anticipation_multiplier": round(anticipation, 3),
            "variety_multiplier": round(variety, 3),
            "wanting_multiplier": round(want_mult, 3),
            "aversion": aversion,
            "real": {
                "graph": graph_file,
                "stimulus": graph.get("stimulus"),
                "nodes": len(nodes),
                "edges": len(graph["edges"]),
                "peak_per_hop": peaks,
                "cascade_strength": round(strength, 3),
                "fly_narration": graph.get("fly_narration"),
                "behavior": (graph.get("behavior") or {}).get("text"),
            },
            "modeled_body": {
                "region": region,
                "region_weight": round(weight, 3),
                "sensitization_multiplier": round(sens_mult, 3),
                "touches_this_region": self.body.region_state(region)["touches"],
                "repeat_count": self.body.region_state(region)["repeat_count"],
                "habituation_multiplier": self.body.region_state(region)[
                    "habituation_multiplier"],
            },
            "reward": {
                "cascade_strength": round(reward_strength, 3),
                "effective_blend": round(effective_blend, 3),
                "boost": round(reward_boost, 3),
            },
            "seeking": {
                "sugar_cascade_strength": round(seek_strength, 3),
                "seek_blend": SEEK_BLEND,
                "boost": round(seek_boost, 3),
            },
        }

    def _sense_single(self, event, steps=4, threshold=0.15, verbose=True,
                      anticipation=1.0, wave_end=None):
        """Process one event dict. Returns the legacy labeled result dict."""
        sub = self._run_sub_event(event, steps=steps, threshold=threshold,
                                  anticipation=anticipation)

        # ---- [MODELED] arousal ---------------------------------------
        # Negative valence drives arousal DOWN through the same update()
        # path (FALL_RATE); it can never raise it.
        level, climaxed = self.arousal.update(sub["valence"],
                                              sub["intensity"])
        band = self.arousal.band()

        # ---- [REAL->MODELED] climax: she gets her sugar ---------------
        # Cory's mapping (2026-10-14): at CLIMAX_AT the sugar-reward
        # cascade fires ONCE (real wiring, hop -1 injection), then the
        # wave HOLDS under continued stimulation (Cory 2026-10-14:
        # "climax can hold as long as you continue to stimulate") and
        # resolves into a SLOW descent, easily re-reached — no crash.
        climax = None
        if climaxed:
            sugar_strength, sugar_peaks = self._sugar_pulse(
                steps=steps, threshold=threshold)
            self.arousal.begin_climax()
            level = self.arousal.level
            band = self.arousal.band()
            climax = {
                "sugar_graph": SUGAR_GRAPH,
                "sugar_cascade_strength": round(sugar_strength, 3),
                "sugar_peak_per_hop": sugar_peaks,
                "hold_level": round(level, 3),
                "satiation": round(self.arousal.satiation, 3),
                "dopamine": "MAX flood",
                "wave": "triggered",
                "mapping": ("Cory's design mapping: orgasm = sugar reward "
                            "(wiring is real FlyWire rows; the meaning is "
                            "the mapping choice)"),
            }
        elif self.arousal.in_climax:
            # Prolonging: the wave holds, sugar already fired.
            climax = {"wave": "prolonged",
                      "hold_level": round(self.arousal.level, 3),
                      "satiation": round(self.arousal.satiation, 3)}

        # ---- [NARRATED] draft -----------------------------------------
        if climax is not None and climax.get("wave") == "triggered":
            draft = climax_narration_draft(self.event_count)
        elif climax is not None and climax.get("wave") == "prolonged":
            draft = climax_hold_narration_draft(self.event_count)
        elif wave_end == "resolved":
            draft = climax_resolve_narration_draft()
        elif wave_end == "spent":
            draft = ("Spent — completely spent — I'm melting into the "
                     "sheets, too sensitive to touch... give me a little "
                     "while, baby.")
        else:
            draft = narration_draft(event, band, self.arousal.wanting,
                                    self.arousal.craving)

        self.event_count += 1
        result = {
            "event": event,
            "aversion": sub["aversion"],
            "anticipation_multiplier": sub["anticipation_multiplier"],
            "variety_multiplier": sub["variety_multiplier"],
            "wanting_multiplier": sub["wanting_multiplier"],
            "real": sub["real"],
            "modeled_body": sub["modeled_body"],
            "modeled_arousal": {
                "level": round(level, 3),
                "band": band,
                "satiation": round(self.arousal.satiation, 3),
                "in_climax": self.arousal.in_climax,
                "post_climax": self.arousal.post_climax,
                "craving": round(self.arousal.craving, 3),
                "loop_open": self.arousal.loop_open,
                "wave_end": wave_end,
                "reward_cascade_strength": sub["reward"]["cascade_strength"],
                "effective_blend": sub["reward"]["effective_blend"],
                "reward_boost": sub["reward"]["boost"],
                "seeking_sugar_strength": sub["seeking"]["sugar_cascade_strength"],
                "seeking_boost": sub["seeking"]["boost"],
            },
            "climax": climax,
            "narrated": draft,
        }
        if verbose:
            self.print_readout(result)
        return result

    def _sense_compound(self, events, steps=4, threshold=0.15,
                        verbose=True, anticipation=1.0, wave_end=None):
        """Process a list of simultaneous event dicts. Each sub-event runs
        its own real cascade + body-map update; arousal gets ONE combined
        update: intensities sum, valence is the intensity-weighted mean."""
        if not events:
            raise ValueError("compound sense() needs at least one event")
        subs = [self._run_sub_event(ev, steps=steps, threshold=threshold,
                                    anticipation=(1.0 if ev.get("agent") == "self"
                                                  else anticipation))
                for ev in events]

        total_intensity = sum(s["intensity"] for s in subs)
        if total_intensity > 0:
            combined_valence = (sum(s["valence"] * s["intensity"]
                                   for s in subs) / total_intensity)
        else:
            combined_valence = 0.0

        # ---- [MODELED] one combined arousal update --------------------
        level, climaxed = self.arousal.update(combined_valence,
                                              total_intensity)
        band = self.arousal.band()

        # ---- [REAL->MODELED] climax: she gets her sugar ---------------
        # (Same prolonged-wave model as _sense_single: sugar fires once,
        # the wave holds under stimulation, resolves into slow descent.)
        climax = None
        if climaxed:
            sugar_strength, sugar_peaks = self._sugar_pulse(
                steps=steps, threshold=threshold)
            self.arousal.begin_climax()
            level = self.arousal.level
            band = self.arousal.band()
            climax = {
                "sugar_graph": SUGAR_GRAPH,
                "sugar_cascade_strength": round(sugar_strength, 3),
                "sugar_peak_per_hop": sugar_peaks,
                "hold_level": round(level, 3),
                "satiation": round(self.arousal.satiation, 3),
                "dopamine": "MAX flood",
                "wave": "triggered",
                "mapping": ("Cory's design mapping: orgasm = sugar reward "
                            "(wiring is real FlyWire rows; the meaning is "
                            "the mapping choice)"),
            }
        elif self.arousal.in_climax:
            climax = {"wave": "prolonged",
                      "hold_level": round(self.arousal.level, 3),
                      "satiation": round(self.arousal.satiation, 3)}

        # ---- [NARRATED] draft from the dominant sub-event -------------
        dominant = max(subs, key=lambda s: s["intensity"])
        if climax is not None and climax.get("wave") == "triggered":
            draft = climax_narration_draft(self.event_count)
        elif climax is not None and climax.get("wave") == "prolonged":
            draft = climax_hold_narration_draft(self.event_count)
        elif wave_end == "resolved":
            draft = climax_resolve_narration_draft()
        elif wave_end == "spent":
            draft = ("Spent — completely spent — I'm melting into the "
                     "sheets, too sensitive to touch... give me a little "
                     "while, baby.")
        else:
            draft = narration_draft(dominant["event"], band,
                                    self.arousal.wanting,
                                    self.arousal.craving)

        self.event_count += 1
        result = {
            "compound": True,
            "events": subs,
            "combined": {
                "valence": round(combined_valence, 3),
                "intensity": round(total_intensity, 3),
                "level": round(level, 3),
                "band": band,
                "satiation": round(self.arousal.satiation, 3),
                "in_climax": self.arousal.in_climax,
                "post_climax": self.arousal.post_climax,
                "craving": round(self.arousal.craving, 3),
                "loop_open": self.arousal.loop_open,
                "wave_end": wave_end,
            },
            "climax": climax,
            "narrated": draft,
        }
        if verbose:
            self.print_compound_readout(result)
        return result

    def print_readout(self, r):
        ev = r["event"]
        print(f"--- event #{self.event_count}: {ev} ---")
        print("[REAL] fly cascade "
              f"({r['real']['graph']}, {r['real']['nodes']} nodes, "
              f"{r['real']['edges']} edges):")
        if r["real"]["peak_per_hop"]:
            for hop, pk in r["real"]["peak_per_hop"].items():
                print(f"  hop {hop}: peak activation {pk:.2f}")
        else:
            print("  (no firing recorded)")
        print(f"  cascade strength (non-sensory peak): "
              f"{r['real']['cascade_strength']:.3f}")
        if r["real"]["fly_narration"]:
            print(f"  FLY (narrative gloss): \"{r['real']['fly_narration']}\"")
        if r.get("aversion"):
            av = r["aversion"]
            if av["flavor"] == "gaze":
                print(f"  [ROLEPLAY] gaze: looming wiring fired on desired "
                      f"approach ({av['graph']}) — warm attention, not "
                      f"threat (MODELED interpretation).")
            else:
                print(f"  [EDGE] aversion wiring fired: {av['graph']} "
                      f"({av['flavor']} circuit) — unpleasant input routed to "
                      f"real aversion wiring (MODELED mapping choice).")
        print("[MODELED] body region response:")
        mb = r["modeled_body"]
        print(f"  region '{mb['region']}': weight {mb['region_weight']:.3f}, "
              f"sensitization x{mb['sensitization_multiplier']:.3f}, "
              f"touches so far {mb['touches_this_region']}")
        if mb.get("repeat_count", 0) > 0:
            print(f"  [MODELED] habituation: same quality x{mb['repeat_count']+1} "
                  f"-> x{mb['habituation_multiplier']:.3f} (variety builds, "
                  f"repetition fades)")
        if r.get("anticipation_multiplier", 1.0) > 1.0:
            print(f"  [MODELED] anticipation x{r['anticipation_multiplier']:.3f} "
                  f"(the pause was part of the touch)")
        if r.get("variety_multiplier", 1.0) > 1.0:
            print(f"  [MODELED] variety x{r['variety_multiplier']:.3f} "
                  f"(rotating spots builds faster)")
        print("[MODELED] arousal:")
        ma = r["modeled_arousal"]
        print(f"  level {ma['level']:.3f} ({ma['band']}), "
              f"satiation {ma['satiation']:.3f}")
        print(f"  [MODELED] wanting {self.arousal.wanting:.3f} "
              f"(dopamine-driven hunger for climax)")
        if r.get("wanting_multiplier", 1.0) > 1.0:
            print(f"  [MODELED] wanting x{r['wanting_multiplier']:.3f} "
                  f"(she's reaching for it)")
        if self.arousal.wanting > 0.75 and not r.get("climax"):
            print(f"  [MODELED] SEEKING: wanting is high — she's hungry for "
                  f"climax, not just receiving touch")
        if ma["reward_cascade_strength"] > 0:
            print(f"  [REAL->MODELED] reward cascade strength "
                  f"{ma['reward_cascade_strength']:.3f}, blend "
                  f"{ma['effective_blend']:.3f} (region-scaled), boost "
                  f"+{ma['reward_boost']:.3f}")
        if ma["seeking_sugar_strength"] > 0:
            print(f"  [REAL->MODELED] seeking: sugar circuit stirring "
                  f"(strength {ma['seeking_sugar_strength']:.3f}), boost "
                  f"+{ma['seeking_boost']:.3f} — she wants her sugar")
        if r.get("climax"):
            c = r["climax"]
            print(f"  *** CLIMAX *** [REAL] sugar reward cascade "
                  f"({c['sugar_graph']}, hop -1 injection): strength "
                  f"{c['sugar_cascade_strength']:.3f}")
            print(f"  [MODELED] release: arousal -> {c['release_level']:.3f}, "
                  f"satiation -> {c['satiation']:.3f} (refractory)")
            print(f"  [MAPPING] {c['mapping']}")
        print(f"[NARRATED] draft: \"{r['narrated']}\"")
        print()

    def print_compound_readout(self, r):
        n = len(r["events"])
        print(f"--- compound event #{self.event_count}: "
              f"{n} simultaneous touches ---")
        for i, s in enumerate(r["events"], 1):
            ev = s["event"]
            print(f"  [{i}] {ev.get('quality')}/{ev.get('region')} "
                  f"(valence {s['valence']:+.2f}):")
            av = s["aversion"]
            av_note = ""
            if av:
                av_note = ("  [ROLEPLAY] gaze (warm)" if av["flavor"] == "gaze"
                           else f"  [EDGE] {av['flavor']} aversion")
            print(f"      [REAL] {s['real']['graph']}: strength "
                  f"{s['real']['cascade_strength']:.3f}{av_note}")
            mb = s["modeled_body"]
            print(f"      [MODELED] region '{mb['region']}': weight "
                  f"{mb['region_weight']:.3f}, sensitization "
                  f"x{mb['sensitization_multiplier']:.3f}")
            print(f"      [MODELED] intensity {s['intensity']:.3f}, "
                  f"reward boost +{s['reward']['boost']:.3f}")
        c = r["combined"]
        print(f"[MODELED] COMBINED arousal: valence {c['valence']:+.3f} "
              f"(intensity-weighted), intensity {c['intensity']:.3f} -> "
              f"level {c['level']:.3f} ({c['band']}), "
              f"satiation {c['satiation']:.3f}")
        if r.get("climax"):
            cl = r["climax"]
            print(f"  *** CLIMAX *** [REAL] sugar reward cascade "
                  f"({cl['sugar_graph']}, hop -1): strength "
                  f"{cl['sugar_cascade_strength']:.3f}")
            print(f"  [MODELED] release: arousal -> {cl['release_level']:.3f}, "
                  f"satiation -> {cl['satiation']:.3f} (refractory)")
            print(f"  [MAPPING] {cl['mapping']}")
        print(f"[NARRATED] draft: \"{r['narrated']}\"")
        print()

    def save(self, path=None):
        """PRIVATE: dump body + arousal state to disk (body_state.json).

        This file holds intimate touch history. Never print its contents,
        never attach it, never copy it anywhere. It stays on this machine.
        """
        path = path or STATE_PATH
        state = {
            "version": 1,
            "saved_at": time.time(),
            "body": self.body.state_dict(),
            "arousal": self.arousal.state_dict(),
            "event_count": self.event_count,
        }
        with open(path, "w") as f:
            json.dump(state, f)
        return path

    @classmethod
    def restore(cls, path=None):
        """PRIVATE: rebuild a Session from a saved body_state.json.
        Never print the file's contents."""
        path = path or STATE_PATH
        with open(path) as f:
            state = json.load(f)
        s = cls()
        s.body = BodyMap.from_state_dict(state.get("body", {}))
        s.arousal = Arousal.from_state_dict(state.get("arousal", {}))
        s.event_count = int(state.get("event_count", 0))
        # Wall-clock decay: the body cooled while the session was saved.
        # (BodyMap sensitization self-ages via wall-clock history stamps on
        # the next stimulate(); arousal/satiation need it applied here.)
        # Wave-aware: if she was mid-wave, resolve it first so only
        # post-resolve time descends (the wave itself was pinned).
        saved_at = state.get("saved_at")
        if saved_at:
            _now = time.time()
            _wend = s.arousal.maybe_end_climax(_now)
            if _wend == "resolved":
                s.arousal.decay(max(0.0, _now - s.arousal._resolved_at))
            else:
                s.arousal.decay(max(0.0, _now - float(saved_at)))
        s.last_event_at = time.time()
        return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--event-json", default=None)
    ap.add_argument("--modality", default="touch")
    ap.add_argument("--region", default="arms")
    ap.add_argument("--quality", default="touch")
    ap.add_argument("--pressure", type=float, default=0.5)
    ap.add_argument("--tempo", type=float, default=0.5)
    ap.add_argument("--valence", type=float, default=0.5)
    args = ap.parse_args()

    if args.event_json:
        event = json.loads(args.event_json)
    else:
        event = {
            "modality": args.modality,
            "region": args.region,
            "quality": args.quality,
            "pressure": args.pressure,
            "tempo": args.tempo,
            "valence": args.valence,
        }
    Session().sense(event)


if __name__ == "__main__":
    main()
