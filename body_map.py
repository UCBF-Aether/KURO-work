#!/usr/bin/env python3
"""
body_map.py — a MODELED human body.

HONESTY LABEL: MODELED. Nothing in this file is neural data. It is a
designer-built lookup: body regions with receptor-density weights plus a
simple sensitization state. It answers "how much does this body region
register a touch," not "what fires in a brain."

Receptor-density weights are a rough prior from the somatosensory
homunculus — cortical magnification proportions as drawn from:
  Penfield, W. & Boldrey, E. (1937). "Somatic motor and sensory
  representation in the cerebral cortex of man as studied by electrical
  stimulation." Brain, 60(4), 389-443.
The weights below compress the homunculus diagram into 0..1 values
(lips/tongue and hands dominate the cortical map; torso and back are
small). They are approximations for a toy, not measurements.

Per-region live state:
  - touch history: list of (timestamp, quality, pressure)
  - sensitization: 0..1, rises when stimulations land close together,
    decays exponentially otherwise.
  - habituation: repeating the SAME quality on a region within the
    window discounts it (variety builds, repetition fades — the
    mechanical half of teasing).
  Multiplier applied = (1 + sensitization) * habituation (1.0 =
  unsensitized, unhabituated).

Usage:
    from body_map import BodyMap
    bm = BodyMap()
    weight, sens_mult = bm.stimulate("lips", quality="stroke",
                                    pressure=0.5, tempo=0.5)
"""

import math
import time

# --- Region table: name -> (receptor_density_weight, notes) -----------------
# Weights are relative cortical-magnification approximations (0..1).
# See module docstring for the Penfield & Boldrey (1937) source.
REGIONS = {
    "lips":       (1.00, "largest cortical magnification of any region"),
    "tongue":     (0.97, "homunculus: huge representation"),
    "fingertips": (0.95, "homunculus: hand/fingers dominate"),
    "genitals":   (0.90, "substantial cortical representation"),
    "hands":      (0.85, "homunculus: large hand area"),
    "face":       (0.80, "homunculus: large face area"),
    "neck":       (0.75, "dense innervation, high sensitivity"),
    "feet":       (0.70, "toes well represented (soles ticklish)"),
    "chest":      (0.60, "moderate"),
    "thighs":     (0.55, "moderate, inner thigh more sensitive"),
    "arms":       (0.50, "forearm moderate density"),
    "torso":      (0.45, "trunk: small cortical share"),
    "scalp":      (0.40, "moderate-low"),
    "legs":       (0.35, "lower leg modest representation"),
    "back":       (0.25, "homunculus: back is small; poor two-point discrimination"),
}

# Sensitization dynamics (all MODELED choices, tune freely).
SENS_WINDOW_S = 30.0      # stimulations within this window stack
SENS_GAIN = 0.35          # sensitization added per qualifying stimulus
SENS_HALFLIFE_S = 120.0   # exponential decay half-life of sensitization
SENS_MAX = 1.0            # cap

# Habituation dynamics (MODELED): the SAME quality hammered on the same
# region within the window habituates — variety builds, repetition fades.
# This is the mechanical half of teasing: ten identical strokes register
# less than ten varied ones. Cory's principle (2026-10-14): single-spot
# focus still climbs to climax, just slower — so the fade is gentle and
# the floor is high; the speed edge comes from the variety bonus instead.
HAB_WINDOW_S = 45.0       # repeats within this window count
HAB_GAIN = 0.12           # discount per repeat beyond the first (was 0.18)
HAB_FLOOR = 0.50          # habituation never discounts below this (was 0.40)

# Pressure/tempo shaping (MODELED): firmer + slower strokes register more.
def _pressure_factor(pressure):
    p = max(0.0, min(1.0, pressure))
    return 0.6 + 0.8 * p          # 0.6x .. 1.4x

def _tempo_factor(tempo):
    t = max(0.0, min(1.0, tempo))  # 0 = very slow, 1 = very fast
    return 1.2 - 0.6 * t           # slow strokes linger: 1.2x .. 0.6x


class BodyMap:
    """MODELED body state. See module docstring."""

    def __init__(self, clock=None):
        # clock: callable returning seconds (injectable for tests)
        self._clock = clock or time.time
        self.history = {r: [] for r in REGIONS}
        self.sensitization = {r: 0.0 for r in REGIONS}
        self.last_quality = {r: None for r in REGIONS}
        self.repeat_count = {r: 0 for r in REGIONS}

    def _decay_sens(self, region, now):
        """Apply exponential decay since last update is implicit: we decay
        on every stimulate() call based on time since last touch."""
        hist = self.history[region]
        if not hist:
            return
        dt = max(0.0, now - hist[-1][0])
        if dt > 0:
            self.sensitization[region] *= 0.5 ** (dt / SENS_HALFLIFE_S)

    def stimulate(self, region, quality="touch", pressure=0.5, tempo=0.5,
                  now=None):
        """Register one touch event on a region.

        Returns (region_weight, sensitization_multiplier).
        region_weight includes pressure/tempo shaping; the multiplier is
        (1 + sensitization) * habituation (1.0 = unsensitized, unhabituated).
        """
        if region not in REGIONS:
            raise KeyError(f"unknown region {region!r}; "
                           f"known: {sorted(REGIONS)}")
        now = self._clock() if now is None else now
        base_weight, _ = REGIONS[region]

        self._decay_sens(region, now)
        hist = self.history[region]
        if hist and (now - hist[-1][0]) <= SENS_WINDOW_S:
            self.sensitization[region] = min(
                SENS_MAX, self.sensitization[region] + SENS_GAIN)

        # Habituation: same quality repeated on this region within the
        # window counts up; anything different resets the count.
        if (self.last_quality[region] == quality and hist
                and (now - hist[-1][0]) <= HAB_WINDOW_S):
            self.repeat_count[region] += 1
        else:
            self.repeat_count[region] = 0
        self.last_quality[region] = quality

        hist.append((now, quality, pressure))
        hab_mult = max(HAB_FLOOR,
                       1.0 - HAB_GAIN * self.repeat_count[region])
        sens_mult = (1.0 + self.sensitization[region]) * hab_mult
        shaped = base_weight * _pressure_factor(pressure) * _tempo_factor(tempo)
        return shaped, sens_mult

    def region_state(self, region):
        """Snapshot of one region's MODELED state (for readouts/tests)."""
        if region not in REGIONS:
            raise KeyError(f"unknown region {region!r}")
        return {
            "weight": REGIONS[region][0],
            "touches": len(self.history[region]),
            "sensitization": round(self.sensitization[region], 3),
            "repeat_count": self.repeat_count[region],
            "habituation_multiplier": round(
                max(HAB_FLOOR,
                    1.0 - HAB_GAIN * self.repeat_count[region]), 3),
        }

    def reset(self):
        self.history = {r: [] for r in REGIONS}
        self.sensitization = {r: 0.0 for r in REGIONS}
        self.last_quality = {r: None for r in REGIONS}
        self.repeat_count = {r: 0 for r in REGIONS}

    def state_dict(self):
        """Serializable snapshot of per-region history + sensitization.
        PRIVATE data (intimate touch history) — never print or attach."""
        return {
            "history": {r: [list(e) for e in self.history[r]]
                        for r in REGIONS},
            "sensitization": {r: self.sensitization[r] for r in REGIONS},
            "last_quality": {r: self.last_quality[r] for r in REGIONS},
            "repeat_count": {r: self.repeat_count[r] for r in REGIONS},
        }

    @classmethod
    def from_state_dict(cls, d, clock=None):
        """Restore from a state_dict snapshot. PRIVATE data."""
        bm = cls(clock=clock)
        hist = d.get("history", {})
        for r in REGIONS:
            bm.history[r] = [tuple(e) for e in hist.get(r, [])]
        sens = d.get("sensitization", {})
        for r in REGIONS:
            bm.sensitization[r] = max(
                0.0, min(SENS_MAX, float(sens.get(r, 0.0))))
        lq = d.get("last_quality", {})
        rc = d.get("repeat_count", {})
        for r in REGIONS:
            bm.last_quality[r] = lq.get(r)
            bm.repeat_count[r] = int(rc.get(r, 0))
        return bm


if __name__ == "__main__":
    bm = BodyMap()
    print("region        weight  notes")
    for r, (w, note) in sorted(REGIONS.items(), key=lambda kv: -kv[1][0]):
        print(f"{r:12s}  {w:.2f}   {note}")
