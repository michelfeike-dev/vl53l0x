#!/usr/bin/env python3
"""Evaluate Measurement Series.

Reads the serial output.
Prints bias (target - mean), standard deviation and RMSE per target distance.
Saves these values as CSV.
Plots the bias with a +-2 sigma band against the target and the
datasheet accuracy limit of the ranging mode (default mode +-4 %,
high accuracy mode +-3 % of the target distance).
Plots the field of view cone of the sensor with the spot diameter at
every target distance.

Usage:
    python3 evaluate.py messung.log -c werte.csv
    python3 evaluate.py messung.log -c werte.csv -o out.png
    python3 evaluate.py messung.log -c werte.csv -m high-accuracy
    python3 evaluate.py messung.log -c werte.csv --spec 4
    python3 evaluate.py messung.log -c werte.csv -o out.png --fov 25

With -o out.png the field of view plot is saved as fov.png in the same
directory. The name is fixed because the field of view only depends on the
sensor, so every run overwrites it.
"""

import argparse
import csv
import math
import os
import re
import statistics
import sys

import matplotlib.pyplot as plt

TARGET_RE = re.compile(r"TARGET DISTANCE:\s*(\d+)")
MEASUREMENT_RE = re.compile(r"MEASUREMENT\s+\d+:\s*(\d+)\s*\[mm\]")

# Reference palette (light mode), see the dataviz skill
COLOR_TARGET = "#52514e"
COLOR_BIAS = "#2a78d6"
COLOR_SPEC = "#e34948"

# Datasheet ranging accuracy per mode, white target up to 120 cm
MODES = {
    "default": ("Default Mode", 4.0),
    "high-accuracy": ("High Accuracy Mode", 3.0),
}


def parse(lines):
    """Return {target_mm: [measured_mm, ...]} in the order of the log."""
    series = {}
    target = None
    for line in lines:
        m = TARGET_RE.search(line)
        if m:
            target = int(m.group(1))
            # A repeated target (new series) starts over
            series[target] = []
            continue
        m = MEASUREMENT_RE.search(line)
        if m and target is not None:
            series[target].append(int(m.group(1)))
    return {t: v for t, v in series.items() if v}


def evaluate(target, values):
    """Return bias, std and RMSE of one series; error = target - measured."""
    errors = [target - v for v in values]
    bias = statistics.mean(errors)
    std = statistics.stdev(errors) if len(errors) > 1 else 0.0
    rmse = math.sqrt(statistics.mean(e * e for e in errors))
    return bias, std, rmse


def spec_limit(target, spec_percent):
    """Return the allowed error in mm for one target distance."""
    return target * spec_percent / 100



def field_limit(target, fov_deg):
    """Return the half width of the field of view in mm at one distance."""
    return math.tan(math.radians(fov_deg) / 2) * target


def in_spec(bias, std, limit):
    """True if the whole 95 % range lies within +-limit."""
    return -limit <= bias - 2 * std and bias + 2 * std <= limit


def print_table(series, spec_percent):
    spec_header = f"Spec \u00b1{spec_percent:g}%"
    print(f"{'Target':>7} {'n':>3} {'Mean':>8} {'Bias':>7} {'Std':>6} "
          f"{'RMSE':>6} {'95% range':>16} {spec_header:>10} {'OK':>3}")
    for target, values in series.items():
        bias, std, rmse = evaluate(target, values)
        lo, hi = bias - 2 * std, bias + 2 * std
        limit = spec_limit(target, spec_percent)
        ok = "yes" if in_spec(bias, std, limit) else "no"
        print(f"{target:>7} {len(values):>3} {statistics.mean(values):>8.1f} "
              f"{bias:>+7.1f} {std:>6.1f} {rmse:>6.1f} "
              f"{f'{lo:+.1f} .. {hi:+.1f}':>16} {f'\u00b1{limit:.1f}':>10} "
              f"{ok:>3}")


def write_csv(series, path, spec_percent):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["target_mm", "n", "mean_mm", "bias_mm", "std_mm",
                         "rmse_mm", "range95_low_mm", "range95_high_mm",
                         "spec_mm", "in_spec"])
        for target, values in series.items():
            bias, std, rmse = evaluate(target, values)
            limit = spec_limit(target, spec_percent)
            writer.writerow([target, len(values),
                             f"{statistics.mean(values):.1f}", f"{bias:.1f}",
                             f"{std:.1f}", f"{rmse:.1f}",
                             f"{bias - 2 * std:.1f}", f"{bias + 2 * std:.1f}",
                             f"{limit:.1f}",
                             int(in_spec(bias, std, limit))])
    print(f"Values saved to {path}")


def plot(series, output, spec_percent, mode_name):
    targets = list(series)
    results = [evaluate(t, v) for t, v in series.items()]
    bias = [r[0] for r in results]
    lower = [r[0] - 2 * r[1] for r in results]
    upper = [r[0] + 2 * r[1] for r in results]
    # The limit grows linearly with the distance, so it starts at the origin
    spec_x = [0] + targets
    spec = [spec_limit(t, spec_percent) for t in spec_x]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axhline(0, color=COLOR_TARGET, linewidth=2, linestyle="--",
               label="Target")
    ax.plot(spec_x, spec, color=COLOR_SPEC, linewidth=1.5, linestyle=":",
            label=f"Datasheet \u00b1{spec_percent:g} %")
    ax.plot(spec_x, [-s for s in spec], color=COLOR_SPEC, linewidth=1.5,
            linestyle=":")
    ax.fill_between(targets, lower, upper, color=COLOR_BIAS, alpha=0.18,
                    linewidth=0, label="Bias \u00b1 2\u03c3 (~95 %)")
    ax.plot(targets, bias, color=COLOR_BIAS, linewidth=2, marker="o",
            markersize=4, label="Bias")

    ax.set_title(f"VL53L0X Accuracy ({mode_name})")
    ax.set_xlabel("Target Distance [mm]")
    ax.set_ylabel("Target - Measured [mm]")
    ax.set_xticks(spec_x)
    ax.set_xlim(left=0)
    ax.grid(color="#e4e3df", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()

    if output:
        fig.savefig(output, dpi=150)
        print(f"Plot saved to {output}")
    else:
        plt.show()



def plot_field_of_view(series, output, fov_deg):
    targets = list(series)
    # The cone starts at the sensor, so it starts at the origin
    cone_x = [0] + targets
    half = [field_limit(t, fov_deg) for t in cone_x]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(cone_x, [-h for h in half], half, color=COLOR_BIAS,
                    alpha=0.12, linewidth=0)
    ax.plot(cone_x, half, color=COLOR_SPEC, linewidth=1.5, linestyle=":",
            label=f"Datasheet FoV {fov_deg:g}\u00b0 (\u00b1{fov_deg / 2:g}\u00b0)")
    ax.plot(cone_x, [-h for h in half], color=COLOR_SPEC, linewidth=1.5,
            linestyle=":")
    ax.axhline(0, color=COLOR_TARGET, linewidth=1, linestyle="--",
               label="Optical axis")
    # Spot on the target at every measured distance
    ax.vlines(targets, [-h for h in half[1:]], half[1:], color=COLOR_BIAS,
              linewidth=2, label="Spot on target")
    for t, h in zip(targets, half[1:]):
        ax.annotate(f"\u00f8{2 * h:.0f}", (t, h), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=8, color=COLOR_TARGET)

    ax.set_title("VL53L0X Field of View")
    ax.set_xlabel("Distance [mm]")
    ax.set_ylabel("Lateral Offset [mm]")
    ax.set_xticks(cone_x)
    ax.set_xlim(left=0)
    # Same scale on both axes, so the cone shows the true angle
    ax.set_aspect("equal")
    ax.grid(color="#e4e3df", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()

    if output:
        fig.savefig(output, dpi=150)
        print(f"Plot saved to {output}")
    else:
        plt.show()


def fov_output(output):
    """Return the FoV plot path next to the accuracy plot (dir/out.png -> dir/fov.png).

    The field of view only depends on the sensor, so every run writes the
    same file and overwrites the previous one.
    """
    if not output:
        return None
    ext = os.path.splitext(output)[1] or ".png"
    return os.path.join(os.path.dirname(output), f"fov{ext}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("log", nargs="?", help="log file (default: stdin)")
    parser.add_argument("-o", "--output", help="save the plot instead of showing it")
    parser.add_argument("-c", "--csv", required=True,
                        help="CSV file for the values")
    parser.add_argument("-m", "--mode", choices=MODES, default="default",
                        help="ranging mode of the measurement "
                             "(default: default)")
    parser.add_argument("--spec", type=float,
                        help="override the datasheet accuracy of the mode "
                             "in percent of the target")
    parser.add_argument("--fov", type=float, default=25.0,
                        help="full field of view of the sensor in degrees "
                             "(default: 25)")
    args = parser.parse_args()

    mode_name, spec_percent = MODES[args.mode]
    if args.spec is not None:
        spec_percent = args.spec

    if args.log:
        with open(args.log, encoding="utf-8", errors="replace") as f:
            series = parse(f)
    else:
        series = parse(sys.stdin)

    if not series:
        sys.exit("No measurements found")

    print(f"{mode_name}: datasheet accuracy \u00b1{spec_percent:g} %")
    print_table(series, spec_percent)
    write_csv(series, args.csv, spec_percent)
    plot(series, args.output, spec_percent, mode_name)
    plot_field_of_view(series, fov_output(args.output), args.fov)


if __name__ == "__main__":
    main()
