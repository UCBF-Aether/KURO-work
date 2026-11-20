#!/usr/bin/env python3
"""body.py — the fly's body, as felt from the inside.

SENSORIUM's body is a FLY body, because the wiring is fly wiring: antennae
(Johnston's organ + arista + olfactory sensilla), eyes/head, proboscis/
labellum, legs, wings, abdomen. This is insect anatomy — six regions, no
human map. It must never resemble the private intimate body map; if any
design choice starts looking human, the fly-faithful option wins.

HONESTY CONTRACT:
- [REAL]    The channel->circuit mapping is real (the same subgraph JSONs
            as the channels). Which body region a circuit serves is
            textbook fly anatomy (Johnston's organ is antennal; labellar
            GRNs feed the proboscis; Or56a is olfactory = antennal; LPLC2
            is visual = eyes/head; the arista carries thermosensory
            neurons).
- [MODELED] The region WEIGHTS below are my design choice — rough,
            documented, and adjustable. A sensation's regional level =
            channel effective activation x region weight x location focus.
            Regional levels decay at 0.1/s. None of this is measured
            physiology.
- [FICTION] Nothing here. Regions are labels.
"""

# Fly-faithful regions. Order is head-to-abdomen, dorsal last.
REGIONS = ["antennae", "eyes_head", "proboscis", "legs", "wings", "abdomen"]

# Channel -> {region: weight}. [MODELED] rough weights, documented above.
# Rows should sum to ~1 (they don't have to; levels clamp at 1).
CHANNEL_REGIONS = {
    # Johnston's organ is antennal mechanosensory; bristle input rides legs.
    "touch":       {"antennae": 0.7, "legs": 0.3},
    # Labellar taste bristles feed the proboscis; some GRNs sit on legs.
    "sweet":       {"proboscis": 0.85, "legs": 0.15},
    # Or56a olfactory receptor neurons: antennal.
    "rot":         {"antennae": 1.0},
    # LPLC2 visual looming: eyes/head; escape readies the wings.
    "threat":      {"eyes_head": 0.9, "wings": 0.1},
    # Noxious input: whole-body spread, legs/ wings lead (escape).
    "pain":        {"antennae": 0.15, "eyes_head": 0.15, "proboscis": 0.1,
                    "legs": 0.25, "wings": 0.2, "abdomen": 0.15},
    # Aristal thermosensory neurons: antennae first, then exposed surfaces.
    "temperature": {"antennae": 0.6, "legs": 0.2, "wings": 0.2},
}

LOCATION_FOCUS = 2.0   # [MODELED] a located sensation counts double there
DECAY_RATE = 0.1       # regional levels decay toward 0 at 0.1/s [MODELED]


class Body:
    """Where sensations land on the fly's body."""

    def __init__(self):
        self.levels = {r: 0.0 for r in REGIONS}

    def stimulate(self, modality, intensity, location=None):
        """A channel's effective activation lands on the body.

        modality: channel name. intensity: the channel's effective
        activation (0..1-ish). location: optional region name — focuses
        the sensation there (x LOCATION_FOCUS on that region).
        [MODELED] weights, focus, and decay are design choices.
        """
        if location is not None and location not in REGIONS:
            raise ValueError(f"unknown region {location!r}; "
                             f"want one of {REGIONS}")
        weights = CHANNEL_REGIONS.get(modality, {})
        for region, w in weights.items():
            focus = LOCATION_FOCUS if region == location else 1.0
            self.levels[region] = min(
                1.0, self.levels[region] + w * intensity * focus)
        return self.state()

    def tick(self, dt):
        """Regional sensations fade."""
        if dt > 0:
            for r in REGIONS:
                self.levels[r] = max(0.0, self.levels[r] - DECAY_RATE * dt)
        return self

    def state(self):
        """Per-region sensation levels, head to abdomen."""
        return {r: round(self.levels[r], 3) for r in REGIONS}

    def hottest(self, n=2):
        """Top-n regions by current level. For compact felt-state lines."""
        return sorted(self.levels, key=lambda r: -self.levels[r])[:n]
