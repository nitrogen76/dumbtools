#!/bin/bash

set -u

INSTANCE="DNA-NURGLE-NET"
MAX_AGE=86400                    # 1 day
HOST="$(hostname -s)"

DOMAIN_SUFFIX="dc=dna,dc=nurgle,dc=net"
CA_SUFFIX="o=ipaca"

# Uptime Kuma Push URLs
DOMAIN_PUSH_URL="https://kuma.example.com/api/push/DOMAIN_TOKEN"
CA_PUSH_URL="https://kuma.example.com/api/push/CA_TOKEN"

PUSH=1

usage()
{
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Check FreeIPA/389-DS replication health.

Options:
    --no-push       Do not send results to Uptime Kuma.
                    Print results to stdout instead.

    -h, --help      Show this help.

Examples:

    Normal monitoring run:
        $(basename "$0")

    Manual check without contacting Uptime Kuma:
        $(basename "$0") --no-push
EOF
}


while (( $# )); do
    case "$1" in
        --no-push)
            PUSH=0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac

    shift
done


check_suffix()
{
    local name="$1"
    local suffix="$2"
    local push_url="$3"

    local output rc status last_end now last_epoch age
    local result="up"
    local message

    output="$(dsconf "$INSTANCE" repl-agmt list --suffix="$suffix" 2>&1)"
    rc=$?

    if (( rc != 0 )); then
        result="down"
        message="$name: dsconf failed: $output"
    else
        status="$(printf '%s\n' "$output" |
            sed -n 's/^nsds5replicaLastUpdateStatus: //p' |
            tail -1)"

        last_end="$(printf '%s\n' "$output" |
            sed -n 's/^nsds5replicaLastUpdateEnd: //p' |
            tail -1)"

        if [[ -z "$status" ]]; then
            result="down"
            message="$name: no replication status returned"

        elif [[ "$status" != Error\ \(0\)* ]]; then
            result="down"
            message="$name: $status"

        elif [[ -z "$last_end" ]]; then
            result="down"
            message="$name: successful status but no LastUpdateEnd"

        else
            # Convert 389-DS generalized time:
            #
            #     20260915030658Z
            #
            # to Unix epoch.

            last_epoch="$(
                date -u -d \
                "${last_end:0:4}-${last_end:4:2}-${last_end:6:2} ${last_end:8:2}:${last_end:10:2}:${last_end:12:2} UTC" \
                +%s 2>/dev/null
            )"

            now="$(date +%s)"

            if [[ -z "$last_epoch" ]]; then
                result="down"
                message="$name: cannot parse LastUpdateEnd $last_end"
            else
                age=$(( now - last_epoch ))

                if (( age > MAX_AGE )); then
                    result="down"
                    message="$name: last successful update ${age}s ago"
                else
                    message="$name replication OK (${age}s ago)"
                fi
            fi
        fi
    fi

    #
    # Always log the result locally.
    #
    logger -t ipa-replication-monitor \
        "$HOST $name status=$result: $message"

    #
    # Interactive/manual mode
    #
    if (( PUSH == 0 )); then
        if [[ "$result" == "up" ]]; then
            printf '%-8s OK     %s\n' "$name" "$message"
        else
            printf '%-8s FAILED %s\n' "$name" "$message"
        fi

    #
    # Uptime Kuma mode
    #
    else
        if ! curl -fsS --get \
            --data-urlencode "status=$result" \
            --data-urlencode "msg=$HOST: $message" \
            --data-urlencode "ping=" \
            "$push_url" >/dev/null
        then
            echo "$HOST $name: failed to push status to Uptime Kuma" >&2
        fi
    fi

    [[ "$result" == "up" ]]
}


FAILED=0

if (( PUSH == 0 )); then
    echo "FreeIPA replication status for $HOST"
    echo
fi

check_suffix "DOMAIN" "$DOMAIN_SUFFIX" "$DOMAIN_PUSH_URL" || FAILED=1
check_suffix "CA"     "$CA_SUFFIX"     "$CA_PUSH_URL"     || FAILED=1

if (( PUSH == 0 )); then
    echo

    if (( FAILED )); then
        echo "Overall: FAILED"
    else
        echo "Overall: OK"
    fi
fi

exit "$FAILED"
