---
name: recommend-front-matter
description: "Scan existing AI-SDD documents and recommend YAML front matter additions"
argument-hint: "[--apply]"
license: MIT
user-invocable: true
model: haiku
allowed-tools: Read, Glob, Grep, AskUserQuestion, Edit(.sdd/**), Edit(.sdd-config.json), Bash(python3 "${CLAUDE_PLUGIN_ROOT}/skills/recommend-front-matter/scripts/scan-documents.py" *)
---

# Recommend Front Matter - Add YAML Metadata to Existing Documents

Scans existing AI-SDD documents (PRD, spec, design, task) and recommends adding YAML front matter for structured metadata.

**Purpose**: Help users add front matter to existing documents created before front matter support was added.

**Note**: Front matter is optional and backward compatible. This skill provides recommendations but does not require adoption.

## Prerequisites

**Read the following prerequisite references before execution:**

- `references/prerequisites_plugin_update.md` - Check for plugin updates
- `references/prerequisites_principles.md` - Read AI-SDD principles document
- `references/prerequisites_directory_paths.md` - Resolve directory paths using `SDD_*` environment variables
- `references/front_matter_prd.md` - PRD front matter schema
- `references/front_matter_spec_design.md` - Spec/Design front matter schema
- `references/front_matter_task.md` - Task front matter schema
- `references/front_matter_impl.md` - Implementation Log front matter schema

### Language Configuration

Output templates are located under `templates/${SDD_LANG:-en}/` within this skill directory.
The `SDD_LANG` environment variable determines the language (default: `en`).

## Input

$ARGUMENTS

### Options

- `--apply`: Automatically apply recommended front matter to documents (after user confirmation)
    - Without this option: Generate recommendation report only
    - With this option: Apply front matter to files and generate result report

### Input Examples

- `/recommend-front-matter` — Generate recommendation report only
- `/recommend-front-matter --apply` — Apply front matter after confirmation

## Processing Flow

**Optimized Execution Flow**:

### Phase 1: Shell Script - Scan Documents

Execute `python3 "${CLAUDE_PLUGIN_ROOT}/skills/recommend-front-matter/scripts/scan-documents.py"` to scan AI-SDD documents.

This script:
1. Loads `.sdd-config.json` to resolve directory paths
2. Scans documents in `${SDD_REQUIREMENT_DIR}`, `${SDD_SPECIFICATION_DIR}`, and `${SDD_TASK_DIR}` directories
3. Detects Front Matter presence (checks for opening/closing `---`)
4. Determines document type from file path and naming convention
5. Extracts title from first `#` heading
6. Generates JSON report (`${SDD_ROOT}/.cache/recommend-front-matter/scan_result.json`)
7. Exports environment variables to `$CLAUDE_ENV_FILE`:
   - `RECOMMEND_FM_CACHE_DIR` - Cache directory
   - `RECOMMEND_FM_SCAN_RESULT` - JSON scan result file path
   - `SDD_LANG` - Language configuration

**Scan Result JSON Schema**: See `references/scan_result_schema.md` for the full schema and an example.

### Phase 2: Claude - Generate Front Matter Recommendations

For each document **without front matter** in the scan result:

#### 1. Read Document Content

Use the Read tool to read the first 100 lines of each document. This provides context for:
- Extracting accurate title
- Inferring tags from headings and content keywords
- Determining category from content structure

#### 2. Infer Common Fields

| Field        | Inference Logic                                                                                                      |
|:-------------|:---------------------------------------------------------------------------------------------------------------------|
| `id`         | Generate from file path and type: `"{type}-{feature-name}"` (hierarchical: `"{type}-{parent}-{feature-name}"`)      |
| `title`      | Extract from first `#` heading (fallback: basename)                                                                  |
| `type`       | Use `type` field from scan result (`prd`, `spec`, `design`, `task`, `implementation-log`)                           |
| `status`     | Default to `"draft"` for new front matter                                                                            |
| `created`    | Use current date `YYYY-MM-DD`                                                                                        |
| `updated`    | Same as `created` for initial front matter                                                                           |
| `depends-on` | Infer from file naming patterns (spec → prd, design → spec, task → design). Empty list if no match found.           |
| `tags`       | Extract from headings and content keywords (max 5 tags). Use lowercase, hyphenated format (e.g., `"user-auth"`).    |
| `category`   | Infer from directory hierarchy or parent feature name. Empty if no clear category.                                   |

**`sdd-version` is intentionally excluded from this table.** Setting it to the current plugin version on a
document that predates front matter entirely would fabricate a false generation-time signal — the document
was not actually generated by that plugin version. This would corrupt the very generation/migration detection
that `front-matter-reviewer` and `doc-consistency-checker` rely on (an absent `sdd-version` is the correct,
already-established signal for "predates this field's introduction"). Leave the field absent for back-filled
front matter.

**Dependency Inference Logic**:

Follow the dependency direction rules from the type-specific front matter references:

- **PRD** → No dependencies (or parent PRD if hierarchical)
- **Spec** → Search for matching PRD in `${SDD_REQUIREMENT_PATH}` directory:
    - Try exact match: `{basename}.md`
    - Try hierarchical match: `{parent-name}.md`
    - If no match found: Empty list
- **Design** → Search for matching spec in `${SDD_SPECIFICATION_PATH}` directory:
    - Try exact match: `{basename}_spec.md`
    - Try hierarchical match: `{parent-name}_spec.md` or `{parent-name}/index_spec.md`
    - If no match found: Empty list
- **Task** → Search for matching design in `${SDD_SPECIFICATION_PATH}` directory:
    - Try exact match: `{basename}_design.md`
    - Try hierarchical match: `{parent-name}_design.md` or `{parent-name}/index_design.md`
    - If no match found: Empty list
- **Implementation Log** → Same logic as Task

**ID Generation for Hierarchical Structure**:

For hierarchical directory structures (e.g., `specification/auth/user-login_design.md`):
- Extract parent from path: `"auth"`
- Extract feature from basename: `"user-login"`
- Generate ID: `"design-auth-user-login"`

For flat structures (e.g., `specification/user-login_design.md`):
- Generate ID: `"design-user-login"`

#### 3. Infer Type-Specific Fields

Based on the `type` field, add the type-specific fields listed in `templates/${SDD_LANG}/type_specific_fields.md` (PRD / Spec / Design / Task / Implementation Log).

#### 4. Existing Specs Missing `impl-status`

Separately from the "without front matter" pass above, check the scan result's `documents` entries for
`type: "spec"` with `has_front_matter: true` and `missing_impl_status: true` — specs that already have front
matter but predate the `impl-status` field. For each:

- Recommend adding a **single field**, not a full front matter block: `impl-status: "not-implemented"` (the
  safe default — a human should confirm if the spec is actually already implemented)
- Do not touch any other existing field or value on the document — this is strictly additive

### Phase 3: Generate Recommendation Report

Use the report template at `templates/${SDD_LANG}/recommendation_report.md`.

For each document without front matter:
1. Show current first heading
2. Show recommended YAML front matter block
3. Explain inference logic for each field
4. Provide copy-paste-ready YAML block

**Report Sections**:
1. **Summary**: Total count, with/without front matter count, count of specs missing `impl-status`
2. **Recommendations**: One section per document with recommended YAML
3. **Specs Missing `impl-status`**: One section per flagged spec, showing only the single field to add (not a
   full YAML block — these documents already have front matter)
4. **Next Steps**: Instructions for applying recommendations (manual or `--apply`)

### Phase 4: Apply Front Matter (if `--apply` option)

**Only execute if `--apply` argument is present.**

#### 1. User Confirmation

Use AskUserQuestion to confirm before modifying files:

**Question**: "以下の {count} 個のファイルに Front Matter を追加します。よろしいですか？" (en: "Add Front Matter to {count} files?")

`{count}` is the combined total: documents without front matter (full block) plus specs missing `impl-status`
(single field). List the two groups separately in the display below so the user knows which files get a full
block vs. a single added field.

**Display**:
- List of files to be modified (max 10 files shown, "+ X more" if >10)
- Warning: "この操作はファイルを直接変更します。変更前に Git コミットを推奨します。" (en: "This operation will modify files directly. Git commit recommended before applying.")

**Options**:
- "Yes, apply to all files" (recommended option)
- "No, cancel"

If user cancels → Output recommendation report only and exit.

#### 2. Apply Front Matter to Files

For each document without front matter (after user confirms):

1. **Read current file content** (Read tool)
2. **Generate YAML front matter block**:
   ```yaml
   ---
   id: "{inferred_id}"
   title: "{extracted_title}"
   type: "{type}"
   status: "draft"
   created: "{created_date}"
   updated: "{updated_date}"
   depends-on: [{dependency_ids}]
   tags: [{inferred_tags}]
   category: "{inferred_category}"
   {type_specific_fields}
   ---
   ```
3. **Insert at file beginning** using Edit tool:
   - Add YAML block at the very top
   - Remove leading blank lines from original content if present
   - Ensure one blank line between front matter closing `---` and first heading

**Error Handling**:
- If Edit fails for any file: Record error, continue to next file
- Track success/skip/error counts

#### 2b. Add Missing `impl-status` to Existing Specs

For each spec flagged in Phase 2 step 4 (after the same user confirmation as step 1):

1. **Read current file content** (Read tool)
2. **Insert a single line** inside the existing front matter block: `impl-status: "not-implemented"`
   (immediately after the `sdd-phase` line, to match the field ordering used elsewhere in this schema)
3. Do not regenerate or reorder any other field — this edit touches exactly one line

**Error Handling**: Same as step 2 — record errors per file, continue, and track under a separate count (do not
mix into the "files updated" count from step 2, since these are a different kind of edit).

#### 3. Generate Application Result Report

Use the result template at `templates/${SDD_LANG}/application_result.md`.

## Output

### Without `--apply` Option

Generate recommendation report using `templates/${SDD_LANG}/recommendation_report.md`:

1. **Summary section**: Document counts, including specs missing `impl-status`
2. **Recommendations section**: Per-document YAML recommendations with inference explanations
3. **Specs Missing `impl-status` section**: Per-spec single-field recommendation
4. **Next Steps**: Instructions for manual or automatic application

### With `--apply` Option

After user confirmation and file updates:

1. **Application result summary**: Success/skip/error counts, plus the `impl-status`-added count
2. **Updated file list**: Paths of successfully updated files
3. **Next Steps**: Instructions for reviewing changes and committing

## Important Notes

### Backward Compatibility

- Front matter is **optional** in AI-SDD v3.x
- Documents without front matter remain fully functional
- This skill helps users adopt structured metadata for better tooling support

### Review Before Applying

**Strongly recommend users to**:
1. Review recommendations in the report
2. Commit current state to Git before applying
3. Manually adjust inferred metadata (especially `depends-on`, `tags`, `category`) after applying

### Inference Limitations

The following fields are inferred using pattern matching and may require manual adjustment:

- **`depends-on`**: May miss dependencies if naming conventions differ
- **`tags`**: Basic keyword extraction, may not capture domain-specific concepts
- **`category`**: Inferred from directory structure, may need refinement
- **`priority`/`risk`**: Always default to `"medium"`, should be reviewed

### What This Skill Does NOT Do

- Does **not** validate existing front matter (use `/check-spec --full` for validation)
- Does **not** update outdated field *values* on documents that already have front matter (e.g., a stale
  `status`) — only adds fields that are entirely missing
- Does **not** modify documents that already have front matter, **except** to add a spec's missing
  `impl-status` field (see "Existing Specs Missing `impl-status`" above) — this is an addition, not a value
  change, so it does not conflict with the backward-compatibility guarantee
