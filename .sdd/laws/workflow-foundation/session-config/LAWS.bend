# spec: spec-workflow-foundation-session-config
#
# spec から起こした法則案。未承認: レビュー後に人が承認行
# (# approved: YYYY-MM-DD <承認者> sha256:<hash>) を追記する。
# approved: 2026-10-21 @ToshikiImagawa sha256:436722e95c81

import Base
import ./main.bend as Model

# model-api: Model.resolve_value(has_config: Bool, has_env: Bool) -> Nat
# unfixed - needs confirmation
# 戻り値のエンコード: 0n = config採用, 1n = 環境変数採用, 2n = 既定値採用

# 点命題 index_* 4 件と env_wins_without_config / default_without_either は差分テスト
# tests/laws/test_workflow_foundation_session_config.py へ移した（laws-drafting_spec FR-014、#220）。

# source: spec-workflow-foundation-session-config §3.1.2 sha256:d9e59c0cafd9
law config_wins:
  for e: Bool
  {Model.resolve_value(True{}, e) == 0n : Nat}
