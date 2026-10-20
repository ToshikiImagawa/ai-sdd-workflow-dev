# spec: spec-task-implementation-proof-gate
#
# Laws drafted from the spec. NOT approved: a human adds the approval line
# (# approved: YYYY-MM-DD <approver> sha256:<hash>) after review.

import Base
import ./main.bend as Model

# model-api: Model.rank_pass() -> Nat  # ranks: PASS=0
# model-api: Model.rank_skipped() -> Nat  # ranks: SKIPPED=1
# model-api: Model.rank_fail() -> Nat  # ranks: FAIL=4
# model-api: Model.aggregate(xs: List<&2, Nat>) -> Nat
# model-api: Model.judge(approved: Bool, exit_ok: Bool, marker: Bool) -> Nat

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law judge_all_ok_pass:
  {Model.judge(True{}, True{}, True{}) == Model.rank_pass() : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law judge_exit_failure_fails:
  for m: Bool
  {Model.judge(True{}, False{}, m) == Model.rank_fail() : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law judge_missing_marker_fails:
  for e: Bool
  {Model.judge(True{}, e, False{}) == Model.rank_fail() : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law judge_unapproved_skipped:
  for e: Bool
  for m: Bool
  {Model.judge(False{}, e, m) == Model.rank_skipped() : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_associative:
  for a: Nat
  for b: Nat
  for c: Nat
  {Model.aggregate([Model.aggregate([a, b]), c]) == Model.aggregate([a, Model.aggregate([b, c])]) : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_commutative:
  for a: Nat
  for b: Nat
  {Model.aggregate([a, b]) == Model.aggregate([b, a]) : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_empty_skipped:
  {Model.aggregate([]) == Model.rank_skipped() : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_pass_identity:
  for a: Nat
  {Model.aggregate([Model.rank_pass(), a]) == Model.aggregate([a]) : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_singleton_fixed:
  for a: Nat
  {Model.aggregate([a]) == a : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_fail_over_pass:
  {Model.aggregate([Model.rank_pass(), Model.rank_fail()]) == Model.rank_fail() : Nat}
