# spec: spec-quality-guardrails-front-matter-validation
#
# main.bend の参照モデルに対する LAWS.bend の証明。

import Base
import ./main.bend as Model
import ./LAWS.bend as Laws

def Laws.depends_on_reversed_is_error():
  {==}

def Laws.crossref_id_duplicate_is_error():
  {==}

def Laws.crossref_depends_on_missing_is_error():
  {==}

def Laws.crossref_laws_dir_missing_is_error():
  {==}

def Laws.crossref_laws_spec_id_mismatch_is_error():
  {==}

def Laws.crossref_orphan_laws_is_error():
  {==}

def Laws.id_format_mismatch_is_warning():
  {==}

def Laws.date_format_invalid_is_warning():
  {==}

def Laws.enum_value_out_of_range_is_warning():
  {==}

def Laws.front_matter_missing_is_info():
  {==}
