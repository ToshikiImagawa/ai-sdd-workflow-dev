# spec: spec-quality-guardrails-constitution-injection
# model-of: plugins/sdd-workflow/scripts/pre-tool-use.py
#
# 承認済み LAWS.bend (sha256:6d89c8845e8a) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

# CONSTITUTION 注入の判定（spec 3.1.1）。
# CONSTITUTION が存在し、ソースコード編集で、未注入のときだけ注入する
def should_inject(constitution_exists: Bool, is_source_code: Bool, already_injected: Bool) -> Bool:
  match constitution_exists is_source_code already_injected:
    case True{} True{} False{}:
      True{}
    case _ _ _:
      False{}

def main() -> Bool:
  should_inject(True{}, True{}, False{})
