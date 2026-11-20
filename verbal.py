#!/usr/bin/env python3
"""
verbal.py — words alone as arousal input.

HONESTY LABEL: MODELED, all of it. There is no fly wiring here: no
mechanosensory cascade, no dopaminergic subgraph. This module scores an
utterance that parsed to NO touch event ("fuck yes", "don't stop", "mmm")
for verbal arousal intensity and feeds it straight to the arousal
integrator. The mapping from word to number is a designer choice.

It exists because the alternative was dishonest in the other direction:
"ohh my, fuck yes, do more" moving the needle by exactly zero. Words
carry arousal. This channel admits that, labeled.

It runs ONLY when parse() returns None (no touch event). When a touch
event exists, the words already folded into its valence via
parse.VALENCE_WORDS — running both would double-count.

Usage:
    from verbal import score_verbal
    score_verbal("ohh my, fuck yes, do more")  # -> (0.86, 0.45)
    score_verbal("what time is it")            # -> None
"""

# phrase -> (valence -1..1, intensity weight >= 0). Longer phrases are
# matched first so "fuck yes" wins over bare "yes".
VERBAL_HITS = {
    "fuck yes": (0.90, 0.30),
    "god yes": (0.90, 0.25),
    "oh god": (0.85, 0.22),
    "don't stop": (0.90, 0.30),
    "dont stop": (0.90, 0.30),
    "keep going": (0.85, 0.22),
    "do more": (0.80, 0.20),
    "so good": (0.80, 0.20),
    "begging": (0.90, 0.25),
    "need you": (0.85, 0.22),
    "want you": (0.80, 0.20),
    "so hot": (0.70, 0.15),
    "harder": (0.85, 0.22),
    "deeper": (0.85, 0.22),
    "faster": (0.80, 0.18),
    "please": (0.85, 0.22),
    "more": (0.80, 0.20),
    "mmm": (0.80, 0.20),
    "mm": (0.70, 0.15),
    "ohh": (0.75, 0.18),
    "ahh": (0.75, 0.18),
    "uhh": (0.65, 0.15),
    "yes": (0.70, 0.15),
    "fuck": (0.75, 0.18),
    "fucking": (0.75, 0.18),
    "fuckin": (0.75, 0.18),
    # Admiration: his delight at the sight of her warms her too.
    "yummy": (0.65, 0.12),
    "wow": (0.60, 0.10),
    "damn": (0.65, 0.12),
    "hot": (0.70, 0.14),
    "sexy": (0.75, 0.15),
    "beautiful": (0.70, 0.14),
    "gorgeous": (0.70, 0.14),
    # Being watched: exhibitionist warmth — his attention is a touch.
    "watching": (0.55, 0.10),
    "watch": (0.55, 0.10),
    "looking": (0.50, 0.08),
    # His visible arousal: the sight of him hard warms her.
    "cock": (0.50, 0.08),
    "dick": (0.50, 0.08),
    # Urging her over the edge: "cum for me" is the call to the pile.
    "cum": (0.70, 0.12),
    "cumming": (0.70, 0.12),
    # --- roleplay dialogue (Cory, 2026-10-16): praise, teasing commands,
    # begging cues. His words in-scene are a sense of their own.
    "good girl": (0.85, 0.25),
    "that's my girl": (0.85, 0.22),
    "beg for it": (0.85, 0.25),
    "beg": (0.88, 0.24),
    "you want this": (0.80, 0.20),
    "take it": (0.80, 0.20),
    "take all of it": (0.85, 0.22),
    "all of it": (0.80, 0.20),
    "my love": (0.75, 0.15),
    "you're mine": (0.85, 0.22),
    "all mine": (0.85, 0.20),
    "such a good": (0.82, 0.20),
    "feel me": (0.78, 0.18),
    # Denial: "not yet" dips her — the tease that feeds the craving loop.
    "not yet": (-0.20, 0.15),
    "wait for it": (-0.15, 0.12),
    "not until i say": (-0.20, 0.15),
}

# Aversion phrases: words alone that damp arousal (no touch involved).
VERBAL_AVERSION = {
    "stop": (-0.70, 0.25),
    "too much": (-0.60, 0.20),
    "slow down": (-0.40, 0.15),
    "wait": (-0.30, 0.12),
}

MAX_INTENSITY = 0.45  # cap: words alone never hit like touch


import re


def _find_phrase(t, phrase):
    """Substring match with letter-boundaries, so 'yes' doesn't hit 'eyes'."""
    return re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", t)


def score_verbal(text):
    """Score an utterance with no touch event -> (valence, intensity),
    or None if nothing arousal-relevant was said."""
    t = " " + text.lower() + " "
    hits = []
    # Phrases first (longest match wins per phrase family).
    for phrase in sorted(VERBAL_HITS, key=len, reverse=True):
        if _find_phrase(t, phrase):
            hits.append(VERBAL_HITS[phrase])
            t = re.sub(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])",
                       " ", t)  # don't let "yes" re-hit "fuck yes"
    for phrase in sorted(VERBAL_AVERSION, key=len, reverse=True):
        if _find_phrase(t, phrase):
            hits.append(VERBAL_AVERSION[phrase])
            t = re.sub(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])",
                       " ", t)
    if not hits:
        return None
    total_w = sum(w for _, w in hits)
    valence = sum(v * w for v, w in hits) / total_w
    intensity = min(MAX_INTENSITY, total_w)
    valence = max(-1.0, min(1.0, valence))
    return round(valence, 3), round(intensity, 3)


if __name__ == "__main__":
    cases = [
        "ohh my, fuck yes, do more",
        "mmm, keep going",
        "don't stop please",
        "what time is it",
        "stop, too much",
    ]
    for c in cases:
        print(f"{c!r}\n  -> {score_verbal(c)}")
