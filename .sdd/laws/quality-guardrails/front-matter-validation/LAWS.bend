# spec: spec-quality-guardrails-front-matter-validation
#
# Laws derived from front-matter-validation_spec 3.1.1 (severity decision table).
# The full table has 19 rows; rank --max 10 cuts the candidates off at 10 (NFR-005).
# The remaining 9 rows are listed as rejected (reason: limit) in the draft report.
# Model API not fixed (no main.bend yet): proposed below, needs confirmation.
# Unapproved: a human reviewer appends the approval line after review.

import Base
import ./main.bend as Model

# model-api: Model.severity_for_check(check_id: Nat) -> Nat
# check_id (table row #): 3=depends-on reversed, 4=cross-ref id duplicate,
#   5=cross-ref depends-on target missing, 6=cross-ref laws: dir missing,
#   7=cross-ref LAWS.bend # spec: mismatch, 8=cross-ref orphan laws,
#   9=id format mismatch, 10=created/updated date format invalid,
#   11=enum value out of range, 16=front matter missing
# severity codes: 0=error, 1=warning, 2=info

# source: spec-quality-guardrails-front-matter-validation §3.1.1 sha256:9c3b6f01cc11
law depends_on_reversed_is_error:
  {Model.severity_for_check(3n) == 0n : Nat}

# source: spec-quality-guardrails-front-matter-validation §3.1.1 sha256:9c3b6f01cc11
law crossref_id_duplicate_is_error:
  {Model.severity_for_check(4n) == 0n : Nat}

# source: spec-quality-guardrails-front-matter-validation §3.1.1 sha256:9c3b6f01cc11
law crossref_depends_on_missing_is_error:
  {Model.severity_for_check(5n) == 0n : Nat}

# source: spec-quality-guardrails-front-matter-validation §3.1.1 sha256:9c3b6f01cc11
law crossref_laws_dir_missing_is_error:
  {Model.severity_for_check(6n) == 0n : Nat}

# source: spec-quality-guardrails-front-matter-validation §3.1.1 sha256:9c3b6f01cc11
law crossref_laws_spec_id_mismatch_is_error:
  {Model.severity_for_check(7n) == 0n : Nat}

# source: spec-quality-guardrails-front-matter-validation §3.1.1 sha256:9c3b6f01cc11
law crossref_orphan_laws_is_error:
  {Model.severity_for_check(8n) == 0n : Nat}

# source: spec-quality-guardrails-front-matter-validation §3.1.1 sha256:9c3b6f01cc11
law id_format_mismatch_is_warning:
  {Model.severity_for_check(9n) == 1n : Nat}

# source: spec-quality-guardrails-front-matter-validation §3.1.1 sha256:9c3b6f01cc11
law date_format_invalid_is_warning:
  {Model.severity_for_check(10n) == 1n : Nat}

# source: spec-quality-guardrails-front-matter-validation §3.1.1 sha256:9c3b6f01cc11
law enum_value_out_of_range_is_warning:
  {Model.severity_for_check(11n) == 1n : Nat}

# source: spec-quality-guardrails-front-matter-validation §3.1.1 sha256:9c3b6f01cc11
law front_matter_missing_is_info:
  {Model.severity_for_check(16n) == 2n : Nat}
