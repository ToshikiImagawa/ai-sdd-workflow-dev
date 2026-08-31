#!/bin/sh
# plugin-lint.sh
# Shell script version of .claude/skills/plugin-lint/SKILL.md checks
# POSIX compatible (macOS bash 3.2 / dash)
# Uses temp files for counters to avoid subshell variable scoping issues

set -e

# Resolve script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PLUGIN_DIR="${REPO_ROOT}/plugins/sdd-workflow"

# Temp files for counters (avoids subshell scoping issues with pipes)
TMP_DIR="$(mktemp -d)"
WARN_FILE="${TMP_DIR}/warn_count"
ERROR_FILE="${TMP_DIR}/error_count"
FENCE_FILE="${TMP_DIR}/fence_state"
printf '0' > "$WARN_FILE"
printf '0' > "$ERROR_FILE"
printf '0' > "$FENCE_FILE"

# shellcheck disable=SC2329
cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

# Colors (only if terminal supports it)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

# Note: Counter updates via temp files are not atomic, but safe because
# callers (pipe subshells) run sequentially within each pipeline.
log_warn() {
    printf '%sWARN%s %s\n' "$YELLOW" "$NC" "$1"
    count=$(cat "$WARN_FILE")
    printf '%d' "$((count + 1))" > "$WARN_FILE"
}

log_error() {
    printf '%sERROR%s %s\n' "$RED" "$NC" "$1"
    count=$(cat "$ERROR_FILE")
    printf '%d' "$((count + 1))" > "$ERROR_FILE"
}

log_ok() {
    printf '%sOK%s %s\n' "$GREEN" "$NC" "$1"
}

# ============================================================
# Check 1: Code Block Detection in Prompt Markdown (warning only)
# ============================================================
printf "=== Check 1: Code Block Detection ===\n\n"

check1_found=0

# Report only opening fences: a closing ``` is the same block, not a second one.
warn_code_blocks() {
    f="$1"
    matches=$(grep -n '^```' "$f" 2>/dev/null || true)
    [ -n "$matches" ] || return 1
    relpath="${f#"$REPO_ROOT"/}"
    echo "$matches" | while IFS= read -r line; do
        in_block="$(cat "$FENCE_FILE")"
        if [ "$in_block" -eq 1 ]; then
            printf '0' > "$FENCE_FILE"
            continue
        fi
        printf '1' > "$FENCE_FILE"
        lineno="${line%%:*}"
        content="${line#*:}"
        block_type=$(echo "$content" | sed 's/^```[[:space:]]*//' | sed 's/[[:space:]].*//')
        [ -z "$block_type" ] && block_type="plain"
        log_warn "${relpath}:${lineno} - code block (${block_type})"
    done
    return 0
}

# Check agents/*.md and skills/*/SKILL.md
# (templates/, examples/, references/ are support files and stay out of scope)
for f in "$PLUGIN_DIR"/agents/*.md "$PLUGIN_DIR"/skills/*/SKILL.md; do
    [ -f "$f" ] || continue
    printf '0' > "$FENCE_FILE"
    if warn_code_blocks "$f"; then
        check1_found=1
    fi
done

if [ "$check1_found" -eq 0 ]; then
    log_ok "No code blocks found in prompt Markdown files"
fi
printf "\n"

# ============================================================
# Check 2: Support File Structure Validation (error on failure)
# ============================================================
printf "=== Check 2: Support File Structure ===\n\n"

ALLOWED_DIRS="templates examples references scripts"

for skill_dir in "$PLUGIN_DIR"/skills/*/; do
    [ -d "$skill_dir" ] || continue
    skill_name="$(basename "$skill_dir")"

    # --- 2.1 Directory Name Accuracy ---
    for entry in "$skill_dir"*/; do
        [ -d "$entry" ] || continue
        dir_name="$(basename "$entry")"
        found=0
        for allowed in $ALLOWED_DIRS; do
            if [ "$dir_name" = "$allowed" ]; then
                found=1
                break
            fi
        done
        if [ "$found" -eq 0 ]; then
            log_error "skills/${skill_name}/${dir_name}/ - unexpected directory (allowed: ${ALLOWED_DIRS})"
        fi
    done

    # Also check for unexpected files (not SKILL.md, not README.md, not directories)
    for entry in "$skill_dir"*; do
        [ -e "$entry" ] || continue
        [ -d "$entry" ] && continue
        fname="$(basename "$entry")"
        if [ "$fname" != "SKILL.md" ] && [ "$fname" != "README.md" ]; then
            log_error "skills/${skill_name}/${fname} - unexpected file at skill root (only SKILL.md and README.md allowed)"
        fi
    done

    # --- 2.2 File Name Convention (snake_case) ---
    for sub_dir in templates examples references; do
        check_dir="${skill_dir}${sub_dir}"
        [ -d "$check_dir" ] || continue
        find "$check_dir" -type f | while IFS= read -r filepath; do
            fname="$(basename "$filepath")"
            if ! echo "$fname" | grep -qE '^[a-z0-9_]+\.[a-z]+$'; then
                relpath="${filepath#"$REPO_ROOT"/}"
                log_error "${relpath} - filename not snake_case (expected: ^[a-z0-9_]+\\.[a-z]+$)"
            fi
        done
    done

    # --- 2.3 Language Directory Completeness ---
    templates_dir="${skill_dir}templates"
    if [ -d "$templates_dir" ]; then
        has_en=0
        has_ja=0
        [ -d "${templates_dir}/en" ] && has_en=1
        [ -d "${templates_dir}/ja" ] && has_ja=1

        if [ "$has_en" -eq 0 ]; then
            log_error "skills/${skill_name}/templates/ - missing en/ directory"
        fi
        if [ "$has_ja" -eq 0 ]; then
            log_error "skills/${skill_name}/templates/ - missing ja/ directory"
        fi

        # --- 2.4 Language File Set Consistency ---
        if [ "$has_en" -eq 1 ] && [ "$has_ja" -eq 1 ]; then
            en_files="$(cd "${templates_dir}/en" && find . -type f | sort)"
            ja_files="$(cd "${templates_dir}/ja" && find . -type f | sort)"

            if [ "$en_files" != "$ja_files" ]; then
                echo "$en_files" | while IFS= read -r f; do
                    [ -z "$f" ] && continue
                    if ! echo "$ja_files" | grep -qFx "$f"; then
                        log_error "skills/${skill_name}/templates/ - file ${f#./} exists in en/ but not in ja/"
                    fi
                done
                echo "$ja_files" | while IFS= read -r f; do
                    [ -z "$f" ] && continue
                    if ! echo "$en_files" | grep -qFx "$f"; then
                        log_error "skills/${skill_name}/templates/ - file ${f#./} exists in ja/ but not in en/"
                    fi
                done
            else
                log_ok "skills/${skill_name}/templates/ - en/ and ja/ file sets match"
            fi
        fi
    fi

    # --- 2.5 Support File Extension (.md required for templates/ and references/) ---
    for sub_dir in templates references; do
        check_dir="${skill_dir}${sub_dir}"
        [ -d "$check_dir" ] || continue
        find "$check_dir" -type f | while IFS= read -r filepath; do
            fname="$(basename "$filepath")"
            ext="${fname##*.}"
            if [ "$ext" != "md" ]; then
                relpath="${filepath#"$REPO_ROOT"/}"
                log_error "${relpath} - extension .${ext} not allowed (expected: .md)"
            fi
        done
    done
done

# --- 2.6 shared/ support files follow the same naming and extension rules ---
# shared/references/ is reachable from skills and agents via symlink, so it is
# subject to the same conventions as a skill's own support files.
if [ -d "$PLUGIN_DIR/shared" ]; then
    find "$PLUGIN_DIR/shared" -type f | while IFS= read -r filepath; do
        fname="$(basename "$filepath")"
        relpath="${filepath#"$REPO_ROOT"/}"
        if ! echo "$fname" | grep -qE '^[a-z0-9_]+\.[a-z]+$'; then
            log_error "${relpath} - filename not snake_case (expected: ^[a-z0-9_]+\\.[a-z]+$)"
        fi
        ext="${fname##*.}"
        if [ "$ext" != "md" ]; then
            log_error "${relpath} - extension .${ext} not allowed (expected: .md)"
        fi
    done
fi

# ============================================================
# Check 3: SDD Path Token Hygiene (error on failure)
# ============================================================
printf "=== Check 3: SDD Path Token Hygiene ===\n\n"

# Keep in sync with session-start.py write_env_vars() (the SessionStart hook is
# the only thing that resolves these ${SDD_*} tokens at runtime).
ALLOWED_SDD_VARS="SDD_ROOT SDD_LANG SDD_INDEX SDD_REQUIREMENT_DIR SDD_SPECIFICATION_DIR SDD_ADR_DIR SDD_TASK_DIR SDD_REQUIREMENT_PATH SDD_SPECIFICATION_PATH SDD_ADR_PATH SDD_TASK_PATH"

check3_errors_before="$(cat "$ERROR_FILE")"

# --- 3.1 Every ${SDD_*} token in prompt Markdown must be an exported var ---
# A typo like ${SDD_SPEC_PATH} would silently never resolve at runtime.
find "$PLUGIN_DIR" -type f -name '*.md' | while IFS= read -r f; do
    grep -oE '\$\{SDD_[A-Za-z_]+\}' "$f" 2>/dev/null | while IFS= read -r token; do
        var_name=$(printf '%s' "$token" | sed -e 's/^\${//' -e 's/}$//')
        allowed=0
        for allow in $ALLOWED_SDD_VARS; do
            if [ "$var_name" = "$allow" ]; then
                allowed=1
                break
            fi
        done
        if [ "$allowed" -eq 0 ]; then
            relpath="${f#"$REPO_ROOT"/}"
            log_error "${relpath} - unknown SDD token \${${var_name}} (not exported by session-start.py write_env_vars)"
        fi
    done
done

# --- 3.2 skills/*/templates/ must not hardcode a default-root SDD path ---
# Templates are resolved per-project, so they must use ${SDD_*_PATH} tokens.
# (examples/ and references/ may keep literal paths for illustration.)
for skill_dir in "$PLUGIN_DIR"/skills/*/; do
    [ -d "$skill_dir" ] || continue
    templates_dir="${skill_dir}templates"
    [ -d "$templates_dir" ] || continue
    find "$templates_dir" -type f -name '*.md' | while IFS= read -r f; do
        if grep -qE '\.sdd/(specification|requirement|adr|task)' "$f" 2>/dev/null; then
            relpath="${f#"$REPO_ROOT"/}"
            log_error "${relpath} - hardcoded .sdd/ path in a template (use \${SDD_*_PATH} tokens so custom roots resolve)"
        fi
    done
done

if [ "$(cat "$ERROR_FILE")" -eq "$check3_errors_before" ]; then
    log_ok "All \${SDD_*} tokens are exported vars; no hardcoded .sdd/ paths in templates/"
fi
printf "\n"

# ============================================================
# Check 4: Plugin Manifest Hygiene (error on failure)
# ============================================================
printf "=== Check 4: Plugin Manifest Hygiene ===\n\n"

# Manifest component-path fields behave in three different ways, so "register
# everything" is not a safe rule (CONSTITUTION T-002 v2.0.0):
#   agents -> REPLACES the default agents/ scan, so an unlisted agent file is
#             never loaded. Registration is mandatory.
#   skills -> ADDS to the default skills/ scan. skills/ is always scanned, so
#             declaring "./skills" is redundant.
#   hooks  -> SUPPLEMENTS the default path. Declaring the standard
#             hooks/hooks.json loads the same file twice and the loader rejects
#             it with "Duplicate hooks file detected".
check4_errors_before="$(cat "$ERROR_FILE")"

PLUGIN_MANIFEST="${PLUGIN_DIR}/.claude-plugin/plugin.json"
MANIFEST_REL="plugins/sdd-workflow/.claude-plugin/plugin.json"
if [ -f "$PLUGIN_MANIFEST" ]; then
    manifest_hooks="$(jq -r '.hooks // empty' "$PLUGIN_MANIFEST")"
    if [ "$manifest_hooks" = "./hooks/hooks.json" ]; then
        log_error "${MANIFEST_REL} - \"hooks\" declares the standard path ./hooks/hooks.json (auto-detected; declaring it causes a duplicate hooks load)"
    fi

    manifest_skills="$(jq -r 'if .skills == null then empty elif (.skills | type) == "array" then .skills[] else .skills end' "$PLUGIN_MANIFEST")"
    echo "$manifest_skills" | while IFS= read -r skills_path; do
        [ -z "$skills_path" ] && continue
        if [ "$skills_path" = "./skills" ] || [ "$skills_path" = "skills" ]; then
            log_error "${MANIFEST_REL} - \"skills\" declares the standard path ${skills_path} (always scanned; the declaration is redundant per T-002)"
        fi
    done

    if [ "$(jq -r '.agents // empty | length' "$PLUGIN_MANIFEST")" = "" ]; then
        log_error "${MANIFEST_REL} - \"agents\" is missing (this field REPLACES the default agents/ scan, so unlisted agents are never loaded)"
    fi
fi

# --- 4.2 agents/ holds nothing but agent definitions ---
# `claude plugin validate --strict` scans agents/** recursively and ignores the
# manifest's agents array, so any support file parked under agents/ is reported
# as an agent with no frontmatter and fails the run. This reproduces that
# invariant without depending on the Claude Code CLI being installed in CI.
for entry in "$PLUGIN_DIR"/agents/*/; do
    [ -d "$entry" ] || continue
    log_error "plugins/sdd-workflow/agents/$(basename "$entry")/ - agents/ must contain only agent definitions (support files belong in shared/; \`plugin validate --strict\` scans agents/** recursively)"
done

for f in "$PLUGIN_DIR"/agents/*.md; do
    [ -f "$f" ] || continue
    if [ "$(head -n 1 "$f")" != "---" ]; then
        log_error "${f#"$REPO_ROOT"/} - agent file has no front matter block (rejected by \`plugin validate --strict\`)"
    fi
done

if [ "$(cat "$ERROR_FILE")" -eq "$check4_errors_before" ]; then
    log_ok "plugin.json registers agents, leaves skills/hooks to auto-detection, and agents/ holds only agent definitions"
fi
printf "\n"

# ============================================================
# Check 5: Front Matter Key Hygiene (error on failure)
# ============================================================
printf "=== Check 5: Front Matter Key Hygiene ===\n\n"

# These keys fail silently when misused - no error, no warning, the declaration
# is simply ignored - so only a lint check catches them:
#   - subagents accept `tools:` / `disallowedTools:`. `allowed-tools:` is a
#     skill-only key; on an agent it is ignored and the agent inherits ALL tools.
#   - a skill's `agent:` selects a SUBAGENT TYPE and only applies with
#     `context: fork`. A model alias there falls back to general-purpose;
#     model selection belongs in `model:`.
#   - an unquoted ${CLAUDE_PLUGIN_ROOT} breaks every hook once the install path
#     contains a space.
MODEL_ALIASES="sonnet haiku opus fable inherit"

check5_errors_before="$(cat "$ERROR_FILE")"

# --- 5.1 agents must not use the skill-only allowed-tools key ---
for f in "$PLUGIN_DIR"/agents/*.md; do
    [ -f "$f" ] || continue
    relpath="${f#"$REPO_ROOT"/}"
    lineno=$(awk 'NR==1 && $0=="---"{f=1;next} f&&$0=="---"{exit} f&&/^allowed-tools:/{print NR;exit}' "$f")
    if [ -n "$lineno" ]; then
        log_error "${relpath}:${lineno} - subagents ignore \"allowed-tools\" (use \"tools\"; otherwise the agent inherits all tools)"
    fi
done

# --- 5.2 skills must not put a model alias in agent:, nor set agent: without fork ---
for f in "$PLUGIN_DIR"/skills/*/SKILL.md; do
    [ -f "$f" ] || continue
    relpath="${f#"$REPO_ROOT"/}"
    front_matter=$(awk 'NR==1 && $0=="---"{f=1;next} f&&$0=="---"{exit} f{print}' "$f")
    agent_val=$(echo "$front_matter" | sed -n 's/^agent:[[:space:]]*//p')
    [ -z "$agent_val" ] && continue

    for alias in $MODEL_ALIASES; do
        if [ "$agent_val" = "$alias" ]; then
            log_error "${relpath} - \"agent: ${agent_val}\" names a model, but agent: selects a subagent type (use \"model: ${agent_val}\")"
            break
        fi
    done
    case "$agent_val" in
        claude-*)
            log_error "${relpath} - \"agent: ${agent_val}\" names a model, but agent: selects a subagent type (use \"model:\")"
            ;;
    esac

    if ! echo "$front_matter" | grep -qE '^context:[[:space:]]*fork[[:space:]]*$'; then
        log_error "${relpath} - \"agent: ${agent_val}\" has no effect without \"context: fork\""
    fi
done

# --- 5.3 hook commands must quote ${CLAUDE_PLUGIN_ROOT} ---
HOOKS_FILE="${PLUGIN_DIR}/hooks/hooks.json"
if [ -f "$HOOKS_FILE" ]; then
    jq -r '.hooks | to_entries[] | .value[] | .hooks[]? | .command // empty' "$HOOKS_FILE" \
        | while IFS= read -r cmd; do
            [ -z "$cmd" ] && continue
            case "$cmd" in
                *'"${CLAUDE_PLUGIN_ROOT}'*) ;;
                *'${CLAUDE_PLUGIN_ROOT}'*)
                    log_error "plugins/sdd-workflow/hooks/hooks.json - unquoted \${CLAUDE_PLUGIN_ROOT} in: ${cmd} (breaks when the install path contains a space)"
                    ;;
            esac
        done
fi

# --- 5.4 skills must not pre-approve write or shell access wholesale ---
# A skill's allowed-tools grants tools *without asking* - it is a pre-approval,
# not a restriction. A bare `Write`/`Edit` pre-approves writing anywhere, and a
# bare `Bash` pre-approves any command. Both must be narrowed with a specifier:
# `Edit(.sdd/**)` for writes (the `Write(path)` form is not honoured by file
# permission checks) and `Bash(python3 "${CLAUDE_PLUGIN_ROOT}/..." *)` for the
# plugin's own scripts. An over-tight scope only costs a permission prompt.
for f in "$PLUGIN_DIR"/skills/*/SKILL.md; do
    [ -f "$f" ] || continue
    relpath="${f#"$REPO_ROOT"/}"
    tools_line=$(awk 'NR==1 && $0=="---"{f=1;next} f&&$0=="---"{exit} f&&/^allowed-tools:/{sub(/^allowed-tools:[[:space:]]*/,"");print;exit}' "$f")
    [ -z "$tools_line" ] && continue
    echo "$tools_line" | tr ',' '\n' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
        | while IFS= read -r tool; do
            case "$tool" in
                Write|Edit)
                    log_error "${relpath} - \"allowed-tools\" pre-approves bare ${tool} (writing anywhere); scope it, e.g. Edit(.sdd/**)"
                    ;;
                Bash)
                    log_error "${relpath} - \"allowed-tools\" pre-approves bare Bash (any command); scope it, e.g. Bash(python3 \"\${CLAUDE_PLUGIN_ROOT}/skills/<name>/scripts/<script>.py\" *)"
                    ;;
            esac
        done
done

if [ "$(cat "$ERROR_FILE")" -eq "$check5_errors_before" ]; then
    log_ok "agents use tools:, skills keep model selection in model: and scope write/shell pre-approval, hook commands quote \${CLAUDE_PLUGIN_ROOT}"
fi
printf "\n"

# ============================================================
# Summary
# ============================================================
WARN_COUNT=$(cat "$WARN_FILE")
ERROR_COUNT=$(cat "$ERROR_FILE")

printf "\n=== Summary ===\n"
printf "Warnings: %d (code blocks in prompts)\n" "$WARN_COUNT"
printf "Errors:   %d (structure violations)\n" "$ERROR_COUNT"

if [ "$ERROR_COUNT" -gt 0 ]; then
    printf '\n%sFAILED%s - %d error(s) found\n' "$RED" "$NC" "$ERROR_COUNT"
    exit 1
fi

printf '\n%sPASSED%s - plugin lint checks completed\n' "$GREEN" "$NC"
exit 0
