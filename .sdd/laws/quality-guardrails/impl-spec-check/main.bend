# spec: spec-quality-guardrails-impl-spec-check
# model-of: plugins/sdd-workflow/skills/check-spec/scripts/find-spec-docs.py
#
# 承認済み LAWS.bend (sha256:321fe1a9bbd8) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

# impl-status -> 重大度（spec 3.1.1）
# impl_status: 0=implemented, 1=not-implemented, 2=in-progress, 3=未設定
# 重大度: 0=Critical, 1=Warning, 2=Info
def severity_for_missing_impl(impl_status: Nat) -> Nat:
  match impl_status:
    case 0n:
      0n
    case 1n:
      2n
    case 2n:
      2n
    case _:
      1n

# シグネチャ不一致は impl-status に依らず常に Critical
def severity_for_signature_mismatch(impl_status: Nat) -> Nat:
  0n

def main() -> Nat:
  severity_for_missing_impl(0n)
