"""Render and package three recorded Agentic Keypoint Programs demonstrations.

Run with the Datagen Python environment. Replays saved states without stepping
physics, with a two-second camera orbit and a six-second code-generation hold.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco
import numpy as np
import pandas as pd
from PIL import Image
import yaml

ROOT = Path(__file__).resolve().parents[1]
FPS, WIDTH, HEIGHT = 30, 960, 720
ORBIT_SECONDS, GENERATION_SECONDS = 2, 6
EXECUTION_START = ORBIT_SECONDS + GENERATION_SECONDS
COLORS = {"robot": [.23, .46, .69, 1], "object": [.32, .62, .25, 1], "target": [.73, .54, 0, 1]}
TASKS = {
    "hang_mug": {
        "title": "Hang the mug",
        "instruction": "Grasp the mug and hang its handle onto the rack.",
        "constraints_sha256": "3899636b1cd832f910cf650b7bdc9e634f98b212837ac5301be51bcef56532fa",
        "phases": [("Approach the mug", [1, 2], ["mug_grasp", "handle_top", "handle_bottom"]),
                   ("Grasp the mug", [], ["mug_grasp"]),
                   ("Lift and align", [4], ["handle_top", "handle_bottom", "rack_tip"]),
                   ("Hang and release", [5], ["handle_top", "handle_bottom", "rack_tip"])],
    },
    "flip_then_arrange_shoe": {
        "title": "Flip and arrange the shoe",
        "instruction": "Flip the right shoe upright, grasp it, and place it in the tray beside the left shoe.",
        "constraints_sha256": "46a1eba7ac9a592375d85a1e6e215f50b2f29189cd9f149fd32883108ae97e90",
        "phases": [("Flip the shoe", [1, 3], ["shoe_opening"]),
                   ("Approach and grasp", [5, 6], ["shoe_grasp"]),
                   ("Place in the tray", [9, 10], ["shoe_sole", "tray_slot"])],
    },
    "table_arrange": {
        "title": "Arrange the table",
        "instruction": "Arrange the spoon, fork, and bowl sequentially at their target positions.",
        "constraints_sha256": "03c5f1ddbfe7ba49d34b31ef0c6b1aa74a1bf2cc7e8e2931caaf4bd367cfbc26",
        "phases": [("Grasp the spoon", [1], ["spoon_grasp"]),
                   ("Place the spoon", [4], ["spoon_placement", "spoon_target"]),
                   ("Grasp the fork", [9], ["fork_grasp"]),
                   ("Place the fork", [12], ["fork_placement", "fork_target"]),
                   ("Grasp the bowl", [16], ["bowl_grasp"]),
                   ("Place the bowl", [19], ["bowl_bottom", "bowl_target"])],
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scene_xml(path: Path, datagen: Path) -> tuple[str, dict]:
    """Resolve archived workstation paths to matching local assets."""
    inputs = {}

    def resolve(reference: str, parent: Path) -> Path:
        source = Path(reference)
        if not source.is_absolute():
            source = parent / source
        if not source.exists():
            if (parent / source.name).exists():
                source = parent / source.name
            elif "/Codegen_Datagen/" in str(source):
                source = datagen / str(source).split("/Codegen_Datagen/", 1)[1]
        if not source.is_file():
            raise FileNotFoundError(source)
        return source.resolve()

    def inline(source: Path) -> ET.Element:
        inputs[str(source)] = digest(source)
        root = ET.parse(source).getroot()
        for element in list(root):
            if element.tag == "include":
                children = list(inline(resolve(element.attrib["file"], source.parent)))
                index = list(root).index(element)
                root.remove(element)
                for offset, child in enumerate(children):
                    root.insert(index + offset, child)
        for element in root.iter():
            if "file" in element.attrib:
                asset = resolve(element.attrib["file"], source.parent)
                inputs[str(asset)] = digest(asset)
                element.set("file", str(asset))
        return root

    return ET.tostring(inline(path), encoding="unicode"), inputs


def load_recording(task: str, datagen: Path, visualization: Path) -> tuple:
    constraints = datagen / "assets/solution" / task / "constraints.py"
    if digest(constraints) != TASKS[task]["constraints_sha256"]:
        raise ValueError(f"{task}: program changed; select a matching recording before packaging.")
    if task == "hang_mug":
        source = visualization / "data/visualization/hang_mug/sample_12_modified/planner_from_scratch"
        recording_path = source / "sample_12.parquet"
        recording = pd.read_parquet(recording_path)
        scene = Path(recording.iloc[0]["meta.xml_path"])
        validation = json.loads((source / "validation.json").read_text())
        if not validation["geometric_judge_passed"] or not validation["final_rack_support"]:
            raise ValueError("Mug recording failed its judge.")
        stages = json.loads((source / "stages.json").read_text())["stages"]
        starts = [0, stages[2]["start"] / 50, stages[3]["start"] / 50, stages[4]["start"] / 50]
        points = {
            "left_gripper": {"index": -2, "site": "left_finger_site", "kind": "robot"},
            "right_gripper": {"index": -1, "site": "right_finger_site", "kind": "robot"},
            "handle_top": {"index": 1, "site": "039_mug_1_kp_0", "kind": "object"},
            "handle_bottom": {"index": 3, "site": "039_mug_1_kp_2", "kind": "object"},
            "mug_grasp": {"index": 8, "site": "039_mug_1_kp_7", "kind": "object"},
            "rack_tip": {"index": 9, "site": "040_rack_1_kp_0", "kind": "target"},
        }
        metadata = [source / "stages.json", source / "validation.json", source / "provenance.json"]
    else:
        source = visualization / "data/visualization" / task / "sample_0"
        recording_path = source / "keypoint_overlays/recording.parquet"
        recording = pd.read_parquet(recording_path)
        report = json.loads((source / "inputs.json").read_text())
        validation_path = Path(report["source_directory"]) / "validation.json"
        validation = json.loads(validation_path.read_text())
        if not validation["success"] or validation["frames"] != len(recording):
            raise ValueError(f"{task}: recording failed validation.")
        scene = Path(report["scene_xml"])
        config_path = source / "keypoint_overlays/config.yaml"
        overlay = yaml.safe_load(config_path.read_text())["tasks"][task]
        points = {name: {**point, "kind": "robot" if "gripper" in name else
                         "target" if "target" in name or name == "tray_slot" else "object"}
                  for name, point in overlay["keypoints"].items()}
        starts = [phase["start_source_frame"] / 50 for phase in overlay["phases"]]
        metadata = [source / "inputs.json", config_path, validation_path]
    xml, scene_inputs = scene_xml(scene, datagen)
    model = mujoco.MjModel.from_xml_string(xml)
    if len(recording.iloc[0]["state_buf"]) != mujoco.mj_stateSize(model, 63):
        raise ValueError(f"{task}: recording and scene state layouts differ.")
    data = mujoco.MjData(model)
    max_error = 0.0
    for state, recorded in zip(recording["state_buf"], recording["observation.keypoints"]):
        mujoco.mj_setState(model, data, np.array(state, dtype=np.float64, copy=True), 63)
        mujoco.mj_forward(model, data)
        keypoints = np.asarray(recorded).reshape(-1, 3)
        for point in points.values():
            if "site" in point:
                error = np.linalg.norm(data.site(point["site"]).xpos - keypoints[point["index"]])
                max_error = max(max_error, float(error))
    if max_error > 0.001:
        raise ValueError(f"{task}: reconstructed keypoints differ by {max_error} m.")
    inputs = {**scene_inputs, str(recording_path.resolve()): digest(recording_path),
              str(constraints): digest(constraints), **{str(p): digest(p) for p in metadata}}
    return model, recording, points, starts, constraints, inputs, max_error


def program_blocks(constraints: Path, task: str, starts: list) -> tuple[list, str]:
    code = constraints.read_text()
    tree = ast.parse(code)
    assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and (t.id.isupper() or t.id in {"grasp_stage", "grasp_keypoints"}) for t in n.targets)]
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    blocks = [{"label": "Keypoint interface", "code": "\n".join(ast.unparse(n) for n in assignments), "start_s": None}]
    for (label, stages, _), start in zip(TASKS[task]["phases"], starts):
        selected = [functions[f"stage{stage}_constraint1"] for stage in stages]
        snippet = "\n\n".join(ast.get_source_segment(code, n) for n in selected)
        if not selected:
            snippet = "\n".join(ast.unparse(n) for n in assignments if any(
                isinstance(t, ast.Name) and t.id in {"grasp_stage", "grasp_keypoints"} for t in n.targets))
        blocks.append({"label": label, "code": snippet, "start_s": start})
    helpers = "\n\n".join(ast.get_source_segment(code, n) for n in tree.body if
        isinstance(n, (ast.Import, ast.ImportFrom)) or isinstance(n, ast.FunctionDef) and not re.match(r"stage\d+_constraint", n.name))
    return blocks, helpers


def render_task(task: str, model, recording, points: dict, starts: list, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    data, camera = mujoco.MjData(model), mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = [.23, -.08, .18]
    camera.distance, camera.azimuth, camera.elevation = 1.1, 180, -30
    options = mujoco.MjvOption()
    options.geomgroup[:] = [1, 1, 1, 0, 0, 0]
    options.sitegroup[:] = 0
    renderer = mujoco.Renderer(model, width=WIDTH, height=HEIGHT)
    execution_frames = int(np.ceil(len(recording) / 50 * FPS))
    encoder = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "fast",
        "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output / "demo.mp4")], stdin=subprocess.PIPE)
    orbit_coordinates = []

    def frame(source_row: int, names: list) -> np.ndarray:
        mujoco.mj_setState(model, data, np.array(recording.iloc[source_row]["state_buf"], dtype=np.float64, copy=True), 63)
        mujoco.mj_forward(model, data)
        renderer.update_scene(data, camera=camera, scene_option=options)
        for name in names:
            point = points[name]
            position = np.asarray(point["world_xyz"]) if "world_xyz" in point else data.site(point["site"]).xpos
            geom = renderer.scene.geoms[renderer.scene.ngeom]
            mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_SPHERE, [.007, .007, .007],
                               position, np.eye(3).flatten(), COLORS[point["kind"]])
            geom.emission = 0.4
            renderer.scene.ngeom += 1
        return renderer.render()

    try:
        for i in range(ORBIT_SECONDS * FPS):
            progress = i / (ORBIT_SECONDS * FPS - 1)
            camera.azimuth = 180 + 26 * np.sin(2 * np.pi * progress)
            camera.elevation = -30 - 5 * np.sin(np.pi * progress) ** 2
            image = frame(0, list(points))
            if i == 0:
                Image.fromarray(image).save(output / "poster.jpg", quality=92)
            if i in [0, 15, 30, 45, 59]:
                Image.fromarray(image).save(output / f"orbit-{i:02d}.jpg", quality=90)
            orbit_coordinates.append({"frame": i, "azimuth": camera.azimuth, "elevation": camera.elevation, "source_row": 0})
            encoder.stdin.write(image.tobytes())
        camera.azimuth, camera.elevation = 180, -30
        held_frame = frame(0, list(points))
        for _ in range(GENERATION_SECONDS * FPS):
            encoder.stdin.write(held_frame.tobytes())
        for i in range(execution_frames):
            time_s = i / FPS
            source_row = min(round(time_s * 50), len(recording) - 1)
            phase = max(index for index, start in enumerate(starts) if start <= time_s)
            names = ["left_gripper", "right_gripper", *TASKS[task]["phases"][phase][2]]
            image = frame(source_row, names)
            if i == execution_frames - 1:
                Image.fromarray(image).save(output / "final.jpg", quality=92)
            encoder.stdin.write(image.tobytes())
    finally:
        encoder.stdin.close()
        renderer.close()
    if encoder.wait() != 0:
        raise RuntimeError(f"FFmpeg failed for {task}.")
    return {"fps": FPS, "frames": EXECUTION_START * FPS + execution_frames,
            "duration_s": EXECUTION_START + execution_frames / FPS,
            "execution_duration_s": execution_frames / FPS, "orbit_cameras": orbit_coordinates,
            "camera": {"lookat": camera.lookat.tolist(), "distance": camera.distance, "azimuth": 180, "elevation": -30}}


def default_markup(tasks: list, version: str) -> str:
    first = tasks[0]
    options = "\n".join(f'              <option value="{t["id"]}">{escape(t["title"])}</option>' for t in tasks)
    fallback = "\n\n".join(block["code"] for block in first["blocks"])
    return f'''        <!-- method-demo:start -->
        <article class="method-subsection program-demo" id="program-demo" aria-labelledby="program-demo-title" data-manifest="./data/method-demo.json?v={version}">
          <div class="program-demo-heading">
            <h3 id="program-demo-title">Agentic Keypoint Programs</h3>
            <p>From a task and 3D scene to a keypoint program and planned motion.</p>
          </div>
          <div class="program-task-bar">
            <label for="program-task">Task</label>
            <select id="program-task" disabled>
{options}
            </select>
          </div>
          <p class="program-instruction" id="program-instruction">{escape(first["instruction"])}</p>
          <ol class="program-steps" aria-label="Demonstration sequence">
            <li data-phase="orbit">1 <span>3D keypoints</span></li>
            <li data-phase="generation">2 <span>Program generation</span></li>
            <li data-phase="execution">3 <span>Planned motion</span></li>
          </ol>
          <div class="program-demo-grid">
            <figure class="program-visualization">
              <figcaption><span>Scene &amp; keypoints</span><span>Recorded simulation</span></figcaption>
              <video id="program-video" controls muted playsinline preload="none" poster="{first["poster"]}" width="960" height="720" aria-label="{escape(first["title"])}: 3D keypoints, program generation, and execution">
                <source src="{first["video"]}" type="video/mp4" />
                Your browser does not support embedded video. <a href="{first["video"]}">Open the demonstration.</a>
              </video>
              <p class="program-phase" id="program-phase" role="status" aria-live="polite">Ready to explore the 3D keypoints</p>
              <div class="program-legend" aria-label="Keypoint colors">
                <span><i class="keypoint-robot" aria-hidden="true"></i>Robot</span>
                <span><i class="keypoint-object" aria-hidden="true"></i>Object</span>
                <span><i class="keypoint-target" aria-hidden="true"></i>Target</span>
              </div>
            </figure>
            <div class="program-panel">
              <div class="program-code-heading"><span>Keypoint program</span><a id="program-source" href="{first["program"]}" target="_blank" rel="noopener">Full source ↗</a></div>
              <div class="program-code-window" tabindex="0" aria-label="Keypoint program excerpt">
                <p class="program-code-empty" id="program-code-empty" hidden>Press Play to explore the scene and generate its program.</p>
                <div id="program-code"><pre class="program-code"><code>{escape(fallback)}</code></pre></div>
              </div>
              <div class="program-stage-control" hidden><label for="program-stage">Execution phase</label><select id="program-stage" disabled></select></div>
            </div>
          </div>
          <div class="program-controls" hidden>
            <button type="button" id="program-play" aria-controls="program-video">Play</button>
            <button type="button" id="program-replay" aria-controls="program-video">Replay</button>
            <label class="sr-only" for="program-seek">Demonstration position</label>
            <input id="program-seek" type="range" min="0" max="{first["duration_s"]}" step="0.033333" value="0" />
            <output id="program-time" for="program-seek">0.00 / {first["duration_s"]:.2f} s</output>
          </div>
          <p class="program-notice" id="program-notice" role="status" hidden></p>
          <p class="program-footnote">Prepared demonstration. The code reveal shows excerpts from the task's actual keypoint program.</p>
          <details class="program-context"><summary>Keypoints and helper functions</summary><pre class="program-code" tabindex="0"><code id="program-context">{escape(first["context"])}</code></pre></details>
        </article>
        <!-- method-demo:end -->'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datagen", type=Path, default=ROOT.parent / "Codegen_Datagen")
    parser.add_argument("--visualization", type=Path, default=ROOT.parent / "Codegen_Blender_Visualization")
    parser.add_argument("--reuse-media", action="store_true", help="Repackage verified media without rendering again.")
    args = parser.parse_args()
    tasks = []
    for task, settings in TASKS.items():
        model, recording, points, starts, constraints, inputs, error = load_recording(task, args.datagen.resolve(), args.visualization.resolve())
        output = ROOT / "media/method" / task
        report_path = output / "render-info.json"
        if args.reuse_media:
            report = json.loads(report_path.read_text())
            if report["source_sha256"] != inputs:
                raise ValueError(f"{task}: source inputs changed; render again.")
            for name, checksum in report["media_sha256"].items():
                if digest(output / name) != checksum:
                    raise ValueError(f"{task}: media changed: {name}.")
        else:
            print(f"Rendering {task}: {len(recording)} recorded states", flush=True)
            report = render_task(task, model, recording, points, starts, output)
            report.update({"source_sha256": inputs, "max_keypoint_error_m": error, "source_fps": 50,
                           "source_frames": len(recording), "keypoints": points,
                           "media_sha256": {name: digest(output / name) for name in ["demo.mp4", "poster.jpg"]}})
            report_path.write_text(json.dumps(report, indent=2) + "\n")
        destination = ROOT / "media/programs" / task / "constraints.py"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(constraints.read_bytes())
        blocks, context = program_blocks(constraints, task, starts)
        tasks.append({"id": task, "title": settings["title"], "instruction": settings["instruction"],
                      "video": f"media/method/{task}/demo.mp4?v={digest(output / 'demo.mp4')[:12]}",
                      "poster": f"media/method/{task}/poster.jpg?v={digest(output / 'poster.jpg')[:12]}",
                      "program": f"media/programs/{task}/constraints.py?v={digest(destination)[:12]}",
                      "fps": FPS, "resolution": [WIDTH, HEIGHT], "duration_s": report["duration_s"],
                      "orbit_end_s": ORBIT_SECONDS, "execution_start_s": EXECUTION_START,
                      "blocks": blocks, "context": context})
        print(f"Packaged {task}: {report['duration_s']:.2f} s; keypoint error {error:.2g} m", flush=True)
    manifest = ROOT / "data/method-demo.json"
    manifest.write_text(json.dumps({"tasks": tasks}, indent=2) + "\n")
    index = ROOT / "index.html"
    html = re.sub(r"        <!-- method-demo:start -->.*?        <!-- method-demo:end -->",
                  lambda _: default_markup(tasks, digest(manifest)[:12]), index.read_text(), flags=re.S)
    for asset in ["site.css", "site.js", "method-demo.js"]:
        html = re.sub(rf"assets/{re.escape(asset)}(?:\?v=[a-f0-9]+)?", f"assets/{asset}?v={digest(ROOT / 'assets' / asset)[:12]}", html)
    index.write_text(html)


if __name__ == "__main__":
    main()
