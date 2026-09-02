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
| Implementation Status | 🟡 Warn | {count} items incomplete |

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

#### 🟡 Incomplete Items

##### API: Password Reset Function

**Specified**: Yes (spec §{section}, {requirement_id})

**Implemented**: Not found

**Recommendation**: Implement or remove from the spec

---

### Implementation Status Update

Updated spec implementation status:

- [x] User Login API → 🟢 Implemented
- [x] Logout API → 🟢 Implemented
- [ ] Password Reset API → 🔴 Not Implemented

### Next Actions

1. Fix mismatches:
    - Update `src/models/user.ts:10` type definition
2. Implement incomplete items:
    - Implement Password Reset API or remove from the spec

### Verification Commands

```bash
# Re-check after fixes
/check_spec {feature}

# Full review (document consistency + quality)
/check_spec {feature} --full
```
