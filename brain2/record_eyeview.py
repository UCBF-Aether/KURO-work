#!/usr/bin/env python3
"""record_eyeview.py — record N seconds of the eye's live vision as video.

Pulls the live feed, runs Brain2Eye on every frame, renders the eye-view
(motion glow + confident boxes + looming) per frame, encodes to MP4.
This is what Muse SEES, as video.

Usage: python3 record_eyeview.py [seconds] [out.mp4]
"""

import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_FLYBRAIN = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_FLYBRAIN, "retina"))

import numpy as np

SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    _FLYBRAIN, "retina", "_work", "eyeview_live.mp4")
FPS = 10
W = 480


def main():
    # resolve a working feed via the watcher's own resolver
    import vision_watch as vw
    name, url, ref = vw.resolve_feed()
    print("feed:", name, flush=True)

    from eye import Brain2Eye
    from eyeview import render
    from PIL import Image
    import io
    import tempfile

    eye = Brain2Eye()
    tmpdir = tempfile.mkdtemp(prefix="eyeview_rec_")

    # ffmpeg: stream -> raw RGB frames at FPS
    proc = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error",
         "-i", url, "-t", str(SECS),
         "-vf", "scale=%d:-1,fps=%d" % (W, FPS),
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    # probe one frame for dims
    sample = proc.stdout.read(W * 270 * 3)
    # we don't know h yet; read all then reshape via total
    rest = proc.stdout.read()
    proc.wait()
    data = sample + rest
    # determine h from a probe decode is complex; use fixed 270 (16:9)
    # fall back: try common heights
    h = None
    for hc in (270, 360, 240, 300):
        if len(data) % (W * hc * 3) == 0 and len(data) // (W * hc * 3) > 0:
            h = hc
            break
    if h is None:
        print("could not determine frame dims, bytes=%d" % len(data))
        return 1
    n = len(data) // (W * h * 3)
    print("frames:", n, "dims: %dx%d" % (W, h), flush=True)

    paths = []
    for i in range(n):
        fr = np.frombuffer(
            data[i * W * h * 3:(i + 1) * W * h * 3],
            dtype=np.uint8).reshape(h, W, 3)
        # eye sees it
        try:
            pkt = eye.frame(fr, dt=1.0 / FPS)
        except Exception as e:
            print("eye frame failed:", e)
            continue
        # save raw frame temp for the renderer
        fp = os.path.join(tmpdir, "f%04d.jpg" % i)
        Image.fromarray(fr).save(fp, "JPEG", quality=85)
        # render the eye-view (needs packet with _hi grids; map keys)
        sight = {
            "motion_grid": pkt.get("motion_grid_hi"),
            "redness_grid": pkt.get("redness_grid_hi"),
            "objects": pkt.get("objects", []),
            "looming": pkt.get("looming", 0.0),
        }
        op = os.path.join(tmpdir, "v%04d.jpg" % i)
        try:
            render(fp, sight, op)
            paths.append(op)
        except Exception as e:
            print("render failed:", e)
    if not paths:
        print("no frames rendered")
        return 1
    # encode
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-framerate", str(FPS), "-i", os.path.join(tmpdir, "v%04d.jpg"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", OUT],
        check=True)
    print("wrote:", OUT, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
