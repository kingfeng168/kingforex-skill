# -*- coding: utf-8 -*-
r"""
kingforex-skill · 决策增强版报告生成器 v2.5.0

严格基于固化模板 assets/decision_enhanced_template.html 生成「今日行情分析 · 决策增强版」。
本次四项变更：
  1. 模板固化：以 assets/decision_enhanced_template.html 为唯一骨架，严禁调格式
  2. 止损止盈合理性评估：新增第 ⑭·补 节（调用 sl_tp_evaluate 引擎口径）
  3. 凯利使用注意事项：从第 ⑪ 节底部迁移至左侧「凯利公式原理」卡片红框区
  4. 仓位评估：改为「五角度评估表 + 最终仓位选择」双段结构（参照 v15.2 情景推荐格式；原六角度，2026-09-21 事件静默角度移除）

用法:
  python decision_enhanced_report_v25.py --date 2026-09-15 --out <目录>
"""
import os
import sys
import csv
import json
import math
import argparse
import datetime as _dt

# 中文 Windows(cp936 控制台)下,print 含 ⑪/⚠ 等字符会抛 UnicodeEncodeError 并中断
# (2026-09-28 修复)。改为不可编码字符降级替换,不改变控制台原生编码,中文照常显示。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(BASE)
ASSETS = os.path.join(SKILL, "assets")
TEMPLATE = os.path.join(ASSETS, "decision_enhanced_template.html")
ECHARTS = os.path.join(ASSETS, "echarts.min.js")

# ---- 统一事实来源: calc_engine.CONTRACTS(合约单位 + pip 刻度) ----
# 修复(2026-09-28): 本文件原自带一份 pip 口径(黄金/白银=0.1,且黄金每 pip 用
# `100.0 * 0.1 * 10.0` 硬凑出 $100),与 calc_engine 的 pip=1.0(黄金)/0.01(白银)相差 10 倍,
# 导致 ⑭·补 节的 pip 距离、ATR sanity、SL/TP 距离在黄金/白银上口径不一致。
# v2.5.2 / v2.5.4 / v2.5.6 生成器均 import 本模块,故此处统一即全链路统一。
if BASE not in sys.path:
    sys.path.insert(0, BASE)
try:
    import calc_engine as _CE
    _CONTRACTS = _CE.CONTRACTS
except Exception:                                    # pragma: no cover
    _CE = None
    _CONTRACTS = {}

_ALIAS = {"XAU": "XAUUSD", "GOLD": "XAUUSD", "XAG": "XAGUSD", "SILVER": "XAGUSD",
          "WTI": "USOIL", "CL": "USOIL", "OIL": "USOIL", "CRUDE": "USOIL"}


def _contract(symbol):
    """取 calc_engine 合约规格(支持 XAU/XAG/WTI 等别名);未登记返回 None。"""
    if not symbol:
        return None
    s = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
    return _CONTRACTS.get(s) or _CONTRACTS.get(_ALIAS.get(s, ""))


# ══════════════════════════════════════════════════════════════════
#  引擎：止损止盈合理性评估（与 scripts/sl_tp_evaluate.py 同口径）
# ══════════════════════════════════════════════════════════════════

def pip_scale(symbol):
    """1 pip 的价格增量(优先 calc_engine 合约表 = 唯一事实来源)。"""
    c = _contract(symbol)
    if c:
        return c["pip"]
    s = symbol.upper()
    if "JPY" in s:
        return 0.01
    if s.startswith("XAU") or s.startswith("XAG"):
        return 0.1
    return 0.0001


def to_pips(a, b, pip):
    return abs(a - b) / pip


# ══════════════════════════════════════════════════════════════════
#  引擎：量化验证（§九）· 分标的独立雷达（v2.5.2 起, 禁止多标的一张图叠加）
# ══════════════════════════════════════════════════════════════════

def quant_block(sym, klines):
    """计算单标的六维量化画像: (|Hurst|, |Z|, |Sharpe|, |Sortino|, |偏度|, 日VaR95%)。
    - Hurst: 对 log 价格序列做 R/S 回归（趋势持续性标准口径, 非收益序列）
    - Z: 收盘价相对 60 日窗口均值的标准差倍数（修正旧版误用收益均值+标准误的 bug）
    - 返回绝对值, 供雷达图按轴 max 归一化展示幅度
    klines: dict[symbol] -> list of OHLC rows, 每行 [t, o, h, l, c, v]
    """
    cs = [r[4] for r in klines[sym]]
    rs = [(cs[i] - cs[i - 1]) / cs[i - 1] for i in range(1, len(cs))]
    n = len(rs)
    mu = sum(rs) / n
    var = sum((x - mu) ** 2 for x in rs) / (n - 1)
    sd = math.sqrt(var)
    sharpe = mu / sd * math.sqrt(252) if sd else 0
    dn = sum(1 for x in rs if x < 0) or 1
    sortino = mu / (math.sqrt(sum(x * x for x in rs if x < 0) / dn)) * math.sqrt(252) if sd else 0
    skew = sum((x - mu) ** 3 for x in rs) / n / (sd ** 3) if sd else 0

    def _hurst(s):
        """Hurst 统一走 quant_metrics.hurst_dfa（唯一事实来源）。

        修复(2026-09-28): 原为本地 R/S 实现(仅 4/8/16/32 四个 lag、非重叠、未修正),
        与 quant_metrics 的口径不一致且系统性高估。现委托 DFA-1(随机游走实测均值 0.505)。
        """
        try:
            import quant_metrics as _qm
            v = _qm.hurst_dfa(s)
            return 0.5 if v is None else v
        except Exception:
            # 兜底: 模块不可用时退化为 0.5(不判趋势), 而不是给出有偏的高值
            return 0.5

    h = _hurst(cs)
    w = min(60, len(cs))
    seg_px = cs[-w:]
    pm = sum(seg_px) / len(seg_px)
    psd = math.sqrt(sum((x - pm) ** 2 for x in seg_px) / len(seg_px))
    z = (cs[-1] - pm) / psd if psd else 0
    var95 = abs(sorted(rs)[int(0.05 * n)]) * 100 if n > 10 else 0
    return abs(h), abs(z), abs(sharpe), abs(sortino), abs(skew), var95


def radar_option(name, vals, color, area):
    """分标的独立雷达 option 工厂 —— v2.5.2 起每个标的一个坐标系, 不再叠加多标的一张图。
    vals: [Hurst, Z, Sharpe, Sortino, |偏度|, 日VaR95]（与 quant_block 返回顺序一致）
    """
    return {
        "backgroundColor": "transparent", "tooltip": {},
        "legend": {"data": [name], "textStyle": {"color": "#a8b8d0"}},
        "radar": {"radius": "55%", "center": ["50%", "54%"],
                  "indicator": [{"name": "趋势强度|Hurst|", "max": 1}, {"name": "偏离|Z|", "max": 3},
                                {"name": "年化Sharpe", "max": 3}, {"name": "Sortino", "max": 4},
                                {"name": "|偏度|", "max": 2}, {"name": "日VaR95%", "max": 3}],
                  "axisName": {"color": "#a8b8d0", "fontSize": 11},
                  "splitLine": {"lineStyle": {"color": "rgba(127,169,255,.15)"}},
                  "splitArea": {"areaStyle": {"color": ["rgba(127,169,255,.02)", "rgba(127,169,255,.05)"]}},
                  "axisLine": {"lineStyle": {"color": "rgba(127,169,255,.2)"}}},
        "series": [{"type": "radar", "data": [{"value": [round(v, 2) for v in vals],
                                                 "name": name, "areaStyle": {"color": area},
                                                 "lineStyle": {"color": color}}]}]
    }


def pip_value_account_per_stdlot(symbol, usdjpy):
    """标准手每 pip 的账户币价值（USD 计价账户）。

    修复(2026-09-28): 原实现对黄金用 `100.0 * 0.1 * 10.0` 硬凑 $100(隐含 pip=0.1 且
    1000 盎司/手),对白银写死 0.01 而其 pip_scale 返回 0.1——两处均与 calc_engine 不一致。
    现统一由 calc_engine.CONTRACTS 推导(1 标准手 = 100 × 每 0.01 手单位数)。
    """
    c = _contract(symbol)
    if c and not c.get("index"):
        pv = 100.0 * c["lot_unit"] * c["pip"]
        return (pv / usdjpy) if c.get("jpy") else pv
    s = symbol.upper()
    pip = pip_scale(s)
    if s.endswith("JPY"):
        # 报价币为 JPY：100000 × pip ÷ USDJPY
        return 100000.0 * pip / usdjpy
    if s.startswith("XAU"):
        # 100 盎司/标准手，pip = 0.1 → 每 pip = $10
        return 100.0 * 0.1 * 10.0
    if s.startswith("XAG"):
        # 5000 盎司/标准手，pip = 0.01 → 每 pip = $50
        return 5000.0 * 0.01
    return 100000.0 * pip


def evaluate_sl_tp(direction, entry, sl, tp, current, symbol,
                   equity, lot, usdjpy=154.885, atr=None, pip=None):
    """返回止损止盈合理性评估结果（与 sl_tp_evaluate.py 判定逻辑一致）"""
    pip = pip or pip_scale(symbol)
    pv_std = pip_value_account_per_stdlot(symbol, usdjpy)
    pv = pv_std * lot

    sign = 1.0 if direction.upper() == "SELL" else -1.0
    entry_to_sl = to_pips(entry, sl, pip)
    entry_to_tp = to_pips(entry, tp, pip)
    cur_to_sl = to_pips(current, sl, pip)
    cur_to_tp = to_pips(current, tp, pip)

    init_rr = (entry_to_tp / entry_to_sl) if entry_to_sl > 0 else 0.0
    rest_rr = (cur_to_tp / cur_to_sl) if cur_to_sl > 0 else float("inf")

    pl_pips = (entry - current) / pip * sign
    pl_usd = pl_pips * pv
    pl_pct = (pl_usd / equity * 100.0) if equity else 0.0

    risk_usd = entry_to_sl * pv
    risk_pct = (risk_usd / equity * 100.0) if equity else 0.0

    # SL 方向校验：空单 SL 应在入场上方；多单 SL 应在入场下方
    if direction.upper() == "SELL":
        sl_side_ok = sl > entry
        sl_triggered = (sl > entry and current >= sl) or (sl < entry and current <= sl)
    else:
        sl_side_ok = sl < entry
        sl_triggered = (sl < entry and current <= sl) or (sl > entry and current >= sl)

    sl_triggered_pips = pl_pips if sl_triggered else 0.0

    # ATR 宽度 sanity：SL 距离应为 1.0× ~ 3.0× ATR
    atr_ratio = (entry_to_sl * pip / atr) if (atr and atr > 0) else None

    flags = []

    # ── 判定 1：SL 反向（空单把 SL 移到入场下方=获利区）──
    if not sl_side_ok:
        if cur_to_sl > 3.0 * cur_to_tp:
            flags.append(("severe", "SL_REVERSED",
                          "止损位于入场%s（获利区）· 距离 %.1f pip 是剩余空间 %.1f pip 的 %.1f 倍 → 非保护性止损"
                          % ("下方" if direction.upper() == "SELL" else "上方",
                             cur_to_sl, cur_to_tp, cur_to_sl / cur_to_tp if cur_to_tp else 0)))
        else:
            flags.append(("warn", "TRAIL_SUGGEST",
                          "止损已移至获利区（锁利 %.1f pip）· 属锁利而非防亏 → 确认是否符合离场计划"
                          % pl_pips))

    # ── 判定 2：剩余 R:R 崩塌 ──
    if not sl_triggered and cur_to_sl > 0:
        if rest_rr < 0.5:
            flags.append(("severe", "REST_RR_BROKEN",
                          "剩余 R:R = %.2f（< 0.50）· 用 %.1f pip 风险博 %.1f pip 空间 → 赔率崩塌"
                          % (rest_rr, cur_to_sl, cur_to_tp)))
        elif rest_rr < 1.5:
            flags.append(("warn", "REST_RR_LOW",
                          "剩余 R:R = %.2f（< 1.50）· 低于最低盈亏比门槛" % rest_rr))

    # ── 判定 3：初始 R:R ──
    if init_rr < 1.5:
        flags.append(("severe" if init_rr < 1.0 else "warn", "BAD_INIT_RR",
                      "初始 R:R = %.2f · 低于最低 1.5 门槛" % init_rr))

    # ── 判定 4：单笔风险超限（硬上限 = calc_engine.RISK_HARD_CAP = 1%）──
    # 修复(2026-09-28): 原 severe 阈值写死 2.0，比框架铁律(1%)宽一倍；现与
    # calc_engine / sl_tp_evaluate 同口径：>硬上限 = severe，>硬上限一半 = warn(小账户保守口径)。
    _risk_cap = getattr(_CE, "RISK_HARD_CAP", 1.0) if _CE else 1.0
    if risk_pct > _risk_cap:
        flags.append(("severe", "OVER_RISK",
                      "建仓单笔风险 $%.2f = %.2f%% · 超 %.1f%% 硬上限"
                      % (risk_usd, risk_pct, _risk_cap)))
    elif risk_pct > _risk_cap / 2.0:
        flags.append(("warn", "OVER_1PCT",
                      "建仓单笔风险 $%.2f = %.2f%% · 已越过小账户保守口径 %.1f%%（硬上限 %.1f%%）"
                      % (risk_usd, risk_pct, _risk_cap / 2.0, _risk_cap)))

    # ── 判定 5：ATR 宽度 ──
    if atr_ratio is not None:
        if atr_ratio < 0.8:
            flags.append(("warn", "SL_TOO_TIGHT",
                          "SL 距离 = %.2f× ATR · 过窄，易被噪音扫损（建议 ≥1.0×）" % atr_ratio))
        elif atr_ratio > 3.0:
            flags.append(("warn", "SL_TOO_WIDE",
                          "SL 距离 = %.2f× ATR · 过宽，风险放大（建议 ≤3.0×）" % atr_ratio))

    # ── 最终判定 ──
    if sl_triggered and sl_triggered_pips > 0:
        # 已锁利离场 → 判定成立，风险类警示降级
        for i, f in enumerate(flags):
            if f[1] in ("OVER_RISK", "OVER_1PCT", "BAD_INIT_RR") and f[0] == "severe":
                flags[i] = ("warn", f[1], f[2])
        verdict = "REASONABLE"
    else:
        levels = [f[0] for f in flags]
        if "severe" in levels:
            verdict = "UNREASONABLE"
        elif "warn" in levels:
            verdict = "CAUTION"
        else:
            verdict = "REASONABLE"

    return {
        "symbol": symbol, "direction": direction.upper(),
        "entry": entry, "sl": sl, "tp": tp, "current": current,
        "pip": pip, "pip_value": round(pv, 4), "pip_value_std": round(pv_std, 4),
        "entry_to_sl_pips": round(entry_to_sl, 1),
        "entry_to_tp_pips": round(entry_to_tp, 1),
        "cur_to_sl_pips": round(cur_to_sl, 1),
        "cur_to_tp_pips": round(cur_to_tp, 1),
        "init_rr": round(init_rr, 2), "rest_rr": round(rest_rr, 2),
        "pl_pips": round(pl_pips, 1), "pl_usd": round(pl_usd, 2),
        "pl_pct": round(pl_pct, 2),
        "risk_usd": round(risk_usd, 2), "risk_pct": round(risk_pct, 2),
        "sl_side_ok": sl_side_ok, "sl_triggered": sl_triggered,
        "sl_triggered_pips": round(sl_triggered_pips, 1),
        "atr": atr, "atr_ratio": round(atr_ratio, 2) if atr_ratio else None,
        "verdict": verdict,
        "flags": [{"level": lv, "code": cd, "msg": ms} for lv, cd, ms in flags],
    }


# ══════════════════════════════════════════════════════════════════
#  引擎：仓位多角度评估
# ══════════════════════════════════════════════════════════════════

def evaluate_position(equity, sl_pips, pip_value_per_std, p, b,
                      atr=None, atr_mult=1.5, portfolio_cap_pct=5.0,
                      open_risk_pct=0.0, event_silent=False, event_name="",
                      min_lot=0.01, pip=None):
    """
    六个角度分别给出建议手数，再收敛为唯一「最终仓位选择」。

    ⚠️ 参数口径（易错点）：
      - `pip_value_per_std` 为「**每 0.01 手**每 pip 的账户币价值」（函数内 ×100 转成
        每标准手口径）。AUDJPY @USDJPY 155 时约 0.0645；**不要传每标准手的 6.45**，
        否则手数会被缩小 100 倍。
      - `sl_pips` 为**止损距离（pips）**，不是价格差。
      - `pip` 为该品种的 pip 最小变动单位（JPY 对 0.01 / XAU·XAG 0.1 / 其余 0.0001），
        仅角度 4（ATR 波动匹配）需要；缺省时按 JPY 口径 0.01 推断。

    角度：
      1. 凯利理论（半凯利，含 1% 硬上限约束）
      2. 1% 单笔风险硬上限
      3. 0.5% 小账户保守口径
      4. ATR 波动匹配（按 1.5×ATR 止损距离反推，与结构止损取较宽者）
      5. 组合总额风险约束（≤5%，扣除已有敞口）

    ⚠️ 变更记录（2026-09-21 用户指令）：原角度 6「事件静默纪律（事件窗口 → 强制 0 手）」
    已移除——event_silent / event_name 参数仅为向后兼容保留，不再参与收敛、
    不再触发一票否决。当前为五角度收敛。
    """
    pv = pip_value_per_std * 100.0          # 每标准手每 pip 美元

    def lots_from_risk(pct, dist_pips=None):
        d = sl_pips if dist_pips is None else dist_pips
        if d <= 0 or pv <= 0:
            return 0.0
        return equity * pct / 100.0 / (d * pv)

    # 角度 1：凯利
    q = 1.0 - p
    f_full = ((p * b - q) / b) if b > 0 else 0.0
    f_neg = f_full <= 0
    if f_neg:
        f_full = 0.0
    f_half = f_full * 0.5
    f_third = f_full / 3.0
    kelly_budget = min(f_half, 0.01)
    kelly_binding = "1% 硬上限" if f_half > 0.01 else "半凯利档位"
    lots_kelly = lots_from_risk(kelly_budget * 100.0)

    # 角度 2：1% 硬上限
    lots_1pct = lots_from_risk(1.0)

    # 角度 3：0.5% 小账户口径
    lots_05pct = lots_from_risk(0.5)

    # 角度 4：ATR 波动匹配（按 1.5×ATR 止损距离反推 1% 预算下的手数）
    # 与结构止损取较宽者：波动放大时 1.5×ATR 往往宽于结构止损，此时应缩减仓位
    atr_sl_pips = None
    lots_atr = None
    if atr and atr > 0:
        _pip = pip if pip else pip_scale_guess(sl_pips)
        atr_sl_pips = (atr_mult * atr) / _pip
        effective_sl = max(sl_pips, atr_sl_pips)
        lots_atr = lots_from_risk(1.0, effective_sl)

    # 角度 5：组合总额
    room_pct = max(0.0, portfolio_cap_pct - open_risk_pct)
    lots_port = lots_from_risk(min(room_pct, 1.0))

    # (2026-09-21 用户指令) 原角度 6「事件静默」已移除：不再计算 lots_event、
    # 不再进入收敛候选、不再触发一票否决。event_silent 参数仅兼容保留。

    # ── 收敛：取各角度最小值（最保守约束）──
    candidates = [("凯利半仓", lots_kelly), ("1% 硬上限", lots_1pct),
                  ("0.5% 保守口径", lots_05pct), ("组合风险约束", lots_port)]
    if lots_atr is not None:
        candidates.append(("ATR 波动匹配", lots_atr))

    binding_name, binding_lots = min(candidates, key=lambda x: x[1])
    if f_neg:
        final_lots = 0.0
        binding_name = "凯利负期望（否决）"
    else:
        final_lots = binding_lots

    # 落地到手（最小 0.01 手向下取整，绝不向上取整以免突破风险预算）
    pre_floor = final_lots
    below_min = False
    if final_lots > 0:
        floored = math.floor(final_lots / min_lot + 1e-9) * min_lot
        if floored < min_lot - 1e-9:
            # 理论手数不足最小手 → 最小手必然超风险预算
            below_min = True
            final_lots = 0.0
        else:
            final_lots = floored

    final_risk_usd = final_lots * sl_pips * pv
    final_risk_pct = (final_risk_usd / equity * 100.0) if equity else 0.0
    # 若强行下最小手，风险占比（用于说明「为什么 0 手」）
    min_lot_risk_usd = min_lot * sl_pips * pv
    min_lot_risk_pct = (min_lot_risk_usd / equity * 100.0) if equity else 0.0

    return {
        "equity": equity, "sl_pips": sl_pips, "pv_std": pip_value_per_std,
        "p": p, "b": b, "f_full": round(f_full * 100, 2),
        "f_half": round(f_half * 100, 2), "f_third": round(f_third * 100, 2),
        "f_neg": f_neg, "kelly_binding": kelly_binding,
        "angles": {
            "kelly": round(lots_kelly, 4),
            "cap1pct": round(lots_1pct, 4),
            "small05": round(lots_05pct, 4),
            "atr": (round(lots_atr, 4) if lots_atr is not None else None),
            "portfolio": round(lots_port, 4),
        },
        "atr_sl_pips": (round(atr_sl_pips, 1) if atr_sl_pips is not None else None),
        "atr_mult": atr_mult, "atr": atr,
        "room_pct": round(room_pct, 2),
        "binding": binding_name, "binding_lots": round(binding_lots, 4),
        "pre_floor_lots": round(pre_floor, 4),
        "below_min_lot": below_min,
        "min_lot": min_lot,
        "min_lot_risk_usd": round(min_lot_risk_usd, 2),
        "min_lot_risk_pct": round(min_lot_risk_pct, 2),
        "final_lots": round(final_lots, 3),
        "final_risk_usd": round(final_risk_usd, 2),
        "final_risk_pct": round(final_risk_pct, 2),
        "event_silent": event_silent, "event_name": event_name,
    }


def pip_scale_guess(sl_pips):
    return 0.01


# ══════════════════════════════════════════════════════════════════
#  HTML 片段渲染
# ══════════════════════════════════════════════════════════════════

VERDICT_STYLE = {
    "REASONABLE": ("#2ecc71", "✅ 合理", "合理"),
    "CAUTION": ("#f1c40f", "⚠️ 需关注", "需关注"),
    "UNREASONABLE": ("#e74c3c", "⛔ 不合理", "不合理"),
}
FLAG_LEVEL_STYLE = {
    "severe": ("#e74c3c", "严重"),
    "warn": ("#f1c40f", "警示"),
    "info": ("#3498db", "提示"),
}


def render_sl_tp_section(r, title="十四·补、止损止盈合理性评估（引擎判定）"):
    """止损止盈合理性评估 HTML 卡片"""
    color, label, _ = VERDICT_STYLE[r["verdict"]]

    if r["sl_triggered"] and r["sl_triggered_pips"] > 0:
        verdict_note = ("原止损 <b>%.3f</b> 已触发并锁定 <b class='green'>+%.1f pip</b> 盈利 → "
                        "离场纪律成立，判定 <b class='green'>REASONABLE</b>。"
                        "若账户实际仍持有该仓位，说明 <b class='red'>MT4 未挂止损</b>，须立即补挂保护性止损。"
                        % (r["sl"], r["sl_triggered_pips"]))
    elif r["verdict"] == "REASONABLE":
        verdict_note = "止损方向正确、剩余赔率合格、单笔风险在纪律范围内 → 结构可持有。"
    elif r["verdict"] == "CAUTION":
        verdict_note = "存在需关注的瑕疵项（见下方警示），建议按提示修正后再持有。"
    else:
        verdict_note = "存在严重缺陷（见下方警示），<b class='red'>建议立即修正止损或了结仓位</b>。"

    # 六项校验表
    checks = [
        ("SL 方向校验",
         ("<span class='green'>正确 ✓</span>" if r["sl_side_ok"]
          else "<span class='red'>错置 ✗</span>"),
         ("空单 SL 位于入场价上方 → 真正的保护性止损" if r["sl_side_ok"]
          else "空单 SL 位于入场价下方（获利区）→ 非保护性止损，价格上行无真实止损")),
        ("初始 R:R",
         ("<span class='green'>%.2f</span>" % r["init_rr"] if r["init_rr"] >= 1.5
          else "<span class='red'>%.2f</span>" % r["init_rr"]),
         "建仓时（目标空间 ÷ 止损距离）；最低门槛 1.50"),
        ("剩余 R:R",
         ("<span class='green'>%.2f</span>" % r["rest_rr"] if r["rest_rr"] >= 1.5
          else ("<span class='yellow'>%.2f</span>" % r["rest_rr"] if r["rest_rr"] >= 0.5
                else "<span class='red'>%.2f</span>" % r["rest_rr"])),
         "当前（剩余目标空间 %.1f pip ÷ 剩余止损距离 %.1f pip）→ 持仓期的真实赔率"
         % (r["cur_to_tp_pips"], r["cur_to_sl_pips"])),
        ("单笔风险",
         ("<span class='red'>$%.2f（%.2f%%）</span>" % (r["risk_usd"], r["risk_pct"])
          if r["risk_pct"] > 1.0
          else "<span class='green'>$%.2f（%.2f%%）</span>" % (r["risk_usd"], r["risk_pct"])),
         "建仓名义风险 vs 1%% 硬上限（%s）"
         % ("超限" if r["risk_pct"] > 1.0 else "合规")),
        ("浮盈状态",
         "<span class='green'>%+.1f pip</span>" % r["pl_pips"]
         if r["pl_pips"] > 0 else "<span class='red'>%+.1f pip</span>" % r["pl_pips"],
         "+$%.2f（占权益 %+.2f%%）· 止损距离 %s"
         % (r["pl_usd"], r["pl_pct"],
            ("%.1f pip · 剩余 R:R %.2f" % (r["cur_to_sl_pips"], r["rest_rr"]))
            if not r["sl_triggered"] else "已越过 SL → 锁利离场")),
        ("ATR 宽度匹配",
         (("<span class='green'>%.2f× ATR</span>" % r["atr_ratio"])
          if (r["atr_ratio"] and 0.8 <= r["atr_ratio"] <= 3.0)
          else (("<span class='yellow'>%.2f× ATR</span>" % r["atr_ratio"])
                if r["atr_ratio"] else "<span class='yellow'>ATR 未取到</span>")),
         ("止损距离应为 1.0× ~ 3.0× ATR（日 ATR = %.4f，止损 %.1f pip）"
          % (r["atr"], r["entry_to_sl_pips"])) if r["atr"]
         else "ATR 数据不可得 → 该项降级为「未校验」，不阻断判定"),
    ]

    rows = ""
    for name, val, note in checks:
        rows += ("<tr><td class='white'>" + name + "</td><td>" + val +
                 "</td><td class='card-sub' style='border:none;padding:0'>" + note + "</td></tr>")

    # 警示列表
    if r["flags"]:
        warn_html = ""
        for f in r["flags"]:
            c, lv = FLAG_LEVEL_STYLE.get(f["level"], ("#3498db", "提示"))
            warn_html += ("<div style='padding:8px 12px;border-left:3px solid " + c +
                          ";background:rgba(0,0,0,.18);border-radius:6px;margin-bottom:8px'>"
                          "<b style='color:" + c + "'>[" + lv + "] " + f["code"] + "</b> — " +
                          f["msg"] + "</div>")
    else:
        warn_html = ("<div style='padding:8px 12px;border-left:3px solid #2ecc71;"
                     "background:rgba(46,204,113,.08);border-radius:6px'>"
                     "<b class='green'>未发现任何缺陷项</b> — 止损方向、赔率、风险、波动匹配四项全部合格。</div>")

    return ("""<div class="section"><div class="section-title">🛡️ """ + title + """</div>
<div class="card-sub" style="margin-bottom:10px">评估对象: <b class="white">""" + r["symbol"] + """ """ +
            r["direction"] + """</b> · 入场 """ + ("%.3f" % r["entry"]) + """ · SL """ + ("%.3f" % r["sl"]) +
            """ · TP """ + ("%.3f" % r["tp"]) + """ · 现价 """ + ("%.3f" % r["current"]) +
            """ · 手数/每 pip $""" + ("%.4f" % r["pip_value"]) + """（0.01手口径）</div>
<div class="grid grid-4">
<div class="card"><div class="card-title">🎯 综合判定</div>
<div class="card-value" style="color:""" + color + """">""" + label + """</div>
<div class="card-sub">引擎判定 <b>""" + r["verdict"] + """</b><br>六项校验 + 缺陷分级（severe/warn）</div></div>
<div class="card"><div class="card-title">📐 R:R 结构</div>
<div class="card-value" style="color:#3498db">""" + ("%.2f" % r["init_rr"]) + """ → """ + ("%.2f" % r["rest_rr"]) + """</div>
<div class="card-sub">初始 R:R → 剩余 R:R<br>""" + ("已锁利离场" if r["sl_triggered"] else "持仓期真实赔率") + """</div></div>
<div class="card"><div class="card-title">💰 浮盈 / 风险</div>
<div class="card-value" style="color:#2ecc71">""" + ("%+.1f pip" % r["pl_pips"]) + """</div>
<div class="card-sub">+$""" + ("%.2f" % r["pl_usd"]) + """（占权益 """ + ("%+.2f%%" % r["pl_pct"]) + """）<br>
建仓风险 $""" + ("%.2f" % r["risk_usd"]) + """（""" + ("%.2f%%" % r["risk_pct"]) + """）</div></div>
<div class="card"><div class="card-title">📏 距离结构</div>
<div class="card-value" style="color:#f1c40f">""" + ("%.1f" % r["cur_to_sl_pips"]) + """ / """ + ("%.1f" % r["cur_to_tp_pips"]) + """</div>
<div class="card-sub">至 SL / 至 TP（pips）<br>入场距 SL """ + ("%.1f" % r["entry_to_sl_pips"]) + """ · 距 TP """ + ("%.1f" % r["entry_to_tp_pips"]) + """</div></div>
</div>
<table class="journal-table" style="margin-top:14px">
<tr><th style="width:16%">校验项</th><th style="width:22%">结果</th><th>说明</th></tr>""" + rows + """</table>
<div class="sub-title">缺陷分级明细（severe = 严重 · warn = 警示）</div>
""" + warn_html + """
<div class="verdict-warn"><b>💡 引擎结论:</b> """ + verdict_note + """</div>
</div>""")


def render_position_section(pos, title="十一·补、仓位多角度评估与最终仓位选择", subtitle=""):
    """仓位多角度评估 + 最终仓位选择（参照 v15.2 情景推荐格式）"""
    a = pos["angles"]
    eq = pos["equity"]

    def usd_of(lots):
        return lots * pos["sl_pips"] * pos["pv_std"] * 100.0

    def pct_of(lots):
        return (usd_of(lots) / eq * 100.0) if eq else 0.0

    # 五角度表
    angle_rows = [
        ("① 凯利理论（半凯利）",
         "%.2f%%" % pos["f_half"],
         "%.4f 手" % a["kelly"],
         "$%.2f（%.2f%%）" % (usd_of(a["kelly"]), pct_of(a["kelly"])),
         "半凯利档 %.2f%% ｜ 约束：%s" % (pos["f_half"], pos["kelly_binding"]),
         "yellow" if a["kelly"] > a["cap1pct"] else ""),
        ("② 1% 单笔风险硬上限",
         "1.00%",
         "%.4f 手" % a["cap1pct"],
         "$%.2f（%.2f%%）" % (usd_of(a["cap1pct"]), pct_of(a["cap1pct"])),
         "纪律红线：单笔风险永不突破 1%",
         ""),
        ("③ 0.5% 小账户保守口径",
         "0.50%",
         "%.4f 手" % a["small05"],
         "$%.2f（%.2f%%）" % (usd_of(a["small05"]), pct_of(a["small05"])),
         "净值 &lt; $700 阶段优先 0.5% 口径，保命优先",
         "green"),
        ("④ 组合总额风险约束",
         "≤%.2f%%" % pos["room_pct"],
         "%.4f 手" % a["portfolio"],
         "$%.2f（%.2f%%）" % (usd_of(a["portfolio"]), pct_of(a["portfolio"])),
         "总风险上限 5.00%% · 已占用 %.2f%% → 余量 %.2f%%" % (round(5.0 - pos["room_pct"], 2), pos["room_pct"]),
         ""),
        ("⑤ ATR 波动匹配",
         "按 %.1f×ATR" % pos.get("atr_mult", 1.5),
         ("%.4f 手" % a["atr"]) if a.get("atr") is not None else "—",
         ("$%.2f（%.2f%%）" % (usd_of(a["atr"]), pct_of(a["atr"]))) if a.get("atr") is not None else "—",
         ("1.5×ATR 止损 ≈ %.1f pips ｜ 与结构止损取较宽者后按 1%% 预算反推" % pos["atr_sl_pips"])
         if pos.get("atr_sl_pips") else "ATR 缺失，本角度跳过",
         "yellow" if (a.get("atr") is not None and a["atr"] < a["cap1pct"]) else ""),
        # (2026-09-21 用户指令) 原角度 ⑥ 事件静默纪律行已移除
    ]

    arows = ""
    for name, budget, lots, usd, note, cls in angle_rows:
        arows += ("<tr><td class='white'>" + name + "</td><td class='" + (cls or "white") + "'>" + budget +
                  "</td><td class='" + (cls or "white") + "'>" + lots +
                  "</td><td class='" + (cls or "white") + "'>" + usd +
                  "</td><td class='card-sub' style='border:none;padding:0'>" + note + "</td></tr>")

    # 最终选择
    if pos["final_lots"] > 0:
        final_lots_txt = "%.3f 手" % pos["final_lots"]
        final_color = "green"
        action = ("按 %s 约束建仓 %.3f 手（理论 %.4f 手向下取整）· 风险 $%.2f（%.2f%%）"
                  % (pos["binding"], pos["final_lots"], pos["pre_floor_lots"],
                     pos["final_risk_usd"], pos["final_risk_pct"]))
    elif pos.get("below_min_lot") and not pos["f_neg"]:
        final_lots_txt = "0.000 手（最小手超预算 · 不可交易）"
        final_color = "yellow"
        action = ("理论手数 %.4f 手 < 最小手 %.2f 手 → 若强行下最小手，"
                  "风险 $%.2f（<b class='red'>%.2f%%</b>）将突破 %s 预算 → "
                  "<b class='red'>判定不可交易</b>，须等止损距离收窄或净值增长后重估"
                  % (pos["pre_floor_lots"], pos["min_lot"], pos["min_lot_risk_usd"],
                     pos["min_lot_risk_pct"], pos["binding"]))
    else:
        final_lots_txt = "0.000 手（空仓）"
        final_color = "yellow"
        action = ("<b class='red'>%s</b> → 今日不建仓" % pos["binding"])

    return ("""<div class="section"><div class="section-title">📐 """ + title + """</div>
""" + (('<div class="card-sub" style="margin-bottom:10px">' + subtitle + '</div>') if subtitle else "") + """
<div class="sub-title">五角度评估（横向对比 · 每个角度独立给出建议手数）</div>
<table>
<tr><th style="width:20%">评估角度</th><th style="width:11%">风险预算</th><th style="width:12%">建议手数</th><th style="width:15%">对应风险</th><th>依据 / 约束</th></tr>""" + arows + """</table>
<div class="card-sub" style="margin-top:8px">收敛规则: 取五角度中的<b class="yellow">最小值</b>为实际约束（最保守者胜出）；凯利负期望直接否决。落地按最小手 0.01 手<b>向下取整</b>，绝不向上取整以免突破风险预算。</div>

<div class="recommendation" style="margin-top:14px"><h3>🎯 最终仓位选择: """ + final_lots_txt + """ —— """ + pos["binding"] + """</h3>
<table><tr><th style="width:16%">项目</th><th>具体操作</th></tr>
<tr><td>评估标的</td><td class="white">""" + pos.get("symbol", "AUDJPY") + """（""" + pos.get("direction", "SELL") + """）</td></tr>
<tr><td>仓位口径</td><td>""" + pos["binding"] + """（五角度最小值收敛）</td></tr>
<tr><td>最终手数</td><td class='""" + final_color + """'>""" + final_lots_txt + """</td></tr>
<tr><td>单笔风险</td><td>$""" + ("%.2f" % pos["final_risk_usd"]) + """ = """ + ("%.2f%%" % pos["final_risk_pct"]) + """（账户净值 $""" + ("%.2f" % eq) + """）</td></tr>
<tr><td>止损距离</td><td>""" + ("%.1f" % pos["sl_pips"]) + """ pips · 每标准手每 pip $""" + ("%.4f" % pos["pv_std"]) + """</td></tr>
<tr><td>凯利参考</td><td>全凯利 """ + ("%.2f%%" % pos["f_full"]) + """ ｜ 半凯利 """ + ("%.2f%%" % pos["f_half"]) + """ ｜ 三分之一凯利 """ + ("%.2f%%" % pos["f_third"]) + ("""  <b class="red">（负期望 · 否决）</b>""" if pos["f_neg"] else "") + """</td></tr>
<tr><td>组合约束</td><td>总风险上限 5.00%% · 当前占用 """ + ("%.2f%%" % (5.0 - pos["room_pct"])) + """% · 剩余余量 """ + ("%.2f%%" % pos["room_pct"]) + """</td></tr>
<tr><td>执行结论</td><td>""" + action + """</td></tr>
</table></div>
</div>""")


# ══════════════════════════════════════════════════════════════════
#  模板装配
# ══════════════════════════════════════════════════════════════════

KELLY_NOTES_HTML = """<div class="verdict-warn" style="margin-top:14px"><b>💡 凯利公式使用注意:</b> ① 凯利假设连胜连败分布均匀, 但实际交易存在连续亏损期, 因此<b class="yellow">半凯利是实战最优解</b>; ② 单笔风险 ≤1% 是硬纪律, 凯利结果超过 1% 时以 1% 为准 (本例 0.5% 账户风险 = $__LOSS05__ = __LOTS05__ 手, 远低于凯利理论值, 说明小账户的真实约束是「1% 纪律」而非凯利); ③ 凯利只适用于正期望值系统 (胜率×盈亏比 &gt; 1), 负期望系统任何仓位都是错的; ④ <b class="yellow">切换投资标的时</b>, 右侧自动代入该品种的 pip 价值与参考止损距离, 但胜率/盈亏比应替换为该标的自身回测参数 (左侧默认展示 __SYMBOL__ 样本), 再点「重新计算」。</div>"""


# ── 变更③ 锚点：左卡「三分之一凯利 (保守)」表格行结束 → </table></div> ──
KELLY_LEFT_ANCHOR = """<tr><td>三分之一凯利 (保守)</td><td class='yellow' style="text-align:right">14.08%</td></tr>
</table></div>"""


def patch_kelly_notes(html, symbol="AUDJPY", loss05=2.87, lots05=0.003):
    """变更③：把凯利使用注意事项从节底 verdict-warn 迁入左侧卡片红框区。"""
    notes = (KELLY_NOTES_HTML
             .replace("__LOSS05__", "%.2f" % loss05)
             .replace("__LOTS05__", "%.3f" % lots05)
             .replace("__SYMBOL__", symbol))

    # (a) 删除节底原有的注意事项块（位于 </div>\n</div>\n<script>\nvar INST= 之前）
    old_tail_marker = "再点「重新计算」。</div>\n</div>\n<script>\nvar INST={"
    if old_tail_marker in html:
        html = html.replace(old_tail_marker, "再点「重新计算」。</div>\n</div>\n<script>\nvar INST={", 1)
        # 精确定位并移除该 verdict-warn 块
        i = html.find("凯利公式使用注意")
        if i > 0:
            blk_start = html.rfind('<div class="verdict-warn"', 0, i)
            blk_end = html.find("再点「重新计算」。</div>", i)
            if blk_start > 0 and blk_end > 0:
                blk_end += len("再点「重新计算」。</div>")
                html = html[:blk_start] + html[blk_end:]

    # (b) 注入左卡红框区
    if KELLY_LEFT_ANCHOR in html:
        html = html.replace(KELLY_LEFT_ANCHOR,
                            KELLY_LEFT_ANCHOR.replace("</table></div>",
                                                       "</table>\n" + notes + "\n</div>"), 1)
        return html, 1
    return html, 0


# ── 变更④ 锚点：⑪ 节结束 → ⑫ 节开始 ──
def patch_position_angles(html, block):
    """变更④：在凯利节之后、相关性节之前插入五角度评估块。"""
    marker = '<div class="section"><div class="section-title">🔗 十二、收益相关性热力图'
    if marker in html:
        html = html.replace(marker, block + marker, 1)
        return html, 1
    return html, 0


# ── 变更② 锚点：⑮ 节开始 → 插入 ⑭·补 节 ──
def patch_sl_tp_section(html, block):
    """变更②：在第十五节（综合判定）之前插入止损止盈合理性评估节。"""
    marker = '<div class="section"><div class="section-title">💡 十五、综合判定与操作建议</div>'
    if marker in html:
        html = html.replace(marker, block + marker, 1)
        return html, 1
    return html, 0


def main():
    ap = argparse.ArgumentParser(description="决策增强版报告生成器 v2.5.0")
    ap.add_argument("--template", default=TEMPLATE, help="模板路径")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--date", default="2026-09-15", help="报告日期")
    args = ap.parse_args()

    # ── 实盘参数（AUDJPY 空单） ──
    SYM = "AUDJPY"
    DIRECTION = "SELL"
    ENTRY, SL, TP, CUR = 114.573, 113.284, 109.781, 111.97327
    EQUITY, LOT = 607.09, 0.02
    USDJPY, ATR = 157.118, 0.8617
    SL_NEW = 112.50          # 已挂的保护性止损
    WD_SL_PIPS = 52.7        # 预案止损距离
    PIP_VAL_STD = 0.0651     # 每标准手每 pip（0.01 手口径 $0.0651）

    sltp = evaluate_sl_tp(DIRECTION, ENTRY, SL, TP, CUR, SYM,
                          EQUITY, LOT, usdjpy=USDJPY, atr=ATR)

    # (2026-09-21 用户指令) 事件静默纪律已移除 → 不再传入 event_silent/event_name
    pos = evaluate_position(EQUITY, WD_SL_PIPS, PIP_VAL_STD, 0.625, 1.85)
    pos["symbol"] = SYM
    pos["direction"] = DIRECTION

    # 构建三大 HTML 片段（此处由外部注入，本函数负责装配）
    global SLTP_BLOCK, POSITION_BLOCK
    SLTP_BLOCK = render_sl_tp_section(sltp)
    POSITION_BLOCK = render_position_section(
        pos,
        subtitle=("评估对象 <b class='white'>%s %s</b> · 账户净值 $%.2f · 预案止损距离 %.1f pips · "
                  "每标准手每 pip $%.4f ｜ 本节从六个独立角度评估仓位，最终收敛为唯一可执行手数。"
                  % (SYM, DIRECTION, EQUITY, WD_SL_PIPS, PIP_VAL_STD)))

    with open(args.template, "r", encoding="utf-8") as f:
        html = f.read()

    print("[INFO] 模板载入 OK: %d chars" % len(html))
    print("[ENG] SL/TP 判定: %s | initRR=%.2f restRR=%.2f | 浮盈 %+.1f pip = $%.2f"
          % (sltp["verdict"], sltp["init_rr"], sltp["rest_rr"], sltp["pl_pips"], sltp["pl_usd"]))
    print("[ENG] 仓位五角度: %s" % {k: round(v, 4) for k, v in pos["angles"].items()})
    print("[ENG] 最终仓位: %.3f 手 (约束=%s)" % (pos["final_lots"], pos["binding"]))

    html, n3 = patch_kelly_notes(html, symbol=SYM, loss05=2.87, lots05=0.003)
    print("[CHG 3] 凯利使用注意 → 左卡红框区: %s" % ("OK" if n3 else "FAIL"))

    html, n4 = patch_position_angles(html, POSITION_BLOCK)
    print("[CHG 4] 仓位多角度评估块注入: %s" % ("OK" if n4 else "FAIL"))

    html, n2 = patch_sl_tp_section(html, SLTP_BLOCK)
    print("[CHG 2] 止损止盈合理性评估节注入: %s" % ("OK" if n2 else "FAIL"))

    os.makedirs(args.out, exist_ok=True)
    out_html = os.path.join(args.out, "今日行情分析_决策增强版_%s.html" % args.date)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print("[OUT] %s (%.1f KB)" % (out_html, os.path.getsize(out_html) / 1024.0))
    return out_html


if __name__ == "__main__":
    main()
