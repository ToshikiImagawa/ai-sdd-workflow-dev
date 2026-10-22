# spec: spec-prd-generation
# model-of: plugins/sdd-workflow/skills/generate-prd/SKILL.md
#
# 承認済み LAWS.bend (sha256:270c60c406c1 系) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

# 大きい方
def max_nat(+a: Nat, +b: Nat) -> Nat:
  match a b:
    case 0n _:
      b
    case 1n+ap 0n:
      1n+ap
    case 1n+ap 1n+bp:
      1n+max_nat(ap, bp)

def fold_max(xs: List<&2, Nat>, acc: Nat) -> Nat:
  match xs:
    case Nil{}:
      acc
    case h <> t:
      fold_max(t, max_nat(acc, h))

# 新規要求 ID の採番（prd-generation_spec 3.3.2）
# 既存 ID 群が空なら 1、そうでなければ最大値の次
def next_id(ids: List<&2, Nat>) -> Nat:
  match ids:
    case Nil{}:
      1n
    case h <> t:
      1n+fold_max(t, h)

def main() -> Nat:
  next_id([1n, 3n, 2n])
