#!/usr/bin/env python3
"""Query hang_mug ACT success rates for dense sampling and v19."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path


TASK_ROOT = Path("/local/robopil/yuan/tasks/hang_mug")
DATA_MODE = "rgb_abs_action"
POLICY = "ACT"
SEED = 1
SCENE_TYPE = "test_rollout"

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = SCRIPT_DIR / "success_rate_sim.csv"

DATASET_STEP_ROLLOUT_RE = re.compile(r"^dataset_step_(?P<step>\d+)_test_rollout$")


@dataclass(frozen=True)
class SuccessPoint:
    policy: str
    experiment: str
    dataset_step: int
    success_rate: float
    info_path: Path


def dataset_step_from_rollout_path(info_path: Path) -> int:
    match = DATASET_STEP_ROLLOUT_RE.fullmatch(info_path.parent.name)
    return int(match.group("step"))


def success_rate_from_info(info_path: Path) -> float:
    with info_path.open("r") as f:
        rollout_info = json.load(f)

    successes = sum(
        sample_info["evaluation"]["status"] == "success"
        for sample_info in rollout_info
    )
    return successes / len(rollout_info)


def make_point(policy: str, experiment: str, info_path: Path) -> SuccessPoint:
    return SuccessPoint(
        policy=policy,
        experiment=experiment,
        dataset_step=dataset_step_from_rollout_path(info_path),
        success_rate=success_rate_from_info(info_path),
        info_path=info_path,
    )


def load_dense_points(
    task_root: Path,
    data_mode: str,
    policy: str,
    seed: int,
) -> list[SuccessPoint]:
    info_paths = (task_root / "dense_sample" / data_mode).glob(
        f"dataset_step_*/{policy}_rollout_seed_{seed}/dataset_step_*_{SCENE_TYPE}/info.json"
    )

    points = [
        make_point(policy, "dense sampling", info_path)
        for info_path in info_paths
    ]
    return sorted(points, key=lambda point: point.dataset_step)


def v19_label(experiment_dir: Path, task_name: str) -> str:
    return experiment_dir.name.removeprefix(f"{task_name}_pos_")


def load_v19_points(
    task_root: Path,
    data_mode: str,
    policy: str,
    seed: int,
) -> list[SuccessPoint]:
    task_name = task_root.name
    points = []
    for experiment_dir in sorted((task_root / "v19").glob(f"{task_name}_pos_*")):
        rollouts_dir = (
            experiment_dir
            / data_mode
            / f"{policy}_seed_{seed}"
            / "rollouts"
        )
        points.extend(
            make_point(policy, v19_label(experiment_dir, task_name), info_path)
            for info_path in rollouts_dir.glob(f"dataset_step_*_{SCENE_TYPE}/info.json")
        )

    return sorted(points, key=lambda point: (point.experiment, point.dataset_step))


def point_sort_key(point: SuccessPoint) -> tuple[int, str, int]:
    series_rank = 0 if point.experiment == "dense sampling" else 1
    return (series_rank, point.experiment, point.dataset_step)


def write_csv(points: list[SuccessPoint], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["policy", "experiment", "dataset_step", "success_rate"])
        for point in sorted(points, key=point_sort_key):
            writer.writerow(
                [
                    point.policy,
                    point.experiment,
                    point.dataset_step,
                    f"{point.success_rate:.6f}",
                ]
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query hang_mug ACT success rates from dense sampling and v19."
    )
    parser.add_argument("--task-root", type=Path, default=TASK_ROOT)
    parser.add_argument("--data-mode", default=DATA_MODE)
    parser.add_argument("--policy", default=POLICY)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_CSV_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    dense_points = load_dense_points(
        args.task_root,
        args.data_mode,
        args.policy,
        args.seed,
    )
    v19_points = load_v19_points(
        args.task_root,
        args.data_mode,
        args.policy,
        args.seed,
    )
    if not dense_points:
        raise ValueError("No dense sampling success-rate points found")
    if not v19_points:
        raise ValueError("No v19 success-rate points found")

    points = [
        *dense_points,
        *v19_points,
    ]
    write_csv(points, args.output_csv)

    print(f"Wrote {len(points)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
