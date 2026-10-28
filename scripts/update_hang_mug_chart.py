#!/usr/bin/env python3
"""Regenerate the inline, progressively enhanced Hang Mug improvement chart."""
import hashlib
from html import escape
import json
from pathlib import Path
import re

import numpy as np
from scipy.stats import binom


ROOT = Path(__file__).resolve().parents[1]
# Same 576-point square canvas and axes as the current emphasized RoboTwin
# figures. CSS offsets the 4.5% top margin so the axes match a 4:3 video.
LEFT, RIGHT, TOP, BOTTOM = 103.68, 561.6, 25.92, 457.92
LAYOUT = {
    "xStart": 114.48, "xPerRound": 24, "yBottom": BOTTOM, "yPerPercent": 432 / 109,
    "clipLeft": LEFT, "clipWidth": RIGHT - LEFT, "markerRadius": 3.25,
    "labelSwitchRound": 5.5, "unikeyLabelOffset": -12.205313, "denseLabelOffset": 29.242813,
}


def x(round_number):
    return LAYOUT["xStart"] + (round_number - 1) * LAYOUT["xPerRound"]


def y(percent):
    return BOTTOM - percent * LAYOUT["yPerPercent"]


def uncertainty(point):
    n, successes = point["trials"], point["successes"]
    if successes in (0, n):
        return ""
    p = successes / n
    low, high = binom.ppf([.025, .975], n, p).astype(int)
    counts = np.arange(low, high + 1)
    density = binom.pmf(counts, n, p)
    half_width = np.r_[0, density / density.max() * 5.184, 0]
    support = np.r_[low, counts, high]
    positions = [(x(point["round"]) - width, y(count / n * 100)) for count, width in zip(support, half_width)]
    positions += [(x(point["round"]) + width, y(count / n * 100)) for count, width in zip(support[::-1], half_width[::-1])]
    return "M " + " L ".join(f"{a:.3f} {b:.3f}" for a, b in positions) + " Z"


def chart(data):
    stages = escape(json.dumps(data["timeline"], separators=(",", ":")), quote=True)
    layout = escape(json.dumps(LAYOUT, separators=(",", ":")), quote=True)
    description = "Measured ACT evaluation checkpoints at equal dataset budgets. Round 1 starts at 10,000 dataset steps; each subsequent round adds 1,000 steps. Both comparison lines are solid. Pale shapes show central 95% bootstrap distributions of binary rollout means."
    if len(data["series"][0]["points"]) == 1:
        description += " Matching Dense Sampling results are currently available only at the shared initial checkpoint."
    lines = [
        f'<svg class="round-improvement-plot" viewBox="0 0 576 576" width="1440" height="1440" role="img" aria-labelledby="hang-mug-chart-title hang-mug-chart-description" data-stages="{stages}" data-chart-layout="{layout}">',
        '  <title id="hang-mug-chart-title">Hang Mug: success rate across training rounds</title>',
        f'  <desc id="hang-mug-chart-description">{escape(description)}</desc>',
        f'  <defs><clipPath id="hang-mug-chart-reveal"><rect data-chart-reveal x="{LEFT}" y="{TOP}" width="{RIGHT - LEFT:g}" height="{BOTTOM - TOP:g}" /></clipPath></defs>',
        '  <g class="round-chart-grid">',
    ]
    for tick in range(0, 101, 20):
        lines.append(f'    <line x1="{LEFT}" y1="{y(tick):.6f}" x2="{RIGHT}" y2="{y(tick):.6f}" />')
    lines += ['  </g>', '  <g class="round-chart-axes">',
              f'    <path d="M {LEFT} {TOP} V {BOTTOM} H {RIGHT}" />',
              f'    <path d="M 0 -5.5 L -5.5 5.5 L 5.5 5.5 Z" transform="translate({LEFT} {TOP})" fill="currentColor" stroke="none" />',
              f'    <path d="M 5.5 0 L -5.5 -5.5 L -5.5 5.5 Z" transform="translate({RIGHT} {BOTTOM})" fill="currentColor" stroke="none" />',
              '  </g>', '  <g class="round-chart-tick-marks">']
    for tick in range(0, 101, 20):
        lines.append(f'    <path d="M {LEFT} {y(tick):.6f} h -6" />')
    for tick in (1, 6, 11, 16, 19):
        lines.append(f'    <path d="M {x(tick):.6f} {BOTTOM} v 6" />')
    lines += ['  </g>', '  <g class="round-chart-ticks">']
    for tick in range(0, 101, 20):
        lines.append(f'    <text x="89.68" y="{y(tick) + 6.07875:.6f}" text-anchor="end">{tick}%</text>')
    for tick in (1, 6, 11, 16, 19):
        steps = data["round_numbering"]["initial_dataset_steps"] + (tick - 1) * data["round_numbering"]["steps_per_round"]
        lines.append(f'    <text x="{x(tick):.6f}" y="484.0775" text-anchor="middle">{steps / 1000:g}k</text>')
    lines += ['  </g>',
              '  <text class="round-chart-axis-title" x="332.64" y="517.361719" text-anchor="middle">Dataset Steps</text>',
              '  <text class="round-chart-axis-title" transform="translate(21.570156 241.92) rotate(-90)" text-anchor="middle">Success Rate</text>']
    for series in data["series"]:
        points = series["points"]
        assert points and [p["round"] for p in points] == sorted({p["round"] for p in points})
        assert all(0 <= p["successes"] <= p["trials"] == 100 for p in points)
        values = escape(json.dumps([[p["round"], 100 * p["successes"] / p["trials"]] for p in points], separators=(",", ":")), quote=True)
        lines.append(f'  <g data-chart-series="{series["id"]}" data-chart-points="{values}" style="color:{series["color"]}">')
        lines.append('    <g clip-path="url(#hang-mug-chart-reveal)">')
        for point in points:
            # Both methods share this evaluation: draw its uncertainty once.
            if point["round"] == 1 and series["id"] == "unikey":
                continue
            shape = uncertainty(point)
            if shape:
                lines.append(f'      <path class="round-chart-uncertainty" d="{shape}" />')
        coordinates = " ".join(f'{x(p["round"]):.3f},{y(p["successes"] / p["trials"] * 100):.3f}' for p in points)
        lines.append(f'      <polyline class="round-chart-line" points="{coordinates}" stroke-width="3.2" />')
        for point in points:
            lines.append(f'      <circle class="round-chart-point" cx="{x(point["round"]):.3f}" cy="{y(point["successes"] / point["trials"] * 100):.3f}" r="3.25" />')
        if series["id"] == "unikey":
            best = max(points, key=lambda point: (point["successes"], -point["round"]))
            lines.append(f'      <path class="round-chart-best" transform="translate({x(best["round"]):.3f} {y(best["successes"]):.3f})" d="M 0 -11.18034 L -2.510143 -3.454915 L -10.633135 -3.454915 L -4.061496 1.31966 L -6.571639 9.045085 L 0 4.270509 L 6.571639 9.045085 L 4.061496 1.31966 L 10.633135 -3.454915 L 2.510143 -3.454915 Z" />')
        lines.append('    </g>')
        end = points[-1]
        right = end["round"] >= LAYOUT["labelSwitchRound"]
        label_x = x(end["round"]) + (-6 if right else 8)
        label_y = y(end["successes"] / end["trials"] * 100) + LAYOUT[series["id"] + "LabelOffset"]
        lines.append(f'    <text class="round-chart-label" data-chart-label x="{label_x:.3f}" y="{label_y:.3f}" text-anchor="{"end" if right else "start"}">{series["label"]}</text>')
        lines.append('  </g>')
    lines += ['  <text class="round-chart-note" x="316.8" y="555.84" text-anchor="middle">100 rollouts / point · 95% bootstrap distributions</text>', '</svg>']
    return "\n".join(lines)


def main():
    data = json.loads((ROOT / "data/hang-mug-improvement.json").read_text())
    path = ROOT / "index.html"
    html = path.read_text()
    svg = chart(data)
    replacement = "<!-- hang-mug-improvement-chart:start -->\n" + "\n".join("                  " + line for line in svg.splitlines()) + "\n                  <!-- hang-mug-improvement-chart:end -->"
    html, count = re.subn(r"<!-- hang-mug-improvement-chart:start -->[\s\S]*?<!-- hang-mug-improvement-chart:end -->", lambda _: replacement, html)
    if count != 1:
        raise ValueError("Expected exactly one Hang Mug improvement chart in index.html")
    for asset in ("assets/round-improvement.js", "assets/site.css",
                  "assets/videos/pipeline/failure-detection-correction/hang-mug/training-rounds.mp4",
                  "assets/videos/pipeline/failure-detection-correction/hang-mug/training-rounds-poster.jpg"):
        digest = hashlib.sha256((ROOT / asset).read_bytes()).hexdigest()[:12]
        html = re.sub(re.escape("./" + asset) + r"(?:\?v=[^\"<>\s]+)?", "./" + asset + "?v=" + digest, html)
    path.write_text(html)
    print("Updated the inline Hang Mug improvement chart and asset versions.")


if __name__ == "__main__":
    main()
