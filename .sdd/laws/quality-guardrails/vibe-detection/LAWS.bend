# spec: spec-quality-guardrails-vibe-detection
#
# Law derived from vibe-detection_spec 3.1.1 (risk-level exhaustiveness/exclusivity
# invariant). Pattern matching of ambiguous expressions (FR-002) is excluded from
# lawification (laws-drafting_spec extraction rule).
# Model API not fixed (no main.bend yet): proposed below, needs confirmation.
# Unapproved: a human reviewer appends the approval line after review.

import Base
import ./main.bend as Model

# model-api: Model.risk_level(signal: Nat) -> Nat
# return codes: 0=High, 1=Medium, 2=Low (a total function: every input maps to
# exactly one of these three codes by construction)
# model-api: Model.is_valid_risk_level(level: Nat) -> Bool

# source: spec-quality-guardrails-vibe-detection §3.1.1 sha256:676b3b698496
law risk_level_is_always_one_of_high_medium_low:
  for signal: Nat
  {Model.is_valid_risk_level(Model.risk_level(signal)) == True{} : Bool}
