# HTML Structure Contract

This skill composes the output HTML from three template layers instead of converting Markdown
line-by-line. This is what keeps the result "structured by decision / rationale / rejected
alternatives" rather than a surface-level Markdown-to-HTML pass.

## Template Layers

| Layer | File | Repeats | Purpose |
|:--|:--|:--|:--|
| Shell | `templates/${SDD_LANG:-en}/review_shell.md` | Once | Page chrome: `<style>`, header banner, footer notice |
| Decision card | `templates/${SDD_LANG:-en}/decision_card.md` | Once per ADR/decision entry | One `<section>` per decision: title, context, rationale |
| Comparison row | `templates/${SDD_LANG:-en}/alternative_row.md` | Once per option considered (adopted + rejected) | One `<tr>` in the comparison table |

Render bottom-up: fill each `alternative_row.md` copy, join them into `{alternative_rows}`, fill
`decision_card.md` with that and the decision's own fields, join the cards into
`{decision_cards}`, then fill `review_shell.md`.

## Placeholder Reference

| Placeholder | Layer | Content |
|:--|:--|:--|
| `{header_title}` | shell | Feature/ticket name being reviewed |
| `{header_meta}` | shell | Source file path(s) and generation context |
| `{decision_cards}` | shell | Concatenated rendered `decision_card.md` blocks |
| `{decision_anchor}` | card | Slug for the `id` attribute (anchor links from the header) |
| `{decision_title}` | card | The decision statement itself |
| `{decision_date}` | card | Date/context recorded with the entry, if any |
| `{decision_rationale}` | card | Why this option was chosen |
| `{alternative_rows}` | card | Concatenated rendered `alternative_row.md` blocks (adopted row first, then rejected) |
| `{option_name}` | row | Name of the option (the adopted decision, or a rejected alternative) |
| `{option_summary}` | row | One-line description of the option |
| `{option_verdict_reason}` | row | Why it was adopted, or why it was rejected |
| `{verdict_class}` | row | `verdict-adopted` or `verdict-rejected` (drives the highlight styling) |
| `{verdict_label}` | row | Localized label ("Adopted"/"Rejected" or "採用"/"却下") |

## Highlighting Rule

The comparison table always lists the adopted decision as its first row (`verdict-adopted`,
highlighted) followed by every rejected alternative recorded in the source entry
(`verdict-rejected`, muted/struck-through). If the source entry recorded no rejected
alternatives, omit the table and render only the rationale section — do not invent alternatives
that were not in the source.

## Non-Goals

- Do not pipe the source Markdown through a generic renderer and drop the result into a single
  `<div>` — every entry must land in its own card with rationale and alternatives in distinct
  regions, or this skill degenerates into the plain conversion it exists to avoid.
- Do not add navigation, search, or multi-page output — this is a single-file scratch artifact for
  one review session (see `SKILL.md` Output section for the non-persistence rule).
