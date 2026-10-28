#!/usr/bin/env python3
"""Render Hang Mug's archived correction rounds at native 1440 × 1080 (4:3).

Retains all 320 frames, the saved moving camera, ghost poses, and overlays.
Requires the sibling visualization project and its archived Blender scenes.
Use --preview to render representative frames without replacing website assets.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT.parent / "Codegen_Blender_Visualization_artifacts"
DESTINATION = ROOT / "assets/videos/pipeline/failure-detection-correction/hang-mug"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def worker(args):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector

    config = module("round_camera_config", args.visualization_root / "render_camera/scene_config.py")
    builder = module("round_scene_builder", args.visualization_root / "render/create_blender_scene.py")
    source_path = ARCHIVE / "hang_mug_camera_transition/fast_camera_transition/metadata.json"
    source = json.loads(source_path.read_text())
    for path, expected in source["source_blend_sha256"].items():
        if digest(Path(path)) != expected:
            raise ValueError(f"Archived scene changed: {path}")
    rounds = json.loads(Path(source["source_metadata"]).read_text())["sources"]
    selected = {1, 100, 101, 184, 185, 248, 249, 320} if args.preview else set(range(1, 321))
    work = args.work_dir / "training-rounds"
    rendered = work / "rendered"
    rendered.mkdir(parents=True, exist_ok=True)
    frames = []
    current_segment = None
    width, height = 1440, 1080
    for record in source["frames"]:
        index = record["frame"]
        if index not in selected:
            continue
        segment = record["segment"]
        if segment != current_segment:
            folder = Path(rounds[segment]["path"]).parent
            request = json.loads((folder / "render_request.json").read_text())
            bpy.ops.wm.open_mainfile(filepath=str(folder / "scene.blend"))
            scene = bpy.context.scene
            scene.render.resolution_x, scene.render.resolution_y = width, height
            scene.render.resolution_percentage = 100
            scene.render.image_settings.file_format = "PNG"
            scene.render.image_settings.color_mode = "RGB"
            scene.render.image_settings.color_depth = "8"
            scene.render.use_motion_blur = False
            scene.render.use_persistent_data = True
            scene.camera.data.dof.use_dof = False
            scene.cycles.samples = args.samples
            scene.cycles.use_denoising = True
            scene.cycles.denoiser = "OPTIX"
            from types import SimpleNamespace
            builder.configure_cycles_device(SimpleNamespace(cycles_render_device="gpu"))
            current_segment = segment
        scene.frame_set(record["source_frame"])
        camera = record["camera"]
        config.apply_camera(scene.camera, camera)
        bpy.context.view_layer.update()
        points = request["points"][record["source_frame"] - 1]
        coords = [world_to_camera_view(scene, scene.camera, Vector(point)) for point in points]
        pixels = [[point.x * width - .5, (1 - point.y) * height - .5] for point in coords]
        inverse = scene.camera.matrix_world.inverted()
        focal = width * camera["lens_mm"] / camera["sensor_width_mm"]
        errors = []
        for point, coord, pixel in zip(points, coords, pixels):
            if coord.z > 0:
                local = inverse @ Vector(point)
                expected = [focal * local.x / -local.z + (width - 1) / 2,
                            focal * local.y / local.z + (height - 1) / 2]
                errors.append(max(abs(a - b) for a, b in zip(expected, pixel)))
        error = max(errors, default=0)
        if error > .001:
            raise ValueError(f"Keypoint projection differs by {error} pixels at frame {index}")
        output = rendered / f"frame_{index:06d}.png"
        if not output.exists():
            config.refresh_camera_ghosts(scene, work / "camera_ghosts.exr")
            scene.render.filepath = str(output)
            bpy.ops.render.render(write_still=True)
        frames.append({**record, "keypoint_pixels": pixels,
                       "keypoint_visible": [point.z > 0 and 0 <= pixel[0] < width and 0 <= pixel[1] < height
                                            for point, pixel in zip(coords, pixels)],
                       "projection_error_pixels": error})
        print(f"4:3 correction frame {index}/320", flush=True)
    for path, expected in source["source_blend_sha256"].items():
        if digest(Path(path)) != expected:
            raise ValueError(f"Archived scene changed during rendering: {path}")
    report = {**source, "resolution": [width, height], "samples": args.samples,
              "source_render_metadata": str(source_path), "source_render_metadata_sha256": digest(source_path),
              "output": str(args.work_dir / "training-rounds.mp4"), "frames": frames,
              "complete": not args.preview, "preview_frames": sorted(selected & {1, 100, 101, 184, 185, 248, 249, 320}),
              "max_keypoint_projection_error_pixels": max(frame["projection_error_pixels"] for frame in frames),
              "blender_version": bpy.app.version_string,
              "framing": "Saved camera and original 4:3 field of view retained. No crop or upscale."}
    (work / "metadata.json").write_text(json.dumps(report, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visualization-root", type=Path, default=ROOT.parent / "Codegen_Blender_Visualization")
    parser.add_argument("--work-dir", type=Path, default=ARCHIVE / "hang_mug_rounds_4x3_20261028")
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)
    args.work_dir = args.work_dir.resolve()
    args.visualization_root = args.visualization_root.resolve()
    if args.samples <= 0:
        parser.error("--samples must be positive")
    if args.worker:
        worker(args)
        return
    args.work_dir.mkdir(parents=True, exist_ok=True)
    command = ["blender", "--background", "--threads", "4", "--python-exit-code", "1", "--python", str(Path(__file__).resolve()),
               "--", "--worker", "--visualization-root", str(args.visualization_root), "--work-dir", str(args.work_dir),
               "--samples", str(args.samples)]
    if args.preview:
        command.append("--preview")
    with (args.work_dir / "render.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    metadata = args.work_dir / "training-rounds/metadata.json"
    subprocess.run([sys.executable, str(args.visualization_root / "render_camera/render_camera_transition.py"),
                    "--finish", str(metadata)], check=True)
    if args.preview:
        print(f"Preview: {args.work_dir / 'training-rounds/preview.png'}")
        return
    DESTINATION.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.work_dir / "training-rounds.mp4", DESTINATION / "training-rounds.mp4")
    from PIL import Image
    Image.open(args.work_dir / "training-rounds/frames/frame_000001.png").save(
        DESTINATION / "training-rounds-poster.jpg", quality=94)
    report = json.loads(metadata.read_text())
    report.pop("frames")
    report["output"] = str((DESTINATION / "training-rounds.mp4").relative_to(ROOT))
    report["output_sha256"] = digest(DESTINATION / "training-rounds.mp4")
    (DESTINATION / "training-rounds-render-info.json").write_text(json.dumps(report, indent=2) + "\n")
    html = (ROOT / "index.html").read_text()
    for name in ("training-rounds.mp4", "training-rounds-poster.jpg"):
        relative = "./" + str((DESTINATION / name).relative_to(ROOT))
        html = re.sub(re.escape(relative) + r"(?:\?v=[^\"<>\s]+)?", relative + "?v=" + digest(DESTINATION / name)[:12], html)
    (ROOT / "index.html").write_text(html)
    print("Published 1440 × 1080 Hang Mug correction video (320 frames at 30 fps).")


if __name__ == "__main__":
    main()
