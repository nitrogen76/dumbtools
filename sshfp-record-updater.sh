#!/usr/bin/env bash
set -euo pipefail

FQDN="${1:-$(hostname -f)}"
ZONE="${FQDN#*.}"
HOST="${FQDN%%.*}"

args=()

while read -r rec; do
    args+=(--sshfp-rec="$rec")
done < <(
    ssh-keygen -r "$FQDN" | awk '{print $4 " " $5 " " $6}'
)

ipa dnsrecord-mod "$ZONE" "$HOST" "${args[@]}"

ipa dnsrecord-show "$ZONE" "$HOST"
