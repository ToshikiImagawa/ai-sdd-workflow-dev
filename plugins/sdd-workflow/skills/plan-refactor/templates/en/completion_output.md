# Completion Output Templates

## Phase 5: Next Steps Summary

```
✅ Refactoring plan completed

**Generated/Updated Files:**
- {spec_path} (Case B only — persistent, reverse-engineered spec)
- {design_draft_path} (temporary draft, deleted after implementation)

**Refactoring Plan Location:**
{design_draft_path} - "Refactoring Plan" section

**Next Steps:**
1. Review the refactoring plan at: {design_draft_path}
2. Run `/task-breakdown {feature-name}` to break down the refactoring into actionable tasks
3. Execute tasks with `/implement {feature-name}` using TDD approach
4. When implementation completes, run `/task-cleanup {feature-name}` to append the settled decisions to
   ${SDD_ADR_PATH}/{feature-name}.md — the draft (and this plan) is deleted at that point, so the decision
   log is the only lasting record
```

## Output Format

```
File: {file_path}
Persistence: {Persistent (specification/) | Temporary draft (task/{ticket-number}/)}
Status: {Created/Updated}
Sections Added: Refactoring Plan
```
