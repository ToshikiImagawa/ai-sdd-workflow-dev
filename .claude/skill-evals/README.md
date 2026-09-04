# skill-evals

`skill-creator` を使って `plugins/sdd-workflow/skills/` 配下のスキルを評価・改善する際に使ったテストケース（プロンプト + assertions）を保存するディレクトリ。

`plugins/sdd-workflow/skills/<skill>/evals/` には置かない（`scripts/plugin-lint.sh` の Check 2 が `skills/*/` 配下の許可ディレクトリを `templates`/`examples`/`references`/`scripts` に限定しているため、`evals/` を置くとCIエラーになる）。

## 構成

```
.claude/skill-evals/<skill-name>/evals.json
```

`evals.json` のスキーマは `skill-creator` の `references/schemas.md` に準拠（`id` / `prompt` / `expected_output` / `files` / `assertions`）。

## 今後の使い方

同じスキルを再度 `skill-creator` で作り直す・改善する際、この `evals.json` をベースラインのテストケースとして再利用できる（プロンプトを流用し、assertions を必要に応じて更新する）。
