### AI-SDD Principles Document

**Before execution, read only the sections of the AI-SDD principles document that this skill / agent needs. Do not read the whole file.**

AI-SDD principles document path: `${SDD_ROOT}/AI-SDD-PRINCIPLES.md`

The sections to read are named by the caller (the `Prerequisites` list of the skill, or the agent's `Prerequisites` section),
written as `§ <heading>`. To read a section:

1. Locate it: `grep -n '^#\{2,3\} ' ${SDD_ROOT}/AI-SDD-PRINCIPLES.md` lists every heading with its line number.
2. Read just that range with `Read` (`offset` = the heading's line, `limit` = up to the next heading of the same or higher level).

If the caller names no section, read nothing beyond what the task requires and look up a section only when a rule is in question.

**Note**: This file is automatically updated at the start of each session.
