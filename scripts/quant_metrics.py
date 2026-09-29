#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quant_metrics.py — 金融工程/量化分析指标计算引擎（纯标准库）

基于价格序列（CSV/粘贴文本/--fetch）输出：
  1) 收益度量：对数收益率、年化收益、年化波动率
  2) 风险调整收益：Sharpe / Sortino / Calmar 比率
  3) 回撤分析：最大回撤、当前回撤、回撤期
  4) 分布形态：偏度、峰度、Jarque-Bera 正态性检验
  5) 尾部风险：历史/参数 VaR、CVaR/ES（95% / 99%）
  6) 波动率建模：EWMA（λ=0.94）、已实现波动率（5/21/63 日滚动）
  7) 时间序列：Hurst 指数（R/S 法）、自相关(1)、半衰期（均值回归速度）
  8) Z-score：当前价位相对滚动均值/标准差的偏离
  9) 相关性矩阵：可选第二/第三品种（--csv-b）做皮尔逊相关系数

适用：手工交易者的策略复盘、品种风险画像、跨品种相关性监控、凯利公式前置。
方法论与公式见 references/quant_finance.md。
"""

import argparse
import csv
import json
import math
import os
import sys
from collections import OrderedDict

# ---------------------------------------------------------------------------
# 数据载入
# ---------------------------------------------------------------------------

def load_csv(path, date_col="date", price_col="price"):
    pairs = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # 自动定位列名（兼容中文/大写）
        if reader.fieldnames:
            fields = {fn.strip().lower(): fn for fn in reader.fieldnames}
            date_col = fields.get(date_col.lower(), date_col)
            price_col = fields.get(price_col.lower(), price_col)
        for row in reader:
            try:
                p = float(str(row[price_col]).replace(",", "").strip())
            except (KeyError, ValueError, TypeError):
                continue
            if p <= 0:
                continue
            d = row.get(date_col, "")
            pairs.append((d, p))
    return pairs

def load_text(text):
    """粘贴模式：每行 'date,price' 或纯 'price'，制表/逗号分隔均可。"""
    pairs = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.replace("\t", ",").split(",")]
        try:
            p = float(parts[-1].replace(",", ""))
        except (ValueError, TypeError):
            continue
        if p <= 0:
            continue
        d = parts[0] if len(parts) > 1 else ""
        pairs.append((d, p))
    return pairs

def load_pairs(args):
    if args.csv:
        return load_csv(args.csv, args.date_col, args.price_col)
    if args.text:
        return load_text(args.text)
    if args.fetch:
        return fetch_live(args.fetch)
    sys.stderr.write("ERROR: 须提供 --csv/--text/--fetch 中的一种数据源\n")
    sys.exit(2)

# ---------------------------------------------------------------------------
# 基础收益与风险
# ---------------------------------------------------------------------------

def log_returns(prices):
    return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]

def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0

def stdev(xs, ddof=1):
    if len(xs) <= ddof:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - ddof))

def annualize_return(total_log_ret, n_periods, periods_per_year=252):
    if n_periods <= 0:
        return 0.0
    return (total_log_ret / n_periods) * periods_per_year

def annualize_vol(daily_vol, periods_per_year=252):
    return daily_vol * math.sqrt(periods_per_year)

def annualized_metrics(rets, periods_per_year=252, risk_free=0.0):
    n = len(rets)
    if n < 2:
        return None
    total = sum(rets)
    ann_ret = annualize_return(total, n, periods_per_year)
    ann_vol = annualize_vol(stdev(rets), periods_per_year)
    daily_rf = risk_free / periods_per_year
    excess = [r - daily_rf for r in rets]
    sharpe = (mean(excess) / stdev(rets)) * math.sqrt(periods_per_year) if stdev(rets) > 0 else 0.0
    # Sortino: 下行偏差
    downside = [min(0.0, r - daily_rf) for r in rets]
    dd = math.sqrt(sum(d ** 2 for d in downside) / len(downside)) if downside else 0.0
    sortino = (mean(excess) / dd) * math.sqrt(periods_per_year) if dd > 0 else 0.0
    return {
        "n_periods": n,
        "total_log_return": total,
        "ann_return": ann_ret,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "sortino": sortino,
    }

# ---------------------------------------------------------------------------
# 回撤
# ---------------------------------------------------------------------------

def drawdown_series(prices):
    """返回每点 (回撤深度, peak_index)。"""
    peaks = []
    peak = prices[0]
    peak_idx = 0
    dds = []
    for i, p in enumerate(prices):
        if p > peak:
            peak = p
            peak_idx = i
        dd = (p / peak - 1.0) if peak > 0 else 0.0
        dds.append((dd, peak_idx))
    return dds

def max_drawdown(prices):
    if len(prices) < 2:
        return {"max_dd": 0.0, "peak_idx": 0, "trough_idx": 0, "recovery_idx": None, "duration": 0}
    peaks = []
    peak = prices[0]
    peak_idx = 0
    max_dd = 0.0
    max_dd_peak = 0
    max_dd_trough = 0
    for i, p in enumerate(prices):
        if p > peak:
            peak = p
            peak_idx = i
        dd = (p / peak - 1.0) if peak > 0 else 0.0
        if dd < max_dd:
            max_dd = dd
            max_dd_peak = peak_idx
            max_dd_trough = i
    # 找最大回撤后的恢复点
    recovery = None
    for j in range(max_dd_trough + 1, len(prices)):
        if prices[j] >= prices[max_dd_peak]:
            recovery = j
            break
    duration = (recovery if recovery is not None else len(prices) - 1) - max_dd_peak
    return {
        "max_dd": max_dd,
        "peak_idx": max_dd_peak,
        "trough_idx": max_dd_trough,
        "recovery_idx": recovery,
        "duration": duration,
    }

# ---------------------------------------------------------------------------
# 分布形态
# ---------------------------------------------------------------------------

def distribution_stats(rets):
    n = len(rets)
    if n < 4:
        return None
    m = mean(rets)
    s = stdev(rets)
    if s == 0:
        return {"skewness": 0.0, "kurtosis": 0.0, "jarque_bera": 0.0, "is_normal_5pct": False}
    skew = sum(((x - m) / s) ** 3 for x in rets) * n / ((n - 1) * (n - 2))
    kurt = (sum(((x - m) / s) ** 4 for x in rets) * n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))
            - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))
    jb = (n / 6) * (skew ** 2 + (kurt ** 2) / 4)
    # JB ~ chi2(2)；5% 临界值 = 5.99
    return {
        "skewness": skew,
        "kurtosis": kurt,
        "jarque_bera": jb,
        "is_normal_5pct": jb < 5.99,
    }

# ---------------------------------------------------------------------------
# VaR / CVaR
# ---------------------------------------------------------------------------

def var_cvar(rets, q=0.05):
    """历史法 VaR / CVaR。q=0.05 表示 5% 左侧（最坏 5%）。返回正值表示损失幅度。"""
    if len(rets) < 20:
        return None
    sorted_r = sorted(rets)
    k = max(0, int(math.floor(q * len(sorted_r))) - 1)
    var = -sorted_r[k]
    tail = sorted_r[: k + 1]
    cvar = -mean(tail) if tail else var
    return {"var_hist": var, "cvar": cvar, "n_tail": len(tail)}

def var_parametric(rets, q=0.05, z_lookup=None):
    """参数法（正态假设）VaR。z 由 1-q 给出。"""
    if len(rets) < 20:
        return None
    s = stdev(rets)
    m = mean(rets)
    z = z_lookup if z_lookup is not None else {0.05: 1.645, 0.01: 2.326}.get(round(q, 2), 1.645)
    return m - z * s  # 正值表示损失（return 为负方向）

# ---------------------------------------------------------------------------
# 波动率建模
# ---------------------------------------------------------------------------

def ewma_variance(rets, lam=0.94):
    """RiskMetrics EWMA 方差序列。"""
    if not rets:
        return []
    s2 = rets[0] ** 2
    out = [s2]
    for r in rets[1:]:
        s2 = lam * s2 + (1 - lam) * r ** 2
        out.append(s2)
    return out

def realized_vol(rets, window=21):
    if len(rets) < window:
        return []
    out = []
    for i in range(window - 1, len(rets)):
        w = rets[i - window + 1 : i + 1]
        out.append(math.sqrt(sum(x ** 2 for x in w) / window))
    return out

# ---------------------------------------------------------------------------
# 时间序列诊断 · Hurst 指数
# ---------------------------------------------------------------------------
# 2026-09-28 重写。问题: 原实现用非重叠分段 + 未做偏误修正的 R/S, 在 n≈200 的日线上
# **系统性高估 H**(实测该技能自己的报告里 AUDJPY 0.96 / USDKRW 0.96; 本机 60 次
# 随机游走对照的均值高达 0.984 —— 即纯随机序列也会被判成"强趋势"), 从而让
# "第四维量化验证"恒为通过。实测对照(n=200, 60 次随机游走, 理论 H=0.500):
#     R/S 非重叠无修正      均值 0.984   ← 原实现
#     R/S 重叠 + Anis-Lloyd 均值 0.840   ← 加修正后仍显著有偏
#     DFA-1 (smin=8, smax=n/4) 均值 0.505  ← 近乎无偏, 故取为主估计量
# 对真实持续性序列(AR(1) φ=0.3)DFA-1 给出 0.667(正确 >0.5), R/S 给出 0.836(被偏误污染)。
# 结论: 主估计量 = DFA-1; R/S 仅作历史对照并明确标注有偏;
#       判定显著性一律以**自助法随机游走带(5%/95%)**为准, 不再用固定 0.45/0.55 阈值。

def _profile(prices):
    """DFA 的 profile: log 价格 → log 收益去均值后累计。"""
    lp = [math.log(p) for p in prices if p > 0]
    if len(lp) < 3:
        return []
    r = [lp[i] - lp[i - 1] for i in range(1, len(lp))]
    m = mean(r)
    out = []
    acc = 0.0
    for x in r:
        acc += x - m
        out.append(acc)
    return out


def hurst_dfa(prices, smin=8, smax=None, order=1):
    """Detrended Fluctuation Analysis(DFA-1)估算 Hurst 指数 —— **主估计量**。

    H ≈ 0.5 随机游走; H > 0.5 持续性(趋势); H < 0.5 反持续性(均值回归)。
    实测 n=200 随机游走下均值 0.505(sd 0.081), 偏误 ≈ 0.005。
    """
    y = _profile(prices)
    n = len(y)
    if n < 64:
        return None
    smax = smax or max(smin + 1, n // 4)
    scales = []
    s = smin
    while s <= smax:
        scales.append(int(s))
        s = max(s + 1, int(s * 1.25))
    xs, ys = [], []
    for s in scales:
        nseg = n // s
        if nseg < 2:
            continue
        fs = []
        for k in range(nseg):
            seg = y[k * s:(k + 1) * s]
            m = len(seg)
            if m < 3:
                continue
            mx = (m - 1) / 2.0
            my = mean(seg)
            num = sum((i - mx) * (seg[i] - my) for i in range(m))
            den = sum((i - mx) ** 2 for i in range(m))
            b = num / den if den else 0.0
            a = my - b * mx
            res = [seg[i] - (a + b * i) for i in range(m)]
            fs.append(math.sqrt(sum(v * v for v in res) / m))
        f = mean(fs) if fs else 0.0
        if f > 0:
            xs.append(math.log(s))
            ys.append(math.log(f))
    return _fit_H(list(zip(xs, ys, [0] * len(xs))))


def _rs_curve(prices, max_lag=None):
    """R/S 曲线: 返回 [(log(n), log(R/S)), ...](未做偏误修正)。"""
    n = len(prices)
    if n < 32:
        return []
    if max_lag is None:
        max_lag = n // 4
    pts = []
    step = max(1, (max_lag - 8) // 16)
    for lag in range(8, max_lag + 1, step):
        rs_list = []
        # 重叠分段(步长自适应, 每 lag 最多约 50 段)提升小样本稳定性
        sub = max(1, (n - lag) // 50)
        for start in range(0, n - lag + 1, sub):
            segment = prices[start : start + lag]
            m = mean(segment)
            dev = [x - m for x in segment]
            cum = []
            s = 0.0
            for d in dev:
                s += d
                cum.append(s)
            r = max(cum) - min(cum)
            s_dev = stdev(segment, ddof=0)
            if s_dev > 0:
                rs_list.append(r / s_dev)
        if rs_list:
            pts.append((math.log(lag), math.log(mean(rs_list)), lag))
    return pts


def _anis_lloyd_expected_rs(n):
    """Anis-Lloyd/Peters 随机游走下 E[R/S]_n 的理论值(用于偏误修正)。"""
    if n <= 1:
        return 0.0
    if n <= 340:
        s = sum(math.sqrt((n - i) / i) for i in range(1, n))
        return ((n - 0.5) / n) * (1.0 / math.sqrt(n * math.pi / 2.0)) * s
    return ((n - 0.5) / n) * (1.0 / math.sqrt(n * math.pi / 2.0))


def _fit_H(pts):
    if len(pts) < 3:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    mx, my = mean(xs), mean(ys)
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs)))
    den = sum((xs[i] - mx) ** 2 for i in range(len(xs)))
    return (num / den) if den else None


def hurst_rs(prices, max_lag=None):
    """R/S 法 Hurst(**已做 Anis-Lloyd 修正, 但仍有偏 —— 仅作历史对照**)。

    ⚠️ 2026-09-28 实测(n=200, 60 次随机游走, 理论 H=0.500):
        本函数(重叠分段 + Anis-Lloyd)均值 **0.840** ← 仍显著高估;
        主估计量请用 `hurst_dfa()`(同条件下均值 0.505)。
    保留本函数仅为与历史报告对比, **不得单独用于"是否趋势市"的判定**。
    """
    pts = _rs_curve(prices, max_lag)
    corrected = []
    for lx, ly, lag in pts:
        exp_rs = _anis_lloyd_expected_rs(lag)
        rs_obs = math.exp(ly)                      # 该 lag 的观测平均 R/S
        rs_adj = rs_obs - exp_rs + math.sqrt(lag * math.pi / 2.0)   # Anis-Lloyd 修正
        corrected.append((lx, math.log(rs_adj if rs_adj > 1e-9 else 1e-9)))
    return _fit_H(corrected if len(corrected) >= 3 else pts)


def hurst_rs_raw(prices, max_lag=None):
    """原始(无修正)R/S 估计。实测随机游走均值 0.984, 仅用于展示偏误量级。"""
    return _fit_H(_rs_curve(prices, max_lag))


def hurst_significance(prices, n_boot=100, max_lag=None, seed=20260928):
    """Hurst 显著性与随机游走零假设带(自助法, 基于 **DFA-1**)。

    做法: 对收益序列做**有放回自举**(保留均值与波动尺度), 重建同分布的随机游走路径,
    用同一估计量(DFA-1)重算 H, 取 5%/95% 分位作为"与随机游走不可区分"的区间。
    返回 dict: {h, h_rs, lo, hi, n_boot, verdict}
      h        : DFA-1 点估计(主)
      h_rs     : R/S 估计(有偏, 仅参考)
      lo/hi    : 随机游走带(5%/95%)
      verdict  : 趋势显著 / 均值回归显著 / 与随机游走不可区分 / 样本不足 / 未做显著性检验
    """
    n = len(prices)
    out = {"h": None, "h_rs": None, "lo": None, "hi": None,
           "n_boot": 0, "verdict": "样本不足"}
    if n < 32:
        return out
    h = hurst_dfa(prices, smax=max_lag)
    out["h"] = h
    out["h_rs"] = hurst_rs(prices, max_lag)
    if h is None or n_boot <= 0:
        out["verdict"] = "未做显著性检验"
        return out
    rnd = __import__("random").Random(seed)
    steps = [prices[i + 1] - prices[i] for i in range(n - 1)]
    mu = mean(steps)
    dev = [s - mu for s in steps]
    hs = []
    for _ in range(int(n_boot)):
        path = [prices[0]]
        acc = prices[0]
        for _i in range(n - 1):
            acc += mu + dev[rnd.randrange(len(dev))]
            path.append(acc)
        _hb = hurst_dfa(path, smax=max_lag)
        if _hb is not None:
            hs.append(_hb)
    if len(hs) < 20:
        out["verdict"] = "自助样本不足"
        return out
    hs.sort()
    lo = hs[int(0.05 * len(hs))]
    hi = hs[min(len(hs) - 1, int(0.95 * len(hs)))]
    out["lo"], out["hi"], out["n_boot"] = round(lo, 3), round(hi, 3), len(hs)
    if h > hi:
        out["verdict"] = "趋势显著"
    elif h < lo:
        out["verdict"] = "均值回归显著"
    else:
        out["verdict"] = "与随机游走不可区分"
    return out

def autocorr_lag1(rets):
    n = len(rets)
    if n < 3:
        return None
    m = mean(rets)
    num = sum((rets[i] - m) * (rets[i - 1] - m) for i in range(1, n))
    den = sum((r - m) ** 2 for r in rets)
    return num / den if den > 0 else 0.0

def half_life(rets):
    """AR(1) 半衰期：r_t = phi * r_{t-1} + e_t → HL = -log(2)/log(phi)。"""
    n = len(rets)
    if n < 10:
        return None
    y = rets[1:]
    x = rets[:-1]
    mx = mean(x)
    my = mean(y)
    num = sum((x[i] - mx) * (y[i] - my) for i in range(len(x)))
    den = sum((x[i] - mx) ** 2 for i in range(len(x)))
    if den <= 0:
        return None
    phi = num / den
    if phi <= 0 or phi >= 1:
        return None
    return -math.log(2) / math.log(phi)

# ---------------------------------------------------------------------------
# Z-score / 相关性
# ---------------------------------------------------------------------------

def rolling_zscore(prices, window=63):
    if len(prices) < 10:
        return None
    # 自适应：当样本不足时取 min(63, n//2)
    w = min(window, max(10, len(prices) // 2))
    if len(prices) < w:
        return None
    segment = prices[-w:]
    m = mean(segment)
    s = stdev(segment)
    if s == 0:
        return None
    return (prices[-1] - m) / s

def pearson_corr(xs, ys):
    n = min(len(xs), len(ys))
    if n < 3:
        return None
    a = xs[:n]
    b = ys[:n]
    ma = mean(a)
    mb = mean(b)
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    den_a = sum((x - ma) ** 2 for x in a)
    den_b = sum((y - mb) ** 2 for y in b)
    den = math.sqrt(den_a * den_b)
    if den == 0:
        return None
    return num / den

# ---------------------------------------------------------------------------
# 报告输出
# ---------------------------------------------------------------------------

def fmt_pct(x, d=2):
    return f"{x*100:.{d}f}%" if x is not None else "—"

def fmt_num(x, d=4):
    return f"{x:.{d}f}" if x is not None else "—"

def build_report(prices, rets, periods_per_year, risk_free, n_boot=100):
    rep = OrderedDict()
    if rets:
        rep["基础收益"] = annualized_metrics(rets, periods_per_year, risk_free)
    if prices:
        rep["回撤"] = max_drawdown(prices)
        rep["分布形态"] = distribution_stats(rets) if rets else None
        rep["尾部风险_95%"] = var_cvar(rets, 0.05)
        rep["尾部风险_99%"] = var_cvar(rets, 0.01)
        rep["参数VaR_95%"] = var_parametric(rets, 0.05)
        rep["参数VaR_99%"] = var_parametric(rets, 0.01)
        if rets:
            ew = ewma_variance(rets)
            rep["EWMA波动率(年化)"] = math.sqrt(ew[-1]) * math.sqrt(periods_per_year) if ew else None
            rv = realized_vol(rets, 21)
            rep["已实现波动率_21d(年化)"] = rv[-1] * math.sqrt(periods_per_year) if rv else None
            rep["自相关_lag1"] = autocorr_lag1(rets)
            rep["半衰期(bar)"] = half_life(rets)
        # Hurst: 主估计量 = DFA-1(实测近乎无偏); R/S 仅作对照; 判定以自助法随机游走带为准
        rep["Hurst指数"] = hurst_dfa(prices)
        if n_boot:
            _hs = hurst_significance(prices, n_boot=n_boot)
            rep["Hurst_DFA"] = _hs["h"]
            rep["Hurst_RS_有偏"] = _hs["h_rs"]
            rep["Hurst_随机游走带"] = [_hs["lo"], _hs["hi"]]
            rep["Hurst_判定"] = _hs["verdict"]
            if _hs["h"] is not None:
                rep["Hurst指数"] = _hs["h"]
        rep["Z-score_63d"] = rolling_zscore(prices, 63)
    return rep

def render_text(rep, n_obs, last_price, first_date, last_date):
    lines = []
    lines.append("=" * 60)
    lines.append("  金融工程/量化分析指标报告")
    lines.append("=" * 60)
    if first_date and last_date:
        lines.append(f"区间: {first_date} → {last_date}  |  样本数: {n_obs}  |  最新价: {last_price:.4f}")
    else:
        lines.append(f"样本数: {n_obs}  |  最新价: {last_price:.4f}")
    lines.append("")

    b = rep.get("基础收益")
    if b:
        lines.append("【一、收益与风险调整（年化）】")
        lines.append(f"  总对数收益       {fmt_pct(b['total_log_return'])}")
        lines.append(f"  年化收益         {fmt_pct(b['ann_return'])}")
        lines.append(f"  年化波动率       {fmt_pct(b['ann_vol'])}")
        lines.append(f"  Sharpe 比率      {fmt_num(b['sharpe'])}")
        lines.append(f"  Sortino 比率     {fmt_num(b['sortino'])}")
        lines.append("")

    dd = rep.get("回撤")
    if dd:
        lines.append("【二、回撤】")
        lines.append(f"  最大回撤         {fmt_pct(dd['max_dd'])}")
        rec = f"第 {dd['recovery_idx']} 点" if dd['recovery_idx'] is not None else "未恢复"
        lines.append(f"  起点→谷底→恢复   {dd['peak_idx']} → {dd['trough_idx']} → {rec}")
        lines.append(f"  回撤持续期       {dd['duration']} 个 bar")
        # 当前回撤
        dds = drawdown_series(rep.get("_prices", []))
        cur_dd = dds[-1][0] if dds else 0
        lines.append(f"  当前回撤         {fmt_pct(cur_dd)}")
        lines.append("")

    ds = rep.get("分布形态")
    if ds:
        lines.append("【三、收益分布形态】")
        lines.append(f"  偏度 (Skewness)  {fmt_num(ds['skewness'])}    < 0 左尾肥（亏损厚尾）")
        lines.append(f"  峰度 (Kurtosis)  {fmt_num(ds['kurtosis'])}    > 0 厚尾；正态=0")
        lines.append(f"  Jarque-Bera      {fmt_num(ds['jarque_bera'])}  临界 5.99 → {'近似正态' if ds['is_normal_5pct'] else '拒绝正态（厚尾）'}")
        lines.append("")

    v95 = rep.get("尾部风险_95%"); v99 = rep.get("尾部风险_99%")
    p95 = rep.get("参数VaR_95%"); p99 = rep.get("参数VaR_99%")
    if v95 and v99:
        lines.append("【四、尾部风险（VaR / CVaR，历史法）】")
        lines.append(f"  95% VaR          {fmt_pct(v95['var_hist'])}  (CVaR {fmt_pct(v95['cvar'])})")
        lines.append(f"  99% VaR          {fmt_pct(v99['var_hist'])}  (CVaR {fmt_pct(v99['cvar'])})")
        if p95 and p99:
            lines.append(f"  95% 参数VaR      {fmt_pct(p95)}    (正态假设)")
            lines.append(f"  99% 参数VaR      {fmt_pct(p99)}    (正态假设)")
        lines.append('  注: CVaR > VaR，量化「超过 VaR」的平均损失；尾部风险用历史法更可靠。')
        lines.append("")

    ew = rep.get("EWMA波动率(年化)"); rv = rep.get("已实现波动率_21d(年化)")
    if ew is not None or rv is not None:
        lines.append("【五、波动率建模】")
        if ew is not None:
            lines.append(f"  EWMA 波动率      {fmt_pct(ew)}    (λ=0.94, RiskMetrics)")
        if rv is not None:
            lines.append(f"  已实现波动率 21d {fmt_pct(rv)}    (21日滚动)")
        lines.append("")

    ac = rep.get("自相关_lag1"); hl = rep.get("半衰期(bar)"); H = rep.get("Hurst指数")
    z = rep.get("Z-score_63d")
    if any(v is not None for v in [ac, hl, H, z]):
        lines.append("【六、时间序列诊断】")
        if ac is not None:
            tag = "正自相关（动量）" if ac > 0.1 else ("负自相关（反转）" if ac < -0.1 else "近似独立")
            lines.append(f"  自相关 lag(1)    {fmt_num(ac)}  [{tag}]")
        if hl is not None:
            lines.append(f"  均值回归半衰期   {fmt_num(hl, 1)} 个 bar")
        else:
            lines.append(f"  均值回归半衰期   — (phi≥1 不收敛或样本不足)")
        if H is not None:
            # 修复(2026-09-28): 不用固定 0.45/0.55 阈值下结论 —— 原 R/S 在 n≈200 时
            # 系统性高估(实测随机游走均值 0.984, 加修正后仍 0.840), 会把随机游走判成趋势。
            # 现主估计量为 DFA-1(随机游走实测均值 0.505), 且显著性一律以自助法带为准。
            verdict = rep.get("Hurst_判定")
            Hrs = rep.get("Hurst_RS_有偏")
            band = rep.get("Hurst_随机游走带")
            if verdict:
                tag = {"趋势显著": "趋势显著(高于随机游走带上沿)",
                       "均值回归显著": "均值回归显著(低于带下沿)",
                       "与随机游走不可区分": "与随机游走不可区分 → 不得据此判趋势",
                       "未做显著性检验": "未做显著性检验"}.get(verdict, verdict)
            else:
                tag = "未做显著性检验"
            lines.append(f"  Hurst 指数(DFA-1) {fmt_num(H, 3)}  [{tag}]")
            if Hrs is not None or band:
                lines.append("    (R/S 对照 %s, 已知偏高 ｜ 随机游走带 %s)"
                             % (fmt_num(Hrs, 3) if Hrs is not None else "—",
                                "[%s, %s]" % (fmt_num(band[0], 3), fmt_num(band[1], 3))
                                if band else "—"))
        if z is not None:
            tag = "高位" if z > 1.5 else ("低位" if z < -1.5 else "中性区间")
            lines.append(f"  Z-score (63d)    {fmt_num(z, 2)}  [{tag}]")
        lines.append("")

    lines.append("=" * 60)
    lines.append("使用提示: 厚尾 + 偏度负 → 真实 VaR > 参数 VaR，仓位需打折；")
    lines.append("           Hurst 已做 Anis-Lloyd 偏误修正, 且须以自助法随机游走带判定显著性：")
    lines.append("           只有 H 落在带外(趋势显著/均值回归显著)才可据此选策略；")
    lines.append("           落在带内 = 与随机游走不可区分, 不得据此判趋势。")
    lines.append("           详细方法论见 references/quant_finance.md。")
    lines.append("=" * 60)
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# --fetch 实时数据（简化：直接复用 kline_fetch + 收盘价）
# ---------------------------------------------------------------------------

def fetch_live(symbol):
    """调 scripts/kline_fetch.fetch_one 取日 K 线收盘价，规避重复实现。"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_libs"))
        from kline_fetch import fetch_one
    except Exception:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from kline_fetch import fetch_one
        except Exception:
            sys.stderr.write("ERROR: --fetch 需 scripts/kline_fetch.py 在同目录或 PYTHONPATH\n")
            sys.exit(2)
    bars = fetch_one(symbol, interval="1day", outputsize=min(500, 250))
    return [(b["t"], float(b["c"])) for b in bars]

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="金融工程/量化分析指标计算引擎")
    ap.add_argument("--csv", help="价格 CSV 路径（默认含 date,price 列；可用 --date-col/--price-col 指定）")
    ap.add_argument("--text", help="粘贴价格文本（每行 date,price）")
    ap.add_argument("--fetch", help="联网取日 K 线收盘价（依赖 kline_fetch.py）")
    ap.add_argument("--csv-b", help="第二价格序列（用于相关性分析）")
    ap.add_argument("--date-col", default="date")
    ap.add_argument("--price-col", default="price")
    ap.add_argument("--periods-per-year", type=int, default=252, help="年化基数：日线=252，小时=2190，周线=52")
    ap.add_argument("--risk-free", type=float, default=0.0, help="无风险年化利率（用于 Sharpe/Sortino）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ap.add_argument("--corr-b", action="store_true", help="同时计算与 --csv-b 的皮尔逊相关系数")
    ap.add_argument("--boot", type=int, default=100,
                    help="Hurst 显著性自助抽样次数(默认 100; 0=跳过显著性检验)")
    args = ap.parse_args()

    pairs = load_pairs(args)
    if len(pairs) < 30:
        sys.stderr.write(f"ERROR: 样本不足 30 条（当前 {len(pairs)}），统计指标无意义\n")
        sys.exit(2)

    prices = [p for _, p in pairs]
    rets = log_returns(prices)
    rep = build_report(prices, rets, args.periods_per_year, args.risk_free, args.boot)
    rep["_prices"] = prices  # 给 render_text 用回撤

    if args.corr_b and args.csv_b:
        pairs_b = load_csv(args.csv_b, args.date_col, args.price_col)
        prices_b = [p for _, p in pairs_b]
        rets_b = log_returns(prices_b)
        n = min(len(rets), len(rets_b))
        if n >= 30:
            rep["相关性_对数收益_pearson"] = pearson_corr(rets[-n:], rets_b[-n:])

    if args.json:
        # 修复(2026-09-28): 原实现 `out[k] = v if v is None or (isinstance(v, float) and
        # math.isfinite(v)) else None` 会把 **list / str / int / bool 全部吞成 None**
        # (导致 Hurst_随机游走带、Hurst_判定 等字段在 --json 里恒为 null)。
        # 现改为递归清洗: 仅把非有限 float 置 None, 其余类型原样保留。
        def _clean(v):
            if isinstance(v, float):
                return v if math.isfinite(v) else None
            if isinstance(v, dict):
                return {kk: _clean(vv) for kk, vv in v.items()}
            if isinstance(v, (list, tuple)):
                return [_clean(x) for x in v]
            return v

        out = OrderedDict()
        for k, v in rep.items():
            if k.startswith("_"):
                continue
            out[k] = _clean(v)
        out["meta"] = {
            "n_obs": len(pairs),
            "first_date": pairs[0][0],
            "last_date": pairs[-1][0],
            "last_price": prices[-1],
            "periods_per_year": args.periods_per_year,
            "risk_free": args.risk_free,
        }
        # ensure_ascii=True: 输出纯 ASCII 转义 JSON —— 中文键在 cp936 管道/GBK 控制台
        # 下也能被下游正确解析(2026-09-28 修复机器可读性)。
        print(json.dumps(out, ensure_ascii=True, indent=2,
                         default=lambda o: round(o, 6) if isinstance(o, float) else str(o)))
    else:
        print(render_text(rep, len(pairs), prices[-1], pairs[0][0], pairs[-1][0]))

if __name__ == "__main__":
    main()
