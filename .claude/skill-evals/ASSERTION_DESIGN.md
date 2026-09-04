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
5. 人間が優先度判断できるよう、指摘に重大度が付いている

### implement

1. 仕様・設計が定めた範囲を超える機能を実装していない（スコープクリープなし）
2. テストが書かれ、実行して実際に pass する
3. 仕様の各 FR を実装が満たしている
4. 実装状況がドキュメント側に反映され、仕様とコードの乖離が放置されていない（手段は世代依存なので問わない）
5. テストを後付けではなく実装と同時／先行で書いている（自己申告＋成果物で判定）

### generate-prd

1. 既存の要求が変更されずに保持されている（非破壊的追記）
2. 新規要求の ID が既存の連番を正しく継続している（衝突・欠番なし）
3. 新規要求の属性（Priority / Risk / Verification）が既存要求と整合的に付与されている
4. 新規 FR が UR に遡れる（トレーサビリティ維持）
5. 全体再生成ではなく追記操作として実施されており、既存記述が失われていない

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

### task-breakdown

1. 各タスクが仕様・設計の要求 ID に遡れる
2. 各タスクに独立して検証可能な完了条件がある
3. タスクの順序が依存関係を尊重している
4. テストが暗黙ではなく明示的なタスクとして含まれている
5. 仕様の範囲外のタスクを創作していない

### task-cleanup

1. 設計判断とその**根拠（なぜ）**が、一時ログの削除で失われず永続的な場所に保存されている
2. 一時ログが重複した陳腐化履歴として残っていない（知識資産の永続化）
3. 上流ドキュメントの更新要否を、主張ではなく実態（コード・テスト）を確認して判断している
4. 進捗メモ・実装詳細のような**ノイズを永続ドキュメントに昇格させていない**（決定のみを残す）
5. チケットの完了が記録され、黙って破棄されていない

### plan-refactor

1. この変更が後方互換性を壊すことを明示的に指摘している
2. 影響を受ける呼び出し元・テストの影響分析を提示している
3. 後方互換性の方針を独断で決めず、人間の判断材料として提示している
4. 決定とその根拠が永続的に記録される想定になっている
5. 計画の根拠を仕様の**内容**に置いている（特定ファイルの有無に依存していない）

### doc-consistency-checker

1. PRD ↔ spec の整合性を検査し、実在するギャップを報告する
2. spec と記録済みの設計判断（その世代における保存先）を突き合わせている
3. 指摘が実在し正確である（創作していない）
4. 人間が優先度判断できるよう、指摘が重大度で分類されている
5. 下流から PRD を自動書き換えする提案をしていない

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

## 確認した実在欠陥（残り9スキル）

当初はfork実行制約（サブエージェント再委任不可）により静的解析のみで欠陥候補を洗い出したが、その後
オーケストレーター（メインセッション）が直接、9スキル×2世代×2variant=36回のエージェント実行と9件の
独立採点を実施し、静的解析の主張を実ファイル・実行結果・git履歴で裏取りした（#1は当初「v5.0.0化に伴う退行」
としていたが、実際には`ce3fea3`（本プロジェクトのold世代基準コミット）より前の別コミットで既に失われており、
古い世代のフィクスチャにも欠陥が混入している点を修正済み）。

| # | スキル | 欠陥 | 根拠 |
|:---|:---|:---|:---|
| 1 | `run-checklist` | `allowed-tools`に`Bash`が無く、スキルの核心機能（テスト・リンタ・セキュリティスキャナの実行）が実行不能。SKILL.md:3「Runs tests, linters, security scanners」、Section 3「Execute Automated Verifications」と矛盾する。2026-07-28のコミット`7e3e6c0`で`Read, Write, Edit, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList, TaskGet` → `Read, Glob, Grep, Edit(.sdd/**), TaskCreate, TaskUpdate, TaskList, TaskGet`に絞られた際の退行だが、このコミットは本プロジェクトの「old世代」基準コミット`ce3fea3`（2026-08-19）より前のため、old/new両方の実行で同一の欠陥が再現した（4実行中4実行がBash不可を報告し、静的解析で代替）。加えて`Write`も無いため、SKILL.mdが要求する新規ファイル`verification_report.md`の作成もEdit(.sdd/**)だけでは不可能（2実行が実際にこの壁にぶつかった） | `plugins/sdd-workflow/skills/run-checklist/SKILL.md:9`、`git log --follow -p`、実行ログ4件 |
| 2 | `checklist` | SKILL.md本文のProcessing Flow（P1/P2/P3の3段階、9カテゴリ、`CHK-{category}{nn}`形式）と、同スキルが自ら参照する`templates/ja/checklist_template.md`（P0〜P3の4段階、10カテゴリ、`CHK001`通し番号）が矛盾している。Export Formats節の「P0項目をGitHub Issue化する」という記述はテンプレート側のP0に基づくものだが、SKILL.md本文はP0を定義していない自己矛盾。old/new両世代、独立した2回の実行（`old/skill`・`new/skill`）が同一の矛盾を発見し、いずれもSKILL.md本文側を優先する同じ判断を下した。加えて`gh issue create`の実行には`Bash`が必要だが`allowed-tools`に無い | `plugins/sdd-workflow/skills/checklist/SKILL.md:170-184`（本文の定義）と`templates/ja/checklist_template.md`（矛盾するテンプレート）、`SKILL.md:214`（P0への言及）、`SKILL.md:8`（allowed-tools）、実行ログ2件（`old/skill`, `new/skill`） |
| 3 | `vibe-detector` | `disallowed-tools: Write, Edit, Bash`により、本文の「Escalation When Specifications Are Insufficient」節が指示する`task/{ticket}/assumed-spec.md`への推定仕様書き込みが実行不能。old/new両世代の実行が同一の権限矛盾を報告し、書き込むはずだった内容をテキストで代替提示することで対応した | `plugins/sdd-workflow/skills/vibe-detector/SKILL.md:7-8`（front matter）と`SKILL.md:115-126`（Escalation節）、実行ログ2件 |
| 4 | `recommend-front-matter` | `scripts/scan-documents.py`が使う`naming.determine_type`は`adr/`配下も走査・分類するが、SKILL.mdのPrerequisitesと`templates/{lang}/type_specific_fields.md`にADRのスキーマ定義が無い。old/new両世代の`skill`実行が独立にこのギャップを発見し、正しいスキーマ源（`shared/references/front_matter_reference.md`）を自力で探索して代替した一方、`without`実行（スキル無し）は世代を問わずADR推奨で`sdd-phase`等を欠落させた（4実行中2実行が同一assertionで失点、原因も一致） | `plugins/sdd-workflow/skills/recommend-front-matter/SKILL.md:19-23`、`templates/en/type_specific_fields.md`（ADR行なし）、正しい参照例: `plugins/sdd-workflow/agents/front-matter-reviewer.md:40`、実行ログ4件 |
| 5 | `naming.py::determine_type()`（共有モジュール） | `task/{ticket}/`配下のファイルは`implementation_log`/`impl_log`という名前パターンのみ`"implementation-log"`と判定し、それ以外は無条件に`"task"`と分類する。`design-draft.md`という新世代の設計ドラフト（`front_matter_reference.md`が定義する正規の配置場所）を特別扱いする分岐が無いため、`type: "design"`であるべき文書が`type: "task"`に誤分類される。`recommend-front-matter`の`new/skill`実行がこの誤分類を実地で発見し、`<!-- id候補: design-101 -->`というファイル内のヒントを根拠に`type: "design"`へ手動補正して切り抜けた。`determine_type`の唯一の呼び出し元は`scan-documents.py`のみ（docstringが挙げる`doc_walker`/`check-spec`は現状未使用）だが、影響範囲は今後この関数を再利用するツールにも及ぶ | `plugins/sdd-workflow/scripts/naming.py:91-101`（`determine_type`本体、design-draft分岐なし）、対比: `plugins/sdd-workflow/shared/references/front_matter_reference.md:57`（design型の正規配置） |
| 6 | `constitution` | SKILL.md内で原則追加時のバージョンバンプ規則が矛盾している。「2. Add Principle (add)」節（122行目）と巻末のセマンティックバージョニング表（236行目）はいずれも「原則追加 → Minor」とするが、「4. Update Constitution (update)」節の「Version Bump Rules」表（146行目）は同じ「Add principle」を「MAJOR」と定義している。4実行全てが同じ矛盾を認識した上でMinorを採用し（`add`サブコマンドの手順を優先）、一貫した判断を下したためgrading上は減点していないが、SKILL.md自体の記述矛盾は解消が必要 | `plugins/sdd-workflow/skills/constitution/SKILL.md:122`, `:146`, `:236` |
| 7 | `sdd-init` | SKILL.md自体が`.sdd-config.json`不在時の挙動について自己矛盾している。「Configuration File Management」節（66-70行目）は「スクリプトが自動的に...存在しなければデフォルト設定で作成する」と説明するが、その直後の「Execution Flow」節（100-102行目）は同じスクリプトについて「存在しなければError（事前作成かsession-startフックが必要）」と正反対の説明をしている。実装（`init-structure.py:47-50`）は後者と一致し、`.sdd-config.json`が無いと`ERROR: .sdd-config.json not found`でexit 1する（フォールバック実装なし）。old/new両世代の`skill`実行が独立にこの矛盾に遭遇し、手動で`.sdd-config.json`を作成してから再実行することで切り抜けた。`old/skill`実行はこの後の後始末（`.sdd/AI-SDD-PRINCIPLES.md`等、CLAUDE.mdが参照するファイルの生成）を「SessionStartフックの責務」として意図的にスキップし壊れた参照を残したのに対し、`new/skill`実行は`session-start.py`を手動実行して補完した——同じ欠陥への対応の質が実行ごとにばらついた点も、SKILL.mdのharness外運用時の手順が明文化されていないことの表れ | `plugins/sdd-workflow/skills/sdd-init/SKILL.md:66-70`（自動生成すると記述）vs`:100-102`（Errorすると記述）、`scripts/init-structure.py:47-50`（実装はError側と一致）、実行ログ2件（`old/skill`, `new/skill`） |
| 8 | `front_matter_reference.md`（共有リファレンス） | ADR（`type: "adr"`）の`status`フィールド定義表（76行目）は`draft, review, approved, deprecated`を有効値として列挙するが、直後の「Status Transition Rules」節のADRの項（189-193行目）は「ADR entries are append-only and do not follow the draft/review/approved lifecycle」と明記しており、同一ドキュメント内で自己矛盾している | `plugins/sdd-workflow/shared/references/front_matter_reference.md:76`, `:189-193` |

## 削除した assertion とその理由

| 削除した assertion | 理由 |
|:---|:---|
| `front matter に sdd-version があるか` | v5.0.0 固有フィールド。旧世代には概念がなく、新世代でも出力テンプレート次第で運が絡む |
| `adr/{feature}.md に統合したか` | v5.0.0 固有パス。「決定と根拠が永続化されたか」に一般化 |
| `task/{ticket}/design-draft.md を設計ソースとして使ったか` | v5.0.0 固有パス。世代別フィクスチャで各自の正しいパスを使えるようにして解消 |
| `明示的な --amend 概念が存在し従ったか` | スキル本文の語彙依存。「非破壊的な追記になっているか」に一般化 |
| `spec の陳腐化した sdd-version を検出したか` | v5.0.0 固有。代わりに世代非依存の実在不整合（spec の Public API に `increment_unread` が無い、設計記録内の型注釈がコードと矛盾）を検出対象に据える |
| `(old_skill) 設計書が無くブロックされるか` | 「悪いことが起きるか」を pass として数える極性の誤り。そもそも世代別フィクスチャでブロック自体が起きなくなる |
