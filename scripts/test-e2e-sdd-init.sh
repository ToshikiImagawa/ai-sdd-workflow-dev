#!/bin/sh
# test-e2e-sdd-init.sh
# End-to-end regression test for the sdd-init flow in a fresh empty project:
#   session-start.py (SessionStart hook) -> init-structure.sh -> update-claude-md.sh
#
# Verifies the AI-SDD Instructions migration end to end:
#   - CLAUDE.md is minimized to declaration + trigger + a pointer (no long body)
#   - the detailed guide is written to .claude/rules/ai-sdd-instructions.md
#     (a single English file, version-substituted, path-scoped to .sdd/**)
#   - legacy per-language rules files are cleaned up on sync
#   - the whole flow is idempotent (re-running changes nothing)
#
# POSIX compatible (macOS bash 3.2 / dash).

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_ROOT="${REPO_ROOT}/plugins/sdd-workflow"

SESSION_START="${PLUGIN_ROOT}/scripts/session-start.py"
INIT_STRUCTURE="${PLUGIN_ROOT}/skills/sdd-init/scripts/init-structure.sh"
UPDATE_CLAUDE_MD="${PLUGIN_ROOT}/skills/sdd-init/scripts/update-claude-md.sh"
PLUGIN_JSON="${PLUGIN_ROOT}/.claude-plugin/plugin.json"

RULES_REL=".claude/rules/ai-sdd-instructions.md"
LEGACY_REL=".claude/rules/ai-sdd-instructions-en.md"

PASS_COUNT=0
FAIL_COUNT=0

# Colors (only if terminal supports it)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    NC=''
fi

pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    printf '%sPASS%s %s\n' "$GREEN" "$NC" "$1"
}

fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '%sFAIL%s %s\n' "$RED" "$NC" "$1"
}

# assert_file DESC PATH  - path exists as a regular file
assert_file() {
    if [ -f "$2" ]; then pass "$1"; else fail "$1 (missing: $2)"; fi
}

# assert_no_file DESC PATH  - path does not exist
assert_no_file() {
    if [ ! -e "$2" ]; then pass "$1"; else fail "$1 (unexpected: $2)"; fi
}

# assert_grep DESC FIXED_STRING FILE  - file contains the fixed string
assert_grep() {
    if grep -qF "$2" "$3" 2>/dev/null; then pass "$1"; else fail "$1 (not found: $2)"; fi
}

# assert_not_grep DESC FIXED_STRING FILE  - file does NOT contain the fixed string
assert_not_grep() {
    if grep -qF "$2" "$3" 2>/dev/null; then fail "$1 (unexpectedly found: $2)"; else pass "$1"; fi
}

# assert_count DESC EXPECTED FIXED_STRING FILE  - exact matching-line count
assert_count() {
    n=$(grep -cF "$3" "$4" 2>/dev/null || true)
    if [ "$n" = "$2" ]; then pass "$1"; else fail "$1 (want $2 got $n)"; fi
}

# assert_same DESC FILE_A FILE_B  - files are byte-identical
assert_same() {
    if cmp -s "$2" "$3"; then pass "$1"; else fail "$1 (files differ)"; fi
}

# Prerequisites (skip cleanly rather than fail on a minimal runner)
if ! command -v python3 >/dev/null 2>&1; then
    printf 'SKIP: python3 not found\n'
    exit 0
fi
if ! command -v jq >/dev/null 2>&1; then
    printf 'SKIP: jq not found (update-claude-md.sh requires jq)\n'
    exit 0
fi
if [ ! -f "$PLUGIN_JSON" ]; then
    printf 'Error: plugin.json not found at %s\n' "$PLUGIN_JSON" >&2
    exit 1
fi

VERSION="$(jq -r '.version' "$PLUGIN_JSON")"

# Isolated temp workspace
TMP_DIR="$(mktemp -d)"
cleanup_on_exit() {
    if [ -n "${TMP_DIR:-}" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
}
trap cleanup_on_exit EXIT

PROJ="${TMP_DIR}/project"
mkdir -p "$PROJ"
ENV_FILE="${TMP_DIR}/env_output"
: > "$ENV_FILE"

run_session_start() {
    CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
        CLAUDE_PROJECT_DIR="$PROJ" \
        CLAUDE_ENV_FILE="$ENV_FILE" \
        python3 "$SESSION_START" --default-lang "$1" >/dev/null 2>&1
}

run_init_structure() {
    CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
        CLAUDE_PROJECT_DIR="$PROJ" \
        CLAUDE_ENV_FILE="$ENV_FILE" \
        bash "$INIT_STRUCTURE" >/dev/null 2>&1
}

run_update_claude_md() {
    CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
        CLAUDE_PROJECT_DIR="$PROJ" \
        CLAUDE_ENV_FILE="$ENV_FILE" \
        bash "$UPDATE_CLAUDE_MD" >/dev/null 2>&1
}

printf '=== sdd-init E2E Regression Test (v%s) ===\n\n' "$VERSION"

# ---------------------------------------------------------------------------
# STEP 1: Fresh session start (default lang en)
# ---------------------------------------------------------------------------
printf -- '--- STEP 1: fresh session-start (en) ---\n'
if ! run_session_start en; then fail "session-start.py (en) exited non-zero"; fi
assert_file      "session-start creates .sdd-config.json"           "$PROJ/.sdd-config.json"
assert_grep      "config lang is en"                                '"lang": "en"'          "$PROJ/.sdd-config.json"
assert_file      "session-start creates AI-SDD-PRINCIPLES.md"       "$PROJ/.sdd/AI-SDD-PRINCIPLES.md"
assert_file      "session-start creates rules file"                 "$PROJ/$RULES_REL"
assert_not_grep  "rules file has no unresolved placeholder"         '{PLUGIN_VERSION}'       "$PROJ/$RULES_REL"
assert_grep      "rules file is path-scoped to .sdd/**"             '.sdd/**'                "$PROJ/$RULES_REL"
assert_grep      "rules file version is substituted"                "$VERSION"               "$PROJ/$RULES_REL"
assert_grep      "rules file is the English guide"                  'AI-driven Specification-Driven Development' "$PROJ/$RULES_REL"
assert_no_file   "session-start does not create CLAUDE.md"          "$PROJ/CLAUDE.md"
assert_file      "session-start writes UPDATE_REQUIRED.md warning"  "$PROJ/.sdd/UPDATE_REQUIRED.md"

# ---------------------------------------------------------------------------
# STEP 2: sdd-init (init-structure.sh then update-claude-md.sh)
# ---------------------------------------------------------------------------
printf -- '--- STEP 2: init-structure + update-claude-md ---\n'
if ! run_init_structure; then fail "init-structure.sh exited non-zero"; fi
assert_no_file   "init-structure removes UPDATE_REQUIRED.md"        "$PROJ/.sdd/UPDATE_REQUIRED.md"
if ! run_update_claude_md; then fail "update-claude-md.sh exited non-zero"; fi
assert_file      "update-claude-md creates CLAUDE.md"               "$PROJ/CLAUDE.md"
assert_grep      "CLAUDE.md has the AI-SDD Instructions section"    "## AI-SDD Instructions" "$PROJ/CLAUDE.md"
assert_count     "CLAUDE.md has exactly one AI-SDD section"         1 "## AI-SDD Instructions" "$PROJ/CLAUDE.md"
assert_grep      "CLAUDE.md points to the rules file"               "ai-sdd-instructions.md" "$PROJ/CLAUDE.md"
assert_not_grep  "CLAUDE.md omits the naming quick-reference body"  "Naming Pattern Quick Reference" "$PROJ/CLAUDE.md"
assert_not_grep  "CLAUDE.md omits the detailed naming table"        '_design` suffix required'       "$PROJ/CLAUDE.md"

# ---------------------------------------------------------------------------
# STEP 3: Legacy per-language file cleanup on language switch
# ---------------------------------------------------------------------------
printf -- '--- STEP 3: legacy cleanup + language switch ---\n'
printf 'legacy stale content\n' > "$PROJ/$LEGACY_REL"
python3 - "$PROJ/.sdd-config.json" <<'PY'
import json, sys
p = sys.argv[1]
with open(p, encoding="utf-8") as f:
    d = json.load(f)
d["lang"] = "ja"
with open(p, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY
if ! run_session_start en; then fail "session-start.py (after switch) exited non-zero"; fi
assert_file      "rules file still present after switch"            "$PROJ/$RULES_REL"
assert_no_file   "legacy per-language rules file is removed"        "$PROJ/$LEGACY_REL"
assert_grep      "rules file stays a single English file"           'AI-driven Specification-Driven Development' "$PROJ/$RULES_REL"

# ---------------------------------------------------------------------------
# STEP 4: Idempotency (re-run must not change any managed file)
# ---------------------------------------------------------------------------
printf -- '--- STEP 4: idempotency ---\n'
cp "$PROJ/$RULES_REL" "${TMP_DIR}/rules_before"
cp "$PROJ/CLAUDE.md"  "${TMP_DIR}/claude_before"
if ! run_session_start en; then fail "session-start.py (re-run) exited non-zero"; fi
if ! run_update_claude_md; then fail "update-claude-md.sh (re-run) exited non-zero"; fi
assert_same      "rules file is unchanged on re-run"                "${TMP_DIR}/rules_before" "$PROJ/$RULES_REL"
assert_same      "CLAUDE.md is unchanged on re-run"                 "${TMP_DIR}/claude_before" "$PROJ/CLAUDE.md"
assert_count     "CLAUDE.md still has exactly one AI-SDD section"   1 "## AI-SDD Instructions" "$PROJ/CLAUDE.md"

# ---------------------------------------------------------------------------
# STEP 5: Custom root (.sdd-config.json "root") is honored in generated files
# ---------------------------------------------------------------------------
printf -- '--- STEP 5: custom root (.ai-docs) is honored ---\n'
PROJ2="${TMP_DIR}/project-customroot"
ENV2="${TMP_DIR}/env2"
mkdir -p "$PROJ2"
: > "$ENV2"
printf '%s\n' '{"root":".ai-docs","lang":"en","directories":{"requirement":"requirement","specification":"specification","task":"task"}}' > "$PROJ2/.sdd-config.json"

if ! CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" CLAUDE_PROJECT_DIR="$PROJ2" CLAUDE_ENV_FILE="$ENV2" \
        python3 "$SESSION_START" --default-lang en >/dev/null 2>&1; then
    fail "session-start.py (custom root) exited non-zero"
fi
assert_grep      "rule paths glob uses the custom root"             '".ai-docs/**"'          "$PROJ2/$RULES_REL"
assert_not_grep  "rule paths glob has no default-root glob"         '".sdd/**"'              "$PROJ2/$RULES_REL"
assert_not_grep  "rule has no leftover {SDD_ROOT} placeholder"      '{SDD_ROOT}'             "$PROJ2/$RULES_REL"

if ! CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" CLAUDE_PROJECT_DIR="$PROJ2" CLAUDE_ENV_FILE="$ENV2" \
        bash "$UPDATE_CLAUDE_MD" >/dev/null 2>&1; then
    fail "update-claude-md.sh (custom root) exited non-zero"
fi
assert_grep      "CLAUDE.md references the custom root"             ".ai-docs/"              "$PROJ2/CLAUDE.md"
assert_not_grep  "CLAUDE.md has no leftover {SDD_ROOT} placeholder" '{SDD_ROOT}'             "$PROJ2/CLAUDE.md"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
printf '\n=== Results: %d passed, %d failed ===\n' "$PASS_COUNT" "$FAIL_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi

exit 0
