# Chrony PPS Monitor for Uptime Kuma

A simple Python script that checks whether Chrony is actively synchronized to a PPS (Pulse Per Second) source and reports the result to Uptime Kuma using a Push monitor.

This is more useful than a basic NTP port check because it verifies:

- PPS is present

- PPS is the selected synchronization source

- Reachability is healthy

- PPS updates are recent

## Requirements

- Python 3

- `chronyc`

- `requests` Python module

- Uptime Kuma Push monitor

Install dependencies:

```bash
dnf install python3-requests
```
or

```bash
pip install requests
```

# Uptime Kuma Setup

Create a new monitor in Uptime Kuma:

* Monitor Type: Push

Copy the generated push URL.

Use only the base endpoint, for example:

```
https://kuma.example.com/api/push/xxxxxxxx
```

# Example Output

Healthy:
```
PPS healthy (reach=377, last_rx=15)
{'ok': True}
```

Unhealthy:

```
PPS source not selected
{'ok': True}
```

This script looks for my gps monitor, so it'll have to be modified for other uses.