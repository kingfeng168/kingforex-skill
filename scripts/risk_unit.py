#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金管控工具箱(Capital / Money Management Toolkit)

子命令:
  kelly       凯利公式 → 最优分数 f* / 半凯利 / 封顶后风险%(封顶默认 1%)
  expectancy  期望值(以 R 倍数计) → 每笔 E(R) 与 正/负期望判定
  drawdown    回撤降仓查表 → 当前回撤对应的单笔风险% 与 总风险上限
  ruin        固定分数法破产风险蒙特卡洛模拟 → 破产概率与存活轮平均最大回撤

纯标准库,无外部依赖。所有金额默认账户币 USD。

用法:
  python risk_unit.py kelly --win 0.55 --payoff 1.8
  python risk_unit.py expectancy --win 0.55 --avgwin 2.0 --avgloss 1.0
  python risk_unit.py drawdown --dd 12
  python risk_unit.py ruin --win 0.45 --risk 1 --trades 200 --runs 5000 --seed 7
"""
import argparse
import random

# 回撤降仓阶梯: (回撤下限%, 单笔风险%, 总风险上限%)
DRAWDOWN_LADDER = [
    (0.0,  1.0, 5.0),
    (5.0,  0.75, 4.0),
    (10.0, 0.5, 3.0),
    (15.0, 0.25, 2.0),
    (20.0, 0.0, 0.0),
]
RISK_CAP = 1.0  # 单笔风险硬封顶(%)


def cmd_kelly(args):
    W = args.win
    R = args.payoff
    if not (0 < W < 1):
        print("胜率 W 须介于 0 与 1 之间(如 0.55)")
        return
    if R <= 0:
        print("盈亏比 R 须为正数")
        return
    f_star = W - (1 - W) / R
    half = f_star / 2.0
    # 实战硬封顶: 全凯利与半凯利一律不得突破 RISK_CAP(本技能 1%, 以百分比数值计)
    f_star_pct = f_star * 100.0
    half_pct = half * 100.0
    full_after_cap = min(max(f_star_pct, 0.0), RISK_CAP)
    half_after_cap = min(max(half_pct, 0.0), RISK_CAP)
    print("=" * 52)
    print("凯利公式 (Kelly Criterion)")
    print(f"  胜率 W        : {W:.2f}")
    print(f"  盈亏比 R      : {R:.2f}")
    print(f"  最优分数 f*   : {f_star*100:.2f}%  (全凯利, 实战过激)")
    print(f"  半凯利 f*/2   : {half*100:.2f}%  (较稳健)")
    print(f"  实战硬封顶(≤{RISK_CAP:.0f}%): 全凯利封顶={full_after_cap:.2f}%  半凯利封顶={half_after_cap:.2f}%")
    print("-" * 52)
    print(f"建议: 取 min(半凯利, {RISK_CAP:.0f}% 封顶) = {half_after_cap:.2f}% 作为单笔风险上限")
    if f_star <= 0:
        print("⚠ f*≤0: 此系统无正期望, 不应交易(先提升 W 或 R)")
    print("=" * 52)


def cmd_expectancy(args):
    W = args.win
    aw = args.avgwin
    al = args.avgloss
    if not (0 < W < 1):
        print("胜率 W 须介于 0 与 1 之间")
        return
    if aw <= 0 or al <= 0:
        print("平均盈利/亏损(R)须为正数")
        return
    E = W * aw - (1 - W) * al
    print("=" * 52)
    print("期望值 (Expectancy, 以 R 倍数计)")
    print(f"  胜率 W        : {W:.2f}")
    print(f"  平均盈利      : {aw:.2f} R")
    print(f"  平均亏损      : {al:.2f} R")
    print(f"  每笔期望 E    : {E:+.2f} R")
    if E > 0:
        print(f"  ✓ 正期望: 长期靠复利放大; 100 笔≈ {E*100:+.0f} R")
    else:
        print("  ⚠ 负期望: 系统长期必亏, 需优化信号/止损/盈亏比")
    print("=" * 52)


def cmd_drawdown(args):
    dd = args.dd
    row = DRAWDOWN_LADDER[0]
    for r in DRAWDOWN_LADDER:
        if dd >= r[0]:
            row = r
    print("=" * 52)
    print(f"回撤降仓查表 (当前回撤 = {dd:.1f}%)")
    print(f"  单笔风险%   : {row[1]:.2f}")
    print(f"  总风险上限% : {row[2]:.2f}")
    print("-" * 52)
    print("阶梯(回撤下限 → 单笔/总风险):")
    for lo, sr, tr in DRAWDOWN_LADDER:
        mark = "  <-- 当前" if lo == row[0] else ""
        print(f"  ≥{lo:>4.0f}%  →  单笔 {sr:.2f}% / 总 {tr:.2f}%{mark}")
    print("=" * 52)


def cmd_ruin(args):
    W = args.win
    risk = args.risk / 100.0
    payoff = args.payoff
    trades = args.trades
    runs = args.runs
    rnd = random.Random(args.seed)
    ruins = 0
    max_dd_list = []
    for _ in range(runs):
        equity = 1.0
        peak = 1.0
        ruined = False
        for _ in range(trades):
            if rnd.random() < W:
                equity *= (1.0 + risk * payoff)   # 盈利 = 风险×盈亏比(占净值)
            else:
                equity *= (1.0 - risk)            # 亏损 = 风险(占净值)
            if equity <= 0:
                ruined = True
                break
            if equity > peak:
                peak = equity
        if ruined:
            ruins += 1
        else:
            max_dd_list.append((peak - equity) / peak)
    p_ruin = ruins / runs
    avg_dd = (sum(max_dd_list) / len(max_dd_list)) if max_dd_list else 0.0
    print("=" * 52)
    print("破产风险蒙特卡洛模拟 (固定分数法)")
    print(f"  胜率 W        : {W:.2f}")
    print(f"  单笔风险      : {args.risk:.2f}% (净值)")
    print(f"  盈亏比 R      : {payoff:.2f}")
    print(f"  模拟规模      : {trades} 笔 × {runs} 轮 (seed={args.seed})")
    print(f"  破产概率      : {p_ruin*100:.2f}%")
    if max_dd_list:
        print(f"  存活轮平均最大回撤: {avg_dd*100:.2f}%")
    print("-" * 52)
    if p_ruin > 0.05:
        print(f"⚠ 破产概率偏高({p_ruin*100:.1f}%): 降低风险% 或提升 W/R")
    else:
        print(f"✓ 破产概率低: 小风险% + 正期望 = 长期存活")
    print("=" * 52)


def build_parser():
    ap = argparse.ArgumentParser(description="资金管控工具箱(凯利/期望值/回撤降仓/破产风险)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_k = sub.add_parser("kelly", help="凯利公式 → 最优分数/半凯利/封顶")
    p_k.add_argument("--win", type=float, required=True, help="胜率(0–1, 如 0.55)")
    p_k.add_argument("--payoff", type=float, default=1.8, help="盈亏比 R(平均盈利/平均亏损), 默认 1.8")
    p_k.set_defaults(func=cmd_kelly)

    p_e = sub.add_parser("expectancy", help="期望值(以 R 倍数计)")
    p_e.add_argument("--win", type=float, required=True, help="胜率(0–1)")
    p_e.add_argument("--avgwin", type=float, default=2.0, help="平均盈利(R), 默认 2.0")
    p_e.add_argument("--avgloss", type=float, default=1.0, help="平均亏损(R), 默认 1.0")
    p_e.set_defaults(func=cmd_expectancy)

    p_d = sub.add_parser("drawdown", help="回撤降仓查表")
    p_d.add_argument("--dd", type=float, required=True, help="当前回撤百分比(如 12 表示 12%)")
    p_d.set_defaults(func=cmd_drawdown)

    p_r = sub.add_parser("ruin", help="固定分数法破产风险蒙特卡洛")
    p_r.add_argument("--win", type=float, required=True, help="胜率(0–1)")
    p_r.add_argument("--risk", type=float, default=1.0, help="单笔风险%(净值), 默认 1")
    p_r.add_argument("--payoff", type=float, default=2.0, help="盈亏比 R, 默认 2.0")
    p_r.add_argument("--trades", type=int, default=200, help="每轮模拟笔数, 默认 200")
    p_r.add_argument("--runs", type=int, default=5000, help="模拟轮数, 默认 5000")
    p_r.add_argument("--seed", type=int, default=7, help="随机种子(可复现), 默认 7")
    p_r.set_defaults(func=cmd_ruin)

    return ap


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
