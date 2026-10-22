# spec: spec-quality-guardrails-stale-doc-detection
# model-of: plugins/sdd-workflow/scripts/post-tool-use.py
#
# 承認済み LAWS.bend (sha256:568e042f05d2) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

# path_kind 0..6 を通知カテゴリへ恒等的に対応づけ（決定表 3.1.1）、範囲外は 7（FR-005 出力なし）。
def category_for_path(path_kind: Nat) -> Nat:
  match path_kind:
    case 0n:
      0n
    case 1n+p1:
      match p1:
        case 0n:
          1n
        case 1n+p2:
          match p2:
            case 0n:
              2n
            case 1n+p3:
              match p3:
                case 0n:
                  3n
                case 1n+p4:
                  match p4:
                    case 0n:
                      4n
                    case 1n+p5:
                      match p5:
                        case 0n:
                          5n
                        case 1n+p6:
                          match p6:
                            case 0n:
                              6n
                            case 1n+p7:
                              7n

def main() -> Nat:
  category_for_path(7n)
