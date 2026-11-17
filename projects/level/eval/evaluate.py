#!/usr/bin/env python3
"""Evaluate Level Measurement Series.

Reads the serial output of the sensor matrix. 
Fits the plane z = a*x + b*y + c to every single reading of the four
sensors (least squares) and converts the slope of the tilted axis into
an angle.
Prints bias (target - mean), standard deviation and RMSE of the angle per
target angle, together with the angle of the other axis (should stay 0),
the plane residual, the distance c and the standard deviation predicted
from the noise of the single sensors.
Fits a straight line measured = k * target + offset over all steps.
Saves the values as CSV.
Plots the bias with a +-2 sigma band and the angle of the other axis
against the target angle, and the measured angle against the target
angle with the fitted line.

Usage:
    python3 evaluate_level.py level_x.log -a x -c werte_x.csv
    python3 evaluate_level.py level_x.log -a x -c werte_x.csv -o out_x.png
    python3 evaluate_level.py level_y.log -a y -c werte_y.csv --zero-offset

The axis is the direction in which the plane is tilted:
    -a x: the plane is tilted along x (rotation about the y axis), slope a
    -a y: the plane is tilted along y (rotation about the x axis), slope b

With -o out.png the measured-vs-target plot is saved as out_fit.png in the
same directory.

With --zero-offset the readings of the 0 degree step are used to align the
four sensors: every sensor gets the offset that moves its mean at 0 degrees
onto the mean of all four sensors. This removes different sensor offsets,
but also any real tilt of the target at 0 degrees.
"""

import argparse
import csv
import math
import os
import re
import statistics
import sys

import matplotlib.pyplot as plt
import numpy as np

TARGET_RE = re.compile(r"TARGET ANGLE:\s*(-?\d+(?:\.\d+)?)")
MEASUREMENT_RE = re.compile(
    r"accuracy:\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)")

POSITIONS = [(30.0, 20.25), (-30.0, 20.25), (-30.0, -20.25), (30.0, -20.25)]

# Sign that turns the arctangent of the slope into the angle of the rig.
# Taken from the measurements: tilting the target by a positive angle
# along x makes a negative, along y it makes b positive.
SIGN = {"x": -1.0, "y": 1.0}

# Reference palette (light mode), see the dataviz skill
COLOR_TARGET = "#52514e"
COLOR_BIAS = "#2a78d6"
COLOR_OTHER = "#e34948"

DESIGN = np.array([[x, y, 1.0] for x, y in POSITIONS])
# Least squares solution p = (A^T A)^-1 A^T d for every reading
SOLVER = np.linalg.inv(DESIGN.T @ DESIGN) @ DESIGN.T


def parse(lines):
    """Return {target_deg: [(d1, d2, d3, d4), ...]} in the order of the log."""
    series = {}
    target = None
    for line in lines:
        m = TARGET_RE.search(line)
        if m:
            target = float(m.group(1))
            # A repeated target (new series) starts over
            series[target] = []
            continue
        m = MEASUREMENT_RE.search(line)
        if m and target is not None:
            series[target].append(tuple(int(v) for v in m.groups()))
    return {t: v for t, v in series.items() if v}


def zero_offsets(series):
    """Return the offset per sensor that aligns the sensors at 0 degrees."""
    if 0.0 not in series:
        sys.exit("--zero-offset needs a series at TARGET ANGLE: 0")
    means = np.array(series[0.0], dtype=float).mean(axis=0)
    return means.mean() - means


def angle(slope, axis):
    """Return the angle in degrees of one slope."""
    return SIGN[axis] * math.degrees(math.atan(slope))


def fit(readings, offsets):
    """Return the plane (a, b, c) and the residual RMS for every reading."""
    d = np.array(readings, dtype=float) + offsets
    planes = d @ SOLVER.T
    residuals = d - planes @ DESIGN.T
    rms = np.sqrt((residuals ** 2).mean(axis=1))
    return d, planes, rms


def predicted_std(d, axis):
    """Return the std of the angle predicted from the single sensor noise.

    The noise of every sensor is propagated through the least squares
    solution, then through the arctangent at the mean slope.
    """
    sensor_var = d.var(axis=0, ddof=1)
    row = SOLVER[0 if axis == "x" else 1]
    slope_std = math.sqrt(float((row ** 2) @ sensor_var))
    slope = float(row @ d.mean(axis=0))
    return math.degrees(slope_std / (1 + slope * slope))


def evaluate(target, readings, axis, offsets):
    """Return the values of one target angle; error = target - measured."""
    other = "y" if axis == "x" else "x"
    d, planes, rms = fit(readings, offsets)
    slopes = planes[:, 0 if axis == "x" else 1]
    other_slopes = planes[:, 1 if axis == "x" else 0]

    measured = [angle(s, axis) for s in slopes]
    errors = [target - m for m in measured]
    return {
        "target": target,
        "n": len(readings),
        "mean": statistics.mean(measured),
        "bias": statistics.mean(errors),
        "std": statistics.stdev(errors) if len(errors) > 1 else 0.0,
        "rmse": math.sqrt(statistics.mean(e * e for e in errors)),
        "std_pred": predicted_std(d, axis) if len(readings) > 1 else 0.0,
        "other": statistics.mean(angle(s, other) for s in other_slopes),
        "residual": float(rms.mean()),
        "c": float(planes[:, 2].mean()),
    }


def line_fit(results):
    """Return k, offset and RMS of measured = k * target + offset."""
    x = np.array([r["target"] for r in results])
    y = np.array([r["mean"] for r in results])
    k, offset = np.polyfit(x, y, 1)
    rms = float(np.sqrt(np.mean((y - (k * x + offset)) ** 2)))
    return float(k), float(offset), rms


def print_table(results, axis):
    other = "y" if axis == "x" else "x"
    print(f"{'Target':>7} {'n':>3} {'Mean':>7} {'Bias':>6} {'Std':>5} "
          f"{'Pred':>5} {'RMSE':>5} {'95% range':>14} "
          f"{f'Angle {other}':>8} {'Resid':>6} {'c':>6}")
    for r in results:
        lo, hi = r["bias"] - 2 * r["std"], r["bias"] + 2 * r["std"]
        print(f"{r['target']:>+7.0f} {r['n']:>3} {r['mean']:>+7.1f} "
              f"{r['bias']:>+6.1f} {r['std']:>5.2f} {r['std_pred']:>5.2f} "
              f"{r['rmse']:>5.1f} {f'{lo:+.1f} .. {hi:+.1f}':>14} "
              f"{r['other']:>+8.1f} {r['residual']:>6.2f} {r['c']:>6.1f}")
    print("Angles in degrees, residual and c in mm. "
          "Pred = std predicted from the single sensor noise.")


def write_csv(results, path, axis):
    other = "y" if axis == "x" else "x"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["target_deg", "n", "mean_deg", "bias_deg",
                         "std_deg", "std_predicted_deg", "rmse_deg",
                         "range95_low_deg", "range95_high_deg",
                         f"angle_{other}_deg", "residual_rms_mm", "c_mm"])
        for r in results:
            writer.writerow([f"{r['target']:g}", r["n"],
                             f"{r['mean']:.2f}", f"{r['bias']:.2f}",
                             f"{r['std']:.2f}", f"{r['std_pred']:.2f}",
                             f"{r['rmse']:.2f}",
                             f"{r['bias'] - 2 * r['std']:.2f}",
                             f"{r['bias'] + 2 * r['std']:.2f}",
                             f"{r['other']:.2f}", f"{r['residual']:.2f}",
                             f"{r['c']:.1f}"])
    print(f"Values saved to {path}")


def style(ax):
    ax.grid(color="#e4e3df", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False)


def show_or_save(fig, output):
    fig.tight_layout()
    if output:
        fig.savefig(output, dpi=150)
        print(f"Plot saved to {output}")
    else:
        plt.show()


def plot(results, output, axis):
    other = "y" if axis == "x" else "x"
    targets = [r["target"] for r in results]
    bias = [r["bias"] for r in results]
    lower = [r["bias"] - 2 * r["std"] for r in results]
    upper = [r["bias"] + 2 * r["std"] for r in results]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axhline(0, color=COLOR_TARGET, linewidth=2, linestyle="--",
               label="Target")
    ax.fill_between(targets, lower, upper, color=COLOR_BIAS, alpha=0.18,
                    linewidth=0, label="Bias ± 2σ (~95 %)")
    ax.plot(targets, bias, color=COLOR_BIAS, linewidth=2, marker="o",
            markersize=4, label=f"Bias {axis}")
    ax.plot(targets, [r["other"] for r in results], color=COLOR_OTHER,
            linewidth=1.5, linestyle=":", marker="s", markersize=3,
            label=f"{other}")

    ax.set_title(f"Level Measurement")
    ax.set_xlabel("Target Angle [°]")
    ax.set_ylabel("Target - Measured [°]")
    ax.set_xticks(targets)
    style(ax)
    show_or_save(fig, output)


def plot_fit(results, output, axis, k, offset):
    targets = [r["target"] for r in results]
    span = [min(targets), max(targets)]

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(span, span, color=COLOR_TARGET, linewidth=2, linestyle="--",
            label="Ideal")
    ax.plot(span, [k * t + offset for t in span], color=COLOR_OTHER,
            linewidth=1.5, linestyle=":",
            label=rf"$\theta_{{\mathrm{{meas}}}} = {k:.3f} \cdot \theta_{{\mathrm{{target}}}} {offset:+.2f}^\circ$")
    ax.errorbar(targets, [r["mean"] for r in results],
                yerr=[2 * r["std"] for r in results], color=COLOR_BIAS,
                linewidth=0, elinewidth=1.5, capsize=3, marker="o",
                markersize=4, label="Bias ± 2σ (~95 %)")

    ax.set_title(f"Level Measurement - Regression line")
    ax.set_xlabel("Target [°]")
    ax.set_ylabel("Measured [°]")
    ax.set_xticks(targets)
    ax.set_yticks(targets)
    ax.set_aspect("equal")
    style(ax)
    show_or_save(fig, output)


def fit_output(output):
    """Return the path of the second plot (dir/out.png -> dir/out_fit.png)."""
    if not output:
        return None
    stem, ext = os.path.splitext(output)
    return f"{stem}_fit{ext or '.png'}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("log", nargs="?", help="log file (default: stdin)")
    parser.add_argument("-a", "--axis", choices=("x", "y"), required=True,
                        help="direction in which the plane is tilted")
    parser.add_argument("-o", "--output",
                        help="save the plots instead of showing them")
    parser.add_argument("-c", "--csv", required=True,
                        help="CSV file for the values")
    parser.add_argument("--zero-offset", action="store_true",
                        help="align the sensors with the 0 degree series")
    args = parser.parse_args()

    if args.log:
        with open(args.log, encoding="utf-8", errors="replace") as f:
            series = parse(f)
    else:
        series = parse(sys.stdin)

    if not series:
        sys.exit("No measurements found")

    offsets = np.zeros(4)
    if args.zero_offset:
        offsets = zero_offsets(series)
        print("Sensor offsets from 0° [mm]: " + ", ".join(
            f"S{i + 1} {o:+.1f}" for i, o in enumerate(offsets)))

    results = [evaluate(t, v, args.axis, offsets)
               for t, v in sorted(series.items())]
    k, offset, rms = line_fit(results)

    print_table(results, args.axis)
    print(f"Line fit: measured = {k:.4f} * target {offset:+.2f}°, "
          f"RMS deviation from the line {rms:.2f}°")
    write_csv(results, args.csv, args.axis)
    plot(results, args.output, args.axis)
    plot_fit(results, fit_output(args.output), args.axis, k, offset)


if __name__ == "__main__":
    main()