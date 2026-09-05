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
