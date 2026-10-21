#!/usr/bin/env python3
"""Regenerate RoboTwin figures from exported results and task-picker labels.

Run from any directory: python3 scripts/update_robotwin.py
Requires matplotlib, numpy, and scipy. No website build step is required.
"""

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


def bootstrap_shape(ax, point, width, color):
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
    ax.fill_betweenx(y, x - half_width, x + half_width, color=color, alpha=0.18, linewidth=0.8, edgecolor=color, zorder=1)


def plot_task(task, title):
    unikey = [task["initial"], *task["unikey"]]
    dense = task["dense"]
    xmin = min(point["steps"] for point in dense + unikey)
    xmax = max(point["steps"] for point in dense + unikey)
    span = xmax - xmin
    fig, ax = plt.subplots(figsize=(12, 9))
    fig.subplots_adjust(left=0.13, right=0.975, bottom=0.17, top=0.94)
    ax.set_xlim(xmin - span * 0.025, xmax + span * 0.035)
    ax.set_ylim(0, 109)
    ax.set_yticks(np.arange(0, 101, 20))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0f}%"))
    tick_spacing = 5000 if xmax <= 30000 else 10000
    ticks = sorted({xmin, xmax, *range(tick_spacing, xmax, tick_spacing)})
    ticks = [value for value in ticks if xmin <= value <= xmax]
    if len(ticks) > 2 and ticks[1] - ticks[0] < tick_spacing * 0.5:
        ticks.pop(1)
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:g}k"))
    ax.set_xlabel("Dataset Steps", fontsize=21, labelpad=14, color="#303630")
    ax.set_ylabel("Success Rate", fontsize=21, labelpad=18, color="#303630")
    ax.tick_params(axis="both", labelsize=16, colors="#545a54", width=1.3, length=6, pad=8)
    ax.grid(axis="y", color="#b4b9b4", linestyle="--", linewidth=1.3, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    for name in ("left", "bottom"):
        ax.spines[name].set_color("#545a54")
        ax.spines[name].set_linewidth(1.5)
    ax.plot(1, 0, marker=">", color="#545a54", markersize=11, transform=ax.transAxes, clip_on=False)
    ax.plot(0, 1, marker="^", color="#545a54", markersize=11, transform=ax.transAxes, clip_on=False)

    for points, color in ((dense, GRAY), (unikey, GREEN)):
        steps = [point["steps"] for point in points]
        spacing = min(np.diff(steps))
        for point in points:
            # Shared initial outcomes are drawn once, in gray.
            if points is unikey and point is task["initial"]:
                continue
            bootstrap_shape(ax, point, min(spacing * 0.22, span * 0.012), color)
        ax.plot(steps, [percentage(point) for point in points], color=color, linewidth=3.2, marker="o", markersize=8.5, markeredgecolor="white", markeredgewidth=1.5, zorder=3)

    best, _ = results(task)
    ax.scatter(best["steps"], percentage(best), marker="*", s=500, color="#e8d995", edgecolor=GREEN, linewidth=1.8, zorder=5)
    dense_perfect = next((point for point in dense if point["successes"] == point["trials"]), None)
    if dense_perfect:
        ax.scatter(dense_perfect["steps"], 100, marker="*", s=430, color="#e8d995", edgecolor=GRAY, linewidth=1.8, zorder=4)

    # Label the lines directly; reserve the space above 100% for the UniKey label.
    for label, points, color, dy in (("UniKey", unikey, GREEN_TEXT, 18), ("Dense Sampling", dense, GRAY_TEXT, -24)):
        end = points[-1]
        near_left = end["steps"] < xmin + span * 0.25
        ax.annotate(label, (end["steps"], percentage(end)), xytext=(8 if near_left else -6, dy), textcoords="offset points", fontsize=19, color=color, ha="left" if near_left else "right", va="center", zorder=6)
    fig.text(0.55, 0.035, "100 rollouts / point · 95% bootstrap distributions", ha="center", color="#737773", fontsize=11)

    output = ROOT / "media" / "robotwin" / task["media_directory"]
    description = f"{title}. Actual evaluation checkpoints. Pale shapes show central 95% empirical bootstrap distributions of binary rollout means, not training-seed variation."
    svg_path = output / "success-rate.svg"
    fig.savefig(svg_path, metadata={"Title": title, "Description": description, "Date": None})
    svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n")
    fig.savefig(output / "success-rate.png", dpi=200, metadata={"Title": title, "Description": description})
    plt.close(fig)


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "svg.hashsalt": "unikey-robotwin", "axes.unicode_minus": False})
    data = json.loads((ROOT / "data" / "robotwin-results.json").read_text())
    html_path = ROOT / "index.html"
    html = html_path.read_text()
    for task in data["tasks"]:
        for series in (task["dense"], task["unikey"]):
            assert len({point["steps"] for point in series}) == len(series)
            assert [point["steps"] for point in series] == sorted(point["steps"] for point in series)
            assert all(point["trials"] == 100 and 0 <= point["successes"] <= 100 for point in series)
        task_id = task["id"]
        title = re.search(rf'<button type="button" data-task="{task_id}"[^>]*>(.*?)</button>', html)[1]
        best, dense = results(task)
        budget = f'{best["steps"] / 1000:g}k'
        plot_task(task, title)
        print(f'{title}: UniKey {percentage(best):g}%, Dense {percentage(dense):g}% at {budget}')


if __name__ == "__main__":
    main()
