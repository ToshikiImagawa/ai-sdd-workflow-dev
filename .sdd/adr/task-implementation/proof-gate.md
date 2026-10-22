---
id: "adr-task-implementation-proof-gate"
title: "Bend 証明ゲート 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-10-17"
updated: "2026-10-22"
sdd-version: "5.1.0"
depends-on: ["spec-task-implementation-proof-gate", "spec-task-implementation-laws-drafting"]
ticket: "149"
tags: ["checklist", "verification", "proof", "bend", "laws"]
category: "task-implementation"
---

# Bend 証明ゲート 決定ログ

## 2026-10-17 hub import を静的 allowlist で禁止する

- **Decision**: 法則ファイルの `import` 文は、Bend 同梱の標準ライブラリ `Base` と、同じ法則ディレクトリ内に実在する `.bend` への相対 `import` だけを許可し、それ以外（未知の形式・未解決の名前・`from` 形式・別名付きを含む）は検査器を起動する前に FAIL とする。
- **Rationale**: 判定のオフライン再現性（NFR-003）、`BEND_NO_TELEMETRY=1` によるテレメトリ停止方針、サプライチェーン面の安全性を揃える。Hub の import 構文を網羅的に deny するより allowlist のほうが構文変更に強く、未知の形式は FAIL 側に倒れる。clarify Q4 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: `.sdd-config.json` で hub import を許可可能にする — 許可した途端に PASS がネットワーク状態に依存するため却下（必要になった時点で別途議論する）。禁止せず bend に任せる — bend が名前解決のためネットワークへ出てしまい PRD NFR_002 に反するため却下。

## 2026-10-17 `laws/` 配下の命名検証を `naming.py` の対象にしない

- **Decision**: `.bend` ファイルの命名は `naming.py` / pre-tool-use の deny 対象に加えず、固定ファイル名（`LAWS.bend` / `PROOF.bend` / `main.bend`）の不備はゲート実行時の SKIPPED / FAIL の理由として報告する。
- **Rationale**: `naming.py` は `requirement/` と `specification/` を名前だけで区別するための書き込み時 deny であり、opt-in 機能のために `.md` 前提（naming.py / doc_walker / sdd_index）を崩す価値がない。`main.bend` が import する補助 `.bend` を置く余地も残せる。不備は front-matter-reviewer の `--cross-ref` と post-tool-use が可視化する。
- **Rejected alternatives**: `naming.py` を `.bend` に拡張し pre-tool-use で deny する — 共有モジュールの `.md` 前提を崩し、補助 `.bend` の配置を阻害するため却下。

## 2026-10-17 `laws-status: proven` は人が立てる

- **Decision**: run-checklist は PASS 時に spec の front matter を書き換えず、レポートで `laws-status: proven` への遷移を推奨するに留める。遷移は人が行う。
- **Rationale**: PASS は実行環境（bend の版、Lean 基盤の有無）に依存し、自動更新は AI の自己昇格を許す経路になる。run-checklist の書き込みは `task/{ticket}/` に閉じており、spec 本文・front matter への書き込み経路を増やさない（PRD DC_002）。`impl-status` のように機械更新する前例はあるが、`proven` は「人が承認した法則が証明された」という承認連鎖の終端なので人の手に置く。前提（承認行・`PROOF.bend`）は front-matter-reviewer が warning で検証する。clarify Q2 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: run-checklist が PASS 時に spec の front matter を書き換える — 環境依存の結果で spec を機械更新し、自己採点の経路を作るため却下。

## 2026-10-17 チェックリスト項目を `CHK-205 [P2]` とし `--category proof` を別名にする

- **Decision**: 仕様レビューカテゴリの固定項目 `CHK-205 [P2]`「法則証明（proof ゲート）」を、front matter に `laws:` を持つ spec に対してのみ生成する。`/run-checklist --category proof` は「CHK-205 のみ」を指す別名として受理する。
- **Rationale**: Bend は必須依存ではないため P1（マージ前必須）にするとマージが環境依存になる（PRD DC_001）。カテゴリ 1〜9 は親 PRD IR_002 で固定されており、`CHK-204`（制約の実装）の隣が意味的にも自然。`laws:` の無い spec に項目を出すと常に SKIPPED のノイズになる。既存の `--category` は CHK カテゴリ名を取るため `proof` は別名として定義する。clarify Q5 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: `CHK-205 [P1]` — マージ可否が bend の有無に依存するため却下。新カテゴリ 10（`CHK-10xx`）— 親 PRD で固定されたカテゴリ体系を崩すため却下。

## 2026-10-17 `# spec:` の値は spec の `id` とする

- **Decision**: `LAWS.bend` の先頭コメント `# spec:` には spec の front matter `id` を書く。
- **Rationale**: ファイル移動・リネームに強く、front-matter-reviewer の `--cross-ref` が持つ id レジストリで spec `laws:` ↔ LAWS `# spec:` の双方向整合を検証できる。id → path の解決は spec の直接走査（または `.cache/index.md`）で可能。clarify Q1 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: `${SDD_ROOT}` 相対パス — インデックス無しでも直接検証できる利点はあるが、移動・リネームに弱いため却下。

## 2026-10-17 `--verdict` で Lean 基盤が無い場合は通常検査にフォールバックする

- **Decision**: `--verdict` 指定時に Lean 基盤が無ければ通常検査にフォールバックして判定を返し、`verdict: "unavailable"` を併記する。TOOL_NOT_FOUND は「`bend` 自体が無い」場合だけに限定する。
- **Rationale**: ゲートの主判定（法則が満たされるか）を Lean の有無で失わない。失敗ケースの出力・終了コードは `--verdict` の有無で同一と実測されているため、フォールバックで判定が揺れない。`verdict` の 3 値（`checked` / `unavailable` / `not-requested`）で再検査の有無を機械可読に残す。clarify Q3 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: Lean 基盤が無ければ TOOL_NOT_FOUND で終える — 主判定まで失われ、bend 不在と区別できなくなるため却下。

## 2026-10-17 法則ディレクトリはスキルが `laws:` を読み `--laws-dir` で渡す

- **Decision**: spec の `laws:` を読み `${SDD_ROOT}/` を前置して `--laws-dir` に渡すのはスキル（LLM）の仕事とし、スクリプトは渡されたディレクトリを検査する。`--laws-dir` 省略時は `SDD_LAWS_PATH` 配下を再帰走査する。
- **Rationale**: CONSTITUTION A-002（spec の解釈は LLM、ディレクトリ検査は決定的なスクリプト）。スクリプトに spec の解釈責務を持ち込まず、`--laws-dir` 無しでも全走査できるため手動実行にも使える。`laws:` は PRD FR_003 どおり `${SDD_ROOT}` 相対に保ち、前置はスキルの定型作業にする。
- **Rejected alternatives**: スクリプトが spec の front matter を読んで対象を決める — スクリプトに spec 解釈の責務が混入し A-002 に反するため却下。

## 2026-10-17 複数法則ディレクトリの集約はスクリプトが行う

- **Decision**: スクリプトが全ディレクトリの判定を FAIL > TIMEOUT > TOOL_NOT_FOUND > SKIPPED > PASS の順で最悪判定に集約し、`results` に個別判定を併記する。スキルは 1 回だけ呼ぶ。
- **Rationale**: run-checklist は 1 項目（CHK-205）に 1 判定を記録する。集約を haiku のスキルに任せると不安定なので、決定的なスクリプト側に置き「見逃し」を作らない。
- **Rejected alternatives**: スキルがディレクトリごとに呼び、スキル側で集約する — 集約が非決定的になるため却下。

## 2026-10-17 `main.bend` は任意とする

- **Decision**: 参照モデル `main.bend` は任意とし、法則がモデル関数を参照しない自己完結の場合は省略できる。
- **Rationale**: `# model-of:` は `main.bend` にのみ置くため、無ければ見直し促し（FR-009）の対象が無いだけで判定には影響しない。
- **Rejected alternatives**: `main.bend` を必須にする — 自己完結の法則にも空のモデルを強いることになるため却下。

## 2026-10-17 階層 spec の法則ディレクトリは `laws/{parent}/{child}/` とする

- **Decision**: 階層 spec に対応する法則ディレクトリの既定を `laws/{parent}/{child}/` とし、省略時の探索は `LAWS.bend` / `PROOF.bend` を直接含むディレクトリだけを対象にして中間ディレクトリを SKIPPED に数えない。
- **Rationale**: spec / requirement / adr と同じ階層規則（AI-SDD の階層構造）に揃え、識別子をディレクトリ名に置く方針と整合する。`laws:` はパスのリストなので別形式でも動作するが、既定を揃えておく。clarify Q6 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: `laws/{parent}-{child}/` — 動作はするが他ディレクトリの階層規則と不一致になるため却下。

## 2026-10-17 承認行に法則本文の内容ハッシュを含めて束縛する

- **Decision**: `# approved:` 行に承認日・承認者に加えて法則本文（先頭コメント部を除く）の内容ハッシュ（sha256 先頭 12 桁）を含め、不一致なら承認失効として SKIPPED とする。ハッシュは `--print-laws-hash` で人が得る。
- **Rationale**: 承認行の有無だけでは「承認後に法則を弱めて PASS を得る」抜け道が残る（prd-reviewer / spec-reviewer 指摘）。`LAWS.bend` 単体で検証でき、先頭コメント部を除外することで承認行の追記自体では失効しない。
- **Rejected alternatives**: 承認行の有無だけを見る — 承認後の改変を検出できないため却下。git の履歴で承認日以降の変更を検出する — フックは git 無しでも動くという方針と相容れず、日付粒度で曖昧なため却下。

## 2026-10-17 孤児 laws はゲートの FAIL と reviewer の error の両方で静的に検出する

- **Decision**: `LAWS.bend` の `# spec:` が実在する spec に解決でき、かつその spec の `laws:` が当該ディレクトリを指すこと（双方向）を法則ディレクトリの成立条件とし、満たさなければゲートは FAIL（判定表 #4）、front-matter-reviewer `--cross-ref` は error とする。明示指定・再帰走査とも同条件で、承認判定（#5）より前に評価する。
- **Rationale**: spec が正典であり（D-001）、spec に結びつかない法則は派生物として成立しないので「失敗ではない」では済まない。両方に置くことで bend の有無によらず静的に検出でき、既存 #2（spec → laws）と対になって双方向の整合が閉じる。`# spec:` による laws → spec の参照は検証のための照合で、`depends-on` の依存方向は変えない。PR #152 レビュー中のユーザー指示で追加した。
- **Rejected alternatives**: warning / SKIPPED に留める — `laws:` の書き忘れや spec 削除後の取り残しがノイズに埋もれ、承認済み法則が spec 無しで PASS を出しうるため却下。ゲート側のみで検出 — bend 未導入環境では TOOL_NOT_FOUND で #4 に到達せず検出経路が無くなるため却下。reviewer 側のみで検出 — `--cross-ref` を実行しない限り見つからず、ゲート単体で判定の完全性を保てないため却下。

## 2026-10-17 `SDD_LAWS_DIR` / `SDD_LAWS_PATH` は常時エクスポートする

- **Decision**: session-start は `laws:` を持つ spec の有無にかかわらず `SDD_LAWS_DIR`（既定 `laws`）/ `SDD_LAWS_PATH`（既定 `${SDD_ROOT}/laws`）を常時エクスポートする。`init-structure.py` の既定 config には `laws` を含めず、ディレクトリ自体は opt-in 時に初めて作る。
- **Rationale**: spec FR-003 / §4.1「他ディレクトリと同様に」エクスポートする定義と整合する。変数が常に存在してもディレクトリが無ければ副作用はない。統括セッションが 2026-10-17 に承認した。
- **Rejected alternatives**: `laws:` を持つ spec があるときだけエクスポートする — セッション開始時に全 spec の front matter を走査する必要があり、フックの軽量性と A-002（スクリプトは決定的・単純）に反するため却下。

## 2026-10-17 承認行の真正性は運用と生成スキルの指示で守り pre-tool-use では deny しない

- **Decision**: AI が `# approved:` 行を書いてしまう事故は、PR レビューで承認行の追加を確認する運用と、法則案生成スキルの指示での禁止で防ぐ。pre-tool-use での deny は入れない。
- **Rationale**: 内容ハッシュによる束縛は「承認後の改変」を塞ぐが「AI が承認行を書く」ことは塞がない。pre-tool-use は `.bend` への書き込み主体（人か AI か）を判別できないため、deny では人の承認作業まで阻害する。
- **Rejected alternatives**: pre-tool-use で `# approved:` を含む `.bend` の書き込みを deny する — 書き込み主体を判別できず人の承認も止めてしまうため却下。

## 2026-10-17 `AI-SDD-PRINCIPLES.source.md` と spec テンプレートの変更を本チケットの範囲外とする

- **Decision**: 原則文書（`AI-SDD-PRINCIPLES.source.md`）の構成図への `laws/` 追記、spec テンプレート（en/ja）への任意「Laws」節の追加、`sdd_index.py` への `laws` / `laws_status` 列の追加は本チケットでは行わない。利用者向けの説明は README / CHANGELOG に限る。本リポジトリ自身の dogfooding 用 `.sdd/laws/`（候補: proof-gate_spec 3.1.1 判定表の法則化）も本チケットでは作らない。
- **Rationale**: 法則への参照は front matter `laws:` で表現でき本文節は重複になる。`sdd_index.py` の列追加はスキーマ bump を伴い、「`drafted` のまま放置された spec」を列挙したくなった時点で別チケットで判断すればよい。原則文書は opt-in 機能のために改版する必要がなく、設計ドラフト（削除済み）§7.1 のモデル作成ガイドは README に反映した。
- **Rejected alternatives**: 本チケットで原則文書・テンプレート・インデックスまで拡張する — opt-in 機能に対して変更範囲が広く、スキーマ bump と原則文書の改版を伴うため却下。

## 2026-10-18 Bend 側の観察の実機再確認は未実施とし自前の静的検査で代替する

- **Decision**: spec §4.1 が実装時に求める Bend 側の観察（先頭コメント部の読み飛ばし、`LAWS.bend` 未 import の拒否、Hub import の構文、`bend --version` の出力形式）の実機再確認は本チケットでは実施していない。ゲートはこれらの観察に依存せず、`laws_header.py` の静的検査（先頭コメント解析・内容ハッシュ・`law` 宣言・LAWS import・import allowlist）で同じ条件を自前で課す。実機再確認は別 issue で扱う。
- **Rationale**: CI に本物の `bend` を入れない方針（NFR-001 / DC_001）のため、実装 PR の検証はダミー `bend` による subprocess テストに限られた。観察に依存しない設計なので、再確認の結果が変わってもゲートの判定表は影響を受けない。未実施を事実どおり記録し、spec の要求に対する受け皿を残す。
- **Rejected alternatives**: 実機再確認が済むまで `impl-status: implemented` を保留する — ゲートの判定が観察に依存しないため、保留する実益がなく却下。再確認を省略して記録も残さない — spec §4.1 の「結果を決定ログに記録する」との不整合が残るため却下。

## 2026-10-18 Bend 側の観察を実機で再確認した

- **Decision**: spec §4.1 が求める 4 点を、実機（Bend 2.0.37、bendlang/bend e5527d5 を bun で起動）で再確認した。上の「実機再確認は未実施」エントリは本エントリで置き換える。設計時の観察と一致したのは 1〜3、食い違ったのは 4 とローカル import の構文（次のエントリ）である。
  1. **先頭コメント部の読み飛ばし**: 一致。`# spec:` / `# approved:` / 空行を `import Base` より前に置いても `bend PROOF.bend` は `ALL PROOFS CHECK`（終了コード 0）を返す。
  2. **`LAWS.bend` 未 import の拒否**: 一致。ただし固定名でのみ働く。`PROOF.bend` が LAWS を import していないと `Error: PROOF.bend must import ./LAWS.bend`（終了コード 1）で拒否するが、同じ内容を別名（`P2.bend`）で検査すると `ALL PROOFS CHECK` になる。ゲートが検査器へ渡すのは常に `PROOF.bend` だが、静的検査（`imports_laws`）はこの固定名依存に頼らず自前で課す方針を維持する。
  3. **Hub import の構文**: 一致。`import 0x<hash>/main.bend as P`（内容ハッシュ）と `import <name>@<version>/main.bend as P`（名前とバージョン）で、`bend` は `https://hub.bend-lang.com` へ取得に行く（オフラインでは `SOME PROOFS FAIL`、終了コード 1）。ゲートの allowlist は `.` と `@` を含む形、実在しない `0x…/` ディレクトリを拒否し、検査器の起動前に FAIL にする。
  4. **`bend --version`**: **食い違い**。`bend --version` は `bend: unknown option --version`（終了コード 1）で、版は `bend version`（標準出力 `bend 2.0.37`）で得る。ゲートの実装は版の取得にどちらも使っていないため判定表への影響はない。版の表示が必要になった場合は `bend version` を使う。
  加えて、`--verdict` は Lean 不在で `Error: BendTT infrastructure: the kernel did not build (lean: Executable not found ...)`（終了コード 1）となり、判定表 #11 の目印 `BendTT infrastructure` と一致した。ゲートは通常検査にフォールバックして `PASS` と `verdict: "unavailable"` を返す。
- **Supersedes**: [2026-10-18 Bend 側の観察の実機再確認は未実施とし自前の静的検査で代替する](#2026-10-18-bend-側の観察の実機再確認は未実施とし自前の静的検査で代替する)。再確認を実施したため、「未実施」の記録は現行の決定ではなくなった。
- **Rationale**: spec §4.1 が「実装時に Bend で再確認して結果を決定ログに記録する」と求めていたこと、および issue #162 の dogfooding で初めて本物の `bend` を実行できたことによる。1〜3 と `--verdict` は設計時の観察どおりで判定表の変更は不要。4 は版取得コマンドの記録の訂正に留まる。ローカル import の構文は影響が大きかったため独立したエントリで扱う。
- **Rejected alternatives**: 再確認を別 issue に残す — dogfooding の受け入れ基準が本物の `bend` での実機確認であり、先送りする理由がなく却下。ゲートに `bend --version` での版検査を足す — 判定が版に依存しない設計（NFR-007 は前提の明記に留める）であり、今回の食い違いは実装に影響しないため却下。

## 2026-10-18 ローカル import は別名付きのみ許可する（2026-10-17「hub import を静的 allowlist で禁止する」を改訂）

- **Decision**: 法則ファイルで許可する import を `import Base` と `import <相対パス>.bend as <Name>` の 2 形式にする。`<Name>` は英字または `_` で始まる英数字と `_`、パスは同じ法則ディレクトリ内に実在する `.bend` ファイル（`./` は任意、サブディレクトリ可）。別名のないローカル import、拡張子のない指定、`from` 形式、hub import（`0x<hash>/…`、`<name>@<version>/…`）、URL、絶対パス、親ディレクトリ（`..`）、末尾コメント付きの行は、従来どおり検査器の起動前に FAIL とする。`PROOF.bend` の LAWS import は `import ./LAWS.bend as <Name>`（`./` 任意）だけを有効とする。2026-10-17 のエントリの「別名付きを含む」を FAIL とする部分だけを改め、hub import 禁止・親ディレクトリ禁止・固定ファイル名という設計意図は変えない。
- **Supersedes**: [2026-10-17 hub import を静的 allowlist で禁止する](#2026-10-17-hub-import-を静的-allowlist-で禁止する) のうち、別名付きの import を FAIL とする部分のみ。それ以外の決定は現行のまま。
- **Rationale**: 実機（Bend 2.0.37）はローカル import に必ず別名を要求し、別名のない形を構文エラーにする。`import ./LAWS.bend` を検査すると次の出力で終了コード 1 になった。
  ```
  SOME PROOFS FAIL
  Error:
  - expected : an import ('import Base', or 'import <path> as <Name>')
  - observed : 'import ./LAWS.bend'
  ```
  一方、公式 demo と同じ `import ./LAWS.bend as Laws`（証明は `def Laws.<law名>`）は `ALL PROOFS CHECK` になる。旧 allowlist は別名付きを拒否し別名なしを許可していたため、実機で通る法則ファイルがすべて規約違反の FAIL になり、PASS を得る経路が存在しなかった。許可を広げるのは別名付きの相対 import だけで、外部取得に至る形（hub・URL）は引き続き静的に拒否するため、オフライン再現性（NFR-003）と PRD NFR_002 は保たれる。実機の許容範囲（`.bend` 拡張子が必須、`./` は任意、別名は英字または `_` で始まる英数字と `_`（`1A` は構文エラー）、`..` はファイル不在で失敗）に合わせて正規表現を定めた。
- **Rejected alternatives**: 別名なしのみ許可する旧決定を維持する — 実機の bend が構文エラーにする形だけを許すことになり、dogfooding を含む全ての実利用で PASS が取れないため却下。ゲートを変えず別 issue に分離する — #162 の受け入れ基準（実機で PASS を確認する）を満たせず、不具合を抱えたまま法則ファイルを置くことになるため却下。別名の有無を問わず許可する — 別名なしは実機で構文エラーとなり、ゲートが通した後に bend が失敗する二重の経路が残るため却下。

## 2026-10-18 PRD FR_005 の優先度を Must に揃える

- **Decision**: PRD（`requirement/task-implementation/proof-gate.md`）の FR_005「法則の見直し促し」の優先度を Should から Must に変更し、第 1 弾の要求 FR_001〜FR_005 をすべて Must とする。spec FR-009 は変更しない。
- **Rationale**: spec FR-009 と実装（PR #154 の `post-tool-use.py` 拡張）は見直し促しを必須として扱っており、PRD だけが Should のまま残って優先度が食い違っていた（issue #157）。参照モデルと実装の乖離は証明では検知できず、編集直後の促しが唯一の緩和策であるため、PRD を実態に合わせて必須に引き上げる。issue #157 でオーナーが選択肢 A（PRD を Must に上げる）を決定した。
- **Rejected alternatives**: spec FR-009 を推奨（任意）に下げる — 実装済みの必須挙動との整合が崩れ、spec → 実装の一方向派生に反するため却下。

## 2026-10-19 第 2 弾（法則案の生成）を新 spec と 3 段階スキルで設計する

- **Decision**: 法則案の生成と承認フローを新 spec [laws-drafting_spec.md](../../specification/task-implementation/laws-drafting_spec.md) に定義する（第 2 弾の実装は別チケット）。要点は次の 6 つ。
  1. 抽出元は判定表・状態遷移・集約規則と、制約事項・NFR の数値目標のうち機械的に等式化できるものだけ（FR 表の散文のみは対象外）とし、法則化しない理由を抽出レポートに残す。
  2. 新規スキル `/draft-laws`（仮称）とし、`/generate-spec` や `/checklist` は拡張しない。
  3. 法則数の既定上限は 10（`.sdd-config.json` の `laws.max_laws`）。優先順は判定表の単調性・順序 > 集約 > 不変条件 > 数値境界で、超過分は「未採用の候補」として残す。
  4. 1 スキルに 3 段階（draft → 人の承認 → model/proof）を持たせ、`laws-status` と 1 対 1 に対応させる。承認行が有効（内容ハッシュ一致）でなければ model/proof 段階を拒否する（`laws-status` は warning 併記に留める）。承認行は AI が書かず、ハッシュと書式を案内するだけとする。
  5. spec 変更への追従は post-tool-use の促し、法則本文側の `# source: <spec id> §<節> sha256:<節ハッシュ>` 出典コメント、`bend` 不要の静的チェック（出典の実在・欠落・重複・自明法則・import 許可形式）で行う。
  6. 検収は第 1 弾の手書き法則 5 件を再現できるかで行い、他 spec への適用は別チケットで提案する。`bend` が無い環境でも法則案の生成はでき、証明段階だけ TOOL_NOT_FOUND になる。
- **Rationale**: clarify Q1〜Q6 として提示し 2026-10-19 にオーナーが承認した。spec が正典（D-001）で、法則は下流の opt-in 派生物なので、spec 生成スキルを拡張せず責務を分ける（A-001 / A-002）。承認の主体を人に固定したまま、承認後の工程だけを AI に任せる。
  出典コメントを法則本文側に置くのは、出典を内容ハッシュの対象に含めるためである。ただし内容ハッシュは `LAWS.bend` の本文だけを対象にするので、**spec だけが変わっても承認は自動では失効しない**。節ハッシュ不一致は静的チェックと促しで検出し、再抽出と再承認は人が判断する。出典コメントを更新するたびに本文が変わり再承認が要るため、承認の手間は増える。この手間を、法則が spec とずれたまま PASS を出し続けるリスクと引き換えに受け入れた。
  第 1 弾 spec の FR-008 は「`drafted` は法則案生成スキルが付与してよい」と許可しているが、これは許可であり義務ではない。第 2 弾のスキルは PRD DC_002（spec の front matter を書き換えない）を優先し、この許可を行使せず `laws:` / `laws-status: drafted` を提案に留める。第 1 弾 spec は変更しない。
- **Rejected alternatives**: `/generate-spec` の拡張 — spec 生成と派生物の生成が混ざり、`bend` 任意の方針と責務がぼやけるため却下。`/checklist` への組み込み — チェックリスト生成の責務を超えるため却下。出典コメントを先頭コメント部に置く — ハッシュ対象外になり、出典の改変を承認が検知できないため却下。承認後の工程を段階ごとの別スキルにする — `laws-status` との対応が分散し、承認確認の実装が重複するため却下。

## 2026-10-19 第 2 弾の追加決定: 節ハッシュのずれをゲートに warning で出す・第 1 弾 spec の文言整合

- **Decision**: (1) `# source:` に記録した節ハッシュと現在の spec 節のずれを、proof ゲート（`CHK-205`）の結果に **warning** として併記する（laws-drafting_spec FR-013）。承認は失効させず PASS も止めない。(2) 第 1 弾 [proof-gate_spec.md](../../specification/task-implementation/proof-gate_spec.md) の `drafted` に関する 4 か所（FR-008、§4 のスキル行、§4.1 の `laws-status` 表、§7.2 の遷移図）を「生成スキルが提案し人が適用」に揃える。判定表・挙動は変えない。なお FR-013 の `warnings` は、第 1 弾 spec §4.1 の出力契約への**加算のみの追加**（既存フィールドと判定は不変）として実装チケットで同 §4.1 に追記する。(3) 承認行の無い既存 `LAWS.bend` も既定では温存し、再生成案は `LAWS.draft.bend` に出す（`--overwrite` で上書き。承認行ありは拒否）。
- **Rationale**: オーナーが 2026-10-19 に承認した。spec だけが変わったときに法則とのずれを見逃さないため、フックの促しに加えてゲートでも可視化する。warning に留めれば、承認の意味と PASS の意味（第 1 弾）を変えない。(2) は、第 1 弾の「付与してよい」が第 2 弾の「提案に留める」（PRD DC_002 を優先）と食い違っていたための文言整合であり、**第 1 弾 spec を変更しない方針に対する例外**（挙動は変えない）として記録する。
- **Rejected alternatives**: 承認ハッシュに節ハッシュを含めて spec 変更で承認を自動失効させる — 意味が変わらない spec 修正（誤字・表現の整理）でも再承認を強いてしまい、承認の手間が過大になるため却下。ずれをゲートに出さず促しだけにする — bend を持つ環境でもゲートの結果からずれが見えないため却下。第 1 弾 spec を変更せず差を ADR の記録だけに留める — 同じ遷移の主体が 2 文書で食い違ったまま残るため却下。

## 2026-10-19 モデル API を `LAWS.bend` 本文の `# model-api:` 行に置く

- **Decision**: 法則が参照する `Model.*` の関数名・型・数値の符号化を、`draft` が `LAWS.bend` の本文（先頭コメント部の外）に `# model-api:` コメント行として書く。`model` 段階はこの行と `Model.*` の参照だけを入力にする。
- **Rationale**: 抽出レポートは `--ticket` 無指定なら標準出力で、`task/` は一時領域のため、`model` 段階の入力として残らない。本文側に置けば内容ハッシュの対象になり、承認時に人がモデルの形も確認できる。
- **Rejected alternatives**: 抽出レポートを `model` の入力にする — 保存されず、承認の対象にもならないため却下。`task/{ticket}/` に置く — 一時領域で承認から `model` までの間に消えうるため却下。`model` 段階が `Model.*` 参照から毎回推測する — 数値の符号化など法則から読み取れない情報があり、LLM の推測が揺れるため却下。

## 2026-10-20 第 2 弾の実装を完了とし、独立再現の合格を #180 に引き継ぐ

- **Decision**: 第 2 弾（#168）の実装（共有モジュール・`draft-laws` スキル・フックの促し・ゲートの `warnings`・利用者向け説明と関連 spec の追従）を完了とし、laws-drafting_spec の `impl-status` は `in-progress` に留める。再生成案は既定で `LAWS.draft.bend` に出し、承認行を持つ `LAWS.bend` は `--overwrite` でも上書きしない。`LAWS.draft.bend` は孤児検査と `# spec:` 照合の対象にしない。検収（第 1 弾 5 法則の再現）は 2 段階判定（機械的一致 → 人による `equivalent` / `weak` / `none`）とし、未完の「独立再現での合格」は #180 で扱う。 設計ドラフトにあった PRD FR_006 の変更提案（承認の有効性が前提である旨・静的チェックの追加・抽出元を構造化された節へ改める、の 3 点）は PRD を変更しておらず、オーナーの判断待ちである。
- **Rationale**: 独立再現は 1・2 回目で機械一致が 5 件中 2 件にとどまり、抽出件数も 7 件 → 10 件とぶれた（NFR-005 のとおり抽出は再現を保証しない）。`aggregate_fail_absorbs` は Nat 全域（a>4）で偽になり、`model` 段階で必ず落ちた。このため、順位を表す定数関数をモデル API に固定して法則側は数値リテラルを書かない、静的チェックに `unbounded_nat_literal` の警告を加えて承認前に人へ見せる、という 2 点を決め、検収を 2 段階判定にした。5 回目の独立再現では 4 件は機械的に一致したが、集約の交換則だけが `aggregate([a, b]) == aggregate([b, a])` ではなく二項演算 `worse` の側で書かれ `weak` になった。基準は下げず、抽出ルール（集約関数がある場合は代数的性質を集約関数の側で書く）の追加で解くため、#180 に分離した。`LAWS.draft.bend` は採用前の提案で正本ではなく、孤児検査の対象にすると採用前の案が FAIL を起こす。
- **Rejected alternatives**: 機械一致のみで判定する — 変数名や定数関数の呼び出し形が違うだけの同値な法則を不合格にし、LLM の抽出のぶれに検収が左右されるため却下。`impl-status: implemented` にして検収を後回しにする — 受け入れ基準が未達のまま完了と表示することになるため却下。`weak` を合格に含める — 命題が別物であり、検収の意味が薄れるため却下。`LAWS.draft.bend` も孤児検査の対象にする — 採用前の案が常に FAIL するため却下。

## 2026-10-21 PRD FR_006 の変更を採用し、#167 の 4 件を決める

- **Decision**: オーナーが、2026-10-20 のエントリで判断待ちとした PRD FR_006 の変更提案（承認の有効性がモデル・証明の作成の前提である旨・検証方法への静的チェックの追加・抽出元を構造化された節へ改める、の 3 点）を採用し、PRD に反映した（#167 / PR #186）。あわせて #167 の 4 件を次のとおり決めた。(1) 用語集に「承認者」（法則の内容ハッシュを確かめ、承認行を手で書く人）を加える。(2) ユースケース図では第 1 弾と第 2 弾を区別しない。(3) RemindReview のアクターを FR_005 の主体に合わせ、他の PRD と同じ「フックランタイム」にする。(4) アクターを結ぶ実線へのラベル付けは proof-gate だけの書き方とし、PRD 全体の方針にしない。理由を PRD に一言残し、他の PRD には広げない。
- **Rationale**: (1) 図に「承認者」というアクターが既にあり、承認は人にしかできないため、用語として定義するほうが読み手に伝わる。(2) 段階（第 1 弾・第 2 弾）は §3.1 の優先度・段階の表で足りる。図で分けると、ノード構造が段階の変更に引きずられる。(3) FR_005 の主体はファイル編集後のフックで、他の PRD は既にフックを「フックランタイム」と書き、「Claude Code」は別の役割として併存している。(4) 全 PRD の関連線 68 本のうちラベル付きは proof-gate の 5 本だけで、承認者・開発者・フックランタイムの役割の違いを示す必要がこの PRD にあった。全体方針にすると他の PRD の書き換えが要る。
- **Rejected alternatives**: 図の subgraph 分割やスタイルで第 1 弾と第 2 弾を分ける — 段階の変更のたびに図を直すことになるため却下。RemindReview のアクターを「Claude Code」のままにする — FR_005 の主体とずれるため却下。ラベル付けを PRD 全体の方針にする — 他の PRD への横展開が大きく、今回は必要性が proof-gate に限られるため却下。

## 2026-10-22 点命題を差分 pytest に回し、prose 実装の spec を法則化から外す

- **Decision**: v5.2.0 の法則 61 件を調査した結果（[#218](https://github.com/ToshikiImagawa/ai-sdd-workflow-dev/issues/218)）、laws-drafting_spec に次を追加する。(1) `for` 宣言を持たず `kind` が `empty` / `singleton` / `identity` でない候補（点命題。判定表 1 行の転記）は Bend 法則にせず、`rank` が `to_tests` に振り分け、`draft` が実装に対する差分 pytest（既定 `tests/laws/test_<feature>.py`。各テスト直前に `# source:`）として書く（FR-014）。(2) 実装の所在は spec 本文の `impl-of:` 宣言で固定し、`main.bend` の `# model-of:` はその写しとする。全パスが `.md` の spec は `prose_implementation` として法則化対象外（FR-015）。(3) 既存法則は読み取り専用の `migrate` が `keep` / `to_tests` / `prose_delete` に分類した移行表を出し、削除・再承認・front matter の更新は人が行う（FR-016）。(4) `check --tests` がテストファイルの `# source:` の実在と節ハッシュ一致を検査する（3.1.3-9）。proof ゲート本体（`run-verification.py`）・判定表・PASS の意味は変えない。
- **Rationale**: 61 法則のうち約 50 件が点命題で、spec の表 → `LAWS.bend` → `main.bend` → `PROOF.bend` と同じ表を 4 回書いて bend で「表 == 表」を証明していた。bend の PASS は参照モデルまでの保証で実装には届かず、CI で bend を走らせない方針のため手元でしか効かない。一方、同じ法則を Python 実装に直接 assert する差分テスト 73 件は全件一致し、bend 無しで CI が毎回実装への回帰を検出できた。点命題を捨てるのではなく検証先を pytest に移す（有限領域では行の列挙が完全な仕様であり、無駄なのは転記であって行の検証ではない）。29 法則は実装が SKILL.md / エージェント定義の散文で、証明しても実装に結べず、うち 2 件は `# model-of:` が実体でない Python ファイルを指していた（`# model-of:` を LLM が選んでいたため）。所在を spec の宣言に固定し、散文実装の spec を対象外にして承認・証明のコストを無くす。点命題の判定を `for` の有無という構文的事実にしたのは、LLM のタグ付けに依存すると再現性（NFR-005）が落ちるため。空入力・単一要素・単位元を例外にしたのは、集約規則の代数的性質で全称法則の基底になり、§11 の検収基準（`agg_empty_skipped` / `agg_single_identity`）を壊さないため。テスト本文はスクリプトで生成せず LLM がテンプレートから書く（`main.bend` と同じ位置づけ）。決定性が要るのは NFR-002 の「ハッシュ・順序・検査」だけで、スクリプトは `# source:` の検査だけを保証する。
- **Rejected alternatives**: 点命題を全廃し全称法則だけ残す — 有限領域では決定表の行の列挙が完全な仕様で、差分テストでは回帰検出に効いたため却下。Markdown 決定表のパーサと pytest 生成器を作る — 表は spec ごとに列が違い（`条件|結果` / `検査|重大度`）方言ごとの保守になる上、差分テストの本質は「spec の値域 → 実装の呼び出し方」の写像とフィクスチャで表から機械導出できず、自動化できるのは assert 1 行だけのため却下。候補に LLM が `point: true` を付ける — 自由変数の有無は構文的事実で、タグ付けに頼ると付け忘れで判定がぶれるため却下。実装の所在を front matter の新キーにする — front-matter-validation_spec・front-matter-reviewer・テンプレートの改訂が波及するため、`model-api:` と同じ本文宣言にした。AI が承認済み `LAWS.bend` を編集・削除する — 承認行を持つ法則は AI が触らない第 1 弾の規約に反するため却下（移行表まで）。bend を CI で走らせる — 本改訂の論点（実装への到達）とは独立で、別 issue とする。散文実装の性質をスキル評価（skill-evals）の assertion に移す — 方向性として妥当だが本チケットの範囲外とし、ここに記録するに留める。`tests_dir` を可変にせず固定する — 配布先のテスト配置は様々なため `.sdd-config.json` の `laws.tests_dir` で変えられるようにした（`allowed-tools` は既定パスのみ事前承認。既定以外では承認プロンプトが出るトレードオフを受け入れる）。

## 2026-10-22 移行表を適用し、法則を全称法則 6 件に整理する

- **Decision**: 移行表（#218）に基づき、法則ディレクトリ 12 件を次のとおり整理した（#220）。(1) 実装が散文の 9 ディレクトリ（prd-generation、quality-guardrails の constitution-injection / doc-consistency-check / front-matter-validation / impl-spec-check / naming-enforcement / stale-doc-detection / vibe-detection、spec-design/clarify）を削除し、対応する spec の front matter から `laws:` / `laws-status:` を外した。constitution-injection / naming-enforcement / stale-doc-detection の 3 件は点命題のみだったため、差分テスト `tests/laws/` が検証を引き継ぐ。(2) sdd-init / session-config の `LAWS.bend` から点命題（2 件 / 6 件）を削除し、全称法則（`no_section_appends` / `config_wins`）だけを残した。`main.bend` / `PROOF.bend` も同期した。内容ハッシュが変わるため既存の承認行は失効し、`laws-status` は `drafted` に戻す。再承認（新ハッシュの承認行）は承認者が書く。(3) 全 12 spec の §4 冒頭に `impl-of:` 宣言を置き、`main.bend` の `# model-of:` をその写しにした（session-config は `hook_common.py` を追加）。残る法則は proof-gate 5 件（うち空入力 1 件）、sdd-init 1 件、session-config 1 件の計 7 件。
- **Rationale**: 2026-10-22 の決定（点命題は差分 pytest へ、散文実装は法則化対象外）を既存法則に適用したもの。削除した 9 ディレクトリの法則はすべて点命題で、全称法則を 1 件も含まなかった。差分テスト 70 件が CI で実装に対して走るため、削除で失われる検証はない。承認行は AI が書かない規約（第 1 弾）を守り、`laws-status` は実態（承認無効）に合わせて `drafted` にした。
- **Rejected alternatives**: 散文実装の法則を `main.bend` だけ残して参考資料にする — 承認・証明の対象でない Bend ファイルが残ると孤児検査と `# spec:` 照合の例外が要るため却下。点命題を `LAWS.bend` にコメントアウトで残す — 内容ハッシュに入らず差分テストと二重管理になるため却下。承認行を AI が新ハッシュで書き直す — 承認は人の行為であるため却下。

## 2026-10-22 bend を optional CI ジョブで実行する（#221 案 A）

- **Decision**: 本リポジトリの CI（`.github/workflows/ci.yml`）に optional ジョブ `proof` を追加する。ubuntu のみ、`continue-on-error: true` で required にしない。bend は公式 `install.sh` ではなく GitHub Releases のビルド済み tarball をバージョン固定（`BEND_VERSION`）で取得して `~/.bend` に展開する。実行は新規の `scripts/proof-gate.sh` が担い、`run-verification.py proof` を `--laws-dir` 無しで呼んで `.sdd/laws/**` の全法則ディレクトリを探索し、JSON の `status` が `PASS` 以外（FAIL / SKIPPED / TOOL_NOT_FOUND）なら exit 1 にする。`run-verification.py` 自体（常に exit 0 で JSON を返す契約）は変えない。laws-drafting_spec §8 / proof-gate_spec §8 / README の「CI に bend を導入しない」は「配布先には要求しない。本リポジトリは optional で実行する」に改める。
- **Rationale**: 計測で、Linux x64 の tarball は 37 MB・取得約 8 秒、残る 7 法則の proof は 1 秒未満、証明の検査に clang は不要だった。コストが `test` ジョブより軽い一方、手元だけの検査では承認失効（SKIPPED）に気づけず、#222 の作業中に実際に発生した。差分テスト（`tests/laws/`）は実装への到達を担い、proof ジョブは参照モデルの証明を担う別の役割で、両方を CI に置いても意味は重ならない。SKIPPED を失敗にするのは、bend 入りの CI で SKIPPED が出るのは承認行の失効か `laws:` のずれであり、Checks で見えるべきだから。
- **Rejected alternatives**: 案 B（週次 schedule / 手動 dispatch）— PR 単位で承認失効が見えないため却下。案 C（現状維持）— 同上。required にする — bend のリリース更新や GitHub Releases の障害で無関係な PR が止まるため却下（運用が安定したら再検討）。`install.sh` 経由で導入 — スクリプトの内容が変わりうるため再現性で tarball 直取得に劣り却下。macOS もマトリクスに加える — 証明の結果は OS に依存せず、コストだけ増えるため却下。`run-verification.py` の終了コードを PASS 以外で非 0 にする — スキル（run-checklist）が JSON を読む契約に触れるため、判定はシェル側に置いた。

## 2026-10-23 差分テストの `# source:` 照合を CI の `test` ジョブで必須にする

- **Decision**: 新規 `scripts/check-laws-tests.sh` が `tests/laws/test_*.py` を走査し、各ファイル先頭の `# spec: <id>` から spec を解決して `draft_laws.py check --tests <file> --spec <spec>` を実行し、error（`test_source_missing` / `test_source_drift` など）が 1 件でもあれば exit 1 にする。CI では `test` ジョブ（ubuntu / macOS）の 1 ステップとして実行し、required 扱いにする。`draft_laws.py check` 自体（常に exit 0 で JSON を返す契約）は変えない。
- **Rationale**: `check --tests` は `--spec` を省くと `# source:` の有無しか見ず、節ハッシュのずれを検出しない。手で正しい spec を渡す運用では忘れるため、テストファイルの `# spec:` ヘッダから機械的に解決する。bend 不要で数秒で終わるため optional ではなく required に置ける。spec を変えて `# source:` を更新し忘れた PR を落とすのが目的で、proof ジョブ（参照モデルの証明）とは独立に働く。
- **Rejected alternatives**: `draft_laws.py check` の終了コードを error 時に非 0 にする — スキル（draft-laws）が JSON を読む契約に触れるため、判定はシェル側に置いた。ファイル名から spec パスを導く — `test_quality_guardrails_constitution_injection.py` の `_` は `/` と `-` のどちらにも対応し一意に戻せないため、`# spec:` ヘッダを使う。proof ジョブに同居させる — bend 不要の検査を optional ジョブに置くと required にできないため却下。

## 2026-10-23 prose 実装の性質を plugin eval と skill-evals の 2 系統で検証する

- **Decision**: 法則化対象外（`prose_implementation`）にした 6 spec（prd-generation、quality-guardrails の front-matter-validation / impl-spec-check / doc-consistency-check / vibe-detection、spec-design/clarify）の性質を次の 2 系統で検証する（#227）。(1) 決定表の 1 行・不変条件 1 件のうち出力値を機械判定できるものは、Claude Code 公式の `claude plugin eval` のケースとしてプラグイン直下 `evals/<feature>/<property>/` に置く（32 ケース。`case.yaml` の `description` に spec の節、grader は regex のみ、fixture は `scaffold.sh`）。実行は `scripts/skill-evals.sh`（`--trust-plugin --scaffold --runs 1 --ablation none`）。CI には入れない（1 回の全件実行で $4〜5 のモデル課金が発生し、不安定ケースも残るため。手元で任意に実行する）。(2) 散文でしか表せない性質（根拠の整合・全順序の遵守・報告の形）は既存の `.claude/skill-evals/<skill>/evals.json` に assertion を追加する（vibe-detector / clarify / doc-consistency-checker に各 1 件）。役割分担は `ASSERTION_DESIGN.md` 末尾と `skill-evals/README.md` に記す。
- **Rationale**: 既存の `.claude/skill-evals/` は main → develop のリフト差を独立グレーダー agent で測る改善計測基盤で、決定表の行を置くと判定がぶれ 4 バリアント分のコストがかかる。`claude plugin eval` は 1 ケース 9〜30 秒・$0.07〜0.25、`--json` と exit code で CI に載る（2026-10-23 実測）。一方、「矛盾の正を上流に置く」のような性質は regex で表せない。両者を役割で分けることで、行の回帰検出は毎 PR、散文の性質は `/evaluate-skills` の手動計測で見る。パイロット（`vibe-detection/risk-level-exactly-one`）は UserPromptSubmit フックが発火してもモデルが vibe-detector のリスクレポートを出さない（2/2）という実装側の問題を検出した。同じ実験で `doc-consistency-checker`（同じく `user-invocable: false`）はプロンプトで名指しすれば `Skill` 経由で起動したため、原因はスキルの可視性ではなくフックの指示文にあると判断し、`user-prompt-submit.py` の注入文を「Skill ツールで `sdd-workflow:vibe-detector` を呼び、リスクレポートを出力してから実装する」と明示する形に改めた（同じチケットで修正）。
- **Rejected alternatives**: skill-evals のみ — CI で走らず LLM 判定で決定性が無いため却下。plugin eval のみ — 全順序や根拠の整合は regex で表せないため却下。`.claude/tests/harness/` — トークン計測用で assertion を持たないため却下。LLM judge を主にする — 判定が非決定的で、決定表の行の検証には過剰なため却下。評価ジョブの required 化 — LLM 呼び出しを含みコストと flakiness があるため、bend の proof ジョブと同じく optional に留めた。vibe-detector の起動問題を別 issue に切り出す — 原因がフックの 1 文に局所化でき、eval ケースを赤のまま merge すると optional ジョブが常に失敗して他の回帰が埋もれるため、同じチケットで修正した。`user-invocable: false` を外して手動呼び出し可能にする — 自動実行スキルという FR-004 の位置づけを変えるため見送った。
