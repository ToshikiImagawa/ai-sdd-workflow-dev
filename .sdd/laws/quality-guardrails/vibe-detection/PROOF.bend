# spec: spec-quality-guardrails-vibe-detection
#
# main.bend の参照モデルに対する LAWS.bend の証明。

import Base
import ./main.bend as Model
import ./LAWS.bend as Laws

def Laws.risk_level_is_always_one_of_high_medium_low(signal):
  match signal:
    case 0n:
      {==}
    case 1n+p:
      match p:
        case 0n:
          {==}
        case 1n+q:
          {==}
