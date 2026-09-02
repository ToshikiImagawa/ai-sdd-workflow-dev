---
name: check-spec
description: "Check consistency between implementation code and abstract specifications (spec), detecting discrepancies"
argument-hint: "[feature-name] [--full]"
arguments: [feature-name]
license: MIT
user-invocable: true
allowed-tools: Read, Glob, Grep, AskUserQuestion, Bash(python3 "${CLAUDE_PLUGIN_ROOT}/skills/check-spec/scripts/find-spec-docs.py" *)
disallowed-tools: Write, Edit
---

# Check Spec - Specification & Implementation Consistency Check

Verifies consistency between implementation code and the abstract specifications under
`${SDD_SPECIFICATION_PATH}/`, detecting discrepancies.

**Role**: This command specializes in **spec <-> implementation consistency checking**.
The spec is the persistent source of truth, so it is the **first-class comparison baseline**.
**Document-level consistency** (PRD <-> spec, spec <-> adr) is handled by the `spec-reviewer`
agent when called with the `--full` option.

**Design drafts are optional**: the technical design document lives at
`${SDD_TASK_PATH}/{ticket-number}/design-draft.md` and is deleted once implementation completes.
When a draft exists it is used as an **auxiliary input** for details the spec cannot express
(module structure, technology stack). Its absence is the normal state and is never reported as a
problem. Projects still carrying v4.x persisted `{feature}_design.md` files under
`${SDD_SPECIFICATION_PATH}/` get the same auxiliary treatment for those files.

## Prerequisites

**Read the following prerequisite references before execution:**

- `references/prerequisites_plugin_update.md` - Check for plugin updates
- `references/prerequisites_principles.md` - Read AI-SDD principles document
- `references/prerequisites_directory_paths.md` - Resolve directory paths using `SDD_*` environment variables

### Document Dependencies

See `references/document_dependencies.md` for the document dependency chain and direction meaning.

### Language Configuration

Output templates are located under `templates/${SDD_LANG:-en}/` within this skill directory.
The `SDD_LANG` environment variable determines the language (default: `en`).

## Input

- `feature-name`: $feature-name

Full argument string: $ARGUMENTS

> **Fallback**: If the value above is empty, remains a literal `$` placeholder, or starts with `--`
> (a flag captured positionally), treat the argument as omitted and interpret the full argument
> string instead (e.g., `/check-spec --full` means all specs with the `--full` option).

| Argument       | Required | Description                                                                                                |
|:---------------|:---------|:-----------------------------------------------------------------------------------------------------------|
| `feature-name` | -        | Target feature name or path (e.g., `user-auth`, `auth/user-login`). If omitted, all specs are targeted     |

### Options

- `--full`: In addition to consistency checking, also runs quality review by the `spec-reviewer` agent
    - CONSTITUTION.md compliance check
    - Completeness, clarity, and SysML compliance check
    - Vague description detection

### Input Examples

- `/check-spec user-auth` — Consistency check only (default)
- `/check-spec task-management --full` — Consistency check + quality review
- `/check-spec --full` — Comprehensive check for all specifications
- `/check-spec` — Without arguments, targets all specifications (consistency check only)

### Scope Confirmation for No-Argument Execution

**When executed without arguments, display the list of target files and ask for user confirmation before starting the process.**

**Reference**: `examples/scope_confirmation.md`

Replace placeholders with actual file names and counts.

**Post-confirmation behavior**:

- User approves -> Execute check on all files
- User cancels or specifies a particular file -> Re-execute with the specified scope

## Processing Flow

**Optimized Execution Flow**:

**Phase 1: Shell Script** - Execute `python3 "${CLAUDE_PLUGIN_ROOT}/skills/check-spec/scripts/find-spec-docs.py" [feature-name]` to scan specification documents.

This script:
1. Finds all spec documents under `${SDD_SPECIFICATION_PATH}/` in flat or hierarchical structure,
   with or without the `_spec` suffix (`{feature}.md` / `{feature}_spec.md`)
2. Collects design drafts (`${SDD_TASK_PATH}/{ticket-number}/design-draft.md`) as an optional
   auxiliary input; an empty list is normal, not an error
3. Generates file mapping JSON (spec → feature name → auxiliary design doc, plus the draft list)
4. Exports environment variables to `$CLAUDE_ENV_FILE`:
   - `CHECK_SPEC_SPEC_FILES` - List of spec files (the comparison baseline)
   - `CHECK_SPEC_DESIGN_DRAFT_FILES` - List of design drafts (empty when none exist)
   - `CHECK_SPEC_MAPPING` - JSON mapping file

**Phase 2: Claude** - Read specs from pre-scanned lists and perform consistency check

### 1. Identify Target Documents

Target the spec documents under `${SDD_SPECIFICATION_PATH}/`. Both flat and hierarchical
structures are supported, and the `_spec` suffix is optional in every case.

**For flat structure**:

- With argument -> Target `${CLAUDE_PROJECT_DIR}/${SDD_SPECIFICATION_PATH}/{argument}_spec.md` and
  `${CLAUDE_PROJECT_DIR}/${SDD_SPECIFICATION_PATH}/{argument}.md` (whichever exist)
- Without argument -> Target all spec `.md` files under
  `${CLAUDE_PROJECT_DIR}/${SDD_SPECIFICATION_PATH}/` (recursively)

**For hierarchical structure** (when argument contains `/`, or when specifying hierarchical path):

- Argument in `"{parent-feature}/{feature-name}"` format -> Target
  `${CLAUDE_PROJECT_DIR}/${SDD_SPECIFICATION_PATH}/{parent-feature}/{feature-name}_spec.md` or
  the suffix-free `.../{feature-name}.md`
- Argument is `"{parent-feature}"` only -> Target every spec `.md` file under
  `${CLAUDE_PROJECT_DIR}/${SDD_SPECIFICATION_PATH}/{parent-feature}/` (the parent's
  `index[_spec].md` and its child features)

**Naming convention**:

- **Under specification**: `_spec` suffix optional (`index.md`, `index_spec.md`,
  `{feature-name}.md`, or `{feature-name}_spec.md`)
- **Not a spec**: `{feature-name}_design.md` under specification is a v4.x persisted design doc.
  It is excluded from the spec list and only used as an auxiliary input (see the mapping JSON)

**Auxiliary design input** (use only if present):

- `${CLAUDE_PROJECT_DIR}/${SDD_TASK_PATH}/{ticket-number}/design-draft.md` — the in-progress
  technical design draft. The filename is fixed and ticket-scoped, so it cannot be matched to a
  spec by name; treat every listed draft as context for the feature under implementation
- The `design` field of each mapping entry — a v4.x persisted `{feature}_design.md`, when present

**Hierarchical structure input examples**:

- `/check-spec auth/user-login` — Check user-login feature under auth domain
- `/check-spec auth` — Check entire auth domain

### 2. Load Specifications

The spec is an **abstract specification**: it states "what to build", not the technical detail of
"how". Only extract what the spec can actually express, and do not expect design-level detail
from it.

**Extract the following information from the spec**:

| Item                        | Typical spec section          | Description                                                                    |
|:----------------------------|:------------------------------|:-------------------------------------------------------------------------------|
| **Public API**              | Provided components, I/O definitions | Public interface names, arguments, return values, CLI arguments/options, environment variables |
| **Data Model**              | I/O definitions, glossary      | Entities, fields and their types, output file/JSON structures                  |
| **Behavior**                | Functional requirements, behavior diagrams | Observable behavior per requirement ID (FR-xxx / NFR-xxx), branch conditions   |
| **Functional Requirements** | Functional requirements table  | List of features to implement, with requirement IDs                            |
| **Constraints**             | Constraints                    | Explicitly excluded behavior, prerequisites                                    |
| **Literal Values**          | Schema Registry, body text     | Thresholds, enum values, CHECK constraint values, durations, and other constants |

**Additional items — only when a design draft (or a v4.x persisted design doc) exists**:

| Item                        | Description                                                        |
|:----------------------------|:-------------------------------------------------------------------|
| **Module Structure**        | Directory structure, file organization                             |
| **Technology Stack**        | Libraries, frameworks used                                         |
| **Implementation Approach** | Architecture patterns, design decisions                            |

If no draft exists, **omit these items from the comparison entirely** — do not report them as
missing or as a discrepancy.

**Literal value extraction sources** (in priority order):

1. **Schema Registry section** in the spec (a "Value Range / Threshold Registry" table), if present.
   Parse each entry as `{value-id, value, unit, source-requirement-id, section}`.
2. If no registry section exists, extract literal values mentioned in the body text of the spec
   (e.g., "confidence threshold 70%", `default 0.7`, `CHECK (risk_level IN ('low', 'high'))`, "p95 <= 15s").
3. A design draft, when present, may refine a value; the spec still holds the authoritative value.

### 3. Verify Implementation Code

Search for code corresponding to specification contents:

- Search APIs/functions (using methods appropriate for project language)
- Search type definitions/data models
- Verify module/file existence
- Extract literal values from implementation:
    - Configuration files (`config.py`, `settings.py`, `*.toml`, `*.yaml`, `*.json`, `.env.example`)
    - ORM CHECK constraints and DB migration files (e.g., `CheckConstraint`, `CHECK (... IN (...))`)
    - Validation constraints (e.g., Pydantic `Field(ge=..., le=...)`, zod, Bean Validation)
    - Language-specific enums and constants (`Enum`, `const`, `Literal[...]`, union types)

### 4. Consistency Check Items

**Note**: This command specializes in **spec <-> implementation consistency checking**. **Document-level consistency**
(PRD <-> spec, spec <-> adr) and **quality review** (CONSTITUTION.md compliance, completeness, clarity) are handled by
the `spec-reviewer` agent when using the `--full` option.

#### Front Matter Consistency

If documents contain YAML front matter, call the `front-matter-reviewer` agent to validate.
Pass all target document paths (the specs, plus any auxiliary design doc).

After results are returned, integrate `impl-status` findings into the spec ↔ implementation consistency results.
Record the spec's `impl-status` value (or its absence) for use in the branching below.

#### Unimplemented-Function Classification by `impl-status`

A spec-documented function with no corresponding implementation is not automatically a defect: whether it is
expected or a regression depends on the spec's `impl-status` front matter field.

| Spec `impl-status`                | Meaning                                     | Classification |
|:------------------------------------|:----------------------------------------------|:-----------------|
| `implemented`                      | Spec declares the implementation is done      | **Critical** — regression: the implementation was removed, or never matched the declared status |
| `not-implemented` / `in-progress`  | Spec intentionally precedes the implementation | **Info** — expected: implementation has not caught up with the spec yet |
| Missing / absent                   | No implementation-state signal available       | **Warning** — undecidable; recommend adding `impl-status` to the spec (`/recommend-front-matter`) |

This branching applies **only** to "function specified in the spec but missing from the implementation."
Public API mismatches, data model mismatches, and behavior contradicting the spec remain unconditionally
Critical regardless of `impl-status` — `impl-status` never excuses an implementation that diverges from what
it claims to implement, only one that simply hasn't started yet.

#### spec <-> Implementation Consistency

| Check Target                | Verification Content                                            | Importance |
|:----------------------------|:----------------------------------------------------------------|:-----------|
| **Public API**              | Do public names, arguments, return values, CLI options, and environment variables match? | High |
| **Data Model**              | Do entities, fields, types, and output structures match?        | High       |
| **Behavior**                | Does observable behavior match the spec per requirement ID?     | High       |
| **Functional Requirements** | Are functions specified in the spec implemented?                | High       |
| **Literal Values**          | Do thresholds, enum values, and constraint values match between spec and implementation? | High |
| **Constraints**             | Does the implementation stay within the spec's stated constraints? | Medium  |

#### design <-> Implementation Consistency (only when a design draft exists)

Skip this table entirely when no design draft (or v4.x persisted design doc) is available.

| Check Target                | Verification Content                               | Importance |
|:----------------------------|:---------------------------------------------------|:-----------|
| **Module Structure**        | Does directory/file structure match?               | Medium     |
| **Technology Stack**        | Are documented libraries being used?               | Low        |

#### Literal Value Consistency Check

Compare literal values between spec and implementation (adding the design draft as a third layer when one
exists) and detect drift:

1. **Build a value table**: For each value extracted in step 2 (spec registry or body text), find the corresponding
   value in the implementation (step 3 extraction sources), and in the design draft when present. Match by value
   identifier, requirement ID (UR/FR/NFR-xxx), or surrounding context (setting name, column name, enum name).
2. **Normalize before comparison**: Treat equivalent representations as equal (e.g., `70%` and `0.7`, `15s` and
   `15000ms`). Report the comparison in the original notation of each layer.
3. **Detect drift**: Report any layer whose value differs from the spec as a **Warning**, marking the drifting layer:

   ```
   [WARN] Value drift detected: rag_confidence_threshold
     spec: 0.7 (§4.1, NFR-AI-005)
     config.py: 0.6 ← drift
   ```

   Include a `design draft:` line only when a draft was actually loaded.

4. **Enum / CHECK constraint completeness**: For enumerated values, compare the full member sets. A member present in
   the implementation but missing from the spec's enumeration (or vice versa) is a drift, even if all other
   members match.
5. **Trace completeness**: If the spec registry entry references a requirement ID, verify the same ID appears in the
   PRD <-> spec traceability table. Report missing IDs as a Warning.

If a value exists in only one layer (e.g., a threshold hard-coded in the implementation with no spec mention),
report it under "Implementation not documented in specs" instead of as drift.

### 5. Discrepancy Classification

Classify detected discrepancies as follows:

**Critical (Immediate Action Required)**:

- Public API mismatch (arguments, return value types, CLI options, environment variables)
- Functions specified in the spec not implemented (see Unimplemented-Function Classification above — this is
  Critical only for the `impl-status: "implemented"` case; the other two cases land in Warning/Info below)
- Data model mismatch (entities, fields, types)
- Behavior contradicting the spec

**Warning (Action Recommended)**:

- Functions specified in the spec not implemented, `impl-status` case: undecidable (see classification above)
- Literal value drift (thresholds, enum values, CHECK constraint values differing between spec and implementation)
- Requirement ID referenced by a spec registry entry missing from the traceability table
- Implementation exceeding a constraint stated in the spec
- Module structure mismatch (only when a design draft was loaded)
- Classes/functions existing but not in documentation
- Naming convention mismatch

**Info (Reference)**:

- Functions specified in the spec not implemented, `impl-status` case: expected (see classification above)
- Minor technology stack differences
- Missing comments/documentation

### 6. Comprehensive Review (--full option only)

When the `--full` option is specified, the `spec-reviewer` agent is invoked to perform comprehensive review.

#### Review Content

| Check Item                      | Description                                                              |
|:--------------------------------|:-------------------------------------------------------------------------|
| **PRD <-> spec Traceability**   | Verify PRD requirements are covered in spec (80% coverage threshold)     |
| **spec <-> adr Consistency**    | Verify recorded decisions are consistent with the spec                   |
| **CONSTITUTION.md Compliance**  | Verify compliance with project principles                                |
| **Completeness**                | Verify required sections (purpose, API, constraints, etc.) are present   |
| **Clarity**                     | Detect vague descriptions ("nice to have", "appropriately", etc.)        |
| **SysML Compliance**            | Verify requirement ID format (UR/FR/NFR-xxx) and traceability are proper |

#### Execution Timing

- Executes after spec <-> implementation consistency check is complete
- Performs comprehensive review for target documents (PRD, spec, adr)
- Generates traceability matrix (PRD -> spec -> implementation correspondence)

**Note**: Comprehensive review requires additional execution time. For quick checks during development, run without
`--full`, and use `--full` before PR creation or for periodic checks.

## Output

Use the `templates/${SDD_LANG:-en}/check_spec_output.md` template for output formatting.

## Check Execution Timing

| Timing                           | Recommended Action                         |
|:---------------------------------|:-------------------------------------------|
| **Before Implementation Start**  | Verify specification existence and content |
| **At Implementation Completion** | Verify consistency with specifications     |
| **Before PR Creation**           | Run as final verification                  |
| **Periodic Check**               | Prevent documentation obsolescence         |

## Serena MCP Integration (Optional)

If Serena MCP is enabled, high-precision consistency checking through semantic code analysis is possible.

### Usage Conditions

- `serena` is configured in `.mcp.json`
- Target language's Language Server is supported (30+ languages supported)

### Additional Features When Serena is Enabled

#### Symbol-Based Consistency Check

| Feature                    | Description                                                             |
|:---------------------------|:------------------------------------------------------------------------|
| `find_symbol`              | Search implementation code for APIs/functions documented in spec        |
| `find_referencing_symbols` | Understand usage locations of specific symbols to identify impact scope |

#### Enhanced Check Items

1. **API Implementation Verification**: Verify functions/classes documented in spec are implemented via symbol search
2. **Signature Match**: Verify function argument/return types match spec
3. **Unused Code Detection**: Detect symbols implemented but not documented in spec
4. **Dependency Understanding**: Analyze reference relationships between modules

#### Additional Output When Using Serena

**Reference**: `examples/serena_symbol_analysis.md`

### Behavior When Serena is Not Configured

Even without Serena, consistency checking is performed using traditional text-based search (Grep/Glob).
Features are limited but work language-agnostically.

## Notes

- If specifications don't exist, recommend creating them with `/generate-spec` first
- A missing design draft is **not** a problem: it is the normal state after implementation completes.
  Never ask the user to create one, and never report its absence as a discrepancy
- If many discrepancies exist, major specification updates may be needed
- If implementation is correct and specs are outdated, update specifications
- If specifications are correct and implementation is wrong, fix implementation
- Detail that the spec deliberately omits (internal structure, private helpers) is out of scope:
  record it under "Implementation not documented in specs" only when it changes observable behavior
