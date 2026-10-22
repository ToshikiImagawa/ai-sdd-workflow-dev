# spec: spec-spec-design-clarify
#
# main.bend の参照モデルに対する LAWS.bend の証明。
# 乗算の結合性などの補題を経て、閾値 80%（5*clear >= 4*total）の等号成立を示す。

import Base
import ./main.bend as Model
import ./LAWS.bend as Laws

def add_zero_r(+a: Nat) -> {Model.add(a, 0n) == a : Nat}:
  match a:
    case 0n:
      {==}
    case 1n+p:
      %add_zero_r(p) : {1n+Model.add(p, 0n) == 1n+_ : Nat}
      {==}

def add_succ_r(+a: Nat, +b: Nat) -> {Model.add(a, 1n+b) == 1n+Model.add(a, b) : Nat}:
  match a:
    case 0n:
      {==}
    case 1n+p:
      %add_succ_r(p, b) : {1n+Model.add(p, 1n+b) == 1n+_ : Nat}
      {==}

def add_succ_r_rev(+a: Nat, +b: Nat) -> {1n+Model.add(a, b) == Model.add(a, 1n+b) : Nat}:
  match a:
    case 0n:
      {==}
    case 1n+p:
      %add_succ_r_rev(p, b) : {1n+1n+Model.add(p, b) == 1n+_ : Nat}
      {==}

def add_assoc(+a: Nat, +b: Nat, +c: Nat) -> {Model.add(Model.add(a, b), c) == Model.add(a, Model.add(b, c)) : Nat}:
  match a:
    case 0n:
      {==}
    case 1n+p:
      %add_assoc(p, b, c) : {1n+Model.add(Model.add(p, b), c) == 1n+_ : Nat}
      {==}

def add_comm(+a: Nat, +b: Nat) -> {Model.add(a, b) == Model.add(b, a) : Nat}:
  match a:
    case 0n:
      %add_zero_r(b) : {_ == Model.add(b, 0n) : Nat}
      {==}
    case 1n+p:
      %add_succ_r_rev(b, p) : {1n+Model.add(p, b) == _ : Nat}
      %add_comm(p, b) : {1n+Model.add(p, b) == 1n+_ : Nat}
      {==}

def mul_add_r(+a: Nat, +b: Nat, +c: Nat) -> {Model.add(Model.mul(a, c), Model.mul(b, c)) == Model.mul(Model.add(a, b), c) : Nat}:
  match a:
    case 0n:
      {==}
    case 1n+p:
      %mul_add_r(p, b, c) : {Model.add(Model.add(c, Model.mul(p, c)), Model.mul(b, c)) == Model.add(c, _) : Nat}
      %add_assoc(c, Model.mul(p, c), Model.mul(b, c)) : {Model.add(Model.add(c, Model.mul(p, c)), Model.mul(b, c)) == _ : Nat}
      {==}

def mul_assoc(+a: Nat, +b: Nat, +c: Nat) -> {Model.mul(Model.mul(a, b), c) == Model.mul(a, Model.mul(b, c)) : Nat}:
  match a:
    case 0n:
      {==}
    case 1n+p:
      %mul_add_r(b, Model.mul(p, b), c) : {_ == Model.add(Model.mul(b, c), Model.mul(p, Model.mul(b, c))) : Nat}
      %mul_assoc(p, b, c) : {Model.add(Model.mul(b, c), Model.mul(Model.mul(p, b), c)) == Model.add(Model.mul(b, c), _) : Nat}
      {==}

def mul_swap_45(+r: Nat) -> {Model.mul(4n, Model.mul(5n, r)) == Model.mul(5n, Model.mul(4n, r)) : Nat}:
  %mul_assoc(4n, 5n, r) : {_ == Model.mul(5n, Model.mul(4n, r)) : Nat}
  %mul_assoc(5n, 4n, r) : {Model.mul(Model.mul(4n, 5n), r) == _ : Nat}
  {==}

def le_refl(+x: Nat) -> {Model.le(x, x) == True{} : Bool}:
  match x:
    case 0n:
      {==}
    case 1n+p:
      le_refl(p)

def le_add(+x: Nat, +t: Nat) -> {Model.le(x, Model.add(x, t)) == True{} : Bool}:
  match x:
    case 0n:
      {==}
    case 1n+p:
      le_add(p, t)

def judge_exact(+r: Nat) -> {Model.judge(Model.mul(4n, r), Model.mul(5n, r)) == True{} : Bool}:
  %mul_swap_45(r) : {Model.le(Model.mul(4n, Model.mul(5n, r)), _) == True{} : Bool}
  le_refl(Model.mul(4n, Model.mul(5n, r)))

def judge_full(+t: Nat) -> {Model.judge(t, t) == True{} : Bool}:
  %add_comm(Model.mul(4n, t), t) : {Model.le(Model.mul(4n, t), _) == True{} : Bool}
  le_add(Model.mul(4n, t), t)

def Laws.judge_exact_threshold_passes(r):
  judge_exact(r)

def Laws.judge_full_match_passes(t):
  judge_full(t)
