# Nine Category Analysis

Analyze specifications across these categories to identify ambiguity and gaps.

## Categories

| Category                           | Analysis Focus                       | Examples of Ambiguity                   |
|:-----------------------------------|:-------------------------------------|:----------------------------------------|
| **1. Functional Scope**            | What the feature does vs doesn't do  | Edge cases, boundary conditions         |
| **2. Data Model**                  | Data structures, types, constraints  | Field nullability, validation rules     |
| **3. Flow & Behavior**             | State transitions, error handling    | Rollback behavior, retry logic          |
| **4. Non-Functional Requirements** | Performance, security, scalability   | Response time requirements, rate limits |
| **5. Integrations**                | External system dependencies         | Authentication methods, API versions    |
| **6. Edge Cases**                  | Boundary conditions, error scenarios | Empty states, network failures          |
| **7. Constraints**                 | Technical limitations, trade-offs    | Browser support, data size limits       |
| **8. Terminology**                 | Domain-specific terms                | Consistent naming, acronym definitions  |
| **9. Completion Signals**          | "Done" criteria, success metrics     | Acceptance criteria, test coverage      |

## Clarity Level Classification

For each category, classify clarity as:

| Level       | Criteria                               | Example                             |
|:------------|:---------------------------------------|:------------------------------------|
| **Clear**   | Fully specified with explicit examples | "Return 404 when user ID not found" |
| **Partial** | Concept exists but details missing     | "Handle errors appropriately"       |
| **Missing** | Not mentioned in specifications        | No mention of authentication flow   |

## Category Analysis Summary (Required Output)

Record the Clear / Partial / Missing classification for **all 9 categories**, not only the ones that
become questions. A category that turns into no question still needs its classification and a one-line
basis (the specific statement, or its absence, that the classification rests on) recorded in the output.
Without this, the analysis's actual coverage — which categories were checked and how thoroughly — is
invisible to the reader, and detection granularity becomes unverifiable run to run.

```markdown
### Category Analysis Summary

| # | Category               | Classification | Basis                                    |
|:--|:------------------------|:----------------|:------------------------------------------|
| 1 | Functional Scope        | Clear/Partial/Missing | {statement, or "not mentioned"}     |
| ... (all 9 rows) |
```

## Question Prioritization

Generate up to 5 high-impact questions prioritizing:

**Selection Criteria**:

1. **Impact**: Would ambiguity cause major implementation divergence?
2. **Frequency**: Will this decision affect multiple modules?
3. **Risk**: Could wrong assumptions require significant rework?

## Question Format

```markdown
### Q{n}: {Category} - {Question Title}

**Context**: {Brief explanation of why this matters}

**Question**: {Specific question requiring user decision}

**Examples to Consider**:
- Option A: {Example}
- Option B: {Example}

**Current Specification State**: Clear / Partial / Missing
```
