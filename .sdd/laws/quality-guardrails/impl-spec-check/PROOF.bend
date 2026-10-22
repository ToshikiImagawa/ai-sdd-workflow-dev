# spec: spec-quality-guardrails-impl-spec-check
#
# main.bend の参照モデルに対する LAWS.bend の証明。

import Base
import ./main.bend as Model
import ./LAWS.bend as Laws

def Laws.missing_impl_implemented_is_critical():
  {==}

def Laws.missing_impl_not_implemented_is_info():
  {==}

def Laws.missing_impl_in_progress_is_info():
  {==}

def Laws.missing_impl_unset_is_warning():
  {==}

def Laws.signature_mismatch_always_critical_implemented():
  {==}

def Laws.signature_mismatch_always_critical_not_implemented():
  {==}

def Laws.signature_mismatch_always_critical_in_progress():
  {==}

def Laws.signature_mismatch_always_critical_unset():
  {==}
