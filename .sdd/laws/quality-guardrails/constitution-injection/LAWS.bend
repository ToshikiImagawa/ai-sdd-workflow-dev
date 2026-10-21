# spec: spec-quality-guardrails-constitution-injection
#
# Laws derived from constitution-injection_spec 3.1.1 (injection decision table).
# The 3,000-character truncation (FR-004) is output formatting and is excluded
# from lawification (laws-drafting_spec extraction rule).
# Model API not fixed (no main.bend yet): proposed below, needs confirmation.
# Unapproved: a human reviewer appends the approval line after review.

import Base
import ./main.bend as Model

# model-api: Model.should_inject(constitution_exists: Bool, is_source_code: Bool,
#   already_injected: Bool) -> Bool

# source: spec-quality-guardrails-constitution-injection §3.1.1 sha256:4597189a8440
law no_constitution_means_no_injection:
  {Model.should_inject(False{}, True{}, False{}) == False{} : Bool}

# source: spec-quality-guardrails-constitution-injection §3.1.1 sha256:4597189a8440
law non_source_edit_means_no_injection:
  {Model.should_inject(True{}, False{}, False{}) == False{} : Bool}

# source: spec-quality-guardrails-constitution-injection §3.1.1 sha256:4597189a8440
law already_injected_means_no_injection:
  {Model.should_inject(True{}, True{}, True{}) == False{} : Bool}

# source: spec-quality-guardrails-constitution-injection §3.1.1 sha256:4597189a8440
law first_source_edit_with_constitution_injects:
  {Model.should_inject(True{}, True{}, False{}) == True{} : Bool}
