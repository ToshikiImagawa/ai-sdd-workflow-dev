# spec: spec-quality-guardrails-naming-enforcement
# model-of: plugins/sdd-workflow/scripts/naming.py
#
# 承認済み LAWS.bend (sha256:34a684e9aeb7) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

# 命名検証の決定表（spec 3.1.1）。上の行ほど優先する
# 0=許可(.md 以外), 1=許可(ignore_patterns 一致), 2=拒否(requirement/ に _spec/_design), 3=許可(それ以外)
def decide(is_md: Bool, ignore_match: Bool, is_requirement_dir: Bool, has_suffix: Bool) -> Nat:
  match is_md:
    case False{}:
      0n
    case True{}:
      match ignore_match:
        case True{}:
          1n
        case False{}:
          match is_requirement_dir has_suffix:
            case True{} True{}:
              2n
            case _ _:
              3n

def main() -> Nat:
  decide(True{}, False{}, True{}, True{})
