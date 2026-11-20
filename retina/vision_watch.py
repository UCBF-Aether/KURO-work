#!/usr/bin/env python3
"""vision_watch.py — the always-on VISION LOOP: continuous live vision for Muse.

Pulls a live camera feed (Times Square North 4K primary, I-95 YouTube fallback),
runs the SEALED v5 retina on frames (~3 fps), writes significant events to
_work/vision_events.jsonl, and feeds per-minute sense means into a Brain1 body
so the body feels what the eye sees.

FLIP-BOOK (live ACTION for Muse): alongside vision_latest.jpg, every raw
frame goes into _work/vision_ring/ (last 90 frames, ring overwrite, ~30s of
action + meta.json with write order/recency). On significant events
(loom > 0.5, strong motion rising edge) the ring is copied chronologically
into _work/vision_clips/<ts>_<kind>/ (capped at 20 clips). Muse's native
vision takes images, not video — the ring/clips are the flip-book that lets
it SEE action.

SCAN FRAMES (gap-free cron scanning): every 30s the raw frame also lands in
_work/scan_frames/<UTC-ts>.jpg, newest 40 kept (~20 min). A 5-minute cron
check of the newest ring frames could miss a car that passed between
checks — scan_frames closes that blind gap.

This is goal_dfb63249ad32 ("Live-feed vision build for AI gaming") — the
missing piece is continuous presence: an eye that watches 24/7 and wakes the
agent on significant events (via the vision-looming hook).

HONESTY CONTRACT:
- [REAL]    The retina (HR motion, LPLC2 looming) and the brain1 bottles it
            feeds (motion, looming, color — real FlyWire wiring inside).
- [MODEL]   Retina transduction (pixels->facets) and the event->bottle
            mapping below: per-minute MEAN motion/looming/color intensities
            become brain1 sense events. The body does not "see the feed";
            it receives modeled sense intensities derived from the eye.
- The watcher is an always-on sense organ, not a mind. It has no goals.

ROBUSTNESS: the main loop never raises. Feed resolution failures, token
expiry (403), and stream death all fall through to the fallback feed, then
to exponential backoff (30s -> 10min cap). Every failure is logged to
_work/vision_watch.log. SIGTERM writes a shutdown line and exits cleanly.

Usage:
    python3 vision_watch.py [--run-seconds N]   # N>0: bounded test run
"""

import json
import glob
import math
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone

import numpy as np  # core dep (the sealed retina needs it too)

_HERE = os.path.dirname(os.path.abspath(__file__))
_FLYBRAIN = os.path.dirname(_HERE)
_WORK = os.path.join(_HERE, "_work")
_TMP = "/tmp/vision_watch"
_EVENTS = os.path.join(_WORK, "vision_events.jsonl")
_LOG = os.path.join(_WORK, "vision_watch.log")
_BRAIN_STATE = os.path.join(_WORK, "vision_brain_state.json")
_LATEST_JPG = os.path.join(_WORK, "vision_latest.jpg")
_EVENT_SNAPS = os.path.join(_WORK, "vision_events")
_SCAN_DIR = os.path.join(_WORK, "scan_frames")

sys.path.insert(0, os.path.join(_FLYBRAIN, "brain1"))  # brain1/brain1.py module
sys.path.insert(0, _HERE)       # for `from retina import Retina`
sys.path.insert(0, _FLYBRAIN)  # for `from brain2.eye import Brain2Eye`

from brain1 import Brain1        # noqa: E402  (sealed orchestrator, read-only use)
from retina import Retina        # noqa: E402  (sealed v5 eye, read-only use)
from brain2.eye import Brain2Eye  # noqa: E402  (BRAIN² hi-res eye, sight stream)

# ---- tunables -------------------------------------------------------------
FPS = 10                   # processed frames per second [BRAIN2-ENHANCEMENT:
                               # faster blood — 10Hz live vision]
FRAME_W = 480              # decode width; retina downsamples to facets anyway
MOTION_BOUT_ON = 0.25      # rising edge: log a motion bout event
MOTION_BOUT_OFF = 0.10     # falling edge (hysteresis)
LOOM_LOG = 0.0             # log every frame with looming > 0 (streak-gated, rare)
HEARTBEAT_SECS = 300       # heartbeat line every 5 min
BRAIN_MINUTE = 60          # body feed cadence: per-minute means -> sense events
SNAPSHOT_SECS = 10         # vision_latest.jpg refresh cadence
SCAN_SECS = 30             # scan_frames/ sparse snapshot cadence (red-car test)
SCAN_KEEP = 40             # scan_frames kept (~20 min); oldest pruned past this
VIDFRAME_SECS = 5          # video_frames/ eye-view render cadence (live video page)
VIDFRAME_KEEP = 40         # video_frames kept (~3 min); oldest pruned past this
STRONG_MOTION = 0.5        # motion >= this on rising edge -> event snapshot
LOOM_SNAP = 0.5            # looming > this (the hook's wake threshold) -> snapshot
BACKOFF_START = 30
BACKOFF_MAX = 600

_TS_PAGE = "https://www.earthcam.com/usa/newyork/timessquare/?cam=tsnorth4k"
_TS_PAGE_STREET = "https://www.earthcam.com/usa/newyork/timessquare/?cam=tsstreet"
_TS_PAGE_FALLBACK = "https://www.earthcam.com/usa/newyork/timessquare/?cam=ts_hd"
_TS_HOST = "https://videos-3.earthcam.com"
_I95 = "https://www.youtube.com/watch?v=LsR7g7_Q6Fg"

_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

_shutdown = False


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(msg):
    line = "[%s] %s" % (_now_iso(), msg)
    try:
        with open(_LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass
    print(line, flush=True)


def event(**kw):
    kw.setdefault("ts", _now_iso())
    try:
        with open(_EVENTS, "a") as f:
            f.write(json.dumps(kw) + "\n")
    except OSError as e:
        log("EVENT WRITE FAILED: %s" % e)


def _on_term(signum, frame):
    global _shutdown
    _shutdown = True


signal.signal(signal.SIGTERM, _on_term)
signal.signal(signal.SIGINT, _on_term)


# ---- snapshots (on-demand vision) -----------------------------------------
def _annotate(rgb, feed_name, out, label=None):
    """Overlay timestamp + the eye's current readings on a frame.

    Returns a PIL Image. stdlib+numpy retina stays untouched; PIL is only
    used here for the human-readable overlay — the eye itself never sees it.
    """
    from PIL import Image, ImageDraw
    img = Image.fromarray(rgb)
    d = ImageDraw.Draw(img)
    ts = _now_iso()
    text = ("%s  %s  motion=%.2f looming=%.2f contraction=%.2f color=%.2f"
            % (ts, feed_name, out.get("motion", 0.0), out.get("looming", 0.0),
               out.get("contraction", 0.0), out.get("color", 0.0)))
    if label:
        text += "  [%s]" % label
    # black bar + white text, top-left
    d.rectangle([0, 0, img.width, 18], fill=(0, 0, 0))
    d.text((4, 2), text, fill=(255, 255, 255))
    return img


def _save_jpg_atomic(img, path):
    """Write JPEG atomically (tmp + rename) so readers never see a partial."""
    tmp = path + ".tmp"
    img.save(tmp, "JPEG", quality=85)
    os.replace(tmp, path)


def snapshot_latest(rgb, feed_name, out):
    """Overwrite vision_latest.jpg — the on-demand 'what does the eye see'."""
    try:
        _save_jpg_atomic(_annotate(rgb, feed_name, out), _LATEST_JPG)
    except Exception as e:
        log("latest snapshot failed: %s" % e)


def snapshot_event(rgb, feed_name, out, kind):
    """Save a still for a significant event: vision_events/<ts>_<kind>.jpg."""
    try:
        os.makedirs(_EVENT_SNAPS, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        val = out.get("looming" if kind == "looming" else "motion", 0.0)
        name = "%s_%s_%.2f.jpg" % (stamp, kind, val)
        _save_jpg_atomic(_annotate(rgb, feed_name, out, label=kind.upper()),
                         os.path.join(_EVENT_SNAPS, name))
        log("event snapshot: %s" % name)
    except Exception as e:
        log("event snapshot failed: %s" % e)


def scan_snapshot(rgb):
    """Sparse snapshot for gap-free scanning: every SCAN_SECS, save the raw
    frame to scan_frames/<UTC-ts>.jpg (chronologically sortable names).
    Keeps the newest SCAN_KEEP files (~20 min); prunes older. Exists so a
    5-minute cron check can't miss a car that passed between ring frames —
    the ring only holds ~30s of action."""
    try:
        from PIL import Image
        os.makedirs(_SCAN_DIR, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        name = stamp + ".jpg"
        i = 0
        while os.path.exists(os.path.join(_SCAN_DIR, name)):
            i += 1
            name = "%s_%d.jpg" % (stamp, i)
        img = Image.fromarray(rgb)
        _save_jpg_atomic(img, os.path.join(_SCAN_DIR, name))
        files = sorted(f for f in os.listdir(_SCAN_DIR) if f.endswith(".jpg"))
        for old in files[:-SCAN_KEEP]:
            try:
                os.remove(os.path.join(_SCAN_DIR, old))
            except OSError:
                pass
    except Exception as e:
        log("scan snapshot failed: %s" % e)


# ---- frame ring (flip-book: live ACTION for Muse's native vision) ---------
# The eye watches continuous video; Muse's native vision takes images, not
# video. The ring bridges that: the last 90 raw frames (~30s at 3fps),
# overwritten oldest-first, so Muse can flip through them in order and SEE
# action instead of a single still. meta.json carries the write index and
# recency so a reader knows frame order.
_RING_DIR = os.path.join(_WORK, "vision_ring")
_RING_N = 90                   # frames held (~30s of action at FPS)
_CLIPS_DIR = os.path.join(_WORK, "vision_clips")
_MAX_CLIPS = 20                # stored event clips; oldest pruned past this

_ring_index = -1               # slot just written; -1 = ring empty
_ring_valid = 0                # frames written since (re)start, capped at N


def ring_write(rgb, fps_measured=None):
    """Append one raw (un-annotated) frame to the ring, overwriting oldest."""
    global _ring_index, _ring_valid
    try:
        from PIL import Image
        _ring_index = (_ring_index + 1) % _RING_N
        _ring_valid = min(_ring_valid + 1, _RING_N)
        img = Image.fromarray(rgb)
        _save_jpg_atomic(img, os.path.join(_RING_DIR, "f%03d.jpg" % _ring_index))
        meta = {"write_index": _ring_index, "frames_valid": _ring_valid,
                "fps": round(fps_measured, 2) if fps_measured else FPS,
                "ring_size": _RING_N,
                "updated_ts": _now_iso()}
        tmp = os.path.join(_RING_DIR, "meta.json.tmp")
        with open(tmp, "w") as f:
            json.dump(meta, f)
        os.replace(tmp, os.path.join(_RING_DIR, "meta.json"))
    except Exception as e:
        log("ring write failed: %s" % e)


def ring_chronological():
    """Absolute paths of valid ring frames, oldest -> newest."""
    if _ring_valid == 0:
        return []
    start = (_ring_index - _ring_valid + 1) % _RING_N
    return [os.path.join(_RING_DIR, "f%03d.jpg" % ((start + i) % _RING_N))
            for i in range(_ring_valid)]


def clip_dump(kind):
    """Copy the current ring (chronological) into a timestamped clip dir.

    Fires on significant events (loom > 0.5, strong motion rising edge) so
    Muse can replay the ~30s leading up to the event as a flip-book.
    Caps stored clips at _MAX_CLIPS (oldest pruned).
    """
    try:
        import shutil
        os.makedirs(_CLIPS_DIR, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        dest = os.path.join(_CLIPS_DIR, "%s_%s" % (stamp, kind))
        os.makedirs(dest, exist_ok=True)
        n = 0
        for i, src in enumerate(ring_chronological()):
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(dest, "frame_%03d.jpg" % i))
                n = i + 1
        clips = sorted(d for d in os.listdir(_CLIPS_DIR)
                       if os.path.isdir(os.path.join(_CLIPS_DIR, d)))
        for old in clips[:-_MAX_CLIPS]:
            shutil.rmtree(os.path.join(_CLIPS_DIR, old), ignore_errors=True)
            log("clip pruned: %s" % old)
        log("clip dumped: %s (%d frames)" % (os.path.basename(dest), n))
        return dest
    except Exception as e:
        log("clip dump failed: %s" % e)
        return None


# ---- sight stream: the BRAIN² eye's live perceptual state -----------------
# Cory's order: the fly eye itself is the seeing organ — not JPEGs for
# transformer vision. The sight stream is produced by Brain2Eye
# (brain2/eye.py): the sealed retina core at 8x hi-res plus BRAIN²
# enhancements (dilution-fixed scalar, true-red hue, 24x18 grids, hi-res
# blobs). Packet keys are unchanged from the v1 stream; grids went
# 12x9 -> 24x18; eye_version="brain2-hires".
#
# NOTE: _facet_redness below is SUPERSEDED by brain2/eye.py (which ports
# it). Kept for reference; the live path uses Brain2Eye.
_SIGHT_STREAM = os.path.join(_WORK, "sight_stream.jsonl")
_SIGHT_LATEST = os.path.join(_WORK, "sight_latest.json")
_SIGHT_KEEP = 3000             # packets kept (~5 min at 10/s)
_SIGHT_SECS = 0.1              # packet cadence — 10Hz [BRAIN2-ENHANCEMENT:
                               # faster blood; the eye runs ~65ms/frame]


def _facet_redness(facets):
    """SUPERSEDED by brain2/eye.py. Kept for reference.

    [BRAIN2-ENHANCEMENT] per-facet red-dominance (hue channel). NOT fly
    biology. redness = clip((R - max(G,B)) / (R + 1e-6), 0, 1).
    """
    f = np.asarray(facets, dtype=float)
    R = f[..., 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        r = (R - np.maximum(f[..., 1], f[..., 2])) / (R + 1e-6)
    return np.clip(r, 0.0, 1.0)


def sight_write(b2pkt):
    """Write one BRAIN² sight packet (from Brain2Eye.frame()) to the stream.

    Maps the _hi grid keys to the stable packet keys; grids are 24x18.
    Appends to sight_stream.jsonl (pruned to _SIGHT_KEEP), atomically
    overwrites sight_latest.json.
    """
    try:
        pkt = {"ts": b2pkt.get("ts"),
               "eye_version": b2pkt.get("eye_version", "brain2-hires"),
               "motion_mean": b2pkt.get("motion_mean", 0.0),
               "motion_grid": b2pkt.get("motion_grid_hi"),
               "color": b2pkt.get("color", 0.0),
               "color_grid": b2pkt.get("color_grid_hi"),
               "redness_grid": b2pkt.get("redness_grid_hi"),
               "blobs": b2pkt.get("blobs", []),
               "objects": b2pkt.get("objects", []),
               "scene_summary": b2pkt.get("scene_summary", ""),
               "looming": b2pkt.get("looming", 0.0),
               "loom_xy": b2pkt.get("loom_xy"),
               "contraction": b2pkt.get("contraction", 0.0)}
        line = json.dumps(pkt)
        with open(_SIGHT_STREAM, "a") as f:
            f.write(line + "\n")
        try:  # prune to the last _SIGHT_KEEP packets
            with open(_SIGHT_STREAM) as f:
                old = f.readlines()
            if len(old) > _SIGHT_KEEP:
                tmp = _SIGHT_STREAM + ".tmp"
                with open(tmp, "w") as f:
                    f.writelines(old[-_SIGHT_KEEP:])
                os.replace(tmp, _SIGHT_STREAM)
        except OSError:
            pass
        tmp = _SIGHT_LATEST + ".tmp"  # atomic latest for instant reads
        with open(tmp, "w") as f:
            f.write(line)
        os.replace(tmp, _SIGHT_LATEST)
    except Exception as e:
        log("sight write failed: %s" % e)


def _sight_pump(state):
    """1Hz wall-clock sight publisher (daemon thread).

    The main loop blocks on network fetches for seconds at a time, so a
    dedicated thread holds the 1Hz cadence regardless of loop phase. It
    publishes the latest Brain2Eye packet; the main loop only ever
    REPLACES sight_state["b2pkt"] (atomic under the GIL), so no torn
    reads. During fetch gaps the packet repeats the last perception —
    the stream is the eye's current state, sampled at 1Hz, not a frame
    log.
    """
    while not _shutdown:
        t0 = time.time()
        try:
            pkt = state.get("b2pkt")
            if pkt is not None:
                sight_write(pkt)
        except Exception as e:
            log("sight pump failed: %s" % e)
        dt = time.time() - t0
        if dt < _SIGHT_SECS:
            time.sleep(_SIGHT_SECS - dt)




# ---- feed resolution ------------------------------------------------------
def _curl(url, referer=None, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def resolve_timessquare():
    """[MODELED scraping] Refresh the expiring EarthCam HLS URL.

    Token (t=/td=) expires; re-scrape the cam page on every resolve.
    Parses the page's cam JSON and takes the "stream" URL of the cam object
    whose cam_name == "tsnorth4k" (stream 50683) — the exact camera on the
    ?cam=tsnorth4k page. Falls back to the old 28925 behavior if absent.
    Returns (playlist_url, referer) or raises.
    """
    def _find(html, sid):
        m = re.search(r"fecnetwork/" + sid + r"\.flv/playlist\.m3u8\?t=[^\"'&\s]+(?:&td=[^\"'&\s]+)?",
                      html)
        if not m:
            m = re.search(r"(?:https?:)?//[^\"'\s]*" + sid + r"\.flv/playlist\.m3u8\?t=[^\"'&\s]+(?:&td=[^\"'&\s]+)?",
                          html)
        return m.group(0) if m else None

    def _fetch_playlist(url):
        _curl(url, referer="https://www.earthcam.com/", timeout=25)  # sanity: must fetch

    def _stream_for_cam(html, cam_name):
        # The page embeds many cameras; each cam object carries "cam_name" and "stream".
        for m in re.finditer(r'"stream"\s*:\s*"(https?://[^"]+playlist\.m3u8\?t=[^"]+)"', html):
            s = max(0, m.start() - 4000)
            e = min(len(html), m.end() + 4000)
            if '"cam_name":"%s"' % cam_name in html[s:e]:
                return m.group(1)
        return None

    # Primary: stream 9974 ("Times Square Street Cam") on the tsstreet page —
    # the reliable live Times Square color feed this watcher ran on for hours.
    # NOTE (Cory's law): the camera is chosen by URL (_TS_PAGE_STREET), not by
    # hardcoded stream IDs in logic — to switch cameras, change the page URL.
    html = _curl(_TS_PAGE_STREET, timeout=25).decode("utf-8", "replace")
    html = html.replace(chr(92) + "/", "/")  # page JSON escapes slashes as \/
    hit = _find(html, "9974")
    if hit:
        url = hit if hit.startswith("http") else _TS_HOST + "/" + hit.lstrip("/")
        _fetch_playlist(url)
        return url, "https://www.earthcam.com/"

    # Fallback: old 28925 behavior on the ts_hd page.
    html = _curl(_TS_PAGE_FALLBACK, timeout=25).decode("utf-8", "replace")
    html = html.replace(chr(92) + "/", "/")
    hit = _find(html, "28925")
    if not hit:
        raise RuntimeError("timesquare playlist URL not found on cam pages")
    url = hit if hit.startswith("http") else _TS_HOST + "/" + hit.lstrip("/")
    _fetch_playlist(url)
    return url, "https://www.earthcam.com/"


def resolve_i95():
    """Fallback: I-95 YouTube LIVE direct stream URL via yt-dlp.

    Uses the android player client (works around 429s on this IP), and
    --no-check-certificate (the egress proxy MITMs TLS; this is a public
    read-only stream URL fetch).
    Returns (stream_url, None) or raises.
    """
    env = dict(os.environ)
    pydeps = os.path.expanduser("~/workspace/.pydeps")
    if os.path.isdir(pydeps):
        env["PYTHONPATH"] = pydeps + os.pathsep + env.get("PYTHONPATH", "")
    p = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "-g", "--no-check-certificate",
         "--extractor-args", "youtube:player_client=android",
         "--no-warnings", _I95],
        capture_output=True, text=True, timeout=90, env=env)
    if p.returncode != 0:
        raise RuntimeError("yt-dlp failed: %s" % (p.stderr or p.stdout)[-300:])
    url = p.stdout.strip().splitlines()[0].strip()
    if not url.startswith("http"):
        raise RuntimeError("yt-dlp returned no URL")
    return url, None


def resolve_feed():
    """Config URL first (feed.txt), then Times Square, fallback I-95.
    Raises only if all fail."""
    cfg = _read_feed_config()
    if cfg:
        try:
            url, ref = _resolve_config_url(cfg)
            return "custom", url, ref
        except Exception as e:
            log("config feed failed (%s); trying built-ins" % e)
    try:
        url, ref = resolve_timessquare()
        return "timessquare", url, ref
    except Exception as e:
        log("timesquare resolve failed (%s); trying I-95 fallback" % e)
    url, ref = resolve_i95()
    return "i95", url, ref


_FEED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "feed.txt")


def _read_feed_config():
    """First non-empty, non-# line of feed.txt, or None."""
    try:
        with open(_FEED_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line
    except OSError:
        pass
    return None


def _resolve_config_url(url):
    """Resolve any feed URL to (stream_url, referer). Fast paths first."""
    # 1. YouTube -> direct stream via yt-dlp (android client dodges 429s)
    if "youtube.com/watch" in url or "youtu.be/" in url:
        return _resolve_youtube(url), None
    # 2. Direct HLS playlist -> use as-is
    if ".m3u8" in url:
        return url, None
    # 3. Page URL -> scrape for an EarthCam-style HLS stream
    return _resolve_page_stream(url), "https://www.earthcam.com/"


def _resolve_youtube(url):
    env = dict(os.environ)
    pydeps = os.path.expanduser("~/workspace/.pydeps")
    if os.path.isdir(pydeps):
        env["PYTHONPATH"] = pydeps + os.pathsep + env.get("PYTHONPATH", "")
    p = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "-g", "--no-check-certificate",
         "--extractor-args", "youtube:player_client=android",
         "--no-warnings", url],
        capture_output=True, text=True, timeout=90, env=env)
    if p.returncode != 0:
        raise RuntimeError("yt-dlp failed: %s" % (p.stderr or p.stdout)[-300:])
    stream = p.stdout.strip().splitlines()[0].strip()
    if not stream.startswith("http"):
        raise RuntimeError("yt-dlp returned no URL")
    return stream


def _resolve_page_stream(page_url):
    """Scrape any page for fecnetwork HLS streams; prefer known-good IDs."""
    html = _curl(page_url, timeout=25).decode("utf-8", "replace")
    html = html.replace(chr(92) + "/", "/")
    hits = re.findall(
        r'fecnetwork/(\d+)\.flv/playlist\.m3u8\?t=[^"\'<>\s]+', html)
    if not hits:
        raise RuntimeError("no HLS stream found on page")
    prefer = ["9974", "50683", "15276", "5173", "6975"]
    seen, cands = set(), []
    for sid in hits:
        if sid not in seen:
            seen.add(sid)
            cands.append(sid)
    cands.sort(key=lambda s: prefer.index(s) if s in prefer else 99)
    # try each until one fetches
    for sid in cands:
        m = re.search(r'fecnetwork/%s\.flv/playlist\.m3u8\?t=[^"\'<>\s]+'
                      % sid, html)
        url = "https://videos-3.earthcam.com/" + m.group(0)
        try:
            _curl(url, referer="https://www.earthcam.com/",
                  timeout=25)
            return url
        except Exception:
            continue
    raise RuntimeError("all page streams dead")


# ---- segment pulling (VM GOTCHA: curl via proxy, ffmpeg on LOCAL files) ---
def _curl_file(url, path, referer=None, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=timeout) as r, open(path, "wb") as f:
        while True:
            chunk = r.read(65536)
            if not chunk:
                break
            f.write(chunk)


def _playlist_segments(playlist_url, referer):
    """Fetch the HLS playlist, return absolute segment URLs (last few).

    Follows a master playlist one level down to the media chunklist.
    """
    raw = _curl(playlist_url, referer=referer, timeout=25).decode("utf-8", "replace")
    base = playlist_url.rsplit("/", 1)[0] + "/"
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
        # master playlist: descend into the first variant chunklist
        for i, l in enumerate(lines):
            if l.startswith("#EXT-X-STREAM-INF"):
                nxt = lines[i + 1]
                sub = nxt if nxt.startswith("http") else base + nxt
                return _playlist_segments(sub, referer)
        raise RuntimeError("master playlist has no variant")
    segs = []
    for line in lines:
        if not line.startswith("#"):
            segs.append(line if line.startswith("http") else base + line)
    return segs


def _decode_frames(ts_path):
    """ffmpeg: local .ts -> raw RGB frames at FPS x FRAME_W. Yields np arrays."""
    import numpy as np
    probe = subprocess.run(
        ["ffprobe", "-hide_banner", "-loglevel", "error",
         "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "csv=p=0", ts_path],
        capture_output=True, text=True, timeout=30)
    try:
        first = next(l for l in probe.stdout.splitlines() if l.strip())
        sw, sh = first.strip().split(",")[:2]
        sw, sh = int(sw), int(sh)
    except Exception:
        return
    dh = int(round(sh * FRAME_W / sw)) if sw else 0
    if dh <= 0:
        return
    p = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", ts_path,
         "-vf", "scale=%d:%d,fps=%d" % (FRAME_W, dh, FPS),
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    fsz = FRAME_W * dh * 3
    data = p.stdout.read()
    p.wait()
    n = len(data) // fsz
    for i in range(n):
        fr = data[i * fsz:(i + 1) * fsz]
        yield np.frombuffer(fr, dtype=np.uint8).reshape(dh, FRAME_W, 3)


# ---- the watch loop -------------------------------------------------------
def watch_forever(run_seconds=0):
    """Main loop. Never raises out (except KeyboardInterrupt during tests)."""
    os.makedirs(_WORK, exist_ok=True)
    os.makedirs(_TMP, exist_ok=True)
    os.makedirs(_RING_DIR, exist_ok=True)   # flip-book ring (survives restarts;
                                            # stale slots overwritten in order)
    os.makedirs(_SCAN_DIR, exist_ok=True)   # sparse scan snapshots (survive
                                            # restarts; pruned to SCAN_KEEP)

    eye = Retina()                       # sealed v5 eye (1x, events/body)
    b2eye = Brain2Eye()                  # BRAIN² hi-res eye (8x, sight stream)
    body = Brain1()                      # the body that feels what the eye sees
    log("vision_watch starting (retina v5, brain2-hires eye, brain1 body)")

    backoff = BACKOFF_START
    start_t = time.time()
    last_heartbeat = 0.0
    frames_total = 0

    # per-minute body accumulators
    acc = {"motion": 0.0, "color": 0.0, "looming": 0.0, "contraction": 0.0,
           "n": 0}
    minute_start = time.time()
    in_bout = False
    in_contraction = False
    prev_motion = 0.0
    prev_loom = 0.0
    last_snapshot = 0.0
    last_scan = 0.0
    last_vidframe = 0.0
    # shared sight state: main loop refreshes the BRAIN² packet per frame;
    # the pump thread publishes it at 1Hz wall-clock
    sight_state = {"b2pkt": None}
    _sight_thread = threading.Thread(target=_sight_pump, args=(sight_state,),
                                     daemon=True, name="sight-pump")
    _sight_thread.start()
    log("sight pump started (1Hz perceptual stream)")
    feed_name = "?"
    _last_frame_t = [0.0]      # mutable cells for the measured-fps EMA
    _frame_dt_ema = [None]

    while not _shutdown:
        if run_seconds and (time.time() - start_t) >= run_seconds:
            log("run_seconds reached; stopping")
            break
        try:
            feed_name, playlist_url, referer = resolve_feed()
            log("feed resolved: %s" % feed_name)
            backoff = BACKOFF_START  # a good resolve resets the backoff
            seen = set()

            while not _shutdown:
                if run_seconds and (time.time() - start_t) >= run_seconds:
                    break
                # heartbeat
                now = time.time()
                if now - last_heartbeat >= HEARTBEAT_SECS:
                    last_heartbeat = now
                    event(type="heartbeat", feed=feed_name,
                          frames=frames_total,
                          uptime_s=int(now - start_t))
                    log("heartbeat feed=%s frames=%d" % (feed_name, frames_total))

                # per-minute body feed
                if now - minute_start >= BRAIN_MINUTE and acc["n"] > 0:
                    _feed_body(body, acc, feed_name)
                    acc = {"motion": 0.0, "color": 0.0, "looming": 0.0,
                           "contraction": 0.0, "n": 0}
                    minute_start = now

                try:
                    segs = _playlist_segments(playlist_url, referer)
                except Exception as e:
                    # playlist fetch failed: token may have expired -> re-resolve
                    log("playlist fetch failed (%s); re-resolving feed" % e)
                    break  # outer loop re-resolves (fallback included)

                new = [s for s in segs if s not in seen][-3:]
                if not new:
                    time.sleep(2)
                    continue
                for seg_url in new:
                    if _shutdown:
                        break
                    if run_seconds and (time.time() - start_t) >= run_seconds:
                        break
                    seen.add(seg_url)
                    if len(seen) > 60:
                        seen = set(list(seen)[-30:])
                    ts_path = os.path.join(_TMP, "seg.ts")
                    try:
                        _curl_file(seg_url, ts_path, referer=referer)
                    except Exception as e:
                        log("segment fetch failed (%s); re-resolving" % e)
                        break
                    decode_ok = True
                    try:
                        for rgb in _decode_frames(ts_path):
                            if _shutdown:
                                break
                            out = eye.frame(rgb)
                            frames_total += 1
                            # BRAIN² hi-res sight packet (pump publishes at 1Hz)
                            try:
                                sight_state["b2pkt"] = b2eye.frame(rgb)
                            except Exception as e:
                                log("b2eye frame failed: %s" % e)
                            # measured frame rate (EMA) for honest meta.json
                            now_w = time.time()
                            if _last_frame_t[0]:
                                dt = now_w - _last_frame_t[0]
                                _frame_dt_ema[0] = (dt if _frame_dt_ema[0] is None
                                                    else 0.9 * _frame_dt_ema[0] + 0.1 * dt)
                            _last_frame_t[0] = now_w
                            ring_write(rgb, (1.0 / _frame_dt_ema[0]
                                             if _frame_dt_ema[0] else None))
                            for k in acc:
                                if k != "n":
                                    acc[k] += out.get(k, 0.0)
                            acc["n"] += 1
                            # significant events
                            m = out["motion"]
                            if m >= MOTION_BOUT_ON and not in_bout:
                                in_bout = True
                                event(type="motion_bout", feed=feed_name,
                                      motion=round(m, 4), color=round(out["color"], 4),
                                      looming=round(out["looming"], 4),
                                      contraction=round(out["contraction"], 4))
                            elif m < MOTION_BOUT_OFF:
                                in_bout = False
                            # strong-motion snapshot: crossing 0.5 upward
                            if m >= STRONG_MOTION > prev_motion:
                                snapshot_event(rgb, feed_name, out, "motion")
                                clip_dump("motion")
                            prev_motion = m
                            if out["looming"] > LOOM_LOG:
                                event(type="looming", feed=feed_name,
                                      motion=round(m, 4), color=round(out["color"], 4),
                                      looming=round(out["looming"], 4),
                                      contraction=round(out["contraction"], 4))
                            # loom snapshot: rising edge over the hook threshold
                            if out["looming"] > LOOM_SNAP >= prev_loom:
                                snapshot_event(rgb, feed_name, out, "looming")
                                clip_dump("looming")
                            prev_loom = out["looming"]
                            if out["contraction"] > 0 and not in_contraction:
                                in_contraction = True
                                event(type="contraction", feed=feed_name,
                                      motion=round(m, 4),
                                      contraction=round(out["contraction"], 4))
                            elif out["contraction"] <= 0:
                                in_contraction = False
                            # on-demand vision: refresh the latest-frame snapshot
                            now_f = time.time()
                            if now_f - last_snapshot >= SNAPSHOT_SECS:
                                last_snapshot = now_f
                                snapshot_latest(rgb, feed_name, out)
                            # sparse scan snapshots: close the cron blind gap
                            if now_f - last_scan >= SCAN_SECS:
                                last_scan = now_f
                                scan_snapshot(rgb)
                            # eye-view video frames: each rendered with its OWN
                            # sight packet so motion glow/tracked boxes move
                            if now_f - last_vidframe >= VIDFRAME_SECS:
                                last_vidframe = now_f
                                try:
                                    from brain2.eyeview import render as _evr
                                    from PIL import Image as _PILImage
                                    vdir = os.path.join(_WORK, "video_frames")
                                    os.makedirs(vdir, exist_ok=True)
                                    _tmp = os.path.join(_TMP, "vf_raw.jpg")
                                    _PILImage.fromarray(rgb).save(_tmp, quality=88)
                                    _evr(_tmp, sight_state.get("b2pkt", {}),
                                         os.path.join(
                                             vdir, "vf_%d.jpg" % int(now_f)))
                                    _vfs = sorted(glob.glob(
                                        os.path.join(vdir, "vf_*.jpg")))
                                    for _old in _vfs[:-VIDFRAME_KEEP]:
                                        os.remove(_old)
                                except Exception as e:
                                    log("video frame render failed: %s" % e)
                    except Exception as e:
                        log("frame decode/retina failed (%s); continuing" % e)
                        decode_ok = False
                    try:
                        os.remove(ts_path)
                    except OSError:
                        pass
                    if not decode_ok:
                        break  # bad segment: re-fetch playlist / re-resolve feed
        except Exception as e:
            log("feed loop error: %s; backing off %ds" % (e, backoff))
            time.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX)

    # flush a final partial minute to the body
    if acc["n"] > 0:
        try:
            _feed_body(body, acc, feed_name)
        except Exception as e:
            log("final body feed failed: %s" % e)
    event(type="shutdown", feed=feed_name, frames=frames_total)
    log("vision_watch stopped cleanly (frames=%d)" % frames_total)


def _feed_body(body, acc, feed_name):
    """[MODELED] Per-minute mean sense intensities -> brain1 sense events.

    Mapping (all MODELED — the body receives intensities, not the feed):
      motion mean      -> sense("motion", intensity=mean)      if mean > 0.02
      looming mean     -> sense("looming", intensity=mean)     if mean > 0
      color mean       -> sense("color", intensity=mean)       if mean > 0.02
      contraction      -> NO bottle exists; logged only, honestly skipped.
    The virtual clock advances by the real elapsed minute so drive decay
    follows. State snapshot written for inspection.
    """
    n = acc["n"]
    means = {k: acc[k] / n for k in ("motion", "color", "looming", "contraction")}
    body.tick(BRAIN_MINUTE)
    fed = []
    if means["motion"] > 0.02:
        body.perceive({"kind": "sense", "bottle": "motion",
                       "intensity": min(1.0, means["motion"])})
        fed.append("motion=%.3f" % means["motion"])
    if means["looming"] > 0:
        body.perceive({"kind": "sense", "bottle": "looming",
                       "intensity": min(1.0, means["looming"])})
        fed.append("looming=%.3f" % means["looming"])
    if means["color"] > 0.02:
        body.perceive({"kind": "sense", "bottle": "color",
                       "intensity": min(1.0, means["color"])})
        fed.append("color=%.3f" % means["color"])
    # contraction: no sense bottle exists in brain1 — logged, not fed (honest).
    try:
        with open(_BRAIN_STATE, "w") as f:
            json.dump({"ts": _now_iso(), "feed": feed_name,
                       "minute_means": {k: round(v, 4) for k, v in means.items()},
                       "body": body.state()}, f)
    except OSError as e:
        log("brain state write failed: %s" % e)
    log("body fed [%s] (%d frames)" % (", ".join(fed) if fed else "quiet", n))


def main():
    run_seconds = 0
    for i, a in enumerate(sys.argv[1:]):
        if a == "--run-seconds" and i + 1 < len(sys.argv[1:]):
            run_seconds = int(sys.argv[1:][i + 1])
    try:
        watch_forever(run_seconds=run_seconds)
    except KeyboardInterrupt:
        log("interrupted")


if __name__ == "__main__":
    main()
