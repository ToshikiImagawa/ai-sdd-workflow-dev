# spec: spec-task-implementation-proof-gate
# model-of: plugins/sdd-workflow/skills/run-checklist/scripts/run-verification.py
#
# Reference model of the proof gate decision logic (run-verification.py proof):
# status ranks, worst-wins aggregation (proof-gate_spec 3.1.1) and the
# approved / ALL PROOFS CHECK judgement. Small pure rewrite, not the implementation.

import Base

# Status ranks, worst = largest (proof-gate_spec 3.1.1: FAIL > TIMEOUT >
# TOOL_NOT_FOUND > SKIPPED > PASS)
def rank_pass() -> Nat:
  0n

def rank_skipped() -> Nat:
  1n

def rank_fail() -> Nat:
  4n

# the worse of two statuses
def worse(+a: Nat, +b: Nat) -> Nat:
  match a b:
    case 0n _:
      b
    case 1n+ap 0n:
      1n+ap
    case 1n+ap 1n+bp:
      1n+worse(ap, bp)

def fold_worst(xs: List<&2, Nat>, acc: Nat) -> Nat:
  match xs:
    case Nil{}:
      acc
    case h <> t:
      fold_worst(t, worse(acc, h))

# aggregate over laws directories; no result at all is SKIPPED
def aggregate(xs: List<&2, Nat>) -> Nat:
  match xs:
    case Nil{}:
      1n
    case h <> t:
      fold_worst(t, h)

# one directory's verdict once the pre-checks passed: unapproved is SKIPPED;
# approved is PASS only with exit 0 and the ALL PROOFS CHECK marker
def judge(approved: Bool, exit_ok: Bool, marker: Bool) -> Nat:
  match approved:
    case False{}:
      1n
    case True{}:
      match exit_ok marker:
        case True{} True{}:
          0n
        case _ _:
          4n

def main() -> Nat:
  aggregate([0n, 1n, 4n])
