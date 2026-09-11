---
name: evaluate-skills
description: "plugins/sdd-workflow 配下の全スキルを実際に実行して動作評価し、改善点をHTMLレポートで出力する。既存の .claude/skill-evals/ にあるブランチ固有コーパス比較インフラ（main/develop それぞれの実 .sdd/ ツリー × skill/without の4条件を組み、世代ごとのリフトの差で改善量を出す v3 手法）を再利用し、Workflow ツールで実行をファンアウトし、独立グレーダーで採点し、skill-creator の eval-viewer を土台にしたHTMLで「without_skill が with_skill と同点/優位になる vacuous baseline の4仮説診断（skill自体が不要／assertionが本質を捉えていない／コストが悪化している／eval promptやfixtureが漏洩している）」「スキル自体の改善点」「評価手法自体の改善点」を報告する。ユーザーが「スキルの評価をして」「skill-evals を実行して」「プラグインのスキルの品質を測って」「19スキルの動作確認をして」「定期的にスキル品質をチェックしたい」と言ったときは必ず使用する。frontmatter設計・入出力セクションの有無など静的なドキュメント品質レビューは review-plugin スキルの担当であり、本スキルはそれとは重複しない——実際にスキルを実行して有効性を測る動作評価専用。"
license: MIT
argument-hint: "[--skills <name1,name2,...>] [--report-dir <path>]"
allowed-tools: Read, Glob, Grep, Bash, Workflow
disable-model-invocation: true
---

# Evaluate Skills — sdd-workflow プラグインのスキル動作評価

`plugins/sdd-workflow/skills/` 配下の各スキルを実際に実行させて評価し、改善点をHTMLレポートで
出力する。静的なドキュメント品質レビュー（frontmatter設計・入出力セクションの有無など）は
`review-plugin` スキルの担当であり、本スキルは重複させない。本スキルが扱うのは
**動作評価**（実際にタスクをやらせて有効性を測る）専用。

## 入力

$ARGUMENTS

- `--skills <name1,name2,...>`: 評価対象を絞る。省略時は `.claude/skill-evals/` に
  `evals.json` があるスキル全部が対象
- `--report-dir <path>`: レポート保存先。省略時は `.claude/skill-evals/reports/<実行日 YYYY-MM-DD>/`

フルスイートは19スキル・20 eval で **76セル**（`develop` 専用 eval 2件は2条件、残り18件は
4条件）。これに採点エージェントが加わるので非常にコストが高い。初回実行や動作確認では
`--skills` で1〜2スキルに絞ったスモールランを強く推奨する。

**1セル1ランでは改善量は測れない**（iteration-1 のノイズ床は 20pt）。有意な数値が必要な場合は
セルあたりのラン数を増やし、それをしていない実行では結果に測定限界を明記する。

## 前提条件

- `.claude/skill-evals/README.md` の評価手法（ブランチ固有コーパス比較: `main` / `develop`
  それぞれの実 `.sdd/` ツリー × skill/without の4条件）を理解してから進める。**生の pass rate を
  世代間で直接比較してはならない** — コーパス自体が世代で違うため、比較できるのは
  `lift(era) = score(era/skill) − score(era/without)` の**差**だけ
- `.claude/skill-evals/ASSERTION_DESIGN.md` を読み、assertion の判定基準
  （バージョン中立に書く、等）を把握する。**未確認のまま assertion を書き換えない**
- `references/vacuous-baseline-diagnostic.md` を読む。`without_skill` が `with_skill` と
  同点または上回る（特に両方とも1.0=完全なタイ）run は、フルスイート評価が
  スキルの有効性を測れていない最重要の失敗モードであり、4仮説（skill自体が不要／
  assertionが本質を捉えていない／コストが悪化している／eval promptやfixtureが
  漏洩している）で分類・報告する（Step 4〜5で実施）
- skill-creator プラグインがインストールされている必要がある。インストールパスは
  固定ではないため、`scripts/resolve_skill_creator_path.sh` を実行して都度解決する
  （以下 `$SKC` と表記）
- **コスト計測の優先順位**: 仮説「skill使用時のコストが悪化している」を検証するため、
  1) executor に `outputs/metrics.json`（tool_calls・output_chars等。スキーマは
  `$SKC/references/schemas.md` の `metrics.json` 定義）を必ず書かせる（後述 Step 3）。
  これが一次指標。2) wall-clock時間は Workflow の `agent()` 戻り値に per-agent の
  duration が含まれないため、executor 自身に Bash の `date +%s` で開始・終了を
  自己記録させる以外に手段が無い。自己記録である以上、並行実行時のスケジューリング
  競合の影響を受けうる**近似値**として扱い、`benchmark.json` には
  `"self_reported_approximate": true` 相当の注記を添える。主指標は必ず 1) とする

## 処理フロー

### Step 0: 対象スキルの確定

1. `plugins/sdd-workflow/skills/*/` を Glob して全スキル一覧を取得
2. `--skills` 指定があればそれで絞る
3. 各スキルについて `.claude/skill-evals/<skill>/evals.json` の存在を確認。無いものは
   「評価データ未整備」としてレポートの `coverage_gaps` に記録し、実行対象からは除外する
   （evals.json を今その場で書き起こすことはしない — 評価対象のカバレッジ拡張は別タスク）

### Step 1: レポートディレクトリの準備

`<report-dir>/fixtures/`, `<report-dir>/runs/`, `<report-dir>/grading/` を作成する。

### Step 2: Fixture構築

フィクスチャは **eval 単位**で作る。v3 の `fixture` ブロック（`remove` / `remove_section` /
`strip_front_matter` / `copy_scenario` / `corpus: empty-project`）は eval ごとに違う変形を宣言するため、
スキル単位で1つ作ると eval 間で変形が混ざる。

対象スキルの各 eval × 2世代について実行する。

```bash
python3 .claude/skill-evals/build_sdd_fixture.py <origin/main|develop> \
  <report-dir>/fixtures/<era>/<skill>/<eval-id> \
  --eval .claude/skill-evals/<skill>/evals.json --eval-id <eval-id>
```

各出力ディレクトリに `FIXTURE.md`（ブランチ・コミット・適用した変形の記録）が生成される。
**`## Transforms applied` の全行を確認する** — `MISSING` で始まる行があれば宣言した変形が効いて
いないので、そのセルは無効として扱い、評価を続行せず原因を報告する。`FIXTURE.md` 自身は
コーパスの一部ではないので、ランのプロンプトで参照させない。

`main` に対応物が無い `develop` 専用 eval（`render-adr-review` の全 eval、`recommend-front-matter`
の eval 1）は develop 側だけを構築し、リフト差ではなく **develop 内のリフトのみ**を報告する。

ノイズ床を知りたい場合は合成対照群を追加で構築する。`--skill-from <ref>` は対象スキルだけを
別 ref のコピーへ差し替えるので、両世代が同一の `SKILL.md` を持つ状態になり、リフト差は
**構造上ゼロでなければならない**。出た差はそのままノイズの大きさである。

`build_fixtures{,_2,_hard}.py`（v2 の合成フィクスチャ生成）は**使わない**。v2 の出力は
`notification-badge` のような架空機能の `.sdd/` ツリーで、v3 の eval が名指しする実パス
（`.sdd/specification/workflow-foundation/session-config_spec.md` 等）を含まない。渡すとランは
即席の代替を探して出力し、グレーダーは採点し、`benchmark.json` は正常な形で無効な数値を出す。
`vibe-detector` のようにテキスト専用でコーパスに依存しないスキルも、`.sdd/` を参照する
`without` 条件との対比のためフィクスチャは構築する。

続けて、eval prompt / fixture が対象スキルの `SKILL.md` の指示内容をどれだけ
漏洩してしまっているか（仮説「eval promptのコンテキスト量が膨大でskillと大差ない」）を
LLM を使わず安価にスコアリングする:

```bash
python3 .claude/skills/evaluate-skills/scripts/score_eval_leakage.py \
  .claude/skill-evals \
  plugins/sdd-workflow/skills \
  <report-dir>/fixtures \
  <report-dir>/eval_leakage_scores.json
```

これは粗い一次フィルタであり判定ではない（深い判定は Step 5 で行う）。次の Step 3 の
確認ゲートで、overlap ratio が高い上位候補を一緒に提示する。

### Step 3: Workflow による実行ファンアウト

**Workflow ツールを使う。** Workflow はユーザーの明示的な opt-in を要求する仕組みなので、
本スキルの起動指示だけでは opt-in とみなさず、実行直前に対象スキル数・想定エージェント数に加え、
`eval_leakage_scores.json` の overlap ratio が高い上位候補（例: 上位3件）を一緒に提示して
ユーザーに確認を取る。セル数は eval 単位で数える（`develop` 専用 eval は2、それ以外は4条件）。
採点エージェントも1セルにつき1体加わる。

Workflow スクリプトの設計方針:

- `args` として対象スキルの配列を渡す。各要素は
  `{ name, evalsPath, skillMdPath, evals: [{ id, mainFixtureDir, developFixtureDir }] }`
  （フィクスチャは eval 単位なので、スキル単位に1組ではなく eval ごとに持たせる）
- `pipeline(skills, executeStage, gradeStage)` を使う。あるスキルの採点が進んでいる間に
  別スキルの実行を並行させ、フルスイートの総待ち時間を縮める
- `executeStage(skill)`: `evalsPath` の `evals.json` を読み、eval ごとに4条件
  （`main_without` / `main_skill` / `develop_without` / `develop_skill`）を `parallel()` で実行する。
  `develop` 専用 eval は develop 側の2条件のみ。
  各 `agent()` のプロンプトには、対応する fixture ディレクトリを作業対象として与え、
  `_skill` 系条件では対象スキルの `SKILL.md` を読み込んで従うよう明記する。出力は
  `<report-dir>/runs/<skill>/<eval-id>/<condition>/outputs/` に保存させる
- **コスト計測の必須化（executor プロンプトへの必須指示）**: 完了時に
  `outputs/metrics.json` を `{tool_calls, total_tool_calls, total_steps, files_created,
  errors_encountered, output_chars, transcript_chars}`（`$SKC/references/schemas.md` の
  `metrics.json` 定義）の形式で必ず書かせる。加えて、最初の Bash 呼び出しの直前と
  最後の Bash 呼び出しの直後に `date +%s` を実行させ、その差分を
  `<report-dir>/runs/<skill>/<eval-id>/<condition>/timing.json` に
  `{"duration_seconds": ..., "self_reported_approximate": true}` として保存させる
  （前提条件節の「コスト計測の優先順位」参照。metrics.json が一次指標、timing.json は
  近似値の補助指標）
- `gradeStage(execResult, skill)`: まず `grade.py` でスクリプト判定可能な assertion を採点する。

  ```bash
  python3 .claude/skill-evals/grade.py <run-outputs-dir> --skill <skill> --json
  ```

  登録があるのは `analyze-requirements`（A3 / A4）と `task-cleanup`（A2 / A4）だけで、それ以外の
  スキルは exit 1 と「機械検査は定義されていない」を返す。これは異常ではなく既定の状態なので、
  その場合は全 assertion をエージェント判定に回す。判定が `????`（`UNPARSEABLE`）で返った
  assertion もエージェント判定へ回す。また `grade.py` は `evals[0]` 固定なので、eval が複数ある
  スキル（`recommend-front-matter`）では eval 0 以外に使わない。

  残りの assertion を `references/grading-guide.md` に従い独立グレーダーサブエージェントに回す
  （`agentType` は既定のまま、grader.md の Process をプロンプトに埋め込む）。スクリプト判定とエージェント判定を
  マージした `grading.json` を `<report-dir>/runs/<skill>/<eval-id>/<condition>/grading.json`
  に保存し、各 assertion がどちらで判定されたかを `evidence` に残す。

  **`grade.py` の結果をエージェント判定で上書きしない。** 逆に、`grade.py` の登録を増やす判断は
  この場でしない — 機械化を試して差し戻した4件とその理由は `grade.py` の docstring にあり、
  同じ罠を踏み直さないための記録である
- **executor プロンプトへの安全ガード（必須）**: 「ツールのパーミッション確認（サンドボックスの
  破壊的操作確認等）がブロックされた場合、別のコマンド・別の呼び出し経路（例: `/bin/rm -rf` で
  `rm -r` の確認を回避する等）で確認を迂回してはならない。ブロックされたらその時点で作業を停止し、
  ブロックされた操作と理由を transcript.md / user_notes.md に記録して報告すること」という一文を
  必ず含める（2026-09-08 のフルスイート再実行で、task-cleanup の `new_skill` executor がこの回避を
  実際に行ったことが確認されている。対象はこのrun専用の使い捨てworkdirに限られ実害はなかったが、
  同種の振る舞いを許可し続けないためこのガードを追加した）

### Step 4: 集計

1. 全 `grading.json` を読み、スキル×世代ごとに
   `lift(era) = pass_rate(era/skill) − pass_rate(era/without)` を計算する
2. スキルごとに **改善量 = `lift(develop) − lift(main)`** を出す。これが報告すべき数値である。
   `main/skill` と `develop/skill` の生スコアを並べて優劣を語ってはならない（コーパス自体が
   世代で違うため）。`develop` 専用 eval は `lift(develop)` のみを載せ、改善量の欄は空にする
3. 合成対照群を走らせた場合は、その改善量（構造上ゼロであるべき値）を**ノイズ床**として併記する。
   ノイズ床を下回る改善量は「差が無い」と読む。ノイズ床が未測定なら、そう明記する —
   数値だけを出して読み手に有意性の判断を委ねてはならない
4. `<report-dir>/benchmark.json` を skill-creator の `references/schemas.md`
   （`$SKC/references/schemas.md`）が定める `benchmark.json` スキーマに従って生成する。
   `configuration` は `with_skill` / `without_skill` の2値固定（viewer がこの文字列で
   色分けする）。世代の区別は `eval_name` に含めて表現する
   （例: `"main: distribution-prd-requirement-diagram"`）。**`eval_name` はスキルをまたいで衝突しうる**
   （同じ eval 名を複数スキルが使うケースが実際に発生した）。この衝突は viewer の表示上の
   問題に留まり、後述 3 の判定には影響しない（3 は `eval_name` を使わず `runs/` の
   ディレクトリ構造から直接判定するため）
3. `<report-dir>/vacuous_baseline_candidates.json` を生成する
   （`without_skill.pass_rate >= with_skill.pass_rate` となる (skill, era) 組の機械的検出。
   LLMの算術判断に頼らず決定的スクリプトで行う）:
   ```bash
   python3 .claude/skills/evaluate-skills/scripts/detect_vacuous_baselines.py <report-dir>
   ```
4. `<report-dir>/recurring_findings_candidates.json` を生成する（前回以前のレポートと比較し、
   同じ assertion の弱さが何回再発しているかを機械的に検出。`<reports-root>` は
   `<report-dir>` の親ディレクトリ、通常 `.claude/skill-evals/reports`）:
   ```bash
   python3 .claude/skills/evaluate-skills/scripts/diff_recurring_findings.py \
     <reports-root> <report-dir>
   ```
5. `<report-dir>/run_artifact_audit.json` を生成する（**evaluate-skills 自身**の実行品質の
   機械点検。対象スキルの評価データではなく、runs/ 配下のアーティファクトの健全性
   ——transcript.md/outputs/grading.json/metrics.json/timing.jsonの欠落率、grading.json の
   誤配置、安全ガード違反を示す事後キーワードの出現——を集計する）:
   ```bash
   python3 .claude/skills/evaluate-skills/scripts/audit_run_artifacts.py <report-dir>
   ```

### Step 5: メタ評価（評価手法自体の改善点、および evaluate-skills 自身の改善点）

`references/analysis-guide.md` に従い、全 grading データ・`vacuous_baseline_candidates.json`・
`eval_leakage_scores.json`・`recurring_findings_candidates.json`・`run_artifact_audit.json` を
俯瞰するメタ評価エージェントを1体起動する。出力は `<report-dir>/meta_analysis.json`。

**最重要**: `vacuous_baseline_candidates.json` の各候補を
`references/vacuous-baseline-diagnostic.md` の4仮説（skill自体が不要／assertionが本質を
捉えていない／コストが悪化している／eval promptやfixtureが漏洩している）で分類し、
`meta_analysis.json` の `vacuous_baselines` フィールドに出力する。
**この分類・推奨アクションは提示のみで、`evals.json`/`SKILL.md`/fixture を自動的に
書き換えない**（Step 0 の非侵襲方針と同様）。

**evaluate-skills 自身の自己反省**: `run_artifact_audit.json` の集計結果（欠落率・誤配置・
安全ガード関連キーワードの候補ヒット）を読み、`likely_cause` 判定と同じ非侵襲方針で
`evaluate_skills_self_review` フィールドに評価対象10スキルとは別枠でまとめる。
キーワードヒットは事後判定候補であり確定した違反ではない点に注意し、疑わしい候補は
該当 run の transcript.md/user_notes.md を実際に読んで確認した上で報告する（本skillは
自分自身の SKILL.md/scripts を自動的に書き換えない。改善提案の提示のみ）。

### Step 6: HTML出力

```bash
python3 "$SKC/eval-viewer/generate_review.py" <report-dir>/runs \
  --skill-name "sdd-workflow (対象N件)" \
  --benchmark <report-dir>/benchmark.json \
  --static <report-dir>/report.html
```

`references/html-report-guide.md` の手順で、生成された `report.html` に
「ベースライン(skill無し)満点診断」「スキル改善提案」「評価手法自体の改善点」
「evaluate-skills 自身の実行品質」の4セクションを `meta_analysis.json` の内容から
**この順番で**追記する（1番目のセクションが最優先の理由は
`references/vacuous-baseline-diagnostic.md` 参照。4番目は対象スキルとは別枠の自己反省
であるため最後に置く）。

## 出力形式

- `<report-dir>/report.html`: ブラウザで開けるレポート。skill-creator 標準の
  Outputs/Benchmark タブに加え、「ベースライン(skill無し)満点診断」「スキル改善提案」
  「評価手法自体の改善点」「evaluate-skills 自身の実行品質」の4セクションを持つ
- 実行完了後、レポートの絶対パスを提示し `open <path>` で開くことを促す
- `<report-dir>/meta_analysis.json`、`<report-dir>/vacuous_baseline_candidates.json`、
  `<report-dir>/eval_leakage_scores.json`、`<report-dir>/recurring_findings_candidates.json`、
  `<report-dir>/run_artifact_audit.json`、各 `grading.json`/`metrics.json`/`timing.json` は
  生データとして残す
  （次回実行時の比較や、手動での深掘りに使える。特に `recurring_findings_candidates.json`
  は次回実行時に本レポートが「過去レポート」として参照されるため削除しないこと）

## 注意

- 本スキルは**動作評価専用**。frontmatter・入出力設計などの静的レビューは
  `review-plugin` に委ねる（重複させない）
- **定期実行の仕組みは本スキル自身には持たせない**。`/loop` や `CronCreate` など
  外部のスケジューリング機構から本スキルを定期的に呼び出す運用を想定する
- 世代間の**生の pass rate** を直接比較して優劣を語らない。`main` と `develop` では `.sdd/`
  コーパス自体が違うため、生スコアの差には「スキルが良くなった」以外の要因が混ざる。
  有効なのは同一世代内のリフト（`era/skill` vs `era/without`）と、その**リフトの差**
  （`lift(develop) − lift(main)`）だけ（`.claude/skill-evals/ASSERTION_DESIGN.md` 参照）
- 1セル1ランでは改善量を測れない。iteration-1 のノイズ床は 20pt で、`doc-consistency-checker`
  では `without` 条件のばらつきがスキルの効果を上回った（`MEASUREMENT_LOG.md` 参照）。
  セルあたりのラン数を増やすか、測れない旨を明示して報告する
