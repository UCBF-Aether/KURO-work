#!/usr/bin/env python3
"""night.py — [BRAIN2-ENHANCEMENT] night vision: see in the dark.

The fly eye is blind without light — motion comes from luminance, no
photons, no seeing. Night vision is the upgrade: adaptive low-light
boost applied BEFORE the eye processes the frame. Dark frames get
lifted (gamma + contrast stretch, keyed to mean luminance); bright
frames pass through untouched.

The fly never evolved this. We do, because the agent watches at 3am.
"""

import numpy as np

try:
    from PIL import Image
    _PIL = True
except ImportError:
    _PIL = False

# below this mean luminance (0..1), the night kicks in
DARK_THRESH = 0.25


def boost(frame_path, out_path=None):
    """Adaptive low-light lift. Returns (out_path, boosted: bool).

    If the frame is dark, applies gamma lift + contrast stretch and
    writes the boosted frame. If bright enough, returns the original
    path untouched with boosted=False.
    """
    if not _PIL:
        return frame_path, False
    img = Image.open(frame_path).convert("RGB")
    a = np.asarray(img).astype(np.float64) / 255.0
    mean = a.mean()
    if mean >= DARK_THRESH:
        return frame_path, False
    # darkness factor 0..1: how deep the night is
    d = min(1.0, (DARK_THRESH - mean) / DARK_THRESH)
    # gamma lift: darker → stronger lift (gamma 1.0 → 0.45)
    gamma = 1.0 - 0.55 * d
    lifted = np.clip(a, 0, 1) ** gamma
    # contrast stretch around the lifted mean
    m = lifted.mean()
    stretched = np.clip((lifted - m) * (1.0 + 0.8 * d) + m, 0, 1)
    out = Image.fromarray((stretched * 255).astype(np.uint8))
    dest = out_path or frame_path.replace(".jpg", "_night.jpg")
    out.save(dest, "JPEG", quality=88)
    return dest, True


def darkness(frame_path):
    """0..1 — how dark the frame is (for the eye's own awareness)."""
    if not _PIL:
        return 0.0
    img = Image.open(frame_path).convert("L")
    mean = np.asarray(img).astype(np.float64).mean() / 255.0
    return float(np.clip((DARK_THRESH - mean) / DARK_THRESH, 0, 1))
