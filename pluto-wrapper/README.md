# pluto-wrapper

`pluto-wrapper` is a compatibility wrapper for playing Pluto TV FAST
streams through Dispatcharr and downstream IPTV software such as
TVHeadend.

It was built to handle Pluto HLS streams containing discontinuities and
dynamic ad insertion (DAI) transitions that can break simpler Streamlink
or direct-FFmpeg pipelines.

## Pipeline

``` text
Pluto / FastChannels
        |
        v
resolve current HLS master
        |
        v
select highest-BANDWIDTH fixed rendition
        |
        v
VLC
(HLS/discontinuity handling)
        |
        v
FFmpeg -c copy
(MPEG-TS normalization)
        |
        v
Dispatcharr
        |
        v
TVHeadend / IPTV client
```

**No video or audio transcoding is performed.**

## What the wrapper does

1.  Accepts a source HLS URL, User-Agent, and optional channel ID.
2.  Fetches the source and follows redirects to the current signed Pluto
    HLS master.
3.  Parses the master playlist.
4.  Selects the variant with the highest advertised `BANDWIDTH`.
5.  Starts VLC on that fixed rendition.
6.  Has VLC output MPEG-TS to a pipe.
7.  Passes that stream through FFmpeg with `-c copy`.
8.  Normalizes the transport stream for Dispatcharr/TVHeadend.
9.  Writes **only MPEG-TS data to stdout**; diagnostics go to stderr.

Using a fixed rendition is intentional. Adaptive switching can introduce
extra resolution, PID, or stream-layout changes downstream.

## Why VLC + FFmpeg?

The programs have separate jobs.

**VLC** faces the HLS source and has proven tolerant of Pluto's playlist
discontinuities and program/ad transitions.

**FFmpeg** does not consume Pluto HLS directly. It receives MPEG-TS from
VLC and remuxes it into a predictable transport stream.

The normalized output uses:

-   MPEG-TS
-   source H.264 video via stream copy
-   source AAC audio via stream copy
-   TSID `1`
-   Service ID `1`
-   stable generated video/audio PIDs
-   service provider `Pluto`
-   service name `Pluto TV`

Resolution and bitrate remain whatever Pluto supplies in the selected
highest-bandwidth rendition.

## Requirements

-   Python 3
-   VLC / `cvlc`
-   FFmpeg
-   network access to the source HLS URLs

The HLS master resolver itself uses only Python standard-library
modules.

## Dispatcharr installation

In the tested installation, Dispatcharr has persistent storage mounted
at `/data`.

Install the wrapper as:

``` text
/data/scripts/pluto-wrapper.py
```

For a host bind mount such as:

``` text
/tank/docker/dispatcharr -> /data
```

the persistent host path is:

``` text
/tank/docker/dispatcharr/scripts/pluto-wrapper.py
```

Make it executable:

``` bash
chmod 755 /tank/docker/dispatcharr/scripts/pluto-wrapper.py
```

Verify it:

``` bash
docker exec dispatcharr \
  ls -l /data/scripts/pluto-wrapper.py
```

## Dispatcharr Custom Stream Profile

Configure the profile as:

``` text
Custom Command:
/data/scripts/pluto-wrapper.py

Parameters:
{streamUrl} {userAgent} {channelId}
```

Dispatcharr continues to expose its ordinary `/proxy/ts/stream/...` URL
to clients. The wrapper is simply an internal processing stage.

## Command-line usage

``` text
pluto-wrapper.py STREAM_URL [USER_AGENT] [CHANNEL_ID]
```

Example:

``` bash
/data/scripts/pluto-wrapper.py \
  'http://fastchannels.example/play/pluto/<channel-id>.m3u8' \
  'Mozilla/5.0' \
  'test-channel' \
  > /tmp/test.ts
```

When testing inside Dispatcharr, execute it as the same user used by
Dispatcharr:

``` bash
docker exec -u dispatch dispatcharr \
  /data/scripts/pluto-wrapper.py \
  'http://fastchannels.example/play/pluto/<channel-id>.m3u8' \
  'Mozilla/5.0' \
  'test-channel' \
  > /tmp/test.ts
```

Stop a live test with `Ctrl-C`.

## Important privilege note

The tested Dispatcharr application processes run as the unprivileged
`dispatch` user.

The wrapper should **not** attempt to change the VLC child to another
UID/GID using `subprocess.Popen(user=..., group=...)`.

Doing that when the wrapper is already running as `dispatch` produces:

``` text
[Errno 1] Operation not permitted
```

Allow VLC and FFmpeg to inherit Dispatcharr's existing unprivileged
identity.

An ordinary `docker exec` defaults to root and is therefore not
representative of how Dispatcharr launches the wrapper. VLC normally
refuses to run as root.

## stdout vs stderr

This is critical:

**stdout is the MPEG-TS video stream.**

Never print logs or diagnostics to stdout.

Logging should go to stderr:

``` python
def log(message):
    print(message, file=sys.stderr, flush=True)
```

Dispatcharr may label anything VLC writes to stderr as a stream-process
error even when it is harmless.

Typical harmless headless VLC noise includes failures involving:

-   PulseAudio
-   D-Bus
-   global hotkeys

If playback continues, these are not fatal stream errors.

## Expected startup

A successful invocation should produce stderr similar to:

``` text
<channel-id>: selected bandwidth 3321280
<channel-id>: starting VLC
<channel-id>: starting FFmpeg normalizer
adaptive demux: Changing stream format Unknown -> TS
mpeg4audio decoder: AAC channels: 2 samplerate: 48000
```

The selected bandwidth depends on the current source playlist.

## Inspecting a captured stream

``` bash
ffprobe -hide_banner /tmp/test.ts
```

A successful result should generally contain:

``` text
Program 1
  service_name     : Pluto TV
  service_provider : Pluto

Stream #0:0: Video: h264
Stream #0:1: Audio: aac
```

Because the wrapper uses `-c copy`, it does not deliberately scale video
or re-encode audio/video.

## Client disconnects

Messages such as:

``` text
Broken pipe
OSError: write error
```

can be completely normal when a viewer stops playback or changes
channels. The client has disappeared while a live stream was still being
written.

VLC may similarly report an HLS request as cancelled or closed during
shutdown.

Interpret these messages in context rather than automatically treating
them as source failures.

## Tested behavior

The pipeline has successfully demonstrated:

-   playback of multiple Pluto channels
-   720p-class source playback
-   program-to-ad transitions
-   recovery after a brief disturbance at an ad boundary
-   stable normalized MPEG-TS
-   operation through a Dispatcharr Custom Stream Profile
-   no transcoding

Some DAI transitions may still produce a brief playback "burp." The
important behavior is that the stream continues rather than permanently
dying at the discontinuity.

## Why not Streamlink?

Streamlink could initially tune the streams but reported:

``` text
Encountered a stream discontinuity. This is unsupported and will result in incoherent output data.
```

Program/ad transitions could subsequently break playback.

That made Streamlink unsuitable for this source behavior.

## Why not direct FFmpeg HLS?

Direct FFmpeg consumption of the Pluto HLS source was also tested.
Besides source/User-Agent details, it did not provide the same reliable
behavior across HLS/timestamp discontinuities.

The successful division of labor is:

``` text
VLC:     HLS client and discontinuity handling
FFmpeg:  MPEG-TS remux/normalization
```

Since FFmpeg uses stream copy rather than codecs, CPU requirements are
modest compared with transcoding.

## Potential use with other FAST providers

The architecture is not inherently Pluto-specific.

The reusable portion is:

``` text
provider stream
      |
      v
resolve/select fixed HLS rendition
      |
      v
VLC
      |
      v
FFmpeg -c copy
      |
      v
normalized MPEG-TS
```

Other FAST providers may need different URL, authentication, token, API,
or playlist-resolution logic.

A generalized version could separate provider resolution from the common
streaming backend:

``` python
rendition_url = resolve_provider_stream(stream_url)
```

Provider-specific resolvers could then feed the same VLC/FFmpeg
normalization pipeline.

## Troubleshooting

If Dispatcharr reports:

``` text
[Errno 1] Operation not permitted
```

check whether the wrapper is attempting to change UID/GID. In the tested
container, Dispatcharr already invokes it as an unprivileged user.

If VLC complains about running as root, test as Dispatcharr's user:

``` bash
docker exec -u dispatch dispatcharr ...
```

If Dispatcharr logs PulseAudio, D-Bus, or global-hotkey errors while
video is playing, they are generally headless VLC noise.

If playback fails specifically at commercials, inspect VLC's behavior
around the HLS discontinuity before changing FFmpeg options. Keeping the
provider's HLS weirdness on VLC's side is the reason for this
architecture.

## Status

**Working home-lab implementation.**

The wrapper has been applied to the Pluto channels in Dispatcharr for
broader real-world testing.

