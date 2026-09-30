#!/usr/bin/env bash
set -euo pipefail

HDHR="http://${YOUR_HD_HOMERUN_IP_OR_HOSTNAME}"
TVH="http://${YOUR_TV_HEADEND_SERVER}:9981"
TVH_USER="${TVHEADEND_USER}"  # Replace with your tvheadend username
TVH_PASS="${TVHEADEND_PASS}"  # Replace with your tvheadend password

PICON_DIR="${YOUR/PICON/DIR}"

mkdir -p "$PICON_DIR"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

echo "Fetching HDHomeRun authentication..."
AUTH=$(
    curl -fsS "$HDHR/discover.json" |
    jq -r '.DeviceAuth'
)

if [[ -z "$AUTH" || "$AUTH" == "null" ]]; then
    echo "ERROR: Couldn't obtain DeviceAuth"
    exit 1
fi

echo "Fetching SiliconDust guide..."
curl -fsS \
    "https://api.hdhomerun.com/api/guide?DeviceAuth=${AUTH}&Duration=1" \
    -o "$tmpdir/guide.json"

echo "Fetching TVHeadend channels..."
curl --digest -fsS -u "${TVH_USER}:${TVH_PASS}" \
    "${TVH}/api/channel/grid?limit=10000" \
    -o "$tmpdir/tvh.json"

downloaded=0
existing=0
no_guide=0
no_image=0
not_picon=0

while IFS=$'\t' read -r number name icon; do

    # Only process channels with a picon:// assignment.
    if [[ "$icon" != picon://*.png ]]; then
        ((++not_picon))
        continue
    fi

    # SiliconDust GuideNumber should correspond to TVHeadend's channel number.
    image_url=$(
        jq -r --arg num "$number" '
            .[] |
            select(.GuideNumber == $num) |
            .ImageURL // empty
        ' "$tmpdir/guide.json" |
        head -1
    )

    if [[ -z "$image_url" ]]; then
        # Distinguish no guide entry from guide entry without artwork.
        if jq -e --arg num "$number" \
            '.[] | select(.GuideNumber == $num)' \
            "$tmpdir/guide.json" >/dev/null; then
            printf "%-7s %-25s no artwork\n" "$number" "$name"
            ((++no_image))
        else
            printf "%-7s %-25s not in HDHomeRun guide\n" "$number" "$name"
            ((++no_guide))
        fi
        continue
    fi

    filename=${icon#picon://}
    dest="${PICON_DIR}/${filename}"

    if [[ -s "$dest" ]]; then
        printf "%-7s %-25s exists: %s\n" \
            "$number" "$name" "$filename"
        ((++existing))
        continue
    fi

    printf "%-7s %-25s -> %s\n" \
        "$number" "$name" "$filename"

    if curl -fLsS "$image_url" -o "${dest}.tmp"; then
        mv "${dest}.tmp" "$dest"
        ((++downloaded))
    else
        echo "        ERROR downloading $image_url"
        rm -f "${dest}.tmp"
    fi

done < <(
    jq -r '
        .entries[] |
        select(.number != null) |
        [
            (.number | tostring),
            (.name // ""),
            (.icon // "")
        ] |
        @tsv
    ' "$tmpdir/tvh.json"
)

echo
echo "Finished:"
echo "  Downloaded:          $downloaded"
echo "  Already present:     $existing"
echo "  No HDHR guide match: $no_guide"
echo "  No HDHR artwork:     $no_image"
echo "  Not a picon:         $not_picon"
