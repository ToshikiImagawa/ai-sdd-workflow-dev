---
name: evaluate-skills
description: "plugins/sdd-workflow 配下の全スキルを実際に実行して動作評価し、改善点をHTMLレポートで出力する。既存の .claude/skill-evals/ にある dual-era fixture 比較インフラ（old/new レイアウト × skill/without の4条件を同一世代内でのみ比較する v2 手法）を再利用し、Workflow ツールで実行をファンアウトし、独立グレーダーで採点し、skill-creator の eval-viewer を土台にしたHTMLで「スキル自体の改善点」と「評価手法自体の改善点」の両方を報告する。ユーザーが「スキルの評価をして」「skill-evals を実行して」「プラグインのスキルの品質を測って」「19スキルの動作確認をして」「定期的にスキル品質をチェックしたい」と言ったときは必ず使用する。frontmatter設計・入出力セクションの有無など静的なドキュメント品質レビューは review-plugin スキルの担当であり、本スキルはそれとは重複しない——実際にスキルを実行して有効性を測る動作評価専用。"
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

19スキル×4条件のフルスイート評価は非常にコストが高い。初回実行や動作確認では
`--skills` で1〜2スキルに絞ったスモールランを強く推奨する。

## 前提条件

- `.claude/skill-evals/README.md` の評価手法（dual-era fixture比較: old/new × skill/without
  の4条件、**同一世代内での比較のみ有効**）を理解してから進める
- `.claude/skill-evals/ASSERTION_DESIGN.md` を読み、assertion の判定基準
  （バージョン中立に書く、等）を把握する。**未確認のまま assertion を書き換えない**
- skill-creator プラグインがインストールされている必要がある。インストールパスは
  固定ではないため、`scripts/resolve_skill_creator_path.sh` を実行して都度解決する
  （以下 `$SKC` と表記）

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

```bash
python3 .claude/skill-evals/build_fixtures.py      <report-dir>/fixtures
python3 .claude/skill-evals/build_fixtures_2.py    <report-dir>/fixtures
python3 .claude/skill-evals/build_fixtures_hard.py <report-dir>/fixtures
```

`<report-dir>/fixtures/{old,new}/<skill>/` が生成されたことを Glob で確認する。
vibe-detector 等テキスト専用で `.sdd/` ツリーを前提にしないスキルは、fixture 無しで
プロンプトのみのラン（後述 Step 3）になる。

### Step 3: Workflow による実行ファンアウト

**Workflow ツールを使う。** Workflow はユーザーの明示的な opt-in を要求する仕組みなので、
本スキルの起動指示だけでは opt-in とみなさず、実行直前に対象スキル数・想定エージェント数
（対象スキル数 × 4条件 × 平均eval数）を提示してユーザーに確認を取る。

Workflow スクリプトの設計方針:

- `args` として対象スキルの配列を渡す。各要素は
  `{ name, evalsPath, oldFixtureDir, newFixtureDir, skillMdPath }`
- `pipeline(skills, executeStage, gradeStage)` を使う。あるスキルの採点が進んでいる間に
  別スキルの実行を並行させ、フルスイートの総待ち時間を縮める
- `executeStage(skill)`: `evalsPath` の `evals.json` を読み、eval ごとに4条件
  （`old_without` / `old_skill` / `new_without` / `new_skill`）を `parallel()` で実行する。
  各 `agent()` のプロンプトには、対応する fixture ディレクトリを作業対象として与え、
  `_skill` 系条件では対象スキルの `SKILL.md` を読み込んで従うよう明記する。出力は
  `<report-dir>/runs/<skill>/<eval-id>/<condition>/outputs/` に保存させる
- `gradeStage(execResult, skill)`: 各 run について `references/grading-guide.md` に従い
  独立グレーダーサブエージェントを起動する（`agentType` は既定のまま、grader.md の
  Process をプロンプトに埋め込む）。`grading.json` を
  `<report-dir>/runs/<skill>/<eval-id>/<condition>/grading.json` に保存する

### Step 4: 集計

1. 全 `grading.json` を読み、スキル×世代ごとに
   `lift = pass_rate(skill条件) - pass_rate(without条件)` を計算する
2. `<report-dir>/benchmark.json` を skill-creator の `references/schemas.md`
   （`$SKC/references/schemas.md`）が定める `benchmark.json` スキーマに従って生成する。
   `configuration` は `with_skill` / `without_skill` の2値固定（viewer がこの文字列で
   色分けする）。old/new の区別は `eval_name` に世代を含めて表現する
   （例: `"old: notification-badge-extract"`）

### Step 5: メタ評価（評価手法自体の改善点）

`references/analysis-guide.md` に従い、全 grading データを俯瞰するメタ評価エージェントを
1体起動する。出力は `<report-dir>/meta_analysis.json`。

### Step 6: HTML出力

```bash
python3 "$SKC/eval-viewer/generate_review.py" <report-dir>/runs \
  --skill-name "sdd-workflow (対象N件)" \
  --benchmark <report-dir>/benchmark.json \
  --static <report-dir>/report.html
```

`references/html-report-guide.md` の手順で、生成された `report.html` に
「スキル改善提案」「評価手法自体の改善点」の2セクションを `meta_analysis.json` の内容から
追記する。

## 出力形式

- `<report-dir>/report.html`: ブラウザで開けるレポート。skill-creator 標準の
  Outputs/Benchmark タブに加え、「スキル改善提案」「評価手法自体の改善点」セクションを持つ
- 実行完了後、レポートの絶対パスを提示し `open <path>` で開くことを促す
- `<report-dir>/meta_analysis.json` と各 `grading.json` は生データとして残す
  （次回実行時の比較や、手動での深掘りに使える）

## 注意

- 本スキルは**動作評価専用**。frontmatter・入出力設計などの静的レビューは
  `review-plugin` に委ねる（重複させない）
- **定期実行の仕組みは本スキル自身には持たせない**。`/loop` や `CronCreate` など
  外部のスケジューリング機構から本スキルを定期的に呼び出す運用を想定する
- 世代間（old vs new）の生の pass rate を直接比較して優劣を語らない。有効な比較は
  同一世代内（`old/skill` vs `old/without`、`new/skill` vs `new/without`）のみ
  （`.claude/skill-evals/ASSERTION_DESIGN.md` 参照）
