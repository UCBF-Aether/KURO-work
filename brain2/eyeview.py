#!/usr/bin/env python3
"""eyeview.py — the eye's vision, rendered human.

The fly eye creates vision (motion fields, tracked objects, looming),
not data. This renders that vision as images: the raw frame (human-like
— you see the car) fused with the eye's visual field (motion glow,
tracked boxes with IDs, looming flash). What Muse LOOKS AT.

This is the upgrade Cory ordered: not the fly's motion-glow world alone,
not the raw camera alone — the eye's vision, human-upgraded, live.

[BRAIN2-ENHANCEMENT] The fly does not render pictures. We do, because
the agent perceives images.
"""

import json
import os

import numpy as np

try:
    from PIL import Image, ImageDraw
    _PIL = True
except ImportError:
    _PIL = False


def _upsample(grid, wh, ww):
    """Bilinear-ish upsample of a (gh, gw) grid to (wh, ww) via PIL."""
    g = np.clip(np.asarray(grid, dtype=np.float64), 0, 1)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize(
        (ww, wh), Image.BILINEAR)
    return np.asarray(im).astype(np.float64) / 255.0


def render(frame_path, sight, out_path):
    """Fuse raw frame + eye's visual field → the eye-view image.

    frame_path: raw camera frame (human-like base).
    sight:      live sight packet (motion_grid, objects, looming...).
    out_path:   where to write the eye-view JPEG.
    Returns out_path.
    """
    if not _PIL:
        raise RuntimeError("PIL required for eyeview rendering")
    base = Image.open(frame_path).convert("RGB")
    ww, wh = base.size
    img = np.asarray(base).astype(np.float64) / 255.0

    # 1. motion glow — the fly's motion world, orange-red where it fires
    mgrid = (sight or {}).get("motion_grid")
    if mgrid:
        glow = _upsample(mgrid, wh, ww)
        # smooth-ish: clip + gamma for visibility
        glow = np.clip(glow * 3.0, 0, 1) ** 0.7
        warm = np.array([1.0, 0.25, 0.05])
        img = np.clip(img + glow[..., None] * warm * 0.55, 0, 1)

    # 2. redness tint — true hue channel, subtle red where red lives
    rgrid = (sight or {}).get("redness_grid")
    if rgrid:
        red = _upsample(rgrid, wh, ww)
        red = np.clip(red * 2.0, 0, 1) ** 0.8
        img = np.clip(img + red[..., None] * np.array([0.35, 0.0, 0.0]), 0, 1)

    out = Image.fromarray((img * 255).astype(np.uint8))
    d = ImageDraw.Draw(out)

    # 3. tracked objects — ONLY the confident ones. The eye shows motion;
    # discerning things is the seer's job, not the tracker's. Boxes appear
    # only for objects that earned it (high energy, stable, actually moving);
    # the rest is left to the eye looking at the glow. The speed gate kills
    # background latches (swaying trees) that spike on energy but go nowhere.
    for o in (sight or {}).get("objects", []):
        if o.get("energy", 0) < 0.35 or o.get("age_frames", 0) < 6:
            continue
        _sp = (o.get("vx", 0) ** 2 + o.get("vy", 0) ** 2) ** 0.5
        if _sp < 0.06:
            continue
        x0, y0 = o["x"] * ww, o["y"] * wh
        x1, y1 = (o["x"] + o["w"]) * ww, (o["y"] + o["h"]) * wh
        d.rectangle([x0, y0, x1, y1], outline=(0, 255, 0), width=2)
        # velocity arrow (yellow)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        d.line([cx, cy, cx + o.get("vx", 0) * ww * 2,
                cy + o.get("vy", 0) * wh * 2],
               fill=(255, 255, 0), width=2)
        d.text((x0 + 3, max(0, y0 - 12)), "#%d" % o["id"], fill=(0, 255, 0))

    # 4. looming — red border flash, the fly's oldest alarm
    if (sight or {}).get("looming", 0) > 0.1:
        bw = 8
        d.rectangle([0, 0, ww - 1, wh - 1], outline=(255, 0, 0), width=bw)

    out.save(out_path, "JPEG", quality=88)
    return out_path
