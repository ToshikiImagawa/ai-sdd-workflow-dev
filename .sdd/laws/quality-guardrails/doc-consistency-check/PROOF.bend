# spec: spec-quality-guardrails-doc-consistency-check
#
# main.bend の参照モデルに対する LAWS.bend の証明。

import Base
import ./main.bend as Model
import ./LAWS.bend as Laws

def Laws.prd_outranks_spec():
  {==}

def Laws.spec_outranks_design():
  {==}

def Laws.prd_outranks_design():
  {==}

def Laws.sdd_version_absent_is_not_fr007_target():
  {==}

def Laws.sdd_version_older_major_is_fr007_target():
  {==}

def Laws.sdd_version_current_major_is_not_fr007_target():
  {==}
