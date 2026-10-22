# spec: spec-quality-guardrails-stale-doc-detection
#
# Laws derived from stale-doc-detection_spec 3.1.1 (file category decision table).
# Model API not fixed (no main.bend yet): proposed below, needs confirmation.
# Unapproved: a human reviewer appends the approval line after review.
# approved: 2026-10-21 @ToshikiImagawa sha256:568e042f05d2

import Base
import ./main.bend as Model

# model-api: Model.category_for_path(path_kind: Nat) -> Nat
# path_kind codes: 0=specification/ (spec), 1=specification/ with laws: front matter,
#   2=requirement/ (PRD), 3=adr/ (decision log), 4=laws/**/*.bend, 5=source with matching spec,
#   6=source modeled by main.bend's # model-of:, 7=none of the above (no trigger)
# category codes: 0=FR-001 (PRD<->spec<->adr check), 1=FR-009 (laws re-extraction),
#   2=FR-002 (downstream spec propagation), 3=FR-006 (adr append-only + spec reflection),
#   4=FR-007 (proof gate re-run), 5=FR-003 (spec sync), 6=FR-008 (reference model review),
#   7=FR-005 (no output)

# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
law spec_edit_triggers_fr001:
  {Model.category_for_path(0n) == 0n : Nat}

# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
law spec_with_laws_triggers_fr009:
  {Model.category_for_path(1n) == 1n : Nat}

# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
law prd_edit_triggers_fr002:
  {Model.category_for_path(2n) == 2n : Nat}

# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
law adr_edit_triggers_fr006:
  {Model.category_for_path(3n) == 3n : Nat}

# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
law law_file_edit_triggers_fr007:
  {Model.category_for_path(4n) == 4n : Nat}

# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
law source_with_spec_triggers_fr003:
  {Model.category_for_path(5n) == 5n : Nat}

# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
law source_modeled_triggers_fr008:
  {Model.category_for_path(6n) == 6n : Nat}

# source: spec-quality-guardrails-stale-doc-detection §3.1.1 sha256:b77949cbd9e8
law unrelated_edit_is_silent:
  {Model.category_for_path(7n) == 7n : Nat}
