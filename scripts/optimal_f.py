#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
optimal_f.py — 最优 f 仓位计算引擎（Ralph Vince《资金管理数学》方法 + 蒙特卡洛回撤模拟）

核心问题:给定历史逐笔盈亏序列,求"使长期几何增长率最大"的仓位分数 f*,
并在该 f* 与分数 f(1/4、1/2)下用蒙特卡洛估计最大回撤分布与破产风险。

数学(Ralph Vince):
    W       = |最大单笔亏损|(正数)
    HPR_i(f)= 1 + f * (P_i / W)            # 每笔"持有期收益"倍数
    TWR(f)  = ∏ HPR_i(f)                   # 期末财富倍数
    G(f)    = TWR(f) ^ (1/N)               # 几何平均收益/笔(唯一该最大化的目标)
    f*      = argmax G(f)                  # 最优 f

与凯利的关系:凯利 f* = p - (1-p)/b 假设收益服从特定分布;Vince 最优 f 直接用
历史序列数值搜索,不依赖分布假设,因此更能反映厚尾真实风险——但也更易过拟合。

用法:
  --csv <path>          CSV,含 pnl/return 列(逐笔盈亏,可正可负)
  --text <...>          粘贴逐笔盈亏(每行一个数)
  --mc 10000            蒙特卡洛模拟次数(默认 10000)
  --json                输出结构化 JSON
"""

import argparse
import csv
import json
import math
import random
import sys

# ---------------------------------------------------------------------------
# 数据载入
# ---------------------------------------------------------------------------

def load_pnl(path=None, text=None):
    vals = []
    if path:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                fields = {fn.strip().lower(): fn for fn in reader.fieldnames}
                col = fields.get("pnl") or fields.get("profit") or fields.get("return") or fields.get("p_l")
            else:
                col = None
            for row in reader:
                try:
                    key = col or reader.fieldnames[0]
                    v = float(str(row[key]).replace(",", "").strip())
                except (KeyError, ValueError, TypeError, IndexError):
                    continue
                vals.append(v)
    elif text:
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                vals.append(float(line.replace(",", "").strip()))
            except ValueError:
                continue
    return vals

# ---------------------------------------------------------------------------
# Vince 最优 f
# ---------------------------------------------------------------------------

def optimal_f(pnl, steps=500):
    """网格搜索最大化几何增长率 G(f)。返回 f*, G*, TWR*, G 曲线。"""
    n = len(pnl)
    if n < 3:
        return None
    worst = min(pnl)
    if worst >= 0:
        return None  # 无亏损,不存在最优 f(风险为 0)
    W = -worst
    best_f = 0.0
    best_G = 1.0
    curve = []
    for i in range(1, steps):
        f = i / steps
        # 若 f 过大导致某笔 HPR <= 0,几何增长率无意义,跳过
        twr = 1.0
        valid = True
        for p in pnl:
            hpr = 1.0 + f * (p / W)
            if hpr <= 0:
                valid = False
                break
            twr *= hpr
        if not valid:
            break
        g = twr ** (1.0 / n)
        curve.append((f, g))
        if g > best_G:
            best_G = g
            best_f = f
    return {
        "f_optimal": best_f,
        "G_optimal": best_G,
        "TWR_optimal": best_G ** n,
        "worst_loss": worst,
        "W": W,
        "n_trades": n,
        "curve": curve,
    }

def twr_at_f(pnl, f, W):
    twr = 1.0
    for p in pnl:
        hpr = 1.0 + f * (p / W)
        if hpr <= 0:
            return 0.0
        twr *= hpr
    return twr

# ---------------------------------------------------------------------------
# 蒙特卡洛回撤 / 破产风险
# ---------------------------------------------------------------------------

def monte_carlo(pnl, f, W, n_runs=10000, ruin_threshold=0.5, seed=42):
    """按 f 重采样逐笔收益,模拟 n_runs 条资金曲线,返回回撤分布与破产概率。
    ruin_threshold: 权益跌破峰值 * threshold 即记一次破产(如 0.5 = 腰斩)。"""
    rng = random.Random(seed)
    n = len(pnl)
    if n == 0:
        return None
    max_dds = []
    ruins = 0
    runs_done = 0
    for _ in range(n_runs):
        equity = 1.0
        peak = 1.0
        max_dd = 0.0
        broke = False
        for _ in range(n):
            p = pnl[rng.randrange(n)]
            hpr = 1.0 + f * (p / W)
            if hpr <= 0:
                hpr = 0.0
            equity *= hpr
            if equity <= 0:
                equity = 0.0
            if equity > peak:
                peak = equity
            dd = (equity / peak - 1.0) if peak > 0 else -1.0
            if dd < max_dd:
                max_dd = dd
            if peak > 0 and equity < peak * ruin_threshold:
                broke = True
                # 一旦破产(腰斩),记录后跳出该条曲线
                break
        runs_done += 1
        max_dds.append(max_dd)
        if broke:
            ruins += 1
    if not max_dds:
        return None
    max_dds.sort()  # 升序:最负(最深回撤)在前
    n_dd = len(max_dds)
    def quantile(q):
        """q∈[0,1]:返回'低于该值的比例 = q'的分位点(升序数组)。"""
        k = max(0, min(n_dd - 1, int(round(q * (n_dd - 1)))))
        return max_dds[k]
    avg_dd = sum(max_dds) / n_dd
    # 语义:95% 的曲线最大回撤"轻于" p95(即只有 5% 更深)→ 取 5% 分位
    #       99% 轻于 p99 → 取 1% 分位
    return {
        "n_runs": runs_done,
        "avg_max_dd": avg_dd,
        "median_max_dd": quantile(0.50),
        "p95_max_dd": quantile(0.05),
        "p99_max_dd": quantile(0.01),
        "worst_max_dd": max_dds[0],
        "ruin_prob": ruins / runs_done if runs_done else 0.0,
        "ruin_threshold": ruin_threshold,
    }

# ---------------------------------------------------------------------------
# 报告
# ---------------------------------------------------------------------------

def fmt_pct(x, d=2):
    return f"{x*100:.{d}f}%" if x is not None else "—"

def render_report(of, mc_full, mc_quarter, mc_half):
    L = []
    L.append("=" * 64)
    L.append("  最优 f 仓位计算报告(Ralph Vince + 蒙特卡洛)")
    L.append("=" * 64)
    if of is None:
        L.append("  无法计算:样本 < 3 笔,或不存在亏损(风险为 0)。")
        return "\n".join(L)
    L.append(f"样本笔数         {of['n_trades']}")
    L.append(f"最大单笔亏损     {of['worst_loss']:.2f}(W = {of['W']:.2f})")
    L.append(f"最优 f           {fmt_pct(of['f_optimal'])}")
    L.append(f"几何增长率/笔   {fmt_pct(of['G_optimal'] - 1)}")
    L.append(f"期末财富倍数 TWR {of['TWR_optimal']:.4f}")
    L.append("")
    L.append("【分数 f 建议(实际交易必须折扣)】")
    L.append(f"  1/4 最优 f = {fmt_pct(of['f_optimal'] / 4)}")
    L.append(f"  1/2 最优 f = {fmt_pct(of['f_optimal'] / 2)}")
    L.append("  全 f(不建议) = " + fmt_pct(of['f_optimal']))
    L.append("")
    L.append("【蒙特卡洛回撤/破产风险(重采样 " + (str(mc_full['n_runs']) if mc_full else "—") + " 次)】")
    L.append("  ┌────────────┬──────────┬──────────┬──────────┐")
    L.append("  │ 指标        │ 全 f      │ 1/2 f     │ 1/4 f     │")
    L.append("  ├────────────┼──────────┼──────────┼──────────┤")
    def row(label, k):
        a = mc_full[k] if mc_full else None
        b = mc_half[k] if mc_half else None
        c = mc_quarter[k] if mc_quarter else None
        fmt = fmt_pct
        return f"  │ {label:<10} │ {fmt(a):>8} │ {fmt(b):>8} │ {fmt(c):>8} │"
    L.append(row("平均回撤", "avg_max_dd"))
    L.append(row("中位回撤", "median_max_dd"))
    L.append(row("P95 回撤", "p95_max_dd"))
    L.append(row("P99 回撤", "p99_max_dd"))
    L.append(row("最坏回撤", "worst_max_dd"))
    L.append(row("破产概率", "ruin_prob"))
    L.append("  └────────────┴──────────┴──────────┴──────────┘")
    L.append("")
    L.append("解读: 破产概率 = 权益跌破峰值 50%(腰斩)的概率。")
    L.append("  全 f 破产概率通常 > 30%(必爆);1/4 f 常 < 5%(可承受)。")
    L.append("  手工交易者建议取 1/4 f 且不超过单笔风险 1% 上限。")
    L.append("=" * 64)
    return "\n".join(L)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="最优 f 仓位计算(Ralph Vince + 蒙特卡洛)")
    ap.add_argument("--csv", help="逐笔盈亏 CSV(含 pnl/profit/return 列)")
    ap.add_argument("--text", help="粘贴逐笔盈亏(每行一个数)")
    ap.add_argument("--mc", type=int, default=10000, help="蒙特卡洛模拟次数")
    ap.add_argument("--ruin-threshold", type=float, default=0.5, help="破产阈值(权益/峰值)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    pnl = load_pnl(args.csv, args.text)
    if len(pnl) < 3:
        sys.stderr.write(f"ERROR: 逐笔盈亏样本不足 3 笔(当前 {len(pnl)})\n")
        sys.exit(2)
    if min(pnl) >= 0:
        sys.stderr.write("ERROR: 无亏损笔,风险为 0,不存在最优 f\n")
        sys.exit(2)

    of = optimal_f(pnl)
    if of is None:
        sys.stderr.write("ERROR: 无法计算最优 f\n")
        sys.exit(2)

    W = of["W"]
    f_full = of["f_optimal"]
    mc_full = monte_carlo(pnl, f_full, W, args.mc, args.ruin_threshold, args.seed)
    mc_half = monte_carlo(pnl, f_full / 2, W, args.mc, args.ruin_threshold, args.seed)
    mc_quarter = monte_carlo(pnl, f_full / 4, W, args.mc, args.ruin_threshold, args.seed)

    if args.json:
        out = {
            "n_trades": of["n_trades"],
            "worst_loss": of["worst_loss"],
            "f_optimal": of["f_optimal"],
            "G_optimal": of["G_optimal"],
            "TWR_optimal": of["TWR_optimal"],
            "fractional_f": {
                "quarter": of["f_optimal"] / 4,
                "half": of["f_optimal"] / 2,
                "full": of["f_optimal"],
            },
            "monte_carlo": {
                "full_f": mc_full,
                "half_f": mc_half,
                "quarter_f": mc_quarter,
            },
        }
        print(json.dumps(out, ensure_ascii=False, indent=2, default=lambda o: round(o, 6) if isinstance(o, float) else str(o)))
    else:
        print(render_report(of, mc_full, mc_quarter, mc_half))

if __name__ == "__main__":
    main()
