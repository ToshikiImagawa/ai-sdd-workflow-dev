### Document Dependencies

#### Creation Order

Documents are created in the following order, where each document references its upstream documents:

```
CONSTITUTION.md → requirement/ (PRD) → specification/*_spec.md → task/{ticket-number}/design-draft.md → Implementation
task/{ticket-number}/design-draft.md → adr/{feature}-decisions.md
```

**Direction meaning**: `A → B` means "B is created referencing A". Upstream documents serve as the source of truth for downstream documents.

- `CONSTITUTION.md`: Project principles (top-level, all documents must comply)
- `requirement/`: PRD/Requirements documents (created following CONSTITUTION)
- `specification/*_spec.md`: Abstract specifications (derived from requirements)
- `task/{ticket-number}/design-draft.md`: Technical design draft (detailed from specifications, temporary)
- `Implementation`: Source code (implemented according to tasks/designs)
- `adr/{feature}-decisions.md`: Decision log (rationale extracted from design-draft.md before it is deleted, persistent)

#### Verification Direction

Consistency checks verify in the reverse direction — from downstream back to upstream:

```
Implementation → task/{ticket-number}/design-draft.md → specification/*_spec.md → requirement/ → CONSTITUTION.md
```

Each downstream document is checked against its upstream source of truth. When inconsistencies are found, prioritize upstream documents (PRD > spec > design draft).

Once `task/{ticket-number}/design-draft.md` is deleted after implementation, its persisted decisions live on in `adr/{feature}-decisions.md`, and ongoing checks compare that against its upstream source:

```
adr/{feature}-decisions.md → specification/*_spec.md
```

#### Document Persistence

| Document | Persistence | Rules |
|:--|:--|:--|
| `CONSTITUTION.md` | **Persistent** | Project principles. Updated only through `/constitution` |
| `requirement/*.md` | **Persistent** | PRD/Requirements. Updated when business requirements change |
| `specification/*_spec.md` | **Persistent** | Abstract specifications. Updated when requirements change |
| `task/` (including `{ticket-number}/design-draft.md`) | **Temporary** | **Delete after implementation complete**. Integrate important decisions and their rationale into `adr/{feature}-decisions.md` before deletion |
| `adr/{feature}-decisions.md` | **Persistent** | **Append-only** log of decisions and their rationale (including rejected alternatives). Never rewrite past entries |

#### Change Propagation

When an upstream document changes, downstream documents may need updates:

| Changed Document | Impact Scope | Update Condition |
|:--|:--|:--|
| `CONSTITUTION.md` | All downstream | Principle changes affect all documents |
| `requirement/` | `specification/*_spec.md`, `task/{ticket-number}/design-draft.md` | New/changed/deleted requirements must be reflected |
| `specification/*_spec.md` | `task/{ticket-number}/design-draft.md` | API signature, data model, or behavior changes |
| `task/{ticket-number}/design-draft.md` | Implementation, `adr/{feature}-decisions.md` | Architecture or interface changes; finalized decisions must be appended to `adr/` before `task/` deletion |

**When updates are NOT needed**:

- Internal implementation optimization (no interface changes)
- Bug fixes (correcting deviations from specifications)
- Refactoring (no behavior changes)

**ADR recording trigger** — append to `adr/{feature}-decisions.md` when:

- Any `task/{ticket-number}/design-draft.md` change listed above is finalized at implementation completion
- An alternative approach is rejected and the rationale is worth recording for future readers

#### Cross-Reference Rules

Documents reference each other using requirement IDs to maintain traceability:

| ID Format | Type | Example |
|:--|:--|:--|
| `UR-xxx` | User Requirements | `UR-001`: User can log in |
| `FR-xxx` | Functional Requirements | `FR-001`: Authenticate via OAuth |
| `NFR-xxx` | Non-Functional Requirements | `NFR-001`: Response time < 200ms |

**Traceability chain**:

```
requirement/ (defines UR/FR/NFR) → specification/*_spec.md (references FR/NFR) → task/{ticket-number}/design-draft.md (implements FR/NFR) → adr/{feature}-decisions.md (records rationale)
```

- `specification/*_spec.md` must reference PRD requirement IDs in its "Functional Requirements" section
- `task/{ticket-number}/design-draft.md` must trace design decisions back to spec requirements
- `adr/{feature}-decisions.md` must record the rationale for finalized design decisions before `task/{ticket-number}/design-draft.md` is deleted
