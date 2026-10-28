#!/usr/bin/env python3
"""Regenerate RoboTwin figures from exported results and task-picker labels.

Run from any directory: python3 scripts/update_robotwin.py
Requires matplotlib, numpy, and scipy. No website build step is required.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from scipy.stats import binom


ROOT = Path(__file__).resolve().parents[1]
GREEN = "#7b9e86"
GREEN_TEXT = "#587261"
GRAY = "#a2a5a3"
GRAY_TEXT = "#737773"


def percentage(point):
    return 100 * point["successes"] / point["trials"]


def results(task):
    best = max(task["unikey"], key=lambda point: (percentage(point), -point["steps"]))
    dense = next(point for point in task["dense"] if point["steps"] == best["steps"])
    return best, dense


def bootstrap_shape(ax, point, width, color, alpha=0.18):
    """Exact bootstrap mean distribution for observed binary rollout outcomes.

    Drawing the central 95% support prevents tails from obscuring nearby curves.
    At all-success/all-failure checkpoints this empirical distribution is a point.
    """
    n = point["trials"]
    p = point["successes"] / n
    if p == 0 or p == 1:
        return
    low, high = binom.ppf([0.025, 0.975], n, p).astype(int)
    counts = np.arange(low, high + 1)
    density = binom.pmf(counts, n, p)
    half_width = width * density / density.max()
    y = np.r_[100 * low / n, 100 * counts / n, 100 * high / n]
    half_width = np.r_[0, half_width, 0]
    x = point["steps"]
    ax.fill_betweenx(y, x - half_width, x + half_width, color=color, alpha=alpha, linewidth=0.8, edgecolor=color, zorder=1)


def plot_task(task, title, emphasized=False):
    green = "#37895b" if emphasized else GREEN
    dense_color = "#6b4935" if emphasized else GRAY
    unikey = [task["initial"], *task["unikey"]]
    dense = task["dense"]
    cutoff = {"dump-bin-bigbin": 5000, "beat-block-hammer": 11000}.get(task["id"])
    if cutoff is not None:
        unikey = [point for point in unikey if point["steps"] <= cutoff]
        dense = [point for point in dense if point["steps"] <= cutoff]
    xmin = min(point["steps"] for point in dense + unikey)
    xmax = max(point["steps"] for point in dense + unikey)
    span = xmax - xmin
    fig, ax = plt.subplots(figsize=(8, 8) if emphasized else (12, 9))
    # The axes are 75% of the square canvas width, matching a 4:3 video.
    # Its 4.5% top margin is offset by the task's CSS so the axes align with it.
    fig.subplots_adjust(left=0.18 if emphasized else 0.13, right=0.975,
                        bottom=0.205 if emphasized else 0.17, top=0.955 if emphasized else 0.94)
    ax.set_xlim(xmin - span * 0.025, cutoff if cutoff is not None else xmax + span * 0.035)
    ax.set_ylim(0, 109)
    ax.set_yticks(np.arange(0, 101, 20))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0f}%"))
    tick_spacing = 1000 if xmax <= 5000 else 5000 if xmax <= 30000 else 10000
    ticks = sorted({xmin, xmax, *range(tick_spacing, xmax, tick_spacing)})
    ticks = [value for value in ticks if xmin <= value <= xmax]
    if len(ticks) > 2 and ticks[1] - ticks[0] < tick_spacing * 0.5:
        ticks.pop(1)
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:g}k"))
    ax.set_xlabel("Dataset Steps", fontsize=21, labelpad=14, color="#303630")
    ax.set_ylabel("Success Rate", fontsize=21, labelpad=18, color="#303630")
    ax.tick_params(axis="both", labelsize=16, colors="#545a54", width=1.3, length=6, pad=8)
    ax.grid(axis="y", color="#d9ddd7" if emphasized else "#b4b9b4", linestyle="--", linewidth=0.9 if emphasized else 1.3, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    for name in ("left", "bottom"):
        ax.spines[name].set_color("#545a54")
        ax.spines[name].set_linewidth(1.5)
    ax.plot(1, 0, marker=">", color="#545a54", markersize=11, transform=ax.transAxes, clip_on=False)
    ax.plot(0, 1, marker="^", color="#545a54", markersize=11, transform=ax.transAxes, clip_on=False)

    for points, color in ((dense, dense_color), (unikey, green)):
        steps = [point["steps"] for point in points]
        spacing = min(np.diff(steps))
        for point in points:
            # Draw the shared initial uncertainty only once.
            if points is unikey and point is task["initial"]:
                continue
            bootstrap_shape(ax, point, min(spacing * 0.22, span * 0.012), color, alpha=0.10 if emphasized else 0.18)
        ax.plot(steps, [percentage(point) for point in points], color=color,
                linewidth=3.2, linestyle="-",
                marker="o", markersize=6.5 if emphasized else 8.5,
                markeredgecolor="white", markeredgewidth=0.6 if emphasized else 1.5,
                zorder=4 if points is unikey else 3)

    for points in (unikey, dense):
        perfect = next((point for point in points if point["successes"] == point["trials"]), None)
        if perfect is not None:
            ax.scatter(perfect["steps"], 100, marker="*", s=500,
                       color="#e5c878" if emphasized else "#e8d995", edgecolor="none",
                       linewidth=0, clip_on=False, zorder=5)

    # Label the lines directly; reserve the space above 100% for the UniKey label.
    for label, points, color, dy in (("UniKey", unikey, green if emphasized else GREEN_TEXT, 18), ("Dense Sampling", dense, dense_color if emphasized else GRAY_TEXT, -24)):
        if cutoff is not None and label == "Dense Sampling":
            dy = -38
        end = points[-1]
        near_left = end["steps"] < xmin + span * 0.25
        ax.annotate(label, (end["steps"], percentage(end)), xytext=(8 if near_left else -6, dy), textcoords="offset points", fontsize=21 if emphasized and points is unikey else 19,
                    fontweight="normal", color=color, ha="left" if near_left else "right", va="center", zorder=6)
    fig.text(0.55, 0.035, "100 rollouts / point · 95% bootstrap distributions", ha="center", color="#737773", fontsize=14 if emphasized else 11)

    output = ROOT / "media" / "robotwin" / task["media_directory"]
    description = f"{title}. Actual evaluation checkpoints. Pale shapes show central 95% empirical bootstrap distributions of binary rollout means, not training-seed variation."
    description += " Yellow stars mark each method's first checkpoint with 100% success."
    if cutoff is not None:
        description += f" Checkpoints through {cutoff:,} dataset steps are shown."
    svg_path = output / "success-rate.svg"
    fig.savefig(svg_path, metadata={"Title": title, "Description": description, "Date": None})
    svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n")
    fig.savefig(output / "success-rate.png", dpi=180 if emphasized else 200, metadata={"Title": title, "Description": description})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", help="Regenerate only this website task ID, for example adjust-bottle.")
    parser.add_argument("--style", choices=("original", "emphasized"), default="emphasized", help="Use the approved styling, or reproduce the original figures.")
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "svg.hashsalt": "unikey-robotwin", "axes.unicode_minus": False})
    data = json.loads((ROOT / "data" / "robotwin-results.json").read_text())
    html_path = ROOT / "index.html"
    html = html_path.read_text()
    tasks = [task for task in data["tasks"] if args.task is None or task["id"] == args.task]
    if not tasks:
        parser.error(f"Unknown task ID: {args.task}")
    versions = {}
    for task in tasks:
        for series in (task["dense"], task["unikey"]):
            assert len({point["steps"] for point in series}) == len(series)
            assert [point["steps"] for point in series] == sorted(point["steps"] for point in series)
            assert all(point["trials"] == 100 and 0 <= point["successes"] <= 100 for point in series)
        task_id = task["id"]
        title = re.search(rf'<button type="button" data-task="{task_id}"[^>]*>(.*?)</button>', html)[1]
        best, dense = results(task)
        budget = f'{best["steps"] / 1000:g}k'
        plot_task(task, title, emphasized=args.style == "emphasized")
        svg = ROOT / "media/robotwin" / task["media_directory"] / "success-rate.svg"
        relative = f'./media/robotwin/{task["media_directory"]}/success-rate.svg'
        digest = hashlib.sha256(svg.read_bytes()).hexdigest()[:12]
        versions[relative] = digest
        print(f'{title}: UniKey {percentage(best):g}%, Dense {percentage(dense):g}% at {budget}')
    html = html_path.read_text()
    for relative, digest in versions.items():
        html = re.sub(re.escape(relative) + r'(?:\?v=[^"<>\s]+)?', relative + "?v=" + digest, html)
    html_path.write_text(html)


if __name__ == "__main__":
    main()
