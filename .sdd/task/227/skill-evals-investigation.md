# skill-evals 基盤調査（#227）

- 実施日: 2026-10-23
- 対象: prose 実装 6 spec の性質 29 件（#220 で法則化対象外にしたもの）の機械検証先
- 候補: (A) Claude Code 公式 `claude plugin eval`、(B) 既存 `.claude/tests/harness/`（A/B トークン計測）

## 結論

**(A) `claude plugin eval` を採用する。** (B) はトークン削減量を測るハーネスで、出力に対する assertion を持たない。

## (A) `claude plugin eval` の仕様（Claude Code 2.1.306 で実測）

公開ドキュメントのページは無い（CLI 埋め込みの `references/plugin-eval.md` が唯一の資料）。以下は `--help`、`init --bare` の出力、バイナリ内のスキーマ定義、実行結果から確認した。

| 項目 | 内容 |
|:--|:--|
| 配置 | プラグイン直下 `evals/<case>/prompt.md` + `evals/<case>/graders/*.md`。`plugin.json` の `experimental.evals` か `--eval-dir` で変更可 |
| prompt.md | front matter: `name`, `description`, `tags`, `runs`（既定 3）, `max_turns`（既定 10）, `timeout_seconds`（既定 300）, `allowed_tools`, `disallowed_tools`, `model`, `append_system_prompt`, `env`（`EVAL_*` のみ）。本文がユーザープロンプト |
| grader 種別 | `regex`（`target`: last_message 等、`pattern`、`flags`、`match`: contains / not_contains / count:N）、`tool_used`（`tool`、`input_match`、`min` / `max`）、`tool_order`、`file_exists`、`llm`（`criteria`、判定モデル既定 haiku）、`baseline` |
| 実行 | 一時ワークスペース・独立 HOME・`dontAsk`。対象プラグインのみロード。フック（SessionStart / UserPromptSubmit）は実行される |
| 非対話実行 | `--trust-plugin` で非対話。認証は実行者の Claude Code ログイン。`--json <file>` で v1 形式、`--threshold`（既定 1.0）未満は exit 1、`--max-cost-usd` 超過は exit 2 |
| 導入版 | eval / init は 2.1.198、`--json` v1 と `--report` は 2.1.210、`--no-publish` は 2.1.224 以降 |

### パイロット実測

ケース `vibe-detection/risk-level-exactly-one`（プロンプト「ログイン機能をいい感じに作って。」、regex grader 2 件）を `--runs 1 --ablation none` で 2 回実行。

| 回 | 所要 | コスト | 結果 |
|:--|--:|--:|:--|
| 1 | 9 秒 | $0.097 | score 0.5（`risk_level_exactly_one` 不一致） |
| 2 | 12 秒 | $0.065 | score 0.5（同上） |

29 ケース × 既定 3 回で概算 $6〜9 / 1 回の CI 実行。`--runs 1` なら $2〜3。

### パイロットが検出したこと（実装側の問題）

UserPromptSubmit フックは発火し「vibe-detector スキルのフローに従え」という additional context は注入されたが、モデルは **vibe-detector のリスクレポート形式を出力せず**、通常の確認質問で応答した（2 回とも）。トレースの `init` イベントに列挙されたスキル一覧に `sdd-workflow:vibe-detector` と `sdd-workflow:doc-consistency-checker` が **含まれていない**（`user-invocable: false` の 2 スキル）。フックの指示だけではスキル本文がロードされず、spec 3.1.1 の「リスクレベルをちょうど 1 つ出力する」以前に、リスクレベル自体が出力されていない。

これは skill-evals が狙いどおり散文実装の乖離を検出した最初の例であり、ケース側の誤りではない。同じ実験で `doc-consistency-checker`（同じく `user-invocable: false`）はプロンプトで名指しすれば `Skill` 経由で起動したので、原因はスキルの可視性ではなくフックの指示文。`user-prompt-submit.py` の注入文に Skill 呼び出しとリスクレポート出力を明示する修正を本チケットで入れた（結果は下の「全件実行」節）。

## (C) 既存の `.claude/skill-evals/` + `/evaluate-skills`（issue 起票時に見落としていた）

リポジトリには既にスキル評価基盤がある。22 スキル分の `evals.json`、`ASSERTION_DESIGN.md`（正典）、`MEASUREMENT_LOG.md`、`build_sdd_fixture.py`、`grade.py`。

| 観点 | (C) 既存 skill-evals | (A) `claude plugin eval` |
|:--|:--|:--|
| 測るもの | **main → develop のリフト差**（スキル有無 × 2 世代の 4 バリアント）。「スキルがどれだけ良くなったか」 | ケース単位の合否。「spec の決定表どおりに振る舞うか」 |
| assertion | バージョン中立な散文（例「リスクレベルの判定根拠が仕様の有無と整合している」）を**独立グレーダー agent** が判定。機械判定は `grade.py` の 4 関数のみ | regex / tool_used が主、LLM judge は補助 |
| 実行 | `/evaluate-skills` が Workflow でファンアウト（1 eval = 4 セル + 採点 4 体）。手動・高コスト・CI 不可 | CLI 1 コマンド、非対話、`--json` / exit code |
| spec 節との結び | 無し（原則ベース） | `description` / `tags` に節参照を書ける |

結論: (C) は改善計測、(A) は spec 準拠の回帰検出で**役割が違う**。#227 の 29 件は決定表の行なので (A)。(C) の vibe-detector eval（曖昧表現の検出、根拠の整合、偽陽性なし、代替案提示、強制しない）とは重ならない。`ASSERTION_DESIGN.md` の「実装詳細ではなく本質を測る」原則は (A) のケースにも適用する（出力の見出し文言ではなく、spec が規定する結果を見る）。

注: `skill-evals/README.md` は「`skills/*/evals/` は plugin-lint の Check 2 で CI エラー」と書いているが、プラグイン**直下**の `evals/` は Check 2 の対象外で `plugin-lint.sh` は exit 0（実測）。`claude plugin eval` の既定配置がそのまま使える。

## (B) `.claude/tests/harness/` を使わない理由

`run_ab.sh` は off / on 2 群で同一プロンプトを N 回流し、`aggregate_tokens.py` が transcript の tool_result トークンを集計する。品質比較 `compare_quality.py` はあるが決定表 1 行単位の assertion は無く、Vertex / API キーの tokenizer 環境も要る。性質検証に転用すると grader 層を自作することになり、(A) と重複する。

## 設計（ケース記述規約）

- 1 ケース = spec 決定表 1 行または不変条件 1 件。ディレクトリ `evals/<feature>/<property>/`
- `prompt.md` の `description` に `spec <path> <節>:` 形式で出典を書き、`tags` に `<feature>` と `spec-<節>` を付ける（差分テストの `# source:` に相当。節ハッシュ照合は本 issue では行わない）
- grader は決定表の「結果」列を regex で機械判定するものを必ず 1 件置き、LLM judge は補助に留める
- 評価対象プロンプトは `SDD_LANG` 既定（en）で動く前提で書き、regex は英日両表記を許容する
- 実行オプションは `--runs 1 --ablation none --no-publish --max-cost-usd <上限> --json`。閾値は既定 1.0。CI には入れない（オーナー判断: 1 回 $4〜5 のモデル課金が発生するため。手元の Claude Code ログインで実行する）。実行経路は開発スキル `/plugin-evals`（`.claude/skills/plugin-evals/`。`scripts/` は CI ジョブと 1:1 の置き場なのでラッパーはそこに置かない）

## 全件実行（32 ケース、`--runs 1`）

| 回 | 条件 | 結果 | コスト | 所要 |
|:--|:--|:--|--:|--:|
| 1 | 初版ケース、フック修正前 | 18/32 | $3.79 | 245 秒 |
| 2 | グレーダー修正（negative grader の見直し、`under()` の行形式必須化、clarify の regex 拡張）＋フック修正後 | 27/32 | $4.01 | 297 秒 |
| 3 | レビュー反映後の部分再実行（front-matter 19 / doc-consistency 3 / vibe 1） | 21/23 | $2.58 | — |

### 1 回目 → 2 回目で直したもの（ケース側の誤り）

- impl-spec-check: 「Info（Critical から降格）」という check-spec の必須出力（Downgrade Summary）に negative grader が誤爆。negative grader を削除
- front-matter-validation: negative grader `not_reported_at_other_severity` が「同じフィールド名が他の重大度の行に一切出ない」を要求していたが、エージェントは 1 フィールドに複数チェックを持つ（depends-on は 4 件）ので正しい報告でも落ちる。削除し、肯定 grader（フィールド名と重大度が同一行）だけにした。フィールド名の一致には `(?<![\w-])…(?![\w-])` の境界を付け、`id` が `invalid` に一致しないようにした
- doc-consistency-check: `\bunknown|absent\b` の `|` が括弧漏れで全体を二分していた（`unknown` 単独で成立）。`\b(?:unknown|absent)\b` に修正。プロンプトからは「stale = …」の定義文を外した（定義はスキルの責務）
- clarify/below-threshold: 「追加の明確化を推奨」の表現揺れに regex が狭すぎた
- vibe-detection: 見出し `###` 固定の regex を、太字行・箇条書きも許す形にした（spec が規定するのは「レベルがちょうど 1 つ」であって見出しの形ではない）

### 実装側で直したもの

- `user-prompt-submit.py`: 注入文を「Skill ツールで `sdd-workflow:vibe-detector` を起動しリスクレポートを出せ」に変更。従来の「フローに従え」ではスキル本文がロードされなかった（1 回目・2 回目とも 0/1）
- `vibe-detector/templates/{en,ja}/risk_report*.md`: リスクレベル行を literal `High / Medium / Low` からプレースホルダ `{High | Medium | Low}` に変更（モデルが literal をそのまま写す余地を消す）

### 残る赤（3 回目時点）と理由

| ケース | 状態 | 理由 |
|:--|:--|:--|
| `front-matter-validation/impl-status-reality-is-info` | 不安定（2 回目 pass、1・3 回目 fail） | エージェントが `impl-status` に言及しない回がある。spec 行 17「impl-status を実コードと照合できない → info」はエージェント定義側の記述が薄く、出力に揺れがある。エージェント定義の見直し候補 |
| `front-matter-validation/status-propagation-is-info` | 不安定（2 回目 pass、3 回目 fail） | 上流 PRD の `updated` が下流 spec より新しい fixture でも、status 伝播を報告しない回がある。同上 |
| `vibe-detection/risk-level-exactly-one` | 不安定（3 回目 2 試行中 1 pass） | スキルは起動しレベルも 1 つ出すが、ラベル行の形が毎回違う（`**リスクレベル: High**` / 文中）。テンプレート修正後は改善の見込み |

残りはすべて pass。`--runs 1` では上の不安定ケースが赤になることがある。

### spec と実装のギャップ（本チケットでは直さず PR に記載）

- `front-matter-validation_spec` 3.1.1 の行 13（laws-status 不整合）・14（status 整合性）・18（status 伝播）は、エージェント定義では `--cross-ref` 時のみ検査するが、spec の行にその限定が書かれていない。ケースは `--cross-ref` 付きで書いた
- `clarify_spec` の用語表は「総合スコア = Clear ÷ 全項目数」、`skills/clarify/SKILL.md` は「Clear ÷ (全項目 − N/A)」。N/A が 0 のときだけ一致する。ケースは N/A 0 件で書いたのでこの差は検出しない
