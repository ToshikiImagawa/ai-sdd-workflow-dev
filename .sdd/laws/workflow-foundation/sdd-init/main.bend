# spec: spec-workflow-foundation-sdd-init
# model-of: plugins/sdd-workflow/skills/sdd-init/scripts/update-claude-md.py
#
# 承認済み LAWS.bend (sha256:e106785a632c 系) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

# CLAUDE.md への AI-SDD セクション反映の判定（sdd-init_spec 3.1.1）
# 0n = append（追記）, 1n = skip（変更なし）, 2n = replace（置換）
def claude_md_action(has_section: Bool, version_match: Bool) -> Nat:
  match has_section:
    case False{}:
      0n
    case True{}:
      match version_match:
        case True{}:
          1n
        case False{}:
          2n

def main() -> Nat:
  claude_md_action(True{}, False{})
