#!/usr/bin/env python3
"""Read the requested robo02 results into data_stat without changing the server.

Hang Mug uses the main_figure/ACT_hang_mug CSVs. The remaining tasks use
ACT seed 1, rgb_abs_action, Dense Sampling and v20's 0p02_time_3 experiment.
Original source files are copied byte-for-byte with SHA-256 provenance.
"""
from __future__ import annotations

import argparse
import ast
import base64
from collections import Counter
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys


TASKS = {"hang_mug": "Hang Mug", "table_arrange": "Arrange Table",
         "flip_then_arrange_shoe": "Flip and Arrange Shoe", "pack_battery": "Pack Battery"}
REMOTE_ROOT = Path("/local/robopil/yuan")


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def collect_remote():
    files = {}

    def capture(path):
        content = path.read_bytes()
        local = "raw/" + str(path.relative_to(REMOTE_ROOT))
        files[local] = {"path": str(path), "local_path": local, "sha256": sha256(content),
                        "bytes": len(content), "base64": base64.b64encode(content).decode("ascii")}
        return content, local

    hang = REMOTE_ROOT / "scripts/main_figure/ACT_hang_mug"
    for name in ("success_rate_sim.csv", "success_rate_real.csv", "plot_success_rate.py", "query_success_rate_sim.py"):
        capture(hang / name)

    records, availability = {}, {}
    for task in TASKS:
        if task == "hang_mug":
            continue
        root = REMOTE_ROOT / "tasks" / task
        patterns = {
            "dense_sampling": "dense_sample/rgb_abs_action/dataset_step_*/ACT_rollout_seed_1/dataset_step_*_test_rollout/info.json",
            "unikey": f"v20/{task}_pos_0p02_time_3/rgb_abs_action/ACT_seed_1/rollouts/dataset_step_*_test_rollout/info.json",
        }
        task_records = []
        for method, pattern in patterns.items():
            for path in sorted(root.glob(pattern)):
                content, local = capture(path)
                rows = json.loads(content)
                if not isinstance(rows, list) or not rows:
                    raise ValueError(f"Expected nonempty episode outcomes: {path}")
                statuses = Counter(row["evaluation"]["status"] for row in rows)
                identifiers = [row.get("xml_path") for row in rows]
                if all(identifiers) and len(identifiers) != len(set(identifiers)):
                    raise ValueError(f"Duplicate evaluated scenes: {path}")
                step = int(re.fullmatch(r"dataset_step_(\d+)_test_rollout", path.parent.name)[1])
                task_records.append({
                    "method": method, "dataset_step": step, "successes": statuses["success"],
                    "trials": len(rows), "success_rate": statuses["success"] / len(rows),
                    "status_counts": dict(sorted(statuses.items())), "counts_origin": "episode outcomes",
                    "source_path": str(path), "source_file": local, "source_sha256": sha256(content),
                    "experiment": "dense_sample" if method == "dense_sampling" else f"v20/{task}_pos_0p02_time_3",
                })
        records[task] = task_records
        availability[task] = {"directory": str(root), "patterns": patterns,
                              "evaluations_found": len(task_records),
                              "top_level_entries": sorted(path.name for path in root.iterdir()) if root.is_dir() else []}
    supplementary = []
    for root in sorted((REMOTE_ROOT / "tasks").glob("tmp_flip_then_arrange_shoe*")):
        if not root.is_dir():
            continue
        for checkpoint in ("base", "finetuned"):
            path = root / "eval" / checkpoint / "info.json"
            if not path.is_file():
                continue
            content, local = capture(path)
            rows = json.loads(content)
            successes = sum(row["evaluation"]["status"] == "success" for row in rows)
            summary_path = path.with_name("summary.json")
            if summary_path.is_file():
                summary_content, _ = capture(summary_path)
                summary = json.loads(summary_content)
                if summary["scenes"] != len(rows) or summary["successes"] != successes:
                    raise ValueError(f"Recorded summary differs from episode outcomes: {path}")
            supplementary.append({"task": "flip_then_arrange_shoe", "experiment": root.name,
                                  "checkpoint": checkpoint, "dataset_step": None,
                                  "successes": successes, "trials": len(rows), "success_rate": successes / len(rows),
                                  "counts_origin": "episode outcomes", "source_path": str(path),
                                  "source_file": local, "source_sha256": sha256(content)})
        comparison = root / "eval/comparison.json"
        if comparison.is_file():
            capture(comparison)
    return {"collected_at": datetime.now(timezone.utc).isoformat(), "files": list(files.values()),
            "records": records, "availability": availability, "supplementary_evaluations": supplementary}


def csv_records(content, domain, sample_sizes, local_path, source):
    records = []
    for row_number, row in enumerate(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))), 2):
        if row["policy"] != "ACT":
            raise ValueError(f"Unexpected policy in requested ACT CSV: {row}")
        experiment = row["experiment"]
        if experiment not in ("dense sampling", "0p02_time_3"):
            raise ValueError(f"Select an explicit UniKey variant rather than mixing experiments: {experiment}")
        rate = Decimal(row["success_rate"])
        n = sample_sizes[domain]
        numerator = rate * n
        if not 0 <= rate <= 1 or numerator != numerator.to_integral_value():
            raise ValueError(f"CSV rate cannot be represented using its declared sample size: {row}")
        records.append({
            "method": "dense_sampling" if experiment == "dense sampling" else "unikey",
            "dataset_step": int(row["dataset_step"]), "success_rate": float(rate),
            "successes": int(numerator), "trials": n, "experiment": experiment,
            "counts_origin": "CSV rate with denominator declared by source plot; raw outcomes not supplied",
            "denominator_source": "plot_success_rate.py:DEFAULT_SAMPLE_SIZE_BY_SOURCE",
            "source_path": source["path"], "source_file": local_path,
            "source_sha256": source["sha256"], "source_row": row_number,
        })
    return records


def normalize(bundle, host):
    files = {entry["local_path"]: entry for entry in bundle["files"]}
    prefix = "raw/scripts/main_figure/ACT_hang_mug/"
    source_plot = base64.b64decode(files[prefix + "plot_success_rate.py"]["base64"]).decode()
    sample_sizes = None
    for node in ast.parse(source_plot).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "DEFAULT_SAMPLE_SIZE_BY_SOURCE" for target in node.targets):
            sample_sizes = ast.literal_eval(node.value)
    if sample_sizes != {"sim": 100, "real": 20}:
        raise ValueError(f"Review changed source sample-size declarations: {sample_sizes}")
    tasks = []
    for task, label in TASKS.items():
        notes, series = [], []
        domains = {"simulation": bundle["records"].get(task, [])}
        if task == "hang_mug":
            domains = {}
            for short, domain in (("sim", "simulation"), ("real", "real_world")):
                local = prefix + f"success_rate_{short}.csv"
                entry = files[local]
                domains[domain] = csv_records(base64.b64decode(entry["base64"]), short, sample_sizes, local, entry)
            notes.append("Simulation and real-world records are kept separate. CSV denominators are declared by the source plot, not independently counted from raw episodes.")
        for domain, rows in domains.items():
            for method in ("dense_sampling", "unikey"):
                points = sorted([row for row in rows if row["method"] == method], key=lambda row: row["dataset_step"])
                if len({point["dataset_step"] for point in points}) != len(points):
                    raise ValueError(f"Duplicate budget in {task}/{domain}/{method}")
                series.append({"method": method, "label": "Dense Sampling" if method == "dense_sampling" else "UniKey",
                               "domain": domain, "points": points})
                if domain == "simulation" and len(points) == 1:
                    notes.append(f"{method.replace('_', ' ').title()} has only one available evaluation ({points[0]['dataset_step']:,} dataset steps). No later checkpoints are inferred.")
        count = sum(len(item["points"]) for item in series)
        if count == 0:
            notes.append("No ACT success-rate evaluation records were found in the requested robo02 task directory.")
        if task == "pack_battery":
            notes.append("The dense-sampling rollout directory at 5k is empty; 21k contains a checkpoint but no evaluation. Both are excluded from the curves.")
        supplementary = [row for row in bundle["supplementary_evaluations"] if row["task"] == task]
        if supplementary:
            notes.append("Additional temporary base/finetuned comparisons are extracted separately. They have no dataset-budget labels and are not combined with the v20 learning curve.")
        tasks.append({"id": task, "label": label, "policy": "ACT", "seed": 1 if task != "hang_mug" else None,
                      "status": "missing_evaluations" if count == 0 else "available",
                      "series": series, "notes": notes,
                      "supplementary_evaluations": supplementary,
                      "availability": bundle["availability"].get(task),
                      "plot_shared_simulation_anchor": task == "hang_mug"})
    return {"schema_version": 1, "host": host, "collected_at": bundle["collected_at"],
            "source_root": str(REMOTE_ROOT),
            "definition": "successes / evaluated episodes; each source episode is counted once. Missing checkpoints remain unavailable.",
            "tasks": tasks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="robo02")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data_stat")
    parser.add_argument("--remote-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.remote_worker:
        print(json.dumps(collect_remote(), separators=(",", ":")))
        return
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", args.host,
               shlex.join(["python3", "-", "--remote-worker"])]
    result = subprocess.run(command, input=Path(__file__).read_text(), capture_output=True, text=True, check=True)
    bundle = json.loads(result.stdout)
    stats = normalize(bundle, args.host)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for entry in bundle["files"]:
        content = base64.b64decode(entry["base64"])
        if sha256(content) != entry["sha256"]:
            raise ValueError(f"Source transfer hash mismatch: {entry['path']}")
        target = args.output / entry["local_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        manifest.append({key: value for key, value in entry.items() if key != "base64"})
    (args.output / "sources.json").write_text(json.dumps({"host": args.host, "collected_at": bundle["collected_at"], "files": manifest}, indent=2) + "\n")
    (args.output / "statistics.json").write_text(json.dumps(stats, indent=2) + "\n")
    for task in stats["tasks"]:
        print(task["label"] + ": " + ", ".join(f"{s['domain']} {s['label']} {len(s['points'])} points" for s in task["series"]))
    print(f"Saved {len(manifest)} unchanged source files and normalized statistics in {args.output.resolve()}")


if __name__ == "__main__":
    main()
