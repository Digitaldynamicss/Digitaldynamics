#!/usr/bin/env python3
"""Render the Auto Scan Honda 15-second reel.

  python3 reel/render.py                 # full render -> reel/output/
  python3 reel/render.py --still 1.5 5 12.5   # preview single frames as PNG
  python3 reel/render.py --no-audio      # visuals only (fast iteration)

Everything editable (offers, copy, phone, timings, colours) lives in reel/config.json.
Photos/logos/voiceover dropped into reel/assets/ are picked up automatically."""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))

from PIL import Image  # noqa: E402

import audio  # noqa: E402
from scenes import Reel  # noqa: E402

OUT = os.path.join(HERE, "output")


def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(reel, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, (t0, t1, s) in enumerate(reel.captions, 1):
            f.write(f"{i}\n{srt_time(t0)} --> {srt_time(t1)}\n{s}\n\n")


def render_video(reel, cfg, path):
    v = cfg["video"]
    n = int(round(v["duration"] * v["fps"]))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f'{v["width"]}x{v["height"]}',
           "-r", str(v["fps"]), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(n):
        frame = reel.frame(i / v["fps"]).convert("RGB")
        proc.stdin.write(frame.tobytes())
        if i % 30 == 0:
            print(f"  frame {i:3d}/{n}  ({time.time() - t0:5.1f}s)", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg video encode failed")


def mux(video, wav, path, duration):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{duration:.3f}",
                    "-movflags", "+faststart", path], check=True)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def contact_sheet(reel, times, path):
    thumbs = [reel.frame(t).convert("RGB").resize((270, 480), Image.LANCZOS) for t in times]
    cols = 6
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 280 + 10, rows * 490 + 10), (30, 30, 30))
    for k, th in enumerate(thumbs):
        sheet.paste(th, (10 + (k % cols) * 280, 10 + (k // cols) * 490))
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", nargs="*", type=float, help="render PNG stills at these times and exit")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--name", default="auto_scan_honda_reel_15s")
    args = ap.parse_args()

    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    os.makedirs(OUT, exist_ok=True)
    reel = Reel(cfg)

    if args.still is not None:
        for t in args.still:
            p = os.path.join(OUT, f"still_{t:05.2f}s.png")
            reel.frame(t).convert("RGB").save(p)
            print(p)
        return

    log = []
    base = os.path.join(OUT, args.name)
    silent = base + "_video_only.mp4"
    print("Rendering frames ...")
    render_video(reel, cfg, silent)
    write_srt(reel, base + ".srt")
    contact_sheet(reel, [0.4, 1.2, 2.4, 3.6, 4.6, 5.6, 7.0, 8.2, 9.5, 10.5, 11.6, 14.5], base + "_contact_sheet.jpg")

    final = base + ".mp4"
    if args.no_audio:
        os.replace(silent, final)
    else:
        print("Building soundtrack ...")
        wav = base + "_mix.wav"
        source = audio.build_soundtrack(cfg, wav, log)
        mux(silent, wav, final, cfg["video"]["duration"])
        os.remove(silent)
        log.append(("voiceover source", source))

    info = probe(final)
    print("\nAudio log:")
    for k, v in log:
        print(f"  {k:16s} {v}")
    print("\nPhotos used (False = illustration placeholder):", reel.photos_used)
    print("\nOutput:", final)
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
