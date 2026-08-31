---
name: doc-consistency-checker
description: "Automatically executed during document updates or before implementation to check consistency between PRD ↔ *_spec.md ↔ adr/*-decisions.md. Detects missing requirement ID (UR/FR/NFR) references, data model mismatches, API definition discrepancies, terminology inconsistencies, PRD-contradicting spec changes, and ensures traceability between documents."
argument-hint: "[feature-name]"
license: MIT
user-invocable: false
allowed-tools: Read, Glob, Grep
disallowed-tools: Write, Edit, Bash
---

# Doc Consistency Checker - Document Consistency Check

Automatically checks consistency between AI-SDD documents (PRD, `*_spec.md`, `adr/*-decisions.md`) and detects inconsistencies.

## Language Configuration

!`echo "Current language: ${SDD_LANG:-en}"`

When reading templates, use the path: `templates/${SDD_LANG:-en}/`

## Prerequisites

**Before execution, read the AI-SDD principles document.**

AI-SDD principles document path: `${CLAUDE_PROJECT_DIR}/${SDD_ROOT}/AI-SDD-PRINCIPLES.md`

**Note**: This file is automatically updated at the start of each session.

Understand AI-SDD principles, document structure, persistence rules, and Vibe Coding prevention details.

See `references/prerequisites_directory_paths.md` for directory path resolution using `SDD_*` environment variables.

### Index Fast Path

When `SDD_INDEX` is `on`, a pre-built compressed index exists at `${SDD_ROOT}/.cache/index.md`.
Read it **once** and use all its tables (`Metadata`, `Requirement IDs`, `SysML Relationships`,
`Data Models`, `API Signatures`) for cross-document consistency checks. This replaces
the need for multiple Glob/Grep/Read calls across `.sdd/`. Fall back to raw Read of a specific file
only when cross-reference verification requires full section text. When `SDD_INDEX` is unset or `off`,
use the existing Glob/Grep/Read flow.

## Input

This skill is triggered by an advisory hint from the `PostToolUse` hook (`scripts/post-tool-use.py`) when
files under `${SDD_REQUIREMENT_PATH}` or `${SDD_SPECIFICATION_PATH}` are edited. It scans documents based on
feature context.

| Input Source       | Description                                                    |
|:-------------------|:---------------------------------------------------------------|
| Feature context    | Current feature being worked on (from task or document update) |
| Document paths     | Automatically resolved from `${SDD_*}` environment variables   |

**Note**: This skill is `user-invocable: false` and cannot be called directly. Use `/check-spec` for manual consistency checks.

## Document Dependencies

See `references/document_dependencies.md` for the document dependency chain and direction meaning.

**⚠️ Known gap**: This shared reference (also used by other skills) has not yet been migrated to the `adr/`
model as of this writing — it still describes `specification/*_design.md` as persistent and does not mention
`adr/`. Until it is updated, treat the check targets and persistence rules defined in this file (`SKILL.md`) as
authoritative for this skill's own checks.

## Directory Structure Support

Both flat and hierarchical structures are supported. See `references/directory_structure.md` for the
flat and hierarchical directory layouts.

**⚠️ Note the difference in naming conventions**:

| Directory         | Naming Pattern                      | Examples                                        |
|:------------------|:-------------------------------------|:-------------------------------------------------|
| **requirement**   | No suffix                            | `index.md`, `user-login.md`                     |
| **specification** | `_spec` required                     | `index_spec.md`, `user-login_spec.md`           |
| **adr**           | `-decisions` required (append-only)  | `index-decisions.md`, `user-login-decisions.md` |

Consistency checks also consider parent-child relationships for hierarchical structures.

## Check Items

### 0. Front Matter Cross-Reference Consistency

**Note**: Detailed front matter validation (common checks, type-specific checks, cross-reference checks) is handled by the `front-matter-reviewer` agent. The caller should invoke `front-matter-reviewer --cross-ref` separately when full front matter validation is needed.

This skill focuses on document content consistency only.

### 1. PRD ↔ spec Consistency

| Check Item                                 | Description                                                                                                                   |
|:--------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------|
| **Requirement ID Mapping**                  | Are PRD requirement IDs referenced in spec?                                                                                    |
| **Functional Requirement Coverage**         | Are PRD functional requirements covered in spec?                                                                               |
| **Non-Functional Requirement Reflection**   | Are PRD non-functional requirements reflected in spec?                                                                         |
| **Terminology Consistency**                 | Is same terminology used in PRD and spec?                                                                                      |
| **PRD Contradiction / Uncovered Behavior**  | Does a spec change contradict a PRD requirement (FR-xxx, NFR-xxx, etc.), or introduce new behavior no PRD requirement covers?  |

**⚠️ The PRD is a record of human business decisions and must never be auto-updated by this check.** When the
"PRD Contradiction / Uncovered Behavior" item finds a contradiction or an uncovered new behavior, always report
it as `[must]` and stop short of editing the PRD. Present the conflicting spec change and the affected PRD
requirement, and let a human decide whether to update the PRD, revert the spec change, or accept it as an
intentional scope change. This mirrors the `task-cleanup` skill's rule for `*_spec.md` updates — see
`task-cleanup/SKILL.md` ("Do not edit `*_spec.md` automatically"); the trigger conditions themselves are listed
in `AI-SDD-PRINCIPLES.md` § Document Update Triggers. The same non-automation principle applies one level up,
from spec to PRD.

**`prd-reviewer` handoff timing**: This skill only detects and reports (its `allowed-tools` is read-only). Once
a human approves a PRD edit for a `[must]` PRD-contradiction finding, the calling agent should invoke
`prd-reviewer` against the updated PRD — the same way `generate-prd` does after PRD generation. Do not call it
before the human approves the edit.

### 2. spec ↔ adr Consistency

| Check Item                    | Description                                                                                                             |
|:---------------------------------|:----------------------------------------------------------------------------------------------------------------------------|
| **Decision Traceability**        | Are spec-driving decisions (API shape, data model choices) captured in `adr/*-decisions.md`?                              |
| **Referenced Spec Still Valid**  | Do adr entries reference spec elements (API, data model, requirement IDs) that still exist in the current spec?          |
| **Terminology Consistency**      | Is the same terminology used in spec and adr?                                                                             |
| **Obsolescence Detection**       | Does an adr entry describe a decision about spec elements that were since changed or removed, with no follow-up entry?   |

**Note — out of scope for this skill**:

- `task/{ticket-number}/design-draft.md` consistency with `*_spec.md`, and its integration into
  `adr/*-decisions.md` before deletion, are checked by the `task-cleanup` skill at cleanup time (see
  `AI-SDD-PRINCIPLES.md`)
- `spec <-> Implementation` and any remaining `*_design.md` artifact checks (module structure, interface
  definitions, technology stack) are checked by `/check-spec` (the `impl-spec-check` feature)

This skill checks the **persisted** artifacts only: `*_spec.md` and `adr/*-decisions.md`.

## Automatic Detection Patterns

### Inconsistency Detection

1. **Missing**: Exists in upstream document but not reflected in downstream
2. **Contradiction**: Different content described in upstream and downstream
3. **Obsolescence**: Downstream changes not reflected in upstream

### Detection Method

See `references/detection_method.md` for the step-by-step detection procedure.

## Output Format

Read `templates/${SDD_LANG:-en}/consistency_report.md` and use it for consistency check output.

## Check Execution Timing

| Timing                        | Recommended Check                                                                             |
|:-------------------------------|:-----------------------------------------------------------------------------------------------|
| **Task Start**                | Verify existing document (PRD, spec, adr) existence and consistency                           |
| **Spec Update**               | PRD ↔ spec consistency (including PRD-contradiction / uncovered-behavior detection) and spec ↔ adr consistency |
| **Implementation Completion** | design-draft ↔ adr integration and spec-update-trigger judgment — handled by `task-cleanup`, not this skill |
| **Review**                    | All inter-document consistency (PRD ↔ spec ↔ adr)                                             |
| **Periodic Check**            | Prevent documentation obsolescence                                                             |

## Document Update Triggers

Based on consistency check results, recommend document updates in the following cases:

### When to Update `*_spec.md`

- Public API signature changes (arguments, return values, types)
- New data model additions
- Fundamental changes to existing behavior
- When new requirements added in requirements diagram

### When a PRD Update Should Be Proposed (never applied automatically)

- A spec change contradicts an existing PRD requirement (FR-xxx, NFR-xxx, etc.)
- A spec change introduces new behavior that no PRD requirement covers

See "PRD ↔ spec Consistency" above for how to report and handle this. This skill never edits `requirement/`
files itself.

### When to Append to `adr/{feature}-decisions.md`

Owned by the `task-cleanup` skill at implementation-completion time, not by this skill — see
`AI-SDD-PRINCIPLES.md` § Document Update Triggers for the trigger conditions.

### When Updates Are NOT Needed

- Internal implementation optimization (no interface changes)
- Bug fixes (correcting deviations from specifications)
- Refactoring (no behavior changes)

## Notes

- This skill **detects and reports** but does not auto-fix
- Inconsistency resolution is left to developer judgment. **PRD updates are never automated** — see
  "PRD ↔ spec Consistency" above
- Prioritize upstream documents (PRD > spec > adr)
- Do not uniformly treat specs as correct, as implementation may be correct and specs outdated
