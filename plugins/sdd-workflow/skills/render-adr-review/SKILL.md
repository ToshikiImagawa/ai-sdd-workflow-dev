---
name: render-adr-review
description: "Render an ADR decision log (or a spec/design doc's decision-rationale section) into a temporary review HTML, restructured around decision / rationale / rejected alternatives instead of a plain Markdown-to-HTML conversion. Output is a scratch file under .sdd/.cache/, never committed."
argument-hint: "<source-path> [ticket-number]"
arguments: [source-path, ticket-number]
license: MIT
user-invocable: true
allowed-tools: Read, Glob, Grep, AskUserQuestion, Edit(.sdd/.cache/**)
---

# Render ADR Review - Decision-Axis Review HTML

Reorganizes an `adr/{feature}.md` decision log (or the decision-rationale content of a
`*_spec.md` / `*_design.md`) around **decision / rationale / rejected alternatives**, and renders it
as a temporary HTML file for human review. This is not a Markdown-to-HTML converter: content is
mapped into dedicated template regions (decision card, comparison table) so a reviewer can see what
was decided, why, and what was passed over, at a glance.

This skill does not modify any existing review agent or skill (`spec-reviewer`, `prd-reviewer`,
`doc-consistency-checker`, etc.) — it only adds a new rendering path for human-facing review
material.

## Prerequisites

**Read the following prerequisite references before execution:**

- `references/prerequisites_plugin_update.md` - Check for plugin updates
- `references/prerequisites_principles.md` - Read AI-SDD principles document
- `references/prerequisites_directory_paths.md` - Resolve directory paths using `SDD_*` environment variables
- `references/html_structure_reference.md` - Template layers, placeholders, and the highlighting contract this skill must follow

### Language Configuration

Templates are located under `templates/${SDD_LANG:-en}/` within this skill directory.
The `SDD_LANG` environment variable determines the language (default: `en`).

## Input

- `source-path`: $source-path
- `ticket-number`: $ticket-number

Full argument string: $ARGUMENTS

> **Fallback**: If `source-path` is empty or remains a literal `$` placeholder, search
> `${CLAUDE_PROJECT_DIR}/${SDD_ADR_PATH}/**/*.md` with Glob (`adr/` is a single-type directory, so every
> file found is a decision log regardless of whether it carries the legacy `-decisions` suffix). If
> exactly one file is found, use it. If several are found, ask the user to pick one with
> `AskUserQuestion`. If none are found, tell the user no ADR decision log exists yet and stop (do not
> fall back to inventing content).

| Argument        | Required | Description                                                                          |
|:-----------------|:---------|:--------------------------------------------------------------------------------------|
| `source-path`    | -        | Path to an `adr/{feature}.md` decision log, or a `*_spec.md` / `*_design.md` that contains a decision-rationale section. Searched under `${SDD_ADR_PATH}` when omitted |
| `ticket-number`  | -        | Used for the output file name. Falls back to the source file's feature name if omitted |

### Input Examples

| Example                                              | Description                                  |
|:------------------------------------------------------|:----------------------------------------------|
| `/render-adr-review adr/auth/user-login.md` | Render a single feature's decision log        |
| `/render-adr-review adr/user-auth.md TICKET-123` | Name the output after the ticket instead of the feature |
| `/render-adr-review`                                  | No argument - pick from ADR logs found under `${SDD_ADR_PATH}` |

## Processing Flow

### 1. Resolve and Read the Source

Both flat (`{feature}.md`) and hierarchical (`{parent-feature}/{child-feature}.md`) ADR layouts are
supported, matching `${SDD_ADR_PATH}` (see the Fallback note above for the legacy `-decisions` suffix
form). Read the resolved file in full.

### 2. Extract Decision Entries

An ADR decision log is append-only: each heading-delimited entry is one decision, in the order it
was recorded. For each entry, extract:

| Field | Source | Notes |
|:--|:--|:--|
| Decision | The choice that was made | This is the entry's own subject, not an alternative |
| Rationale | Why it was chosen | Keep the source's own wording; do not paraphrase away specifics |
| Rejected alternatives | Options considered and not chosen, with the reason each was rejected | Omit the comparison table entirely if the entry recorded none - do not invent alternatives |
| Date/context | Whatever date or situational note the entry carries | Leave blank if the entry has none |

If a `*_spec.md` / `*_design.md` is given instead of an ADR log, apply the same extraction to its
design-decision / rationale sections; skip sections that are plain behavior description with no
decision-vs-alternative content.

### 3. Render Bottom-Up

Follow `references/html_structure_reference.md` exactly:

1. For each option in an entry (the adopted decision first, then each rejected alternative), fill a
   copy of `templates/${SDD_LANG:-en}/alternative_row.md`.
2. Join those rows and fill `templates/${SDD_LANG:-en}/decision_card.md` for the entry.
3. Join all cards and fill `templates/${SDD_LANG:-en}/review_shell.md` to produce the full HTML
   document.

### 4. Write the Output File

Write the rendered HTML with `Edit` to
`${CLAUDE_PROJECT_DIR}/${SDD_ROOT}/.cache/render-adr-review/{ticket-number or feature-name}-review.html`.

Report the absolute path to the user so they can open it directly in a browser.

## Output

**This HTML file is a temporary scratch artifact, exactly like the other per-skill caches under
`${SDD_ROOT}/.cache/` (`.sdd/.cache/` is listed in `.gitignore`). It is not part of the persisted
AI-SDD documentation set (PRD / spec / design / adr) and must never be `git add`-ed or committed.**
Re-running this skill overwrites the previous file for the same feature/ticket; nothing here needs
to survive between review sessions.

## Notes

- Read-only with respect to the source ADR/spec — this skill never edits `adr/` or `specification/`
  content, only writes the rendered HTML under `.sdd/.cache/`
- If the source has no rejected alternatives for a decision, render the rationale only and omit the
  comparison table for that card - an empty table implies a comparison that never happened
- Do not start a dev server or open a browser automatically; report the file path and let the user
  open it
