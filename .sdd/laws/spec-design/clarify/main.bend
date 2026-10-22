# spec: spec-spec-design-clarify
# model-of: plugins/sdd-workflow/skills/clarify/SKILL.md
#
# 承認済み LAWS.bend (sha256:6bf012365158 系) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

def add(+a: Nat, +b: Nat) -> Nat:
  match a:
    case 0n:
      b
    case 1n+p:
      1n+add(p, b)

def mul(+a: Nat, +b: Nat) -> Nat:
  match a:
    case 0n:
      0n
    case 1n+p:
      add(b, mul(p, b))

def le(+a: Nat, +b: Nat) -> Bool:
  match a b:
    case 0n _:
      True{}
    case 1n+_ 0n:
      False{}
    case 1n+ap 1n+bp:
      le(ap, bp)

# 明確度判定（clarify_spec 3.1.1）: 明確度 = clear/total >= 80% を 5*clear >= 4*total で判定する
def judge(+clear: Nat, +total: Nat) -> Bool:
  le(mul(4n, total), mul(5n, clear))

def main() -> Bool:
  judge(4n, 5n)
