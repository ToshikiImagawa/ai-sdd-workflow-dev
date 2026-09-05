# skill-evals

`plugins/sdd-workflow/skills/` 配下のスキルを評価・改善する際に使うテストケースと、その評価手法を保存するディレクトリ。

`plugins/sdd-workflow/skills/<skill>/evals/` には置かない（`scripts/plugin-lint.sh` の Check 2 が `skills/*/` 配下の許可ディレクトリを `templates`/`examples`/`references`/`scripts` に限定しているため、`evals/` を置くとCIエラーになる）。

## 構成

```
.claude/skill-evals/
├── ASSERTION_DESIGN.md          # 評価手法の正典。assertion の設計基準と、そこに至った経緯
├── MEASUREMENT_LOG.md           # 実測記録。各イテレーションの結果・ノイズ床・発見した実在欠陥
├── build_sdd_fixture.py         # v3: 実 .sdd/ コーパスからブランチ固有フィクスチャを構築
├── build_fixtures.py            # v2 の合成フィクスチャ生成（初期10スキル）。v3 では未使用
├── build_fixtures_2.py          # 同（残り9スキル）。v3 では未使用
├── build_fixtures_hard.py       # 同（高難度シナリオ：要求が互いに競合するケース）。v3 では未使用
└── <skill-name>/
    ├── evals.json               # プロンプト + assertion + フィクスチャ変形の宣言
    └── scenario/                # 一部のスキルのみ。フィクスチャへ投入する追加ファイル
```

## 評価手法（v3: 実 `.sdd/` コーパス）

測るもの: **`main` → `develop` でスキルがどれだけ良くなったか**。

### 1. フィクスチャはブランチの実 `.sdd/` ツリーそのもの

v2 は世代別の `.sdd/` を手で合成していた。v3 では合成しない。**このリポジトリは自分のプラグインで
dogfooding しているため、`main` と `develop` はそれぞれ自世代と整合した実 `.sdd/` ツリーを持っている**。

| | `main` | `develop` |
|:---|:---|:---|
| `.sdd/CONSTITUTION.md` | v4系（`adr/`・`design-draft` の記述なし） | v5系（`task/{ticket}/design-draft.md`・`adr/{feature}.md` を義務化） |
| `.sdd/adr/` | なし | あり |
| `.sdd/task/{ticket}/design-draft.md` | なし | あり |
| 設計成果物 | `specification/{feature}_design.md`（永続） | 上記 + ADR |

`git archive <branch> -- .sdd` を取るだけで世代整合フィクスチャが手に入る。手で書かないので、
`ASSERTION_DESIGN.md` の欠陥2（世代不一致のフィクスチャで新規約が旧世代へ漏れる）が構造的に起きない。

構築は `build_sdd_fixture.py` が担う。

```bash
python3 .claude/skill-evals/build_sdd_fixture.py develop /path/to/sandbox \
  --eval .claude/skill-evals/check-spec/evals.json
```

このスクリプトはブランチのツリー全体を展開した上で、次の3点を行う。

1. **`.claude/skill-evals/` を除外する** — eval 定義には採点基準が平文で書かれている。サンドボックスに
   残すと実行が自分の答案を読めてしまう
2. **`.sdd/.cache/` を削除する** — session-start が生成する索引。陳腐化した写しを残すと、実行が
   ドキュメントから読み解くべき情報を先に与えてしまう
3. **`.sdd/AI-SDD-PRINCIPLES.md` と `.claude/rules/ai-sdd-instructions.md` をブランチのプラグイン
   ソースから再レンダリングする** — この2ファイルは SessionStart フックが**インストール済み**プラグインから
   生成するため（[plugin-development.md](../rules/plugin-development.md)）、両ブランチとも v4.1.0 の内容を
   コミットしている。そのまま渡すと `develop` のスキルは**自分が実装していない規則**で採点される。
   再レンダリングは「このブランチがリリースされ、インストールされた状態」を再現する操作である

各 eval の `fixture` ブロック（`remove` / `strip_front_matter` / `copy_scenario` / `corpus: empty-project`）は
シナリオを作るための変形宣言。**4バリアント全てに同一の変形が適用される**ので、シナリオは再現可能。

### 2. バリアントは4つ、比較するのは「リフトの差」

| バリアント | コーパス | スキル |
|:---|:---|:---|
| `main/skill` | `main` の `.sdd/` | `main` の SKILL.md |
| `main/without` | `main` の `.sdd/` | ロードしない |
| `develop/skill` | `develop` の `.sdd/` | `develop` の SKILL.md |
| `develop/without` | `develop` の `.sdd/` | ロードしない |

`skill` と `without` は**同一のフィクスチャをバイト単位で共有する**。違いは SKILL.md をロードするかだけ。

```
lift(era)   = score(era/skill) − score(era/without)
改善量       = lift(develop) − lift(main)
```

**素点の `main/skill` vs `develop/skill` を直接比較してはならない。** `.sdd/` コーパスの中身自体が
ブランチ間で異なる（59ファイル、+1754/−626行）ため、素点差は「スキルが良くなった」のか
「`develop` のコーパスが充実した」のか分離できない。各世代の `without` がコーパスの難易度を吸収し、
それによって2つの lift が比較可能になる。

これは `ASSERTION_DESIGN.md` の「`main/without` と `develop/without` を直接比較してはならない」という
規則と矛盾しない。比較するのは lift であり、ベースライン素点そのものではない。

**限界**: リフト差はコーパス差を*近似的に*相殺するだけで、証明ではない。`without` が
コーパス差に対してスキルと同じ感度を持つという仮定に依存している。だから対照群を置く（次項）。

### 3. `analyze-requirements` は対照群

このスキルは `main` と `develop` で**1行も変わっていない**（+0/−0）。したがってリフト差は 0 付近に
出るはずである。ここで大きな差が出たら、それは測定ノイズの大きさであり、他スキルの数値を
そのまま信じてはならないという警告になる。**削除せず必ず一緒に走らせる。**

### 4. プロンプトは実ドキュメントの実パスに固定する

`.sdd/` には**両ブランチでバイト一致する26ファイル**があり、うち7機能は PRD → spec → design の
完全な三点セットが一致している（`distribution` / `constitution-injection` / `spec-review` /
`constitution-management` / `sdd-init` / `session-config` / `run-checklist`）。プロンプトの入力は
可能な限りこの一致集合に置く。各 eval の `input_parity` フィールドがその状態を記録している。

- `identical-on-both-branches` — 入力が完全同一。最も信頼できる
- 入力が異なる場合はその理由と、リフト差で吸収する旨を明記する（`check-spec` / `plan-refactor` /
  `constitution` / `vibe-detector`）
- `develop-only` — `main` に対応物が無い新機能（`render-adr-review`、`recommend-front-matter` の
  ADR eval）。**`main` の数値を報告してはならない**。`develop` 内のリフトだけを「新規能力」として報告する

### 5. assertion はバージョン中立に書く

判定基準と、初期設計（v1）で何を誤ったかは `ASSERTION_DESIGN.md` が正典。
**`evals.json` の assertion を書き換える際は必ず先にこれを読むこと。**

## 対象スキル（18件）

`main` → `develop` で変更のあった17スキル全部と、対照群1件。

| スキル | 差分 (+/−) | 備考 |
|:---|:---|:---|
| `plan-refactor` | +541/−296 | |
| `check-spec` | +427/−330 | 入力の実装コードがブランチ依存 |
| `render-adr-review` | +302/−0 | **新規スキル**。`develop` 専用 |
| `run-checklist` | +268/−16 | `scripts/run-verification.py` 追加 |
| `recommend-front-matter` | +196/−14 | eval 1 は `develop` 専用（ADRスキーマ） |
| `doc-consistency-checker` | +193/−78 | |
| `checklist` | +192/−179 | |
| `task-cleanup` | +114/−51 | |
| `generate-prd` | +79/−15 | |
| `generate-spec` | +75/−28 | |
| `sdd-init` | +68/−25 | |
| `vibe-detector` | +50/−3 | |
| `task-breakdown` | +49/−37 | |
| `finalize-prd` | +42/−8 | |
| `implement` | +41/−15 | |
| `clarify` | +38/−17 | |
| `constitution` | +29/−13 | |
| `analyze-requirements` | +0/−0 | **対照群**。差が出ないことが期待値 |

`generate-requirements-diagram` / `generate-usecase-diagram` は差分が無く、かつファイルを書かない
テキスト専用スキルなので v3 の対象外。

## v2 の資産

`build_fixtures*.py`（合成フィクスチャ生成）は削除せず残している。v3 では未使用だが、
`build_fixtures_hard.py` の「要求が互いに競合する高難度シナリオ」は実 `.sdd/` コーパスに存在しない
検査であり、再利用価値がある。
