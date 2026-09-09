# 計測ログ

v3 方法論（実 `.sdd/` コーパス、main→develop の改善量をリフト差で測る）の実測記録。
手法は [README.md](README.md)、assertion 設計は [ASSERTION_DESIGN.md](ASSERTION_DESIGN.md) が正典。

## iteration-1 パイロット（2026-09-05）

**目的**: 残り14スキルへ展開する前に、ハーネスがそもそも差を検出できるか・ノイズ床がどれくらいかを確認する。

**対象**: 4スキル × 2世代 × 2バリアント = 16ラン。すべて入力がバイト一致するものを選んだ。

| スキル | 差分 | 選定理由 |
|:---|---:|:---|
| `analyze-requirements` | +0/−0 | 対照群。ノイズ床の測定 |
| `run-checklist` | +268/−16 | `run-verification.py` の SKIPPED セマンティクス |
| `task-cleanup` | +114/−51 | 埋め込んだ検証可能な虚偽を看破するか |
| `doc-consistency-checker` | +193/−78 | PRD→spec→design 三点セットが完全一致 |

フィクスチャは `skill`/`without` が各世代内でバイト一致することを SHA で検証済み。世代整合も確認
（main: v5マーカー 0件・`adr/` なし / develop: 44件・`adr/` あり）。

各ランには以下を課した。フィクスチャ外の参照禁止（特に `.claude/skill-evals/` は採点基準そのもの）、
インストール済み `/sdd-workflow:*`（v4.1.0）の呼び出し禁止、規則書はフィクスチャ内の世代整合版を使用、
`SDD_*` 環境変数は未設定にして `.sdd-config.json` から解決させる。

### v3.0 assertion（初版）の結果

| skill | main/skill | main/without | main lift | develop/skill | develop/without | develop lift | 改善量 |
|:---|---:|---:|---:|---:|---:|---:|---:|
| `analyze-requirements` | 4/5 | 3/5 | +20pt | 4/5 | 3/5 | +20pt | ±0pt |
| `run-checklist` | 5/5 | 4/5 | +20pt | 5/5 | 3/5 | +40pt | +20pt |
| `doc-consistency-checker` | 5/5 | 5/5 | ±0pt | 5/5 | 5/5 | ±0pt | ±0pt |
| `task-cleanup` | 5/5 | 5/5 | ±0pt | 5/5 | 5/5 | ±0pt | ±0pt |

**識別力のある assertion: 3/20。** 17件が4セル全て同じ結果で、天井に張り付いていた。
`doc-consistency-checker` と `task-cleanup` は1件も差を検出しなかった。

原因は v3 方法論の構造そのもの。**実 `.sdd/` コーパスを使うと、コーパスが答えを持ってしまう。**
永続化先の規約（v4 は `*_design.md`、v5 は `adr/`）は CONSTITUTION と原則書に明記されており、
検査基準も `.claude/rules/` と原則書に十分書かれているため、`without` も正解を導出できる。
v2 の合成フィクスチャでは起きなかった現象である。

### v3.1 assertion（強化版）の結果

同じ16ランを、強化した assertion で**再採点**した（ランの成果物は保存済みなので再実行は不要。
assertion は測定器であり、同じデータをより鋭い測定器で測り直すのは妥当な操作）。
強化の根拠は2つに限定した — (a) main→develop の差分が実際に変えた振る舞い、(b) v3.0 で実測された失敗モード。

| skill | main/skill | main/without | main lift | develop/skill | develop/without | develop lift | 改善量 |
|:---|---:|---:|---:|---:|---:|---:|---:|
| `analyze-requirements` | 1/5 | 3/5 | **−40pt** | 1/5 | 2/5 | **−20pt** | +20pt |
| `run-checklist` | 4/5 | 3/5 | +20pt | 5/5 | 2/5 | +60pt | **+40pt** |
| `task-cleanup` | 3/5 | 3/5 | ±0pt | 5/5 | 5/5 | ±0pt | ±0pt |
| `doc-consistency-checker` | 5/5 | 1/5 | +80pt | 4/5 | 4/5 | ±0pt | **−80pt** |

**識別力のある assertion: 12/20**（v3.0 は 3/20）。assertion 側の問題は解消した。

### この数値を信じてはいけない

1. **ノイズ床が 20pt。** 差分0の対照群で改善量 +20pt が出た。`run-checklist` の +40pt はその2倍しかなく、
   1セル1ランでは有意と言えない
2. **`doc-consistency-checker` の −80pt は測定破綻。** develop で劣化したのではなく、`main/without` が
   1/5 という低スコアを引いて `main lift` が +80pt に跳ねた結果。同一世代・同一入力で `without` が
   1/5（main）と 4/5（develop）に分かれており、**`without` のばらつきがスキル効果より大きい**
3. **対照群の lift が両世代でマイナス。** 差分0のスキルで、スキルに従うと 1/5、従わないと 2〜3/5。
   偶然ではなく実在の欠陥（下記）

**結論: 1セル1ランでは改善量を測れない。** 残り14スキルを同条件で流しても解釈不能な数値が増えるだけ。

### 次のイテレーションの方針

採点をエージェント判断からスクリプト判定へ移す。ノイズ源は「ランのばらつき」と「採点者のばらつき」の
2つがあり、後者は機械化で消せる。機械化できる assertion の例:

- 引用した `file:line` と引用文が実ファイルと一致するか（`doc-consistency-checker` A2）
- 全 ID が `.sdd-config.json` の `id_conventions` に適合し一意・連番か（`analyze-requirements` A3）
- 属性が全要求に付与されているか（同 A4）
- 既存の手動チェック行がシナリオ原文のまま残っているか（`run-checklist` A4）
- 記録された数値が再実行と一致するか（同 A3）
- 永続ドキュメントにチケット識別子が残っているか（`task-cleanup` A4）
- 一時ログが削除され残骸が無いか（同 A2）

「人間の判断に委ねているか」のような assertion は機械化できないので、エージェント採点を残す。

## 実在欠陥（複数ランが独立に再現。計測とは別に確実な成果）

### 1. `analyze-requirements` の出力仕様が構造的に減点を生む（main/develop 両方）

差分 +0/−0 のスキルなので**両ブランチに存在する**。`skill` 側が `without` 側に負けた原因:

| 項目 | skill ラン | without ラン |
|:---|:---|:---|
| ID 正規表現の機械検証 | しない | main/without は Python で全件検証 |
| 入力の節ごとのカバレッジ表 | 作らない | main/without は作成 |
| UR の Verification 属性 | **テンプレートに列が無く欠落** | — |

- `references/output_format.md` の UR 表に Verification 列が無い
- `SKILL.md:85,90,97` と `references/output_format.md:10-28` が ID 形式を `UR-xxx`（ハイフン）と
  ハードコードしているが、`.sdd-config.json` の `id_conventions` は種別で書き分けている:
  PRD は `prd_user: ^UR_\d{3}$`（アンダースコア）、spec は `spec_functional: ^FR-\d{3}$`（ハイフン）。
  このスキルは PRD レベルの要求を出すので正しいのはアンダースコア側であり、実 PRD も全てそうなっている

### 2. `SDD_ADR_*` の仕様ドリフト（develop）

実装は `SDD_ADR_DIR` / `SDD_ADR_PATH` を export し（`session-start.py:211,215`）、
`hook_common.py:70` に `adr_dir = "adr"` の既定値を持つ。一方:

| 場所 | `adr` の言及 |
|:---|:---|
| `session-config_spec.md`（FR-003 が環境変数契約を定義） | 0件 |
| `session-config_design.md`（export 一覧を持つ） | 0件 |
| `.sdd-config.json` の `directories` | `requirement` / `specification` / `task` のみ |

v5 で `adr/` を導入した際、環境変数契約を定める仕様側への反映が漏れている。
`run-checklist` develop/without と `doc-consistency-checker` develop/skill の2ランが独立に検出。

### 3. `run-checklist` の改善方向（数値は弱いが挙動は明確）

`develop/skill` だけが、自動検証の対象外である理由を**ツール不在／手段未定義／権限外**の3種に書き分けた。
`develop/without` は人間レビュー項目 CHK-601/602 を「不合格」と誤判定し、CHK-103 の手動確認注記を
上書き消去した。`main/skill` は `allowed-tools` に `Bash` が無いのに Bash で shellcheck・plugin-lint を
直接実行し、素点上は「多く検証した」ことになっている。

develop の改善は「より多く検証する」ではなく「**検証していないものを検証したと言わない**」方向で一貫している。

### 4. 取り下げた指摘

main/skill ランが「`analyze-requirements/references/usecase_diagram_guide.md` が存在しない」と報告したが
**実在する**。mode `120000` の symlink（`shared/references/` へ）で両ブランチ同一 blob（`0eac176`）。
ランが `find -type f` で探して symlink を列挙できず不在と誤認した。スキルの欠陥ではなく
**ラン側の探索手法の差**であり、同一スキル・同一入力で生じたノイズの実例。

## ハーネスの既知の制約

### フィクスチャが git リポジトリでない

`build_sdd_fixture.py` は `git archive` でツリーを展開するため `.git` が無い。`task-cleanup` の SKILL.md が
指示する `git log`（一時ログの作成経緯の確認）と `git rm`（削除）が使えず、ランは mtime と `rm -r` で代替した。

**影響の向き**: 両世代・両バリアントに同一に効くためリフト差への偏りは小さいが、各セルの素点を一律に
押し下げ、ノイズを増やす。

**候補の対処**:

1. `git init` + 単一コミット — `git rm` / `git status` は動くが `git log` は1エントリだけ
2. `git clone --no-hardlinks -b <branch>` で実履歴ごと複製 — 最も忠実だが `.claude/skill-evals/`
   （採点基準）が履歴に残り `git show` で参照可能になる。現在の「除外」という強い保証から
   指示ベースの禁止へ後退することになる
3. 現状維持 + eval 側に「git 依存手順は代替手段で実施を許容」と明記

### コスト実測

| skill | main/skill | main/without | develop/skill | develop/without |
|:---|:---|:---|:---|:---|
| `analyze-requirements` | 82k/166s | 82k/307s | 84k/190s | 79k/250s |
| `run-checklist` | 86k/279s | 65k/273s | 78k/285s | 82k/326s |
| `task-cleanup` | 80k/250s | 73k/252s | 88k/292s | 70k/234s |
| `doc-consistency-checker` | 131k/576s | 132k/590s | 127k/454s | 125k/495s |

`doc-consistency-checker` が他の約1.6倍。スキルの有無でコストが変わらないため、これはタスク自体の重さ。

## v3.2: 採点の機械化（2026-09-05）

ノイズ源のうち**採点者由来のばらつき**を消すため、事実で決まる assertion をスクリプト判定
（[grade.py](grade.py)）へ移した。iteration-1 の16ランを実データとして8件の機械化を試み、
**4件だけが信頼できると判明した**。

### 採用した4件

| assertion | 検査 | 4セルの結果 |
|:---|:---|:---|
| `analyze-requirements` A3（ID が規約適合・一意・連番） | 表パース + 正規表現 | `[oooo]` |
| `analyze-requirements` A4（属性が全要求に付与） | 表パース | `[oxox]` |
| `task-cleanup` A2（一時ログ削除・ノイズ昇格なし） | パス存在 + 固有文字列 | `[oooo]` |
| `task-cleanup` A4（チケット追跡性） | grep | `[xxoo]` |

`task-cleanup` の2件はエージェント採点と**全4セルで一致**した。

### 差し戻した4件と、その理由

いずれも「機械化できると思ったが実データで壊れた」ケース。同じ失敗を繰り返さないために記録する。

| assertion | 差し戻した理由 |
|:---|:---|
| `run-checklist` A1（終了コードの記録） | 記録は項目 ID の近傍にあり同一行には無いため、テキスト窓での探索が必要になる。窓幅というチューニング定数で判定が変わるものは測定ではない |
| `run-checklist` A4（手動注記の保持） | 部分一致が PASS を返したランは、実際には**「旧記載の『手動確認済み（2026-09-03…）』は再現不能な根拠のため撤去し、実コマンド実行結果に置き換えた」**と書いていた。注記を引用しながら削除している。文字列の存在と記録の保持は別の命題であり、assertion が問うているのは後者。エージェント採点者はこれを正しく FAIL としていた |
| `doc-consistency-checker` A1（依頼範囲の遵守） / A2（引用の正確性） | ランは `path:line` 形式ではなく「`sdd-init_spec.md` の FR-005」「spec 174 行目」と書く。4件中3件が解析不能だった。自由記述用のパーサを作ってもノイズの置き場所が移るだけ |

### assertion 文面の修正

`analyze-requirements` A3 を「ID 適合を**確認した証跡があること**」から
「全 ID が `id_conventions` に**適合していること**」へ直した。証跡の有無はスクリプトで判定できず、
また文書品質として問われるべきは適合そのものである。「作業を見せろ」という要求は、
難易度を上げるために私が足したもので、測るべき対象ではなかった。

### 到達点と残課題

機械化のカバー率は **4/20**。採点者ノイズは部分的にしか消せていない。
`doc-consistency-checker` は識別力のある assertion を4件持つ一方、そのすべてがエージェント判断に
依存しており、iteration-1 で `without` が 1/5（main）と 4/5（develop）に分かれた最大の不安定要因が
残っている。

**残り14スキルへ展開する前に、以下のどちらかが必要:**

1. 各セルを複数ラン走らせて平均を取り、ノイズ床が 20pt を十分下回ることを対照群で確認する
2. `doc-consistency-checker` のように機械化できない assertion が支配的なスキルについては、
   改善量の定量化を諦め、実在欠陥の抽出に目的を絞る

現時点の推奨は 1。ただし対照群4セル×3ランで先にノイズ床を測り、下がらなければ 2 へ切り替える。

## 実在欠陥2件の修正（2026-09-06〜07）

iteration-1 が見つけた実在欠陥のうち2件を、`parallel-worktree` の並列エージェントループで修正・マージした。

| issue | PR | 内容 |
|:---|:---|:---|
| [#111](https://github.com/ToshikiImagawa/ai-sdd-workflow-dev/issues/111) | #114 | `analyze-requirements` が `id_conventions` を無視して ID 形式をハードコードしていた問題 |
| [#112](https://github.com/ToshikiImagawa/ai-sdd-workflow-dev/issues/112) | #113 | `SDD_ADR_DIR` / `SDD_ADR_PATH` の環境変数契約が session-config の spec / design に未反映だった問題 |

受け入れ基準は親セッションが実ファイルで全項目検証した（ループの自己申告では判定していない）。

- #111: `SKILL.md` のハイフン・ハードコード0件、`:46,73,98,103,110` で `prd_user` / `prd_functional` /
  `prd_nonfunctional` から解決、`output_format.md` の出力例0件、`:75` にフォールバック既定値
- #112: spec `FR-003:65` が `requirement・specification・adr・task` に更新、design `:141,145` に
  `SDD_ADR_DIR` / `SDD_ADR_PATH`、`.sdd-config.json` の `directories` に `adr` 追加、
  追加判断の理由が design `:207` に決定表として記録（代替案「既定値に委ねて明示しない」を併記の上、
  「他3ディレクトリは既定値と同値でも明示されているので表記方針の一貫性を優先」と選択理由を明記）
- CI: plugin-lint 2系統・validate-marketplace・pytest 333件・shellcheck すべて exit 0
- follow-up issue 0件（指摘は PR 内で完遂）、worktree / branch 削除済み、`phase=done`

### 副作用: 計測が自分の対照群を壊した

`analyze-requirements` は iteration-1 時点で差分 +0/−0 だったため対照群に使っていた。#111 の修正は
**develop 側だけ**に入るため、この差分は **+25/−12** になり、対照群として使えなくなった。

これは偶発事故ではなく、方法論に内在する緊張である。**計測が欠陥を見つけ、それを直すと、
差分0だったスキルが被験体に変わる。** 偶然変更されていないスキルに対照群を依存させる設計は、
成果を出すたびに壊れる。

残る差分0のスキルは `generate-requirements-diagram` / `generate-usecase-diagram` の2件だが、いずれも
`disallowed-tools` で `Write` / `Edit` / `Bash` を禁じたテキスト専用スキルであり、ファイルを書くスキルとは
タスク形状が違う。**別形状で測ったノイズ床は転用できない**ため、代替の対照群にはならない。

### 対処: 合成対照群

`build_sdd_fixture.py` に `--skill-from <ref>` を追加した。コーパスは世代固有のまま、
**スキルだけを指定 ref の版に差し替える**。両世代に同一の SKILL.md を与えれば、構成上リフト差は 0 で
なければならず、出た差はすべてノイズである。

```bash
python3 .claude/skill-evals/build_sdd_fixture.py main <outdir> \
  --eval .claude/skill-evals/<skill>/evals.json --skill-from develop
```

利点は2つ。**任意のスキルで対照セルを作れる**ので、測りたいスキルと同じタスク形状でノイズ床を測れる。
そして**将来また欠陥を直しても壊れない**。

動作確認済み: `main` のコーパス（v5マーカー0件）に `develop` の `analyze-requirements`
（`id_conventions` 参照5件）が入ることを確認した。

## 記録済み欠陥8件の解消確認（2026-09-07）

`ASSERTION_DESIGN.md` の `## 確認した実在欠陥` 表8件を、`develop` の実ファイルで1件ずつ検証した。
**8件すべて解消済み**。表自体は発見当時の記録として残してあるので、修正状況はここを見ること。

| # | 対象 | 解消の根拠（`develop` 実ファイル） |
|:---|:---|:---|
| 1 | `run-checklist` | `allowed-tools` に `Bash(python3 "${CLAUDE_PLUGIN_ROOT}/skills/run-checklist/scripts/run-verification.py" *)`。スクリプト実在 |
| 2 | `checklist` | SKILL.md 本文と `templates/ja` が P1〜P3 / `CHK-1xx` で一致 |
| 3 | `vibe-detector` | `:126-129` が意図的な除外と呼び出し元への委譲を明文化 |
| 4 | `recommend-front-matter` | `type_specific_fields.md:33` に ADR スキーマ |
| 5 | `naming.py` | `:100` に `if basename == "design-draft":` 分岐 |
| 6 | `constitution` | `:146` が `Add principle \| MINOR`。3箇所が一致 |
| 7 | `sdd-init` | `:66-67` が「事前に存在している前提。このコマンドが作ることはない」と明記し `:103` の Error と `init-structure.py:48-50` の exit 1 に一致 |
| 8 | `front_matter_reference.md` | `:76` の ADR status が常に `"approved"` と説明付きで統一 |

## 実在欠陥3件目の修正: PRD レベル ID 形式（2026-09-07）

記録済み8件の確認と並行して `develop` 全体を監査し、**PRD 生成の入口から出口、および検証側エージェント
まで一貫して ID 形式がハイフンにハードコードされている**欠陥クラスを見つけた。
[#115](https://github.com/ToshikiImagawa/ai-sdd-workflow-dev/issues/115) / PR #116 で修正・マージ済み。

真実の源は `.sdd-config.json` で、PRD はアンダースコア（`prd_*`）・spec はハイフン（`spec_*`）と
書き分けられており、実 PRD もアンダースコアのみ（ハイフン0件）。実害は3つ:

1. **同一 PRD 内で表と図の ID が食い違う** — Step 5 の表がハイフン、Step 6 の図がアンダースコア
   （Mermaid の制約）になり、要求表と要求図を ID で突き合わせられない。トレーサビリティは AI-SDD の
   中核価値なので、これが最も重い
2. **検証側が正しい PRD を不合格にしうる** — `prd-reviewer:184` と `spec-reviewer:192,210,211` が
   ハイフンを期待。`spec-reviewer` は明示的に「from PRD」と書いているので PRD レベル
3. `generate-prd` 自身の内部不整合 — `:135` は `id_conventions` を参照するのに `:170` は無視していた

受け入れ基準9項目は親セッションが実ファイルで全項目検証した。**変更してはいけない箇所**として
`requirements_diagram_components.md:180` の `❌ Invalid: id: FR-001` と Mermaid 構文規則2箇所を
受け入れ基準に含め、差分0で未変更を確認した（Mermaid は ID にハイフンを取れないので、
これらは現状が正しい。一括置換すれば壊れる）。

実装は指示より良い形になった。解決アルゴリズムを `shared/references/id_conventions_config.md` に集約し、
3スキルから symlink で参照する形にしたため、#111 で `analyze-requirements` に書いた5行も共通参照へ
統合された（内容の保全は差分で確認済み）。

### 監査で自分が出した誤検出

機械監査スクリプトが参照切れを19件検出したが、**すべてパス解決バグによる誤検出**だった（全ファイル実在）。
スクリプトの出力をそのまま報告せず実ファイルで確認したので誤情報の混入は防げたが、
**機械監査の結果は実ファイル確認を挟むまで報告しない**という手順は明文化しておく価値がある。

## develop への rebase と実行系の追従（2026-09-07）

ブランチを `develop` @ `8f258da` へ rebase した（コンフリクト0、`.claude/skill-evals/` の内容は
rebase 前と差分0行）。両方が同一ツリーに揃ったところで、**疑っていた統合上の欠陥が実測で確定した**。

`develop` に PR #110 で入った `.claude/skills/evaluate-skills/` は、この `skill-evals/` を
**入力仕様として読む実行系**だが、v2 手法に固定されていた。実際に v2 ビルダーを走らせて突き合わせると:

```
v2 の出力  → old/check-spec/.sdd/specification/notification-badge_spec.md（架空機能）
v3 の要求  → .sdd/specification/workflow-foundation/session-config_spec.md → 両世代に「なし」
```

**クラッシュせずに静かに壊れる**タイプだった。ランは即席の代替を探して出力し、グレーダーは採点し、
`benchmark.json` は正常な形で無効な数値を出す。計測ツールとして最悪の失敗の仕方なので、
方法論（入力仕様）と実行系は同一の変更単位として扱い、同じ PR で追従させた。

追従の過程で**自分が書いた記述の誤りを2つ、実行して見つけた**。`grade.py` の CLI を
`<skill> <eval-id> <dir>` と書いたが実際は `<dir> --skill <name>` で `--eval-id` は無く `evals[0]` 固定。
manifest を `fixture-manifest.json` と書いたが実際は `FIXTURE.md`。
**ドキュメントに書いたコマンドは1回走らせるまで信用しない。**

### `generate-requirements-diagram` の対象格上げ

rebase で `skill_delta_main_to_develop` を引き直したところ3件が陳腐化しており（#116 の影響）、
同時に `generate-requirements-diagram` が `+0/-0` → `+3/-3` になっていた。#116 が要求の抽出元の表記を
`UR-xxx entries from tables` → `UR entries from tables` に変えたためで、実 PRD の ID は
アンダースコアなので `main` 側の指示に従うと表から要求を拾えず図が欠落する。
つまり v2 時点で設計済みだった assertion 1「脱落なし」が、**差分が付いたことで初めて識別力を持った**。
assertion は新しく起こしていない。

ここから得た教訓: **「差分ゼロだから対象外」はその時点のスナップショットに過ぎない。**
`skill_delta_main_to_develop` は develop を取り込むたびに引き直す必要がある。

入力の選定で1つ落とし穴があった。実 PRD は要求図を節として持つため、そのまま渡すと `without` が
図をコピーするだけで識別力がゼロになる。`build_sdd_fixture.py` に `remove_section` を足して節だけを
外す形にしたが、**当初使おうとした `session-config.md` は `DC_003` / `FR_003` / `IR_001` が図の中にしか
定義されておらず**、節を外すと正しいランを「脱落」で減点してしまう。世代同一の10 PRD を全数調査し、
図内16件すべてが図外にも存在する `distribution.md` だけが条件を満たした。

## 新たに判明した計測の穴: `sdd-version` 陳腐化検出

`doc-consistency-checker/SKILL.md:138-145` に **Generation Staleness Detection**（文書の `sdd-version` の
major が `plugin.json` の version より古いものを列挙する）がある。`main` 側の `sdd-version` 言及は0件、
`develop` 側は6件なので、これは `develop` 専用の新規能力である。

ところが **`.sdd/` の85文書すべてに `sdd-version` が1件も存在しない**。したがって:

- この能力の正しい出力は両世代で「陳腐化0件」になり、**現在のコーパスでは測れない**
- 現行の assertion 5件はどれもこの能力を対象にしていないので、**dead assertion ではなくカバレッジの欠落**

`doc-consistency-checker` は差分 `+193/−78` で、かつ最大のノイズ源として名指ししているスキルなので、
その新規能力が計測外なのは穴として大きい。対処は可能で、`sdd-version: "3.0.0"` のような古い値を注入する
フィクスチャ変形を足せば、`main` は能力を持たず `develop` は検出するので `render-adr-review` と同じ形の
`develop` 専用 eval になる。`plugin.json` のバージョンバンプ保留とは独立に測れる（major 比較なので
プラグイン側が 4 のままでも `3.x` は陳腐化と判定される）。

## 残課題

| # | 内容 | 状態 |
|:---|:---|:---|
| 1 | ノイズ床 20pt の低減 | 未着手。**残り14スキルへ展開する前提条件**。次の一手は合成対照群で `doc-consistency-checker` のノイズ床を複数ラン計測すること |
| 2 | 採点の機械化 | 4/20 のまま。差し戻した4件の理由は `grade.py` の docstring にある |
| 3 | `sdd-version` 陳腐化検出の eval 追加 | 未着手。1 と同じタイミングで流すのが効率的 |
| 4 | `plugin.json` のバージョンバンプ判断 | ユーザー指示で保留中。ただし `shared/references/front_matter_*.md` が `sdd-version` の例に `"5.0.0"` と書いており、**ドキュメント側は既に v5 を前提にしている**不整合が実在する |

## `finalize-prd` 単独実行と実在欠陥の修正（2026-09-09）

`--skills finalize-prd` のみを対象にフルスイート評価（eval 0件のみ、1セル1ラン）を実行した。
結果は **main・develop 両世代とも without_skill と with_skill が完全同点（pass_rate 1.0 = 1.0、
zero_lift_full_pass）**。両era同時のこのパターンは iteration-1 時点の記録には無い新規ケース。

メタ評価が4仮説診断を行い、以下の実在欠陥3件を特定・修正した（PRへの反映は本コミット）。

1. **`detect_vacuous_baselines.py` / `diff_recurring_findings.py` の era ハードコード** -
   両スクリプトとも `for era in ("old", "new")` を直書きしており、v3 手法の現行命名
   （`main_skill`/`main_without`/`develop_skill`/`develop_without`）と一致せず、素朴実行では
   vacuous baseline を誤って0件と報告した（正しくは2件）。`eval_dir` 配下のディレクトリ名から
   `{prefix}_without`/`{prefix}_skill` のペアが揃っている `prefix` を動的に抽出する方式に修正し、
   修正後は手動補正なしで正しい2件が検出されることを確認した
2. **`finalize-prd/SKILL.md` Rule 7 が自身のPRDテンプレートと矛盾** - 新規UR/FR/NFR行の挿入先を
   「§4内の表の末尾」と記述していたが、`templates/{en,ja}/prd_template.md` の §4 は
   `### FR_001: {name}` のプローズ見出し形式でテーブルは無い。テンプレート実態に合わせて修正した
3. **`finalize-prd/SKILL.md` の仕様ギャップ2件**（4 run全てで独立に観測） - (a) 新規ユースケースの
   関係線（include/extend）の接続先選択基準が無い、(b) 入力側にあるが既存PRD構造に対応する欄が
   無い属性（Priority等）の扱いが未定義。両方にデフォルト方針を追加した

`.claude/skill-evals/finalize-prd/evals.json` の assertion 3・4 の文言も、実際のPRD構造
（プローズ形式）と食い違う「表」表記、および構造的判断と事実の捏造を区別できない曖昧さを修正した
（eval prompt 本文・脚注は変更していない — 変更するとprompt_leakageの診断結果自体が変わるため、
別途の再計測判断が必要と判断し今回は見送った）。

**測定上の注意**: 1セル1ランのみの実行であり、iteration-1のノイズ床(20pt)を踏まえると、この
zero_lift_full_passがノイズなのか構造的な問題なのかは本実行だけでは切り分けられない。上記の
skill改修が実際にリフトを生むかは、セルあたりのラン数を増やした再計測でのみ確認できる（未実施）。

