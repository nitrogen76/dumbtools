# getmoon

A small, accurate command-line tool that computes the **current lunar illumination** using modern astronomical ephemerides.

Unlike traditional Unix tools (`pom`, `phases`) that rely on simplified approximations, `getmoon` uses **Astropy + JPL ephemerides** to compute the Moon’s illumination continuously and precisely for any moment in time.

It is fast enough for interactive use, accurate enough to agree with NASA when timestamps match, and simple enough to live happily in `/usr/local/bin`.

---

## Features

- Computes **fraction of lunar disk illuminated** (percentage)
- Defaults to **NOW** (current UTC time)
- Accepts:
  - ISO-8601 date (`YYYY-MM-DD`)
  - ISO-8601 datetime (`YYYY-MM-DDTHH:MM:SS`)
  - Unix epoch time (seconds)
- Optional **progress bar** visualization
- Automatic bar width:
  - Half terminal width if available
  - Fallback to 25 characters
- Clean CLI interface using `argparse`
- No GUI, no curses, no nonsense

---

## Requirements

Python 3.8+

Python dependencies:


