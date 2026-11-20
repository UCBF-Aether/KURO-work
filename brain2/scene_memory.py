#!/usr/bin/env python3
"""scene_memory.py — [BRAIN2-ENHANCEMENT] the eye remembers the ground.

The fly does figure-ground: it knows what moves against what stays.
Scene memory is the upgrade: a running background model of the static
scene, learned over minutes. What's new — a parked car that wasn't
there, a door now open — stands out as NOVEL, not just moving.

EMA background of the luminance field; per-facet novelty = distance
from the learned background. Slow to learn (minutes), quick to notice
(seconds). The eye stops seeing only now; it knows what belongs.
"""

import numpy as np

try:
    from PIL import Image
    _PIL = True
except ImportError:
    _PIL = False


class SceneMemory:
    """Running background model → novelty field.

    feed(luma): update the background with a luminance field (any shape;
                resampled to the model's grid on first feed).
    novelty(luma): per-cell 0..1 novelty vs the learned background.
    describe(): one-line read of what's novel.
    """

    LEARN_ALPHA = 0.005   # background EMA — slow (~minutes at 10Hz)
    NOVEL_THRESH = 0.12   # luminance distance that counts as novel

    def __init__(self, grid=(24, 18)):
        self.grid = grid  # (gw, gh)
        self.bg = None
        self._n = 0

    def _to_grid(self, luma):
        gw, gh = self.grid
        a = np.asarray(luma, dtype=np.float64)
        if not _PIL:
            return None
        im = Image.fromarray(
            (np.clip(a, 0, 1) * 255).astype(np.uint8)).resize(
                (gw, gh), Image.BILINEAR)
        return np.asarray(im).astype(np.float64) / 255.0

    def feed(self, luma):
        """Fold one luminance field into the background model."""
        g = self._to_grid(luma)
        if g is None:
            return
        if self.bg is None:
            self.bg = g.copy()
        else:
            a = self.LEARN_ALPHA
            self.bg += a * (g - self.bg)
        self._n += 1

    def novelty(self, luma):
        """Per-cell novelty 0..1 vs background. None until learned."""
        if self.bg is None or self._n < 30:
            return None
        g = self._to_grid(luma)
        if g is None:
            return None
        d = np.abs(g - self.bg)
        return np.clip((d - self.NOVEL_THRESH * 0.5)
                       / self.NOVEL_THRESH, 0, 1)

    def describe(self, luma):
        """One-line: what's novel in the scene."""
        nov = self.novelty(luma)
        if nov is None:
            return "learning the scene…"
        frac = float((nov > 0.5).mean())
        if frac < 0.02:
            return "scene as remembered"
        # where, coarsely
        gh, gw = nov.shape
        ys, xs = np.nonzero(nov > 0.5)
        cx, cy = xs.mean() / gw, ys.mean() / gh
        zone = "left" if cx < 0.33 else ("right" if cx > 0.66 else "center")
        return "something new %s (%.0f%% of view)" % (zone, frac * 100)
