# spec: spec-spec-design-clarify
#
# spec から起こした法則案。未承認: レビュー後に人が承認行
# (# approved: YYYY-MM-DD <承認者> sha256:<hash>) を追記する。
# approved: 2026-10-21 @ToshikiImagawa sha256:6bf012365158

import Base
import ./main.bend as Model

# model-api: Model.judge(clear: Nat, total: Nat) -> Bool  # unfixed - needs confirmation
# model-api: Model.mul(a: Nat, b: Nat) -> Nat  # unfixed - needs confirmation

# source: spec-spec-design-clarify §3.1.1 sha256:2d372236400d
law judge_exact_threshold_passes:
  for r: Nat
  {Model.judge(Model.mul(4n, r), Model.mul(5n, r)) == True{} : Bool}

# source: spec-spec-design-clarify §3.1.1 sha256:2d372236400d
law judge_full_match_passes:
  for t: Nat
  {Model.judge(t, t) == True{} : Bool}
