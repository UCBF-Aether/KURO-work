#!/usr/bin/env python3
"""Watch a video URL live through the BRAIN2 eye. Writes sight packets to
_work/movie_sight.jsonl + _work/movie_latest.json for live reading."""
import sys, os, json, time, subprocess, shutil
sys.path.insert(0, os.path.expanduser("~/workspace/fly-brain/retina"))
sys.path.insert(0, os.path.expanduser("~/workspace/fly-brain"))
sys.path.insert(0, os.path.expanduser("~/workspace/.pydeps"))
os.chdir(os.path.expanduser("~/workspace/fly-brain/retina/_work"))

from brain2.eye import Brain2Eye
from brain2.cortex import Tracker, scene_summary
import numpy as np

url = sys.argv[1]
eye = Brain2Eye()          # 8x hi-res eye
tracker = Tracker()

# pull frames via ffmpeg from the stream URL, raw rgb, 480px wide, ~8fps
W = 480
ffmpeg = ["ffmpeg", "-hide_banner", "-loglevel", "error",
          "-i", url, "-vf", f"scale={W}:-1", "-r", "8",
          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
proc = subprocess.Popen(ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**7)
fw = None
pkt_n = 0
t0 = time.time()
sj = open("movie_sight.jsonl", "w")
try:
    while True:
        # read one frame (need height first)
        if fw is None:
            # probe: read enough for header via ffprobe
            pr = subprocess.run(["ffprobe", "-hide_banner", "-loglevel", "error",
                                 "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                 "-of", "csv=p=0", url],
                                capture_output=True, text=True, timeout=30)
            ow, oh = map(int, pr.stdout.strip().split(","))
            fh = int(oh * W / ow)
            fw = (W, fh)
            print("frame size:", fw, flush=True)
        raw = proc.stdout.read(fw[0]*fw[1]*3)
        if len(raw) < fw[0]*fw[1]*3:
            print("stream ended", flush=True)
            break
        rgb = np.frombuffer(raw, dtype=np.uint8).reshape(fw[1], fw[0], 3)
        out = eye.frame(rgb, dt=1.0/8)
        objs = tracker.update(out["blobs"], dt=1.0/8)
        pkt = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
               "t": round(time.time()-t0, 1),
               "objects": objs,
               "scene": scene_summary(objs),
               "motion": round(float(out["motion_mean"]), 3)}
        sj.write(json.dumps(pkt) + "\n"); sj.flush()
        json.dump(pkt, open("movie_latest.json", "w"))
        pkt_n += 1
        if pkt_n % 40 == 0:
            print(f"t={pkt['t']}s {pkt['scene']}", flush=True)
finally:
    proc.terminate()
    sj.close()
print("done, packets:", pkt_n)
