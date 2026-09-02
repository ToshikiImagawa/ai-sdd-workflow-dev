## Spec & Implementation Consistency Check

### Target

- Spec: `${SDD_SPECIFICATION_PATH}/[{parent}/]{feature}[_spec].md`
- Design draft (auxiliary, only if present): `${SDD_TASK_PATH}/{ticket-number}/design-draft.md`
- Implementation: `{implementation_files}`

> Omit the design draft line when no draft exists — that is the normal state after implementation
> completes, not a finding.

### Consistency Check Results

#### Summary

| Category              | Status  | Details                  |
|:----------------------|:--------|:-------------------------|
| Public API            | 🟢 OK   | All APIs implemented     |
| Data Model            | 🔴 NG   | {count} mismatches found |
| Behavior              | 🟢 OK   | Matches the spec         |
| Literal Values        | 🟡 Warn | {count} value drifts     |
| Implementation Status | 🔴/🟡/🔵 | {critical_count} regression / {warning_count} undecidable / {info_count} expected-not-yet-implemented |

> Add a **Module Structure** row only when a design draft was loaded.

#### 🔴 Mismatches

##### Data Model: User Type Definition

**Spec**:

```typescript
interface User {
    id: string;
    name: string;
    email: string;
}
```

**Implementation**: `src/models/user.ts:10`

```typescript
interface User {
    id: number;  // ← Different type
    name: string;
    email: string;
}
```

**Impact**: Type mismatch causes runtime errors

**Fix Suggestion**: Change `id` to `string` type

---

#### 🟡 Value Drift

##### {value_name} (e.g., rag_confidence_threshold)

```
[WARN] Value drift detected: {value_name}
  spec: {spec_value} ({spec_section}, {requirement_id})
  {implementation_file}: {impl_value} ← drift
```

**Impact**: {impact description, e.g., gate threshold looser than specified}

**Fix Suggestion**: Align {implementation_file} with the spec value, or update the spec if the implementation is correct

---

#### Unimplemented Functions

A spec-documented function with no matching implementation is classified by the spec's `impl-status`:

| Function            | Spec Location                        | Spec `impl-status` | Classification            |
|:---------------------|:---------------------------------------|:----------------------|:----------------------------|
| Password Reset API  | spec §{section} ({requirement_id})   | `implemented`          | 🔴 Regression              |
| {feature_name}      | spec §{section} ({requirement_id})   | `not-implemented`      | 🔵 Expected (not due yet)  |
| {feature_name}      | spec §{section} ({requirement_id})   | Not set               | 🟡 Undecidable             |

**🔴 Regression example — API: Password Reset Function**

**Impact**: The spec declares this as implemented, but no matching code was found — likely a regression
(removed, or the field was set before the implementation actually landed).

**Recommendation**: Restore the implementation, or correct the spec's `impl-status` if it was never actually
implemented (and document why in the spec/adr). A 🟡 Undecidable row instead recommends adding `impl-status`
to the spec's front matter (`/recommend-front-matter` can suggest it); a 🔵 Expected row needs no action.

---

### Next Actions

1. Fix mismatches:
    - Update `src/models/user.ts:10` type definition
2. Address regressions (🔴 Unimplemented):
    - Restore Password Reset API, or correct its spec `impl-status`
3. Add `impl-status` to specs flagged as undecidable (🟡)

### Verification Commands

```bash
# Re-check after fixes
/check_spec {feature}

# Full review (document consistency + quality)
/check_spec {feature} --full
```
