# Document Consistency Check Results Template

This template is the output format for document consistency check results.

---

## Document Consistency Check Results

### Target Documents

| Document | Path                                          | Last Updated |
|:---------|:----------------------------------------------|:-------------|
| PRD      | `${SDD_REQUIREMENT_PATH}/{feature-name}.md`          | YYYY-MM-DD   |
| spec     | `${SDD_SPECIFICATION_PATH}/{feature-name}_spec.md`   | YYYY-MM-DD   |
| adr      | `${SDD_ADR_PATH}/{feature-name}.md`                  | YYYY-MM-DD   |

### Check Results Summary

| Check Target            | Result                    | Count     |
|:------------------------|:--------------------------|:----------|
| PRD ↔ spec              | Consistent / Inconsistent | {n} items |
| spec ↔ adr              | Consistent / Inconsistent | {n} items |

---

### Inconsistency Details

#### PRD ↔ spec

##### 1. {Inconsistency Title}

**Type**: Missing / Contradiction / Obsolescence

**PRD States**:

```markdown
{PRD content}
```

**spec States**:

```markdown
{spec content (or "Not documented")}
```

**Recommended Action**:

- [ ] Update spec to reflect requirement
- [ ] If PRD requirement is unnecessary, remove it

> **Note**: If the type is `Contradiction`, or `Missing` in the PRD → spec direction (a new behavior no PRD
> requirement covers), always report this item as `[must]` and do **not** edit the PRD automatically. Present
> the conflicting spec change and the affected PRD requirement, and let a human decide whether to update the
> PRD, revert the spec change, or accept it as an intentional scope change.

---

#### spec ↔ adr

##### 1. {Inconsistency Title}

**Type**: Missing / Contradiction / Obsolescence

**spec States**:

```
{spec content}
```

**adr States**:

```
{adr content (or "Not documented")}
```

**Recommended Action**:

- [ ] Append a new entry to adr to capture the decision behind the spec change
- [ ] If the adr entry is now stale (the spec element it describes was changed/removed), flag it for a
      follow-up append — never rewrite the existing entry

---

> **Note**: `spec ↔ Implementation` and any remaining `*_design.md` artifact checks are out of scope for this
> skill. Use `/check-spec` (the `impl-spec-check` feature) for those checks.

### Verified Consistent Items

- {Verified item 1}
- {Verified item 2}

---

### Recommended Actions (Prioritized)

1. **High Priority**: {Action}
2. **Medium Priority**: {Action}
3. **Low Priority**: {Action}

---

### Notes

- {Supplementary notes}
