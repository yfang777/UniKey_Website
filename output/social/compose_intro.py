#!/usr/bin/env python3
"""Compose the UniKey introduction montage from the original local videos.

Requires FFmpeg, Pillow, Brotli, and a current fontTools release (4.65+).
"""

from fractions import Fraction
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "Codegen_Blender_Visualization/data"
WORK = Path(tempfile.mkdtemp(prefix="unikey-intro-render-"))
VIDEO = OUT / "unikey-introduction.mp4"
FPS = 30
TRANSITION = Fraction(12, FPS)
SOURCES = {
    "generation": SOURCE / "live_text_generation/hang_mug_grid/hang_mug_v5_shrink_into_grid_4x3.mp4",
    "correction": SOURCE / "automatic_detection_correction/hang_mug_v5/policy_with_divergence_v4_3.mp4",
    "randomization": SOURCE / "domain_randomization/hang_mug/domain_randomization_mujoco.mp4",
    "realworld": Path("/home/yuan/Desktop/hang_mug_w_text.mp4"),
}


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path),
    ]))


def make_font(weight):
    font = TTFont(ROOT / "assets/fonts/source-serif-4-latin.woff2")
    if "fvar" in font:
        axes = {axis.axisTag for axis in font["fvar"].axes}
        values = {"wght": weight} if "wght" in axes else {}
        font = instantiateVariableFont(font, values, inplace=True)
    font.flavor = None
    path = WORK / f"source-serif-{weight}.ttf"
    font.save(path)
    return path


REGULAR = make_font(400)
SEMIBOLD = make_font(600)
FILTERS = []


def draw_text(text, size, x, y, bold=False, color="0x0c0c0c", max_width=None):
    font = SEMIBOLD if bold else REGULAR
    if max_width is not None:
        assert ImageFont.truetype(str(font), size).getlength(text) <= max_width, text
    path = WORK / f"text-{hashlib.sha256(text.encode()).hexdigest()[:12]}.txt"
    path.write_text(text)
    return (
        f"drawtext=fontfile={font}:textfile={path}:expansion=none:fontsize={size}"
        f":fontcolor={color}:x={x}:y={y}"
    )


def normalize(index, label):
    FILTERS.append(
        f"[{index}:v]fps={FPS},settb=1/{FPS},setpts=PTS-STARTPTS,"
        "scale=1600:900:force_original_aspect_ratio=decrease:flags=lanczos,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf6f6ef,"
        f"setsar=1,format=yuv420p[{label}]"
    )


def decorate(source, target, title, subtitle, number):
    filters = [
        "drawbox=x=160:y=78:w=1600:h=1:color=0x0c0c0c@0.25:t=fill",
        draw_text("UniKey", 64, "160", "5", bold=True, max_width=240),
        draw_text(title, 52, "1760-tw", "13", max_width=1200),
        draw_text(subtitle, 42, "160", "1007", color="0x454540", max_width=1440),
        draw_text(f"{number:02d} / 04", 32, "1760-tw", "1014", color="0x65655f"),
    ]
    FILTERS.append(f"[{source}]" + ",".join(filters) + f"[{target}]")


for path in SOURCES.values():
    if not path.is_file():
        raise FileNotFoundError(path)

correction_info = probe(SOURCES["correction"])
correction_stream = next(s for s in correction_info["streams"] if s["codec_type"] == "video")
assert Fraction(correction_stream["avg_frame_rate"]) == FPS
correction_duration = Fraction(int(correction_stream["nb_frames"]), FPS)

command = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y", "-filter_complex_threads", "1"]
command += ["-ss", "1.1", "-t", "3.0", "-i", str(SOURCES["generation"])]
command += ["-ss", "7.9", "-t", "2.8", "-i", str(SOURCES["generation"])]
command += ["-i", str(SOURCES["correction"])]
command += ["-ss", "0.6", "-t", "3.8", "-i", str(SOURCES["randomization"])]
command += ["-ss", "55.133333", "-t", "4.4", "-i", str(SOURCES["realworld"])]
command += ["-f", "lavfi", "-t", "1.4", "-i", "color=c=0xf6f6ef:s=1920x1080:r=30"]
command += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]

for index in range(5):
    normalize(index, f"raw{index}")

FILTERS.append("[raw0][raw1]xfade=transition=fade:duration=0.2:offset=2.8[generation]")
decorate("generation", "chapter1", "Scalable Data Generation",
         "Keypoint programs generate expert demonstrations at scale.", 1)
decorate("raw2", "chapter2", "Automatic Corrective Data Generation",
         "Detect divergence. Generate corrections. Improve the policy.", 2)
decorate("raw3", "chapter3", "Sim-to-Real: Domain Randomization",
         "Randomize lighting, textures, backgrounds, and cameras.", 3)
decorate("raw4", "chapter4", "Robust Real-World Rollout",
         "30-minute evaluation (excerpt) | 100% success | 30× playback", 4)

closing = [
    draw_text("UniKey", 120, "(w-tw)/2", "365", bold=True, max_width=1600),
    draw_text("From keypoint programs to robust manipulation", 48, "(w-tw)/2", "545", max_width=1600),
    draw_text("Columbia University · Toyota Research Institute", 40, "(w-tw)/2", "645",
              color="0x65655f", max_width=1600),
]
FILTERS.append("[5:v]settb=1/30,setpts=PTS-STARTPTS,format=yuv420p," + ",".join(closing) + "[closing]")

durations = [Fraction(28, 5), correction_duration, Fraction(19, 5), Fraction(22, 5), Fraction(7, 5)]
labels = ["chapter1", "chapter2", "chapter3", "chapter4", "closing"]
current = labels[0]
duration = durations[0]
for index, (following, following_duration) in enumerate(zip(labels[1:], durations[1:]), 1):
    offset = duration - TRANSITION
    target = f"joined{index}"
    FILTERS.append(
        f"[{current}][{following}]xfade=transition=fade:duration={float(TRANSITION):.6f}"
        f":offset={float(offset):.6f}[{target}]"
    )
    current = target
    duration += following_duration - TRANSITION
FILTERS.append(f"[{current}]fps=30,format=yuv420p[video]")

graph = WORK / "filters.txt"
graph.write_text(";\n".join(FILTERS))
command += [
    "-filter_complex_script", str(graph), "-map", "[video]", "-map", "6:a",
    "-t", f"{float(duration):.9f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
    "-profile:v", "high", "-level:v", "4.1", "-pix_fmt", "yuv420p",
    "-maxrate", "15M", "-bufsize", "30M", "-c:a", "aac", "-b:a", "128k",
    "-ar", "48000", "-movflags", "+faststart", str(VIDEO),
]

print(f"Rendering {float(duration):.3f}s introduction to {VIDEO}", flush=True)
subprocess.run(command, check=True)
result = probe(VIDEO)
video_stream = next(s for s in result["streams"] if s["codec_type"] == "video")
assert (video_stream["width"], video_stream["height"], video_stream["pix_fmt"]) == (1920, 1080, "yuv420p")
assert Fraction(video_stream["avg_frame_rate"]) == FPS
assert abs(float(result["format"]["duration"]) - float(duration)) < 0.08

manifest = {
    "output": str(VIDEO),
    "duration_seconds": float(duration),
    "resolution": [1920, 1080],
    "fps": FPS,
    "sources": {name: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                for name, path in SOURCES.items()},
    "edits": [
        {"chapter": "Data Generation", "source": "generation", "ranges_seconds": [[1.1, 4.1], [7.9, 10.7]],
         "internal_crossfade_seconds": 0.2},
        {"chapter": "Corrective Data Generation", "source": "correction", "ranges_seconds": [[0, float(correction_duration)]]},
        {"chapter": "Domain Randomization", "source": "randomization", "ranges_seconds": [[0.6, 4.4]]},
        {"chapter": "Real-World Rollout", "source": "realworld", "ranges_seconds": [[55.133333, 59.533333]],
         "speed_already_encoded_in_source": 30},
        {"chapter": "Closing Card", "duration_seconds": 1.4},
    ],
    "chapter_crossfade_seconds": float(TRANSITION),
    "additional_playback_speed_multiplier": 1,
    "audio": "Silent AAC stereo track",
    "font": str(ROOT / "assets/fonts/source-serif-4-latin.woff2"),
    "background": "#f6f6ef",
}
(OUT / "unikey-introduction-edit.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Done: {VIDEO} ({VIDEO.stat().st_size / 1024 / 1024:.1f} MiB)", flush=True)
