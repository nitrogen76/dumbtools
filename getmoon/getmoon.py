#!/usr/bin/env python3

import os
from datetime import datetime
## See if I can get timezone
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from pytz import timezone as ZoneInfo  # Python 3.8 fallback

import argparse
import shutil
import sys
import numpy as np

from astropy.time import Time
from astropy.coordinates import get_body, get_sun

from datetime import datetime, timezone

def parse_time(value, tzname):
    tzname = tzname.strip()

    # Resolve timezone
    if tzname.lower() == "utc":
        tz = timezone.utc
    elif tzname.lower() == "local":
        tz = datetime.now().astimezone().tzinfo
    else:
        tz = ZoneInfo(tzname)

    # NOW
    if value is None:
        dt = datetime.now(tz)
        return Time(dt.astimezone(timezone.utc))

    # Unix epoch
    if value.isdigit():
        return Time(float(value), format="unix", scale="utc")

    # ISO date or datetime
    dt = datetime.fromisoformat(value)

    # If no timezone info, assume provided tz
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)

    return Time(dt.astimezone(timezone.utc))

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
        "--tz",
        default="utc",
        help="Timezone for input/output (utc, local, or IANA name like America/Chicago)",
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

    t = parse_time(args.time, args.tz)
    illum = moon_illumination(t)

    from datetime import timezone

    dt_utc = t.to_datetime(timezone=timezone.utc)
    if args.tz.lower() == "local":
        dt_disp = dt_utc.astimezone()
        tz_label = f"local {dt_disp.tzinfo}"

    elif args.tz.lower() == "utc":
        dt_disp = dt_utc
        tz_label = "UTC"
    else:
        dt_disp = dt_utc.astimezone(ZoneInfo(args.tz))
        tz_label = args.tz

    print(f"Time ({tz_label}): {dt_disp.isoformat()}")


    if args.bar:
        width = args.width if args.width else default_bar_width()
        bar = render_bar(illum / 100.0, width)
        print(f"{bar} {illum:.2f}%")


if __name__ == "__main__":
    main()

