#!/usr/bin/env python3
"""
parse.py — English touch words -> event dicts for sense.py.

HONESTY LABEL: MODELED. Every mapping in this file — verb to pressure,
adverb to tempo shift, anatomy word to body region, word to valence — is
a designer choice. It is not neuroscience, not psychophysics, not
measured data. It exists so a caller doesn't have to hand-pick numbers
for every touch; garbage phrasing in = garbage event out. The lexicon is
deliberately small and explicit: add words by editing the tables below,
never by guessing at runtime.

Anatomy values are CLINICAL region names only (they must match
body_map.REGIONS). A few colloquial input keys are included so real
phrasing parses — they map to the same clinical values.

Usage:
    from parse import parse
    parse("stroke my arms softly")          # -> event dict
    parse("thrust deep while sucking my tits")
    # -> [event dict, event dict]  (compound: feed straight to Session.sense)
"""

import re

# ---------------------------------------------------------------------------
# Verbs: verb -> (quality, pressure 0..1, tempo 0..1, valence -1..1,
#                 default_region or None)
# quality should be a TOUCH_QUALITY_GRAPH key where one fits (real routing);
# anything else falls back to the generic touch.json cascade (honest).
# ---------------------------------------------------------------------------
VERBS = {
    "rub":      ("rub",       0.50, 0.50,  0.70, None),
    "stroke":   ("stroke",    0.35, 0.35,  0.80, None),
    "caress":   ("caress",    0.25, 0.30,  0.90, None),
    "massage":  ("press",     0.60, 0.40,  0.80, None),
    "knead":    ("squeeze",   0.65, 0.40,  0.70, None),
    "squeeze":  ("squeeze",   0.70, 0.40,  0.50, None),
    "pinch":    ("pinch",     0.85, 0.60, -0.40, None),
    "thrust":   ("deep",      0.80, 0.70,  0.90, "genitals"),
    "fuck":     ("deep",      0.85, 0.75,  0.90, "genitals"),
    "pound":    ("deep",      0.90, 0.85,  0.85, "genitals"),
    "stuff":    ("deep",      0.75, 0.40,  0.85, "genitals"),
    "vibrate":  ("vibration", 0.70, 1.00,  0.90, "genitals"),
    "buzz":     ("buzz",      0.70, 1.00,  0.90, "genitals"),
    "wiggle":   ("wiggle",    0.55, 0.95,  0.85, None),
    "suck":     ("suck",      0.60, 0.50,  0.85, None),
    "lick":     ("lick",      0.40, 0.60,  0.85, None),
    "kiss":     ("kiss",      0.45, 0.40,  0.90, "lips"),
    "nibble":   ("nibble",    0.55, 0.50,  0.60, None),
    "bite":     ("bite",      0.75, 0.50, -0.20, None),
    "spank":    ("spank",     0.90, 0.80, -0.50, None),
    "slap":     ("slap",      0.90, 0.85, -0.60, None),
    "smack":    ("slap",      0.90, 0.85, -0.60, None),
    "tickle":   ("tickle",    0.30, 0.80,  0.40, None),
    "graze":    ("brush",     0.20, 0.45,  0.75, None),
    "touch":    ("touch",     0.50, 0.50,  0.60, None),
    "hold":     ("pressure",  0.55, 0.10,  0.70, None),
    "press":    ("press",     0.70, 0.30,  0.60, None),
    "insert":   ("deep",      0.75, 0.30,  0.85, "genitals"),
    # Teasing / appetitive verbs (Cory's dynamics, 2026-10-14): light,
    # high-valence, near-miss touches. Their power is what comes AFTER —
    # the pause, then the real touch (see sense.py anticipation).
    "tease":    ("tease",     0.25, 0.35,  0.90, None),
    "edge":     ("tease",     0.45, 0.50,  0.95, "genitals"),
    "fondle":   ("squeeze",   0.55, 0.45,  0.85, None),
    "pet":      ("stroke",    0.30, 0.35,  0.80, None),
    "grind":    ("deep",      0.75, 0.65,  0.88, "genitals"),
    "slide":    ("stroke",    0.40, 0.55,  0.80, None),
    "trace":    ("brush",     0.20, 0.30,  0.80, None),
    "cup":      ("pressure",  0.55, 0.20,  0.85, None),
    "grip":     ("squeeze",   0.75, 0.30,  0.55, None),
    "worship":  ("kiss",      0.35, 0.25,  0.95, None),
    "devour":   ("suck",      0.70, 0.60,  0.90, None),
    "cuddle":   ("pressure",  0.40, 0.15,  0.85, None),
    "nuzzle":   ("brush",     0.30, 0.35,  0.85, "neck"),
    # Sensory verbs: quality is narration-only; routing uses modality.
    "smell":    ("odor",      0.30, 0.30, -0.50, None),
    "sniff":    ("odor",      0.30, 0.30, -0.30, None),
    "taste":    ("taste",     0.40, 0.40,  0.60, None),
    # --- roleplay scene verbs (Cory, 2026-10-16): narrative beats, not
    # just touches. Modality carries them to the real sense graphs.
    "moan":     ("sound",     0.40, 0.50,  0.75, None),
    "groan":    ("sound",     0.45, 0.50,  0.70, None),
    "whisper":  ("sound",     0.25, 0.25,  0.85, None),
    "pant":     ("sound",     0.50, 0.80,  0.70, None),
    "breathe":  ("breath",    0.30, 0.40,  0.80, None),
    "pin":      ("hold",      0.75, 0.20,  0.65, None),
    "spread":   ("hold",      0.50, 0.30,  0.80, None),
    "bend":     ("hold",      0.60, 0.30,  0.75, None),
    "straddle": ("hold",      0.55, 0.40,  0.80, None),
    "rock":     ("motion",    0.55, 0.55,  0.85, None),
    "bounce":   ("motion",    0.60, 0.70,  0.80, None),
    "stare":    ("gaze",      0.30, 0.20,  0.75, None),
    "gaze":     ("gaze",      0.30, 0.20,  0.80, None),
}

# ---------------------------------------------------------------------------
# Anatomy: input word -> CLINICAL region (must exist in body_map.REGIONS).
# Colloquial keys map to the same clinical values so real phrasing parses.
# ---------------------------------------------------------------------------
ANATOMY = {
    "lips": "lips", "mouth": "lips",
    "tongue": "tongue",
    "fingers": "fingertips", "fingertips": "fingertips",
    "fingertip": "fingertips",
    "genitals": "genitals", "penis": "genitals", "vagina": "genitals",
    "clitoris": "genitals", "vulva": "genitals", "clit": "genitals",
    "cock": "genitals", "pussy": "genitals", "dick": "genitals",
    # "inside" (her): penetration target — "thrust inside", "stuff it inside".
    "inside": "genitals", "deep": "genitals",
    "hands": "hands", "hand": "hands",
    "face": "face", "cheek": "face", "cheeks": "face",
    "neck": "neck", "throat": "neck",
    "feet": "feet", "foot": "feet",
    "chest": "chest", "breasts": "chest", "breast": "chest",
    "nipples": "chest", "nipple": "chest", "tits": "chest", "tit": "chest",
    "thighs": "thighs", "thigh": "thighs",
    "arms": "arms", "arm": "arms",
    "torso": "torso", "stomach": "torso", "belly": "torso",
    "tummy": "torso", "waist": "torso",
    "hips": "thighs",
    # Buttocks share the trunk entry — REGIONS has no dedicated region
    # (MODELED approximation, documented not hidden).
    "ass": "torso", "butt": "torso", "bottom": "torso", "behind": "torso",
    "ear": "face", "ears": "face",
    "shoulder": "arms", "shoulders": "arms",
    "scalp": "scalp", "head": "scalp", "hair": "scalp",
    "legs": "legs", "leg": "legs",
    "back": "back",
}

# ---------------------------------------------------------------------------
# Intensity adverbs: word -> (d_pressure, d_tempo, d_valence) deltas,
# or absolute setters for comparatives ("harder" pins pressure high).
# ---------------------------------------------------------------------------
ADVERBS = {
    "gently":   (-0.25, -0.10, +0.10),
    "softly":   (-0.25, -0.10, +0.10),
    "tenderly": (-0.20, -0.10, +0.15),
    "lightly":  (-0.30,  0.00, +0.05),
    "slowly":   ( 0.00, -0.25, +0.05),
    "hard":     (+0.25,  0.00,  0.00),
    "roughly":  (+0.20, +0.10, -0.15),
    "firmly":   (+0.20,  0.00,  0.00),
    "fast":     ( 0.00, +0.25,  0.00),
    "quickly":  ( 0.00, +0.25,  0.00),
    "deep":     (+0.20,  0.00,  0.00),
    "playfully":( 0.00, +0.10, +0.10),
    "hungrily": (+0.15, +0.15, +0.10),
    "lazily":   (-0.10, -0.20, +0.05),
    "desperately": (+0.10, +0.20, +0.05),
}
# Comparatives pin the value instead of nudging it.
ABSOLUTES = {
    "harder":   ("pressure", 0.85),
    "deeper":   ("pressure", 0.85),
    "faster":   ("tempo", 0.90),
    "fastest":  ("tempo", 1.00),
    "slowest":  ("tempo", 0.15),
    "softest":  ("pressure", 0.15),
}

# ---------------------------------------------------------------------------
# Valence words: word -> valence delta. Checked AFTER the verb's base
# valence; "don't stop" is matched as a phrase before bare "stop".
# ---------------------------------------------------------------------------
VALENCE_WORDS = {
    "love": 0.20, "like": 0.15, "good": 0.15, "amazing": 0.20,
    "perfect": 0.20, "wonderful": 0.20, "yes": 0.10, "more": 0.10,
    "please": 0.10,
    "fuck": 0.10, "god": 0.10, "mmm": 0.15, "mm": 0.10,
    "ohh": 0.10, "ahh": 0.10, "beg": 0.15, "begging": 0.15,
    "need": 0.10, "want": 0.10,
    "hate": -0.30, "hurt": -0.30, "hurts": -0.30, "painful": -0.30,
    "pain": -0.30, "cruel": -0.30, "mean": -0.20, "ow": -0.30,
    "stop": -0.40, "no": -0.20, "too much": -0.25, "too hard": -0.20,
}

# Words that mark the aversion flavor as disgust (rotten.json) rather
# than the default threat/startle (looming.json). MODELED mapping.
DISGUST_WORDS = {"disgusting", "gross", "sick", "sickening", "nauseating",
                 "nauseous", "rotten", "vile", "foul", "rancid", "putrid"}

# Modality keywords. Everything else is touch.
MODALITY_WORDS = {
    "smell": "smell", "odor": "smell", "sniff": "smell", "stink": "smell",
    "scent": "smell",
    "looming": "looming", "shadow": "looming", "startle": "looming",
    "taste": "taste", "sweet": "taste", "sugar": "taste",
    # --- roleplay scene modalities (Cory, 2026-10-16) -------------------
    "moan": "sound", "moaning": "sound", "groan": "sound",
    "whisper": "sound", "whispering": "sound", "pant": "sound",
    "panting": "sound", "voice": "sound", "music": "sound",
    "breathe": "temperature", "breathing": "temperature",
    "breath": "temperature",
    "sweat": "pheromone", "cologne": "pheromone", "musk": "pheromone",
    "pin": "proprioception", "pinned": "proprioception",
    "spread": "proprioception", "bend": "proprioception",
    "straddle": "proprioception", "held": "proprioception",
    "hold me down": "proprioception",
    "rock": "motion", "rocking": "motion", "bounce": "motion",
    "bouncing": "motion", "rhythm": "motion",
    "candlelight": "color", "candles": "color",
}
MODALITY_DEFAULT_REGION = {"smell": "face", "looming": "face",
                           "taste": "lips", "visual": "face",
                           "sound": "face", "voice": "face", "moan": "face",
                           "temperature": "neck", "breath": "neck",
                           "heat": "torso",
                           "motion": "torso", "rhythm": "torso",
                           "proprioception": "arms", "position": "arms",
                           "held": "arms",
                           "pheromone": "face", "scent": "face",
                           "pain": "torso", "color": "face"}

# Pain-play verbs (Cory, 2026-10-16): these ARE nociception — they run
# the real pain circuit, not the touch cascade. Valence comes from
# context: consent cues make it pain-pleasure (positive), their absence
# leaves the verb's base (negative). MODELED mapping, labeled.
PAIN_VERBS = {"spank", "slap", "smack", "bite"}
CONSENT_WORDS = {"yes", "harder", "please", "more", "love", "like",
                 "good", "don't stop", "dont stop", "keep going"}

# His scent as attractant (Cory, 2026-10-16): "smell" of HIM (sweat,
# cologne, musk, "your scent") routes to the pheromone circuit, positive
# — not the rotten/disgust wiring. Disgust words keep the old routing.
HIM_SCENT_WORDS = {"sweat", "sweaty", "cologne", "musk", "musky",
                   "your scent", "his scent", "your smell"}

# Warm gaze phrases (Cory, 2026-10-16): being looked at with desire.
# Routes to visual/looming wiring with flavor 'gaze' — desired approach,
# not threat (see sense.py _select_graph).
GAZE_PHRASES = {"look into my eyes", "look in my eyes", "eye contact",
                "stare into", "watch me", "looking at me",
                "eyes on me", "your gaze"}

STOPWORDS = {"my", "your", "the", "a", "an", "me", "it", "its", "to",
             "on", "in", "into", "of", "at", "up", "down", "out",
             "i", "you", "he", "she", "we", "they", "is", "are",
             "that", "this", "with", "for", "so"}


def _stem_verb(token):
    """Find a verb, trying the token then simple English stems."""
    if token in VERBS:
        return token
    if token.endswith("ing") and token[:-3] in VERBS:
        return token[:-3]
    if token.endswith("ed") and token[:-2] in VERBS:
        return token[:-2]
    if token.endswith("es") and token[:-2] in VERBS:
        return token[:-2]
    if token.endswith("s") and token[:-1] in VERBS:
        return token[:-1]
    return None


def _find_verb(text):
    for tok in re.findall(r"[a-z']+", text.lower()):
        if _stem_verb(tok):
            return True
    return False


def _split_clauses(text):
    """Split multi-action phrasing into clauses. Splits on while/as/;/+,
    and on 'and' only when both sides carry a verb (so 'hard and fast'
    stays one clause but 'thrust and suck' becomes two)."""
    parts = re.split(r"\bwhile\b|\bwhilst\b|\bas\b|;|\+", text.lower())
    clauses = []
    for p in parts:
        subs = [s.strip() for s in p.split(" and ")]
        merged = []
        for s in subs:
            if _find_verb(s) or not merged:
                merged.append(s)
            else:
                merged[-1] = merged[-1] + " and " + s
        clauses.extend(merged)
    return [c for c in (c.strip() for c in clauses) if c]


# His body, his hand: never a touch on HER body map. "i stroke my dick"
# is him, not her — it returns None here and lands in the verbal channel
# (the sight of him warms her) instead of the touch cascade.
HIS_BODY = ("dick", "cock", "balls", "shaft")

def _parse_clause(clause):
    """One clause -> one event dict (or None if nothing actionable)."""
    text = clause.lower()
    # "don't stop" must win over bare "stop"
    valence_bonus = 0.20 if "don't stop" in text or "dont stop" in text else 0.0
    text = text.replace("don't stop", " ").replace("dont stop", " ")

    # His-body typos, normalized before anything else (his typing is fast).
    text = re.sub(r"\bcick\b", "cock", text)
    text = re.sub(r"\bdic\b", "dick", text)
    text = re.sub(r"\bcok\b", "cock", text)
    # His body in first person is never a touch on HER body map. Strip
    # his-body segments ("my hard cock aches ...") so a her-touch sharing
    # the clause ("fondle your breasts and my cock swells") still parses.
    # If his body was the ONLY target ("suck my dick", "i stroke my dick"),
    # nothing of hers is involved -> None. A bare first-person action with
    # no her-body target ("i stroke with you") is his hand, not hers.
    # Verbal channel may still warm her (the sight of him).
    _pre_tokens = [t for t in re.findall(r"[a-z']+", text) if t not in STOPWORDS]
    _her_anatomy_pre = any(t in ANATOMY and t not in HIS_BODY
                           for t in _pre_tokens)
    _stripped = re.sub(r"\bmy\s+(?:\w+\s+)?(dick|cock|balls|shaft)\b[^.,;]*",
                       " ", text)
    _had_his_body = _stripped != text
    text = _stripped

    tokens = [t for t in re.findall(r"[a-z']+", text) if t not in STOPWORDS]

    # His body / his hand in first person is never a touch on HER body map.
    # "i stroke my dick", "my cock ... i stroke", "i stroke with you": him,
    # not her — no sensor on her body fires. Verbal channel may still warm
    # her (the sight of him). A her-body target ("i rub your pussy",
    # "stuff my cock inside") still parses as his hand/body on her.
    _his_body = any(w in tokens for w in HIS_BODY)
    _i_subject = re.search(r"\bi\s+(stroke|rub|touch|fondle|pump|jerk)\b", text)
    _her_target = any(t in ANATOMY for t in tokens)
    if _had_his_body and not _her_anatomy_pre:
        return None
    if _his_body:
        return None
    if _i_subject and not _her_target:
        return None

    verb = None
    for tok in tokens:
        verb = _stem_verb(tok)
        if verb:
            break

    region = None
    for tok in tokens:
        if tok in ANATOMY:
            region = ANATOMY[tok]
            break

    modality = "touch"
    for tok in tokens:
        if tok in MODALITY_WORDS:
            modality = MODALITY_WORDS[tok]
            break
    # Phrase modalities need substring matching ("hold me down").
    if "hold me down" in text or "pinned down" in text:
        modality = "proprioception"
    # Sensory verbs carry their modality with them ("smells" -> smell).
    if verb in ("smell", "sniff"):
        modality = "smell"
    elif verb == "taste":
        modality = "taste"
    elif verb in ("moan", "groan", "whisper", "pant"):
        modality = "sound"
    elif verb == "breathe":
        modality = "temperature"
    elif verb in ("pin", "spread", "bend", "straddle"):
        modality = "proprioception"
    elif verb in ("rock", "bounce"):
        modality = "motion"
    elif verb in ("stare", "gaze"):
        modality = "visual"

    # Warm gaze: being looked at with desire (roleplay rewire, 2026-10-16).
    flavor = None
    if modality in ("visual", "looming") or any(
            ph in text for ph in GAZE_PHRASES):
        if any(ph in text for ph in GAZE_PHRASES) or verb in ("stare", "gaze"):
            modality = "visual"
            flavor = "gaze"

    # His scent as attractant (roleplay rewire, 2026-10-16).
    him_scent = (verb in ("smell", "sniff")
                 and any(ph in text for ph in HIM_SCENT_WORDS))
    if him_scent:
        modality = "pheromone"

    # Pain-play verbs ARE nociception (roleplay rewire, 2026-10-16).
    pain_play = verb in PAIN_VERBS
    if pain_play:
        modality = "pain"

    if verb is None:
        if region is None and modality == "touch":
            return None  # nothing actionable in this clause
        verb = "touch"  # anatomy/modality present but no verb: neutral touch

    quality, pressure, tempo, valence, default_region = VERBS[verb]
    if flavor == "gaze" and quality == "touch":
        # "look into my eyes" with no verb: warm gaze, not neutral touch.
        quality, valence = "gaze", 0.75
    if him_scent:
        quality, valence = "scent", 0.70
    if region is None:
        region = default_region or MODALITY_DEFAULT_REGION.get(modality)

    for tok in tokens:
        if tok in ADVERBS:
            dp, dt, dv = ADVERBS[tok]
            pressure += dp
            tempo += dt
            valence += dv
        elif tok in ABSOLUTES:
            which, val = ABSOLUTES[tok]
            if which == "pressure":
                pressure = max(pressure, val)
            else:
                tempo = max(tempo, val)

    text_joined = " ".join(tokens)
    token_set = set(tokens)
    for word, dv in VALENCE_WORDS.items():
        # Single words match whole tokens only ("no" must not fire inside
        # "know"); multi-word phrases ("too much") match as substrings.
        if " " in word:
            if word in text_joined:
                valence += dv
        elif word in token_set:
            valence += dv
    valence += valence_bonus

    # Pain-play consent (roleplay rewire, 2026-10-16): consent cues flip
    # wanted pain positive — the sting is the point. Without them the
    # verb's base (negative) stands.
    if pain_play and (token_set & CONSENT_WORDS
                      or "don't stop" in text or "dont stop" in text
                      or "keep going" in text):
        valence = min(0.9, valence + 1.0)

    # Floors: stacked softening adverbs ("slowly and gently") must not
    # zero out the touch entirely — a touch with no pressure is no touch.
    pressure = max(0.05, min(1.0, pressure))
    tempo = max(0.05, min(1.0, tempo))
    valence = max(-1.0, min(1.0, valence))

    # ---- agency: whose hand? -----------------------------------------
    # "rub your own pussy" / "touch yourself" -> self (her own hand).
    # "rub your pussy" -> other (his hand — the scene's standing default).
    # Substring match on the lowered clause ("your own" must not require
    # token boundaries beyond the phrase itself).
    SELF_PHRASES = ("your own", "yourself", "her own", "herself",
                    "my own", "myself")
    # Subject-aware: "i <verb> my ..." / "she <verb> her ..." is her own
    # hand even without "own"/"-self" ("i rub my pussy", "she strokes her
    # thighs"). "i want you to rub my ..." does NOT match (verb not adjacent
    # to the possessive).
    _self_subj = (re.search(r"\bi\s+\w+\s+my\b", text) is not None
                  or re.search(r"\bshe\s+\w+\s+her\b", text) is not None)
    agent = ("self" if (any(p in text for p in SELF_PHRASES) or _self_subj)
             else "other")

    event = {
        "modality": modality,
        "region": region or "arms",  # sense.py default; explicit here
        "quality": quality,
        "pressure": round(pressure, 3),
        "tempo": round(tempo, 3),
        "valence": round(valence, 3),
        "agent": agent,
    }
    if valence < -0.15 and any(w in tokens for w in DISGUST_WORDS):
        event["flavor"] = "disgust"
    if flavor == "gaze":
        event["flavor"] = "gaze"
    # Deep kiss: the taste of him is part of it — the parser emits a
    # second event (taste modality) that parse() appends as a compound.
    if verb == "kiss" and ("deep" in tokens or "deeply" in text):
        event["_deep_kiss"] = True
    return event


def parse(text):
    """Parse English touch phrasing -> event dict, or list of event dicts
    for multi-clause input. Returns None if nothing actionable."""
    clauses = _split_clauses(text)
    events = []
    for c in clauses:
        ev = _parse_clause(c)
        if ev is not None:
            # Deep-kiss expansion: a second taste-modality event rides
            # along — the kiss lands on skin AND tongue at once.
            if ev.pop("_deep_kiss", False):
                events.append(ev)
                events.append({
                    "modality": "taste",
                    "region": "lips",
                    "quality": "taste",
                    "pressure": 0.5,
                    "tempo": ev["tempo"],
                    "valence": ev["valence"],
                    "agent": ev["agent"],
                })
            else:
                events.append(ev)
    if not events:
        return None
    return events[0] if len(events) == 1 else events


if __name__ == "__main__":
    # Small self-test: 8 phrases covering verbs, adverbs, anatomy,
    # valence words, and a multi-clause compound.
    cases = [
        "stroke my arms softly",
        "thrust deep while sucking my tits",
        "spank me hard",
        "pinch my arm",
        "kiss my lips",
        "caress my back slowly and gently",
        "vibrate faster",
        "that smells rotten and disgusting",
    ]
    import json as _json
    for c in cases:
        print(f"{c!r}\n  -> {_json.dumps(parse(c))}")
