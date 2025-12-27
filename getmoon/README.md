# getmoon

A small, accurate command-line tool that computes the **current lunar illumination** using modern astronomical ephemerides.

Unlike traditional Unix tools (`pom`, `phases`) that rely on simplified approximations, `getmoon` uses **Astropy + JPL ephemerides** to compute the Moon’s illumination continuously and precisely for any moment in time.

It is fast enough for interactive use, accurate enough to agree with NASA when timestamps match, and simple enough to live happily in `/usr/local/bin`.

---

## Features

- Computes **fraction of lunar disk illuminated** (percentage)
- Defaults to **NOW**
- Accepts multiple time formats:
  - ISO-8601 date (`YYYY-MM-DD`)
  - ISO-8601 datetime (`YYYY-MM-DDTHH:MM:SS`)
  - ISO-8601 datetime **with timezone offset**
  - Unix epoch time (seconds)
- Optional **progress bar** visualization
- Automatic progress bar width:
  - Half terminal width if available
  - Fallback to 25 characters
- Timezone-aware input and output
- Clean CLI interface using `argparse`
- No GUI, no curses, no nonsense

---

## Requirements

Python **3.8 or newer**

Python dependencies:
```
astropy>=4.3
numpy>=1.19
pytz>=2020.1; python_version < "3.9"
```

Install with:

```
pip install -r requirements.txt
```

## Or on Fedora:

```bash
dnf install python3-astropy python3-numpy python3-pytz
```

---

# Installation
## Make the script executable:

```
chmod +x getmoon.py
```

## Optionally install system-wide:

```
sudo cp getmoon.py /usr/local/bin/getmoon
```
---
# Usage
## Default (current time, UTC)

```
$ getmoon
Time (UTC): 2025-12-27T16:19:00+00:00
Moon illumination: 48.83%
```

## Timezone selection (--tz)

The --tz option controls how input times are interpreted and how output times are displayed.

Supported values:

- utc (default)
- local
- Any IANA timezone name (e.g. America/Chicago, Europe/London)

## Local timezone

```
$ getmoon --tz local
Time (local America/Chicago): 2025-12-27T10:19:00-06:00
Moon illumination: 48.83%
```

## Explicit Timezone
```
$ getmoon --tz America/Chicago
Time (America/Chicago): 2025-12-27T10:19:00-06:00
Moon illumination: 48.83%
```

## Specific date
```
$ getmoon 2025-12-26
```

## Specific datetime

```
$ getmoon 2025-12-26T19:00:00 --tz America/Chicago
```


## Offset-aware ISO datetime

If the timestamp includes a timezone offset, it is honored directly and does not require --tz:

```
$ getmoon 2025-12-27T10:27:06.600064-06:00
Time (UTC): 2025-12-27T16:27:06.600064+00:00
Moon illumination: 48.83%
```

## Unix epoch time
```
$ getmoon 1766812800 --tz local
```

## Progress Bar

### Enable progress bar

```
$ getmoon --bar
[###############----------------] 48.83%
```

### Explicit Width

```
$ getmoon --bar --width 40
[##################----------------------] 48.83%
```

Near quarter phases, you can literally see the illumination tick upward.

---

# Accuracy Notes
- Illumination is computed using Sun–Moon–Earth geometry
- Uses geocentric ephemerides
- All calculations are performed in **UTC**
- Timezones affect interpretation and display only
- Differences with web sites usually come down to timestamp choice
(many sites report illumination at a fixed daily reference time)
- If you pass the same timestamp, results should agree closely with NASA and other authoritative sources.

---

# Acknowledgments

- Classic BSD tools (pom, phases) for inspiration
- Astropy for doing the hard parts correctly
- The Moon, for cooperating
