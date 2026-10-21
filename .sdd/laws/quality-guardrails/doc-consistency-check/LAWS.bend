# spec: spec-quality-guardrails-doc-consistency-check
#
# Laws derived from doc-consistency-check_spec 3.1.1 (upstream precedence order)
# and 3.1.2 (sdd-version FR-007 inclusion decision table).
# Model API not fixed (no main.bend yet): proposed below, needs confirmation.
# Unapproved: a human reviewer appends the approval line after review.

import Base
import ./main.bend as Model

# model-api: Model.precedence(layer: Nat) -> Nat
# layer codes: 0=PRD, 1=spec, 2=design. Lower return value = higher precedence
# (the layer whose description is taken as authoritative on conflict).
# model-api: Model.is_fr007_target(sdd_version_state: Nat) -> Bool
# sdd_version_state codes: 0=absent, 1=present and major < current plugin major,
#   2=present and major >= current plugin major

# source: spec-quality-guardrails-doc-consistency-check §3.1.1 sha256:b50d498f5bd7
law prd_outranks_spec:
  {Model.precedence(0n) < Model.precedence(1n) : Bool}

# source: spec-quality-guardrails-doc-consistency-check §3.1.1 sha256:b50d498f5bd7
law spec_outranks_design:
  {Model.precedence(1n) < Model.precedence(2n) : Bool}

# source: spec-quality-guardrails-doc-consistency-check §3.1.1 sha256:b50d498f5bd7
law prd_outranks_design:
  {Model.precedence(0n) < Model.precedence(2n) : Bool}

# source: spec-quality-guardrails-doc-consistency-check §3.1.2 sha256:8320d5156c4f
law sdd_version_absent_is_not_fr007_target:
  {Model.is_fr007_target(0n) == False{} : Bool}

# source: spec-quality-guardrails-doc-consistency-check §3.1.2 sha256:8320d5156c4f
law sdd_version_older_major_is_fr007_target:
  {Model.is_fr007_target(1n) == True{} : Bool}

# source: spec-quality-guardrails-doc-consistency-check §3.1.2 sha256:8320d5156c4f
law sdd_version_current_major_is_not_fr007_target:
  {Model.is_fr007_target(2n) == False{} : Bool}
