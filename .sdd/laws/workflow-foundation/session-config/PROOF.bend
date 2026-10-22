# spec: spec-workflow-foundation-session-config
#
# main.bend の参照モデルに対する LAWS.bend の証明。

import Base
import ./main.bend as Model
import ./LAWS.bend as Laws

def Laws.config_wins(e):
  {==}
