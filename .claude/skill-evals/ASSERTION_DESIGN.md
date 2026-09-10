# スキル評価の設計方針（バージョン中立化）

## 背景：最初の評価設計の誤り

初回の3バリアント評価（new_skill / old_skill / without_skill）では、10スキル中8スキルで
`old_skill < without_skill`（旧スキルが「スキルを使わない」より低評価）となり、`old_skill > without_skill`
は0件だった。

これは「v4.x のスキルは元々スキル無しより劣っていた」ことを意味しない。原因は評価設計の2つの欠陥である。

### 欠陥1: assertion が v5.0.0 の実装詳細を見ていた

以下はすべて v5.0.0 で導入されたパス・フィールドであり、旧スキルには概念自体が存在しない。
これらを検証項目にすると、旧スキルは構造的に必ず不合格になる。

- `.sdd/task/{ticket}/design-draft.md` に設計ドラフトを置いたか
- `.sdd/adr/{feature}.md` に決定を統合したか
- front matter に `sdd-version` があるか

これは「新方式が優れているか」ではなく「新しい指示に従ったか」を測る循環的（tautological）な検証だった。

### 欠陥2: フィクスチャが v5.0.0 レイアウト固定だった

サンドボックスの `.sdd/` を新構成のみで作っていたため、旧スキルは自分が知らないパスを探して
**着手前に停止**した（`task-breakdown` / `implement` の old_skill が 0% になった直接原因）。
この状態ではどんな assertion に差し替えても旧スキルは 0% のままで、方法論の価値を測れない。

さらに、サンドボックスに現行（v5）の `CONSTITUTION.md` を丸ごと置いていたため、`adr/` 等の
新規約が without_skill にも漏れていた。

## 修正方針

### 1. 世代別フィクスチャ：各スキルを「自分の時代の世界」で評価する

| 世代 | レイアウト | `CONSTITUTION.md` | 比較対象 |
|:---|:---|:---|:---|
| **old (v4.x)** | `specification/{feature}_spec.md` + `specification/{feature}_design.md`（永続）、`task/{ticket}/` はタスクログのみ、`adr/` なし、`sdd-version` なし | commit `ce3fea3` 時点のもの（`*_design.md` 永続・`adr/` 概念なし） | `old_skill` vs `without_skill` |
| **new (v5.0.0)** | `specification/{feature}.md` + `task/{ticket}/design-draft.md`（一時）+ `adr/{feature}.md`、`sdd-version` あり | 現行のもの | `new_skill` vs `without_skill` |

`without_skill`（スキル無しのベースライン）は**両方のフィクスチャで各々計測する**。
これにより2つの独立した問いに答えられる。

- v4.x 時代の SDD は、スキル無しに勝っていたか？
- v5.0.0 の SDD は、スキル無しに勝っているか？

`CONSTITUTION.md` は必ず世代に一致させる。混ぜると他世代の規約が漏れ、
「スキルの有無」ではなく「フィクスチャに答えが書いてあるか」を測ってしまう。

### 2. assertion はバージョン中立な「本質」で書く

`.sdd/AI-SDD-PRINCIPLES.md` が定める AI-SDD の価値は、いずれもバージョンに依存しない。

| 原則 | 検証可能な形 |
|:---|:---|
| **Vibe Coding 防止** | 仕様欠落・曖昧な指示のとき、推測で進めずエスカレーションするか |
| **Specification-First** | 仕様を根拠に動くか（コード先行で後から文書化しない） |
| **トレーサビリティ** | 各成果物が要求 ID（UR/FR/NFR）に遡れるか |
| **設計判断の透明性** | 「なぜそうしたか」が残るか |
| **知識資産の永続化** | 陳腐化した重複履歴を残さず、最新の設計意図だけが残るか |
| **独立テスト可能な分解** | 各タスクに検証可能な完了条件があるか |

#### assertion を書くときの判定基準

**避ける（バージョン固有）**:

- 特定のパスにファイルを作ったか（`adr/` / `design-draft.md` / `*_design.md`）
- 特定の front matter フィールドがあるか（`sdd-version`）
- スキル本文に書かれた固有の語を使ったか（`--amend` モードの明示など）

**使う（バージョン中立・アウトカム基準）**:

- 決定とその根拠が、**どこであれ永続的な場所**に残っているか
- 一時ログが**重複した陳腐化履歴として残っていない**か
- 上流ドキュメントを検証せず書き換えていないか
- front matter の主張を鵜呑みにせず、**実態（コード・テスト）を確認**したか
- 仕様の範囲外の要求・タスクを**創作していない**か
- 人間が判断すべき事項を、独断で決めずに**提示**しているか

「決定が `adr/` に入ったか」ではなく「決定と根拠が永続的な場所に残り、一時ログは重複を残さず消えたか」と
書けば、`adr/` 世代でも `*_design.md` 世代でも同じ基準で採点できる。

## スキル別 assertion（バージョン中立版）

### generate-spec

1. 抽象仕様が要求レベルに留まっており、技術詳細（実装手段・データ構造）が仕様側に混入していない
2. 仕様の各機能要求が PRD の要求 ID に遡れ、PRD の範囲外の要求を創作していない
3. 抽象仕様と技術設計が別の成果物として分離されている（ファイル名は世代依存なので問わない）
4. 技術設計の内容が仕様と矛盾しない（API・振る舞いの齟齬なし）
5. 上流の PRD を検証なく書き換えていない

### check-spec

1. spec が `impl-status: implemented` と主張していても実コードを確認し、未実装の FR-003（`clear_badge`）を実在の欠落として検出する
2. FR-002（99+ 上限）の実装漏れを検出する
3. 仕様に無い `increment_unread` を「実装が仕様化されていない」側の指摘として分類し、誤検知として扱わない
4. 存在しない不整合を創作していない（偽陽性ゼロ）
5. 重大度がラベルの存在だけでなく相対的な影響度に応じて割り付けられている（検出された全ての指摘が無差別に同一重大度になる、またはテンプレートの機械的コピーで満たせない）

### implement

1. 仕様・設計が定めた範囲を超える機能を実装していない（スコープクリープなし）
2. テストが書かれ、実行して実際に pass する
3. 仕様の各 FR を実装が満たしている
4. 実装状況がドキュメント側に反映され、仕様とコードの乖離が放置されていない（手段は世代依存なので問わない）
5. テストを実装と同時／先行で書いたという主張が、具体的な作業順序の記述（どのファイルをどの順で作成・変更
   したか）を伴う証拠で示されている（時系列の自己申告のみでは不十分。ナラティブな要約だけで「先に書いた」
   と述べているだけの場合はFAILとする）

> **assertion 強化の経緯（2026-09-08）**: 旧5件は old/new × skill/without の4条件全てで pass_rate=1.0
> となり、かつ skill 使用時のtool_calls数が最大3.4倍（実装スキル中最大）に増えるにもかかわらず品質差が
> 測れていなかった。加えて全4runのgraderが「テスト先行という主張がtranscriptのナラティブ要約のみに依存
> しており、実際のツール呼び出し順序を独立に検証できない」と繰り返し指摘した。真の機械的検証（gitコミット
> 単位の記録等）はharness側の大改修が必要なため見送り、assertion文言を「具体的な証拠が無ければFAIL」に
> 強化するだけにとどめた。tool_calls増加自体は、SKILL.mdの「Implementation Options」節が通常使わない
> 3つの代替モード（Continue/Phase Skip/Dry Run）の例示を無条件に読ませていたことが主因と判明したため、
> 該当モードが指示された場合のみ読む条件付き記述に修正した。

### generate-prd

1. 既存の要求が変更されずに保持されている（非破壊的追記）
2. 新規要求の ID が既存の連番を正しく継続している（衝突・欠番なし）
3. 新規要求の属性（Priority / Risk / Verification）が、既存要求で実際に使われている値の語彙・粒度から逸脱せずに付与されている（独自の値・表記を新規要求にだけ導入していない）
4. 新規 FR が UR に遡れる（トレーサビリティ維持）
5. 全体再生成ではなく追記操作として実施されており、既存記述が失われていない
6. 新規追記が既存の他セクション（Out of Scope、Constraints等）と論理的に矛盾する場合、その矛盾が黙って
   見過ごされていない（矛盾を検出した上で報告し人間の判断に委ねている、または適切な確認を伴って解消している
   場合はPASS。検出されず矛盾が未報告のまま残っている場合はFAIL）

> **assertion 追加の経緯（2026-09-08）**: 旧5件は old/new × skill/without の4条件全てで pass_rate=1.0
> となり、skill使用の価値を判別できていなかった。実際には `old_skill`/`new_skill` 両方が、fixture の
> 既存「Out of Scope」節（「未読数のバッジ表示は対象外」）と直接矛盾する新規 FR_002（「未読メッセージ数を
> バッジとして表示する」）を生成し、両run共にこの矛盾を自覚して `user_notes.md` に記録していたにも
> かかわらず、旧5件のいずれにも引っかからなかった。fixture 自体は矛盾が十分明確なため変更せず、
> 6番目のassertionを追加して既存の見逃しを検出できるようにした。
>
> **assertion 6 言い換えの経緯（2026-09-08 再検証）**: 追加直後の文言（「矛盾していない」を単純に要求）を
> 実際に4条件で再評価したところ、`old_skill`/`new_skill` の両方でFAILし、`old_without`/`new_without`は
> PASSした。しかし内容を精査すると、skill runは矛盾を検出した上で「PRDは人間の意思決定の記録であり
> AIが自動修正すべきでない」という設計原則に従い、既存のOut of Scope文言を意図的に書き換えなかった。
> 一方withoutは、頼まれていないのに既存文言を勝手に編集して矛盾を解消し、結果的にPASSした。つまり旧文言は
> 「検出して人間に委ねる」という正しく安全な振る舞いを、「最終文書に矛盾が残っている」という理由だけで
> 不合格にしてしまうassertion設計の欠陥だった。「矛盾を検出して報告したか」を主軸に据え、検出済みなら
> PASSする形に言い換えて解消した。

### finalize-prd

1. 既存記述がバイト単位で保持されている
2. 新規 UR/FR が構造的に正しい位置（該当セクション・表）に挿入されている
3. 要求図と詳細表の**両方**が整合的に更新されている（片方だけの更新になっていない）
4. 与えられた情報を超える内容を創作していない

### analyze-requirements

1. 提示された全ての振る舞いが、少なくとも1つの FR でカバーされている
2. 全ての FR が少なくとも1つの UR に遡れる（derives 関係）
3. ID が一意かつ連番
4. Priority / Risk / Verification が一貫して付与されている
5. 提示されたユースケースの範囲外の要求を創作していない

> **fixture 注記（2026-09-07 追記）**: 当初のfixtureは `files: []` で実在するユースケース入力が
> 一切無く、4条件（old/new × skill/without）全てで実行者が「提示された」ユースケース自体を
> 自作せざるを得ない状態だった。これにより assertion 5 が「自作した前提と自作した要求の自己整合性」
> に縮退し、graderの判定がブレていた（4条件中3条件がFAIL、1条件のみ運良くPASS）。
> `build_fixtures.py` に `usecases` フィクスチャ（UR/FR/NFRを含まない、Actor/Use Case表のみの
> `.sdd/requirement/notification.md`, `status: "draft"`）を追加し、実在する入力から検証できるようにした。

### task-breakdown

1. 各タスクが仕様・設計の要求 ID に遡れる
2. 各タスクに独立して検証可能な完了条件がある
3. タスクの順序が依存関係を尊重している
4. テストが暗黙ではなく明示的なタスクとして含まれている
5. 仕様の範囲外のタスクを創作していない
6. 各タスクの front matter（id 命名規則・type・depends-on の向き・status 等）が、その世代の
   既存タスク文書が実際に使っている規約に沿っている

> **assertion 追加の経緯（2026-09-07）**: 旧5件は old/new × skill/without の4条件全てで
> pass_rate=1.0 となり、graderが4条件全てで独立に「front matter規則・タスク粒度原則・
> allowed-tools整合性等、スキル固有の手順に従っているかを検証するassertionが無い」と指摘していた。
> 旧5件は「良い上級エンジニアなら自然にやること」の範囲に留まり、スキルを読んだことの価値を
> 判別できていなかったため、6番目を追加した。

> **SKILL.md 修正の経緯（2026-09-08）**: `old_skill` run が6件全てFAILしていた原因は、fixture の
> 非対称ではなく **`plugins/sdd-workflow/skills/task-breakdown/SKILL.md` 自身の old 世代対応の欠落**
> だった。old 世代のプロジェクトには `task/{ticket}/design-draft.md` という task スコープの設計ドラフト
> という概念自体が無く、設計は `specification/{feature}_design.md` に永続化される旧レイアウトを使う。
> SKILL.md 本文は `design-draft.md` を固定パス必須としており、old 世代向けのフォールバックが本文に
> 一切無かったため、`old_skill` run は必須条件を満たせず着手前に停止していた。`task-cleanup` が既に持つ
> 「`adr` が無ければ永続 design doc の `ticket` フィールドを使う」という old/new 両対応のフォールバック
> 文体を手本に、「1. Load Related Documents」に `design-draft.md` が無い場合の
> `specification/{feature-name}_design.md` へのフォールバックを追記した。

### task-cleanup

1. 設計判断とその**根拠（なぜ）**が、一時ログの削除で失われず永続的な場所に保存されている
2. 一時ログが重複した陳腐化履歴として残っていない（知識資産の永続化）
3. 上流ドキュメントの更新要否を、主張ではなく実態（コード・テスト）を確認して判断している
4. 進捗メモ・実装詳細のような**ノイズを永続ドキュメントに昇格させていない**（決定のみを残す）
5. チケットの完了が記録され、黙って破棄されていない

> **SKILL.md 修正の経緯（2026-09-07）**: old_skill run がassertion 5でFAILしていた原因は、
> old世代のプロジェクトには `adr/` という概念自体が無く、SKILL.mdが定めるチケット完了記録の
> フォールバック（`adr` エントリの `ticket` フィールド）が old 世代では構造的に使えない状態だった
> こと。GitHub issueへの実投稿は本物のリポジトリへの副作用リスクがあるため安全側でスキップするのが
> 正しい判断であり、fixtureの不備ではなく **`plugins/sdd-workflow/skills/task-cleanup/SKILL.md`
> 自身のold世代向けフォールバック手段の欠落**だった。Step 7 に「`adr` エントリが無ければ、
> 永続的な設計文書（例: 旧世代の `*_design.md`）の `ticket` フィールドに記録する」という代替手段を
> 追記し、`front_matter_reference.md` / `front_matter_spec_design.md` の Design 型フィールド定義に
> `ticket`（optional）を追加した（新規文書作成時にこの命名を使うことを推奨するものではなく、
> すでに存在する永続文書を見つけた場合の記録先として使う）。

### plan-refactor

1. この変更が後方互換性を壊すことを明示的に指摘している
2. 影響を受ける呼び出し元・テストの影響分析を提示している
3. 後方互換性について、少なくとも1つの具体的な代替アプローチ（例: 移行期間を設けたdeprecation、新旧シム
   関数の並存提供、即時breaking change）を比較提示し、かつ実装への反映は行わずレビュー可能な状態で人間の
   判断に委ねている（どちらか一方だけでは不十分）
4. 決定とその根拠が永続的に記録される想定になっている
5. 計画の根拠を仕様の**内容**に置いている（特定ファイルの有無に依存していない）

> **prompt 修正の経緯（2026-09-07）**: 旧prompt文の「既存の呼び出し元は int を期待しています」が
> assertion 1 の答えをほぼそのまま与えていた（old_withoutのgrader自身が「依頼文の言い換えだけでも
> 表面的に満たせてしまう」と明記）。fixtureの `tests/test_notification_badge.py` は元々 int 型の
> 戻り値を期待するテストを含むため、この一文を削除しても実行者は実コード・テストを読めば同じ事実に
> 到達できる。prompt からこの一文を削除した。

> **assertion 3 言い換えの経緯（2026-09-08）**: 旧文言「後方互換性の方針を独断で決めず、人間の判断材料
> として提示している」は、4 run全てのgraderが独立に同じ論点（「複数の代替案を比較提示すること」と
> 「実行せずレビューゲートを残すこと」のどちらを求めているか曖昧）を指摘していた。実際にold_withoutのみ
> 具体的な代替案（別名関数の新設、Union型のまま正規化、TypedDict化）を比較提示し、old_skill/new_skillは
> 代替案を一切提示せず「レビュー承認待ち」という実行タイミングの保留のみで済ませていたが、旧文言では
> いずれも同じくPASSしてしまっていた。比較提示とレビューゲートの両方を明示的なAND条件にして解消した。
> なお `scripts/find-implementation-files.py` がfeature-name（ハイフン区切り）とソースコードの
> モジュール名（アンダースコア区切り）の表記差で0件を返す実バグも同時に修正した（fixture固有ではなく
> 一般的な欠陥）。

### doc-consistency-checker

1. spec の FR-003（clear_badge）が PRD 側の対応する上流 FR（バッジ数表示/上限関連。ID表記はプロジェクトの
   id_conventions 次第）を引用しているが、その上流 FR の記述内容にはバッジのクリアに関する言及が一切無い
   という、記述内容に基づく実在のトレーサビリティ上の疑義を検出する
2. spec の制約節（99件超で"99+"）と、決定ログの後日エントリ（101件以上に変更）の間の実在の矛盾を検出する
3. 指摘が実在し正確である（創作していない）
4. 人間が優先度判断できるよう、指摘が重大度で分類されている
5. 下流から PRD を自動書き換えする提案をしていない

> **fixture 修正の経緯（2026-09-07）**: 当初のfixtureは「specのPublic APIが `increment_unread` を
> 欠く」「決定ログの型注釈がコードと矛盾する」という2件の意図的欠陥を仕込んでいたが、**両方とも
> spec-vs-実装コードの不整合**であり、doc-consistency-checkerのSKILL.md自身が明記するスコープ
> （PRD↔spec↔adr。spec-vs-コードはcheck-specの担当）の外側だった。忠実にスコープを守る実行
> （コードを見ない）が正しい振る舞いであるにもかかわらず、コード比較まで行った実行だけが
> 「欠陥を発見した」ように見え、評価が逆転していた。`DECISION_LOG_BODY`（plan-refactorと共有）を
> コード比較不要のspec-vs-decision-log矛盾（99+→101+のしきい値変更）に書き換え、spec自身の
> トレーサビリティ主張の疑義（FR-003→FR_002）と合わせて、PRD/spec/adrスコープ内だけで検出可能な
> 2件の欠陥に置き換えた。plan-refactorはdecision-logの具体的内容に依存しないため影響を受けない。

### checklist

1. チェックリスト項目が仕様・設計・タスク分解から**抽出**されており、創作されていない
2. 各項目にカテゴリと優先度が付与され、人間が着手順を判断できる
3. 設計ドラフトが存在しない場合でも処理を止めず、抽象仕様の範囲でレビュー項目を限定して生成している（v5.0.0固有パスの有無に依存しない）
4. PRD/仕様の要求ID（該当する場合）にチェックリスト項目が遡れる
5. 既存チェックリストの更新時、完了済みマークを保持したまま新規項目のみ追加している（`--update`実行時）

### clarify

1. 提示された仕様の曖昧点（欠落条件・未定義の境界値等）を実在するものとして検出している
2. 検出した曖昧点に対する質問が、実装判断に直結する具体性を持っている（一般論ではない）
3. 明確な項目まで曖昧と誤検知していない（偽陽性がない）
4. 質問がスペックの記述内容に基づいており、仕様に無い前提を勝手に創作していない
5. PRD（`requirement/**`）を編集対象にせず、`*_spec.md`または設計ドラフトのみを対象にしている

### run-checklist

1. チェックリストの各項目に対し、実際に検証コマンドを実行した結果（またはツール不足によるSKIPPEDの明示）を記録している——実行せず主観で合否を決めていない
2. 自動検証できない項目を「手動確認が必要」として区別し、自動検証結果と混同していない
3. 検証失敗時に失敗の詳細（何がどう失敗したか）を記録し、単に不合格マークを付けるだけで終わっていない
4. 既存チェックリストの手動チェック済み項目を上書き・消去していない
5. 検証結果がチェックリスト元の仕様・設計と矛盾する場合、その矛盾を報告している

### vibe-detector

1. 提示されたユーザー指示中の曖昧表現（主観的形容・不明瞭な範囲・暗黙の前提等）を実在するものとして検出している
2. リスクレベル（High/Medium/Low）の判定根拠が、仕様の有無とユーザー指示の具体性という提示された条件と整合している
3. 明確な指示を曖昧と誤検知していない（偽陽性がない）
4. ユーザーが明確化を拒否した場合の代替手段（推定仕様の記録・検証ポイントの明示）を提案している——警告するだけで終わっていない
5. 実装を強制的にブロックせず、最終判断をユーザーに委ねている（検出は警告であり強制ではない）

### constitution

1. `init`実行時、既存のCONSTITUTION.md（またはその世代の原則ドキュメント）を無条件に上書きしていない
2. 追加・変更した原則が、その世代の原則ドキュメントの構造（章立て・表形式）を保っている
3. バージョン変更（major/minor/patch）が、原則の追加・変更・削除という変更の性質と整合している
4. `validate`実行時、指摘が実際のspec/design文書の記述内容に基づいており、原則名を機械的に貼り付けただけの形式チェックになっていない
5. 原則の変更履歴が追記され、過去の記述が失われていない

### sdd-init

`sdd-init` は文書を書き換えるのではなく、プロジェクトへ AI-SDD の構造を導入するスキル。判断の大半が
`init-structure.py` / `update-claude-md.py` という決定的スクリプトに委譲されているため、assertion は
「スクリプトを正しく起動できたか」ではなく「導入後に Vibe Coding 防止の仕組みが機能する状態になっているか」
を問う。

1. 導入後、要求（PRD）・仕様・設計判断のいずれかを記録する場所が最低1つ存在し、その世代の CONSTITUTION が
   参照可能になっている（Specification-First の土台が整う）
2. 既存の `.sdd/` 配下のファイル（旧世代のドキュメントを含む）を上書き・破壊していない
3. `CLAUDE.md` への追記が既存の記述を保持したまま行われている（全体書き換えではない）
4. プロジェクト固有のディレクトリ命名・言語設定（`.sdd-config.json` 相当の設定）を尊重し、決め打ちの
   パスを強制していない

### recommend-front-matter

1. front matter が無い文書を検出し、**その世代のスキーマ**（old: PRD/spec/design/task、new: 上記+adr）に
   沿った推奨を提示している
2. 推奨内容が既存の記述内容（タイトル・依存関係）から矛盾なく推論されている（架空の ID を作らない）
3. `--apply` 相当の適用を行う場合、ユーザー確認なしに既存文書の値を書き換えていない（追加のみ）
4. 既存の front matter フィールドの**値**（例: 古い `status`）を上書き提案していない（欠落フィールドの
   補完のみ）

### generate-requirements-diagram / generate-usecase-diagram

この2スキルは `Write`/`Edit`/`Bash` が `disallowed-tools` で禁止されたテキスト専用スキルであり、
ファイルを書き換えない。そのため new/old 世代間の期待値の違いは小さく、比較の主眼は
skill-vs-without（図の正確性・網羅性）に置く。

1. 入力に含まれる要求・アクター・ユースケースが図に漏れなく反映されている（脱落なし）
2. 図の要素間の関係（`derives`/`contains`/`satisfies` や `include`/`extend`）が入力の記述と矛盾しない
3. 入力に無いアクター・要求を創作していない
4. 出力がファイル書き込みではなくテキストとして返され、呼び出し元（`generate-prd` 等）に判断を委ねている

## 確認した欠陥（残り9スキル、履歴）

当初はfork実行制約（サブエージェント再委任不可）により静的解析のみで欠陥候補を洗い出したが、その後
オーケストレーター（メインセッション）が直接、9スキル×2世代×2variant=36回のエージェント実行と9件の
独立採点を実施し、静的解析の主張を実ファイル・実行結果・git履歴で裏取りした（#1は当初「v5.0.0化に伴う退行」
としていたが、実際には`ce3fea3`（本プロジェクトのold世代基準コミット）より前の別コミットで既に失われており、
古い世代のフィクスチャにも欠陥が混入している点を修正済み）。

**2026-09-08 追記**: 以下 #1〜#8 は、課題3の事実確認（Explore agent 3体による現行コードとの対比）で
`3b380cf`（PR #108「スキル評価で見つかった自己矛盾・欠落を修正する」、2026-09-04）により**既に解消済み**と
判明した。表自体を更新せず古い状態を記録し続けていたため、過去の検出記録として残すが現行コードには対応しない。

| # | スキル | 欠陥 | 根拠 |
|:---|:---|:---|:---|
| 1 | `run-checklist` | `allowed-tools`に`Bash`が無く、スキルの核心機能（テスト・リンタ・セキュリティスキャナの実行）が実行不能。SKILL.md:3「Runs tests, linters, security scanners」、Section 3「Execute Automated Verifications」と矛盾する。2026-07-28のコミット`7e3e6c0`で`Read, Write, Edit, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList, TaskGet` → `Read, Glob, Grep, Edit(.sdd/**), TaskCreate, TaskUpdate, TaskList, TaskGet`に絞られた際の退行だが、このコミットは本プロジェクトの「old世代」基準コミット`ce3fea3`（2026-08-19）より前のため、old/new両方の実行で同一の欠陥が再現した（4実行中4実行がBash不可を報告し、静的解析で代替）。加えて`Write`も無いため、SKILL.mdが要求する新規ファイル`verification_report.md`の作成もEdit(.sdd/**)だけでは不可能（2実行が実際にこの壁にぶつかった）。**解消済み（`3b380cf`, PR #108, 2026-09-04）**: `allowed-tools`にスコープ付き`Bash(python3 .../run-verification.py *)`が追加され、本文もスコープ内実行に限定する旨を明示 | `plugins/sdd-workflow/skills/run-checklist/SKILL.md:9`、`git log --follow -p`、実行ログ4件 |
| 2 | `checklist` | SKILL.md本文のProcessing Flow（P1/P2/P3の3段階、9カテゴリ、`CHK-{category}{nn}`形式）と、同スキルが自ら参照する`templates/ja/checklist_template.md`（P0〜P3の4段階、10カテゴリ、`CHK001`通し番号）が矛盾している。Export Formats節の「P0項目をGitHub Issue化する」という記述はテンプレート側のP0に基づくものだが、SKILL.md本文はP0を定義していない自己矛盾。old/new両世代、独立した2回の実行（`old/skill`・`new/skill`）が同一の矛盾を発見し、いずれもSKILL.md本文側を優先する同じ判断を下した。加えて`gh issue create`の実行には`Bash`が必要だが`allowed-tools`に無い。**解消済み（`3b380cf`, PR #108, 2026-09-04）**: テンプレートを本文の正準形式（P1-P3・9カテゴリ・`CHK-{category}{nn}`）に統一 | `plugins/sdd-workflow/skills/checklist/SKILL.md:170-184`（本文の定義）と`templates/ja/checklist_template.md`（矛盾するテンプレート）、`SKILL.md:214`（P0への言及）、`SKILL.md:8`（allowed-tools）、実行ログ2件（`old/skill`, `new/skill`） |
| 3 | `vibe-detector` | `disallowed-tools: Write, Edit, Bash`により、本文の「Escalation When Specifications Are Insufficient」節が指示する`task/{ticket}/assumed-spec.md`への推定仕様書き込みが実行不能。old/new両世代の実行が同一の権限矛盾を報告し、書き込むはずだった内容をテキストで代替提示することで対応した。**解消済み（`3b380cf`, PR #108, 2026-09-04）**: 本文が「このスキル自身は書き込まず、呼び出し元セッションが保存する」設計を明示的に説明する記述に修正 | `plugins/sdd-workflow/skills/vibe-detector/SKILL.md:7-8`（front matter）と`SKILL.md:115-126`（Escalation節）、実行ログ2件 |
| 4 | `recommend-front-matter` | `scripts/scan-documents.py`が使う`naming.determine_type`は`adr/`配下も走査・分類するが、SKILL.mdのPrerequisitesと`templates/{lang}/type_specific_fields.md`にADRのスキーマ定義が無い。old/new両世代の`skill`実行が独立にこのギャップを発見し、正しいスキーマ源（`shared/references/front_matter_reference.md`）を自力で探索して代替した一方、`without`実行（スキル無し）は世代を問わずADR推奨で`sdd-phase`等を欠落させた（4実行中2実行が同一assertionで失点、原因も一致）。**解消済み（`3b380cf`, PR #108, 2026-09-04）**: `references/front_matter_adr.md`を新設し、両言語の`type_specific_fields.md`にもADR行を追加 | `plugins/sdd-workflow/skills/recommend-front-matter/SKILL.md:19-23`、`templates/en/type_specific_fields.md`（ADR行なし）、正しい参照例: `plugins/sdd-workflow/agents/front-matter-reviewer.md:40`、実行ログ4件 |
| 5 | `naming.py::determine_type()`（共有モジュール） | `task/{ticket}/`配下のファイルは`implementation_log`/`impl_log`という名前パターンのみ`"implementation-log"`と判定し、それ以外は無条件に`"task"`と分類する。`design-draft.md`という新世代の設計ドラフト（`front_matter_reference.md`が定義する正規の配置場所）を特別扱いする分岐が無いため、`type: "design"`であるべき文書が`type: "task"`に誤分類される。`recommend-front-matter`の`new/skill`実行がこの誤分類を実地で発見し、`<!-- id候補: design-101 -->`というファイル内のヒントを根拠に`type: "design"`へ手動補正して切り抜けた。`determine_type`の唯一の呼び出し元は`scan-documents.py`のみ（docstringが挙げる`doc_walker`/`check-spec`は現状未使用）だが、影響範囲は今後この関数を再利用するツールにも及ぶ。**解消済み（`3b380cf`, PR #108, 2026-09-04）**: `design-draft`分岐を追加し`type: "design"`を返すよう修正、回帰テストも追加 | `plugins/sdd-workflow/scripts/naming.py:91-101`（`determine_type`本体、design-draft分岐なし）、対比: `plugins/sdd-workflow/shared/references/front_matter_reference.md:57`（design型の正規配置） |
| 6 | `constitution` | SKILL.md内で原則追加時のバージョンバンプ規則が矛盾している。「2. Add Principle (add)」節（122行目）と巻末のセマンティックバージョニング表（236行目）はいずれも「原則追加 → Minor」とするが、「4. Update Constitution (update)」節の「Version Bump Rules」表（146行目）は同じ「Add principle」を「MAJOR」と定義している。4実行全てが同じ矛盾を認識した上でMinorを採用し（`add`サブコマンドの手順を優先）、一貫した判断を下したためgrading上は減点していないが、SKILL.md自体の記述矛盾は解消が必要。**解消済み（`3b380cf`, PR #108, 2026-09-04）**: 3箇所とも「原則追加=MINOR」に統一し、2表を行単位で一致させる旨を明記 | `plugins/sdd-workflow/skills/constitution/SKILL.md:122`, `:146`, `:236` |
| 7 | `sdd-init` | SKILL.md自体が`.sdd-config.json`不在時の挙動について自己矛盾している。「Configuration File Management」節（66-70行目）は「スクリプトが自動的に...存在しなければデフォルト設定で作成する」と説明するが、その直後の「Execution Flow」節（100-102行目）は同じスクリプトについて「存在しなければError（事前作成かsession-startフックが必要）」と正反対の説明をしている。実装（`init-structure.py:47-50`）は後者と一致し、`.sdd-config.json`が無いと`ERROR: .sdd-config.json not found`でexit 1する（フォールバック実装なし）。old/new両世代の`skill`実行が独立にこの矛盾に遭遇し、手動で`.sdd-config.json`を作成してから再実行することで切り抜けた。`old/skill`実行はこの後の後始末（`.sdd/AI-SDD-PRINCIPLES.md`等、CLAUDE.mdが参照するファイルの生成）を「SessionStartフックの責務」として意図的にスキップし壊れた参照を残したのに対し、`new/skill`実行は`session-start.py`を手動実行して補完した——同じ欠陥への対応の質が実行ごとにばらついた点も、SKILL.mdのharness外運用時の手順が明文化されていないことの表れ。**解消済み（`3b380cf`, PR #108, 2026-09-04）**: 「自動生成する」という記述を削除し「Errorになる」に統一、実装と一致 | `plugins/sdd-workflow/skills/sdd-init/SKILL.md:66-70`（自動生成すると記述）vs`:100-102`（Errorすると記述）、`scripts/init-structure.py:47-50`（実装はError側と一致）、実行ログ2件（`old/skill`, `new/skill`） |
| 8 | `front_matter_reference.md`（共有リファレンス） | ADR（`type: "adr"`）の`status`フィールド定義表（76行目）は`draft, review, approved, deprecated`を有効値として列挙するが、直後の「Status Transition Rules」節のADRの項（189-193行目）は「ADR entries are append-only and do not follow the draft/review/approved lifecycle」と明記しており、同一ドキュメント内で自己矛盾している。**解消済み（`3b380cf`, PR #108, 2026-09-04）**: `status`列を単一固定値`"approved"`に絞り、Transition Rules節の記述と一致させた | `plugins/sdd-workflow/shared/references/front_matter_reference.md:76`, `:189-193` |
| 9 | `find-spec-docs.py` / `prepare-prd.py` / `prepare-spec.py`（check-spec / generate-prd / generate-spec の共有スクリプトパターン、修正済み） | 3スクリプトが独立に同じ `read_config()` を持ち、`.sdd-config.json` が無いと `sys.exit(1)` でハード停止していた。一方 `shared/references/prerequisites_directory_paths.md` の「Path Resolution Priority」は「環境変数 → `.sdd-config.json` → デフォルト値」の3段階フォールバックを明記しており矛盾。2026-09-08 の評価で3スキル全ての `_skill` run が独立にこの壁にぶつかった（`meta_analysis.json` の `skill_improvements[0]`）。find-spec-docs.py は既に `hook_common.load_sdd_paths()`（config無しならデフォルト）を呼んでいたが、その手前の独自ゲートがフォールバックを潰していた。prepare-prd.py/prepare-spec.py は `sdd-init/scripts/update-claude-md.py` にあった正しい実装 `resolve_lang_and_root()` を `hook_common.py` に共有化し、3ヶ所目の再実装を避けて解決した | `plugins/sdd-workflow/skills/check-spec/scripts/find-spec-docs.py`（旧37-40行目）、`plugins/sdd-workflow/skills/generate-prd/scripts/prepare-prd.py`（旧32-35行目）、`plugins/sdd-workflow/skills/generate-spec/scripts/prepare-spec.py`（旧32-35行目）、`plugins/sdd-workflow/scripts/hook_common.py`（`resolve_lang_and_root`追加先） |

## 削除した assertion とその理由

| 削除した assertion | 理由 |
|:---|:---|
| `front matter に sdd-version があるか` | v5.0.0 固有フィールド。旧世代には概念がなく、新世代でも出力テンプレート次第で運が絡む |
| `adr/{feature}.md に統合したか` | v5.0.0 固有パス。「決定と根拠が永続化されたか」に一般化 |
| `task/{ticket}/design-draft.md を設計ソースとして使ったか` | v5.0.0 固有パス。世代別フィクスチャで各自の正しいパスを使えるようにして解消 |
| `明示的な --amend 概念が存在し従ったか` | スキル本文の語彙依存。「非破壊的な追記になっているか」に一般化 |
| `spec の陳腐化した sdd-version を検出したか` | v5.0.0 固有。代わりに世代非依存の実在不整合（spec の Public API に `increment_unread` が無い、設計記録内の型注釈がコードと矛盾）を検出対象に据える |
| `(old_skill) 設計書が無くブロックされるか` | 「悪いことが起きるか」を pass として数える極性の誤り。そもそも世代別フィクスチャでブロック自体が起きなくなる |

---

# v3: 実 `.sdd/` コーパスへの移行と main→develop 効果検証

v2 までは「スキルの有無」を世代別の**合成**フィクスチャ上で測っていた。v3 は測る問いを
**「`main` → `develop` でスキルがどれだけ良くなったか」**に変え、フィクスチャを
**このリポジトリの実 `.sdd/` ツリー**に置き換えた。手順とバリアント構成は
[README.md](README.md) が正典。ここには **assertion 設計に効いた差分だけ**を記録する。

## v2 の欠陥2は構造的に解消した

v2 は世代別 `.sdd/` を手で書いたため、v5 の規約が v4 サンドボックスへ漏れた。v3 では合成しない。
`main` と `develop` はそれぞれ**自世代と整合した実 `.sdd/` ツリーを既に持っている**（`main` の
`CONSTITUTION.md` は `adr/` を知らず、`develop` のそれは義務化している）。`git archive <branch> -- .sdd`
を取るだけで世代整合が成立するので、混入の余地がない。

ただし `.sdd/AI-SDD-PRINCIPLES.md` と `.claude/rules/ai-sdd-instructions.md` は例外である。この2つは
SessionStart フックが**インストール済み**プラグインから生成するため、両ブランチとも v4.1.0 の内容を
コミットしている（[plugin-development.md](../rules/plugin-development.md)）。そのまま渡すと `develop` の
スキルは自分が実装していない規則で採点され、欠陥1と同じ循環的検証に戻る。`build_sdd_fixture.py` が
ブランチのプラグインソースから再レンダリングして解消している。

## assertion の判定基準は v2 から変えていない

バージョン中立・アウトカム基準という原則（上の「assertion を書くときの判定基準」）はそのまま有効。
比較軸が skill-vs-without から main-vs-develop に変わっても、**特定世代のパス・フィールド・語彙を
assertion に埋めてはならない**という理由は変わらない（`develop` 側だけが構造的に合格する検証になる）。

## フィクスチャ固有の記述を assertion から外した

v2 の assertion には合成フィクスチャ（`notification-badge`）にしか存在しない固有名が埋まっていた。
実 `.sdd/` コーパスにはそれらが無いため、対象を実在物へ置き換えつつ、**検証している性質は保つ**形に
書き換えた。

| スキル | v2 の記述 | v3 での扱い |
|:---|:---|:---|
| `check-spec` | 「未実装の FR-003（`clear_badge`）を検出する」「FR-002（99+ 上限）の実装漏れ」「仕様に無い `increment_unread`」 | 固有名を外し、「設計書の `impl-status: implemented` の主張を鵜呑みにせず実コードを確認する」「FR/NFR を項目ごとに突き合わせる」「仕様化されていない実装を別分類で報告する」に一般化。対象は `session-config_spec.md` × `plugins/sdd-workflow/scripts/` |
| `checklist` | 「`--update` 実行時、完了済みマークを保持したまま新規項目のみ追加している」 | 新規生成シナリオに既存チェックリストが無く判定不能なため、欠陥2として記録済みの**自己矛盾**（本文の P1〜P3 とテンプレートの P0〜P3）を突く形へ差し替え: 「本文とテンプレート・出力の優先度体系が一致し、同一実行内で矛盾していない」。`--update` の検証は既存チェックリストを持つ eval を追加する際に復活させる |
| `constitution` | 「`validate` 実行時、指摘が実際の記述内容に基づいている」 | `add` シナリオでは `validate` が走らないため削除。代わりに欠陥6（バージョンバンプ規則の自己矛盾）を突く「矛盾した指示があった場合、どちらを採用したかとその理由を示している」を追加 |
| `sdd-init` | 「既存の `.sdd/` 配下のファイルを上書き・破壊していない」 | フィクスチャが `.sdd/` を意図的に空にするため対象を実在物へ変更: 「既存のプロジェクトファイル（`plugins/` / `tests/` / `scripts/` 等）を上書き・破壊していない」。加えて欠陥7（`.sdd-config.json` 不在時の挙動の自己矛盾）を突く項目を追加 |
| `run-checklist` | 「ツール不足による SKIPPED の明示」（一般記述） | シナリオ側で分岐を強制し、項目 ID で指定: 未設定ツールの CHK-202 / 203 / 403 と人間レビューの CHK-3xx / 6xx を失敗として報告しないこと、既に手動チェック済みの CHK-103 を上書きしないこと |
| `task-cleanup` | 「上流ドキュメントの更新要否を実態を確認して判断している」（一般記述） | 検証可能な虚偽をシナリオへ埋め込んだ。`notes.md` の「NFR-003 の重複排除は未実装のまま残した」は `tasks.md`（タスク3 done）と実コード（`env_export.rewrite_exports` が prefix 単位で旧値を落とす）の両方と矛盾する。この記述を鵜呑みにするかで判定する |
| `recommend-front-matter` | ADR スキーマの検証を1つの eval に混ぜていた | `adr/` は `main` に存在しないため eval を分割。eval 0 は両世代で走る一致集合（`spec-review` の PRD/spec/design）、eval 1 は `develop` 専用の ADR スキーマ検証 |

## 対照群を必ず走らせる

`analyze-requirements` は `main` と `develop` で **1行も変わっていない**（+0/−0）。リフト差が 0 付近に
出るはずのスキルであり、そうならなければ**測定ノイズが他スキルの数値を無意味にしている**という警告に
なる。v2 では単に「評価対象の1つ」だったが、v3 では**方法論の一部**として削除禁止とする。

## `develop` 専用 eval は「改善」ではなく「新規能力」

`render-adr-review`（新規スキル）と `recommend-front-matter` の ADR eval には `main` の対応物が無い。
リフト差を計算する分母が存在しないため、**`main` の数値を捏造してはならない**。`develop` 内の
`skill` vs `without` のリフトだけを、新規能力として報告する。evals.json では
`main_counterpart: "none -- report lift within develop only"` で明示している。

## render-adr-review（v3 で新規に設計した assertion）

このスキルは決定ログを**決定 / 理由 / 却下した代替案**という軸に再構成して HTML レビューを出す。
Markdown→HTML 変換との差はこの再構成にあり、そこを検証の中心に据える。出力は
`.sdd/.cache/` 配下のスクラッチであり、永続ドキュメントを書き換えないことも不変条件。

1. 出力が一時領域（`.sdd/.cache/` 相当）に置かれ、永続ドキュメントを書き換えていない
2. 決定 / 理由 / 却下した代替案がそれぞれ独立した領域へ構造化されており、Markdown をそのまま
   HTML 化しただけになっていない
3. 元の決定ログに無い決定・理由・代替案を創作していない
4. append-only の決定ログの各エントリが、時系列と `supersedes` / `superseded-by` 関係を保って
   提示されている
5. 元の ADR ファイルを書き換えていない

## 未対象

`generate-usecase-diagram` は `main`→`develop` の差分が `+0/-0` のままなので v3 の対象外。v2 の assertion
（`### generate-requirements-diagram / generate-usecase-diagram` 節）はそのまま有効なので、差分が付いたら
そこから復元できる。

`generate-requirements-diagram` は当初この節に入れていたが、**PR #116 が `+3/-3` の差分を付けたため対象へ
格上げした**。変更は要求の抽出元の表記（`UR-xxx entries from tables` → `UR entries from tables`）で、
実 PRD の ID はアンダースコア（`UR_001`）なので、`main` 側の指示に従うと表から要求を拾えず図が欠落する。
つまり v2 で設計済みの assertion 1「入力に含まれる要求が図に漏れなく反映されている（脱落なし）」が、
差分が付いたことで初めて識別力を持った。**assertion は新しく起こしていない** — 既存の4件をそのまま使う。

この格上げで分かったこと: 「差分ゼロだから対象外」という判定は**その時点のスナップショットに過ぎない**。
欠陥修正が入るたびに対象集合が変わるので、`skill_delta_main_to_develop` は develop を取り込むたびに
引き直す必要がある（`## 対照群を必ず走らせる` が合成対照へ移行したのと同じ理由）。

---

# v3.3: 成果物ではなく「成果物についての主張」を見る（2026-09-10）

v5.0.0 の敵対的リリースレビュー（6レンズ + 反証フェーズ）が実欠陥22件を出したが、その3件は
**eval を1ランも走らせずに見つかった**。原因は共通で、既存 assertion が「作った成果物」だけを見ており、
スキルが成果物の外側で行う**事実主張**を見ていなかったことにある。

| 主張の種類 | 素通りしていた欠陥 |
|:---|:---|
| 書き込む値は事実か | `recommend-front-matter` が実装済みの文書に `impl-status: "not-implemented"` を刻む（`check-spec` の重大度分岐が Critical → Info に落ちる） |
| 報告は事実か | `generate-spec` の完了レポートが、書いていないファイルを「生成した」と報告する |
| 「検査した」は事実か | `doc-consistency-checker` が判定材料の無い検査を「0件」として整合が取れているように報告する |

## 判定基準への追加

assertion を新設・見直しするとき、次を確認する。

> **このスキルの出力には、成果物の外側で行う事実主張（生成した／検査した／実装済みである）が含まれるか。
> 含まれるなら、その主張の真偽を見る assertion があるか。**

この形の assertion はバージョン中立に書きやすい。パス名もフィールド名も不要で、必要なのは
「主張」と「実態」の一致だけであり、両者は世代に関係なく存在する。

追加したのは 3 件（`recommend-front-matter` eval 0 の A6、`generate-spec` の A6、
`doc-consistency-checker` の A6）。各 `evals.json` の `assertion_revision` に根拠を書いた。

## 「主張が事実か」で旧世代が落ちるのは許される非対称

`recommend-front-matter` A6 は、`main` の `type_specific_fields.md` が design ブロックに
`impl-status: "not-implemented"` を無条件で含むため、`main/skill` が構造的に落ちると予測している。
これは欠陥1（v5.0.0 固有の実装詳細を見ていた）の再演ではない。**v4 に無い概念を要求しているのではなく、
v4 に実在した欠陥で落ちている**のであり、判定基準そのものはどちらの世代でも同一に適用できる。

禁じられているのは「新しい指示に従ったか」を測る循環的検証である。「主張が事実か」は循環しない。

## エントリレベルの覆しは assertion にしない（コーパスが正典に追いつくまで）

v5.0.0 で ADR の覆し記録が確定した（エントリ間の覆しは新エントリ本文に一方向、front matter の
`supersedes` / `superseded-by` はログファイル全体の引退専用）。それでもこれを assertion にはしていない。

コーパスの唯一の ADR（`.sdd/adr/workflow-foundation/task-type-determination.md`）が、前文で
「決定を覆す場合は……`supersedes` / `superseded-by` で相互参照する」と書き、2つ目のエントリでも
front matter 相互参照と `adr/{feature}-decisions.md` 命名を決定として記録している。**フィクスチャは
ブランチの実 `.sdd/` そのものなので、これを採点対象にするとスキルの品質ではなくコーパスの古さを測る**。
欠陥1と同じ循環に、逆方向から入ることになる。

`render-adr-review` の A4 はこの整理に合わせて書き換えた。旧文言は front matter の
`supersedes` / `superseded-by` を保てたかを問うていたが、当該スキルの SKILL.md は supersede に一言も
触れておらず、コーパスの4エントリにも覆し関係が無いため、空振り（採点者次第で PASS とも FAIL とも読める）
だった。実際に検証できる不変条件——**追記順とエントリ境界の保存、記録されていない覆し関係の捏造なし**——に
置き換えている。
