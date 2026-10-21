# Ambiguity Assessment Criteria

Single place for the criteria used to judge ambiguity. Consumers (`vibe-detector`, and the skills that follow its risk wording) reference this file instead of restating the criteria.

All ratios and thresholds here are **guidance**, not fixed cut-offs. The judgment is made per requirement; the overall level is a reading of those judgments.

## 1. Per-Requirement Marks (○ / △ / ×)

Judge each requirement (FR, NFR, or a stated request item) on its own. The marks correspond to the clarity scale used by `/clarify`: ○ = Clear, △ = Partial, × = Missing.

| Mark | Meaning | Test |
|:-----|:--------|:-----|
| ○ | Clear | A third party can decide pass/fail from the text alone: target, inputs/outputs, error behavior, boundary conditions, and completion criteria that apply to the requirement are all stated |
| △ | Partial | The requirement is stated but at least one applicable item is missing or vague (e.g., a target without a value, a success path without error cases) |
| × | Missing | The requirement is absent, or only names a topic with nothing to judge against ("Create X feature", "improve performance") |

Rules:

- Judge only items that apply to the requirement; mark an item N/A explicitly rather than counting it as missing
- When unsure between two marks, choose the lower one and list the missing item as a clarification question
- For an NFR, use the quantification levels in `nfr_checklist.md` (Section 3) instead of the test above

### Ratio Guidance (when a PRD or spec exists)

Let n = number of judged requirements. Read the marks as a distribution, not a score to compute:

| Reading | Guidance |
|:--------|:---------|
| Low-ambiguity | Almost all ○; no × |
| Medium-ambiguity | ○ is the majority, with some △; × is rare and each is already listed as a question |
| High-ambiguity | △ and × are the majority, or × appears on core requirements |

A single × on a core requirement outweighs a high ○ ratio. Report the counts (○ / △ / ×) with the judgment so the reader can disagree.

## 2. Risk Level Viewpoints (for `vibe-detector`)

`vibe-detector` also receives input with no PRD or spec (a one-line request), so a ratio cannot always be computed. Decide High / Medium / Low from the **viewpoint checks** below instead.

### Viewpoints

For the request (and the specs, if any), mark each as ○ / △ / ×:

| # | Viewpoint | ○ when |
|:--|:----------|:-------|
| V1 | Target and purpose | What is built or changed, and why, is identifiable |
| V2 | Inputs/outputs | Arguments, return values, data shapes are stated |
| V3 | Error handling | Abnormal-case behavior is stated |
| V4 | Boundary conditions | Limits and edge cases are stated |
| V5 | Completion criteria | "Done" can be verified |
| V6 | Non-functional targets | Performance/security/etc. targets that matter here are quantified (see Section 3). N/A when no NFR is relevant to the request |

### Decision

| Level | Condition |
|:------|:----------|
| **High** | No specs exist and at least one of V1–V5 is × (vague instructions) |
| **Medium** | Specs exist and at least one viewpoint is △ or ×; or no specs exist but V1–V5 are all stated in the request (a spec is still needed) |
| **Low** | Specs exist and all applicable viewpoints are ○ |

This is the same High/Medium/Low definition as the table in `vibe-detector`; this section only makes "vague" and "some ambiguity" checkable. Task type is determined separately.

## 3. NFR: Using `nfr_checklist.md`

Do not invent a second scale for NFRs. Take the level (0–3) of each category from `nfr_checklist.md` and map it to a mark per its "Mapping to Risk Tiers" section:

| NFR level | Mark |
|:----------|:-----|
| 0 Not stated | × |
| 1 Mention only | △ |
| 2 Target value, 3 Target + condition + measurement | ○ |

### Aggregating the Seven Categories

The seven categories are Performance, Security, Reliability, Scalability, Usability, Maintainability, Compatibility.

1. Decide which categories are **in scope** for the product. A category left unmentioned is Level 0 (×), not out of scope. It is out of scope only when the PRD or spec says so explicitly
2. Mark each in-scope category
3. The **NFR mark** is the lowest mark among in-scope categories (any × → ×; else any △ → △; else ○)
4. Report the per-category marks alongside the NFR mark, so one weak category is visible and the others are not hidden

Use the NFR mark as the V6 value in Section 2, and as one requirement-level mark in the distribution in Section 1.

Level 3 vs Level 2 does not change the mark; it is a quality note ("measurement method missing"), not a risk difference.
