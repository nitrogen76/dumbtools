#!/usr/bin/env python3

import argparse
import shutil
import sys
import numpy as np

from astropy.time import Time
from astropy.coordinates import get_body, get_sun


def parse_time(value):
    """
    Parse a time argument:
    - None        -> now (UTC)
    - digits      -> Unix epoch seconds
    - otherwise   -> ISO-8601 date/datetime
    """
    if value is None:
        return Time.now()

    if value.isdigit():
        return Time(float(value), format="unix", scale="utc")

#    return Time(value, scale="utc")
# python 3.8
    return Time(value, format="isot", scale="utc")



def moon_illumination(t):
    moon = get_body("moon", t)
    sun = get_sun(t)

    # Vectors
    v_ms = (sun.cartesian - moon.cartesian).xyz.to_value()
    v_me = (-moon.cartesian).xyz.to_value()

    # Normalize
    v_ms /= np.linalg.norm(v_ms)
    v_me /= np.linalg.norm(v_me)

    # Phase angle
    cos_alpha = np.dot(v_ms, v_me)
    cos_alpha = np.clip(cos_alpha, -1.0, 1.0)
    phase_angle = np.arccos(cos_alpha)

    illumination = (1 + np.cos(phase_angle)) / 2 * 100
    return illumination


def default_bar_width():
    try:
        cols = shutil.get_terminal_size().columns
        return max(10, cols // 2)
    except Exception:
        return 25


def render_bar(fraction, width):
    filled = int(round(fraction * width))
    empty = width - filled
    return "[" + "#" * filled + "-" * empty + "]"


def main():
    parser = argparse.ArgumentParser(
        description="Compute lunar illumination using JPL ephemerides."
    )

    parser.add_argument(
        "time",
        nargs="?",
        help="ISO date/datetime or Unix epoch (default: now)",
    )

    parser.add_argument(
        "--bar",
        action="store_true",
        help="Show illumination as a progress bar",
    )

    parser.add_argument(
        "--width",
        type=int,
        help="Progress bar width (default: half terminal width, fallback 25)",
    )

    args = parser.parse_args()

    t = parse_time(args.time)
    illum = moon_illumination(t)

    print(f"Time (UTC): {t.isot}")
    print(f"Moon illumination: {illum:.2f}%")

    if args.bar:
        width = args.width if args.width else default_bar_width()
        bar = render_bar(illum / 100.0, width)
        print(f"{bar} {illum:.2f}%")


if __name__ == "__main__":
    main()

