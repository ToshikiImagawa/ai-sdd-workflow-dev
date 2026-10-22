# spec: spec-workflow-foundation-session-config
#
# spec から起こした法則案。未承認: レビュー後に人が承認行
# (# approved: YYYY-MM-DD <承認者> sha256:<hash>) を追記する。
# approved: 2026-10-21 @ToshikiImagawa sha256:436722e95c81

import Base
import ./main.bend as Model

# model-api: Model.normalize_index(value_kind: Nat) -> Bool
# unfixed - needs confirmation
# value_kind のエンコード: 0n = キー欠落, 1n = true, 2n = false, 3n = 真偽値以外の不正値
# model-api: Model.resolve_value(has_config: Bool, has_env: Bool) -> Nat
# unfixed - needs confirmation
# 戻り値のエンコード: 0n = config採用, 1n = 環境変数採用, 2n = 既定値採用

# source: spec-workflow-foundation-session-config §3.1.1 sha256:9863d3b55139
law index_absent_defaults_true:
  {Model.normalize_index(0n) == True{} : Bool}

# source: spec-workflow-foundation-session-config §3.1.1 sha256:9863d3b55139
law index_true_preserved:
  {Model.normalize_index(1n) == True{} : Bool}

# source: spec-workflow-foundation-session-config §3.1.1 sha256:9863d3b55139
law index_false_preserved:
  {Model.normalize_index(2n) == False{} : Bool}

# source: spec-workflow-foundation-session-config §3.1.1 sha256:9863d3b55139
law index_invalid_defaults_true:
  {Model.normalize_index(3n) == True{} : Bool}

# source: spec-workflow-foundation-session-config §3.1.2 sha256:d9e59c0cafd9
law config_wins:
  for e: Bool
  {Model.resolve_value(True{}, e) == 0n : Nat}

# source: spec-workflow-foundation-session-config §3.1.2 sha256:d9e59c0cafd9
law env_wins_without_config:
  {Model.resolve_value(False{}, True{}) == 1n : Nat}

# source: spec-workflow-foundation-session-config §3.1.2 sha256:d9e59c0cafd9
law default_without_either:
  {Model.resolve_value(False{}, False{}) == 2n : Nat}
