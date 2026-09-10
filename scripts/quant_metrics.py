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
# 时间序列诊断
# ---------------------------------------------------------------------------

def hurst_rs(prices, max_lag=None):
    """R/S 法估算 Hurst 指数。
    H < 0.5 → 均值回归；H = 0.5 → 随机游走；H > 0.5 → 趋势。
    """
    n = len(prices)
    if n < 32:
        return None
    if max_lag is None:
        max_lag = n // 4
    log_rs = []
    log_n = []
    for lag in range(8, max_lag + 1, max(1, (max_lag - 8) // 16)):
        rs_list = []
        for start in range(0, n - lag, lag):
            segment = prices[start : start + lag]
            if len(segment) < lag:
                continue
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
            log_rs.append(math.log(mean(rs_list)))
            log_n.append(math.log(lag))
    if len(log_n) < 3:
        return None
    # 线性拟合 log(R/S) = H * log(n) + c
    n_pts = len(log_n)
    mx = mean(log_n)
    my = mean(log_rs)
    num = sum((log_n[i] - mx) * (log_rs[i] - my) for i in range(n_pts))
    den = sum((log_n[i] - mx) ** 2 for i in range(n_pts))
    if den == 0:
        return None
    H = num / den
    return H

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

def build_report(prices, rets, periods_per_year, risk_free):
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
        rep["Hurst指数"] = hurst_rs(prices)
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
            tag = "强趋势" if H > 0.55 else ("强均值回归" if H < 0.45 else "随机游走")
            lines.append(f"  Hurst 指数       {fmt_num(H, 3)}  [{tag}]")
        if z is not None:
            tag = "高位" if z > 1.5 else ("低位" if z < -1.5 else "中性区间")
            lines.append(f"  Z-score (63d)    {fmt_num(z, 2)}  [{tag}]")
        lines.append("")

    lines.append("=" * 60)
    lines.append("使用提示: 厚尾 + 偏度负 → 真实 VaR > 参数 VaR，仓位需打折；")
    lines.append("           H<0.45 适合均值回归策略；H>0.55 适合趋势跟踪。")
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
    args = ap.parse_args()

    pairs = load_pairs(args)
    if len(pairs) < 30:
        sys.stderr.write(f"ERROR: 样本不足 30 条（当前 {len(pairs)}），统计指标无意义\n")
        sys.exit(2)

    prices = [p for _, p in pairs]
    rets = log_returns(prices)
    rep = build_report(prices, rets, args.periods_per_year, args.risk_free)
    rep["_prices"] = prices  # 给 render_text 用回撤

    if args.corr_b and args.csv_b:
        pairs_b = load_csv(args.csv_b, args.date_col, args.price_col)
        prices_b = [p for _, p in pairs_b]
        rets_b = log_returns(prices_b)
        n = min(len(rets), len(rets_b))
        if n >= 30:
            rep["相关性_对数收益_pearson"] = pearson_corr(rets[-n:], rets_b[-n:])

    if args.json:
        out = OrderedDict()
        for k, v in rep.items():
            if k.startswith("_"):
                continue
            if isinstance(v, dict):
                out[k] = {kk: (vv if not isinstance(vv, float) or math.isfinite(vv) else None) for kk, vv in v.items()}
            else:
                out[k] = v if v is None or (isinstance(v, float) and math.isfinite(v)) else None
        out["meta"] = {
            "n_obs": len(pairs),
            "first_date": pairs[0][0],
            "last_date": pairs[-1][0],
            "last_price": prices[-1],
            "periods_per_year": args.periods_per_year,
            "risk_free": args.risk_free,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2, default=lambda o: round(o, 6) if isinstance(o, float) else str(o)))
    else:
        print(render_text(rep, len(pairs), prices[-1], pairs[0][0], pairs[-1][0]))

if __name__ == "__main__":
    main()
