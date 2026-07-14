#!/bin/sh
# verify_parity.sh - Issue #16 Step1 A/B parity guard (LOCAL ONLY; not in CI).
#
# Checks (2-project design):
#   pair <off-fixture> <on-fixture>   assert the two .sdd bodies are byte-identical
#                                     (the independent variable must be config only)
#   snapshot <fixture>                record a fixture's .sdd checksum baseline
#   verify   <fixture>                assert the fixture .sdd is unchanged since
#                                     snapshot (consumers are Read/Glob/Grep only)
# .sdd/.cache/ is excluded everywhere (index artifacts differ/appear by design).
set -eu

body_hash() {
    # total checksum of one fixture's .sdd body, excluding .cache
    (
        CDPATH='' cd -- "$1/.sdd" && \
        find . -type f -not -path '*/.cache/*' | LC_ALL=C sort \
            | xargs shasum | shasum | awk '{print $1}'
    )
}

MODE=${1:-}
case "$MODE" in
    pair)
        OFF=${2:-}; ON=${3:-}
        if [ ! -d "$OFF/.sdd" ] || [ ! -d "$ON/.sdd" ]; then
            echo "usage: verify_parity.sh pair <off-fixture> <on-fixture>" >&2
            exit 2
        fi
        H_OFF=$(body_hash "$OFF")
        H_ON=$(body_hash "$ON")
        echo "off body: $H_OFF"
        echo "on  body: $H_ON"
        if [ "$H_OFF" = "$H_ON" ]; then
            echo "[verify_parity] PASS: off/on .sdd bodies are byte-identical"
        else
            echo "[verify_parity] FAIL: off/on .sdd bodies differ" >&2
            exit 1
        fi
        ;;
    snapshot)
        FIX=${2:-}
        [ -d "$FIX/.sdd" ] || { echo "usage: verify_parity.sh snapshot <fixture>" >&2; exit 2; }
        body_hash "$FIX" > "$FIX/.sdd-parity.sha"
        echo "[verify_parity] baseline recorded for $FIX"
        ;;
    verify)
        FIX=${2:-}
        [ -d "$FIX/.sdd" ] || { echo "usage: verify_parity.sh verify <fixture>" >&2; exit 2; }
        SNAP="$FIX/.sdd-parity.sha"
        [ -f "$SNAP" ] || { echo "[verify_parity] no baseline; run snapshot first" >&2; exit 2; }
        if [ "$(body_hash "$FIX")" = "$(cat "$SNAP")" ]; then
            echo "[verify_parity] PASS: $FIX .sdd unchanged (excluding .cache)"
        else
            echo "[verify_parity] FAIL: $FIX .sdd changed" >&2
            exit 1
        fi
        ;;
    *)
        echo "usage: verify_parity.sh {pair <off> <on> | snapshot <fix> | verify <fix>}" >&2
        exit 2
        ;;
esac
