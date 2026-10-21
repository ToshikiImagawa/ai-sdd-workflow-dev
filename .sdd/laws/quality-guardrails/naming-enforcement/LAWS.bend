# spec: spec-quality-guardrails-naming-enforcement
#
# Laws derived from naming-enforcement_spec 3.1.1 (naming validation decision table).
# Model API not fixed (no main.bend yet): proposed below, needs confirmation.
# Unapproved: a human reviewer appends the approval line after review.

import Base
import ./main.bend as Model

# model-api: Model.decide(is_md: Bool, ignore_match: Bool, is_requirement_dir: Bool,
#   has_suffix: Bool) -> Nat
# result codes: 0=allow (not .md), 1=allow (ignore_patterns match), 2=deny
#   (requirement/ with _spec/_design suffix), 3=allow (fallthrough)

# source: spec-quality-guardrails-naming-enforcement §3.1.1 sha256:e7e118384ddc
law non_md_is_allowed:
  {Model.decide(False{}, False{}, False{}, False{}) == 0n : Nat}

# source: spec-quality-guardrails-naming-enforcement §3.1.1 sha256:e7e118384ddc
law ignore_pattern_match_is_allowed:
  {Model.decide(True{}, True{}, True{}, True{}) == 1n : Nat}

# source: spec-quality-guardrails-naming-enforcement §3.1.1 sha256:e7e118384ddc
law requirement_with_suffix_is_denied:
  {Model.decide(True{}, False{}, True{}, True{}) == 2n : Nat}

# source: spec-quality-guardrails-naming-enforcement §3.1.1 sha256:e7e118384ddc
law requirement_without_suffix_is_allowed:
  {Model.decide(True{}, False{}, True{}, False{}) == 3n : Nat}

# source: spec-quality-guardrails-naming-enforcement §3.1.1 sha256:e7e118384ddc
law non_requirement_dir_is_allowed:
  {Model.decide(True{}, False{}, False{}, True{}) == 3n : Nat}
