# Existing Document Check

## For Flat Structure

```
Does ${CLAUDE_PROJECT_DIR}/${SDD_REQUIREMENT_PATH}/{feature-name}.md exist? (PRD)
Does ${CLAUDE_PROJECT_DIR}/${SDD_SPECIFICATION_PATH}/{feature-name}_spec.md already exist?
```

## For Hierarchical Structure (when placing under parent feature)

```
Does ${CLAUDE_PROJECT_DIR}/${SDD_REQUIREMENT_PATH}/{parent-feature}/index.md exist? (parent feature PRD)
Does ${CLAUDE_PROJECT_DIR}/${SDD_REQUIREMENT_PATH}/{parent-feature}/{feature-name}.md exist? (child feature PRD)
Does ${CLAUDE_PROJECT_DIR}/${SDD_SPECIFICATION_PATH}/{parent-feature}/index_spec.md already exist? (parent feature spec)
Does ${CLAUDE_PROJECT_DIR}/${SDD_SPECIFICATION_PATH}/{parent-feature}/{feature-name}_spec.md already exist? (child feature spec)
```

## Design Doc Draft (ticket-scoped, independent of flat/hierarchical structure)

```
Does ${CLAUDE_PROJECT_DIR}/${SDD_TASK_PATH}/{ticket-number}/design-draft.md already exist?
```
