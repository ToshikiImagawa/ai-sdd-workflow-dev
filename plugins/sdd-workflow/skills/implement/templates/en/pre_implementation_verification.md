# Pre-Implementation Verification

## Load and Verify Documents

```
1. Load task breakdown: ${SDD_TASK_PATH}/{ticket}/tasks.md
2. Load design draft: ${SDD_TASK_PATH}/{ticket}/design-draft.md
3. Load abstract spec: ${SDD_SPECIFICATION_PATH}/[{path}/]{feature}.md or {feature}_spec.md
4. Load PRD (if exists): ${SDD_REQUIREMENT_PATH}/[{path}/]{feature}.md
```

**Note the difference in naming conventions**:

- **Under requirement**: No suffix (`index.md`, `{feature-name}.md`)
- **Under specification**: `_spec` suffix optional (`index_spec.md`, `{feature-name}_spec.md`, or no suffix) —
  either form satisfies step 3
- **Under task**: Design draft uses the fixed filename `design-draft.md`, ticket-scoped and independent of
  the spec's flat/hierarchical structure
