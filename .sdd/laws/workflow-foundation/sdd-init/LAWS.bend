# spec: spec-workflow-foundation-sdd-init
#
# spec から起こした法則案。未承認: レビュー後に人が承認行
# (# approved: YYYY-MM-DD <承認者> sha256:<hash>) を追記する。
# approved: 2026-10-21 @ToshikiImagawa sha256:3f37a062f6eb

import Base
import ./main.bend as Model

# model-api: Model.claude_md_action(has_section: Bool, version_match: Bool) -> Nat
# unfixed - needs confirmation
# 戻り値のエンコード: 0n = append（追記）, 1n = skip（変更なし）, 2n = replace（置換）

# source: spec-workflow-foundation-sdd-init §3.1.1 sha256:e106785a632c
law no_section_appends:
  for v: Bool
  {Model.claude_md_action(False{}, v) == 0n : Nat}

# source: spec-workflow-foundation-sdd-init §3.1.1 sha256:e106785a632c
law same_version_skips:
  {Model.claude_md_action(True{}, True{}) == 1n : Nat}

# source: spec-workflow-foundation-sdd-init §3.1.1 sha256:e106785a632c
law version_mismatch_replaces:
  {Model.claude_md_action(True{}, False{}) == 2n : Nat}
