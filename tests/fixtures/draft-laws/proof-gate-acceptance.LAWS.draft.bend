# spec: spec-task-implementation-proof-gate
#
# Laws drafted from the spec. NOT approved: a human adds the approval line
# (# approved: YYYY-MM-DD <approver> sha256:<hash>) after review.

import Base
import ./main.bend as Model

# model-api: Model.judge(approved: Bool, exit_ok: Bool, marker: Bool) -> Nat  # rows 5/10/12 of the table, assuming rows 1-4 did not match; ranks: PASS=0 SKIPPED=1 TOOL_NOT_FOUND=2 TIMEOUT=3 FAIL=4
# model-api: Model.worse(a: Nat, b: Nat) -> Nat  # aggregation of two ranks (FAIL > TIMEOUT > TOOL_NOT_FOUND > SKIPPED > PASS); same rank encoding as judge
# model-api: Model.aggregate_empty() -> Nat  # aggregate over zero directories, same rank encoding

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law approved_exit_failure_fails:
  for m: Bool
  {Model.judge(True{}, False{}, m) == 4n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law approved_marker_ok_passes:
  {Model.judge(True{}, True{}, True{}) == 0n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law approved_without_marker_fails:
  for e: Bool
  {Model.judge(True{}, e, False{}) == 4n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law unapproved_never_pass:
  for e: Bool
  for m: Bool
  {Model.judge(False{}, e, m) == 1n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_associative:
  for a: Nat
  for b: Nat
  for c: Nat
  {Model.worse(Model.worse(a, b), c) == Model.worse(a, Model.worse(b, c)) : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_commutative:
  for a: Nat
  for b: Nat
  {Model.worse(a, b) == Model.worse(b, a) : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_empty_is_skipped:
  {Model.aggregate_empty() == 1n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_fail_absorbs:
  for a: Nat
  {Model.worse(4n, a) == 4n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_idempotent:
  for a: Nat
  {Model.worse(a, a) == a : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_pass_identity:
  for a: Nat
  {Model.worse(0n, a) == a : Nat}
