#!/usr/bin/env python3
"""Apply a median filter to a measurement log and evaluate the result.

Reads the serial output of the accuracy or filter project and runs a
median filter with window N over the readings of each target distance.
The filter is reset at every "TARGET DISTANCE" line, like the firmware.
Until the window is full, the median is taken over the readings so far.

Prints bias, standard deviation and RMSE per target distance of the
filtered readings. Plots the bias with a +-2 sigma band against the
datasheet accuracy limit, like evaluate.py.

Saves the values as CSV, in the same format as evaluate.py, so they can
be compared with the CSV of the raw readings. Optionally saves the
filtered log (same format as the input).

Usage:
    python3 filter.py data/s1.log -n 5 -c data/s1_med5.csv
    python3 filter.py data/s1.log -n 5 -c data/s1_med5.csv -p data/s1_med5.png
    python3 filter.py data/s1.log -n 5 -c data/s1_med5.csv -m high-accuracy
    python3 filter.py data/s1.log -n 5 -c data/s1_med5.csv -o data/s1_med5.log
"""

import argparse
import re
import sys
from collections import deque

import matplotlib.pyplot as plt

# Reuse parsing and statistics of evaluate.py in the same directory
from evaluate import (COLOR_SPEC, COLOR_TARGET, MODES,  # noqa: E402
                      evaluate, parse, print_table, spec_limit, write_csv)

TARGET_RE = re.compile(r"TARGET DISTANCE:\s*\d+")
MEASUREMENT_RE = re.compile(r"MEASUREMENT\s+\d+:\s*(\d+)\s*\[mm\]")

# Second categorical color, see the dataviz skill
COLOR_FILTERED = "#1baf7a"


class MedianFilter:
    """Sliding median over the last n values."""

    def __init__(self, n):
        if n <= 0 or n % 2 == 0:
            raise ValueError("window must be odd and > 0")
        self.buf = deque(maxlen=n)

    def update(self, x):
        self.buf.append(x)
        values = sorted(self.buf)
        # Same element as nth_element(count / 2) in median.hpp
        return values[len(values) // 2]


def filter_log(lines, n):
    """Return the log lines with every measurement replaced by its median."""
    out = []
    filt = MedianFilter(n)
    for line in lines:
        if TARGET_RE.search(line):
            filt = MedianFilter(n)
        else:
            m = MEASUREMENT_RE.search(line)
            if m:
                value = filt.update(int(m.group(1)))
                line = line[:m.start(1)] + str(value) + line[m.end(1):]
        out.append(line)
    return out


def window(text):
    n = int(text)
    if n <= 0 or n % 2 == 0:
        raise argparse.ArgumentTypeError("window must be odd and > 0")
    return n


def stats(series):
    """Return targets, bias and std of every target distance."""
    targets = list(series)
    results = [evaluate(t, v) for t, v in series.items()]
    return targets, [r[0] for r in results], [r[1] for r in results]


def plot_bias(ax, series, color, marker):
    targets, bias, std = stats(series)
    lower = [b - 2 * s for b, s in zip(bias, std)]
    upper = [b + 2 * s for b, s in zip(bias, std)]
    ax.fill_between(targets, lower, upper, color=color, alpha=0.18,
                    linewidth=0, label=f"± 2σ (~95 %)")
    ax.plot(targets, bias, color=color, linewidth=2, marker=marker,
            markersize=5, label=f"Bias")


def plot(filtered, n, output, spec_percent, mode_name):
    spec_x = [0] + list(filtered)
    spec = [spec_limit(t, spec_percent) for t in spec_x]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axhline(0, color=COLOR_TARGET, linewidth=2, linestyle="--",
               label="Target")
    ax.plot(spec_x, spec, color=COLOR_SPEC, linewidth=1.5, linestyle=":",
            label=f"Datasheet ±{spec_percent:g} %")
    ax.plot(spec_x, [-s for s in spec], color=COLOR_SPEC, linewidth=1.5,
            linestyle=":")
    plot_bias(ax, filtered, COLOR_FILTERED, "s")

    ax.set_title(f"VL53L0X Median Filter N={n} ({mode_name})")
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


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("log", nargs="?", help="log file (default: stdin)")
    parser.add_argument("-n", "--window", type=window, required=True,
                        help="median filter window, odd and > 0")
    parser.add_argument("-p", "--plot",
                        help="save the plot instead of showing it")
    parser.add_argument("-o", "--output", help="save the filtered log")
    parser.add_argument("-c", "--csv", required=True,
                        help="CSV file for the values of the filtered readings")
    parser.add_argument("-m", "--mode", choices=MODES, default="default",
                        help="ranging mode of the measurement "
                             "(default: default)")
    parser.add_argument("--spec", type=float,
                        help="override the datasheet accuracy of the mode "
                             "in percent of the target")
    args = parser.parse_args()

    mode_name, spec_percent = MODES[args.mode]
    if args.spec is not None:
        spec_percent = args.spec

    if args.log:
        with open(args.log, encoding="utf-8", errors="replace") as f:
            lines = list(f)
    else:
        lines = list(sys.stdin)

    filtered_lines = filter_log(lines, args.window)
    filtered = parse(filtered_lines)

    if not filtered:
        sys.exit("No measurements found")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.writelines(filtered_lines)
        print(f"Filtered log saved to {args.output}")

    print(f"{mode_name}: datasheet accuracy ±{spec_percent:g} %")
    print(f"Median filter N={args.window}")
    print_table(filtered, spec_percent)
    write_csv(filtered, args.csv, spec_percent)
    plot(filtered, args.window, args.plot, spec_percent, mode_name)


if __name__ == "__main__":
    main()
