# spec: spec-quality-guardrails-vibe-detection
# model-of: plugins/sdd-workflow/skills/vibe-detector/SKILL.md
#
# 承認済み LAWS.bend (sha256:3cc634161f3a 系) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

# リスクレベル判定（vibe-detection_spec 3.1.1）
# signal = 検出された曖昧観点の数。戻り値: 0n = High, 1n = Medium, 2n = Low
# どの入力もちょうど 1 つのレベルに定まる（全域関数）
def risk_level(+signal: Nat) -> Nat:
  match signal:
    case 0n:
      2n
    case 1n+p:
      match p:
        case 0n:
          1n
        case 1n+_:
          0n

# level が {0n, 1n, 2n} のいずれかか
def is_valid_risk_level(+level: Nat) -> Bool:
  match level:
    case 0n:
      True{}
    case 1n+p:
      match p:
        case 0n:
          True{}
        case 1n+q:
          match q:
            case 0n:
              True{}
            case 1n+_:
              False{}

def main() -> Nat:
  risk_level(3n)
