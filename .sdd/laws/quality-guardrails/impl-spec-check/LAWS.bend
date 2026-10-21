# spec: spec-quality-guardrails-impl-spec-check
#
# Laws derived from impl-spec-check_spec 3.1.1 (impl-status -> severity decision table).
# Model API not fixed (no main.bend yet): proposed below, needs confirmation.
# Unapproved: a human reviewer appends the approval line after review.

import Base
import ./main.bend as Model

# model-api: Model.severity_for_missing_impl(impl_status: Nat) -> Nat
# impl_status codes: 0=implemented, 1=not-implemented, 2=in-progress, 3=unset (field absent)
# severity codes: 0=Critical, 1=Warning, 2=Info
# model-api: Model.severity_for_signature_mismatch(impl_status: Nat) -> Nat
# same impl_status codes; always Critical (0) regardless of impl_status (unbounded invariant)

# source: spec-quality-guardrails-impl-spec-check §3.1.1 sha256:c3219ce2ea61
law missing_impl_implemented_is_critical:
  {Model.severity_for_missing_impl(0n) == 0n : Nat}

# source: spec-quality-guardrails-impl-spec-check §3.1.1 sha256:c3219ce2ea61
law missing_impl_not_implemented_is_info:
  {Model.severity_for_missing_impl(1n) == 2n : Nat}

# source: spec-quality-guardrails-impl-spec-check §3.1.1 sha256:c3219ce2ea61
law missing_impl_in_progress_is_info:
  {Model.severity_for_missing_impl(2n) == 2n : Nat}

# source: spec-quality-guardrails-impl-spec-check §3.1.1 sha256:c3219ce2ea61
law missing_impl_unset_is_warning:
  {Model.severity_for_missing_impl(3n) == 1n : Nat}

# source: spec-quality-guardrails-impl-spec-check §3.1.1 sha256:c3219ce2ea61
law signature_mismatch_always_critical_implemented:
  {Model.severity_for_signature_mismatch(0n) == 0n : Nat}

# source: spec-quality-guardrails-impl-spec-check §3.1.1 sha256:c3219ce2ea61
law signature_mismatch_always_critical_not_implemented:
  {Model.severity_for_signature_mismatch(1n) == 0n : Nat}

# source: spec-quality-guardrails-impl-spec-check §3.1.1 sha256:c3219ce2ea61
law signature_mismatch_always_critical_in_progress:
  {Model.severity_for_signature_mismatch(2n) == 0n : Nat}

# source: spec-quality-guardrails-impl-spec-check §3.1.1 sha256:c3219ce2ea61
law signature_mismatch_always_critical_unset:
  {Model.severity_for_signature_mismatch(3n) == 0n : Nat}
