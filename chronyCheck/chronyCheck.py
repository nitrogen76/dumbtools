#!/usr/bin/env python3

import subprocess
import requests
import sys

KUMA_URL = "http://kuma.example.com/api/push/yourwebhookhere""


def get_chrony_sources():
    result = subprocess.run(
        ["chronyc", "sources"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.splitlines()


def check_pps(lines):
    for line in lines:
        if line.startswith("#* PPS"):
            parts = line.split()

            # Example:
            # #* PPS 0 4 377 14 -576ns[-1140ns] +/- 231ns
            reach = parts[4]
            last_rx = int(parts[5])

            if reach == "377" and last_rx < 30:
                return True, f"PPS healthy (reach={reach}, last_rx={last_rx})"

            return False, f"PPS unhealthy (reach={reach}, last_rx={last_rx})"

    return False, "PPS source not selected"


def send_to_kuma(up, message):
    status = "up" if up else "down"

    response = requests.get(
        KUMA_URL,
        params={
            "status": status,
            "msg": message
        },
        timeout=10
    )
# debug
#    print(response.url)
#    print(response.text)
    response.raise_for_status()

    try:
        print(response.json())
    except Exception:
        print(response.text)


def main():
    try:
        lines = get_chrony_sources()
        healthy, message = check_pps(lines)

        print(message)

        send_to_kuma(healthy, message)

        sys.exit(0 if healthy else 1)

    except Exception as e:
        error_msg = f"Check failed: {e}"

        print(error_msg)

        try:
            send_to_kuma(False, error_msg)
        except Exception:
            pass

        sys.exit(2)


if __name__ == "__main__":
    main()
