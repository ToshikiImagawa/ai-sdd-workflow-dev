# spec: spec-workflow-foundation-session-config
# model-of: plugins/sdd-workflow/scripts/session-start.py
# model-of: plugins/sdd-workflow/scripts/hook_common.py
#
# LAWS.bend（点命題を差分テストへ移した後の全称法則 config_wins）を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

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

def main() -> Nat:
  resolve_value(False{}, True{})
