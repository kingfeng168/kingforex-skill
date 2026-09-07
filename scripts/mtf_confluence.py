#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mtf_confluence.py — 多周期共振(三维印证)分析引擎  (kingforex-skill 模块十)

定位
----
把 kingforex-skill 的「三维印证」哲学落到**可计算、可溯源、结论不含糊**的盘面上:
  宏观/背景方向建立在 周线(W) + 日线(D);
  1H 线只用于**进场时机**确认,不得与大周期反向。

本引擎直接复用 `kline_read.py` 的 `analyze()` 做单周期客观解读(趋势背景、市场结构、
关键位、EMA5/10/60 排列、ATR、趋势线、成交密集区、形态、量价背离),再在聚合层做四件事:

  1. 方向共识矩阵:对 W / D / 1H 各取趋势背景 + EMA 排列 + 摆动结构,三方投票,
     给出每周期「偏多/偏空/中性」及强度,并算出大周期(W+D)背景方向。
  2. 关键位融合(confluence zone):合并三周期阻力/支撑/整数位,邻近(±容差内)的位
     聚类成「共振区」并按重合周期数/测试次数定强度(强/中/弱)。
  3. ATR 跨周期差异量化:对比 W/D/1H 的 ATR14,算日线 ATR 是 1H 的几倍、周线 ATR 是
     日线的几倍,用于止损距离与仓位尺度,并标注波动 regime。
  4. 明确结论:仅在 W+D 背景同向、且 1H 顺向(或回调至支撑区)时给出「做多/做空」
     + 具体入场区/止损(结构外 1.5×ATR_h1)/目标(最近共振阻力区)/R 倍数;
     任一反向 → 「不交易」并指明冲突周期。**禁用模糊词,结论必须基于客观数值**。

铁律(与本技能一致)
------------------
  - 只消费真实传入/抓取的 OHLC;任一周期数据缺失或分析失败,明确降级并说明,绝不编造价格。
  - 数据源(Twelve Data)只提供 OHLC,不提供方向;方向由本引擎的共识逻辑收敛决定。
  - 结论出现「可能/或许/大概/观望待定」等模糊表述即视为缺陷——必须给确定性动作或明确的
    「不交易 + 原因」。

用法
----
  # 本地 CSV(每周期一个文件)
  python mtf_confluence.py --csv-w W.csv --csv-d D.csv --csv-h1 H1.csv --symbol USDJPY --html --json

  # 粘贴文本(每周期一段 OHLC,列:date,o,h,l,c[,v])
  python mtf_confluence.py --text-w "..." --text-d "..." --text-h1 "..." --symbol XAUUSD --html

  # 联网抓取(Twelve Data,需 API Key)
  python mtf_confluence.py --fetch --symbol EURUSD --api-key <KEY> --html --json

输出:`scripts/output/mtf_<SYMBOL>_<日期>.html`(ECharts 图表) + 同名 `.json`(结构化结论)
"""

import argparse
import json
import os
import sys
import datetime

# 复用同一技能内的引擎与抓取器(同目录)
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import kline_read as kr          # parse_csv / parse_text / analyze / ema / atr
import kline_fetch as kf          # fetch_one

# ----------------------------------------------------------------------------
# 常量
# ----------------------------------------------------------------------------
TFS = ["W", "D", "H1"]                       # 周 / 日 / 1小时
TF_LABEL = {"W": "周线", "D": "日线", "H1": "1小时"}
STOP_ATR_MULT = 1.5                          # 触发止损 = 结构外 1.5×ATR_h1 (indicators.md §2)
TARGET_ATR_MULT = 2.0                        # 次级目标参考
MIN_BG_SCORE = 1.5                           # 大周期背景达到此分才认定方向(见 resolve())
CONFLUENCE_TOL_PCT = 0.003                   # 关键位聚类容差(价差的 0.3%)


# ----------------------------------------------------------------------------
# 单周期加载与方向分类
# ----------------------------------------------------------------------------
def load_tf(tf, source):
    """source: {"csv":path} | {"text":str} | {"bars":[...]} | {"fetch":(symbol,interval,apikey)}
    返回 (report, bars) 或 ({"error":...}, None)
    """
    bars = None
    err = None
    if "csv" in source and source["csv"]:
        bars = kr.parse_csv(source["csv"])
    elif "text" in source and source["text"]:
        bars = kr.parse_text(source["text"])
    elif "bars" in source and source["bars"]:
        bars = source["bars"]
    elif "fetch" in source and source["fetch"]:
        sym, interval, apikey = source["fetch"]
        bars, e = kf.fetch_one(sym, interval, apikey)
        if bars is None:
            err = f"抓取失败:{e}"
    if bars is None:
        return {"error": err or "未提供有效数据源"}, None
    if len(bars) < 10:
        return {"error": f"K 线数量不足(<10),无法可靠解读 {TF_LABEL[tf]}"}, None
    rep = kr.analyze(bars, symbol=source.get("symbol", ""), tf=TF_LABEL[tf])
    if "error" in rep:
        return rep, None
    return rep, bars


def classify_bias(rep):
    """从 (趋势背景 trend_context, EMA 排列 trend_ema, 摆动结构 structure) 推出每周期方向。
    返回 (bias, strength, reason)
      bias ∈ {"LONG","SHORT","NEUTRAL"}
    """
    ctx = rep.get("trend_context", "range")      # up / down / range / unknown
    ema_t = rep.get("trend_ema", "")
    struct = rep.get("structure", "")
    close = rep.get("last_close", 0)

    long_ctx = ctx in ("up",) or "偏多" in struct
    short_ctx = ctx in ("down",) or "偏空" in struct
    bull_ema = "多头排列" in ema_t or ("反弹" in ema_t and close > rep.get("ema10", close))
    bear_ema = "空头排列" in ema_t or ("回落" in ema_t and close < rep.get("ema10", close))
    ema_tangled = "纠缠" in ema_t or "无明确" in ema_t

    reasons = []
    if long_ctx:
        reasons.append("趋势背景偏多")
    if short_ctx:
        reasons.append("趋势背景偏空")
    if bull_ema:
        reasons.append(ema_t)
    if bear_ema:
        reasons.append(ema_t)
    if ema_tangled:
        reasons.append("均线纠缠")

    if (long_ctx or bull_ema) and not short_ctx and not bear_ema:
        # 偏多
        strong = long_ctx and bull_ema
        return "LONG", ("强" if strong else "中"), "；".join(reasons) or "价格与均线偏多"
    if (short_ctx or bear_ema) and not long_ctx and not bull_ema:
        strong = short_ctx and bear_ema
        return "SHORT", ("强" if strong else "中"), "；".join(reasons) or "价格与均线偏空"
    # 中性:震荡 / 纠结 / 多空信号冲突
    return "NEUTRAL", "弱", "；".join(reasons) or "区间震荡/无明确方向"


# ----------------------------------------------------------------------------
# 关键位融合(confluence)
# ----------------------------------------------------------------------------
def collect_levels(reps):
    """汇总三周期所有关键位,带权重与来源标注。
    返回 [{"price","type","tf","w"}]  type∈resistance/support/round
    """
    items = []
    for tf in TFS:
        rep = reps.get(tf)
        if not rep:
            continue
        for lv in rep.get("resistance", []):
            items.append({"price": lv, "type": "resistance", "tf": tf, "w": 2.0})
        for lv in rep.get("support", []):
            items.append({"price": lv, "type": "support", "tf": tf, "w": 2.0})
        for lv in rep.get("round_levels", []):
            items.append({"price": lv, "type": "round", "tf": tf, "w": 1.0})
    return items


def cluster_levels(reps):
    """把邻近关键位聚成共振区,给强度分级。
    返回 sorted zones: [{"price","score","tfs":set,"types":set,"grade","role"}]
    role: 相对日线收盘价的支撑/阻力/中枢。
    """
    items = collect_levels(reps)
    if not items:
        return []
    d_rep = reps.get("D")
    ref = d_rep.get("last_close", 0) if d_rep else max(i["price"] for i in items)
    # 容差:价差的 0.3% 与 0.4×日线ATR 取大
    tol = CONFLUENCE_TOL_PCT * ref
    if d_rep and d_rep.get("atr14"):
        tol = max(tol, 0.4 * d_rep["atr14"])

    # 贪心聚类
    items_sorted = sorted(items, key=lambda x: x["price"])
    zones = []
    cur = [items_sorted[0]]
    for it in items_sorted[1:]:
        if it["price"] - cur[-1]["price"] <= tol:
            cur.append(it)
        else:
            zones.append(cur)
            cur = [it]
    zones.append(cur)

    out = []
    for grp in zones:
        price = sum(x["price"] for x in grp) / len(grp)
        score = sum(x["w"] for x in grp)
        tfs = set(x["tf"] for x in grp)
        types = set(x["type"] for x in grp)
        # 强度:跨周期数 + 总权重
        ntf = len(tfs)
        if score >= 5 and ntf >= 2:
            grade = "强"
        elif score >= 3 or ntf >= 2:
            grade = "中"
        else:
            grade = "弱"
        # 角色:相对日线收盘
        if price >= ref * (1 + CONFLUENCE_TOL_PCT):
            role = "阻力区"
        elif price <= ref * (1 - CONFLUENCE_TOL_PCT):
            role = "支撑区"
        else:
            role = "中枢区"
        out.append({
            "price": round(price, 5),
            "score": round(score, 1),
            "tfs": tfs,
            "types": types,
            "grade": grade,
            "role": role,
            "n_tf": ntf,
        })
    # 降噪:只保留对交易有参考意义的强/中位(剔除孤立弱位),按强度降序、距日线收盘升序排列,
    # 限制总数避免参考意义稀释(旧版把每周期数十个阻力/支撑/整数位全列出,无意义)
    out = [z for z in out if z["grade"] in ("强", "中")]
    out.sort(key=lambda z: (-z["score"], abs(z["price"] - ref)))
    return out[:8]


def nearest_zone(zones, ref, side):
    """side='below' 取 ref 下方最近的支撑共振区(严格在中枢带下方);
    'above' 取 ref 上方最近的阻力共振区(严格在中枢带上方)。
    排除与现价处在同一中枢带(±容差)的位,避免把当前价当目标/入场。"""
    lo = ref * (1 - CONFLUENCE_TOL_PCT)
    hi = ref * (1 + CONFLUENCE_TOL_PCT)
    if side == "below":
        cands = [z for z in zones if z["price"] <= lo]
    else:
        cands = [z for z in zones if z["price"] >= hi]
    if not cands:
        return None
    cands.sort(key=lambda z: abs(z["price"] - ref))
    return cands[0]


# ----------------------------------------------------------------------------
# ATR 跨周期差异
# ----------------------------------------------------------------------------
def atr_diff(reps):
    """对比 W/D/1H 的 ATR14,量化跨周期波动差异。"""
    a = {tf: (reps[tf]["atr14"] if reps.get(tf) else None) for tf in TFS}
    info = {"atr": a}
    d = a["D"]
    h = a["H1"]
    w = a["W"]
    if d and h:
        info["d_over_h1"] = round(d / h, 2)          # 日线 ATR ≈ 几个 1H ATR
    if w and d:
        info["w_over_d"] = round(w / d, 2)            # 周线 ATR ≈ 几个日线 ATR
    # 波动 regime:以 1H ATR 占日线收盘比例刻画小周期相对波动
    if h and d is not None and reps.get("D"):
        info["h1_vol_pct"] = round(100 * h / reps["D"]["last_close"], 3)
    if d and reps.get("D"):
        info["d_vol_pct"] = round(100 * d / reps["D"]["last_close"], 3)
    return info


# ----------------------------------------------------------------------------
# 综合判定(明确结论)
# ----------------------------------------------------------------------------
def resolve(reps, biases, zones, atr_info, symbol=""):
    """把 W+D 背景方向与 1H 时机 gate 收敛为确定性结论。"""
    d_rep = reps.get("D")
    h1_rep = reps.get("H1")
    if not d_rep or not h1_rep:
        missing = "日线" if not d_rep else "1H"
        return {
            "verdict": "不交易",
            "reason": f"缺少关键周期数据({missing}),无法做共振判定——需补全 {missing} 周期后再评估。",
            "action": "补全数据",
            "entry": None, "stop": None, "target": None, "r_multiple": None,
        }

    ref = d_rep["last_close"]
    h1 = biases["H1"][0]
    h1_close = h1_rep["last_close"]

    # 大周期背景(W + D)评分
    bg_score = 0.0
    bg_parts = []
    for tf in ("W", "D"):
        b, s, _ = biases[tf]
        rep = reps[tf]
        ema60 = rep.get("ema60", ref)
        if b == "LONG":
            bg_score += 1.0
            bg_parts.append(f"{TF_LABEL[tf]}偏多(强)")
        elif b == "SHORT":
            bg_score -= 1.0
            bg_parts.append(f"{TF_LABEL[tf]}偏空(强)")
        elif b == "NEUTRAL":
            # 中性看价格相对 EMA60(慢线)的姿态
            if h1_close > 0 and rep["last_close"] > ema60:
                bg_score += 0.5
                bg_parts.append(f"{TF_LABEL[tf]}中性但价在 EMA60 上方(偏多姿态)")
            elif rep["last_close"] < ema60:
                bg_score -= 0.5
                bg_parts.append(f"{TF_LABEL[tf]}中性但价在 EMA60 下方(偏空姿态)")
            else:
                bg_parts.append(f"{TF_LABEL[tf]}中性(无方向)")

    if bg_score >= MIN_BG_SCORE:
        bg = "LONG"
    elif bg_score <= -MIN_BG_SCORE:
        bg = "SHORT"
    else:
        bg = "NEUTRAL"

    # 结论分支
    if bg == "NEUTRAL":
        return {
            "verdict": "不交易",
            "reason": "周线与日线方向未共振(背景评分 %.1f,未达 ±%.1f):%s。大周期无明确方向,放弃做单,等 W/D 收敛出方向再评估。"
                      % (bg_score, MIN_BG_SCORE, "；".join(bg_parts)),
            "action": "等待 W/D 收敛",
            "entry": None, "stop": None, "target": None, "r_multiple": None,
            "bg_score": round(bg_score, 2), "bg_parts": bg_parts,
        }

    if bg == "LONG":
        if h1 == "SHORT":
            return {
                "verdict": "不交易",
                "reason": "大周期(周线+日线)看多,但 1H 逆势偏空。禁止逆大周期做空;等待 1H 回调至支撑共振区并转多后再评估多头。背景:%s。"
                          % "；".join(bg_parts),
                "action": "等大周期支撑区 + 1H 转多触发",
                "entry": None, "stop": None, "target": None, "r_multiple": None,
                "bg_score": round(bg_score, 2), "bg_parts": bg_parts,
            }
        # 做多:入场区 = 日线收盘下方最近支撑共振区
        zone = nearest_zone(zones, ref, "below")
        if not zone:
            return {
                "verdict": "不交易",
                "reason": "大周期看多,但未找到日线收盘下方的支撑共振区作为入场锚。不裸追高;等待价格回踩出共振支撑位再介入。背景:%s。"
                          % "；".join(bg_parts),
                "action": "等回踩共振支撑",
                "entry": None, "stop": None, "target": None, "r_multiple": None,
                "bg_score": round(bg_score, 2), "bg_parts": bg_parts,
            }
        entry = round(zone["price"], 5)
        stop = round(entry - STOP_ATR_MULT * h1_rep["atr14"], 5)
        tgt_zone = nearest_zone(zones, ref, "above")
        target = round(tgt_zone["price"], 5) if tgt_zone else round(entry + TARGET_ATR_MULT * h1_rep["atr14"], 5)
        risk = entry - stop
        r = round((target - entry) / risk, 2) if risk > 0 else None
        return {
            "verdict": "做多",
            "reason": ("周线+日线共振看多(背景评分 +%.1f:%s),1H %s,顺大周期做多。"
                       % (bg_score, "；".join(bg_parts), ("已转多" if h1 == "LONG" else "回调中待转多触发")))
                      + f"入场锚定支撑共振区 {entry}({zone['grade']}·{','.join(TF_LABEL[t] for t in zone['tfs'])});"
                      + f"止损 {stop}(结构外 1.5×ATR_1H={round(1.5*h1_rep['atr14'],5)});"
                      + f"目标 {target}(最近阻力共振区);R 倍数 {r}。",
            "action": "在支撑共振区挂多/等 1H 转多触发",
            "entry": entry, "stop": stop, "target": target, "r_multiple": r,
            "zone_grade": zone["grade"], "bg_score": round(bg_score, 2), "bg_parts": bg_parts,
        }

    # bg == SHORT (镜像)
    if h1 == "LONG":
        return {
            "verdict": "不交易",
            "reason": "大周期(周线+日线)看空,但 1H 逆势偏多。禁止逆大周期做多;等待 1H 反弹至阻力共振区并转空后再评估空头。背景:%s。"
                      % "；".join(bg_parts),
            "action": "等大周期阻力区 + 1H 转空触发",
            "entry": None, "stop": None, "target": None, "r_multiple": None,
            "bg_score": round(bg_score, 2), "bg_parts": bg_parts,
        }
    zone = nearest_zone(zones, ref, "above")
    if not zone:
        return {
            "verdict": "不交易",
            "reason": "大周期看空,但未找到日线收盘上方的阻力共振区作为入场锚。不裸追空;等待价格反抽至共振阻力位再介入。背景:%s。"
                      % "；".join(bg_parts),
            "action": "等反抽共振阻力",
            "entry": None, "stop": None, "target": None, "r_multiple": None,
            "bg_score": round(bg_score, 2), "bg_parts": bg_parts,
        }
    entry = round(zone["price"], 5)
    stop = round(entry + STOP_ATR_MULT * h1_rep["atr14"], 5)
    tgt_zone = nearest_zone(zones, ref, "below")
    target = round(tgt_zone["price"], 5) if tgt_zone else round(entry - TARGET_ATR_MULT * h1_rep["atr14"], 5)
    risk = stop - entry
    r = round((entry - target) / risk, 2) if risk > 0 else None
    return {
        "verdict": "做空",
        "reason": ("周线+日线共振看空(背景评分 -%.1f:%s),1H %s,顺大周期做空。"
                   % (abs(bg_score), "；".join(bg_parts), ("已转空" if h1 == "SHORT" else "反弹中待转空触发")))
                  + f"入场锚定阻力共振区 {entry}({zone['grade']}·{','.join(TF_LABEL[t] for t in zone['tfs'])});"
                  + f"止损 {stop}(结构外 1.5×ATR_1H={round(1.5*h1_rep['atr14'],5)});"
                  + f"目标 {target}(最近支撑共振区);R 倍数 {r}。",
        "action": "在阻力共振区挂空/等 1H 转空触发",
        "entry": entry, "stop": stop, "target": target, "r_multiple": r,
        "zone_grade": zone["grade"], "bg_score": round(bg_score, 2), "bg_parts": bg_parts,
    }


# ----------------------------------------------------------------------------
# 文本输出
# ----------------------------------------------------------------------------
def to_text_mtf(symbol, reps, biases, zones, atr_info, verdict):
    L = []
    L.append(f"【多周期共振分析】{symbol or '—'}  (周线定方向 · 日线定背景 · 1H 定时机)")
    L.append("=" * 60)
    # 1) 方向共识矩阵
    L.append("\n① 方向共识矩阵(每周期:趋势背景 + EMA 排列 + 摆动结构 → 投票)")
    L.append(f"{'周期':<6}{'方向':<8}{'强度':<6}{'依据'}")
    for tf in TFS:
        rep = reps.get(tf)
        if not rep:
            L.append(f"{TF_LABEL[tf]:<6}{'—':<8}{'—':<6}数据缺失")
            continue
        b, s, why = biases[tf]
        L.append(f"{TF_LABEL[tf]:<6}{b:<8}{s:<6}{why}  | 收{rep['last_close']} EMA5 {rep['ema5']} EMA10 {rep['ema10']} EMA60 {rep['ema60']} ATR {rep['atr14']}")
    # 2) 关键位融合
    L.append("\n② 关键位融合(confluence zone,按强度降序)")
    if not zones:
        L.append("  无有效共振区(三周期关键位均不重合)。")
    else:
        L.append(f"{'价位':<12}{'强度':<6}{'角色':<8}{'跨周期':<16}{'得分'}")
        for z in zones:
            L.append(f"{z['price']:<12}{z['grade']:<6}{z['role']:<8}{','.join(TF_LABEL[t] for t in z['tfs']):<16}{z['score']}")
    # 3) ATR 跨周期差异
    L.append("\n③ ATR 跨周期差异(波动尺度)")
    a = atr_info.get("atr", {})
    L.append(f"  W ATR={a.get('W')}  D ATR={a.get('D')}  H1 ATR={a.get('H1')}")
    if "d_over_h1" in atr_info:
        L.append(f"  日线 ATR ≈ {atr_info['d_over_h1']} 个 1H ATR —— 1H 触发止损需用 1H ATR 度量,日线波动决定单笔大风险上限。")
    if "w_over_d" in atr_info:
        L.append(f"  周线 ATR ≈ {atr_info['w_over_d']} 个日线 ATR —— 大周期波动显著,顺势单持有空间充裕。")
    if "h1_vol_pct" in atr_info:
        L.append(f"  1H 波动占现价 {atr_info['h1_vol_pct']}%,日线波动占现价 {atr_info.get('d_vol_pct')}% —— 当前波动 regime 如上。")
    # 4) 结论
    L.append("\n④ 明确结论")
    L.append(f"  ★ 判定:【{verdict['verdict']}】")
    L.append(f"  {verdict['reason']}")
    if verdict.get("entry") is not None:
        L.append(f"  入场区 {verdict['entry']} | 止损 {verdict['stop']} | 目标 {verdict['target']} | R {verdict['r_multiple']}")
        L.append(f"  动作:{verdict['action']}")
    else:
        L.append(f"  动作:{verdict['action']}")
    return "\n".join(L)


# ----------------------------------------------------------------------------
# HTML 图表(ECharts,暗色,与 kline_read 风格一致)
# ----------------------------------------------------------------------------
def _ema_line(bars, n):
    vals = kr.ema([b["c"] for b in bars], n)
    return [round(v, 5) if v is not None else None for v in vals]


def _trend_line_values(bars, n=30):
    """返回最近 n 根收盘的线性回归趋势线序列(长度与 bars 对齐,前段补 None)。"""
    if len(bars) < 10:
        return [None] * len(bars)
    seg = bars[-min(n, len(bars)):]
    ys = [b["c"] for b in seg]
    xs = list(range(len(ys)))
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = 0.0 if sxx == 0 else sxy / sxx
    intercept = my - slope * mx
    line = [intercept + slope * x for x in xs]
    out = [None] * (len(bars) - len(seg)) + [round(v, 5) for v in line]
    return out


def _tf_marks(rep, zones, poc=None):
    """K 线图表上只标真正重要的位:强/中共振区 + 成交密集区(POC),避免点位过多稀释参考意义。"""
    marks = []
    for z in zones:
        col = "#22d3ee" if z["grade"] == "强" else "#38bdf8"
        marks.append({"yAxis": z["price"],
                      "label": {"formatter": "共%.4f(%s)" % (z["price"], z["grade"]), "color": col},
                      "lineStyle": {"color": col, "width": 1.4, "type": "solid"}})
    if poc:
        marks.append({"yAxis": poc,
                      "label": {"formatter": "POC%.4f" % poc, "color": "#fbbf24"},
                      "lineStyle": {"color": "#fbbf24", "width": 1.2, "type": "dashed"}})
    return marks


def _tf_panel(rep, account_usd=None, risk_pct=1.0):
    """单周期指标面板:精简为交易者最常用的 EMA5/10/60 均线 + 趋势线 + 成交密集区(POC/HVN) + ATR 风控。
    避免指标过多稀释判断,仅保留价格结构类提示(量价背离/跳空),不引入 MACD/RSI/布林等额外指标。"""
    rows = [
        ("趋势背景", "%s（%s）" % (rep.get("trend_context"), rep.get("trend_ctx_source"))),
        ("市场结构", rep.get("structure")),
        ("收/EMA5/EMA10/EMA60", "%.4f / %.4f / %.4f / %.4f" % (
            rep.get("last_close"), rep.get("ema5") or 0, rep.get("ema10") or 0, rep.get("ema60") or 0)),
        ("EMA排列(5/10/60)", rep.get("trend_ema")),
        ("ATR(14)", rep.get("atr14")),
    ]
    tline = rep.get("trend_line")
    if tline:
        rows.append(("趋势线", "角度 %.2f° · %s · 当前值 %.4f" % (tline["angle"], tline["state"], tline["last"])))
    vc = rep.get("volume_concentration")
    if vc:
        rows.append(("成交密集区", "POC %.4f · HVN %.4f–%.4f · %s" % (
            vc["poc"], vc["hvn_low"], vc["hvn_high"], vc["note"])))
    # ATR 止损与仓位(基于本周期 ATR)
    atr = rep.get("atr14") or 0
    close = rep.get("last_close") or 0
    if atr and close:
        stop_15 = round(1.5 * atr, 5)
        stop_10 = round(1.0 * atr, 5)
        rows.append(("ATR止损参考", "1.0×ATR=%.4f · 1.5×ATR=%.4f(结构外)" % (stop_10, stop_15)))
        if account_usd:
            risk_usd = account_usd * risk_pct / 100.0
            units_15 = risk_usd / stop_15 if stop_15 else 0
            units_10 = risk_usd / stop_10 if stop_10 else 0
            rows.append(("仓位参考(%.1f%%风险)" % risk_pct,
                         "账户$%.2f → 风险$%.2f → 1.0×ATR仓位 %.2f手 · 1.5×ATR仓位 %.2f手" % (
                             account_usd, risk_usd, units_10, units_15)))
    # 关键位只列最近两个,避免重复
    resist = rep.get("resistance") or []
    support = rep.get("support") or []
    rows.append(("关键阻力", ", ".join("%.4f" % x for x in resist[:2]) or "—"))
    rows.append(("关键支撑", ", ".join("%.4f" % x for x in support[:2]) or "—"))
    # 仅保留重要背离/跳空提示(价格结构类,不引入额外指标)
    if rep.get("divergence"):
        rows.append(("量价背离", rep.get("divergence")))
    g = rep.get("gap")
    if g:
        rows.append(("跳空窗口", "%s 幅度 %.4f · %s" % (g["dir"], g["size"], g["note"])))
    html = '<table class="kv">'
    for k, v in rows:
        html += '<tr><td class="k">%s</td><td>%s</td></tr>' % (k, v)
    html += "</table>"
    return html


def _tf_pats(rep):
    """Morris 量化形态表。"""
    pats = rep.get("patterns") or []
    if not pats:
        return '<p class="muted">近 %d 根无符合 Morris 统计标准的有效形态。</p>' % rep.get("bars_used", 0)
    html = ('<table class="tbl"><thead><tr><th>形态</th><th>方向</th><th>价位</th><th>确认状态</th>'
            '<th>1日胜率</th><th>净盈亏比</th><th>评级</th><th>频次</th></tr></thead><tbody>')
    for p in pats[:8]:
        st = p.get("confirm_state", "")
        cls = "conf" if st == "已确认" else ("dead" if st == "已证伪" else "")
        html += ('<tr class="%s"><td>%s</td><td>%s</td><td>%.4f</td><td>%s</td><td>%s%%</td>'
                 '<td>%s</td><td>%s</td><td>%s</td></tr>'
                 % (cls, p.get("name"), p.get("dir"), p.get("price"), st, p.get("win1"), p.get("pnl1"), p.get("rank"), p.get("freq")))
    html += "</tbody></table>"
    return html


def to_html_mtf(symbol, reps, bars_map, biases, zones, atr_info, verdict, account_usd=None, risk_pct=1.0):
    today = datetime.date.today().isoformat()
    # ---------- 三周期 K 线数据 + 标线 ----------
    charts = []
    for tf in TFS:
        rep = reps.get(tf)
        bars = bars_map.get(tf)
        if not rep or not bars:
            charts.append((tf, None, None, None))
            continue
        view = bars[-max(60, rep["bars_used"]):]
        data = [[b["t"], b["o"], b["c"], b["l"], b["h"]] for b in view]
        cats = [b["t"] for b in view]
        ema5 = _ema_line(view, 5)
        ema10 = _ema_line(view, 10)
        ema60 = _ema_line(view, 60)
        trend = _trend_line_values(view, n=30)
        poc = (rep.get("volume_concentration") or {}).get("poc")
        marks = _tf_marks(rep, zones, poc)
        charts.append((tf, data, cats, {"ema5": ema5, "ema10": ema10, "ema60": ema60, "trend": trend, "marks": marks}))

    a = atr_info.get("atr", {})
    atr_cats = [TF_LABEL[t] for t in TFS if a.get(t) is not None]
    atr_vals = [a[t] for t in TFS if a.get(t) is not None]

    vc = {"做多": "#2ee6a6", "做空": "#ff5a6e", "不交易": "#94a3b8"}.get(verdict["verdict"], "#94a3b8")
    bg = verdict.get("bg_score", 0) or 0
    bg_pct = 50 + min(max(bg, -2), 2) / 2.0 * 50  # -2→0%, +2→100%
    bg_color = "#2ee6a6" if bg > 0 else ("#ff5a6e" if bg < 0 else "#94a3b8")

    # ---------- JS 图表模板(% 格式化,避免 f-string 大括号冲突) ----------
    CHART_TPL = """
(function(){
 var el = document.getElementById('chart_%(tf)s');
 if(!el) return;
 var chart = echarts.init(el, 'dark');
 var data = %(data)s;
 var cats = %(cats)s;
 var e5 = %(e5)s, e10 = %(e10)s, e60 = %(e60)s, trend = %(trend)s, marks = %(marks)s;
 chart.setOption({
  backgroundColor:'#070b14',
  grid:{left:64,right:24,top:26,bottom:56},
  xAxis:{type:'category',data:cats,axisLabel:{color:'#7c8aa0',fontSize:10,hideOverlap:true}},
  yAxis:{scale:true,axisLabel:{color:'#7c8aa0'},splitLine:{lineStyle:{color:'#16203299'}}},
  tooltip:{trigger:'axis'},
  legend:{data:['EMA5','EMA10','EMA60','趋势线'],textStyle:{color:'#7c8aa0'},top:2,itemWidth:18,itemHeight:8},
  series:[
   {type:'candlestick',barWidth:'55%%',
    data:data.map(function(d){return [d[1],d[2],d[3],d[4]];}),
    itemStyle:{color:'#ff5a6e',color0:'#2ee6a6',borderColor:'#ff5a6e',borderColor0:'#2ee6a6',borderWidth:1.2,
               shadowBlur:4,shadowColor:'#ff5a6e'},
    markLine:{symbol:'none',data:marks,lineStyle:{width:1}}},
   {type:'line',name:'EMA5',data:e5,smooth:true,showSymbol:false,lineStyle:{color:'#a78bfa',width:1}},
   {type:'line',name:'EMA10',data:e10,smooth:true,showSymbol:false,lineStyle:{color:'#22d3ee',width:1}},
   {type:'line',name:'EMA60',data:e60,smooth:true,showSymbol:false,lineStyle:{color:'#fbbf24',width:1.2}},
   {type:'line',name:'趋势线',data:trend,smooth:false,showSymbol:false,lineStyle:{color:'#94a3b8',width:1,type:'dashed'}}
  ]
 });
})();
"""
    js_parts = []
    for tf, data, cats, extra in charts:
        if data is None:
            continue
        js_parts.append(CHART_TPL % {
            "tf": tf, "data": json.dumps(data, ensure_ascii=False),
            "cats": json.dumps(cats, ensure_ascii=False),
            "e5": json.dumps(extra["ema5"], ensure_ascii=False),
            "e10": json.dumps(extra["ema10"], ensure_ascii=False),
            "e60": json.dumps(extra["ema60"], ensure_ascii=False),
            "trend": json.dumps(extra["trend"], ensure_ascii=False),
            "marks": json.dumps(extra["marks"], ensure_ascii=False),
        })
    ATR_TPL = """
(function(){
 var el=document.getElementById('atrChart'); if(!el) return;
 var c=echarts.init(el,'dark');
 c.setOption({backgroundColor:'#070b14',
  grid:{left:64,right:24,top:24,bottom:30},
  xAxis:{type:'category',data:%(cats)s},
  yAxis:{scale:true,axisLabel:{color:'#7c8aa0'},splitLine:{lineStyle:{color:'#16203299'}}},
  tooltip:{trigger:'axis'},
  series:[{type:'bar',data:%(vals)s,itemStyle:{color:'#22d3ee',borderRadius:[4,4,0,0]},barWidth:'45%%'},
          {type:'line',data:%(vals)s,itemStyle:{color:'#fbbf24'},smooth:true}]});
})();
"""
    atr_js = ATR_TPL % {"cats": json.dumps(atr_cats, ensure_ascii=False), "vals": json.dumps(atr_vals, ensure_ascii=False)}

    # ---------- 各周期深度盘面小节 ----------
    tf_sections = ""
    for tf in TFS:
        rep = reps.get(tf)
        if not rep:
            tf_sections += ('<div class="card"><h3>%s · 数据缺失</h3>'
                            '<p class="muted">未提供或未通过解析,跳过该周期盘面。</p></div>') % TF_LABEL[tf]
            continue
        b, s, why = biases[tf]
        note = rep.get("pattern_note", "")
        tf_sections += """
<div class="card" id="tf-%(tf)s">
  <div class="card-h"><span class="dot %(b)s"></span><h3>%(lab)s 盘面深度 · %(sym)s</h3>
    <span class="badge %(b)s">%(b)s · %(s)s</span></div>
  <div class="grid2">
    <div><div id="chart_%(tf)s" class="chart"></div></div>
    <div>%(panel)s</div>
  </div>
  <h4>Morris 量化形态</h4>
  %(pats)s
  <p class="note">盘面解读:%(why)s。%(note)s</p>
</div>
""" % {"tf": tf, "lab": TF_LABEL[tf], "sym": symbol, "b": b, "s": s, "panel": _tf_panel(rep, account_usd, risk_pct),
       "pats": _tf_pats(rep), "why": why, "note": note}

    # ---------- 关键位融合表 ----------
    zone_rows = ""
    for z in zones:
        tags = " ".join('<span class="tag">%s</span>' % TF_LABEL[t] for t in sorted(z["tfs"]))
        bar = '<div class="bar"><i style="width:%d%%;background:%s"></i></div>' % (
            min(int(z["score"] * 12), 100), "#22d3ee" if z["grade"] == "强" else ("#38bdf8" if z["grade"] == "中" else "#0ea5e9"))
        zone_rows += ('<tr><td>%(price).4f</td><td><b class="%(g)s">%(g)s</b></td><td>%(role)s</td>'
                      '<td>%(tags)s</td><td>%(score)s</td><td>%(bar)s</td></tr>'
                      % {"g": z["grade"], "role": z["role"], "tags": tags, "score": z["score"], "bar": bar, "price": z["price"]})

    # ---------- 交易计划 / 情景分支 ----------
    # 仓位与止损(基于 1H ATR 和账户风险)
    h1_rep = reps.get("H1") or {}
    h1_atr = h1_rep.get("atr14") or 0
    pos_note = "—"
    if account_usd and h1_atr and verdict.get("entry") is not None:
        risk_usd = account_usd * risk_pct / 100.0
        stop_dist = abs(verdict["stop"] - verdict["entry"])
        if stop_dist > 0:
            units = risk_usd / stop_dist
            pos_note = "账户$%.2f · 单笔风险 %.1f%%($%.2f) · 止损距 %.4f → 建议仓位 %.2f手" % (
                account_usd, risk_pct, risk_usd, stop_dist, units)

    if verdict.get("entry") is not None:
        vd = verdict["verdict"]
        # 失效条件与触发逻辑:1H 入场以价格行为(EMA5/10/60排列、吞没/锤子/流星等形态、关键位)为主导
        if vd == "做多":
            trig = "价格回踩至支撑共振区 %.4f 附近,且 1H 出现转多信号(收上 EMA5/10 或站上 EMA60 / 看涨吞没 / 锤子线)→ 入场。" % verdict["entry"]
            inval = "有效跌破支撑共振区 %.4f 且 1H 维持偏空 → 放弃,禁止摊平补仓。" % verdict["entry"]
            tgt_note = "目标看最近阻力共振区 %.4f;若大周期顺势、动能强,可移动止损至成本线后持有。" % verdict["target"]
        else:
            trig = "价格反抽至阻力共振区 %.4f 附近,且 1H 出现转空信号(收下 EMA5/10 或跌破 EMA60 / 看跌吞没 / 流星线)→ 入场。" % verdict["entry"]
            inval = "有效升破阻力共振区 %.4f 且 1H 维持偏多 → 放弃,禁止摊平补仓。" % verdict["entry"]
            tgt_note = "目标看最近支撑共振区 %.4f;若大周期顺势、动能强,可移动止损至成本线后持有。" % verdict["target"]
        plan = """
<div class="card">
  <h3>⑦ 交易计划(1H 盘面触发,宏观仅过滤)</h3>
  <p class="note" style="margin-bottom:8px"><b>周期角色:</b>周线+日线定方向背景;1H 小时级别以盘面(关键位、结构、量价、形态、ATR)为绝对主导,宏观只决定是否参与,不给具体入场点。</p>
  <table class="plan">
    <tr><th>品种</th><td>%(sym)s</td><th>方向</th><td class="%(v)s">%(v)s</td></tr>
    <tr><th>入场区</th><td>%(entry)s</td><th>止损</th><td>%(stop)s（结构外 1.5×ATR_1H）</td></tr>
    <tr><th>目标</th><td>%(target)s</td><th>R 倍数</th><td>%(r)s</td></tr>
    <tr><th>仓位参考</th><td colspan="3">%(pos)s</td></tr>
  </table>
  <p class="note"><b>触发:</b>%(trig)s</p>
  <p class="note"><b>失效:</b>%(inval)s</p>
  <p class="note"><b>持有:</b>%(tgt)s</p>
</div>
""" % {"sym": symbol, "v": vd, "entry": verdict["entry"], "stop": verdict["stop"],
       "target": verdict["target"], "r": verdict["r_multiple"], "trig": trig, "inval": inval,
       "tgt": tgt_note, "pos": pos_note}
    else:
        plan = ('<div class="card"><h3>⑦ 交易计划(1H 盘面触发,宏观仅过滤)</h3>'
                '<p class="note"><b>本周期组合不交易。</b>%s 等待 W/D 收敛出方向、且 1H 顺大周期时再评估。</p></div>') % verdict["reason"]

    bg_parts = "；".join(verdict.get("bg_parts", [])) or "—"

    # ---------- 周期差异对比表 ----------
    def _cell(tf, key, fmt=None):
        rep = reps.get(tf)
        if not rep:
            return "—"
        v = rep.get(key)
        if fmt and v is not None:
            return fmt(v)
        return str(v) if v is not None else "—"
    diff_dims = [
        ("趋势背景", lambda tf: _cell(tf, "trend_context") + "（" + _cell(tf, "trend_ctx_source") + "）"),
        ("市场结构", lambda tf: _cell(tf, "structure")),
        ("EMA排列", lambda tf: _cell(tf, "trend_ema")),
        ("最新收盘", lambda tf: "%.4f" % (_cell(tf, "last_close", float))),
        ("ATR(14)", lambda tf: "%.4f" % (_cell(tf, "atr14", float))),
        ("趋势线", lambda tf: (lambda r: "%.2f° · %s" % (r["trend_line"]["angle"], r["trend_line"]["state"]) if r and r.get("trend_line") else "—")(reps.get(tf))),
        ("关键阻力", lambda tf: ", ".join("%.4f" % x for x in (reps.get(tf, {}).get("resistance") or [])[:2]) or "—"),
        ("关键支撑", lambda tf: ", ".join("%.4f" % x for x in (reps.get(tf, {}).get("support") or [])[:2]) or "—"),
        ("最强形态", lambda tf: (lambda p: p[0]["name"] + "(" + p[0]["confirm_state"] + ")" if p else "无")(reps.get(tf, {}).get("patterns") or [])),
    ]
    tf_diff_rows = ""
    for dim, fn in diff_dims:
        vals = [fn(tf) for tf in TFS]
        # 交易含义列(仅对关键维度)
        meaning = {
            "趋势背景": "W/D 方向一致才能定背景;H1 只在大周期方向内找机会",
            "市场结构": "大周期 HH/HL 或 LH/LL 决定趋势可信性;H1 结构只决定触发",
            "EMA排列": "W/D EMA 方向一致提供顺势背景;H1 EMA 用于找回调/触发",
            "最新收盘": "三周期价格位置必须相互印证,避免孤立信号",
            "ATR(14)": "W ATR 决定持仓空间,H1 ATR 决定止损与仓位",
            "趋势线": "W/D 趋势线定义主方向;H1 趋势线决定短线节奏",
            "关键阻力": "大周期阻力压制更强;H1 阻力在顺势中多为目标",
            "关键支撑": "大周期支撑更有价值;H1 支撑用于回踩触发",
            "最强形态": "大周期形态决定方向;H1 形态仅决定入场确认",
        }.get(dim, "")
        tf_diff_rows += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            dim, vals[0], vals[1], vals[2], meaning)

    matrix_rows = ""
    for tf in TFS:
        rep = reps.get(tf)
        if not rep:
            matrix_rows += '<tr><td>%s</td><td class="NEUTRAL">—</td><td>—</td><td style="text-align:left">数据缺失</td></tr>' % TF_LABEL[tf]
        else:
            b, s, why = biases[tf]
            matrix_rows += ('<tr><td>%s</td><td class="%s">%s</td><td>%s</td><td style="text-align:left">%s</td></tr>'
                           % (TF_LABEL[tf], b, b, s, why))

    atr_txt = ("日线 ATR ≈ %s 个 1H ATR;周线 ATR ≈ %s 个日线 ATR;1H 波动占现价 %s&#37;,日线波动占现价 %s&#37;。"
               % (atr_info.get("d_over_h1", "—"), atr_info.get("w_over_d", "—"),
                  atr_info.get("h1_vol_pct", "—"), atr_info.get("d_vol_pct", "—")))

    css = """
<style>
:root{--bg:#070b14;--panel:#0e1422;--panel2:#111a2c;--line:#1c2740;--cyan:#22d3ee;--green:#2ee6a6;--red:#ff5a6e;--amber:#fbbf24;--txt:#dbe4f0;--mut:#8aa0bd}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 600px at 70% -10%,#0d1830 0,transparent 60%),var(--bg);color:var(--txt);
  font-family:system-ui,'Microsoft YaHei',sans-serif;line-height:1.6}
a{color:var(--cyan);text-decoration:none}
.wrap{max-width:1180px;margin:0 auto;padding:24px 20px 80px}
header.hero{padding:28px 26px;border-radius:18px;background:linear-gradient(135deg,#0e1830,#0b1222);
  border:1px solid var(--line);box-shadow:0 0 40px #0a1a3a55, inset 0 0 30px #0a1838}
.hero h1{margin:0 0 6px;font-size:26px;color:#eaf2ff;text-shadow:0 0 18px #1b6fff66}
.hero .sub{color:var(--mut);font-size:13px}
.verdict{margin-top:16px;padding:16px 18px;border-radius:14px;font-size:22px;font-weight:800;letter-spacing:1px}
.v-做多{color:#06231a;background:linear-gradient(90deg,#2ee6a6,#16c79a);box-shadow:0 0 30px #2ee6a688}
.v-做空{color:#2a0a10;background:linear-gradient(90deg,#ff5a6e,#ff7a8a);box-shadow:0 0 30px #ff5a6e77}
.v-不交易{color:#1a2233;background:linear-gradient(90deg,#94a3b8,#cbd5e1);box-shadow:0 0 24px #94a3b855}
.reason{margin-top:12px;padding:14px 16px;border-radius:12px;background:var(--panel);border:1px solid var(--line);font-size:14px;color:#cdd9ea}
nav.toc{position:sticky;top:0;z-index:9;display:flex;flex-wrap:wrap;gap:8px;padding:12px;margin:18px 0;
  background:#0a1120cc;backdrop-filter:blur(8px);border:1px solid var(--line);border-radius:12px}
nav.toc a{font-size:12.5px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;color:#bcd0ea;background:var(--panel)}
nav.toc a:hover{border-color:var(--cyan);color:var(--cyan);box-shadow:0 0 12px #22d3ee44}
section{margin-top:26px;scroll-margin-top:70px}
.card{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-radius:16px;padding:18px 20px;margin-top:16px;box-shadow:0 0 0 1px #0000, 0 8px 30px #00000055}
.card-h{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.card-h h3{margin:0;color:#eaf2ff;font-size:17px}
.dot{width:10px;height:10px;border-radius:50%}
.dot.LONG,.badge.LONG{background:var(--green);box-shadow:0 0 10px var(--green)}
.dot.SHORT,.badge.SHORT{background:var(--red);box-shadow:0 0 10px var(--red)}
.dot.NEUTRAL,.badge.NEUTRAL{background:#94a3b8}
.badge{color:#06121f;font-weight:700;font-size:12px;padding:3px 9px;border-radius:20px}
h4{color:var(--cyan);margin:16px 0 8px;font-size:14px;letter-spacing:.5px}
.grid2{display:grid;grid-template-columns:1.25fr .9fr;gap:16px}
@media(max-width:820px){.grid2{grid-template-columns:1fr}}
.chart{width:100%;height:330px}
.kv{width:100%;border-collapse:collapse;font-size:13px}
.kv td{border-bottom:1px solid var(--line);padding:6px 8px;vertical-align:top}
.kv td.k{color:var(--cyan);width:140px;white-space:nowrap}
.tbl{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:4px}
.tbl th,.tbl td{border:1px solid var(--line);padding:6px 8px;text-align:center}
.tbl th{background:#0c1730;color:var(--cyan)}
.tbl tr.conf td{background:#0e2a2233}
.tbl tr.dead td{background:#2a111633;color:#ff8a9a;text-decoration:line-through}
.tag{display:inline-block;font-size:11px;padding:2px 7px;margin:1px;border:1px solid var(--line);border-radius:6px;color:#bcd0ea;background:#0c1426}
table.plan{width:100%;border-collapse:collapse;font-size:14px;margin:6px 0 10px}
table.plan th,table.plan td{border:1px solid var(--line);padding:9px 10px}
table.plan th{background:#0c1730;color:var(--cyan);width:120px;text-align:left}
.plan .做多{color:var(--green);font-weight:800}.plan .做空{color:var(--red);font-weight:800}
.bar{height:8px;background:#0c1426;border-radius:6px;overflow:hidden;min-width:80px}
.bar i{display:block;height:100%;border-radius:6px}
.note{color:var(--mut);font-size:13px;line-height:1.7}
.muted{color:var(--mut);font-size:13px}
.bigbar{height:14px;border-radius:8px;background:linear-gradient(90deg,#ff5a6e,#94a3b8 50%,#2ee6a6);position:relative;margin:6px 0 2px}
.bigbar i{position:absolute;top:-4px;width:4px;height:22px;background:#fff;border-radius:3px;box-shadow:0 0 10px #fff}
.mini{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}
.minicard{background:#0b1322;border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.minicard h5{margin:0 0 6px;color:var(--cyan);font-size:13px}
.minicard .v{font-size:15px;font-weight:700}
.minicard .m{color:var(--mut);font-size:11.5px;margin-top:4px}
ul.rules{margin:6px 0;padding-left:20px}.rules li{margin:5px 0;font-size:13.5px;color:#cdd9ea}
footer{margin-top:40px;color:var(--mut);font-size:12px;text-align:center;border-top:1px solid var(--line);padding-top:18px}
</style>"""

    html = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>多周期共振深度报告 · %(sym)s · %(today)s</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
%(css)s</head>
<body><div class="wrap">
<header class="hero">
  <h1>多周期共振深度分析报告</h1>
  <div class="sub">品种 <b>%(sym)s</b> · 生成日期 %(today)s · 周线定方向 · 日线定背景 · 1H 定时机 ·
  数据溯源:真实 OHLC(Twelve Data / 用户 CSV),方向由引擎收敛 · 宏观仅做 W/D 方向指引,1H 交易以盘面为主导</div>
  <div class="verdict v-%(v)s">判定:【%(v)s】</div>
  <div class="reason">%(reason)s</div>
</header>

<nav class="toc">
  <a href="#s1">① 执行摘要</a><a href="#s2">② 三维共振总览</a><a href="#s3">③ 宏观/跨市场衔接</a>
  <a href="#s4">④ 各周期深度盘面</a><a href="#s4b">④-B 周期差异</a><a href="#s5">⑤ 关键位融合</a><a href="#s6">⑥ ATR 跨周期波动</a>
  <a href="#s7">⑦ 交易计划</a><a href="#s8">⑧ 风险与纪律</a><a href="#s9">⑨ 数据溯源与方法学</a>
</nav>

<section id="s1"><div class="card">
  <h3>① 执行摘要</h3>
  <div class="mini">
    <div class="minicard"><h5>大周期背景评分</h5><div class="v" style="color:%(bgc)s">%(bg).2f</div>
      <div class="bigbar"><i style="left:%(bgpct).1f%%"></i></div><div class="m">≥+1.5 看多 / ≤−1.5 看空 / 中间冲突</div></div>
    <div class="minicard"><h5>周线 / 日线 / 1H 方向</h5><div class="v">%(w)s / %(d)s / %(h1)s</div>
      <div class="m">背景:%(bgp)s</div></div>
    <div class="minicard"><h5>最终动作</h5><div class="v" style="color:%(v)s">%(act)s</div>
      <div class="m">结论基于客观数值,不含模糊推测</div></div>
  </div>
  <p class="note" style="margin-top:12px">核心论点:%(reason2)s</p>
</div></section>

<section id="s2"><div class="card">
  <h3>② 三维共振总览(方向共识矩阵)</h3>
  <p class="note">每周期由「趋势背景(ATR 归一化摆动斜率)+ EMA5/10/60 排列 + 摆动结构」三方投票,定偏多/偏空/中性及强度;周线+日线收敛为大周期背景方向(评分 ≥±1.5)。</p>
  <table class="tbl"><thead><tr><th>周期</th><th>方向</th><th>强度</th><th>客观依据</th></tr></thead>
  <tbody>%(matrix)s</tbody></table>
  <p class="note" style="margin-top:10px"><b>背景收敛:</b>%(bgp)s</p>
</div></section>

<section id="s3"><div class="card">
  <h3>③ 宏观 / 跨市场衔接(三维印证之另两维)</h3>
  <p class="note" style="background:#0c1426;border:1px solid #1c2740;border-radius:10px;padding:10px 12px">
    <b>周期角色声明:</b>宏观与跨市场分析只用于<b>周线/日线级别的大方向指引</b>,不给出具体入场、止损或目标。
    当出现 1H 小时级别交易机会时,盘面分析(关键位、结构、量价、形态、ATR)占绝对主导地位;宏观仅作为过滤条件——若宏观/跨市场与 W/D 方向冲突,放弃交易。</p>
  <p class="note">本引擎聚焦三维印证中的<b>「盘面」维度</b>。下单前须同步确认另两维,三者共振才高确定性出手(任一反向即降级或放弃):</p>

  <h4>3.1 美元与利率地基(实际利率框架)</h4>
  <p class="note">实际利率 = 名义利率 − 通胀预期。本报告依据 <b>US10Y(DGS10)、10Y TIPS(DFII10)、盈亏平衡通胀率(T10YIE)</b> 判断美元资产估值与无息货币/黄金的相对压力。
    名义利率上行快于通胀预期 → 实际利率升 → 通常压制黄金、压制无息资产;通胀预期跑赢名义利率 → 实际利率降 → 利好黄金。
    外汇视角:美元作为融资/储备货币,US10Y 是全球资产定价锚;实际利率趋势决定 DXY 中期方向,进而影响所有非美货币与商品。</p>

  <h4>3.2 四大央行周期与利差</h4>
  <table class="tbl"><thead><tr><th>央行</th><th>核心目标</th><th>当前工具</th><th>周期判断维度</th><th>对汇率的指引</th></tr></thead><tbody>
    <tr><td>美联储(Fed)</td><td>通胀回落 + 就业</td><td>政策利率 + 缩表(QT)</td><td>点阵图 vs FedWatch 隐含路径</td><td>点阵图更鹰 → 美元偏强;更鸽 → 美元偏弱</td></tr>
    <tr><td>欧央行(ECB)</td><td>通胀目标 2%%</td><td>存款便利利率 + QT</td><td>与 Fed 利差</td><td>利差扩大 → EUR/USD 承压;收窄 → 欧元支撑</td></tr>
    <tr><td>日央行(BoJ)</td><td>YCC/负利率正常化</td><td>收益率曲线控制</td><td>日元作为全球套息融资货币</td><td>BoJ 转向 → 套息平仓 → 日元急升</td></tr>
    <tr><td>英央行(BoE)</td><td>通胀与增长平衡</td><td>银行利率 + QT</td><td>英国数据敏感性</td><td>数据强于预期 → GBP 走强</td></tr>
  </tbody></table>
  <p class="note">利差交易(Carry)逻辑:借低息(日元、瑞郎)买高息(澳元等)的套息头寸,在利差收窄或风险恶化时会快速平仓,导致高息货币急跌。实际利差(剔除通胀)比名义利差更根本。</p>

  <h4>3.3 收益率曲线状态</h4>
  <p class="note">用 2s10s 利差刻画经济预期:<b>陡峭化</b>(长端上行更快)=增长/通胀升温,利好周期货币与商品;<b>平坦化</b>=加息后期增长担忧;<b>倒挂</b>=衰退领先信号,利好避险资产(美元、日元、瑞郎、黄金),压制风险货币与商品。</p>

  <h4>3.4 宏观 Regime 与 risk-on/off</h4>
  <table class="tbl"><thead><tr><th>Regime</th><th>增长</th><th>通胀</th><th>偏好方向</th></tr></thead><tbody>
    <tr><td>周期扩张</td><td>强</td><td>升</td><td>商品货币、原油、铜;黄金中性偏强</td></tr>
    <tr><td>滞胀担忧</td><td>弱</td><td>高</td><td>黄金强、美元强;商品货币弱</td></tr>
    <tr><td>宽松预期</td><td>弱</td><td>回落</td><td>债券、黄金;商品弱</td></tr>
    <tr><td>流动性危机/避险</td><td>崩</td><td>无序</td><td>美元、日元、瑞郎;黄金先跌后涨</td></tr>
  </tbody></table>
  <p class="note">Risk-on/off 定性:VIX 低 + 标普升 + 信用利差收窄 + 商品货币强 → Risk-on;VIX 高 + 股指跌 + 日元/瑞郎/美元强 + 黄金强 → Risk-off。当 Regime 与 W/D 技术方向一致时,交易胜率提升;冲突时,以宏观为准放弃。</p>

  <h4>3.5 跨市场验证(至少两个相关市场确认)</h4>
  <p class="note">交易某一货币/商品前,必须用相关市场验证:如分析黄金需同步看 DXY、10Y TIPS、盈亏平衡;分析澳元需看铜、AUD/JPY、中国信贷脉冲;分析原油需看 Brent/WTI 价差、加元、能源股。
    <b>背离即警告:</b>若价格走强但相关市场不配合(如黄金跌但实际利率未升、铜强但澳元弱),降低仓位或放弃,不强行入场。</p>

  <h4>3.6 宏观方向指引结论(客观理性,不替代盘面)</h4>
  <p class="note"><b>当前状态:</b>宏观与跨市场维度需用户填入/核对最新数据(参考 `references/macro_rates.md`、`cross_market.md`)。
    本引擎已给出的 W/D 方向(见执行摘要与共识矩阵)应与上述宏观框架一致;若出现冲突,本报告结论自动降级为<b>不交易</b>,等待宏观与盘面重新共振。</p>
</div></section>

<section id="s4"><h3 style="color:#eaf2ff">④ 各周期深度盘面</h3>%(tfsec)s</section>

<section id="s4b"><div class="card">
  <h3>④-B 周期差异与"看大做小"逻辑</h3>
  <p class="note">多周期共振的核心是<b>大周期定方向、小周期定时机</b>。下表对比三周期在同一时刻的差异,明确为什么 1H 只能在大周期方向一致时做顺向触发。</p>
  <table class="tbl"><thead><tr><th>维度</th><th>周线 W</th><th>日线 D</th><th>1H H1</th><th>交易含义</th></tr></thead><tbody>%(tfdiff)s</tbody></table>
  <p class="note" style="margin-top:10px"><b>纪律:</b>周线/日线方向冲突(背景评分未达 ±1.5) → 不交易;1H 逆势(大周期看多但 1H 偏空,或反之) → 不交易;仅在 W/D 同向 + 1H 顺向/回调到位时才评估入场。</p>
</div></section>

<section id="s5"><div class="card">
  <h3>⑤ 关键位融合(confluence zone)</h3>
  <p class="note">合并三周期阻力/支撑/整数位,邻近(±0.3%% 价或 ±0.4×日线 ATR 容差内)聚类为共振区;只保留<b>强/中</b>级别的跨周期共振位,按强度排序,剔除孤立弱位与过远噪音,避免参考意义稀释(旧版把每周期数十个原始位全列出,无参考意义)。</p>
  <table class="tbl"><thead><tr><th>价位</th><th>强度</th><th>角色</th><th>跨周期</th><th>得分</th><th>强度条</th></tr></thead>
  <tbody>%(zones)s</tbody></table>
</div></section>

<section id="s6"><div class="card">
  <h3>⑥ ATR 跨周期波动结构</h3>
  <div id="atrChart" style="width:100%%;height:260px"></div>
  <p class="note" style="margin-top:10px">%(atrtxt)s 1H 触发止损须用 1H ATR 度量,日线波动决定单笔大风险上限;周线波动显著则顺势单持有空间充裕。</p>
</div></section>

<section id="s7">%(plan)s</section>

<section id="s8"><div class="card">
  <h3>⑧ 风险与纪律(铁律)</h3>
  <ul class="rules">
    <li>周期角色:周线+日线定方向背景,不给出具体入场/止损/目标;1H 小时级别以盘面(关键位、结构、量价、形态、ATR)为绝对主导,宏观只决定是否参与,不替代盘面触发。</li>
    <li>单笔风险 ≤ 账户 0.5&#37;–1&#37;;总风险 ≤ 3&#37;–5&#37;;连续亏损 3 次暂停,复盘后再动。</li>
    <li>仓位按 ATR 计算:仓位 = 账户风险金额 ÷ 止损距离(结构外 1.5×ATR_1H),绝不凭感觉重仓。</li>
    <li>逆大周期的单子一律不做;本引擎已硬约束(周线/日线冲突或 1H 逆势 → 不交易)。</li>
    <li>不摊平、不补仓摊低成本;失效条件触发即离场,保护本金优先。</li>
    <li>止损前置:入场前定好止损(结构外 1.5×ATR_1H)与目标,不凭感觉移动止损放大风险。</li>
    <li>本报告为分析辅助,最终决策由交易者基于实时盘面确认;引擎不做任何自动下单。</li>
  </ul>
</div></section>

<section id="s9"><div class="card">
  <h3>⑨ 数据溯源与方法学</h3>
  <p class="note"><b>数据铁律:</b>仅消费真实传入/抓取的 OHLC;任一周期缺失或分析失败,明确降级并说明,绝不编造或估算价格。数据源(Twelve Data / 用户 CSV)只提供价格,不提供方向;方向由本引擎共识逻辑收敛。</p>
  <p class="note"><b>方法学引用(IMA 知识库「金融」id 7490653902604963):</b>魏强斌《外汇交易进阶》第十八阶"多重时间框架分析"(大周期定方向、小周期定入场,禁止跨周期反向);《ATR止损法深度研究与实践指南》(止损=波动尺)。数值规则以本技能本地参考为准:关键位与盘面 `references/ta_reading.md`、均线/ATR/指标 `references/indicators.md`、趋势线/通道/斐波 `references/channels.md`、多周期共振 `references/mtf_confluence.md`。</p>
  <p class="note">引擎:`scripts/mtf_confluence.py`,直接复用 `kline_read.analyze()` 做单周期客观解读,聚合层输出方向共识矩阵、关键位融合、ATR 跨周期差异与明确结论。</p>
</div></section>

<footer>kingforex-skill · 多周期共振深度报告 v1.2.1 · 生成于 %(today)s · 仅供研究,不构成投资建议</footer>
</div>
<script>
%(atrjs)s
%(js)s
</script>
</body></html>""" % {
        "sym": symbol, "today": today, "v": verdict["verdict"], "reason": verdict["reason"],
        "reason2": verdict["reason"], "css": css, "bg": bg, "bgc": bg_color, "bgpct": bg_pct,
        "w": biases.get("W", ("—",))[0] if reps.get("W") else "—",
        "d": biases.get("D", ("—",))[0] if reps.get("D") else "—",
        "h1": biases.get("H1", ("—",))[0] if reps.get("H1") else "—",
        "bgp": bg_parts, "act": verdict["action"], "matrix": matrix_rows, "tfsec": tf_sections,
        "zones": zone_rows, "atrtxt": atr_txt, "atrjs": atr_js, "js": "".join(js_parts),
        "plan": plan, "tfdiff": tf_diff_rows,
    }
    return html



# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------
def run(args):
    symbol = args.symbol or ""
    sources = {}
    if args.fetch:
        apikey = args.api_key
        for tf, ival in (("W", "1week"), ("D", "1day"), ("H1", "1h")):
            sources[tf] = {"fetch": (symbol, ival, apikey), "symbol": symbol}
    else:
        if args.csv_w:
            sources["W"] = {"csv": args.csv_w, "symbol": symbol}
        if args.csv_d:
            sources["D"] = {"csv": args.csv_d, "symbol": symbol}
        if args.csv_h1:
            sources["H1"] = {"csv": args.csv_h1, "symbol": symbol}
        if args.text_w:
            sources["W"] = {"text": args.text_w, "symbol": symbol}
        if args.text_d:
            sources["D"] = {"text": args.text_d, "symbol": symbol}
        if args.text_h1:
            sources["H1"] = {"text": args.text_h1, "symbol": symbol}

    if not sources:
        print("✗ 未提供任何数据源:用 --fetch --symbol 或 --csv-w/--csv-d/--csv-h1 或 --text-w/--text-d/--text-h1")
        sys.exit(2)

    reps = {}
    bars_map = {}
    for tf in TFS:
        if tf not in sources:
            continue
        rep, bars = load_tf(tf, sources[tf])
        if "error" in rep:
            print(f"! {TF_LABEL[tf]} 分析失败:{rep['error']}")
            reps[tf] = None
        else:
            reps[tf] = rep
            bars_map[tf] = bars

    # 缺关键周期则整体降级
    if not reps.get("D") or not reps.get("H1"):
        miss = "日线" if not reps.get("D") else "1H"
        verdict = {"verdict": "不交易",
                   "reason": f"缺少关键周期数据({miss}),无法做共振判定——需补全 {miss} 周期后再评估。",
                   "action": "补全数据", "entry": None, "stop": None, "target": None, "r_multiple": None}
    else:
        biases = {tf: classify_bias(reps[tf]) for tf in TFS if reps.get(tf)}
        zones = cluster_levels(reps)
        atr_info = atr_diff(reps)
        verdict = resolve(reps, biases, zones, atr_info, symbol)

    # 文本
    if not args.no_text:
        biases_full = {tf: classify_bias(reps[tf]) for tf in TFS if reps.get(tf)}
        zones_full = cluster_levels(reps) if any(reps.values()) else []
        atr_full = atr_diff(reps) if any(reps.values()) else {}
        print(to_text_mtf(symbol, reps, biases_full, zones_full, atr_full, verdict))

    # JSON 安全化(set -> list)
    def _safe(o):
        if isinstance(o, set):
            return sorted(o)
        if isinstance(o, dict):
            return {k: _safe(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_safe(x) for x in o]
        return o

    # JSON
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.date.today().isoformat()
    safesym = (symbol or "SYM").replace("/", "_")
    json_path = os.path.join(out_dir, f"mtf_{safesym}_{stamp}.json")
    html_path = os.path.join(out_dir, f"mtf_{safesym}_{stamp}.html")
    if args.json:
        out = {"symbol": symbol, "verdict": verdict,
               "biases": {tf: classify_bias(reps[tf]) for tf in TFS if reps.get(tf)},
               "zones": cluster_levels(reps), "atr": atr_diff(reps),
               "reports": {tf: reps[tf] for tf in TFS if reps.get(tf)}}
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(_safe(out), f, ensure_ascii=False, indent=2)
        print(f"[JSON] -> {json_path}")

    # HTML
    if args.html:
        html = to_html_mtf(symbol, reps, bars_map,
                           {tf: classify_bias(reps[tf]) for tf in TFS if reps.get(tf)},
                           cluster_levels(reps), atr_diff(reps), verdict,
                           account_usd=args.account_usd, risk_pct=args.risk_pct)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[HTML] -> {html_path}")
    return verdict


def main():
    ap = argparse.ArgumentParser(description="多周期共振(三维印证)分析引擎")
    ap.add_argument("--symbol", default="", help="品种名(分析/抓取标注)")
    ap.add_argument("--csv-w", help="周线 CSV 路径")
    ap.add_argument("--csv-d", help="日线 CSV 路径")
    ap.add_argument("--csv-h1", help="1H CSV 路径")
    ap.add_argument("--text-w", help="周线 OHLC 文本")
    ap.add_argument("--text-d", help="日线 OHLC 文本")
    ap.add_argument("--text-h1", help="1H OHLC 文本")
    ap.add_argument("--fetch", action="store_true", help="经 Twelve Data 抓取 W/D/1H(需 --symbol 与 API Key)")
    ap.add_argument("--api-key", default=os.environ.get("TWELVEDATA_API_KEY", "") or kf._read_td_key(),
                    help="Twelve Data API Key(或环境变量 / scripts/.td_key)")
    ap.add_argument("--out", default=os.path.join(_HERE, "output"), help="输出目录(默认 scripts/output)")
    ap.add_argument("--json", action="store_true", help="输出 JSON 结论文件")
    ap.add_argument("--html", action="store_true", help="输出 ECharts HTML 图表")
    ap.add_argument("--no-text", action="store_true", help="不打印文本解读")
    ap.add_argument("--account-usd", type=float, default=None,
                    help="账户权益(美元),用于在 HTML 中计算 ATR 仓位参考")
    ap.add_argument("--risk-pct", type=float, default=1.0,
                    help="单笔风险百分比(默认 1.0%%)")
    args = ap.parse_args()
    run(args)


if __name__ == "__main__":
    main()
