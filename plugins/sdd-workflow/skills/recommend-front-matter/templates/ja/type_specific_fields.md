# タイプ別 Front Matter フィールド

ドキュメントの `type` フィールドに応じて追加するフィールド。

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

`ticket` は元の `task/{ticket-number}/` に到達可能な課題管理ツールが無かった場合のみ設定する。
`supersedes`/`superseded-by` は、このエントリが他のADRエントリを覆す、または覆される場合のみ設定する。

**Implementation Log** (`type: "implementation-log"`):

```yaml
sdd-phase: "implement"
ticket: ""
completed: ""
implementer: ""
```
