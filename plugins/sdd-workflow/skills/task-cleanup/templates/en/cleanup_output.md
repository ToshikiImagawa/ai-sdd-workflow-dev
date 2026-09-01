## Task Cleanup Confirmation

### Target

- Directory: `${SDD_TASK_PATH}/{target}/`

### Analysis Results

#### Integration Status

| File                         | Decisions / Rejected Alternatives | Status       |
|:-----------------------------|:-----------------------------------|:-------------|
| `implementation_log_{id}.md` | {decision count}                   | To Integrate |
| `implementation_log_{id}.md` | {decision count}                   | To Integrate |

**Total**: {count} entries to append to `adr/{feature}.md`

#### Files to Delete

- [ ] `${SDD_TASK_PATH}/{target}/implementation_log_{id}.md`
- [ ] `${SDD_TASK_PATH}/{target}/implementation_log_{id}.md`
- [ ] `${SDD_TASK_PATH}/{target}/tasks.md`

### Spec Update Judgement

| Decision | Trigger Matched | Recommendation |
|:---------|:-----------------|:----------------|
| {decision} | {Public API change / New data model / Behavior change / None} | {Propose update to `{name}_spec.md` / No spec update needed} |

### Ticket Dump

- Ticket: `{ticket-number}`
- Summary to post: {one-paragraph summary of appended decisions, spec update outcome, and deleted files}

### Next Actions

1. **Append decisions to ADR**:
    - Append {decision} to `${SDD_ADR_PATH}/{feature}.md`
    - Append {decision} to `${SDD_ADR_PATH}/{feature}.md`

2. **Delete processed files**:
    - Delete `${SDD_TASK_PATH}/{target}/` directory

3. **Post summary to ticket `{ticket-number}`**

Would you like to proceed with cleanup?
