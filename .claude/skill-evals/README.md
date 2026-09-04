# skill-evals

`plugins/sdd-workflow/skills/` 配下のスキルを評価・改善する際に使ったテストケースと、その評価手法を保存するディレクトリ。

`plugins/sdd-workflow/skills/<skill>/evals/` には置かない（`scripts/plugin-lint.sh` の Check 2 が `skills/*/` 配下の許可ディレクトリを `templates`/`examples`/`references`/`scripts` に限定しているため、`evals/` を置くとCIエラーになる）。

## 構成

```
.claude/skill-evals/
├── ASSERTION_DESIGN.md          # 評価手法の正典。assertion の設計基準と、そこに至った経緯
├── build_fixtures.py            # 世代別フィクスチャ生成（初期10スキル）
├── build_fixtures_2.py          # 同（残り9スキル）
├── build_fixtures_hard.py       # 同（高難度シナリオ：要求が互いに競合するケース）
└── <skill-name>/evals.json      # スキル別のプロンプト + assertion
```

## 評価手法（v2）

**assertion はバージョン中立に書く。** 特定世代のファイルパス・フィールド名・語彙を assertion に埋め込むと、
スキルの品質ではなく世代差を測ってしまう。判定基準と、初期設計（v1）で何を誤ったかは
`ASSERTION_DESIGN.md` が正典。**`evals.json` の assertion を書き換える際は必ず先にこれを読むこと。**

**フィクスチャは世代別に用意する。** `old`（v5.0.0以前のレイアウト）と `new`（現行レイアウト）でそれぞれ
別のフィクスチャツリーを作り、各スキルを「自分の時代の世界」で評価する。生成は `build_fixtures*.py` が担う。

**比較は同一世代内でのみ有効。** `old/skill` vs `old/without`、または `new/skill` vs `new/without`。
`old/without` と `new/without` の比較は**してはならない** — どちらもスキルを持たないため、その差は
スキルについて何も語らない。同様に、世代間で同一 variant を比較して「モデルの世代差」と解釈することもできない
（世代の違いは SKILL.md のスナップショットとフィクスチャのレイアウトだけで、モデルは同一）。

## 今後の使い方

同じスキルを再評価・改善する際、`evals.json` のプロンプトをベースラインとして再利用できる。
assertion は `ASSERTION_DESIGN.md` の判定基準に照らして毎回見直す（スキルの責務が変わっていれば assertion も変わる）。
