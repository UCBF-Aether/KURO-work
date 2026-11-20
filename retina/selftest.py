#!/usr/bin/env python3
"""selftest.py — RETINA v2 build-time self-check.

SEALED: deterministic (fixed synthetic frames, no randomness), no clock
(the retina is a pure transducer — frames in, intensities out), no
network, no file writes, no side effects. This is NOT an endpoint and NOT
a runtime component — agents integrate via frame() and feed the resulting
intensities to the existing bottles' sense() API.
Run at build time to prove the transducer is wired correctly.

Exit 0 when every check passes, exit 1 on the first failure.
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from retina import Retina, OVERLAP_SHARED, ACUTE_GAIN  # noqa: E402

CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


def assert_eq(a, b, msg=""):
    assert a == b, "%s: %r != %r" % (msg, a, b)


def assert_gt(a, b, msg=""):
    assert a > b, "%s: %r not > %r" % (msg, a, b)


def assert_lt(a, b, msg=""):
    assert a < b, "%s: %r not < %r" % (msg, a, b)


def _frame(w=90, h=78, bg=230):
    return np.full((h, w, 3), bg, dtype=np.uint8)


def _bar(img, x0, x1, val=40):
    img = img.copy()
    img[:, x0:x1] = val
    return img


def _disc(img, cx, cy, r, val=40):
    img = img.copy()
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    img[(xx - cx) ** 2 + (yy - cy) ** 2 <= r ** 2] = val
    return img


@check("constructs; two eyes, 23x35 hex = 805 facets each (biofaithful)")
def _():
    r = Retina()
    assert_eq(r.lattice, "hex", "default lattice")
    assert_eq(r.grid, (23, 35), "grid")
    st = r.state()
    assert_eq(st["eyes"], 2, "eye count")
    assert_eq(st["facets_per_eye"], 805, "facets per eye")
    assert_eq(st["total_facets"], 1610, "total facets")
    assert_eq(st["overlap_shared"], OVERLAP_SHARED, "overlap")


@check("hex lattice: 6 equidistant neighbors (real ommatidial packing)")
def _():
    r = Retina(lattice="hex")
    f = np.zeros((48, 64, 3), dtype=np.uint8)
    r.frame(f)
    r.frame(f)
    xs, ys = r.eyes["L"]._hex_xy
    pw, ph = r.eyes["L"]._pitch
    # neighbor distances for an interior facet: all 6 equal
    i, j = 17, 11
    pts = []
    for di, dj in ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, 1)):
        # odd-r offset: row i is odd -> shift applies
        pts.append((xs[i + di, j + dj], ys[i + di, j + dj]))
    d = [float(np.hypot(px - xs[i, j], py - ys[i, j])) for px, py in pts]
    for dd in d:
        assert abs(dd - d[0]) < 1e-9, "neighbors not equidistant: %r" % (d,)
    # and equal to the lattice pitch
    assert abs(d[0] - pw) < 1e-9, "neighbor distance != pitch"


@check("eye windows tile the frame with ~25% frontal overlap")
def _():
    r = Retina()
    (x0L, x1L), (x0R, x1R) = r._split(240)
    # left starts at 0, right ends at frame edge, overlap in the middle
    assert_eq(x0L, 0, "left starts at 0")
    assert_eq(x1R, 240, "right ends at frame edge")
    overlap = x1L - x0R
    assert_gt(overlap, 0, "positive overlap")
    # overlap is ~25% of each eye's window
    frac = overlap / float(x1L - x0L)
    assert_gt(frac, 0.20, "overlap fraction lower bound")
    assert_lt(frac, 0.30, "overlap fraction upper bound")


@check("acute-zone gain ramps toward the frontal edge, mean-normalized")
def _():
    r = Retina()
    gl = r.eyes["L"]._gain_x
    gr = r.eyes["R"]._gain_x
    # left eye: frontal = +x edge (high j); right eye: frontal = -x edge
    assert_gt(gl[0, -1], gl[0, 0], "L gain rises toward frontal edge")
    assert_gt(gr[0, 0], gr[0, -1], "R gain rises toward frontal edge")
    assert_eq(round(float(gl.mean()), 9), 1.0, "L gain normalized")
    assert_eq(round(float(gr.mean()), 9), 1.0, "R gain normalized")
    assert_gt(gl.max(), 1.0, "L acute boost exists")
    assert_lt(gl.min(), 1.0, "L periphery below unity")


@check("first frame reports no motion (no temporal reference)")
def _():
    r = Retina()
    out = r.frame(_frame())
    assert_eq(out["motion"], 0.0, "motion")
    assert_eq(out["looming"], 0.0, "looming")
    assert_eq(set(out.keys()), {"motion", "color", "looming",
                                "contraction"}, "exact output keys")


@check("identical frames are exactly silent on change channels")
def _():
    r = Retina()
    f = _bar(_frame(), 20, 30)
    r.frame(f)
    out = r.frame(f.copy())
    assert_eq(out["motion"], 0.0, "motion")
    assert_eq(out["looming"], 0.0, "looming")


@check("rightward bar gives fused motion (detection, no direction)")
def _():
    r = Retina()
    r.frame(_bar(_frame(), 20, 30))
    out = r.frame(_bar(_frame(), 26, 36))
    assert_gt(out["motion"], 0.0, "motion intensity")
    assert_eq("motion_dir" in out, False, "no direction field")
    assert_eq("flow_dir" in out, False, "no flow field")


@check("leftward bar gives the same fused motion (both are just motion)")
def _():
    r = Retina()
    r.frame(_bar(_frame(), 26, 36))
    out = r.frame(_bar(_frame(), 20, 30))
    assert_gt(out["motion"], 0.0, "motion intensity")
    assert_eq("motion_dir" in out, False, "no direction field")


@check("expanding disc gives looming > 0 (sustained growth)")
def _():
    r = Retina()
    base = _frame(bg=230)
    looms = []
    for rad in (4, 6, 8, 10, 12):
        looms.append(r.frame(_disc(base, 45, 39, rad))["looming"])
    assert_gt(max(looms), 0.0, "looming on expansion")


@check("translating disc does not loom (boundary veto)")
def _():
    r = Retina()
    base = _frame(bg=230)
    looms = []
    for cx in (20, 26, 32, 38, 44, 50):
        looms.append(r.frame(_disc(base, cx, 39, 8))["looming"])
    assert_eq(max(looms), 0.0, "looming on translation")


@check("contracting disc does not loom; reports contraction instead")
def _():
    r = Retina()
    base = _frame(bg=230)
    looms, contrs = [], []
    for rad in (12, 10, 8, 6, 4):
        out = r.frame(_disc(base, 45, 39, rad))
        looms.append(out["looming"])
        contrs.append(out["contraction"])
    assert_eq(max(looms), 0.0, "looming on contraction")
    assert_gt(max(contrs), 0.0, "contraction signal on contraction")


@check("entering disc does not loom (radial opponency, not centroid)")
def _():
    r = Retina()
    base = _frame(bg=230)
    looms = []
    for cx in (-6, -2, 2, 6, 10, 14):
        looms.append(r.frame(_disc(base, cx, 39, 8))["looming"])
    assert_eq(max(looms), 0.0, "looming on entry")


@check("two expanding discs: both eyes detect (tiled LPLC2 templates)")
def _():
    r = Retina()
    base = _frame(bg=230)
    for rad in (3, 5, 7, 9, 11):
        r.frame(_disc(_disc(base, 25, 39, rad), 65, 39, rad))
    eo = r.eye_outputs()
    assert_gt(eo["L"]["looming"], 0.0, "left eye sees its disc expand")
    assert_gt(eo["R"]["looming"], 0.0, "right eye sees its disc expand")


@check("saturated frame registers color; gray frame does not")
def _():
    r = Retina()
    sat = np.zeros((78, 90, 3), dtype=np.uint8)
    sat[:, :] = (0, 0, 220)
    out = r.frame(sat)
    assert_gt(out["color"], 0.5, "color on saturated frame")
    r2 = Retina()
    out2 = r2.frame(_frame(bg=128))
    assert_eq(out2["color"], 0.0, "color on gray frame")


@check("binocular: frontal-zone motion seen by BOTH eyes")
def _():
    r = Retina()
    # overlap zone for a 90px frame: split gives [0,51]/[39,90]
    base = _frame(w=90)
    r.frame(_bar(base, 41, 45))
    r.frame(_bar(base, 44, 48))
    eo = r.eye_outputs()
    assert_gt(eo["L"]["motion"], 0.0, "left eye sees frontal motion")
    assert_gt(eo["R"]["motion"], 0.0, "right eye sees frontal motion")


@check("binocular: far-left motion seen ONLY by the left eye")
def _():
    r = Retina()
    base = _frame(w=90)
    r.frame(_bar(base, 4, 8))
    r.frame(_bar(base, 7, 11))
    eo = r.eye_outputs()
    assert_gt(eo["L"]["motion"], 0.0, "left eye sees edge motion")
    assert_eq(eo["R"]["motion"], 0.0, "right eye blind to far-left motion")


@check("invalid input raises ValueError")
def _():
    r = Retina()
    for bad in (np.zeros((10, 10), dtype=np.uint8),
                np.zeros((10, 10, 4), dtype=np.uint8),
                np.zeros((4, 4, 3), dtype=np.uint8)):
        try:
            r.frame(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("no ValueError for shape %r" % (bad.shape,))


def _textured_car_scene(direction):
    """Deterministic textured scene: 72x48 correlated-noise car sliding
    over a static correlated-noise road. Returns list of frames."""
    rng = np.random.RandomState(11)

    def snoise(shape, k):
        w = rng.normal(0, 1, shape)
        pad = k // 2
        out = w
        for axis in (1, 0):
            ap = np.pad(out, [(pad, pad) if d == axis else (0, 0)
                              for d in range(out.ndim)], mode="edge")
            z = np.zeros_like(ap)
            s0 = [slice(None)] * out.ndim
            s0[axis] = slice(0, 1)
            cs = np.concatenate([z[tuple(s0)], np.cumsum(ap, axis=axis)],
                                axis=axis)
            n = out.shape[axis]
            hi = [slice(None)] * out.ndim
            hi[axis] = slice(k, k + n)
            lo = [slice(None)] * out.ndim
            lo[axis] = slice(0, n)
            out = (cs[tuple(hi)] - cs[tuple(lo)]) / k
        return out

    Hh, Ww = 78, 90
    bg = np.full((Hh, Ww, 3), 150.0)
    bg += snoise((Hh, Ww, 1), 7) * 22.0
    car = 55.0 + snoise((16, 24, 1), 9) * 40.0
    car = np.clip(car, 15, 120)
    frames = []
    for fi in range(12):
        img = np.clip(bg, 0, 255).astype(np.uint8).copy()
        x0 = 8 + fi * 4 if direction > 0 else 60 - fi * 4
        img[30:46, x0:x0 + 24] = np.clip(car, 0, 255).astype(np.uint8)
        frames.append(img)
    return frames


@check("unsigned motion detects a textured car moving right (no direction)")
def _():
    r = Retina()
    out = None
    for f in _textured_car_scene(+1):
        out = r.frame(f)
    assert_gt(out["motion"], 0.0, "motion on right-moving car")
    assert_eq("motion_dir" in out, False, "no direction field")


@check("unsigned motion detects a textured car moving left (same output)")
def _():
    r = Retina()
    out = None
    for f in _textured_car_scene(-1):
        out = r.frame(f)
    assert_gt(out["motion"], 0.0, "motion on left-moving car")
    assert_eq("flow_dir" in out, False, "no flow field")


@check("deterministic: same frames twice give identical outputs")
def _():
    def run():
        r = Retina()
        outs = []
        base = _frame()
        for i in range(6):
            outs.append(r.frame(_bar(base, 20 + 3 * i, 30 + 3 * i)))
        return outs
    a, b = run(), run()
    for oa, ob in zip(a, b):
        assert_eq(oa, ob, "determinism")


def main():
    failed = 0
    for name, fn in CHECKS:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            print("FAIL %s — %s: %s" % (name, type(e).__name__, e))
            failed += 1
        else:
            print("PASS %s" % name)
    print("%d/%d checks passed" % (len(CHECKS) - failed, len(CHECKS)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
