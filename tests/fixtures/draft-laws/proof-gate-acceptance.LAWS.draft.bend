# spec: spec-task-implementation-proof-gate
#
# spec から起こした法則案。未承認: レビュー後に人が承認行
# (# approved: YYYY-MM-DD <承認者> sha256:<hash>) を追記する。

import Base
import ./main.bend as Model

# model-api: Model.rank_pass() -> Nat
# model-api: Model.rank_skipped() -> Nat
# model-api: Model.rank_fail() -> Nat
# model-api: Model.worse(a: Nat, b: Nat) -> Nat
# model-api: Model.aggregate(xs: List<&2, Nat>) -> Nat
# model-api: Model.judge(approved: Bool, exit_ok: Bool, marker: Bool) -> Nat

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law approved_exit_fail_is_fail:
  for m: Bool
  {Model.judge(True{}, False{}, m) == Model.rank_fail() : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law approved_no_marker_is_fail:
  for e: Bool
  {Model.judge(True{}, e, False{}) == Model.rank_fail() : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law approved_ok_marker_pass:
  {Model.judge(True{}, True{}, True{}) == Model.rank_pass() : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law unapproved_never_pass:
  for e: Bool
  for m: Bool
  {Model.judge(False{}, e, m) == Model.rank_skipped() : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_empty_skipped:
  {Model.aggregate([]) == Model.rank_skipped() : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law aggregate_singleton:
  for a: Nat
  {Model.aggregate([a]) == a : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law worse_associative:
  for a: Nat
  for b: Nat
  for c: Nat
  {Model.worse(Model.worse(a, b), c) == Model.worse(a, Model.worse(b, c)) : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law worse_commutative:
  for a: Nat
  for b: Nat
  {Model.worse(a, b) == Model.worse(b, a) : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law worse_pass_identity:
  for a: Nat
  {Model.worse(Model.rank_pass(), a) == a : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:f90b56b320d1
law fail_worse_than_skipped:
  {Model.worse(Model.rank_skipped(), Model.rank_fail()) == Model.rank_fail() : Nat}
