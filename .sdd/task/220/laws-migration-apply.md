# 法則 移行表の適用記録（#220）

- 実施日: 2026-10-22
- 入力: [laws-migration-report.md](../218/laws-migration-report.md)（#218 の移行表）
- 決定の記録: [proof-gate.md](../../adr/task-implementation/proof-gate.md) 2026-10-22 エントリ「移行表を適用し、法則を全称法則 6 件に整理する」

## 実施内容

| 区分 | 対象 | 結果 |
|:--|:--|:--|
| prose_delete | prd-generation / doc-consistency-check / front-matter-validation / impl-spec-check / vibe-detection / clarify | 法則ディレクトリ削除、spec の `laws:` / `laws-status:` 除去、`impl-of:` 追記 |
| to_tests（全件） | constitution-injection / naming-enforcement / stale-doc-detection | 法則ディレクトリ削除（差分テスト `tests/laws/` が引き継ぐ）、spec 同上 |
| to_tests（一部） | sdd-init（2 件）/ session-config（6 件） | 点命題を `LAWS.bend` / `PROOF.bend` / `main.bend` から削除、`laws-status` を `drafted` に |
| keep | proof-gate（5 件） | 変更なし。`impl-of:` のみ追記 |

## 人の作業（承認者）

承認行を `LAWS.bend` の先頭コメント部に追記する（書式 `# approved: YYYY-MM-DD <承認者> sha256:<12 桁>`）。
AI は承認行を書かない。

| laws dir | 新しい内容ハッシュ | 残る法則 |
|:--|:--|:--|
| `.sdd/laws/workflow-foundation/sdd-init` | `80492540b53d` | `no_section_appends` |
| `.sdd/laws/workflow-foundation/session-config` | `feb456f599fb` | `config_wins` |

承認後に spec の `laws-status` を `approved` にし、`/run-checklist <feature> 220 --category proof` が PASS したら `proven` にする。
