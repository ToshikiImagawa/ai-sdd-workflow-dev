# spec: spec-task-implementation-proof-gate
#
# Proofs of LAWS.bend over the reference model in main.bend.

import Base
import ./main.bend as Model
import ./LAWS.bend as Laws

def Laws.agg_empty_skipped():
  {==}

def Laws.agg_single_identity(x):
  {==}

def worse_comm(+a: Nat, +b: Nat) -> {Model.worse(a, b) == Model.worse(b, a) : Nat}:
  match a b:
    case 0n 0n:
      {==}
    case 0n 1n+bp:
      {==}
    case 1n+ap 0n:
      {==}
    case 1n+ap 1n+bp:
      %worse_comm(ap, bp) : {1n+Model.worse(ap, bp) == 1n+_ : Nat}
      {==}

def Laws.agg_pair_commutes(a, b):
  worse_comm(a, b)

def Laws.unapproved_never_pass(e, m):
  {==}

def Laws.pass_requires_marker(e):
  match e:
    case True{}:
      {==}
    case False{}:
      {==}
