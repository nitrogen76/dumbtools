# TVHeadend HDHomeRun Picon Updater

Automatically populate TVHeadend channel icons (picons) using the
channel artwork supplied by SiliconDust's HDHomeRun Guide API.

## What this solves

TVHeadend can automatically assign HDHomeRun/ATSC channels picon
references such as:

``` text
picon://1_0_0_1_AF1_10000_DDDD0000_0_0_0.png
```

but it does not automatically obtain the corresponding image file.

The HDHomeRun tuner's local `lineup.json` contains channel numbers and
names, but not artwork:

``` json
{
  "GuideNumber": "8.1",
  "GuideName": "WFAA",
  "URL": "http://hdhomerun.example:5004/auto/v8.1"
}
```

SiliconDust's Guide API, however, supplies an `ImageURL` for many
channels:

``` json
{
  "GuideNumber": "8.1",
  "GuideName": "WFAA",
  "ImageURL": "https://img.hdhomerun.com/channels/....png"
}
```

This updater joins the TVHeadend channel list to the SiliconDust guide
by channel number and downloads the artwork using the exact picon
filename TVHeadend requested.

The resulting flow is:

``` text
TVHeadend
8.1 -> picon://1_0_0_1_AF1_10000_DDDD0000_0_0_0.png
                         |
                         | GuideNumber = 8.1
                         v
SiliconDust Guide API
8.1 -> ImageURL
                         |
                         v
/var/lib/tvheadend/picons/
1_0_0_1_AF1_10000_DDDD0000_0_0_0.png
```

This also means there is no need to reverse-engineer TVHeadend's picon
naming scheme.

## Tested environment

This setup was tested with:

-   HDHomeRun FLEX 4K
-   TVHeadend running in Docker
-   TVHeadend persistent data mounted as:

``` text
/path/on/host/to/tvheadend -> /var/lib/tvheadend
```

-   Picons stored on the host in:

``` text
/path/on/host/to/picons
```

and visible inside the container as:

``` text
/var/lib/tvheadend/picons
```

Adjust paths and hostnames below for your environment.

## TVHeadend configuration

In:

**Configuration -\> General -\> Base -\> Channel icon/Picon Settings**

use:

``` text
Prefer picons over channel icons:
    unchecked

Channel icon path:
    file:///var/lib/tvheadend/picons/%C.png

Channel icon name scheme:
    Service name picons

Picon path:
    file:///var/lib/tvheadend/picons/

Picon name scheme:
    Standard
```

The important setting for automatically generated `picon://...`
references is the **Picon path**.

Create the persistent directory on the Docker host:

``` bash
mkdir -p /path/on/host/to/picons
```

Verify that the container can see it:

``` bash
docker exec tvheadend \
    ls -ld /var/lib/tvheadend/picons
```

## Verify SiliconDust artwork

Get the tuner's current `DeviceAuth`:

``` bash
AUTH=$(
    curl -s http://HDHOMERUN_IP_OR_HOSTNAME/discover.json |
    jq -r '.DeviceAuth'
)
```

For example, look up WFAA 8.1:

``` bash
curl -s \
  "https://api.hdhomerun.com/api/guide?DeviceAuth=$AUTH&Duration=1" |
jq '.[] | select(.GuideNumber == "8.1") |
    {GuideNumber, GuideName, ImageURL}'
```

A successful response looks similar to:

``` json
{
  "GuideNumber": "8.1",
  "GuideName": "WFAA",
  "ImageURL": "https://img.hdhomerun.com/channels/US....png"
}
```

## Verify TVHeadend's picon reference

TVHeadend in this setup uses HTTP Digest authentication.

To inspect a channel:

``` bash
curl --digest -s -u 'TVHEADEND_USER:TVHEADEND_PASS' \
  'http://TVHEADEND_SERVER:9981/api/channel/grid?limit=1000' |
jq '.entries[] |
    select(.name | test("WFAA"; "i")) |
    {name, number, icon, uuid}'
```

Example:

``` json
{
  "name": "WFAA",
  "number": "8.1",
  "icon": "picon://1_0_0_1_AF1_10000_DDDD0000_0_0_0.png",
  "uuid": "..."
}
```

The corresponding file must therefore be:

``` text
/var/lib/tvheadend/picons/1_0_0_1_AF1_10000_DDDD0000_0_0_0.png
```

Inside this Docker setup, that corresponds to:

``` text
/path/on/host/to/picons/1_0_0_1_AF1_10000_DDDD0000_0_0_0.png
```

## Configure the updater for your environment

Before running the updater, edit these variables at the top of the
script:

``` bash
HDHR="http://${YOUR_HD_HOMERUN_IP_OR_HOSTNAME}"
TVH="http://${YOUR_TV_HEADEND_SERVER}:9981"
TVH_USER="${TVHEADEND_USER}"  # Replace with your TVHeadend username
TVH_PASS="${TVHEADEND_PASS}"  # Replace with your TVHeadend password

PICON_DIR="${YOUR_PICON_DIR}"
```

For example, `HDHR` can contain either an IP address or a resolvable
hostname. `TVH` should point to the TVHeadend HTTP interface, normally
on port 9981.

`PICON_DIR` is the **host-side directory into which the script downloads
the images**. If TVHeadend runs in Docker, that directory must be
mounted somewhere the TVHeadend container can read. The TVHeadend
**Picon path** must point to the corresponding path *inside* the
container.

For example:

``` text
Docker host:
    /srv/tvheadend/picons

Container:
    /var/lib/tvheadend/picons
```

with a mount such as:

``` text
/srv/tvheadend -> /var/lib/tvheadend
```

would use:

``` bash
PICON_DIR="/srv/tvheadend/picons"
```

while TVHeadend's Picon path would be:

``` text
file:///var/lib/tvheadend/picons/
```

The two paths do not have to be identical; they only need to refer to
the same files through the container mount.

## Automatic updater

Install the script as:

``` text
/usr/local/sbin/update-tvh-hdhomerun-picons
```

Make it executable:

``` bash
chmod 755 /usr/local/sbin/update-tvh-hdhomerun-picons
```

Run it manually:

``` bash
/usr/local/sbin/update-tvh-hdhomerun-picons
```

## Example result

On the initial tested run:

``` text
Finished:
  Downloaded:          59
  Already present:     1
  No HDHR guide match: 16
  No HDHR artwork:     9
  Not a picon:         347
```

The large `Not a picon` count is expected on a TVHeadend installation
containing many IPTV/FAST channels. Those channels are ignored by this
updater.

Likewise, channels that do not have a matching SiliconDust `GuideNumber`
are left untouched.

## Why existing files are not overwritten

The updater deliberately skips an icon if its destination file already
exists.

This has two benefits:

1.  Repeated runs generate very little unnecessary traffic.
2.  A manually customized station logo is preserved instead of being
    replaced by SiliconDust artwork.

This is useful because SiliconDust may sometimes provide a generic
network logo (for example ABC) rather than local-station branding (for
example WFAA).

To refresh a particular icon from SiliconDust, simply remove that picon
file and run the updater again.

## Optional systemd automation

After verifying a manual run, create:

``` text
/etc/systemd/system/tvh-picons.service
```

with:

``` ini
[Unit]
Description=Update TVHeadend picons from HDHomeRun guide
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/update-tvh-hdhomerun-picons
```

Then create:

``` text
/etc/systemd/system/tvh-picons.timer
```

with:

``` ini
[Unit]
Description=Update TVHeadend HDHomeRun picons

[Timer]
OnBootSec=5min
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable it:

``` bash
systemctl daemon-reload
systemctl enable --now tvh-picons.timer
```

Check the timer:

``` bash
systemctl list-timers tvh-picons.timer
```

Run the service manually if desired:

``` bash
systemctl start tvh-picons.service
```

Inspect its output:

``` bash
journalctl -u tvh-picons.service
```

## Dependencies

The updater requires:

``` text
bash
curl
jq
```

It also assumes:

-   TVHeadend is reachable through its HTTP API.
-   The supplied TVHeadend account has API access.
-   The HDHomeRun is reachable through its local HTTP interface.
-   The machine can reach `api.hdhomerun.com` and the returned image
    URLs.
-   The configured picon directory is visible to TVHeadend.

## Notes

### TVHeadend authentication

The tested TVHeadend installation requires Digest authentication, hence:

``` bash
curl --digest -u 'TVHEADEND_USER:TVHEADEND_PASS' ...
```

A plain `curl -u` request returned HTTP 401.

### `lineup.json` does not contain the logos

The local HDHomeRun endpoint:

``` text
http://HDHOMERUN/lineup.json
```

provides useful channel information but does not expose the artwork URL.

The artwork comes from SiliconDust's Guide API.

### FAST/IPTV channels

The updater does not attempt to obtain logos for Pluto, Tubi, Plex, FAST
Channels, or other IPTV sources.

It only downloads an image when:

1.  TVHeadend has assigned the channel a `picon://...` reference, and
2.  SiliconDust has a guide entry with the same channel number, and
3.  that guide entry contains an `ImageURL`.

This prevents the HDHomeRun updater from interfering with unrelated
TVHeadend channels.

