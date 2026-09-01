---
name: task-cleanup
description: "Clean up task/ directory after implementation completion, integrating design decisions and rejected alternatives into adr/{feature}.md before deletion"
argument-hint: "[ticket-number]"
arguments: [ticket-number]
license: MIT
user-invocable: true
model: haiku
allowed-tools: Read, Glob, Grep, AskUserQuestion, Edit(.sdd/**)
---

# Task Cleanup - Task Log Cleanup

Organizes documents under `${CLAUDE_PROJECT_DIR}/${SDD_TASK_PATH}/`, integrating design decisions and rejected
alternatives into `${CLAUDE_PROJECT_DIR}/${SDD_ADR_PATH}/{feature}.md` (append-only) before deletion.

## Prerequisites

**Read the following prerequisite references before execution:**

- `references/prerequisites_plugin_update.md` - Check for plugin updates
- `references/prerequisites_principles.md` - Read AI-SDD principles document
- `references/prerequisites_directory_paths.md` - Resolve directory paths using `SDD_*` environment variables

### Document Persistence Rules (Reference)

| Path                          | Persistence    | Management Rules                                                                                  |
|:-------------------------------|:---------------|:----------------------------------------------------------------------------------------------------|
| `specification/*_design.md`   | **Temporary**  | Draft technical plan. Deleted by a separate flow after implementation — not handled by this skill  |
| `task/`                       | **Temporary**  | **Delete** after implementation complete (this skill). Integrate decisions/rejected alternatives into `adr/{feature}.md` first |
| `adr/{feature}.md`            | **Persistent** | **Append-only** decision log. Never rewrite past entries — append new decisions as they are made   |

**Role separation**: `task/` is temporary, AI-facing working notes, deleted once cleanup completes. The ticket
(GitHub Issue / JIRA) is the persistent, team-facing progress record — step 9 dumps a summary there so humans
keep visibility after `task/` is gone.

### Language Configuration

Output templates are located under `templates/${SDD_LANG:-en}/` within this skill directory.
The `SDD_LANG` environment variable determines the language (default: `en`).

## Input

- `ticket-number`: $ticket-number

Full argument string: $ARGUMENTS

> **Fallback**: If the value above is empty or remains a literal `$` placeholder, treat the
> argument as omitted and follow the no-argument flow (scope confirmation below).

| Argument | Required | Description |
|:--|:--|:--|
| `ticket-number` | - | Target ticket number or path. Targets entire task/ if omitted |

### Input Examples

- `/task-cleanup TICKET-123`
- `/task-cleanup feature/task-management`
- `/task-cleanup` (without arguments, targets entire task/)

### Scope Confirmation for No-Argument Execution

**When executed without arguments, display the contents of the target directory and ask for user confirmation before starting the process.**

**Reference**: `examples/scope_confirmation.md`

Replace placeholders with actual directory/file names, types, dates, and counts.

**Post-confirmation behavior**:
- User approves -> Execute cleanup on entire task/
- User cancels or specifies a particular directory -> Re-execute with the specified scope

## Processing Flow

### 1. Identify Target Directory

- With argument -> Target `${CLAUDE_PROJECT_DIR}/${SDD_TASK_PATH}/{argument}/`
- Without argument -> Target entire `${CLAUDE_PROJECT_DIR}/${SDD_TASK_PATH}/` (one or more `{ticket}/` subdirectories)

Record each target subdirectory's ticket identifier now (directory name, or its `ticket` front matter field) — later steps reuse it rather than re-resolving it.

### 2. Check Target Files

Get the file list in the target directory with `ls -la ${CLAUDE_PROJECT_DIR}/${SDD_TASK_PATH}/{target}/`, then check the last update date for each file with `git log -1 --format="%ci" -- <file_path>`.

### 3. Analyze and Classify Content

Review content of each file and classify as follows:

**Content to Integrate (-> `adr/{feature}.md`)**:

| Category                           | Examples                                                                  |
|:-----------------------------------|:--------------------------------------------------------------------------|
| **Design decisions and rationale** | "Reason for choosing Redis: ...", "Reason for adopting this pattern: ..." |
| **Rejected alternatives**          | "Comparison of Option A vs Option B", "Rejected alternatives and reasons" |

**Content Safe to Delete (No Migration Needed)**:

| Category                          | Examples                                            |
|:-----------------------------------|:-----------------------------------------------------|
| **Work progress notes**           | "Implementing X", "Y completed"                     |
| **Temporary investigation logs**  | Diary-like content, trial and error records         |
| **Specific implementation steps** | Detailed procedures already reflected in code       |
| **Task lists**                    | Lists of completed tasks                            |
| **Date-dependent information**    | Information dependent on specific periods or dates  |
| **Technical tips / troubleshooting / reusable patterns** | Implementation know-how, performance findings, debugging notes |

### 4. Determine Integration Target

When there is information to integrate, determine the appropriate `adr/{feature}.md`:

1. Find the existing decision log most related to content with a single Glob covering both the current
   suffix-free name and the legacy `-decisions` suffix (still valid on existing files):
   - Flat layout: `${CLAUDE_PROJECT_DIR}/${SDD_ADR_PATH}/{feature-name}*.md`
   - Hierarchical layout: `${CLAUDE_PROJECT_DIR}/${SDD_ADR_PATH}/{parent-feature}/{child-feature}*.md`
2. If no existing file for the feature -> create a new `adr/{feature}.md` (no suffix — the default for new files)
3. If no design decision or rejected alternative was found in the target -> skip integration (nothing to append)

### 5. Integrate Information

When performing integration:

- **Append-only**: add a new entry at the end of the file. Never rewrite or remove past entries
- Each entry captures: the decision, its rationale, and rejected alternatives (if any)
- Do not document source file name (don't leave history)
- Match the structure of existing entries in the file (or the Architecture Decision Record section of `AI-SDD-PRINCIPLES.md` if the file is new)

### 6. Determine Whether a Spec Update Is Needed

For each decision integrated in step 5, judge whether it matches the "When to Update `*_spec.md`" rule defined in
`AI-SDD-PRINCIPLES.md` (public API changes, new data models, fundamental behavior changes, new requirements).

If any decision matches, propose a `*_spec.md` update to the user via `AskUserQuestion` (present the matching
decision and the affected `*_spec.md`). **Do not edit `*_spec.md` automatically** — spec changes require explicit
user confirmation. Record the outcome (updated / deferred / not applicable) for the output.

### 7. Update Front Matter in Related Documents

Independent of step 6 — do not wait for the spec-update decision to perform these edits. Before deleting task
files, update front matter in related documents if they have YAML front matter. See `references/front_matter_task.md`
for task fields and `references/front_matter_spec_design.md` for design fields.

| Action | Description |
|:-------|:------------|
| **Update/create `adr` front matter** | Set the common fields (`id`, `title`, `type: "adr"`, `status`, `created`, `updated`, `sdd-version` — read `version` from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`). The detailed `adr` schema is not yet defined in `${CLAUDE_PLUGIN_ROOT}/shared/references/front_matter_reference.md`; use only the common fields until it is added |
| **Update design doc `updated`** | If the related `*_design.md` still exists, set to current date |
| **Update spec `status`** | Consider updating to `"approved"` if implementation validates the spec |

### 8. Delete Files/Directories

Delete individual files with `git rm ${CLAUDE_PROJECT_DIR}/${SDD_TASK_PATH}/{target}/{file}`, or delete the entire directory after all files are processed with `git rm -r ${CLAUDE_PROJECT_DIR}/${SDD_TASK_PATH}/{target}/`.

### 9. Dump Summary to Ticket

For each target ticket identified in step 1, once its integration and deletion are done, post a summary comment
on that ticket (don't wait for other targets when running without an argument — post per ticket as it completes).

The summary should include: which `adr/{feature}.md` entries were added, whether a spec update was
proposed (and its outcome), and which files were deleted.

- GitHub: `gh issue comment <ticket-number> --body "<summary>"`
- JIRA: use the `mcp-atlassian` MCP (`jira_add_comment`) with the ticket key

If the ticket tracker cannot be determined, skip this step and note it in the output instead of failing.

## Output

Use the `templates/${SDD_LANG:-en}/cleanup_output.md` template for output formatting.

## Notes

### Cases Requiring Careful Judgment

- **Implementation not complete**: Keep task/
- **Integration target unclear**: Confirm with user
- **Information spanning multiple features**: Integrate into most related document
- **Spec update trigger matched but user declines**: Record as "deferred" in the output, do not re-prompt within the same run

### Deletion Principles

- **Don't leave history**: Don't add notations like "migrated from ..." during migration
- **Minimal migration**: Migrate only truly valuable information (decisions and rejected alternatives only)
- **Avoid duplication**: Don't migrate content already documented in `adr/{feature}.md`
