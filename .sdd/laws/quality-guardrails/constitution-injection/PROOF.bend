# spec: spec-quality-guardrails-constitution-injection
#
# main.bend の参照モデルに対する LAWS.bend の証明。

import Base
import ./main.bend as Model
import ./LAWS.bend as Laws

def Laws.no_constitution_means_no_injection():
  {==}

def Laws.non_source_edit_means_no_injection():
  {==}

def Laws.already_injected_means_no_injection():
  {==}

def Laws.first_source_edit_with_constitution_injects():
  {==}
