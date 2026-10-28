#!/usr/bin/env python3
"""Render RoboTwin demonstrations in Blender, retaining saved cameras and timelines.

Run with the codegen_realworld Python environment (MuJoCo 3.8.0). Intermediates
are stored outside the website. Import the completed clip with
update_robotwin_media.py. Use --task to select one task or --resume to retain
completed clips; --preview renders four representative frames per task.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT.parent / "Codegen_Blender_Visualization_artifacts"


def render_blender(directory, visualization, samples, preview):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector

    request = json.loads((directory / "render_request.json").read_text())
    spec = importlib.util.spec_from_file_location(
        "robotwin_scene_builder", visualization / "render/create_blender_scene.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    args = builder.parse_args([
        "--animation-pkl", str(directory / "animation.pkl"),
        "--blend-out", str(directory / "scene.blend"),
        "--engine", "CYCLES", "--cycles-render-device", "gpu",
        "--samples", str(samples), "--camera-mode", "mujoco",
        "--width", str(request["resolution"][0]), "--height", str(request["resolution"][1]),
    ])
    builder.build_scene(args)
    scene = bpy.context.scene
    scene.camera.data.dof.use_dof = False
    scene.render.use_motion_blur = False
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1.0
    scene.cycles.filter_width = 0.5
    scene.cycles.adaptive_threshold = 0.03
    scene.cycles.denoiser = "OPTIX"
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 15
    scene.view_settings.exposure = -0.3

    for obj in list(scene.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    for name, position, energy, size in (
        ("Key", (1.2, -0.4, 1.8), 110, 1.4),
        ("Fill", (0.4, 1.0, 1.4), 55, 1.2),
        ("Rim", (-0.5, 0.3, 1.6), 70, 1.0),
    ):
        bpy.ops.object.light_add(type="AREA", location=position)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (Vector((0.25, 0.05, 0.25)) - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.88, 0.90, 0.93, 1)
    background.inputs["Strength"].default_value = 0.25

    coordinates = json.loads((directory / "coordinates.json").read_text())
    width, height = request["resolution"]
    errors = []
    for frame in coordinates:
        for name, point in frame["points"].items():
            projected = world_to_camera_view(scene, scene.camera, Vector(point))
            expected = frame["projection"][name]["pixel"]
            actual = (projected.x * width - 0.5, (1 - projected.y) * height - 0.5)
            errors.append(sum((a - b) ** 2 for a, b in zip(actual, expected)) ** 0.5)
    projection_error = max(errors)
    if projection_error > 0.02:
        raise ValueError(f"Blender camera differs from keypoint projections by {projection_error:g} pixels.")

    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(directory / "scene.blend"))
    count = request["frames"]
    frames = (1, 1 + count // 3, 1 + 2 * count // 3, count) if preview else range(1, count + 1)
    frames_dir = directory / "frames"
    frames_dir.mkdir(exist_ok=True)
    for frame in frames:
        output = frames_dir / f"frame_{frame:06d}.png"
        if output.exists():
            continue
        scene.frame_set(frame)
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {frame}/{request['frames']}", flush=True)
    report = {
        **request,
        "renderer": "Blender Cycles",
        "blender_version": bpy.app.version_string,
        "engine": scene.render.engine,
        "device": scene.cycles.device,
        "samples": scene.cycles.samples,
        "denoising": scene.cycles.use_denoising,
        "denoiser": scene.cycles.denoiser,
        "preview_only": preview,
        "max_keypoint_projection_error_px": projection_error,
        "keypoint_projections_checked": len(errors),
        "frame_mapping": "Blender frame = source row + 1; native frame rate, no resampling.",
    }
    (directory / "render_info.json").write_text(json.dumps(report, indent=2) + "\n")


def render_task(args, task):
    directory = args.work_dir.resolve() / task["task"] / task["episode"]
    if args.resume and (directory / "clean.mp4").is_file():
        report = json.loads((directory / "render_info.json").read_text())
        if (report["engine"] != "CYCLES" or report["preview_only"]
                or (report["frames"], report["fps"], report["resolution"], report["samples"])
                != (task["frames"], task["fps"], task["resolution"], args.samples)):
            raise ValueError(f"Completed render differs from requested settings: {task['task']}")
        print(f"Retained completed Blender video: {task['task']}", flush=True)
        return

    reference = args.source.resolve() / task["task"] / task["episode"]
    info = json.loads((reference / "render_info.json").read_text())
    original_episode = Path(info["source_episode"])
    recording = args.recording or original_episode
    if not recording.is_dir():
        recording = ARCHIVE / "20261008T164407Z/data" / recording.relative_to(args.visualization / "data")
    recording = recording.resolve()
    metadata = json.loads((recording / "metadata.json").read_text())
    if (metadata["frames"], metadata["fps"]) != (info["frame_count"], info["fps"]):
        raise ValueError("Recording and keypoint overlays have different timelines.")
    directory.mkdir(parents=True, exist_ok=True)
    scene_dir = directory / "scene"
    scene_dir.mkdir(exist_ok=True)
    tree = ET.parse(reference / "render_scene.xml")
    for element in tree.getroot().iter():
        if "file" in element.attrib:
            path = Path(element.attrib["file"])
            if path.is_relative_to(original_episode):
                path = recording / path.relative_to(original_episode)
            if not path.is_file():
                raise FileNotFoundError(path)
            element.set("file", str(path))
    tree.write(scene_dir / "scene.xml", encoding="unicode")
    for name in ("coordinates.json", "style.yaml"):
        shutil.copyfile(reference / name, directory / name)
    subprocess.run([
        sys.executable, "-m", "render.export_blender_animation",
        "--rollout", str(recording / "rollout.parquet"),
        "--scene-dir", str(scene_dir), "--camera", "blender_reference",
        "--fps", str(info["fps"]), "--width", str(info["resolution"][0]),
        "--height", str(info["resolution"][1]), "--geom-groups", "0", "1", "2", "3",
        "--output", str(directory / "animation.pkl"),
    ], cwd=args.visualization, check=True)
    sources = [recording / name for name in ("rollout.parquet", "metadata.json", "scene/scene.xml")]
    sources += [reference / name for name in ("render_scene.xml", "coordinates.json", "style.yaml", "wood.png")]
    sources += [Path(__file__).resolve(), args.visualization / "render/create_blender_scene.py",
                args.visualization / "render/export_blender_animation.py"]
    request = {
        "task": task["task"], "episode": task["episode"], "frames": info["frame_count"],
        "fps": info["fps"], "resolution": info["resolution"],
        "duration_s": info["frame_count"] / info["fps"], "camera": info["camera"],
        "source_episode": str(recording),
        "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
    }
    (directory / "render_request.json").write_text(json.dumps(request, indent=2) + "\n")
    command = [
        args.blender, "--background", "--threads", "4", "--python-exit-code", "1", "--python", str(Path(__file__).resolve()),
        "--", "--blender-worker", "--task", task["task"], "--work-dir", str(args.work_dir.resolve()),
        "--visualization", str(args.visualization.resolve()), "--samples", str(args.samples),
    ]
    if args.preview:
        command.append("--preview")
    with (directory / "blender.log").open("w") as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    if not args.preview:
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-framerate", str(info["fps"]),
            "-i", str(directory / "frames/frame_%06d.png"), "-an", "-c:v", "libx264",
            "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-threads", "2",
            "-movflags", "+faststart", str(directory / "clean.mp4"),
        ], check=True)
    print(f"Blender {'previews' if args.preview else 'video'}: {directory}", flush=True)


def main():
    manifest = json.loads((ROOT / "data/visualization-media.json").read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=[task["task"] for task in manifest["tasks"]])
    parser.add_argument("--recording", type=Path, help="Override the recording for a single --task.")
    parser.add_argument("--source", type=Path, default=ROOT.parent / "Codegen_Robotwin_Mujoco/data/visualization")
    parser.add_argument("--visualization", type=Path, default=ROOT.parent / "Codegen_Blender_Visualization")
    parser.add_argument("--work-dir", type=Path, default=ARCHIVE / "robotwin_blender_20261028")
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--jobs", type=int, default=2, help="Number of independent task render processes.")
    parser.add_argument("--blender", default="blender")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--blender-worker", action="store_true")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
    args = parser.parse_args(argv)
    if args.recording and args.task is None:
        parser.error("--recording requires one --task.")
    tasks = [task for task in manifest["tasks"] if args.task is None or task["task"] == args.task]
    if args.blender_worker:
        task = tasks[0]
        directory = args.work_dir.resolve() / task["task"] / task["episode"]
        render_blender(directory, args.visualization.resolve(), args.samples, args.preview)
        return
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = [executor.submit(render_task, args, task) for task in tasks]
        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
