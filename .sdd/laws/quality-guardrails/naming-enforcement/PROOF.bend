# spec: spec-quality-guardrails-naming-enforcement
#
# main.bend の参照モデルに対する LAWS.bend の証明。

import Base
import ./main.bend as Model
import ./LAWS.bend as Laws

def Laws.non_md_is_allowed():
  {==}

def Laws.ignore_pattern_match_is_allowed():
  {==}

def Laws.requirement_with_suffix_is_denied():
  {==}

def Laws.requirement_without_suffix_is_allowed():
  {==}

def Laws.non_requirement_dir_is_allowed():
  {==}
