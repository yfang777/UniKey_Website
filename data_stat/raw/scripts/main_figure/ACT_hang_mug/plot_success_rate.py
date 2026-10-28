#!/usr/bin/env python3
"""Draw beta-posterior violin plots for hang_mug ACT success rates."""

from __future__ import annotations

import argparse
import colorsys
import csv
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PathCollection, PolyCollection
from matplotlib.colors import to_hex, to_rgb
from matplotlib import font_manager
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter, StrMethodFormatter
from matplotlib.transforms import offset_copy
import numpy as np
from scipy.stats import beta as beta_dist


PRIOR_ALPHA = 1
PRIOR_BETA = 1
LOWER_Q = 0.025
UPPER_Q = 0.975
DEFAULT_SAMPLE_SIZE_BY_SOURCE = {
    "sim": 100,
    "real": 20,
}

X_AXIS_START = 2000.0
X_AXIS_END = 40000.0
X_AXIS_INTERVAL = 1000.0
X_AXIS_EXCLUDED_DATASET_STEPS: tuple[int, ...] = ()
X_AXIS_EDGE_PADDING_INTERVALS = 0.5
REAL_POINT_X_OFFSET_INTERVALS = 0.3

DENSE_SAMPLING_BASE_COLOR = "#8c8c8c"
FAILURE_RECOVERY_BASE_COLOR = "#55A868"


def sim_success_color(color: str) -> str:
    """Lighten the base color by mixing in 20% white."""
    return to_hex([channel * 0.8 + 0.2 for channel in to_rgb(color)])


def real_success_color(color: str) -> str:
    """Preserve hue, increase HSV saturation 20%, and reduce brightness 30%."""
    hue, saturation, brightness = colorsys.rgb_to_hsv(*to_rgb(color))
    return to_hex(colorsys.hsv_to_rgb(
        hue, min(1.0, saturation * 1.2), brightness * 0.7,
    ))


DENSE_SAMPLING_COLOR = sim_success_color(DENSE_SAMPLING_BASE_COLOR)
FAILURE_RECOVERY_COLOR = sim_success_color(FAILURE_RECOVERY_BASE_COLOR)
REAL_DENSE_SAMPLING_COLOR = real_success_color(DENSE_SAMPLING_BASE_COLOR)
REAL_FAILURE_RECOVERY_COLOR = real_success_color(FAILURE_RECOVERY_BASE_COLOR)
SIM_DENSE_SAMPLING_VIOLIN_COLOR = DENSE_SAMPLING_COLOR
SIM_FAILURE_RECOVERY_VIOLIN_COLOR = FAILURE_RECOVERY_COLOR
REAL_DENSE_SAMPLING_VIOLIN_COLOR = REAL_DENSE_SAMPLING_COLOR
REAL_FAILURE_RECOVERY_VIOLIN_COLOR = REAL_FAILURE_RECOVERY_COLOR
EXPERIMENT_COLORS = {
    "dense sampling": DENSE_SAMPLING_COLOR,
    "0p02_time_3": FAILURE_RECOVERY_COLOR,
}
REAL_EXPERIMENT_COLORS = {
    "dense sampling": REAL_DENSE_SAMPLING_COLOR,
    "0p02_time_3": REAL_FAILURE_RECOVERY_COLOR,
}
SIM_VIOLIN_COLORS = {
    "dense sampling": SIM_DENSE_SAMPLING_VIOLIN_COLOR,
    "0p02_time_3": SIM_FAILURE_RECOVERY_VIOLIN_COLOR,
}
REAL_VIOLIN_COLORS = {
    "dense sampling": REAL_DENSE_SAMPLING_VIOLIN_COLOR,
    "0p02_time_3": REAL_FAILURE_RECOVERY_VIOLIN_COLOR,
}
VIOLIN_WIDTH = 300
TIME_SERIES_SPACING = 300
BACKGROUND_LINE_COLOR = "0.6"
BACKGROUND_LINE_ALPHA = 1.0
FIGURE_WIDTH = 5
FIGURE_HEIGHT = 4

# Manual line overlay. Each tuple is one polyline of generated point names.
# Naming examples:
# dense sampling, 2000, sim -> ds_2000_sim
# 0p02_time_3, 3000, sim -> 0p02_t_3_3000_sim
REAL_LINE_STYLE = "--"
REAL_LINE_WIDTH = 1.5
REAL_LINE_ALPHA = 0.85
LINE_SPECS = (
    (
        ("ds_2000_sim", "ds_10000_real"),
        REAL_DENSE_SAMPLING_COLOR,
    ),
    (
        ("ds_2000_sim", "0p02_t_3_10000_real"),
        REAL_FAILURE_RECOVERY_COLOR,
    ),
    (
        ("ds_10000_real", "ds_20000_real"),
        REAL_DENSE_SAMPLING_COLOR,
    ),
    (
        ("0p02_t_3_10000_real", "0p02_t_3_20000_real"),
        REAL_FAILURE_RECOVERY_COLOR,
    ),
)
# Automatic sim line segments matching these generated names are not drawn.
EXCLUDE_LINE_SPECS = (
    # ("0p02_t_3_11000_sim", "0p02_t_3_12000_sim"),
)

SOURCE_ORDER = ("sim", "real")
SOURCE_LINE_STYLES = {
    "sim": "-",
    "real": "--",
}
SOURCE_MARKERS = {
    "sim": "o",
    "real": "s",
}
SIM_SUCCESS_MARKER_SIZE = 150
SIM_SUCCESS_MARKER_COLOR = "#f2c94c"

SCRIPT_DIR = Path(__file__).resolve().parent
FONT_PATH = SCRIPT_DIR / "fonts" / "NimbusSans-Regular.otf"
font_manager.fontManager.addfont(str(FONT_PATH))
FONT_FAMILY = font_manager.FontProperties(fname=FONT_PATH).get_name()
matplotlib.rcParams.update({
    "font.family": FONT_FAMILY,
    "font.size": 9,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "figures" / "v4"
DEFAULT_SIM_CSV = SCRIPT_DIR / "success_rate_sim.csv"
DEFAULT_REAL_CSV = SCRIPT_DIR / "success_rate_real.csv"

V19_EXPERIMENTS = (
    ("0p02_time_2", "hang_mug_pos_0p02_time_2"),
    ("0p02_time_3", "hang_mug_pos_0p02_time_3"),
    ("0p02_time_6", "hang_mug_pos_0p02_time_6"),
    ("0p01_time_2", "hang_mug_pos_0p01_time_2"),
    ("0p03_time_2", "hang_mug_pos_0p03_time_2"),
    ("0p03_time_6", "hang_mug_pos_0p03_time_6"),
    ("0p04_time_2", "hang_mug_pos_0p04_time_2"),
)

SAME_THRESHOLD_DIFFERENT_TIME_EXPERIMENTS = tuple(
    label for label, _ in V19_EXPERIMENTS if label.startswith("0p02_time_")
)

FIGURE_SPECS = (
    (
        "ACT_hang_mug_same_threshold_different_time_violin.pdf",
        "ACT hang_mug: same threshold, different time",
        SAME_THRESHOLD_DIFFERENT_TIME_EXPERIMENTS,
    ),
)


@dataclass(frozen=True)
class PosteriorPoint:
    policy: str
    experiment: str
    source: str
    dataset_step: int
    success_count: int
    sample_size: int
    success_rate: float
    alpha: float
    beta: float
    lower_95: float
    upper_95: float


@dataclass(frozen=True)
class PlottedPoint:
    x: float
    success_rate: float
    dataset_step: int


@dataclass(frozen=True)
class PlottedSeries:
    source: str
    experiment: str
    dataset_steps: np.ndarray
    markers: PathCollection
    intervals: LineCollection
    violins: tuple[PolyCollection, ...]
    stars: PathCollection | None
    star_steps: np.ndarray


@dataclass(frozen=True)
class PlottedLine:
    source: str
    dataset_steps: np.ndarray
    artist: Line2D


@dataclass(frozen=True)
class FigureStyle:
    width_pt: float = FIGURE_WIDTH * 72
    height_pt: float = FIGURE_HEIGHT * 72
    axis_label_size: float = 11
    tick_label_size: float = 8
    direct_label_size: float = 11
    layout_pad: float = 1.08
    geometry_scale: float = 1.0


@dataclass(frozen=True)
class PlotScene:
    figure: plt.Figure
    axes: plt.Axes
    series: tuple[PlottedSeries, ...]
    lines: tuple[PlottedLine, ...]
    sim_legend: Legend
    real_legend: Legend
    axis_arrows: tuple[Line2D, Line2D]
    style: FigureStyle


def has_value(row: dict[str, str], key: str) -> bool:
    return row.get(key) not in (None, "")


def point_from_row(row: dict[str, str], source: str) -> PosteriorPoint:
    success_rate = float(row["success_rate"])

    if has_value(row, "success_count") and has_value(row, "sample_size"):
        success_count = int(row["success_count"])
        sample_size = int(row["sample_size"])
    else:
        sample_size = int(
            row.get("sample_size") or DEFAULT_SAMPLE_SIZE_BY_SOURCE[source]
        )
        success_count = round(success_rate * sample_size)

    failure_count = sample_size - success_count
    alpha = (
        float(row["beta_alpha"])
        if has_value(row, "beta_alpha")
        else PRIOR_ALPHA + success_count
    )
    beta = (
        float(row["beta_beta"])
        if has_value(row, "beta_beta")
        else PRIOR_BETA + failure_count
    )
    lower_95 = (
        float(row["lower_95"])
        if has_value(row, "lower_95")
        else beta_dist.ppf(LOWER_Q, alpha, beta)
    )
    upper_95 = (
        float(row["upper_95"])
        if has_value(row, "upper_95")
        else beta_dist.ppf(UPPER_Q, alpha, beta)
    )

    return PosteriorPoint(
        policy=row["policy"],
        experiment=row["experiment"],
        source=source,
        dataset_step=int(row["dataset_step"]),
        success_count=success_count,
        sample_size=sample_size,
        success_rate=success_rate,
        alpha=alpha,
        beta=beta,
        lower_95=lower_95,
        upper_95=upper_95,
    )


def point_sort_key(point: PosteriorPoint) -> tuple[str, int, int]:
    return (point.experiment, point.dataset_step, SOURCE_ORDER.index(point.source))


def experiment_name_token(experiment: str) -> str:
    if experiment == "dense sampling":
        return "ds"
    return experiment.replace("_time_", "_t_")


def base_point_name(point: PosteriorPoint) -> str:
    return f"{experiment_name_token(point.experiment)}_{point.dataset_step}"


def point_name(point: PosteriorPoint) -> str:
    return f"{base_point_name(point)}_{point.source}"


def load_points_csv(input_csv: Path, source: str) -> list[PosteriorPoint]:
    points = []
    with input_csv.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            points.append(point_from_row(row, source))
    return points


def load_points(sim_csv: Path, real_csv: Path) -> list[PosteriorPoint]:
    points = [
        *load_points_csv(sim_csv, "sim"),
        *load_points_csv(real_csv, "real"),
    ]
    return sorted(points, key=point_sort_key)


def points_by_experiment(points: list[PosteriorPoint]) -> dict[str, list[PosteriorPoint]]:
    grouped = {}
    for point in points:
        grouped.setdefault(point.experiment, []).append(point)
    for series in grouped.values():
        series.sort(key=point_sort_key)
    return grouped


def points_by_source(points: list[PosteriorPoint]) -> dict[str, list[PosteriorPoint]]:
    grouped = {}
    for point in points:
        grouped.setdefault(point.source, []).append(point)
    for series in grouped.values():
        series.sort(key=lambda point: point.dataset_step)
    return grouped


def posterior_samples(point: PosteriorPoint, sample_count: int) -> np.ndarray:
    quantiles = np.linspace(0.001, 0.999, sample_count)
    return beta_dist.ppf(quantiles, point.alpha, point.beta)


def excluded_line_segments(
    point_registry: dict[str, PlottedPoint],
) -> set[tuple[str, str]]:
    segments = set()
    for line_spec in EXCLUDE_LINE_SPECS:
        for name in line_spec:
            point_registry[name]
        segments.update(zip(line_spec, line_spec[1:]))
    return segments


def draw_line_specs(
    ax: plt.Axes,
    point_registry: dict[str, PlottedPoint],
    geometry_scale: float = 1.0,
) -> list[PlottedLine]:
    lines = []
    for line_spec, line_color in LINE_SPECS:
        line_points = [point_registry[name] for name in line_spec]
        (artist,) = ax.plot(
            [point.x for point in line_points],
            [point.success_rate for point in line_points],
            color=line_color,
            linestyle=REAL_LINE_STYLE,
            linewidth=REAL_LINE_WIDTH * geometry_scale,
            alpha=REAL_LINE_ALPHA,
            zorder=4,
        )
        lines.append(PlottedLine(
            source="real",
            dataset_steps=np.array([point.dataset_step for point in line_points]),
            artist=artist,
        ))
    return lines


def draw_auto_line_specs(
    ax: plt.Axes,
    point_registry: dict[str, PlottedPoint],
    auto_line_specs: list[tuple[tuple[str, ...], str, str]],
    geometry_scale: float = 1.0,
) -> list[PlottedLine]:
    lines = []
    excluded_segments = excluded_line_segments(point_registry)
    for line_spec, color, linestyle in auto_line_specs:
        for start_name, end_name in zip(line_spec, line_spec[1:]):
            if (start_name, end_name) in excluded_segments:
                continue
            start_point = point_registry[start_name]
            end_point = point_registry[end_name]
            (artist,) = ax.plot(
                [start_point.x, end_point.x],
                [start_point.success_rate, end_point.success_rate],
                color=color,
                linestyle=linestyle,
                linewidth=2.0 * geometry_scale,
                alpha=0.95,
                zorder=2,
            )
            lines.append(PlottedLine(
                source="sim",
                dataset_steps=np.array([
                    start_point.dataset_step, end_point.dataset_step,
                ]),
                artist=artist,
            ))
    return lines


def output_formats(output_format: str) -> tuple[str, ...]:
    if output_format == "both":
        return ("pdf", "png")
    return (output_format,)


def x_axis_step_positions(
    points: list[PosteriorPoint],
    experiments: tuple[str, ...],
) -> dict[int, float]:
    plotted_experiments = {"dense sampling", *experiments}
    available_steps = {
        point.dataset_step
        for point in points
        if point.experiment in plotted_experiments
    }
    x_axis_count = int((X_AXIS_END - X_AXIS_START) / X_AXIS_INTERVAL) + 1
    raw_positions = X_AXIS_START + np.arange(x_axis_count) * X_AXIS_INTERVAL
    return {
        int(position): float(position)
        for position in raw_positions
        if int(position) in available_steps
        and int(position) not in X_AXIS_EXCLUDED_DATASET_STEPS
    }


def draw_success_legends(ax: plt.Axes) -> tuple[Legend, Legend]:
    """Reserve two aligned blocks so showing Real never moves the Sim block."""
    legends = []
    for source, marker, colors in (
        ("Sim", "o", (FAILURE_RECOVERY_COLOR, DENSE_SAMPLING_COLOR)),
        ("Real", "s", (REAL_FAILURE_RECOVERY_COLOR, REAL_DENSE_SAMPLING_COLOR)),
    ):
        labels = [f"UniKey ({source})", f"dense sampling ({source})"]
        handles = [
            Line2D(
                [], [], linestyle="None", marker=marker, markersize=6,
                markerfacecolor=color, markeredgecolor="white", markeredgewidth=0.8,
            )
            for color in colors
        ]
        legend = Legend(
            ax, handles, labels,
            loc="lower left", bbox_to_anchor=(0.98, 0.015), borderaxespad=0,
            fontsize=9, handlelength=0.8, handletextpad=0.5, labelspacing=0.55,
            borderpad=0.45, facecolor="white", edgecolor="none", framealpha=0.95,
        )
        legend.set_in_layout(False)
        ax.add_artist(legend)
        legends.append(legend)

    # Offset in physical points, independent of export DPI and visibility.
    renderer = ax.figure.canvas.get_renderer()
    pixels_to_points = 72 / ax.figure.dpi
    width = max(item.get_window_extent(renderer).width for item in legends) * pixels_to_points
    sim_height = legends[0].get_window_extent(renderer).height * pixels_to_points
    for legend, y_offset in zip(legends, (0.0, sim_height + 2.0)):
        transform = offset_copy(
            ax.transAxes, fig=ax.figure, x=-width, y=y_offset, units="points",
        )
        legend.set_bbox_to_anchor((0.98, 0.015), transform=transform)
    return legends[0], legends[1]


def set_dataset_axis_ticks(ax: plt.Axes, first_step: float, last_step: float) -> None:
    ticks = {first_step, last_step}
    ticks.update(np.arange(np.ceil(first_step / 5000) * 5000, last_step + 1, 5000))
    ax.set_xticks(sorted(ticks))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))


def build_violin_scene(
    points: list[PosteriorPoint],
    title: str,
    experiments: tuple[str, ...],
    posterior_sample_count: int,
    *,
    include_real: bool = True,
    style: FigureStyle = FigureStyle(),
) -> PlotScene:
    """Build the static figure and retain artist groups for progressive reveals."""
    if not include_real:
        points = [point for point in points if point.source == "sim"]
    grouped = points_by_experiment(points)
    dense_points = grouped.get("dense sampling", [])
    dense_points_by_source = points_by_source(dense_points)
    dense_anchor_by_source = {
        source: series[0]
        for source, series in dense_points_by_source.items()
        if series[0].dataset_step not in X_AXIS_EXCLUDED_DATASET_STEPS
    }

    series_order = ("dense sampling",) + experiments
    active_count = max(len(experiments), 1)
    x_by_step = x_axis_step_positions(points, experiments)
    x_axis_interval = X_AXIS_INTERVAL
    real_point_x_offset = x_axis_interval * REAL_POINT_X_OFFSET_INTERVALS

    fig, ax = plt.subplots(figsize=(style.width_pt / 72, style.height_pt / 72))
    geometry_scale = style.geometry_scale
    point_registry: dict[str, PlottedPoint] = {}
    auto_line_specs: list[tuple[tuple[str, ...], str, str]] = []
    plotted_series: list[PlottedSeries] = []
    plotted_positions = []

    for index, experiment in enumerate(series_order):
        raw_series = list(grouped.get(experiment, []))
        source_series_by_name = points_by_source(raw_series)
        if not source_series_by_name:
            print(f"Warning: no points found for {experiment}")
            continue

        if experiment != "dense sampling":
            active_index = index - 1
            offset = (active_index - (active_count - 1) / 2) * TIME_SERIES_SPACING
        else:
            offset = 0.0

        color = EXPERIMENT_COLORS[experiment]

        for source in SOURCE_ORDER:
            raw_source_series = source_series_by_name.get(source)
            if raw_source_series is None:
                continue

            series = [
                point
                for point in raw_source_series
                if point.dataset_step in x_by_step
            ]
            if not series:
                print(f"Warning: no visible points found for {experiment} {source}")
                continue
            source_offset = real_point_x_offset if source == "real" else 0.0
            positions = [
                x_by_step[point.dataset_step] + offset + source_offset
                for point in series
            ]
            samples = [
                posterior_samples(point, posterior_sample_count)
                for point in series
            ]

            violin = ax.violinplot(
                samples,
                positions=positions,
                widths=VIOLIN_WIDTH,
                showmeans=False,
                showmedians=False,
                showextrema=False,
            )
            violin_color = (
                REAL_VIOLIN_COLORS[experiment]
                if source == "real"
                else SIM_VIOLIN_COLORS[experiment]
            )
            for body in violin["bodies"]:
                body.set_facecolor(violin_color)
                body.set_edgecolor(violin_color)
                body.set_alpha(0.18 if experiment == "dense sampling" else 0.25)
                body.set_linewidth(0.7 * geometry_scale)

            rates = [point.success_rate for point in series]
            lows = [point.lower_95 for point in series]
            highs = [point.upper_95 for point in series]
            marker_color = (
                REAL_EXPERIMENT_COLORS[experiment]
                if source == "real"
                else color
            )

            markers = ax.scatter(
                positions,
                rates,
                s=30 * geometry_scale**2,
                marker=SOURCE_MARKERS[source],
                color=marker_color,
                edgecolor="white",
                linewidth=0.8 * geometry_scale,
                zorder=3,
            )
            stars = None
            star_steps = np.array([], dtype=int)
            if source == "sim":
                star_positions = [
                    position
                    for point, position in zip(series, positions)
                    if point.success_rate >= 1.0
                ]
                star_rates = [
                    point.success_rate
                    for point in series
                    if point.success_rate >= 1.0
                ]
                star_steps = np.array([
                    point.dataset_step for point in series
                    if point.success_rate >= 1.0
                ], dtype=int)
                stars = ax.scatter(
                    star_positions,
                    star_rates,
                    s=SIM_SUCCESS_MARKER_SIZE * geometry_scale**2,
                    marker="*",
                    color=SIM_SUCCESS_MARKER_COLOR,
                    edgecolor=color,
                    linewidth=0.8 * geometry_scale,
                    zorder=5,
                )
            intervals = ax.vlines(
                positions, lows, highs, color=marker_color,
                linewidth=geometry_scale, alpha=0.55,
            )
            plotted_series.append(PlottedSeries(
                source=source,
                experiment=experiment,
                dataset_steps=np.array([point.dataset_step for point in series]),
                markers=markers,
                intervals=intervals,
                violins=tuple(violin["bodies"]),
                stars=stars,
                star_steps=star_steps,
            ))
            for point, position in zip(series, positions):
                point_registry[point_name(point)] = PlottedPoint(
                    x=position,
                    success_rate=point.success_rate,
                    dataset_step=point.dataset_step,
                )
            if source == "sim":
                if experiment != "dense sampling" and source in dense_anchor_by_source:
                    dense_anchor = dense_anchor_by_source[source]
                    line_spec = (
                        point_name(dense_anchor),
                        *(point_name(point) for point in series),
                    )
                else:
                    line_spec = tuple(point_name(point) for point in series)
                auto_line_specs.append(
                    (line_spec, color, SOURCE_LINE_STYLES[source])
                )
            plotted_positions.extend(positions)

    lines = draw_auto_line_specs(ax, point_registry, auto_line_specs, geometry_scale)
    if include_real:
        lines.extend(draw_line_specs(ax, point_registry, geometry_scale))

    x_axis_padding = x_axis_interval * X_AXIS_EDGE_PADDING_INTERVALS
    ax.set_xlim(
        min(plotted_positions) - x_axis_padding,
        max(plotted_positions) + x_axis_padding,
    )
    ax.margins(x=0.0)
    visible_steps = [point.dataset_step for point in point_registry.values()]
    set_dataset_axis_ticks(ax, min(visible_steps), max(visible_steps))
    ax.set_xlabel(
        "Dataset Steps", fontsize=style.axis_label_size, labelpad=7 * geometry_scale,
    )
    ax.set_ylabel(
        "Success Rate", fontsize=style.axis_label_size, labelpad=7 * geometry_scale,
    )
    ax.tick_params(
        axis="both", labelsize=style.tick_label_size, colors="0.25",
        width=0.8 * geometry_scale, length=3 * geometry_scale,
        pad=3.5 * geometry_scale,
    )

    ax.set_ylim(0.0, 1.05)
    ax.set_yticks(np.linspace(0.0, 1.0, 6))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    ax.grid(
        True,
        axis="y",
        linestyle="--",
        linewidth=matplotlib.rcParams["grid.linewidth"] * geometry_scale,
        color=BACKGROUND_LINE_COLOR,
        alpha=BACKGROUND_LINE_ALPHA,
    )
    for name, spine in ax.spines.items():
        spine.set_visible(name in ("left", "bottom"))
        spine.set_color("0.25")
        spine.set_linewidth(0.8 * geometry_scale)

    axis_arrows = []
    for x, y, marker in ((1.0, 0.0, ">"), (0.0, 1.0, "^")):
        (arrow,) = ax.plot(
            [x], [y], transform=ax.transAxes, linestyle="None",
            marker=marker, markersize=6 * geometry_scale, markeredgewidth=0, color="0.25",
            clip_on=False, zorder=6,
        )
        # Account for the arrow tips when fitting a figure with no outer padding.
        arrow.set_in_layout(style.layout_pad == 0)
        axis_arrows.append(arrow)

    fig.tight_layout(pad=style.layout_pad)
    sim_legend, real_legend = draw_success_legends(ax)
    real_legend.set_visible(any(series.source == "real" for series in plotted_series))
    return PlotScene(
        fig, ax, tuple(plotted_series), tuple(lines), sim_legend, real_legend,
        (axis_arrows[0], axis_arrows[1]), style,
    )


def plot_violin(
    points: list[PosteriorPoint],
    output_path: Path,
    title: str,
    experiments: tuple[str, ...],
    posterior_sample_count: int,
) -> None:
    scene = build_violin_scene(points, title, experiments, posterior_sample_count)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene.figure.savefig(output_path, dpi=300)
    plt.close(scene.figure)


def plot_requested_figures(
    points: list[PosteriorPoint],
    output_dir: Path,
    posterior_sample_count: int,
    requested_output_formats: tuple[str, ...],
) -> list[Path]:
    output_paths = []
    for filename, title, experiments in FIGURE_SPECS:
        for output_format in requested_output_formats:
            output_path = (output_dir / filename).with_suffix(f".{output_format}")
            plot_violin(points, output_path, title, experiments, posterior_sample_count)
            output_paths.append(output_path)
    return output_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Draw beta-posterior violin plots for hang_mug ACT success rates."
    )
    parser.add_argument("--sim-csv", type=Path, default=DEFAULT_SIM_CSV)
    parser.add_argument("--real-csv", type=Path, default=DEFAULT_REAL_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--output-format",
        choices=("pdf", "png", "both"),
        default="both",
        help="Write a PDF, PNG, or both output files.",
    )
    parser.add_argument("--posterior-samples", type=int, default=800)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    points = load_points(args.sim_csv, args.real_csv)

    plot_paths = plot_requested_figures(
        points,
        args.output_dir,
        args.posterior_samples,
        output_formats(args.output_format),
    )

    for plot_path in plot_paths:
        print(f"Wrote plot to {plot_path}")


if __name__ == "__main__":
    main()
