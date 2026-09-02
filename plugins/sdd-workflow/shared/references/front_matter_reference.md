# Front Matter Reference

YAML front matter is optional metadata added at the top of AI-SDD documents. It enables structured search, filtering,
and cross-reference validation.

## Schema Definition

### Common Fields (All Document Types)

| Field        | Type   | Required | Description                                           |
|:-------------|:-------|:---------|:------------------------------------------------------|
| `id`         | string | Yes      | Unique identifier. Pattern: `"{type}-{feature-name}"` |
| `title`      | string | Yes      | Human-readable title                                  |
| `type`       | string | Yes      | Document type (see per-type tables below)             |
| `status`     | string | Yes      | Current status                                        |
| `created`    | string | Yes      | Creation date (YYYY-MM-DD)                            |
| `updated`    | string | Yes      | Last update date (YYYY-MM-DD)                         |
| `sdd-version` | string | No      | sdd-workflow plugin version at generation time (e.g., `"5.0.0"`), read from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. Absent in documents generated before this field was introduced |
| `depends-on` | list   | No       | IDs of upstream documents                             |
| `tags`       | list   | No       | Keywords for search/filtering                         |
| `category`   | string | No       | Feature category                                      |

### Per-Type Fields

#### PRD (`type: "prd"`)

| Field        | Valid Values / Pattern                      | Notes                                 |
|:-------------|:--------------------------------------------|:--------------------------------------|
| `id`         | `"prd-{name}"`                              | Hierarchical: `"prd-{parent}-{name}"` |
| `type`       | `"prd"`                                     |                                       |
| `status`     | `draft`, `review`, `approved`, `deprecated` |                                       |
| `priority`   | `critical`, `high`, `medium`, `low`         | PRD-specific field                    |
| `risk`       | `high`, `medium`, `low`                     | PRD-specific field                    |
| `depends-on` | `["prd-*"]` (parent PRDs only)              |                                       |

#### Spec (`type: "spec"`)

| Field        | Valid Values / Pattern                      | Notes                                  |
|:-------------|:--------------------------------------------|:---------------------------------------|
| `id`         | `"spec-{name}"`                             | Hierarchical: `"spec-{parent}-{name}"` |
| `type`       | `"spec"`                                    |                                        |
| `status`     | `draft`, `review`, `approved`, `deprecated` |                                        |
| `sdd-phase`  | `"specify"`                                 | Always `"specify"`                     |
| `priority`   | `critical`, `high`, `medium`, `low`         | Inherit from PRD if available          |
| `risk`       | `high`, `medium`, `low`                     | Inherit from PRD if available          |
| `depends-on` | `["prd-*"]`                                 | References PRD                         |

#### Design (`type: "design"`) — temporary draft under `task/{ticket-number}/design-draft.md`

| Field         | Valid Values / Pattern                          | Notes                                    |
|:--------------|:------------------------------------------------|:-----------------------------------------|
| `id`          | `"design-{ticket-number}"`                      | Ticket-scoped, not feature-scoped        |
| `type`        | `"design"`                                      |                                          |
| `status`      | `draft`, `review`, `approved`, `deprecated`     |                                          |
| `sdd-phase`   | `"plan"`                                        | Always `"plan"`                          |
| `impl-status` | `not-implemented`, `in-progress`, `implemented` | Design-specific field                    |
| `priority`    | `critical`, `high`, `medium`, `low`             | Inherit from spec                        |
| `risk`        | `high`, `medium`, `low`                         | Inherit from spec                        |
| `depends-on`  | `["spec-*"]`                                    | References spec                          |

#### ADR (`type: "adr"`) — persistent decision log under `adr/{feature-name}.md`

| Field            | Valid Values / Pattern              | Notes                                                                  |
|:-----------------|:-------------------------------------|:------------------------------------------------------------------------|
| `id`             | `"adr-{name}"`                       | Hierarchical: `"adr-{parent}-{name}"`                                   |
| `type`           | `"adr"`                              |                                                                          |
| `status`         | `draft`, `review`, `approved`, `deprecated` |                                                                    |
| `sdd-phase`      | `"implement"`                        | Always `"implement"`                                                    |
| `depends-on`     | `["spec-*"]`                         | References the spec whose decisions this entry records                  |
| `supersedes`     | list of `"adr-*"`                    | IDs of prior entries this decision replaces. Omit if this is not a reversal |
| `superseded-by`  | `"adr-*"`                            | ID of the entry that later replaced this decision. Absent while still current |

`adr/` is append-only: past entries are never rewritten. When a decision is reversed, append a new entry with
`supersedes` pointing at the old one, and set `superseded-by` on the old entry to point at the new one — the
old entry's text stays intact as a historical record.

#### Task (`type: "task"`)

| Field        | Valid Values / Pattern                             | Notes                                            |
|:-------------|:---------------------------------------------------|:-------------------------------------------------|
| `id`         | `"task-{name}"`                                    | Hierarchical: `"task-{parent}-{name}"`           |
| `type`       | `"task"`                                           |                                                  |
| `status`     | `pending`, `in-progress`, `completed`, `cancelled` |                                                  |
| `sdd-phase`  | `"tasks"`                                          | Always `"tasks"`                                 |
| `ticket`     | string                                             | External ticket reference (e.g., `"TICKET-123"`) |
| `depends-on` | `["design-*"]`                                     | References design doc                            |

#### Implementation Log (`type: "implementation-log"`)

| Field         | Valid Values / Pattern     | Notes                                               |
|:--------------|:---------------------------|:----------------------------------------------------|
| `id`          | `"impl-{name}"`            | Hierarchical: `"impl-{parent}-{name}"`              |
| `type`        | `"implementation-log"`     |                                                     |
| `status`      | `in-progress`, `completed` |                                                     |
| `sdd-phase`   | `"implement"`              | Always `"implement"`                                |
| `ticket`      | string                     | External ticket reference                           |
| `completed`   | string                     | Completion date (YYYY-MM-DD). Empty until completed |
| `implementer` | string                     | Name of the implementer                             |
| `depends-on`  | `["design-*"]`             | References design doc                               |

## Dependency Direction Rules

Dependencies (`depends-on`) point **upstream only** — toward higher-level documents. A document never references its
downstream documents.

```
prd ← spec (depends-on: ["prd-*"]) ← design (depends-on: ["spec-*"]) ← task (depends-on: ["design-*"])
                                   ← adr (depends-on: ["spec-*"])
                                                                       ← impl-log (depends-on: ["design-*"])
```

- **PRD**: May depend on parent PRDs only (`"prd-*"`)
- **Spec**: Depends on PRD (`"prd-*"`)
- **Design**: Depends on spec (`"spec-*"`)
- **ADR**: Depends on spec (`"spec-*"`). `supersedes` / `superseded-by` are lateral references between ADR
  entries, not upstream dependencies
- **Task**: Depends on design (`"design-*"`)
- **Implementation Log**: Depends on design (`"design-*"`)

## Validation Checklist

### Common Checks (All Documents)

| Check Item                  | Description                                                                                      | Importance |
|:----------------------------|:-------------------------------------------------------------------------------------------------|:-----------|
| **`id` format**             | Matches expected pattern for type (`prd-*`, `spec-*`, `design-*`, `task-*`, `impl-*`, `adr-*`)   | Medium     |
| **`type` correctness**      | Matches document location (`"prd"` for `requirement/`, `"spec"`/`"design"` for `specification/`, `"adr"` for `adr/`) | Medium |
| **`depends-on` references** | All referenced IDs exist in actual documents                                                     | High       |
| **`depends-on` direction**  | Dependencies point upstream only (spec→prd, design→spec, task→design)                            | High       |
| **`status` validity**       | Value is one of the allowed values for the document type                                         | Low        |
| **`id` uniqueness**         | No duplicate IDs across all documents in the project                                             | High       |

### Type-Specific Checks

| Document Type | Additional Check            | Description                                 | Importance |
|:--------------|:----------------------------|:--------------------------------------------|:-----------|
| PRD           | **`priority` validity**     | One of: `critical`, `high`, `medium`, `low` | Low        |
| PRD           | **`risk` validity**         | One of: `high`, `medium`, `low`             | Low        |
| Spec          | **`sdd-phase` correctness** | Must be `"specify"`                         | Low        |
| Design        | **`sdd-phase` correctness** | Must be `"plan"`                            | Low        |
| Design        | **`impl-status` accuracy**  | Matches actual implementation state         | Medium     |
| Task          | **`sdd-phase` correctness** | Must be `"tasks"`                           | Low        |
| Impl Log      | **`sdd-phase` correctness** | Must be `"implement"`                       | Low        |
| ADR           | **`sdd-phase` correctness** | Must be `"implement"`                       | Low        |
| ADR           | **`supersedes`/`superseded-by` consistency** | Referenced IDs exist and the reverse pointer is set on both entries | High |

### Cross-Reference Checks

| Check Item                 | Description                                                                | Importance |
|:---------------------------|:---------------------------------------------------------------------------|:-----------|
| **`status` consistency**   | Downstream documents should not be `approved` if upstream is still `draft` | Medium     |
| **`depends-on` integrity** | All referenced IDs exist in actual documents                               | High       |
| **Status propagation**     | Changes in upstream status may require downstream review                   | Medium     |

## Status Transition Rules

### PRD / Spec / Design

```
draft → review → approved → deprecated
```

### Task

```
pending → in-progress → completed
pending → cancelled
```

### Implementation Log

```
in-progress → completed
```

### ADR

ADR entries are append-only and do not follow the draft/review/approved lifecycle: an entry is written once a
decision is made. Validity is tracked by `superseded-by` rather than by rewriting `status` — an entry with
`superseded-by` set has been replaced by a later decision but its text is never edited.

### Design `impl-status` Transitions

```
not-implemented → in-progress → implemented
```

## Missing Front Matter Policy

- Documents without front matter remain valid (backward compatibility).
- If front matter is absent, note in reports: "Front matter not found. Consider adding YAML front matter for structured
  metadata."
- Do **not** treat missing front matter as a violation.
- When generating new documents, always include front matter.
- When updating existing documents that lack front matter, do not add it unless explicitly requested.
