# 法則 移行表: 全 12 法則ディレクトリ（#218）

- 生成日: 2026-10-22（`/draft-laws migrate` を 12 ディレクトリに実行。読み取り専用: 法則ディレクトリ・spec・承認行は変更していない）
- 根拠: [laws-drafting_spec.md](../../specification/task-implementation/laws-drafting_spec.md) FR-014〜FR-016、[proof-gate.md](../../adr/task-implementation/proof-gate.md) 2026-10-22 エントリ
- 分類の規則: `prose_delete` = 実装が散文（`.md`）のみ／`to_tests` = `for` を持たない点命題（空入力は `kind_guess: empty` で `keep`）／`keep` = それ以外
- 差分テストの出力先: `tests/laws/test_<feature>.py`（`.sdd-config.json` `laws.tests_dir` 既定）。Python 実装の 6 ディレクトリ分は本チケットで作成済み（70 ケース、全件 PASS、`check --tests` error 0）

## 全体サマリ

| feature | 実装の所在（現 `# model-of:`） | 法則化可 | keep | to_tests | prose_delete | 対応テストファイル |
|:--|:--|:--|--:|--:|--:|:--|
| prd-generation | `skills/generate-prd/SKILL.md` | × prose | 0 | 0 | 2 | — |
| quality-guardrails/constitution-injection | `scripts/pre-tool-use.py` | ○ | 0 | 4 | 0 | `test_quality_guardrails_constitution_injection.py` |
| quality-guardrails/doc-consistency-check | `scripts/doc_walker.py`（**実体は SKILL.md**） | ○（要訂正 → ×） | 3 | 3 | 0 | — |
| quality-guardrails/front-matter-validation | `agents/front-matter-reviewer.md` | × prose | 0 | 0 | 10 | — |
| quality-guardrails/impl-spec-check | `skills/check-spec/scripts/find-spec-docs.py`（**実体は SKILL.md**） | ○（要訂正 → ×） | 0 | 8 | 0 | — |
| quality-guardrails/naming-enforcement | `scripts/naming.py` | ○ | 0 | 5 | 0 | `test_quality_guardrails_naming_enforcement.py` |
| quality-guardrails/stale-doc-detection | `scripts/post-tool-use.py` | ○ | 0 | 8 | 0 | `test_quality_guardrails_stale_doc_detection.py` |
| quality-guardrails/vibe-detection | `skills/vibe-detector/SKILL.md` | × prose | 0 | 0 | 1 | — |
| spec-design/clarify | `skills/clarify/SKILL.md` | × prose | 0 | 0 | 2 | — |
| task-implementation/proof-gate | `skills/run-checklist/scripts/run-verification.py` | ○ | 5 | 0 | 0 | `test_task_implementation_proof_gate.py`（全称法則の列挙検証。法則は残す） |
| workflow-foundation/sdd-init | `skills/sdd-init/scripts/update-claude-md.py` | ○ | 1 | 2 | 0 | `test_workflow_foundation_sdd_init.py` |
| workflow-foundation/session-config | `scripts/session-start.py` | ○ | 1 | 6 | 0 | `test_workflow_foundation_session_config.py` |

パスの接頭辞 `plugins/sdd-workflow/` は省略。`impl.source` は全ディレクトリで `main.bend`（spec に `impl-of:` 宣言が無い）。

### 実装の所在に関する訂正（人の確認が必要）

- **doc-consistency-check**: `# model-of: scripts/doc_walker.py` だが、順位比較（`prd_outranks_*`）と `sdd-version` 判定の実体は `skills/doc-consistency-checker/SKILL.md` の散文手順。`doc_walker.py` はドキュメント走査のみで判定を持たない。`impl-of:` を SKILL.md に訂正すると **prose_delete**（6 法則）になる
- **impl-spec-check**: `# model-of: skills/check-spec/scripts/find-spec-docs.py` だが、重大度判定（`missing_impl_*` / `signature_mismatch_*`）の実体は `skills/check-spec/SKILL.md`。`find-spec-docs.py` は spec 探索のみ。訂正すると **prose_delete**（8 法則）になる

訂正後の内訳: prose_delete 6 ディレクトリ（29 法則）、Python 実装 6 ディレクトリ（32 法則: keep 7 / to_tests 25）。

## ディレクトリ別の分類

### prd-generation（`laws-status: proven`、承認: valid）→ prose_delete

| 法則 | 出典 | 分類 | `for` | kind 推定 | 備考 |
|:--|:--|:--|:--|:--|:--|
| `next_id_empty` | §3.3.2 | prose_delete | no | empty | ID 採番は generate-prd SKILL.md の手順 |
| `next_id_singleton` | §3.3.2 | prose_delete | yes | — | 全称法則だが実装が散文 |

### quality-guardrails/constitution-injection（proven、valid）→ 全件 to_tests

| 法則 | 出典 | 分類 | `for` | 対応テスト |
|:--|:--|:--|:--|:--|
| `no_constitution_means_no_injection` | §3.1.1 | to_tests | no | `test_no_constitution_means_no_injection` ✅ |
| `non_source_edit_means_no_injection` | §3.1.1 | to_tests | no | `test_non_source_edit_means_no_injection` ✅ |
| `already_injected_means_no_injection` | §3.1.1 | to_tests | no | `test_already_injected_means_no_injection` ✅ |
| `first_source_edit_with_constitution_injects` | §3.1.1 | to_tests | no | `test_first_source_edit_with_constitution_injects` ✅ |

4 法則すべてがテストへ移るため、`LAWS.bend` は空になる → 法則ディレクトリごと削除し、spec の `laws:` / `laws-status` を外す（差分テストが検証先）。

### quality-guardrails/doc-consistency-check（`laws-status: drafted`、承認: missing）→ 訂正後 prose_delete

| 法則 | 出典 | 分類（現） | `for` | 備考 |
|:--|:--|:--|:--|:--|
| `prd_outranks_spec` | §3.1.1 | keep | no | `==` でない比較式のため点命題判定外 |
| `spec_outranks_design` | §3.1.1 | keep | no | 同上 |
| `prd_outranks_design` | §3.1.1 | keep | no | 同上 |
| `sdd_version_absent_is_not_fr007_target` | §3.1.2 | to_tests | no | |
| `sdd_version_older_major_is_fr007_target` | §3.1.2 | to_tests | no | |
| `sdd_version_current_major_is_not_fr007_target` | §3.1.2 | to_tests | no | |

未承認（`drafted`）のため承認の失効は生じない。`impl-of:` を SKILL.md に訂正 → 全件 prose_delete。

### quality-guardrails/front-matter-validation（proven、valid）→ prose_delete（10 法則）

`depends_on_reversed_is_error` / `crossref_id_duplicate_is_error` / `crossref_depends_on_missing_is_error` / `crossref_laws_dir_missing_is_error` / `crossref_laws_spec_id_mismatch_is_error` / `crossref_orphan_laws_is_error` / `id_format_mismatch_is_warning` / `date_format_invalid_is_warning` / `enum_value_out_of_range_is_warning` / `front_matter_missing_is_info`（すべて §3.1.1、`for` なし）。実装は `agents/front-matter-reviewer.md`。

### quality-guardrails/impl-spec-check（proven、valid）→ 訂正後 prose_delete（8 法則）

`missing_impl_{implemented_is_critical, not_implemented_is_info, in_progress_is_info, unset_is_warning}` / `signature_mismatch_always_critical_{implemented, not_implemented, in_progress, unset}`（すべて §3.1.1、`for` なし。現分類は to_tests）。実装は `skills/check-spec/SKILL.md`。

### quality-guardrails/naming-enforcement（proven、valid）→ 全件 to_tests

| 法則 | 分類 | 対応テスト |
|:--|:--|:--|
| `non_md_is_allowed` | to_tests | `test_non_md_is_allowed` ✅ |
| `ignore_pattern_match_is_allowed` | to_tests | `test_ignore_pattern_match_is_allowed` ✅ |
| `requirement_with_suffix_is_denied` | to_tests | `test_requirement_with_suffix_is_denied` ✅ |
| `requirement_without_suffix_is_allowed` | to_tests | `test_requirement_without_suffix_is_allowed` ✅ |
| `non_requirement_dir_is_allowed` | to_tests | `test_non_requirement_dir_is_allowed` ✅ |

全件移行 → 法則ディレクトリ削除、`laws:` / `laws-status` 除去。注: 実装は allow を空文字列で返すため、モデルの 3 種の allow 符号（0/1/3）はテストでは区別しない。

### quality-guardrails/stale-doc-detection（proven、valid）→ 全件 to_tests

`spec_edit_triggers_fr001` / `spec_with_laws_triggers_fr009` / `prd_edit_triggers_fr002` / `adr_edit_triggers_fr006` / `law_file_edit_triggers_fr007` / `source_with_spec_triggers_fr003` / `source_modeled_triggers_fr008` / `unrelated_edit_is_silent` → 同名 `test_*` ✅（8 件）。全件移行 → 法則ディレクトリ削除。注: モデルは多重該当を単一値に落としているが、テストは「該当カテゴリのメッセージが含まれる」で検証する（実装の多重注入を正とする）。

### quality-guardrails/vibe-detection（proven、valid）→ prose_delete

| 法則 | 出典 | `for` | 備考 |
|:--|:--|:--|:--|
| `risk_level_is_always_one_of_high_medium_low` | §3.1.1 | yes | 全称法則だが実装は `skills/vibe-detector/SKILL.md`。性質自体の検証先はスキル評価（skill-evals） |

### spec-design/clarify（proven、valid）→ prose_delete

| 法則 | 出典 | `for` | 備考 |
|:--|:--|:--|:--|
| `judge_exact_threshold_passes` | §3.1.1 | yes | 80% 閾値（5·clear ≥ 4·total）の等号成立。実装は `skills/clarify/SKILL.md` |
| `judge_full_match_passes` | §3.1.1 | yes | 同上。PROOF.bend 101 行の補題群も削除対象 |

### task-implementation/proof-gate（proven、valid）→ 全件 keep（検収基準 §11 を維持）

| 法則 | 分類 | `for` | kind 推定 |
|:--|:--|:--|:--|
| `agg_empty_skipped` | keep | no | empty |
| `agg_single_identity` | keep | yes | — |
| `agg_pair_commutes` | keep | yes | — |
| `unapproved_never_pass` | keep | yes | — |
| `pass_requires_marker` | keep | yes | — |

変更なし。`test_task_implementation_proof_gate.py` は補助（有限値域の列挙で実装も検証）。

### workflow-foundation/sdd-init（proven、valid）

| 法則 | 分類 | `for` | 対応テスト |
|:--|:--|:--|:--|
| `no_section_appends` | keep | yes | （補助: `test_no_section_appends` ✅） |
| `same_version_skips` | to_tests | no | `test_same_version_skips` ✅ |
| `version_mismatch_replaces` | to_tests | no | `test_version_mismatch_replaces` ✅ |

`LAWS.bend` に `no_section_appends` のみ残す → 本文が変わるため再承認、`PROOF.bend` から 2 法則の証明を削除。

### workflow-foundation/session-config（proven、valid）

| 法則 | 出典 | 分類 | `for` | 対応テスト |
|:--|:--|:--|:--|:--|
| `index_absent_defaults_true` | §3.1.1 | to_tests | no | `test_index_absent_defaults_true` ✅ |
| `index_true_preserved` | §3.1.1 | to_tests | no | `test_index_true_preserved` ✅ |
| `index_false_preserved` | §3.1.1 | to_tests | no | `test_index_false_preserved` ✅ |
| `index_invalid_defaults_true` | §3.1.1 | to_tests | no | `test_index_invalid_defaults_true` ✅ |
| `config_wins` | §3.1.2 | keep | yes | （補助: `test_config_wins` ✅） |
| `env_wins_without_config` | §3.1.2 | to_tests | no | `test_env_wins_without_config` ✅ |
| `default_without_either` | §3.1.2 | to_tests | no | `test_default_without_either` ✅ |

`LAWS.bend` に `config_wins` のみ残す → 再承認、`PROOF.bend` から 6 法則の証明を削除。`main.bend` の `normalize_index` は不要になる。

## 各 spec への `impl-of:` 追記案（人が適用）

spec 本文（§4 提供コンポーネント付近）に行頭で追記する。`#` は付けない。

| spec | 追記する行 |
|:--|:--|
| `prd-generation_spec.md` | `impl-of: plugins/sdd-workflow/skills/generate-prd/SKILL.md` |
| `quality-guardrails/constitution-injection_spec.md` | `impl-of: plugins/sdd-workflow/scripts/pre-tool-use.py` |
| `quality-guardrails/doc-consistency-check_spec.md` | `impl-of: plugins/sdd-workflow/skills/doc-consistency-checker/SKILL.md`（現 `# model-of:` の `doc_walker.py` から訂正） |
| `quality-guardrails/front-matter-validation_spec.md` | `impl-of: plugins/sdd-workflow/agents/front-matter-reviewer.md` |
| `quality-guardrails/impl-spec-check_spec.md` | `impl-of: plugins/sdd-workflow/skills/check-spec/SKILL.md`（現 `# model-of:` の `find-spec-docs.py` から訂正） |
| `quality-guardrails/naming-enforcement_spec.md` | `impl-of: plugins/sdd-workflow/scripts/naming.py` |
| `quality-guardrails/stale-doc-detection_spec.md` | `impl-of: plugins/sdd-workflow/scripts/post-tool-use.py` |
| `quality-guardrails/vibe-detection_spec.md` | `impl-of: plugins/sdd-workflow/skills/vibe-detector/SKILL.md` |
| `spec-design/clarify_spec.md` | `impl-of: plugins/sdd-workflow/skills/clarify/SKILL.md` |
| `task-implementation/proof-gate_spec.md` | `impl-of: plugins/sdd-workflow/skills/run-checklist/scripts/run-verification.py` |
| `workflow-foundation/sdd-init_spec.md` | `impl-of: plugins/sdd-workflow/skills/sdd-init/scripts/update-claude-md.py` |
| `workflow-foundation/session-config_spec.md` | `impl-of: plugins/sdd-workflow/scripts/session-start.py` と `impl-of: plugins/sdd-workflow/scripts/hook_common.py` |

## 人の作業（分類ごと）

| 分類 | 作業 | 対象 |
|:--|:--|:--|
| `keep` | なし | proof-gate 5 件、sdd-init `no_section_appends`、session-config `config_wins` |
| `to_tests`（ディレクトリ内に `keep` が残る） | `LAWS.bend` から該当法則を削除 → `PROOF.bend` の対応する証明を削除 → `run-verification.py proof --print-laws-hash --laws-dir <dir>` で新ハッシュを得て `# approved:` 行を書き直す → `/run-checklist <feature> 218 --category proof` で PASS 確認 | sdd-init（2 件）、session-config（6 件） |
| `to_tests`（全法則が移る） | 法則ディレクトリ（`LAWS.bend` / `main.bend` / `PROOF.bend`）を削除 → spec front matter の `laws:` と `laws-status` を除去 → 差分テスト（作成済み）が検証先 | constitution-injection、naming-enforcement、stale-doc-detection |
| `prose_delete` | `impl-of:` を spec に追記（上表）→ 法則ディレクトリを削除 → spec front matter の `laws:` と `laws-status` を除去 → 理由 `prose_implementation` は ADR 2026-10-22 に記録済み | prd-generation、front-matter-validation、vibe-detection、clarify、doc-consistency-check、impl-spec-check |

削除前に `python3 -m pytest tests/laws/ -q` が PASS であることを確認する。AI はこの表の作成までで、`LAWS.bend`・spec の front matter・承認行には触れていない。
