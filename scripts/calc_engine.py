#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kingforex-skill v3.0 — 统一计算引擎 (Single Source of Truth)

设计目标（对应 v3.0 规范第五章 / 3.2 模板问题修复）：
- 所有模块（HTML 报告、凯利计算器、风险仪表盘、浮盈、相关性、评分、一致性校验）
  只调用本引擎，禁止模块内手算、禁止硬编码关键数值。
- 修复 v2.3 模板矛盾：
  * pip 价值差数量级（v2.3 写 $0.864/0.01手；实测 0.01 手 ≈$0.0652/0.02 手 $0.1303
    @ USDJPY 153.478，随结算汇率实时变动，禁止写死）
  * AUDJPY 现价三处不一致（110.46967 / 110.54 / 110.47）
  * 凯利显示「最优仓位 20%」但受 1% 风险硬约束（误导）
  * 相关性文字 -0.78 与矩阵 0.44 冲突
  * 回测 12 笔却给 +27%~+41% 年化预测（样本不足）
  * 评分黑箱（只有总分，无子项/权重明细）
- 所有函数纯标准库，确定性、可单测、可复盘。

约定：
- 「手」以标准手为单位；1 标准手 = 100,000 基础货币单位（FX）。
- lot_unit 在合约表中定义为「每 0.01 手对应的合约单位数」，故
  实际单位数 = hand * 100 * lot_unit，pip 价值按此推导。
- JPY 交叉盘 pip 价值需除以 USDJPY 结算汇率（美元计价）。
"""

import math
from statistics import mean, pstdev

# ---------------------------------------------------------------------------
# 5.1 合约规格表（v3.0 规范，唯一事实来源）
# lot_unit = 每 0.01 手对应的合约单位数（FX=1000, XAU=1oz, XAG=50oz, USOIL=10bbl）
# pip = 该品种 1 个报价点的价格增量
# jpy = 是否需要用 USDJPY 将 JPY 价值折算为 USD
# ---------------------------------------------------------------------------
CONTRACTS = {
    "AUDJPY": {"lot_unit": 1000, "pip": 0.01,   "jpy": True,  "label": "澳元/日元"},
    "USDJPY": {"lot_unit": 1000, "pip": 0.01,   "jpy": True,  "label": "美元/日元"},
    "EURUSD": {"lot_unit": 1000, "pip": 0.0001, "jpy": False, "label": "欧元/美元"},
    "GBPUSD": {"lot_unit": 1000, "pip": 0.0001, "jpy": False, "label": "英镑/美元"},
    "AUDUSD": {"lot_unit": 1000, "pip": 0.0001, "jpy": False, "label": "澳元/美元"},
    "XAUUSD": {"lot_unit": 1,    "pip": 1.0,    "jpy": False, "label": "伦敦金"},
    "XAGUSD": {"lot_unit": 50,   "pip": 0.01,   "jpy": False, "label": "伦敦银"},
    "USOIL":  {"lot_unit": 10,   "pip": 0.01,   "jpy": False, "label": "WTI 原油"},
    "DXY":    {"lot_unit": 1000, "pip": 0.01,   "jpy": False, "label": "美元指数", "index": True},
    "USDCNH": {"lot_unit": 1000, "pip": 0.0001, "jpy": False, "label": "美元/离岸人民币"},
}

# 评分权重（四维，和为 1.0）
SCORE_WEIGHTS = {"macro": 0.25, "tech": 0.30, "quant": 0.25, "sentiment": 0.20}
SCORE_BUILD = 75.0   # ≥75 才考虑建仓
SCORE_WATCH = 60.0  # 60-74 观望；<60 不建议

RISK_HARD_CAP = 1.0       # 单笔风险硬上限 %
PORTFOLIO_CAP = 5.0       # 组合风险上限 %
EVENT_SILENCE_H = 4.0     # 事件前 4h 不开新仓
FOMC_CLEAR_H = 24.0       # 议息前 24h 清仓/最小仓
MIN_RR = 1.5              # 合格风险回报比
BACKTEST_MIN = 100        # 回测样本下限，不足不预测年化


# ---------------------------------------------------------------------------
# 5.2 / 5.3 / 5.4  pip 价值、手数、浮盈
# ---------------------------------------------------------------------------
def pip_value_per_pip(inst: str, hand: float, usdjpy: float) -> float:
    """每 pip 的美元价值（按持仓手数 hand）。

    推导：每 0.01 手单位数 = lot_unit；hand 手对应单位数 = hand*100*lot_unit。
    每 pip 价格增量 = pip；JPY 盘需 /usdjpy 折算为 USD。
    """
    c = CONTRACTS.get(inst)
    if not c or c.get("index"):
        return 0.0
    units = hand * 100.0 * c["lot_unit"]
    raw = units * c["pip"]
    return raw / usdjpy if c["jpy"] else raw


def pnl(inst: str, direction: str, entry: float, now: float, hand: float,
        usdjpy: float) -> float:
    """浮盈（美元）。空单=(entry-now)，多单=(now-entry)，均 ×pip 价值。"""
    if CONTRACTS.get(inst, {}).get("index"):
        return 0.0
    pv = pip_value_per_pip(inst, hand, usdjpy)
    diff = (entry - now) if direction.upper().startswith("S") else (now - entry)
    # diff 为价格差；换算成 pips：diff / pip，再 × 每 pip 价值
    pip = CONTRACTS[inst]["pip"]
    pips = diff / pip
    return pips * pv


def compute_lots(equity: float, risk_pct: float, stop_pips: float,
                 inst: str, usdjpy: float, cap: float = RISK_HARD_CAP) -> float:
    """由风险预算反推手数。风险金额 = 净值×风险%；手数 = 风险金额/(止损pip×每pip价值)。

    返回的手数以「标准手」计；超额自动按硬上限压回。
    """
    risk_pct = min(risk_pct, cap)
    risk_amt = equity * risk_pct / 100.0
    if stop_pips <= 0:
        return 0.0
    c = CONTRACTS.get(inst)
    if not c or c.get("index"):
        return 0.0
    pv_per_hand = pip_value_per_pip(inst, 1.0, usdjpy)  # 1 标准手每 pip 价值
    lots = risk_amt / (stop_pips * pv_per_hand)
    return round(lots, 4)


# ---------------------------------------------------------------------------
# 5.5 凯利
# ---------------------------------------------------------------------------
def kelly(winrate: float, payoff: float):
    """f* = (p*b - q)/b。返回 (full, half, third, fstar_le0)。

    - 负期望否决：f*<=0 → 全部 0，外部应判 0 手不开仓。
    - 实战只用半凯利，且以风险预算为准（见 kelly_recommended_lots）。
    """
    p = winrate / 100.0
    b = payoff
    q = 1.0 - p
    f_full = (p * b - q) / b if b > 0 else 0.0
    f_full = max(f_full, 0.0)
    return f_full, f_full / 2.0, f_full / 3.0, f_full <= 0


def kelly_recommended_lots(equity, risk_pct, stop_pips, inst, usdjpy,
                           winrate, payoff, user_cap=None, mode="half"):
    """最终推荐手数 = min(凯利档位对应手数, 1%风险最大手数, 用户上限)。

    禁止把理论全凯利直接当实盘仓位；禁止输出「最优仓位 20%」类误导数字。
    返回 dict：kelly_tier_pct / kelly_lots / risk_lots / user_lots / final_lots / binder。
    """
    f_full, f_half, f_third, veto = kelly(winrate, payoff)
    tier = {"full": f_full, "half": f_half, "third": f_third}[mode]
    kelly_pct = tier * 100.0
    # 凯利对应手数：以凯利百分比占用权益的风险金额反推
    kelly_risk_amt = equity * kelly_pct / 100.0
    c = CONTRACTS.get(inst, {})
    pv_per_hand = pip_value_per_pip(inst, 1.0, usdjpy) if c and not c.get("index") else 0
    kelly_lots = (kelly_risk_amt / (stop_pips * pv_per_hand)) if (stop_pips > 0 and pv_per_hand > 0) else 0.0
    # 1% 风险预算手数
    risk_lots = compute_lots(equity, min(risk_pct, RISK_HARD_CAP), stop_pips, inst, usdjpy)
    candidates = [risk_lots]
    if not veto:
        candidates.append(kelly_lots)
    if user_cap is not None:
        candidates.append(user_cap)
    final = min(candidates)
    binder = "用户上限" if (user_cap is not None and abs(final - user_cap) < 1e-9) else \
             ("凯利%d档" % {"full": 100, "half": 50, "third": 33}[mode]) if (not veto and abs(final - kelly_lots) < 1e-9) else "1%风险预算"
    return {
        "veto": veto, "kelly_full_pct": f_full * 100.0, "kelly_half_pct": f_half * 100.0,
        "kelly_third_pct": f_third * 100.0, "tier_mode": mode, "kelly_tier_pct": kelly_pct,
        "kelly_lots": round(kelly_lots, 4), "risk_lots": round(risk_lots, 4),
        "final_lots": round(final, 4), "binder": binder,
    }


# ---------------------------------------------------------------------------
# 5.6 相关性（最近 60 日收益 Pearson 矩阵）
# ---------------------------------------------------------------------------
def returns(series):
    """由价格序列算简单收益率。"""
    out = []
    for i in range(1, len(series)):
        if series[i - 1]:
            out.append((series[i] - series[i - 1]) / series[i - 1])
    return out


def pearson(a, b):
    n = min(len(a), len(b))
    if n < 3:
        return None
    a, b = a[:n], b[:n]
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    if da == 0 or db == 0:
        return None
    return num / (da * db)


def corr_matrix(prices: dict):
    """prices: {inst: [close,...]}。返回 {inst: {inst: r}} 与 文字分类。"""
    insts = list(prices.keys())
    rets = {k: returns(v) for k, v in prices.items()}
    m = {k: {kk: (1.0 if k == kk else None) for kk in insts} for k in insts}
    for i in range(len(insts)):
        for j in range(i + 1, len(insts)):
            r = pearson(rets[insts[i]], rets[insts[j]])
            m[insts[i]][insts[j]] = r
            m[insts[j]][insts[i]] = r
    high, low = [], []
    for i in range(len(insts)):
        for j in range(i + 1, len(insts)):
            r = m[insts[i]][insts[j]]
            if r is None:
                continue
            if r >= 0.6:
                high.append((insts[i], insts[j], round(r, 2)))
            elif r <= 0.3:
                low.append((insts[i], insts[j], round(r, 2)))
    # 文字必须与矩阵一致（修复 v2.3 文字 -0.78 vs 矩阵 0.44 矛盾）
    text = {"high": high, "low": low,
            "note": "相关性文字由矩阵实时计算生成，确保描述与数值一致。"}
    return m, text


# ---------------------------------------------------------------------------
# 5.7 四维评分（可量化子项 + 权重明细，修复黑箱）
# ---------------------------------------------------------------------------
def score_4d(subs: dict) -> dict:
    """subs: {macro:{name:raw_score(0-100),...}, tech:{...}, quant:{...}, sentiment:{...}}。
    每维 = 子项均值；总分 = Σ(维分×权重)。返回总分/各维分/子项明细。
    """
    dim_avg = {}
    detail = {}
    for dim in SCORE_WEIGHTS:
        items = subs.get(dim, {})
        if not items:
            dim_avg[dim] = 0.0
            detail[dim] = {}
            continue
        vals = list(items.values())
        dim_avg[dim] = round(mean(vals), 2)
        detail[dim] = {k: round(v, 2) for k, v in items.items()}
    total = sum(dim_avg[d] * w for d, w in SCORE_WEIGHTS.items())
    total = round(total, 2)
    if total >= SCORE_BUILD:
        verdict = "可建仓"
    elif total >= SCORE_WATCH:
        verdict = "观望"
    else:
        verdict = "不建议"
    return {"total": total, "dims": {d: dim_avg[d] for d in SCORE_WEIGHTS},
            "weights": SCORE_WEIGHTS, "detail": detail, "verdict": verdict}


# ---------------------------------------------------------------------------
# 5.8 事件静默
# ---------------------------------------------------------------------------
def event_silence(hours_to_event: float, star: int = 5) -> dict:
    """自动计算距离事件小时数，触发静默规则。"""
    new_allowed = hours_to_event >= EVENT_SILENCE_H
    fomc_clear = hours_to_event <= FOMC_CLEAR_H
    return {
        "hours_to_event": round(hours_to_event, 2),
        "new_position_allowed": new_allowed,
        "fomc_pre24h_clear": fomc_clear,
        "star": star,
        "rule": "事件前%.0fh不开新仓；议息前%.0fh清仓/最小仓" % (EVENT_SILENCE_H, FOMC_CLEAR_H),
    }


# ---------------------------------------------------------------------------
# 5.9 回测（样本不足禁止年化预测）
# ---------------------------------------------------------------------------
def backtest(trades: list):
    """trades: [{pnl, r}]。返回统计；样本<100 禁止年化预测。"""
    n = len(trades)
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    wr = len(wins) / n if n else 0.0
    rp = (sum(t["pnl"] for t in wins) / len(wins)) if wins else 0.0
    rl = (abs(sum(t["pnl"] for t in losses)) / len(losses)) if losses else 0.0
    payoff = rp / rl if rl else 0.0
    rs = [t["r"] for t in trades]
    ev = mean(rs) if rs else 0.0
    enough = n >= BACKTEST_MIN
    return {
        "n": n, "win_rate": round(wr * 100, 2), "payoff": round(payoff, 2),
        "expectancy_r": round(ev, 3), "sample_enough": enough,
        "annualized_prediction": ("禁止(样本<100笔)" if not enough else "可在样本外/Walk-forward/蒙特卡洛后给出"),
    }


# ---------------------------------------------------------------------------
# 第八章 一致性校验清单
# ---------------------------------------------------------------------------
def consistency_check(d: dict) -> list:
    """d 含快照价/图表收盘/计算器价/浮盈/单笔风险/净值/凯利/相关性/评分/事件。
    返回问题列表 [] 表示通过。
    """
    issues = []
    snap = d.get("snapshot_price")
    chart = d.get("chart_close")
    calc = d.get("calc_price")
    if not (snap is None or chart is None or calc is None):
        if not (abs(snap - chart) < 1e-6 and abs(snap - calc) < 1e-6):
            issues.append("价格不一致: 快照%.5f / 图表收盘%.5f / 计算器%.5f" % (snap, chart, calc))
    if d.get("pnl") is not None and d.get("pnl_calc") is not None:
        if abs(d["pnl"] - d["pnl_calc"]) > max(0.01, abs(d["pnl"]) * 0.01):
            issues.append("浮盈矛盾: 报告%.2f vs 计算%.2f" % (d["pnl"], d["pnl_calc"]))
    if d.get("single_risk") is not None and d.get("equity"):
        pct = d["single_risk"] / d["equity"] * 100
        if pct > RISK_HARD_CAP + 1e-6:
            issues.append("单笔风险超 1%%: %.2f%%" % pct)
    if d.get("kelly_tier_pct") is not None and d.get("final_lots") is not None:
        if d.get("veto") and d["final_lots"] > 0:
            issues.append("凯利负期望却给仓: 应 0 手")
    if d.get("score_total") is not None and d.get("score_dims"):
        recon = sum(d["score_dims"][k] * w for k, w in SCORE_WEIGHTS.items())
        if abs(recon - d["score_total"]) > 0.05:
            issues.append("评分加权和不等于总分: %.2f vs %.2f" % (recon, d["score_total"]))
    if d.get("corr_text_high") and d.get("corr_matrix"):
        # 文字高相关对必须矩阵 r>=0.6，低相关必须 r<=0.3
        for a, b, r in d["corr_text_high"]:
            if d["corr_matrix"].get(a, {}).get(b, 0) < 0.6:
                issues.append("相关性文字与矩阵冲突(高): %s/%s" % (a, b))
    return issues


if __name__ == "__main__":
    # 自检：用真实 AUDJPY 持仓验证 v2.3 矛盾已修复
    # 注：以下 USDJPY / 现价 / 止损距离为示例值，实盘请传当日结算汇率与真实止损
    USDJPY = 153.478
    pv = pip_value_per_pip("AUDJPY", 0.02, USDJPY)
    print("AUDJPY 0.02手 每pip价值 = $%.4f (实时计算 | lot_unit x pip / USDJPY)" % pv)
    p = pnl("AUDJPY", "SELL", 114.573, 110.121, 0.02, USDJPY)
    print("AUDJPY SELL 0.02 浮盈(114.573->110.121) = $%.2f" % p)
    lots = compute_lots(574.23, 1.0, 32.7, "AUDJPY", USDJPY)
    print("AUDJPY 1%%风险/止损32.7pip 手数 = %.4f 手" % lots)
    k = kelly_recommended_lots(574.23, 1.0, 32.7, "AUDJPY", USDJPY, 62.5, 1.85, user_cap=0.02)
    print("凯利推荐: 全%.2f%%/半%.2f%%/三%.2f%% 最终手数%.4f(%s) 否决=%s"
          % (k["kelly_full_pct"], k["kelly_half_pct"], k["kelly_third_pct"], k["final_lots"], k["binder"], k["veto"]))
    sc = score_4d({"macro": {"rate_diff": 70, "cpi": 65}, "tech": {"trend": 80, "structure": 75},
                   "quant": {"sharpe": 60, "hurst": 55}, "sentiment": {"cftc": 70, "news": 65}})
    print("评分: 总分%.2f 维%s 判定%s" % (sc["total"], sc["dims"], sc["verdict"]))
    # 一致性校验演示（构造一个价格矛盾场景）
    bad = {"snapshot_price": 110.121, "chart_close": 110.46967, "calc_price": 110.47,
           "score_total": 80, "score_dims": {"macro": 75, "tech": 80, "quant": 80, "sentiment": 85}}
    print("一致性校验(故意矛盾):", consistency_check(bad))
    good = {"snapshot_price": 110.121, "chart_close": 110.121, "calc_price": 110.121,
            "score_total": 79.75, "score_dims": {"macro": 75, "tech": 80, "quant": 80, "sentiment": 85}}
    print("一致性校验(已修正):", consistency_check(good))
