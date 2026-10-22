# spec: spec-workflow-foundation-session-config
# model-of: plugins/sdd-workflow/scripts/session-start.py
#
# 承認済み LAWS.bend (sha256:436722e95c81 系) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

# index 設定値の正規化（session-config_spec 3.1.1）
# value_kind: 0n = キー欠落, 1n = true, 2n = false, 3n 以上 = 真偽値以外の不正値
# 明示的な false 以外はすべて true に倒す
def normalize_index(+value_kind: Nat) -> Bool:
  match value_kind:
    case 0n:
      True{}
    case 1n+p:
      match p:
        case 0n:
          True{}
        case 1n+q:
          match q:
            case 0n:
              False{}
            case 1n+_:
              True{}

# 設定値の解決優先順位（session-config_spec 3.1.2）
# 0n = config採用, 1n = 環境変数採用, 2n = 既定値採用
def resolve_value(has_config: Bool, has_env: Bool) -> Nat:
  match has_config:
    case True{}:
      0n
    case False{}:
      match has_env:
        case True{}:
          1n
        case False{}:
          2n

def main() -> Bool:
  normalize_index(2n)
