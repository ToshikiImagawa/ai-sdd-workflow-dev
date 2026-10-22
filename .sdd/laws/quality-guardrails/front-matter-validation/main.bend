# spec: spec-quality-guardrails-front-matter-validation
# model-of: plugins/sdd-workflow/agents/front-matter-reviewer.md
#
# 承認済み LAWS.bend (sha256:1a0efcce0923) を満たすよう書いた参照モデル。
# 実装ではなく小さな純粋関数での書き直し。LAWS.bend の '# model-api:' 行に厳密に従う。

import Base

# severity codes: 0=error, 1=warning, 2=info
# check_id 3..8 = error, 9..11 = warning, それ以外（16 含む）= info
def severity_for_check(check_id: Nat) -> Nat:
  match check_id:
    case 0n:
      2n
    case 1n+p1:
      match p1:
        case 0n:
          2n
        case 1n+p2:
          match p2:
            case 0n:
              2n
            case 1n+p3:
              match p3:
                case 0n:
                  0n
                case 1n+p4:
                  match p4:
                    case 0n:
                      0n
                    case 1n+p5:
                      match p5:
                        case 0n:
                          0n
                        case 1n+p6:
                          match p6:
                            case 0n:
                              0n
                            case 1n+p7:
                              match p7:
                                case 0n:
                                  0n
                                case 1n+p8:
                                  match p8:
                                    case 0n:
                                      0n
                                    case 1n+p9:
                                      match p9:
                                        case 0n:
                                          1n
                                        case 1n+p10:
                                          match p10:
                                            case 0n:
                                              1n
                                            case 1n+p11:
                                              match p11:
                                                case 0n:
                                                  1n
                                                case 1n+_:
                                                  2n

def main() -> Nat:
  severity_for_check(16n)
