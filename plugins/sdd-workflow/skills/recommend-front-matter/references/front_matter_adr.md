# Front Matter Reference — ADR

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

### ADR (`type: "adr"`) — persistent decision log under `adr/{feature-name}.md`

| Field            | Valid Values / Pattern              | Notes                                                                  |
|:-----------------|:-------------------------------------|:------------------------------------------------------------------------|
| `id`             | `"adr-{name}"`                       | Hierarchical: `"adr-{parent}-{name}"`                                   |
| `type`           | `"adr"`                              |                                                                          |
| `sdd-phase`      | `"implement"`                        | Always `"implement"`                                                    |
| `depends-on`     | `["spec-*"]`                         | References the spec whose decisions this entry records                  |
| `ticket`         | string                               | External ticket reference (e.g., `"TICKET-123"`) of the implementation that produced this entry. Optional, but set it when the source `task/{ticket-number}/` had no reachable issue tracker to record completion in |
| `supersedes`     | list of `"adr-*"`                    | IDs of prior entries this decision replaces. Omit if this is not a reversal |
| `superseded-by`  | `"adr-*"`                            | ID of the entry that later replaced this decision. Absent while still current |

ADR does not use the `status` field's usual draft/review/approved/deprecated lifecycle — see "Status Transition
Rules" below. `adr/` is append-only: past entries are never rewritten. When a decision is reversed, append a new
entry with `supersedes` pointing at the old one, and set `superseded-by` on the old entry to point at the new one.

## Dependency Direction Rules

Dependencies (`depends-on`) point **upstream only** — toward higher-level documents. A document never references its
downstream documents.

```
prd ← spec (depends-on: ["prd-*"]) ← adr (depends-on: ["spec-*"])
```

- **ADR**: Depends on spec (`"spec-*"`). `supersedes` / `superseded-by` are lateral references between ADR
  entries, not upstream dependencies.

## Validation Checklist

### Common Checks (All Documents)

| Check Item                  | Description                                                                                      | Importance |
|:----------------------------|:----------------------------------------------------------------------------------------------------|:-----------|
| **`id` format**             | Matches expected pattern for type (`adr-*`)                                                      | Medium     |
| **`type` correctness**      | Matches document location (`"adr"` for `adr/`)                                                    | Medium     |
| **`depends-on` references** | All referenced IDs exist in actual documents                                                      | High       |
| **`depends-on` direction**  | Dependencies point upstream only (adr→spec)                                                       | High       |
| **`id` uniqueness**         | No duplicate IDs across all documents in the project                                              | High       |

### ADR-Specific Checks

| Check Item                                    | Description                                                          | Importance |
|:-----------------------------------------------|:-----------------------------------------------------------------------|:-----------|
| **`sdd-phase` correctness**                    | Must be `"implement"`                                                  | Low        |
| **`supersedes`/`superseded-by` consistency**   | Referenced IDs exist and the reverse pointer is set on both entries    | High       |

## Status Transition Rules

### ADR

ADR entries are append-only and do not follow the draft/review/approved/deprecated lifecycle: an entry is written
once a decision is made. Validity is tracked by `superseded-by` rather than by rewriting `status` — an entry with
`superseded-by` set has been replaced by a later decision but its text is never edited.

## Missing Front Matter Policy

- Documents without front matter remain valid (backward compatibility).
- If front matter is absent, note in reports: "Front matter not found. Consider adding YAML front matter for structured
  metadata."
- Do **not** treat missing front matter as a violation.
- When generating new documents, always include front matter.
- When updating existing documents that lack front matter, do not add it unless explicitly requested.
