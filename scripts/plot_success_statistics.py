#!/usr/bin/env python3
"""Plot the extracted data_stat results locally, using the current RoboTwin style.

Run extract_success_statistics.py first. This script reads only local files and
does not change the main webpage or combine separate experiment evaluations.
"""
from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from update_robotwin import bootstrap_shape


ROOT = Path(__file__).resolve().parents[1]
COLORS = {"unikey": "#37895b", "dense_sampling": "#6b4935"}


def selected_series(task, domain):
    return [series for series in task["series"] if series["domain"] == domain]


def plot_points(task, series, domain):
    points = list(series["points"])
    # The supplied Hang Mug source plot explicitly connects UniKey's simulation
    # curve to the first Dense Sampling evaluation. Keep that plotting anchor
    # separate from the CSV's original measurement rows.
    if task.get("plot_shared_simulation_anchor") and domain == "simulation" and series["method"] == "unikey" and points:
        dense = next(s for s in selected_series(task, domain) if s["method"] == "dense_sampling")
        initial = dense["points"][0]
        if initial["dataset_step"] < points[0]["dataset_step"]:
            points.insert(0, {**initial, "plot_anchor": True})
    return points


def draw(ax, task, domain="simulation", compact=False):
    series_list = selected_series(task, domain)
    all_points = [point for series in series_list for point in series["points"]]
    if not all_points:
        ax.set_axis_off()
        ax.text(.5, .55, "No evaluation records found", ha="center", va="center", fontsize=21, color="#545a54", transform=ax.transAxes)
        ax.text(.5, .46, "Arrange Table results are unavailable\nin the specified robo02 task directory.", ha="center", va="center", fontsize=15, color="#737773", linespacing=1.6, transform=ax.transAxes)
        return
    xmin = min(point["dataset_step"] for point in all_points)
    xmax = max(point["dataset_step"] for point in all_points)
    span = max(xmax - xmin, 1000)
    ax.set_xlim(xmin - span * .025, xmax + span * .035)
    ax.set_ylim(0, 109)
    ax.set_yticks(np.arange(0, 101, 20))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0f}%"))
    tick_spacing = 5000 if xmax <= 30000 else 10000
    ticks = sorted({xmin, xmax, *range(tick_spacing, xmax, tick_spacing)})
    ticks = [value for value in ticks if xmin <= value <= xmax]
    if len(ticks) > 2 and ticks[1] - ticks[0] < tick_spacing * .5:
        ticks.pop(1)
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:g}k"))
    ax.set_xlabel("Dataset Steps", fontsize=18 if compact else 21, labelpad=14, color="#303630")
    ax.set_ylabel("Success Rate", fontsize=18 if compact else 21, labelpad=18, color="#303630")
    ax.tick_params(axis="both", labelsize=13 if compact else 16, colors="#545a54", width=1.3, length=6, pad=8)
    ax.grid(axis="y", color="#d9ddd7", linestyle="--", linewidth=.9, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    for name in ("left", "bottom"):
        ax.spines[name].set_color("#545a54")
        ax.spines[name].set_linewidth(1.5)
    ax.plot(1, 0, marker=">", color="#545a54", markersize=11, transform=ax.transAxes, clip_on=False)
    ax.plot(0, 1, marker="^", color="#545a54", markersize=11, transform=ax.transAxes, clip_on=False)
    for series in series_list:
        points = plot_points(task, series, domain)
        if not points:
            continue
        color = COLORS[series["method"]]
        steps = [point["dataset_step"] for point in points]
        spacing = min(np.diff(steps)) if len(steps) > 1 else span
        for point in points:
            if point.get("plot_anchor"):
                continue
            bootstrap_shape(ax, {"steps": point["dataset_step"], "successes": point["successes"], "trials": point["trials"]},
                            min(spacing * .22, span * .012), color, alpha=.1)
        ax.plot(steps, [100 * point["success_rate"] for point in points], color=color, linewidth=3.2, linestyle="-",
                marker="o", markersize=6.5, markeredgecolor="white", markeredgewidth=.6,
                zorder=4 if series["method"] == "unikey" else 3)
        if series["method"] == "unikey":
            best = max(series["points"], key=lambda point: (point["success_rate"], -point["dataset_step"]))
            ax.scatter(best["dataset_step"], 100 * best["success_rate"], marker="*", s=500, color="#e5c878", edgecolor="none", linewidth=0, zorder=5)
        end = points[-1]
        near_left = end["dataset_step"] < xmin + span * .25
        label_offset = 18 if series["method"] == "unikey" else (-24 if end["success_rate"] >= .12 else 0)
        ax.annotate(series["label"], (end["dataset_step"], 100 * end["success_rate"]),
                    xytext=(8 if near_left else -6, label_offset), textcoords="offset points",
                    fontsize=(18 if compact else 21) if series["method"] == "unikey" else (17 if compact else 19),
                    fontweight="normal", color=color, ha="left" if near_left else "right", va="center", zorder=6)


def summary(task):
    result = {"id": task["id"], "label": task["label"], "status": task["status"], "series": [],
              "supplementary_evaluations": task.get("supplementary_evaluations", [])}
    for series in task["series"]:
        points = series["points"]
        item = {"method": series["method"], "domain": series["domain"], "point_count": len(points)}
        if points:
            best = max(points, key=lambda point: (point["success_rate"], -point["dataset_step"]))
            item.update({"first_step": points[0]["dataset_step"], "last_step": points[-1]["dataset_step"],
                         "last_success_rate": points[-1]["success_rate"], "best_step": best["dataset_step"],
                         "best_success_rate": best["success_rate"], "trials_per_point": sorted({p["trials"] for p in points})})
        result["series"].append(item)
    return result


def html_preview(stats, directory):
    cards = []
    for task in stats["tasks"]:
        methods = selected_series(task, "simulation")
        counts = " · ".join(f"{series['label']}: {len(series['points'])} checkpoints" for series in reversed(methods))
        notes = "".join(f"<p>{escape(note)}</p>" for note in task["notes"])
        supplementary = task.get("supplementary_evaluations", [])
        if supplementary:
            rows = "".join(f"<tr><td>{escape(row['experiment'])}</td><td>{escape(row['checkpoint'])}</td><td>{row['successes']}/{row['trials']}</td><td>{row['success_rate']:.0%}</td></tr>" for row in supplementary)
            notes += '<p>Separate base/finetuned evaluations:</p><table style="width:100%;font-size:12px;overflow-wrap:anywhere"><thead><tr><th>Experiment</th><th>Policy</th><th>Successes</th><th>Rate</th></tr></thead><tbody>' + rows + '</tbody></table>'
        filename = f"plots/{task['id']}.svg"
        digest = hashlib.sha256((directory / filename).read_bytes()).hexdigest()[:12]
        cards.append(f'''<article><h2>{escape(task['label'])}</h2><p class="coverage">{escape(counts)}</p>
<a href="{filename}" target="_blank"><img src="{filename}?v={digest}" width="1440" height="1440" alt="{escape(task['label'])} simulation success rates" /></a>
<p class="downloads"><a href="{filename}">SVG</a><a href="plots/{task['id']}.png">PNG</a></p><div class="notes">{notes}</div></article>''')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ACT Success Rates — Local Preview</title><style>
*{box-sizing:border-box}body{margin:0;background:#f6f6ef;color:#303630;font:17px/1.55 Arial,sans-serif}main{max-width:1400px;margin:auto;padding:40px 28px 64px}h1,h2{font-family:Georgia,serif;font-weight:400;line-height:1.2}h1{font-size:38px;margin:0 0 16px}h2{font-size:27px;margin:0 0 8px}a{color:#37895b;text-underline-offset:3px}header{margin-bottom:36px}header p{margin:8px 0}.links,.downloads{display:flex;flex-wrap:wrap;gap:20px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:40px 32px}article{min-width:0;border-top:1px solid #d9ddd7;padding-top:22px}article img{display:block;width:100%;height:auto;mix-blend-mode:multiply}.coverage{color:#65655f;font-size:14px;margin:0 0 8px}.notes{font-size:14px;color:#65655f}.notes p{margin:8px 0}.downloads{font-size:14px;margin:8px 0}.real{margin-top:48px;max-width:680px}.real img{width:100%;height:auto;mix-blend-mode:multiply}@media(max-width:700px){main{padding:28px 18px 44px}.grid{grid-template-columns:1fr}h1{font-size:30px}}
</style></head><body><main><header><h1>ACT success rates</h1>
<p>Simulation results from robo02. Both methods use solid lines; every available checkpoint is retained.</p>
<p class="coverage">Extracted ''' + escape(stats["collected_at"]) + '''. Pale shapes show central 95% empirical bootstrap distributions, separate from variation across training seeds.</p>
<p class="links"><a href="statistics.json">Statistics JSON</a><a href="summary.json">Summary JSON</a><a href="sources.json">Source files and hashes</a><a href="plots/overview.png">Four-task overview</a></p></header>
<section class="grid">''' + "\n".join(cards) + '''</section>
<section class="real"><h2>Hang Mug: real-world results</h2><p>The four reported real-world evaluations are plotted separately from simulation.</p><a href="plots/hang_mug_real.svg"><img src="plots/hang_mug_real.svg" alt="Hang Mug real-world success rates" width="1440" height="1440"></a><p class="downloads"><a href="plots/hang_mug_real.svg">SVG</a><a href="plots/hang_mug_real.png">PNG</a></p></section>
</main></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data_stat")
    args = parser.parse_args()
    directory = args.data_dir.resolve()
    stats = json.loads((directory / "statistics.json").read_text())
    plots = directory / "plots"
    plots.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "svg.hashsalt": "unikey-data-stat", "axes.unicode_minus": False})
    for task in stats["tasks"]:
        domains = ["simulation", "real_world"] if task["id"] == "hang_mug" else ["simulation"]
        for domain in domains:
            fig, ax = plt.subplots(figsize=(8, 8))
            fig.subplots_adjust(left=.18, right=.975, bottom=.205, top=.955)
            draw(ax, task, domain)
            series = selected_series(task, domain)
            counts = {p["trials"] for s in series for p in s["points"]}
            if counts:
                note = f"{', '.join(str(n) for n in sorted(counts))} rollouts / point · 95% bootstrap distributions"
                fig.text(.55, .035, note, ha="center", color="#737773", fontsize=14)
            name = task["id"] + ("_real" if domain == "real_world" else "")
            metadata = {"Title": task["label"] + (" real-world" if domain == "real_world" else " simulation"),
                        "Description": "Extracted success rates. " + " ".join(task["notes"])}
            fig.savefig(plots / f"{name}.svg", metadata={**metadata, "Date": None})
            fig.savefig(plots / f"{name}.png", dpi=180, metadata=metadata)
            plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(16, 15))
    fig.subplots_adjust(left=.09, right=.97, bottom=.105, top=.94, wspace=.28, hspace=.4)
    for ax, task in zip(axes.flat, stats["tasks"]):
        draw(ax, task, compact=True)
        ax.set_title(task["label"], fontsize=23, color="#303630", pad=20, fontweight="normal")
    fig.text(.5, .02, "Simulation · 95% empirical bootstrap distributions · Missing evaluations are not interpolated", ha="center", fontsize=14, color="#737773")
    fig.savefig(plots / "overview.png", dpi=150)
    plt.close(fig)
    (directory / "summary.json").write_text(json.dumps({"host": stats["host"], "collected_at": stats["collected_at"], "tasks": [summary(task) for task in stats["tasks"]]}, indent=2) + "\n")
    (directory / "index.html").write_text(html_preview(stats, directory))
    print(f"Saved five standalone plots, a four-task overview, summaries, and local preview: {directory / 'index.html'}")


if __name__ == "__main__":
    main()
