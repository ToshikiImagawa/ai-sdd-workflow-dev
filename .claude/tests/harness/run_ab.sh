#!/bin/sh
# run_ab.sh - Issue #16 A/B launcher (2-PROJECT design; LOCAL ONLY, not CI).
#
# Launches the off and on fixture PROJECTS with the SAME prompt/model, N times
# each. Each project uses its own plugin (via --plugin-dir) and its own cwd =>
# its own transcript project-key dir => aggregate_tokens.py classifies groups
# by directory.
#   off project: marketplace plugin (no index support)
#   on  project: local plugin with index support (session-start builds index)
#
# Usage: run_ab.sh [scale] [N] [prompt-name]
#   scale: small (default) | medium | large   (must match synthesize_sdd.py)
#   prompt-name: doc_consistency (default) | requirement_analyzer
#
# Env vars:
#   SDD_AB_MODEL       model to use (default: claude-sonnet-5)
#   SDD_AB_PLUGIN_OFF  plugin-dir for off group (default: marketplace install)
#   SDD_AB_PLUGIN_ON   plugin-dir for on group (default: repo local)
#
# Requires: claude CLI, jq, python3.
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)
SCALE=${1:-small}
N=${2:-5}
PROMPT_NAME=${3:-doc_consistency}
PLUGIN_OFF=${SDD_AB_PLUGIN_OFF:-"$HOME/.claude/plugins/marketplaces/ai-sdd-workflow/plugins/sdd-workflow"}
PLUGIN_ON=${SDD_AB_PLUGIN_ON:-"$REPO/plugins/sdd-workflow"}
MODEL=${SDD_AB_MODEL:-claude-sonnet-5}
PROMPT_DIR="$SCRIPT_DIR/prompts"
PROMPT_FILE="$PROMPT_DIR/${PROMPT_NAME}.txt"
OFF_FIX="$REPO/.claude/tests/fixtures/sdd-${SCALE}-off"
ON_FIX="$REPO/.claude/tests/fixtures/sdd-${SCALE}-on"

for d in "$OFF_FIX" "$ON_FIX"; do
    if [ ! -d "$d/.sdd" ]; then
        echo "fixture not found: $d (run: python3 $SCRIPT_DIR/synthesize_sdd.py --scale $SCALE)" >&2
        exit 1
    fi
done
[ -f "$PROMPT_FILE" ] || { echo "prompt not found: $PROMPT_FILE" >&2; exit 1; }

RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)
OUT_DIR="$REPO/.claude/tests/runs/$RUN_ID"
mkdir -p "$OUT_DIR"
START_UTC=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
SYSTEM_PIN=$(cat "$PROMPT_DIR/system_pin.txt")

# run_project LABEL FIXTURE IDS_FILE PLUGIN_DIR -> prints the fixture abs path on stdout
run_project() {
    label=$1; fix=$2; ids_file=$3; plugin_dir=$4
    fix_abs=$(CDPATH='' cd -- "$fix" && pwd)
    key=$(printf '%s' "$fix_abs" | sed 's/[^a-zA-Z0-9]/-/g')
    key_dir="$HOME/.claude/projects/$key"
    mkdir -p "$key_dir"
    : > "$ids_file"
    i=1
    while [ "$i" -le "$N" ]; do
        echo "[run_ab] $label trial=$i/$N (project=$fix_abs)" >&2
        before=$(mktemp); after=$(mktemp)
        find "$key_dir" -maxdepth 1 -name '*.jsonl' | LC_ALL=C sort > "$before"
        (
            cd "$fix_abs" && \
            SDD_LANG=en CLAUDE_PROJECT_DIR="$fix_abs" \
            claude --print --plugin-dir "$plugin_dir" --model "$MODEL" \
                --append-system-prompt "$SYSTEM_PIN" < "$PROMPT_FILE"
        ) > "$OUT_DIR/${label}_${i}.out" 2>&1 || \
            echo "[run_ab] warning: claude exited non-zero (${label}_${i}.out)" >&2
        find "$key_dir" -maxdepth 1 -name '*.jsonl' | LC_ALL=C sort > "$after"
        comm -13 "$before" "$after" | while IFS= read -r newf; do
            [ -n "$newf" ] || continue
            basename "$newf" .jsonl >> "$ids_file"
        done
        rm -f "$before" "$after"
        i=$((i + 1))
    done
    printf '%s' "$fix_abs"
}

OFF_IDS="$OUT_DIR/off_ids.txt"
ON_IDS="$OUT_DIR/on_ids.txt"
OFF_DIR=$(run_project off "$OFF_FIX" "$OFF_IDS" "$PLUGIN_OFF")
ON_DIR=$(run_project on "$ON_FIX" "$ON_IDS" "$PLUGIN_ON")

OFF_JSON=$(jq -R -s 'split("\n")|map(select(length>0))' < "$OFF_IDS")
ON_JSON=$(jq -R -s 'split("\n")|map(select(length>0))' < "$ON_IDS")
COMMIT=$(git -C "$REPO" rev-parse HEAD)
CLI_VER=$(claude --version 2>/dev/null | head -1 || echo unknown)

jq -n \
    --arg run "$RUN_ID" --arg start "$START_UTC" --arg scale "$SCALE" \
    --argjson n "$N" --arg commit "$COMMIT" --arg cli "$CLI_VER" --arg prompt "$PROMPT_NAME" \
    --arg offdir "$OFF_DIR" --arg ondir "$ON_DIR" \
    --arg offplugin "$PLUGIN_OFF" --arg onplugin "$PLUGIN_ON" \
    --argjson off "$OFF_JSON" --argjson on "$ON_JSON" \
    '{run_id:$run, start_utc:$start, scale:$scale, N:$n, prompt:$prompt,
      commit:$commit, cli_version:$cli,
      off:{project_dir:$offdir, plugin_dir:$offplugin, sessions:$off},
      on:{project_dir:$ondir, plugin_dir:$onplugin, sessions:$on}}' \
    > "$OUT_DIR/manifest.json"

echo "[run_ab] manifest: $OUT_DIR/manifest.json" >&2
echo "[run_ab] next: python3 $SCRIPT_DIR/aggregate_tokens.py --manifest '$OUT_DIR/manifest.json' --out-dir '$OUT_DIR'" >&2
