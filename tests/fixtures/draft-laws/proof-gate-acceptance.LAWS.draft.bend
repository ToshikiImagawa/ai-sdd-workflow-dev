# spec: spec-task-implementation-proof-gate
#
# Laws drafted from the spec. NOT approved: a human adds the approval line
# (# approved: YYYY-MM-DD <approver> sha256:<hash>) after review.

import Base
import ./main.bend as Model

# model-api: Model.worse(a: Nat, b: Nat) -> Nat  # the worse of two ranks; larger is worse; ranks: PASS=0 SKIPPED=1 TOOL_NOT_FOUND=2 TIMEOUT=3 FAIL=4
# model-api: Model.aggregate(xs: List<Nat>) -> Nat  # worst rank of a list of per-directory ranks
# model-api: Model.judge(approved: Bool, exit_ok: Bool, marker: Bool) -> Nat  # verdict of one directory after the pre-checks (table rows #5, #10, #12); approved = valid approval line, exit_ok = exit code 0, marker = stdout has ALL PROOFS CHECK; ranks: PASS=0 SKIPPED=1 FAIL=4

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law approved_exit_failure_fails:
  for m: Bool
  {Model.judge(True{}, False{}, m) == 4n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law approved_missing_marker_fails:
  {Model.judge(True{}, True{}, False{}) == 4n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law approved_ok_marker_pass:
  {Model.judge(True{}, True{}, True{}) == 0n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law unapproved_never_pass:
  for e: Bool
  for m: Bool
  {Model.judge(False{}, e, m) == 1n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law aggregate_singleton:
  for x: Nat
  {Model.aggregate([x]) == x : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law worse_associative:
  for a: Nat
  for b: Nat
  for c: Nat
  {Model.worse(Model.worse(a, b), c) == Model.worse(a, Model.worse(b, c)) : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law worse_commutative:
  for a: Nat
  for b: Nat
  {Model.worse(a, b) == Model.worse(b, a) : Nat}
