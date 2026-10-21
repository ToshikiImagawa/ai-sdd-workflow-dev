# spec: spec-prd-generation
#
# spec から起こした法則案。未承認: レビュー後に人が承認行
# (# approved: YYYY-MM-DD <承認者> sha256:<hash>) を追記する。

import Base
import ./main.bend as Model

# model-api: Model.next_id(ids: List<&2, Nat>) -> Nat

# source: spec-prd-generation §3.3.2 sha256:aae9d33947cc
law next_id_empty:
  {Model.next_id(Nil{}) == 1n : Nat}

# source: spec-prd-generation §3.3.2 sha256:aae9d33947cc
law next_id_singleton:
  for a: Nat
  {Model.next_id([a]) == 1n+a : Nat}
