#!/usr/bin/env python3

import signal
import os
import subprocess
import sys
import urllib.parse
import urllib.request


DEFAULT_USER_AGENT = "Mozilla/5.0"


def log(message):
    # NEVER log to stdout. Dispatcharr expects MPEG-TS there.
    print(message, file=sys.stderr, flush=True)


def get_best_rendition(source_url, user_agent):
    req = urllib.request.Request(
        source_url,
        headers={"User-Agent": user_agent},
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        master_url = response.geturl()
        master = response.read().decode("utf-8")

    best_bandwidth = -1
    best_uri = None

    lines = master.splitlines()

    for i, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF:"):
            continue

        bandwidth = None

        for attr in line.split(":", 1)[1].split(","):
            attr = attr.strip()

            if attr.startswith("BANDWIDTH="):
                try:
                    bandwidth = int(attr.split("=", 1)[1])
                except ValueError:
                    pass
                break

        if bandwidth is None:
            continue

        for candidate in lines[i + 1:]:
            candidate = candidate.strip()

            if not candidate:
                continue

            if candidate.startswith("#"):
                continue

            if bandwidth > best_bandwidth:
                best_bandwidth = bandwidth
                best_uri = candidate

            break

    if best_uri is None:
        raise RuntimeError("No HLS variants found")

    return (
        urllib.parse.urljoin(master_url, best_uri),
        best_bandwidth,
    )


def main():
    if len(sys.argv) < 2:
        print(
            f"Usage: {sys.argv[0]} STREAM_URL [USER_AGENT] [CHANNEL_ID]",
            file=sys.stderr,
        )
        return 2

    source_url = sys.argv[1]

    user_agent = (
        sys.argv[2]
        if len(sys.argv) >= 3 and sys.argv[2]
        else DEFAULT_USER_AGENT
    )

    channel_id = (
        sys.argv[3]
        if len(sys.argv) >= 4
        else "unknown"
    )

    vlc = None
    ffmpeg = None

    try:
        rendition_url, bandwidth = get_best_rendition(
            source_url,
            user_agent,
        )

        log(
            f"{channel_id}: selected bandwidth {bandwidth}"
        )
        log(
            f"{channel_id}: starting VLC"
        )

        vlc_cmd = [
            "cvlc",
            "-I", "dummy",
            rendition_url,
            f"--http-user-agent={user_agent}",
            "--no-spu",
            "--no-video-title-show",
            "--sout",
            "#standard{access=fd,mux=ts,dst=1}",
        ]

        vlc = subprocess.Popen(
            vlc_cmd,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            bufsize=0,
            user="nobody",
            group="nogroup",
            env={
                **os.environ,
                "HOME": "/tmp",
                "XDG_CONFIG_HOME": "/tmp",
            },
        )

        ffmpeg_cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "warning",
            "-i", "pipe:0",

            "-map", "0:v:0",
            "-map", "0:a:0",

            "-c", "copy",

            "-mpegts_transport_stream_id", "1",
            "-mpegts_service_id", "1",

            "-metadata", "service_provider=Pluto",
            "-metadata", "service_name=Pluto TV",

            "-f", "mpegts",
            "pipe:1",
        ]

        log(
            f"{channel_id}: starting FFmpeg normalizer"
        )

        ffmpeg = subprocess.Popen(
            ffmpeg_cmd,
            stdin=vlc.stdout,

            # THIS is the important difference from app.py:
            # FFmpeg writes directly to our stdout, which is
            # what Dispatcharr will consume.
            stdout=sys.stdout.buffer,

            stderr=sys.stderr,
            bufsize=0,
        )

        vlc.stdout.close()

        return ffmpeg.wait()

    except KeyboardInterrupt:
        return 130

    except Exception as exc:
        log(f"{channel_id}: ERROR: {exc}")
        return 1

    finally:
        if ffmpeg is not None and ffmpeg.poll() is None:
            ffmpeg.terminate()

            try:
                ffmpeg.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ffmpeg.kill()
                ffmpeg.wait()

        if vlc is not None and vlc.poll() is None:
            vlc.terminate()

            try:
                vlc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                vlc.kill()
                vlc.wait()


if __name__ == "__main__":
    sys.exit(main())
