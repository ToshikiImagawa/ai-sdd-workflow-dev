# spec: spec-task-implementation-proof-gate
#
# Laws drafted from the spec. NOT approved: a human adds the approval line
# (# approved: YYYY-MM-DD <approver> sha256:<hash>) after review.

import Base
import ./main.bend as Model

# model-api: Model.judge(approved: Bool, exit_ok: Bool, marker: Bool) -> Nat  # ranks: PASS=0 SKIPPED=1 FAIL=4
# model-api: Model.aggregate(xs: List<Nat>) -> Nat  # worst wins; empty list = SKIPPED(1)

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law pass_requires_marker:
  for e: Bool
  {Model.judge(True{}, e, False{}) == 4n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law unapproved_never_pass:
  for e: Bool
  for m: Bool
  {Model.judge(False{}, e, m) == 1n : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law agg_pair_commutes:
  for a: Nat
  for b: Nat
  {Model.aggregate([a, b]) == Model.aggregate([b, a]) : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law agg_single_identity:
  for x: Nat
  {Model.aggregate([x]) == x : Nat}

# source: spec-task-implementation-proof-gate §3.1.1 sha256:fa3ebed3050e
law agg_empty_skipped:
  {Model.aggregate(Nil{}) == 1n : Nat}
