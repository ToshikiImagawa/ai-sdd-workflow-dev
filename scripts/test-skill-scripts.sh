#!/bin/sh
# test-skill-scripts.sh
# Regression test for the skill helper scripts that pre-scan files into a cache:
#   plugins/sdd-workflow/skills/check-spec/scripts/find-design-docs.sh
#   plugins/sdd-workflow/skills/constitution/scripts/validate-files.sh
#   plugins/sdd-workflow/skills/recommend-front-matter/scripts/scan-documents.py
#
# Both derive their cache directory from the configured SDD root
# (.sdd-config.json "root"). This test runs them under a NON-default root and
# verifies they honor it end to end:
#   - the cache dir is created under <root>/.cache/... (never a bare .sdd/)
#   - the scan output files land under that cache dir
#   - CLAUDE_ENV_FILE exports point at the configured cache path
# A regression back to a hardcoded ".sdd" would fail these assertions.
#
# POSIX compatible (macOS bash 3.2 / dash).

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_ROOT="${REPO_ROOT}/plugins/sdd-workflow"

FIND_DESIGN="${PLUGIN_ROOT}/skills/check-spec/scripts/find-design-docs.sh"
VALIDATE_FILES="${PLUGIN_ROOT}/skills/constitution/scripts/validate-files.sh"
SCAN_DOCUMENTS="${PLUGIN_ROOT}/skills/recommend-front-matter/scripts/scan-documents.py"

# Non-default custom root; both scripts must derive every path from this.
ROOT=".ai-docs"

PASS_COUNT=0
FAIL_COUNT=0

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

# Isolated temp workspace
TMP_DIR="$(mktemp -d)"
cleanup_on_exit() {
    if [ -n "${TMP_DIR:-}" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
}
trap cleanup_on_exit EXIT

PROJ="${TMP_DIR}/project"
mkdir -p "$PROJ/${ROOT}/requirement" "$PROJ/${ROOT}/specification"
printf '%s\n' "{\"root\":\"${ROOT}\",\"lang\":\"en\",\"directories\":{\"requirement\":\"requirement\",\"specification\":\"specification\",\"task\":\"task\"}}" > "$PROJ/.sdd-config.json"

# Seed documents so the scans have something to find.
printf '# design\n' > "$PROJ/${ROOT}/specification/user-login_design.md"
printf '# spec\n'   > "$PROJ/${ROOT}/specification/user-login_spec.md"
printf '# prd\n'    > "$PROJ/${ROOT}/requirement/user-login.md"

ENV_FILE="${TMP_DIR}/env_output"
: > "$ENV_FILE"

FD_CACHE="$PROJ/${ROOT}/.cache/check-spec"
VF_CACHE="$PROJ/${ROOT}/.cache/constitution"
SD_CACHE="$PROJ/${ROOT}/.cache/recommend-front-matter"

printf '=== skill helper scripts custom-root regression (root=%s) ===\n\n' "$ROOT"

# ---------------------------------------------------------------------------
# find-design-docs.sh (/check-spec)
# ---------------------------------------------------------------------------
printf -- '--- find-design-docs.sh ---\n'
if ! CLAUDE_PROJECT_DIR="$PROJ" CLAUDE_ENV_FILE="$ENV_FILE" bash "$FIND_DESIGN" >/dev/null 2>&1; then
    fail "find-design-docs.sh exited non-zero"
fi
assert_file      "find-design-docs writes design_files.txt under the custom root" "$FD_CACHE/design_files.txt"
assert_file      "find-design-docs writes spec_files.txt under the custom root"   "$FD_CACHE/spec_files.txt"
assert_file      "find-design-docs writes file_mapping.json under the custom root" "$FD_CACHE/file_mapping.json"
assert_no_file   "find-design-docs creates no bare .sdd/ directory"               "$PROJ/.sdd"
assert_grep      "design_files.txt lists the seeded design doc"                   "user-login_design.md" "$FD_CACHE/design_files.txt"
assert_grep      "env exports CHECK_SPEC_CACHE_DIR"                               "CHECK_SPEC_CACHE_DIR"  "$ENV_FILE"
assert_grep      "CHECK_SPEC_CACHE_DIR points under the custom root"              "${ROOT}/.cache/check-spec" "$ENV_FILE"

# ---------------------------------------------------------------------------
# validate-files.sh (/constitution validate)
# ---------------------------------------------------------------------------
printf -- '--- validate-files.sh ---\n'
if ! CLAUDE_PROJECT_DIR="$PROJ" CLAUDE_ENV_FILE="$ENV_FILE" bash "$VALIDATE_FILES" >/dev/null 2>&1; then
    fail "validate-files.sh exited non-zero"
fi
assert_file      "validate-files writes requirement_files.txt under the custom root" "$VF_CACHE/requirement_files.txt"
assert_file      "validate-files writes spec_files.txt under the custom root"        "$VF_CACHE/spec_files.txt"
assert_file      "validate-files writes design_files.txt under the custom root"      "$VF_CACHE/design_files.txt"
assert_file      "validate-files writes scan_summary.json under the custom root"     "$VF_CACHE/scan_summary.json"
assert_no_file   "validate-files creates no bare .sdd/ directory"                    "$PROJ/.sdd"
assert_grep      "env exports CONSTITUTION_CACHE_DIR"                                "CONSTITUTION_CACHE_DIR" "$ENV_FILE"
assert_grep      "CONSTITUTION_CACHE_DIR points under the custom root"               "${ROOT}/.cache/constitution" "$ENV_FILE"

# ---------------------------------------------------------------------------
# scan-documents.py (/recommend-front-matter)
# ---------------------------------------------------------------------------
printf -- '--- scan-documents.py ---\n'
if ! CLAUDE_PROJECT_DIR="$PROJ" CLAUDE_ENV_FILE="$ENV_FILE" python3 "$SCAN_DOCUMENTS" >/dev/null 2>&1; then
    fail "scan-documents.py exited non-zero"
fi
assert_file      "scan-documents writes scan_result.json under the custom root"   "$SD_CACHE/scan_result.json"
assert_no_file   "scan-documents creates no bare .sdd/ directory"                 "$PROJ/.sdd"
assert_grep      "scan_result.json lists the seeded design doc"                   "user-login_design.md" "$SD_CACHE/scan_result.json"
assert_grep      "env exports RECOMMEND_FM_CACHE_DIR"                             "RECOMMEND_FM_CACHE_DIR" "$ENV_FILE"
assert_grep      "RECOMMEND_FM_CACHE_DIR points under the custom root"            "${ROOT}/.cache/recommend-front-matter" "$ENV_FILE"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
printf '\n=== Results: %d passed, %d failed ===\n' "$PASS_COUNT" "$FAIL_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi

exit 0
