---
name: draft-laws
description: "Draft Bend laws (LAWS.bend) from a spec for human approval, then write the reference model and proofs once approved. Never writes approval lines."
argument-hint: "<draft|model> <feature-name> [--ticket <number>] [--overwrite]"
arguments: [subcommand, feature-name]
license: MIT
user-invocable: true
allowed-tools: Read, Glob, Grep, Edit(.sdd/**), Bash(python3 "${CLAUDE_PLUGIN_ROOT}/skills/draft-laws/scripts/draft_laws.py" *)
---

# Draft Laws - Spec to Bend Law Drafts

Turns the machine-checkable properties of a spec into Bend laws, and after a human approves them writes the reference model and proofs. Detailed contract: `laws-drafting_spec.md`. This skill never calls `bend`; checking is `/run-checklist --category proof`.

## Prerequisites

**Read the following prerequisite references before execution:**

- `references/prerequisites_plugin_update.md` - Check for plugin updates
- `references/prerequisites_principles.md` - Read AI-SDD principles document
- `references/prerequisites_directory_paths.md` - Resolve directory paths using `SDD_*` environment variables

Templates are under `templates/${SDD_LANG:-en}/`. Write the whole output (report, comments) in that one language.

## Input

- `subcommand`: $subcommand (`draft` or `model`)
- `feature-name`: $feature-name (`parent/child` for hierarchical specs)

Full argument string: $ARGUMENTS

## Hard rules

- **Never write** a `# approved:` line, `laws-status: approved|proven`, or any change to the spec (`laws:` / `laws-status: drafted` are only *proposed* in the report).
- Never modify a `LAWS.bend` that has an approval line (even with `--overwrite`). Never modify `LAWS.bend` in the `model` stage.
- Write only under `${SDD_LAWS_PATH}/{feature}/` and the report. Do not edit the PRD or spec.
- Only the script decides hashes, ordering, cut-off and checks. Do not compute them yourself.

## Script

All deterministic work goes through one script (JSON on stdout):

| Subcommand | Command (prefix: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/draft-laws/scripts/draft_laws.py"`) |
|:--|:--|
| state | `status <feature>` |
| section hash | `hash <spec-path> <section>` |
| order and cut off | `rank --max <n> <candidates.json>` |
| static check | `check <laws-file> --spec <spec-path> [--require-model]` |

## `draft <feature>`

1. `status <feature>`. If `ok` is false (spec missing, or no front matter `id`), stop with that error. Show `warnings` (including an invalid `laws.max_laws`, which falls back to 10). The state table decides the target: `draft_target` is `LAWS.bend` for `none`/`drafted`, otherwise `LAWS.draft.bend`. `--overwrite` makes `LAWS.bend` the target only when the state is `drafted` (no approval line); with an approval line (valid, expired or malformed approval) refuse `--overwrite` and use `LAWS.draft.bend`. An existing `LAWS.bend` or `LAWS.draft.bend` is never replaced without `--overwrite`; show a diff instead.
2. Read the spec and extract candidates by priority (1 = decision tables / state transitions, 2 = aggregation rules, 3 = constraints and invariants, 4 = numeric targets of NFRs/constraints). Rules:
   - Only from structured sections. Never derive a law from FR-table prose alone.
   - Never from IO, network, filesystem, clock, performance measurements, output formatting.
   - A section without a leading number cannot be a source: list it under "Sections not turned into laws".
   - Write each law as an equation over the model API (`{lhs == rhs : T}`); state the model functions, argument types and numeric encodings in `# model-api:` lines (the spec does not state encodings: decide and document them, a human approves them).
3. For each candidate get the section hash with `hash`. Put candidates in a JSON array `{name, section, priority, body, trivial}` (`body` = the law text, `trivial` = true for tautologies, restatements of a model definition, or type-only properties) and run `rank --max <max_laws>`. Adopt exactly `adopted`; everything in `not_adopted` goes to "Rejected candidates" with its `reason`.
4. If nothing is adopted and nothing can be a law: write no `LAWS.bend` / `LAWS.draft.bend`, report "Sections not turned into laws" per section and finish successfully (not a failure; existing files untouched).
5. Write the law file from `templates/${SDD_LANG}/laws_draft.md`. Every `law` is preceded by `# source: <spec id> §<section> sha256:<hash>` placed **after** the imports (inside the hashed body). No approval line.
6. `check <file> --spec <spec>`. Put the findings in the report. If `propose_drafted` is false, do not propose `drafted`; fix generation errors first when possible.
7. Report from `templates/${SDD_LANG}/laws_draft_report.md`: with `--ticket <n>` write `${SDD_TASK_PATH}/<n>/laws-draft-report.md`, else print it. Include the current content hash and the approval-line format for the human. Mention that until the spec lists `laws:`, the gate reports orphan laws (FAIL, row #4) before the unapproved SKIPPED (row #5).

## `model <feature>`

1. `status <feature>`. If `model_allowed` is false, **refuse** with `model_refusal` and, for an expired approval, the `current_hash`. Create nothing. (The spec's `laws-status` and `laws:` only produce warnings.)
2. Read `LAWS.bend`'s `# model-api:` lines and `Model.*` references only. Write `main.bend` (with `# spec:` and `# model-of: <implementation file>`) and `PROOF.bend` from `templates/${SDD_LANG}/main_model.md` and `proof_model.md` (the file bodies are the Bend text; the `.md` extension only satisfies the support-file rule). `PROOF.bend` may only use `import Base`, `import ./main.bend as Model` and `import ./LAWS.bend as Laws`.
3. Existing `main.bend` / `PROOF.bend` are not overwritten: show the diff instead.
4. If a law looks wrong, report it; do not edit `LAWS.bend` (a human revises it and re-approves).
5. `check LAWS.bend --spec <spec> --require-model`, then point to `/run-checklist <feature> <ticket> --category proof`. A missing `bend` is reported there as TOOL_NOT_FOUND.
