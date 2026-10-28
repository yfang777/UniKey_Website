#!/usr/bin/env python3
"""Render a local wrist-camera preview using the archived simulation animations.

Run with the sibling visualization project's Python environment:
  python scripts/preview_domain_randomization.py

The published videos and index.html are read-only inputs. Assets go into
output/previews/domain-randomization/ and the page is preview-domain-randomization.html.
Render intermediates go into --work-dir. Blender matches Hang Mug's original renderer.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import pickle
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VISUALIZATION = ROOT.parent / "Codegen_Blender_Visualization"
ARCHIVE = ROOT.parent / "Codegen_Blender_Visualization_artifacts"
OUTPUT = ROOT / "output/previews/domain-randomization"
HANG_SOURCE = ARCHIVE / "20261008T164407Z/data/visualization/hang_mug/sample_12/planner_d/camera_perspective_1"
OTHER_SOURCE = ARCHIVE / "domain_randomization_other_tasks_5s_4x3"
TASKS = {
    "hang-mug": HANG_SOURCE / "domain_randomization_camera_4x3",
    "arrange-table": OTHER_SOURCE / "table_arrange/rendered",
    "flip-and-arrange-shoe": OTHER_SOURCE / "flip_then_arrange_shoe/rendered",
    "pack-battery": OTHER_SOURCE / "pack_battery/rendered",
}
CAMERA = "D405_130322271320"
INSET_WIDTH, INSET_HEIGHT = 432, 243  # 1.5× larger; preserve the D405's native 16:9 view.
RENDER_WIDTH, RENDER_HEIGHT = 576, 324  # Reuse the supersampled wrist-camera renders.
MARGIN, BORDER = 12, 2
INSET_LABEL, LABEL_FONT_SIZE = "wrist camera", 20


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=width,height,r_frame_rate,nb_frames,duration", "-of", "json", str(path),
    ], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)["streams"][0]


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(task, directory):
    """Recover the moving calibrated camera from the exported link7 geometry."""
    import mujoco
    import numpy as np

    source = TASKS[task]
    manifest = json.loads((source / "domains.json").read_text())
    animation = HANG_SOURCE / "animation.pkl" if task == "hang-mug" else source.parent / "animation.pkl"
    with animation.open("rb") as stream:
        payload = pickle.load(stream)
    scene_path = Path(payload["source"]["scene_xml"])
    if not scene_path.is_absolute():
        scene_path = VISUALIZATION / scene_path
    payload["source"]["scene_xml"] = str(scene_path)
    model = mujoco.MjModel.from_xml_path(payload["source"]["scene_xml"])
    camera_id = model.camera(CAMERA).id
    reference = next((i, v) for i, v in enumerate(payload["visuals"]) if v["name"] == "end_tool")
    reference_index, visual = reference
    geom_id = model.geom(visual["name"]).id
    if model.geom_bodyid[geom_id] != model.cam_bodyid[camera_id]:
        raise ValueError("Reference geometry and wrist camera must share the same body")

    def rotation(quaternion):
        matrix = np.empty(9)
        mujoco.mju_quat2Mat(matrix, np.asarray(quaternion, dtype=float))
        return matrix.reshape(3, 3)

    geom_rotation = rotation(model.geom_quat[geom_id])
    camera_rotation = rotation(model.cam_quat[camera_id])
    matrices, positions, quaternions = [], [], []
    for frame_positions, frame_quaternions in zip(payload["positions"], payload["quaternions"], strict=True):
        body_rotation = rotation(frame_quaternions[reference_index]) @ geom_rotation.T
        matrix = np.eye(4)
        matrix[:3, :3] = body_rotation @ camera_rotation
        matrix[:3, 3] = (np.asarray(frame_positions[reference_index]) +
                          body_rotation @ (model.cam_pos[camera_id] - model.geom_pos[geom_id]))
        quaternion = np.empty(4)
        mujoco.mju_mat2Quat(quaternion, matrix[:3, :3].ravel())
        matrices.append(matrix.tolist())
        positions.append(matrix[:3, 3].tolist())
        quaternions.append(quaternion.tolist())

    # Export exact intrinsics for Blender; MuJoCo uses the original camera directly.
    resolution = model.cam_resolution[camera_id].astype(int)
    sensor = model.cam_sensorsize[camera_id]
    intrinsic = model.cam_intrinsic[camera_id]
    payload["camera"] = {
        "name": CAMERA, "resolution": resolution.tolist(),
        "focalpixel": (intrinsic[:2] / sensor * resolution).tolist(),
        "principalpixel": (intrinsic[2:] / sensor * resolution).tolist(),
        "positions": positions, "quaternions": quaternions,
        "world_pos": positions[0], "world_xmat": np.asarray(matrices[0])[:3, :3].ravel().tolist(),
    }
    payload["resolution"] = [RENDER_WIDTH, RENDER_HEIGHT]
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "frames").mkdir(exist_ok=True)
    with (directory / "animation.pkl").open("wb") as stream:
        pickle.dump(payload, stream)
    metadata = {
        "task": task, "source": str(source), "source_animation": str(animation),
        "animation_sha256": sha256(animation), "scene": payload["source"]["scene_xml"],
        "scene_sha256": sha256(Path(payload["source"]["scene_xml"])),
        "camera": CAMERA, "camera_reference_geom": visual["name"],
        "camera_matrices": matrices, "camera_intrinsics": {k: payload["camera"][k] for k in ("resolution", "focalpixel", "principalpixel")},
        "frame_count": len(matrices), "fps": manifest["fps"],
        "domains_sha256": sha256(source / "domains.json"),
    }
    if metadata["frame_count"] != manifest["frame_count"]:
        raise ValueError("Animation and randomization timeline lengths differ")
    write_json(directory / "metadata.json", metadata)
    return manifest, payload, model, metadata


def render_mujoco(directory, manifest, payload, model, metadata, frames):
    import mujoco
    import numpy as np
    from PIL import Image

    sys.path.insert(0, str(VISUALIZATION))
    from render.export_selected_mujoco_domain_randomization import NativeRenderer

    source = Path(metadata["source"])
    lighting = json.loads((source / "renderer.json").read_text())["frames"]
    lighting = {entry["frame"]: entry["lighting"] for entry in lighting}
    model.vis.global_.offwidth, model.vis.global_.offheight = RENDER_WIDTH, RENDER_HEIGHT
    model.vis.quality.offsamples = 8
    model.vis.quality.shadowsize = 4096
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    renderer = NativeRenderer(model)
    renderer.option.sitegroup[:] = 0
    # Match the exported visible geometry, including the archived object poses.
    visible = {v["id"] for v in payload["visuals"]}
    camera_id = model.camera(CAMERA).id
    active_domain = None
    samples = 4  # Preview soft shadows; the full-sized source used 16 samples.
    angles = np.arange(samples) * math.pi * (3 - math.sqrt(5))
    radii = 0.08 * np.sqrt((np.arange(samples) + 0.5) / samples)
    offsets = np.column_stack((radii * np.cos(angles), radii * np.sin(angles)))
    try:
        for frame in frames:
            domain = next(d for d in manifest["domains"] if d["start_frame"] <= frame <= d["end_frame"])
            if domain["index"] != active_domain:
                for group, appearance in domain["appearance"].items():
                    geom = model.geom(manifest["background_visuals"][group]["name"]).id
                    material = model.geom_matid[geom]
                    if "texture" in appearance:
                        texture = model.mat_texid[material, mujoco.mjtTextureRole.mjTEXROLE_RGB]
                        width, height = int(model.tex_width[texture]), int(model.tex_height[texture])
                        with Image.open(source / appearance["texture"]) as image:
                            pixels = np.asarray(image.convert("RGB").resize((width, height), Image.Resampling.LANCZOS))
                        address = model.tex_adr[texture]
                        model.tex_data[address:address + pixels.size] = pixels.ravel()
                        mujoco.mjr_uploadTexture(model, renderer.context, texture)
                    else:
                        model.mat_rgba[material] = appearance["rgba"]
                        model.geom_rgba[geom] = appearance["rgba"]
                active_domain = domain["index"]

            for i, visual in enumerate(payload["visuals"]):
                geom_id = visual["id"]
                data.geom_xpos[geom_id] = payload["positions"][frame - 1][i]
                mujoco.mju_quat2Mat(data.geom_xmat[geom_id], np.asarray(payload["quaternions"][frame - 1][i]))
            matrix = np.asarray(metadata["camera_matrices"][frame - 1])
            data.cam_xpos[camera_id], data.cam_xmat[camera_id] = matrix[:3, 3], matrix[:3, :3].ravel()
            renderer.update(data, CAMERA, [RENDER_WIDTH, RENDER_HEIGHT])
            for geom in renderer.scene.geoms[:renderer.scene.ngeom]:
                if geom.objtype != mujoco.mjtObj.mjOBJ_GEOM or geom.objid not in visible:
                    geom.rgba[3] = 0
            values = lighting[frame]
            total = np.zeros((RENDER_HEIGHT, RENDER_WIDTH, 3), dtype=float)
            for offset in offsets:
                renderer.scene.nlight = len(values["lights"]) + 1
                for slot, state in enumerate(values["lights"]):
                    light = renderer.scene.lights[slot]
                    direction = np.asarray(values["target"]) - state["position"]
                    direction /= np.linalg.norm(direction)
                    tangent = np.cross(direction, [0, 1, 0])
                    tangent /= np.linalg.norm(tangent)
                    light.pos[:] = state["position"] + offset[0] * tangent + offset[1] * np.cross(direction, tangent)
                    direction = np.asarray(values["target"]) - light.pos
                    light.dir[:] = direction / np.linalg.norm(direction)
                    light.type = mujoco.mjtLightType.mjLIGHT_SPOT
                    light.headlight, light.castshadow = False, True
                    light.ambient[:], light.diffuse[:], light.specular[:] = 0, state["power"], state["specular"]
                    light.attenuation[:] = [1, 0, 0]
                    light.cutoff, light.exponent, light.texid = 90, 0, -1
                    light.intensity, light.range = 0, 10
                ambient = renderer.scene.lights[len(values["lights"])]
                ambient.type = mujoco.mjtLightType.mjLIGHT_DIRECTIONAL
                ambient.pos[:], ambient.dir[:] = [0, 0, 3], [0, 0, -1]
                ambient.headlight, ambient.castshadow = False, False
                ambient.ambient[:] = sum(light["ambient"] for light in values["lights"])
                ambient.diffuse[:], ambient.specular[:] = 0, 0
                ambient.texid, ambient.intensity = -1, 0
                total += renderer.render()
            averaged = np.rint(total / samples).astype(np.uint8)
            pixels = np.rint((averaged.astype(float) / 255) ** (1 / manifest["render"]["display_gamma"]) * 255).astype(np.uint8)
            Image.fromarray(pixels).save(directory / "frames" / f"frame_{frame:06d}.png")
            if frame == frames[0] or frame % 50 == 0:
                print(f"{metadata['task']}: wrist frame {frame}/{metadata['frame_count']}", flush=True)
    finally:
        renderer.close()


def render_blender(directory):
    """Match Hang Mug's Cycles materials, lights, and animation at preview quality."""
    import bpy
    from mathutils import Vector

    request = json.loads((directory / "request.json").read_text())
    source = Path(request["source"])
    manifest = json.loads((source / "domains.json").read_text())
    lighting = {entry["frame"]: entry for entry in json.loads((source / "renderer.json").read_text())["lighting_frames"]}
    with (directory / "animation.pkl").open("rb") as stream:
        payload = pickle.load(stream)
    builder = module_at("wrist_scene_builder", VISUALIZATION / "render/create_blender_scene.py")
    args = builder.parse_args([
        "--animation-pkl", str(directory / "animation.pkl"), "--blend-out", str(directory / "unused.blend"),
        "--engine", "CYCLES", "--cycles-render-device", "gpu", "--samples", "24", "--camera-mode", "mujoco",
        "--width", str(RENDER_WIDTH), "--height", str(RENDER_HEIGHT),
    ])
    builder.clear_scene()
    builder.configure_scene(payload, args)
    builder.configure_freestyle(args)
    cache = {}
    objects = [builder.make_visual_object(v, payload, builder.material_for_visual(v, cache)) for v in payload["visuals"]]
    builder.keyframe_objects(payload, objects)
    builder.add_camera(payload)
    scene = bpy.context.scene
    scene.render.use_motion_blur = False
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.resolution_percentage = 100
    scene.cycles.use_denoising = True
    scene.cycles.seed = manifest["seed"]
    scene.cycles.use_animated_seed = False
    scene.render.use_persistent_data = True
    materials = {}
    for group, visual in manifest["background_visuals"].items():
        obj = bpy.data.objects[builder.sanitize_name(visual["name"])]
        obj.active_material = obj.active_material.copy()
        materials[group] = obj.active_material
    world = scene.world
    world.use_nodes = True
    world.node_tree.nodes.clear()
    background = world.node_tree.nodes.new("ShaderNodeBackground")
    background.inputs["Color"].default_value = (1, 1, 1, 1)
    world_output = world.node_tree.nodes.new("ShaderNodeOutputWorld")
    world.node_tree.links.new(background.outputs["Background"], world_output.inputs["Surface"])
    lights = []
    for index in range(manifest["config"]["lighting"]["count"][1]):
        light_data = bpy.data.lights.new(f"Domain_Light_{index}", "SPOT")
        light_data.spot_size, light_data.spot_blend, light_data.shadow_soft_size = math.pi, 0, 0.08
        light = bpy.data.objects.new(light_data.name, light_data)
        scene.collection.objects.link(light)
        lights.append(light)
    active_domain = None
    for frame in request["frames"]:
        domain = next(d for d in manifest["domains"] if d["start_frame"] <= frame <= d["end_frame"])
        if active_domain != domain["index"]:
            for group, appearance in domain["appearance"].items():
                material = materials[group]
                if "texture" in appearance:
                    texture = next(node for node in material.node_tree.nodes if node.type == "TEX_IMAGE")
                    texture.image = bpy.data.images.load(str(source / appearance["texture"]), check_existing=True)
                else:
                    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = appearance["rgba"]
            active_domain = domain["index"]
        scene.frame_set(frame)
        values = lighting[frame]
        background.inputs["Strength"].default_value = values["world_strength"]
        for light, state in zip(lights, values["lights"], strict=True):
            light.location = state["position"]
            light.rotation_euler = (Vector(domain["lighting"]["target"]) - light.location).to_track_quat("-Z", "Y").to_euler()
            light.data.energy = state["energy_w"]
        scene.render.filepath = str(directory / "frames" / f"frame_{frame:06d}.png")
        bpy.ops.render.render(write_still=True)


def compose(task, directory, metadata):
    original = ROOT / "assets/videos/pipeline/domain-randomization" / f"{task}.mp4"
    output = OUTPUT / f"{task}.mp4"
    base = probe(original)
    if int(base["nb_frames"]) != metadata["frame_count"] or base["r_frame_rate"] != f"{metadata['fps']}/1":
        raise ValueError(f"{task}: wrist and main timelines do not match")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(original),
        "-framerate", str(metadata["fps"]), "-start_number", "1", "-i", str(directory / "frames/frame_%06d.png"),
        "-filter_complex", (
            f"[1:v]format=rgba,scale={INSET_WIDTH}:{INSET_HEIGHT}:flags=lanczos,setsar=1,"
            f"drawtext=font=DejaVu Sans:text='{INSET_LABEL}':fontsize={LABEL_FONT_SIZE}:fontcolor=white:"
            "x=(w-text_w)/2:y=10:box=1:boxcolor=black@0.48:boxborderw=5,"
            f"pad=iw+{2 * BORDER}:ih+{2 * BORDER}:{BORDER}:{BORDER}:color=0xf3f1eb[wrist];"
            f"[0:v][wrist]overlay={MARGIN}:{MARGIN}:shortest=1:format=auto,format=yuv420p[v]"
        ),
        "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ], check=True)
    if probe(output) != base:
        raise ValueError(f"{task}: exported timing or dimensions changed")
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(output), "-frames:v", "1", "-q:v", "2", str(OUTPUT / f"{task}-poster.jpg")], check=True)
    return {"source_sha256": sha256(original), "preview_sha256": sha256(output), **base,
            "inset": {"width": INSET_WIDTH, "height": INSET_HEIGHT, "margin": MARGIN, "border": BORDER,
                      "label": INSET_LABEL, "label_position": "top-center", "label_font_size": LABEL_FONT_SIZE},
            "preview_render": {"engine": "Cycles" if task == "hang-mug" else "MuJoCo OpenGL",
                               "resolution": [RENDER_WIDTH, RENDER_HEIGHT],
                               "samples": 24 if task == "hang-mug" else 4},
            **{k: v for k, v in metadata.items() if k != "camera_matrices"}}


def build_page():
    page = (ROOT / "index.html").read_text()
    page = re.sub(r"<title>(.*?)</title>", r"<title>Wrist Camera Preview · \1</title>", page, count=1)
    for task in TASKS:
        poster = "poster.jpg" if task == "hang-mug" else f"{task}-poster.jpg"
        for source_name, target_name in [(f"{task}.mp4", f"{task}.mp4"), (poster, f"{task}-poster.jpg")]:
            target = OUTPUT / target_name
            if not target.exists():
                raise FileNotFoundError(f"Render all tasks before building the preview page: {target}")
            page = re.sub(r"\./assets/videos/pipeline/domain-randomization/" + re.escape(source_name) + r"(?:\?v=[a-f0-9]+)?",
                          f"./output/previews/domain-randomization/{target_name}?v={sha256(target)[:12]}", page)
    (ROOT / "preview-domain-randomization.html").write_text(page)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=TASKS, action="append")
    parser.add_argument("--work-dir", type=Path, default=Path("/tmp/unikey-domain-wrist-preview"))
    parser.add_argument("--frames", help="One-based comma-separated frames for a render check; skips video export")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--page-only", action="store_true", help="Refresh the preview page using already rendered assets")
    parser.add_argument("--blender-worker", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)
    if args.blender_worker:
        render_blender(args.blender_worker)
        return
    if args.page_only:
        build_page()
        return
    os.environ.setdefault("MUJOCO_GL", "egl")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    reports = json.loads((OUTPUT / "manifest.json").read_text()) if (OUTPUT / "manifest.json").exists() else {}
    for task in args.task or TASKS:
        directory = args.work_dir / task
        manifest, payload, model, metadata = prepare(task, directory)
        frames = [int(f) for f in args.frames.split(",")] if args.frames else list(range(1, metadata["frame_count"] + 1))
        if not all(1 <= frame <= metadata["frame_count"] for frame in frames):
            raise ValueError("Requested frame outside the animation")
        if not args.skip_render:
            if task == "hang-mug":
                write_json(directory / "request.json", {"source": metadata["source"], "frames": frames})
                with (directory / "blender.log").open("w") as log:
                    subprocess.run(["blender", "--background", "--python", str(Path(__file__).resolve()), "--", "--blender-worker", str(directory)], check=True, stdout=log, stderr=subprocess.STDOUT)
            else:
                render_mujoco(directory, manifest, payload, model, metadata, frames)
        if not args.frames:
            reports[task] = compose(task, directory, metadata)
            write_json(OUTPUT / "manifest.json", reports)
            print(f"Ready: {task}", flush=True)
    if not args.frames and all((OUTPUT / f"{task}.mp4").exists() for task in TASKS):
        build_page()
        print("Preview: http://127.0.0.1:8000/preview-domain-randomization.html#domain-randomization", flush=True)


if __name__ == "__main__":
    main()
