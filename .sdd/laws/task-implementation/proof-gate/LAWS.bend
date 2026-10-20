# spec: spec-task-implementation-proof-gate
#
# Laws derived from proof-gate_spec 3.1.1 (decision table and aggregation).
# The approval line is added by a human reviewer, never by AI.
# approved: 2026-10-19 @ToshikiImagawa sha256:33cefef841bf

import Base
import ./main.bend as Model

law agg_empty_skipped:
  {Model.aggregate(Nil{}) == 1n : Nat}

law agg_single_identity:
  for x: Nat
  {Model.aggregate([x]) == x : Nat}

law agg_pair_commutes:
  for a: Nat
  for b: Nat
  {Model.aggregate([a, b]) == Model.aggregate([b, a]) : Nat}

law unapproved_never_pass:
  for e: Bool
  for m: Bool
  {Model.judge(False{}, e, m) == 1n : Nat}

law pass_requires_marker:
  for e: Bool
  {Model.judge(True{}, e, False{}) == 4n : Nat}
