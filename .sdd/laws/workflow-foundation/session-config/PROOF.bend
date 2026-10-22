# spec: spec-workflow-foundation-session-config
#
# main.bend の参照モデルに対する LAWS.bend の証明。

import Base
import ./main.bend as Model
import ./LAWS.bend as Laws

def Laws.index_absent_defaults_true():
  {==}

def Laws.index_true_preserved():
  {==}

def Laws.index_false_preserved():
  {==}

def Laws.index_invalid_defaults_true():
  {==}

def Laws.config_wins(e):
  {==}

def Laws.env_wins_without_config():
  {==}

def Laws.default_without_either():
  {==}
