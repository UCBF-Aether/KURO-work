#!/usr/bin/env python3
"""fovea.py — [BRAIN2-ENHANCEMENT] the fovea: look CLOSER at what matters.

The fly eye sees the whole field at once, no gaze, no zoom. The fovea
is the upgrade: when the cortex tracks an object, crop that region and
enlarge it — a directed look at the thing worth seeing. The eye's
periphery watches everything; the fovea darts to what moves.

The fly moves its whole body to inspect. We evolve past: directed zoom.
"""

import os

import numpy as np

try:
    from PIL import Image
    _PIL = True
except ImportError:
    _PIL = False


def foveate(frame_path, objects, out_path, zoom=3.0, margin=0.15):
    """Crop+enlarge the highest-energy tracked object.

    frame_path: raw camera frame.
    objects:    tracked objects [{x,y,w,h,energy,...}] in 0..1 fractions.
    out_path:   where to write the fovea close-up.
    zoom:       enlargement factor. margin: extra context around the box.
    Returns out_path, or None if no objects.
    """
    if not _PIL or not objects:
        return None
    o = max(objects, key=lambda o: o.get("energy", 0))
    base = Image.open(frame_path).convert("RGB")
    ww, wh = base.size
    # expand box by margin, clamp to frame
    x0 = max(0, (o["x"] - margin * o["w"]) * ww)
    y0 = max(0, (o["y"] - margin * o["h"]) * wh)
    x1 = min(ww, (o["x"] + o["w"] * (1 + margin)) * ww)
    y1 = min(wh, (o["y"] + o["h"] * (1 + margin)) * wh)
    if x1 <= x0 or y1 <= y0:
        return None
    crop = base.crop((int(x0), int(y0), int(x1), int(y1)))
    w, h = crop.size
    close = crop.resize((int(w * zoom), int(h * zoom)), Image.LANCZOS)
    close.save(out_path, "JPEG", quality=88)
    return out_path
