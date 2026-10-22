---
name: plugin-evals
description: "plugins/sdd-workflow/evals/ の plugin eval ケース（prose 実装 spec の決定表 1 行 = 1 ケース）を Claude Code 公式の `claude plugin eval` で手元実行し、pass/fail・落ちた grader・コストを整形して報告する。ユーザーが「plugin eval を回して」「evals を実行して」「eval スイートを流して」「check-spec（や front-matter-reviewer、vibe-detector、doc-consistency-checker、generate-prd、clarify）を直したので spec どおり動くか確認して」「決定表の行が守られているか確かめて」と言ったとき、および prose 実装のスキル・エージェント・フック（user-prompt-submit）やそのテンプレートを変更した PR の仕上げで必ず使用する。モデル呼び出しに課金が発生するため CI には入れておらず、このスキルが唯一の実行経路。main→develop のリフト差を測る evaluate-skills（.claude/skill-evals/）とは別物で、こちらは spec 準拠の合否だけを見る。"
license: MIT
argument-hint: "[--case '<feature>/*' | --case '<feature>/<property>'] [--tag <tag>] [--keep-temp]"
allowed-tools: Read, Glob, Grep, Bash(bash .claude/skills/plugin-evals/scripts/run_evals.sh *)
disable-model-invocation: true
---

# Plugin Evals — spec 決定表の回帰確認

`plugins/sdd-workflow/evals/<feature>/<property>/` の各ケースは、Bend 法則化の対象外にした prose 実装 spec
（prd-generation / front-matter-validation / impl-spec-check / doc-consistency-check / vibe-detection / clarify）の
決定表 1 行または不変条件 1 件に対応する。`case.yaml` の `description` が spec の節を指し、grader は regex のみ
（判定を決定的にするため LLM judge は使わない）。このスキルはそれを実行し、結果を読める形にする。

実行は実際に Claude を呼ぶので課金が発生する（1 ケース約 $0.1〜0.3・10〜30 秒、全 32 ケースで約 $4〜5・5 分）。
CI には入れていない。認証は実行者の Claude Code ログインがそのまま使われる（API キーは不要）。

## 手順

最初に `references/known_unstable_cases.md` を読む。手順 3 で失敗ケースを「既知の揺れ」かどうか判断するのに使う。

### 1. 対象を絞る

変更したものに対応する feature だけ流すのが基本。何を直したか分かっているなら全件は要らない。

| 変更したもの | `--case` |
|:--|:--|
| `skills/check-spec/` | `'impl-spec-check/*'`（5 ケース） |
| `agents/front-matter-reviewer.md`、`shared/templates/*/front_matter_validation_report.md` | `'front-matter-validation/*'`（19 ケース・約 $2） |
| `skills/doc-consistency-checker/` | `'doc-consistency-check/*'`（3 ケース） |
| `skills/vibe-detector/`、`scripts/user-prompt-submit.py` | `'vibe-detection/*'`（1 ケース） |
| `skills/generate-prd/`（`--amend` の採番） | `'prd-generation/*'`（2 ケース） |
| `skills/clarify/` | `'clarify/*'`（2 ケース） |
| リリース前の全件確認 | 引数なし |

`--case` は 1 つしか効かない（複数指定すると最後だけが使われる）。複数 feature を見るときは回数を分けて実行する。

### 2. 実行する

```
bash .claude/skills/plugin-evals/scripts/run_evals.sh --case '<feature>/*'
```

スクリプトは `claude plugin eval ./plugins/sdd-workflow --trust-plugin --scaffold --runs 1 --ablation none
--no-publish --max-cost-usd 5 --json <out>` を実行し、結果 JSON を要約して stderr に出す。終了コードは CLI のまま
（0 全 pass / 1 閾値未満か読込エラー / 2 コスト上限）だが、合否は要約行 `passed N/M` で読めば足りる（N = M なら 0。
パイプを挟むと終了コードが取りにくいので、そこで判定しなくてよい）。追加の環境変数と引数の詳細はスクリプト先頭の
コメントを参照。

- `--scaffold` は各ケースの `scaffold.sh`（本リポジトリが作成した fixture）を実行者権限で走らせる。本リポジトリの
  ケース以外に向けて使わない
- 失敗ケースの最終出力を見たいときは `--keep-temp` を付ける。残った `/private/tmp/e-*/out/trace.jsonl` は
  `chmod 700` してから読む（結果 JSON の `tracePath` は `--keep-temp` 無しだと既に消えている）
- 結果は `plugins/sdd-workflow/evals/results/`（`.gitignore` 済み）に残る。コミットしない

### 3. 結果を報告する

スクリプトの要約（`plugin-evals: passed N/M cases, cost $X, Ys`）と `FAIL <case>: <grader>` 行をもとに、次の表で報告する。

```
| ケース | 結果 | 落ちた grader | 判断 |
|:--|:--|:--|:--|
```

pass したケースは「判断」を **問題なし** とし、落ちた grader は「なし」と書く。落ちたケースの「判断」は次の 3 つのどれかにする。

- **既知の揺れ**: `references/known_unstable_cases.md` に載っているケースで、同じ grader が落ちた。`--runs 1` で
  起きる出力の揺れなので、変更が原因ではない。再実行で緑になることが多い
- **実装の退行の疑い**: 既知でないケースが落ちた、または既知ケースでも別の grader が落ちた。spec の該当行
  （`case.yaml` の `description`）とスキル・エージェントの変更差分を突き合わせて報告する。自動では直さない
- **grader の誤り**: `--keep-temp` で見た最終出力は spec どおりなのに regex が一致していない。ケース側の修正提案を
  出す（ケースの生成元・設計規約は `.sdd/task/227/skill-evals-investigation.md` と
  `.sdd/adr/task-implementation/proof-gate.md` の 2026-10-23 エントリ）

コストと所要時間も必ず添える。ユーザーが次に全件を流すか判断する材料になる。

## やらないこと

- 落ちたケースに合わせてスキル・エージェント・grader を自動修正すること（提案までに留める）
- CI への組み込み提案（オーナー判断で入れないと決めている。理由は上の課金）
- `.claude/skill-evals/`（evaluate-skills）の assertion の実行。散文でしか表せない性質はあちらが担う
