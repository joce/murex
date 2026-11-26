"""Take the reference frame and contact sheets of the steps from a video.

    uv run --with imageio-ffmpeg python frames.py VIDEO OUT_DIR
        [--final MM:SS] [--sheet NAME FROM TO [--sheet ...]] [--count 12]

``--final`` writes OUT_DIR/final.png, the frame at that time at 640 x 480.
Each ``--sheet NAME FROM TO`` writes OUT_DIR/NAME.jpg: ``--count`` frames
evenly spaced from FROM to TO, in rows of four, each 480 px wide, to see how
the hand moves through one step.
"""

import argparse
import os
import subprocess
import tempfile

from PIL import Image


def seconds(text):
    """MM:SS, H:MM:SS or plain seconds."""
    total = 0.0
    for part in text.split(":"):
        total = total * 60 + float(part)
    return total


def grab(ffmpeg, video, t, out):
    cmd = [ffmpeg, "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", video]
    subprocess.run([*cmd, "-frames:v", "1", out], check=True)
    return Image.open(out).convert("RGB")


def main():
    import imageio_ffmpeg  # (uv run --with imageio-ffmpeg)

    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("video")
    p.add_argument("out")
    p.add_argument("--final")
    p.add_argument("--sheet", nargs=3, action="append", default=[])
    p.add_argument("--count", type=int, default=12)
    a = p.parse_args()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(a.out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        frame = os.path.join(tmp, "frame.png")
        if a.final:
            im = grab(ffmpeg, a.video, seconds(a.final), frame)
            im.resize((640, 480), Image.Resampling.LANCZOS).save(
                os.path.join(a.out, "final.png")
            )
        for name, t0, t1 in a.sheet:
            t0, t1 = seconds(t0), seconds(t1)
            n = max(1, a.count)
            times = [t0 + (t1 - t0) * k / max(1, n - 1) for k in range(n)]
            shots = [grab(ffmpeg, a.video, t, frame) for t in times]
            w = 480
            h = round(shots[0].height * w / shots[0].width)
            sheet = Image.new("RGB", (4 * w, h * ((n + 3) // 4)))
            for k, im in enumerate(shots):
                small = im.resize((w, h), Image.Resampling.LANCZOS)
                sheet.paste(small, ((k % 4) * w, (k // 4) * h))
            sheet.save(os.path.join(a.out, f"{name}.jpg"), quality=88)
            print(os.path.join(a.out, f"{name}.jpg"))


if __name__ == "__main__":
    main()
