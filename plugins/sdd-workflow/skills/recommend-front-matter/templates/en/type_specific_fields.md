# Type-Specific Front Matter Fields

Additional fields to include based on the document `type` field.

**PRD** (`type: "prd"`):

```yaml
priority: "medium"
risk: "medium"
```

**Spec** (`type: "spec"`):

```yaml
sdd-phase: "specify"
impl-status: "not-implemented"
```

**Design** (`type: "design"`):

```yaml
sdd-phase: "plan"
impl-status: "not-implemented"
```

**Task** (`type: "task"`):

```yaml
sdd-phase: "tasks"
ticket: ""
```

**ADR** (`type: "adr"`):

```yaml
sdd-phase: "implement"
```

Set `ticket` only if the source `task/{ticket-number}/` had no reachable issue tracker to record completion in.
Set `supersedes`/`superseded-by` only when this entry reverses, or is reversed by, another ADR entry.

**Implementation Log** (`type: "implementation-log"`):

```yaml
sdd-phase: "implement"
ticket: ""
completed: ""
implementer: ""
```
