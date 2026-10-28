"""Recreate the RoboTwin keypoint videos without stage captions.

Uses the renderer's clean clips and recorded pixel coordinates, so camera,
keypoints, frame counts, and playback timing stay aligned with the source.
Run with the Datagen Python environment (imageio, numpy, Pillow, PyYAML).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw
import yaml

ROOT = Path(__file__).resolve().parents[1]


def draw_keypoints(rgb, frame, style):
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image)
    projection = frame["projection"]
    for first, second in frame["connections"]:
        if not projection[first]["in_frame"] or not projection[second]["in_frame"]:
            continue
        start = np.asarray(projection[first]["pixel"])
        end = np.asarray(projection[second]["pixel"])
        length = np.linalg.norm(end - start)
        if length < 1:
            continue
        direction = (end - start) / length
        for distance in np.arange(0, length, style["dash_length"] + style["dash_gap"]):
            segment = [tuple(start + distance * direction),
                       tuple(start + min(distance + style["dash_length"], length) * direction)]
            draw.line(segment, fill="#303030", width=style["line_width"] + 2)
            draw.line(segment, fill="white", width=style["line_width"])
    for name, point in projection.items():
        if not point["in_frame"]:
            continue
        x, y = point["pixel"]
        radius = style["point_radius"]
        color = style["colors"][frame["roles"][name]]
        outline = [(x, y - radius - 2), (x + radius + 2, y),
                   (x, y + radius + 2), (x - radius - 2, y)]
        diamond = [(x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)]
        draw.polygon(outline, outline="white", width=style["outline_width"])
        draw.polygon(diamond, fill=color, outline=color, width=3)
    return np.asarray(image)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=ROOT.parent / "Codegen_Blender_Visualization_artifacts/robotwin_blender_20261028")
    parser.add_argument("--task", help="Update only this task directory, for example 01_adjust_bottle_01.")
    parser.add_argument("--renderer", choices=("MuJoCo", "Blender Cycles"), default="Blender Cycles")
    args = parser.parse_args()
    manifest_path = ROOT / "data/visualization-media.json"
    manifest = json.loads(manifest_path.read_text())
    html_path = ROOT / "index.html"
    tasks = [task for task in manifest["tasks"] if args.task is None or task["task"] == args.task]
    if not tasks:
        parser.error("No tasks match the requested task directory and renderer.")
    for task in tasks:
        episode = args.source / task["task"] / task["episode"]
        if args.renderer == "Blender Cycles":
            source_info = json.loads((episode / "render_info.json").read_text())
            if source_info["engine"] != "CYCLES" or source_info["preview_only"]:
                raise ValueError("Blender imports require a complete Cycles render.")
        source_files = [episode / name for name in ("clean.mp4", "coordinates.json", "style.yaml")]
        coordinates = json.loads(source_files[1].read_text())
        style = yaml.safe_load(source_files[2].read_text())
        if len(coordinates) != task["frames"]:
            raise ValueError(f"Coordinate count differs for {task['task']}.")
        destination = ROOT / "media/robotwin" / task["task"]
        temporary = destination / "rollout-caption-free.mp4"
        with imageio.get_reader(source_files[0]) as reader:
            metadata = reader.get_meta_data()
            if (list(metadata["size"]) != task["resolution"] or metadata["fps"] != task["fps"]
                    or reader.count_frames() != task["frames"]):
                raise ValueError(f"Clean source clip differs for {task['task']}.")
            with imageio.get_writer(temporary, fps=task["fps"], codec="libx264", quality=None,
                                    macro_block_size=1,
                                    ffmpeg_params=["-crf", "18", "-preset", "medium", "-threads", "2",
                                                   "-movflags", "+faststart"]) as writer:
                for index, rgb in enumerate(reader):
                    writer.append_data(draw_keypoints(rgb, coordinates[index], style))
        probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                                "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames,duration",
                                "-of", "json", str(temporary)], check=True, capture_output=True, text=True)
        stream = json.loads(probe.stdout)["streams"][0]
        if ([stream["width"], stream["height"]] != task["resolution"]
                or int(stream["nb_read_frames"]) != task["frames"]
                or stream["r_frame_rate"] != f"{task['fps']}/1"
                or abs(float(stream["duration"]) - task["duration_s"]) > 1 / task["fps"]):
            raise ValueError(f"Caption-free export differs for {task['task']}.")
        video = destination / "rollout.mp4"
        temporary.replace(video)
        poster = destination / "poster.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.5", "-i", str(video),
                        "-frames:v", "1", "-q:v", "2", str(poster)], check=True)
        task["sha256"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (video, poster)}
        task["source_sha256"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files}
        task["stage_labels"] = False
        task["renderer"] = args.renderer
        if args.renderer == "Blender Cycles":
            render_info = destination / "render-info.json"
            shutil.copyfile(episode / "render_info.json", render_info)
            task["render_info"] = str(render_info.relative_to(ROOT))
            task["sha256"][render_info.name] = hashlib.sha256(render_info.read_bytes()).hexdigest()
        print(f"Updated {task['task']}: {task['frames']} frames, {task['duration_s']:g} seconds, no stage captions.",
              flush=True)
    html = html_path.read_text()
    for task in tasks:
        if args.renderer == "Blender Cycles":
            html = re.sub(r'<video\b[^>]*>', lambda match: match[0].replace(
                "demonstration in MuJoCo", "demonstration rendered in Blender")
                if f"/{task['task']}/poster.jpg" in match[0] else match[0], html)
        for filename, digest in task["sha256"].items():
            if filename not in ("rollout.mp4", "poster.jpg"):
                continue
            relative = f"./media/robotwin/{task['task']}/{filename}"
            html, count = re.subn(re.escape(relative) + r'(?:\?v=[^"<>\s]+)?',
                                 relative + "?v=" + digest[:12], html)
            if count != (2 if filename == "rollout.mp4" else 1):
                raise ValueError(f"Unexpected website references for {relative}: {count}.")
    manifest["description"] = "RoboTwin keypoint program demonstrations without stage captions."
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    html_path.write_text(html)


if __name__ == "__main__":
    main()
