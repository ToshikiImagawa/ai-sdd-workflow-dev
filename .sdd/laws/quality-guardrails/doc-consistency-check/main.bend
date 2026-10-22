# spec: spec-quality-guardrails-doc-consistency-check
# model-of: plugins/sdd-workflow/scripts/doc_walker.py
#
# 承認済み LAWS.bend (sha256:4257aaed2381) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

# 上流の優先順位（spec 3.1.1）。値が小さいほど優先（衝突時に正とする層）
# layer: 0=PRD, 1=spec, 2=design
def precedence(layer: Nat) -> Nat:
  layer

# FR-007 の検査対象か（spec 3.1.2）
# sdd_version_state: 0=欠落, 1=現行プラグインの major より古い, 2=現行 major 以上
def is_fr007_target(sdd_version_state: Nat) -> Bool:
  match sdd_version_state:
    case 1n:
      True{}
    case _:
      False{}

def main() -> Bool:
  is_fr007_target(1n)
