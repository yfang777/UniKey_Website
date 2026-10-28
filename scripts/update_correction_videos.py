#!/usr/bin/env python3
"""Rebuild the three correction clips from validated lossless compositions.

Run with the sibling visualization project's codegen_realworld Python environment.
Pack Battery reuses its existing compositor's first-threshold mode. Cropping the
15-pixel left gutter plus one image column keeps H.264's dimensions even without
stretching the scene or changing any chart pixels in the lossless input.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import imageio.v2 as imageio
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "output/correction-videos"
REPORT = ROOT / "data/correction-videos.json"
TASKS = {
    "arrange-table": ("table_arrange", 9),
    "flip-and-arrange-shoe": ("flip_then_arrange_shoe", 7),
    "pack-battery": ("pack_battery", 8),
}
FPS = 30
CROP = (16, 0, 1920, 1080)
SIZE = (1904, 1080)


def read(path):
    return json.loads(path.read_text())


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def threshold_rewind(rows, threshold):
    crossing = next(i for i, row in enumerate(rows)
                    if row["phase"] in ("policy", "policy_failure")
                    and any(bar["value_cm"] is not None and bar["value_cm"] > threshold
                            for bar in row["bars"]))
    rewind = next(i for i, row in enumerate(rows) if row["phase"] == "rewind")
    assert rewind == crossing + 1, "Rewind must immediately follow the first crossing"
    assert rows[rewind]["source_render_frame_zero_based"] == rows[crossing]["source_render_frame_zero_based"]
    assert rows[rewind]["bars"] == rows[crossing]["bars"]
    return {"threshold_cm": threshold, "first_crossing_frame_zero_based": crossing,
            "first_crossing_seconds": crossing / FPS,
            "first_crossing_value_cm": max(bar["value_cm"] or 0 for bar in rows[crossing]["bars"]),
            "rewind_start_frame_zero_based": rewind, "rewind_start_seconds": rewind / FPS}


def build(task, source_root, verify_rewind):
    source_task, version = TASKS[task]
    source = source_root / "data/automatic_detection_correction" / f"{source_task}_v{version}"
    timeline = read(source / "timeline.json")
    validation = read(source / "validation.json")
    source_video = source / f"policy_with_divergence_v{version}.mp4"
    assert validation["passed"] and sha256(source_video) == validation["output_sha256"]
    assert timeline["fps"] == FPS and timeline["resolution"] == [1920, 1080]
    rows = timeline["timeline"]
    assert len(rows) == timeline["frames"]
    rewind_report = verify_rewind(rows, validation["fixed_axis_max_cm"])
    trigger = threshold_rewind(rows, rewind_report["threshold_cm"]) if task != "flip-and-arrange-shoe" else None
    if task == "pack-battery":
        old_rows = read(source.parent / "pack_battery_v7/timeline.json")["timeline"]
        correction = lambda sequence: [(row["source_file"], row["source_render_frame_zero_based"], row["bars"])
                                       for row in sequence if row["phase"].startswith("correction")]
        assert correction(rows) == correction(old_rows), "The correction handoff and motion must be preserved"

    work = WORK / task
    sequence = work / "sequence"
    sequence.mkdir(parents=True, exist_ok=True)
    paths, source_hashes = [], {}
    for index, row in enumerate(rows):
        path = Path(row["composite_file"]).resolve(strict=True)
        if str(path) not in source_hashes:
            source_hashes[str(path)] = sha256(path)
        link = sequence / f"frame_{index:06d}.png"
        if link.is_symlink():
            link.unlink()
        link.symlink_to(path)
        paths.append(path)

    transitions = {0}
    transitions.update(i for i in range(1, len(rows))
                       if rows[i]["phase"] != rows[i - 1]["phase"]
                       or rows[i].get("speed_label") != rows[i - 1].get("speed_label"))
    previews = {len(rows) - 1} | transitions | {i - 1 for i in transitions if i}
    temporary = work / "rollout.mp4"
    print(f"{task}: encoding {len(rows)} frames, {SIZE[0]} x {SIZE[1]}", flush=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-start_number", "0",
                    "-i", str(sequence / "frame_%06d.png"), "-frames:v", str(len(rows)), "-an",
                    "-vf", "crop=1904:1080:16:0,setsar=1", "-c:v", "libx264", "-threads", "4",
                    "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-force_key_frames", ",".join(str(i / FPS) for i in sorted(transitions)),
                    "-movflags", "+faststart", str(temporary)], check=True)
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames", "-show_streams",
        "-show_entries", "stream=codec_name,width,height,avg_frame_rate,duration:frame=best_effort_timestamp_time",
        "-of", "json", str(temporary)], text=True))
    stream = probe["streams"][0]
    assert (stream["codec_name"], stream["width"], stream["height"], stream["avg_frame_rate"]) == ("h264", *SIZE, "30/1")
    np.testing.assert_allclose([float(frame["best_effort_timestamp_time"]) for frame in probe["frames"]],
                               np.arange(len(rows)) / FPS, atol=1e-6, rtol=0)
    assert abs(float(stream["duration"]) - len(rows) / FPS) < 1e-5
    errors, chart_errors, left_white = [], [], []
    with imageio.get_reader(str(temporary), format="FFMPEG") as reader:
        for index, pixels in enumerate(reader):
            with Image.open(paths[index]) as raw:
                assert raw.size == (1920, 1080)
                expected = np.asarray(raw.convert("RGB").crop(CROP), dtype=np.int16)
            difference = np.abs(pixels.astype(np.int16) - expected)
            errors.append(float(difference.mean()))
            chart_errors.append(float(difference[:, 1470 - CROP[0]:].mean()))
            left_white.append(float(np.all(pixels[:, :2] >= 245, axis=2).mean(axis=0).max()))
            if index == 0:
                Image.fromarray(pixels).save(work / "poster.jpg", quality=95)
            if index in previews:
                Image.fromarray(pixels).save(work / f"frame_{index:06d}_{rows[index]['phase']}.jpg", quality=90)
    assert len(errors) == len(rows) and max(errors) < 4, "Encoded frames differ from the lossless inputs"
    assert max(chart_errors) < 2, "The chart must remain sharp and fully visible"
    assert max(left_white) < .95, "A white gutter remains at the left edge"
    assert all(sha256(Path(path)) == digest for path, digest in source_hashes.items())

    destination = ROOT / "assets/videos/pipeline/failure-detection-correction" / task
    for name in ("rollout.mp4", "poster.jpg"):
        existing = destination / name
        backup = work / f"before_{existing.stem}_{sha256(existing)[:12]}{existing.suffix}"
        if not backup.exists():
            shutil.copy2(existing, backup)
        shutil.copy2(work / name, existing)

    report = {"source": str(source.relative_to(source_root)),
              "source_video_sha256": validation["output_sha256"],
              "source_timeline_sha256": sha256(source / "timeline.json"),
              "video_sha256": sha256(destination / "rollout.mp4"),
              "poster_sha256": sha256(destination / "poster.jpg"),
              "resolution": list(SIZE), "fps": FPS, "frames": len(rows), "duration_seconds": len(rows) / FPS,
              "source_crop_xywh": [16, 0, *SIZE], "scene_stretched": False,
              "decoded_frames_compared": len(errors), "timestamps_verified": True,
              "maximum_encoded_pixel_error": max(errors), "maximum_encoded_chart_error": max(chart_errors),
              "maximum_left_edge_white_fraction": max(left_white),
              "threshold_trigger": trigger, **rewind_report}
    print(f"PASS: {task}, {len(rows) / FPS:.3f}s; every frame decoded and compared", flush=True)
    return report


def update_pages(tasks):
    for name in ("index.html", "preview-domain-randomization.html"):
        path = ROOT / name
        if not path.exists():
            continue
        html = path.read_text()
        for task in tasks:
            directory = f"./assets/videos/pipeline/failure-detection-correction/{task}/"
            for filename in ("rollout.mp4", "poster.jpg"):
                url = directory + filename
                digest = sha256(ROOT / url)[:12]
                html = re.sub(re.escape(url) + r"(?:\?v=[a-f0-9]+)?", url + "?v=" + digest, html)
            pattern = r'(<video\b[^>]*poster="' + re.escape(directory) + r'poster\.jpg[^>]*\bwidth=")\d+(" height=")\d+(")'
            html, count = re.subn(pattern, rf"\g<1>{SIZE[0]}\g<2>{SIZE[1]}\g<3>", html)
            assert count == 1, f"Expected one correction player for {task} in {name}"
        css_hash = sha256(ROOT / "assets/site.css")[:12]
        html = re.sub(r"(\./assets/site\.css\?v=)[a-f0-9]+", rf"\g<1>{css_hash}", html)
        path.write_text(html)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT.parent / "Codegen_Blender_Visualization")
    parser.add_argument("--task", choices=["all", *TASKS], default="all")
    args = parser.parse_args()
    source_root = args.source_root.resolve(strict=True)
    sys.path.insert(0, str(source_root))
    from render.create_task_cinematic_rewinds import compose
    from render.divergence_chart import verify_rewind

    tasks = TASKS if args.task == "all" else [args.task]
    if "pack-battery" in tasks:
        source = source_root / "data/automatic_detection_correction/pack_battery_v8"
        if not (source / "validation.json").exists():
            compose("pack_battery", first_threshold=True)
    report = read(REPORT) if REPORT.exists() else {}
    for task in tasks:
        report[task] = build(task, source_root, verify_rewind)
        REPORT.write_text(json.dumps(report, indent=2) + "\n")
    update_pages(tasks)


if __name__ == "__main__":
    main()
