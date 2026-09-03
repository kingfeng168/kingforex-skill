#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kline_read.py — K 线盘面解读引擎 (kingforex-skill 模块九 · 盘面分析)

定位:把"宏观对"落实为"现在能不能做、怎么做"的客观盘面事实。
  输入 MT4 / 通用 OHLCV CSV(或 --text 粘贴),输出结构化盘面解读:
    趋势(EMA 排列) · 市场结构(HH/HL/LH/LL) · ATR(14) · 关键支撑阻力
    · 价格行为形态(Morris《蜡烛图精解》量化库 + 经典日本蜡烛图补充集) · 量价背离提示
  输出:JSON(机器可读) + 文本解读(AI 可直接引用) + 可选 HTML 标注图。
  盘面事实另涵盖:回归通道(上/中/下轨与突破状态) · MACD(DIF/DEA/柱/背离)
    · RSI(14) · 布林带(20,±2σ) · 随机 %K/%D,均依 Murphy《金融市场技术分析》框架。

设计约束:
  - 纯标准库,不联网(避开中国大陆被墙的免费 K 线源)。
  - 取数依赖用户在 MT4 导出历史 CSV(或粘贴 OHLC),脚本只做确定性计算。
  - 形态/结构判定为"客观信号",不含任何主观方向建议;方向必须顺宏观与跨市场印证。

用法:
  # 解读 MT4 导出的 EURUSD H1 CSV(最近 120 根)
  python kline_read.py --csv "D:/MT4/EURUSD_H1.csv" --symbol EURUSD --tf H1 --last 120 \
      --out "./output/" --html

  # 直接粘贴 OHLC。分隔符 逗号/分号/制表符/空格 均可,列数自适应:
  #   date,o,h,l,c[,v] / date,time,o,h,l,c[,v] / 纯 o,h,l,c 都支持,可直接粘 MT4 剪贴板
  python kline_read.py --text "2026-08-01,1.0800,1.0820,1.0790,1.0810
2026-08-02,1.0810,1.0835,1.0805,1.0828" --symbol XAUUSD --tf D1

  # 仅出 JSON(供其他脚本/AI 流水消费)
  python kline_read.py --csv data.csv --json --no-text
"""

import argparse
import json
import math
import os
import re
import sys

DEFAULT_OUT = os.environ.get("KINGFOREX_OUT", "./output")


# ----------------------------- 解析层 -----------------------------
# 严格数字:仅 1.0800 / -1.5 / .5 / 12,不把 "2026-08-01"、"10:00" 算作数字
NUM_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")


def _is_num(s):
    s = s.strip().replace(",", "").replace("-", "")
    if s.startswith(".") or s.endswith("."):
        return False
    return s.replace(".", "").isdigit() and s.count(".") <= 1


def _is_date(s):
    s = s.strip()
    if not s:
        return False
    if any(ch in s for ch in "-./:"):
        clean = s.replace("-", "").replace(".", "").replace(":", "").replace("/", "")
        return not clean.isdigit()
    return False


def parse_csv(path):
    """解析 MT4 导出 CSV 或通用 OHLCV,返回 bars=[{t,o,h,l,c,v}]"""
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    delim = ";" if text.count(";") > text.count(",") else ","
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    colmap = None
    bars = []
    for ln in lines:
        cols = [c.strip() for c in ln.split(delim)]
        low = [c.lower() for c in cols]
        # 检测表头(仅取第一次出现的表头)
        if colmap is None and ("open" in low or "close" in low or "<open" in low):
            colmap = {}
            for i, c in enumerate(low):
                if "open" in c:
                    colmap["o"] = i
                elif "high" in c:
                    colmap["h"] = i
                elif "low" in c:
                    colmap["l"] = i
                elif "close" in c:
                    colmap["c"] = i
                elif "vol" in c:
                    colmap["v"] = i
                elif "date" in c:
                    colmap["date"] = i
                elif "time" in c:
                    colmap["time"] = i
            continue
        try:
            if colmap:
                o = float(cols[colmap["o"]])
                h = float(cols[colmap["h"]])
                l = float(cols[colmap["l"]])
                c = float(cols[colmap["c"]])
                v = float(cols[colmap["v"]]) if ("v" in colmap and colmap["v"] < len(cols)) else 0.0
                tparts = [cols[colmap[k]] for k in ("date", "time") if k in colmap and colmap[k] < len(cols)]
                t = " ".join(tparts)
            else:
                if _is_date(cols[0]):
                    rest = [x for x in cols[1:] if _is_num(x)]
                    nums = [float(x.replace(",", "")) for x in rest]
                    if len(nums) < 4:
                        continue
                    o, h, l, c = nums[0], nums[1], nums[2], nums[3]
                    v = nums[4] if len(nums) > 4 else 0.0
                    t = cols[0] + (" " + cols[1] if len(cols) >= 6 else "")
                else:
                    nums = [float(x.replace(",", "")) for x in cols if _is_num(x)]
                    if len(nums) < 4:
                        continue
                    o, h, l, c = nums[0], nums[1], nums[2], nums[3]
                    v = nums[4] if len(nums) > 4 else 0.0
                    t = str(len(bars) + 1)
        except Exception:
            continue
        if h < max(o, c) or l > min(o, c):
            # 非法 HL 关系跳过
            continue
        bars.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": v})
    return bars


def parse_text(text):
    """解析 --text 粘贴的 OHLC,自动兼容多种粘贴格式。

    分隔符可为 逗号 / 分号 / 制表符 / 空格,可混用;列可多可少:
        date,o,h,l,c[,v]                 文档示例
        date,time,o,h,l,c[,v]            MT4 复制到剪贴板的常见格式
        date<TAB>time<TAB>o h l c v      MT4 制表符导出
        o,h,l,c[,v]                      无时间戳的纯 OHLC
    规则:第一个可解析为数字的列之前的所有列,合并成时间标签。
    """
    bars = []
    for ln in text.strip().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        parts = [p for p in re.split(r"[,;\t ]+", ln) if p]
        if len(parts) < 4:
            continue
        # 严格数字匹配(不能用 _is_num:它会把 "2026-08-01" 判成数字)
        idxs = [i for i, p in enumerate(parts) if NUM_RE.match(p)]
        if len(idxs) < 4:
            continue  # 表头行或日期-only 行
        first = idxs[0]
        label = " ".join(parts[:first]) if first > 0 else str(len(bars) + 1)
        nums = [float(parts[i]) for i in idxs]
        o, h, l, c = nums[0], nums[1], nums[2], nums[3]
        v = nums[4] if len(nums) > 4 else 0.0
        if h < max(o, c) or l > min(o, c):
            continue  # 非法 HL 关系
        bars.append({"t": label, "o": o, "h": h, "l": l, "c": c, "v": v})
    return bars


# ----------------------------- 计算层 -----------------------------
def ema(vals, n):
    if not vals or n <= 0:
        return []
    k = 2.0 / (n + 1)
    out = []
    prev = vals[0]
    for i, v in enumerate(vals):
        prev = v if i == 0 else v * k + prev * (1 - k)
        out.append(prev)
    return out


def atr(highs, lows, closes, n=14):
    if len(closes) < 2:
        return 0.0
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        trs.append(tr)
    if not trs:
        return 0.0
    return sum(trs[-n:]) / len(trs[-n:])


def pivots(highs, lows, window=5):
    """找局部摆动高低点,返回 (idx, price) 列表"""
    ph, pl = [], []
    for i in range(window, len(highs) - window):
        seg_h = highs[i - window:i + window + 1]
        seg_l = lows[i - window:i + window + 1]
        # 浮点容差比较(避免随机数据下极值几乎不严格相等导致漏检)
        if highs[i] >= max(seg_h) - 1e-9:
            ph.append((i, highs[i]))
        if lows[i] <= min(seg_l) + 1e-9:
            pl.append((i, lows[i]))
    return ph, pl


def structure_from_pivots(ph, pl):
    """基于最近摆动高低点判断 HH/HL/LH/LL(单边数据也尽量判)"""
    if len(ph) < 2 and len(pl) < 2:
        return "样本不足"
    rh = [p for _, p in ph[-3:]]
    rl = [p for _, p in pl[-3:]]
    up_h = all(rh[i] < rh[i + 1] for i in range(len(rh) - 1)) if len(rh) >= 2 else None
    dn_h = all(rh[i] > rh[i + 1] for i in range(len(rh) - 1)) if len(rh) >= 2 else None
    up_l = all(rl[i] < rl[i + 1] for i in range(len(rl) - 1)) if len(rl) >= 2 else None
    dn_l = all(rl[i] > rl[i + 1] for i in range(len(rl) - 1)) if len(rl) >= 2 else None
    up = (up_h is True) or (up_l is True)
    dn = (dn_h is True) or (dn_l is True)
    if up and not dn:
        return "上升趋势(HH/HL)"
    if dn and not up:
        return "下降趋势(LH/LL)"
    if not up and not dn:
        return "区间震荡(高低点走平)"
    return "结构转换中(高低点方向不一)"


def round_levels(price, n=5):
    """生成价格附近的整数关口(网格):step=mag/20,返回当前价上下各约 2 档"""
    if price <= 0:
        return []
    mag = 10 ** math.floor(math.log10(price))
    step = mag / 20.0  # 1.09→0.05, 2300→50, 114→5, 0.68→0.05
    base = round(price / step) * step
    out = []
    for i in range(-n, n + 1):
        lv = round(base + i * step, 5)
        if lv > 0:
            out.append(lv)
    # 仅保留靠近当前价的若干档
    out = [x for x in out if abs(x - price) <= step * 2.5]
    return sorted(out)[:6]


# ---- 技术指标计算(Murphy《金融市场技术分析》框架) ----
def sma(vals, n):
    if n <= 0:
        return []
    out = []
    for i in range(len(vals)):
        if i + 1 < n:
            out.append(None)
        else:
            out.append(sum(vals[i + 1 - n:i + 1]) / n)
    return out


def macd(closes, fast=12, slow=26, signal=9):
    """返回 DIF/DEA/柱 三条序列(长度对齐 closes,前段为 None)。"""
    if len(closes) < slow + signal:
        return None
    ef = ema(closes, fast)
    es = ema(closes, slow)
    dif = [ef[i] - es[i] for i in range(len(closes))]
    dea = ema(dif, signal)
    hist = [dif[i] - dea[i] for i in range(len(closes))]
    return {"dif": dif, "dea": dea, "hist": hist}


def macd_state(m, c):
    """提炼 MACD 的最新状态:零轴位置、近期金叉/死叉、顶/底背离。"""
    if not m:
        return {}
    dif, dea, hist = m["dif"], m["dea"], m["hist"]
    last = len(dif) - 1
    info = {
        "dif": round(dif[last], 5),
        "dea": round(dea[last], 5),
        "hist": round(hist[last], 5),
        "zero": "零轴上方" if dif[last] > 0 else "零轴下方",
        "cross": "—",
        "divergence": "",
    }
    for i in range(max(1, last - 3), last + 1):
        if dif[i - 1] <= dea[i - 1] and dif[i] > dea[i]:
            info["cross"] = "金叉(近期)"; break
        if dif[i - 1] >= dea[i - 1] and dif[i] < dea[i]:
            info["cross"] = "死叉(近期)"; break
    win = min(20, len(c))
    seg_c, seg_d = c[-win:], dif[-win:]
    i_h, i_l = seg_c.index(max(seg_c)), seg_c.index(min(seg_c))
    if i_h >= win - 5 and seg_d[i_h] < max(seg_d):
        info["divergence"] = "价格新高但 MACD 未新高→顶背离预警"
    elif i_l >= win - 5 and seg_d[i_l] > min(seg_d):
        info["divergence"] = "价格新低但 MACD 未新低→底背离预警"
    return info


def rsi(closes, n=14):
    """Wilder RSI(14),返回长度对齐 closes,前段为 None。"""
    if len(closes) < n + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        gains.append(max(ch, 0.0)); losses.append(max(-ch, 0.0))
    out = [None] * n
    ag, al = sum(gains[:n]) / n, sum(losses[:n]) / n
    rs = ag / al if al else float("inf")
    out.append(100 - 100 / (1 + rs))
    for i in range(n, len(gains)):
        ag = (ag * (n - 1) + gains[i]) / n
        al = (al * (n - 1) + losses[i]) / n
        rs = ag / al if al else float("inf")
        out.append(100 - 100 / (1 + rs))
    # 补齐到 closes 长度(前面 n 个已 None,需与索引对齐:closes[0..n-1] 无 RSI)
    return out


def bollinger(closes, n=20, k=2):
    """返回 (mid, upper, lower) 序列,前段为 (None,None,None)。"""
    if len(closes) < n:
        return None
    out = []
    for i in range(len(closes)):
        if i + 1 < n:
            out.append((None, None, None))
        else:
            w = closes[i + 1 - n:i + 1]
            mid = sum(w) / n
            sd = math.sqrt(sum((x - mid) ** 2 for x in w) / n)
            out.append((mid, mid + k * sd, mid - k * sd))
    return out


def stochastic(highs, lows, closes, n=14, d_n=3):
    """返回 %K / %D 序列(长度对齐,前段 None)。"""
    if len(closes) < n:
        return None
    k = []
    for i in range(len(closes)):
        if i + 1 < n:
            k.append(None)
        else:
            hh, ll = max(highs[i + 1 - n:i + 1]), min(lows[i + 1 - n:i + 1])
            k.append(50.0 if hh == ll else (closes[i] - ll) / (hh - ll) * 100)
    d = []
    for i in range(len(k)):
        w = [x for x in k[max(0, i + 1 - d_n):i + 1] if x is not None]
        d.append(sum(w) / len(w) if w else None)
    return {"k": k, "d": d}


def detect_channel(bars, n=60, k=2.0):
    """线性回归通道:中线=回归线,上下轨=中线 ± k*残差标准差;标注突破状态。"""
    if len(bars) < 10:
        return None
    if len(bars) < n:
        n = len(bars)
    seg = bars[-n:]
    xs = list(range(len(seg)))
    ys = [b["c"] for b in seg]
    m_ = len(xs)
    mx, my = sum(xs) / m_, sum(ys) / m_
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((xs[i] - mx) * (ys[i] - my) for i in range(m_))
    slope = 0.0 if sxx == 0 else sxy / sxx
    intercept = my - slope * mx
    resid = [ys[i] - (intercept + slope * xs[i]) for i in range(m_)]
    sd = math.sqrt(sum(r * r for r in resid) / m_) if m_ > 1 else 0.0
    last_x = m_ - 1
    mid = intercept + slope * last_x
    upper, lower = mid + k * sd, mid - k * sd
    last_c = ys[-1]
    if last_c > upper:
        state = "突破上轨(顺势加速/警惕假突破)"
    elif last_c < lower:
        state = "跌破下轨(转弱/警惕假突破)"
    else:
        state = "通道内运行"
    return {"slope": round(slope, 5), "mid": round(mid, 5),
            "upper": round(upper, 5), "lower": round(lower, 5),
            "sd": round(sd, 5), "state": state, "k": k, "n": m_}


def detect_gap(bars, n=5):
    """识别最近 n 根内的跳空(窗口):方向、幅度、是否回补。Murphy 第 2、11 章。

    向上跳空: 今开 > 昨高; 向下跳空: 今开 < 昨低。窗口关闭(回补) = 后续价格回到缺口内。
    """
    if len(bars) < 2:
        return None
    seg = bars[-n:] if len(bars) >= n else bars
    for i in range(len(seg) - 1, 0, -1):
        cur, prev = seg[i], seg[i - 1]
        if cur["o"] > prev["h"]:
            gap = cur["o"] - prev["h"]
            filled = any(b["l"] <= prev["h"] for b in seg[i + 1:])
            return {"dir": "up", "size": round(gap, 5), "filled": filled,
                    "note": "向上跳空;未回补=突破/中继动能,回补=普通或衰竭"}
        if cur["o"] < prev["l"]:
            gap = prev["l"] - cur["o"]
            filled = any(b["h"] >= prev["l"] for b in seg[i + 1:])
            return {"dir": "down", "size": round(gap, 5), "filled": filled,
                    "note": "向下跳空;未回补=突破/中继动能,回补=普通或衰竭"}
    return None


# ---- 经典日本蜡烛图形态(Murphy 第2章,补充 Morris 量化库) ----
def detect_classic(bars, ctx, n=8):
    """识别十字星/纺锤/marubozu/刺透/乌云盖顶/启明星/黄昏星/红三兵/黑三鸦。
    与 Morris 库共享前提:先定趋势背景(ctx),再判形态含义。"""
    res = []
    lo = max(3, len(bars) - n)
    for i in range(lo, len(bars)):
        b = bars[i]
        rng = b["h"] - b["l"]
        if rng <= 0:
            continue
        body = abs(b["c"] - b["o"])
        up_sh = b["h"] - max(b["o"], b["c"])
        dn_sh = min(b["o"], b["c"]) - b["l"]
        bull = b["c"] > b["o"]
        br = body / rng
        if br < 0.1:
            res.append((i, "十字星", "多空平衡/转折(趋势末端留意)", b["c"], 0)); continue
        if up_sh < 0.05 * rng and dn_sh < 0.05 * rng:
            res.append((i, "光头光脚" + ("阳线" if bull else "阴线"),
                        "强趋势驱动(顺势突破力度高)", b["c"], 1 if bull else -1)); continue
        if br < 0.35 and up_sh > 0.2 * rng and dn_sh > 0.2 * rng:
            res.append((i, "纺锤线", "动能衰减/犹豫(转折前兆)", b["c"], 0)); continue
        if i >= 2:
            p1 = bars[i - 1]
            p1b = abs(p1["c"] - p1["o"]) / max(p1["h"] - p1["l"], 1e-9)
            if (not p1["c"] > p1["o"]) and bull and b["o"] < p1["c"] and \
               b["c"] > (p1["o"] + p1["c"]) / 2 and ctx == "down":
                res.append((i, "刺透线", "看涨反转(需确认,弱于吞没)", b["c"], 1))
            if (p1["c"] > p1["o"]) and (not bull) and b["o"] > p1["c"] and \
               b["c"] < (p1["o"] + p1["c"]) / 2 and ctx == "up":
                res.append((i, "乌云盖顶", "看跌反转(需确认,弱于吞没)", b["c"], -1))
            if i >= 3:
                p3 = bars[i - 3]
                if (p3["c"] < p3["o"]) and p1b < 0.3 and bull and \
                   b["c"] > (p3["o"] + p3["c"]) / 2 and ctx == "down":
                    res.append((i, "启明星", "看涨反转(经典底部三星)", b["c"], 1))
                if (p3["c"] > p3["o"]) and p1b < 0.3 and (not bull) and \
                   b["c"] < (p3["o"] + p3["c"]) / 2 and ctx == "up":
                    res.append((i, "黄昏星", "看跌反转(经典顶部三星)", b["c"], -1))
        if i >= 3:
            a, b1, c1, d1 = bars[i - 3], bars[i - 2], bars[i - 1], b
            if all(x["c"] > x["o"] for x in (b1, c1, d1)) and b1["c"] > a["c"] and \
               c1["c"] > b1["c"] and d1["c"] > c1["c"]:
                res.append((i, "红三兵", "看涨驱动(底部/上升初,高位警惕透支)", b["c"], 1))
            if all(x["c"] < x["o"] for x in (b1, c1, d1)) and b1["c"] < a["c"] and \
               c1["c"] < b1["c"] and d1["c"] < c1["c"]:
                res.append((i, "黑三鸦", "看跌驱动", b["c"], -1))
    return res


# ---- Morris《蜡烛图精解》形态统计库 ----
# 样本: 7275 只常见流通股票 / 1460 万个交易日(Morris 实证)
#   dir     R+=看涨反转, R-=看跌反转
#   confirm 是否需次日确认(必须 / 推荐 / 不需要)
#   win1    第 1 日获利比例(%); pnl1 第 1 日 净收益/净亏损(>0 为统计正期望)
#   rank    综合评级 5=最优; freq 形态出现频率
# 关键结论:
#   1) 反转形态胜率大多不足 50%,须靠"确认"与位置过滤提升期望;
#   2) 顶部形态(上吊线)统计优势显著强于底部形态(锤子线)——反直觉但被数据支持;
#   3) 持续形态出现概率远高于反转形态(1日 75% vs 25%),故默认倾向顺势。
PATTERN_STATS = {
    "倒锤子线": {"dir": "R+", "confirm": "不需要", "win1": 67, "pnl1": 1.44, "rank": 5, "freq": "罕见(均隔1226根)"},
    "上吊线":   {"dir": "R-", "confirm": "不需要", "win1": 69, "pnl1": 1.32, "rank": 4, "freq": "频繁(均隔117根)"},
    "看涨孕线": {"dir": "R+", "confirm": "不需要", "win1": 49, "pnl1": 0.07, "rank": 3, "freq": "极频繁(均隔69根)"},
    "看涨吞没": {"dir": "R+", "confirm": "推荐",   "win1": 44, "pnl1": -0.27, "rank": 2, "freq": "极频繁(均隔74根)"},
    "看跌孕线": {"dir": "R-", "confirm": "必须",   "win1": 50, "pnl1": -0.08, "rank": 2, "freq": "极频繁(均隔59根)"},
    "流星线":   {"dir": "R-", "confirm": "必须",   "win1": 46, "pnl1": -0.44, "rank": 1, "freq": "罕见(均隔3418根)"},
    "看跌吞没": {"dir": "R-", "confirm": "必须",   "win1": 45, "pnl1": -0.34, "rank": 1, "freq": "极频繁(均隔73根)"},
    "锤子线":   {"dir": "R+", "confirm": "必须",   "win1": 41, "pnl1": -0.57, "rank": 1, "freq": "频繁(均隔284根)"},
    "内包线":   {"dir": "—",  "confirm": "必须(待突破方向)", "win1": None, "pnl1": None, "rank": None, "freq": "—"},
}

# Morris: 预测时段越长,形态预测力越弱(持续形态 vs 反转形态 vs 抛硬币)
HORIZON_TABLE = [(1, 75, 25, 50), (3, 65, 35, 50), (5, 60, 40, 50), (7, 55, 45, 50), (10, 50, 50, 50)]


def trend_context(bars, look=20):
    """形态识别前必须先确认现有趋势(Morris 第二假定)。

    返回 (趋势标签, 标准化斜率)。up=上升 / down=下降 / range=震荡
    """
    c = [b["c"] for b in bars]
    if len(c) < look + 1:
        return "unknown", 0.0
    base = c[-look - 1]
    slope = (c[-1] - base) / base if base else 0.0
    # 用 ATR 归一化,避免不同品种量纲差异
    a = atr([b["h"] for b in bars], [b["l"] for b in bars], c, 14) or 1e-9
    norm = (c[-1] - base) / (a * look)          # 每根平均推进多少个 ATR
    if norm > 0.05:
        return "up", slope
    if norm < -0.05:
        return "down", slope
    return "range", slope


def _confirm_state(bars, i, direction):
    """用次日 K 线确认形态是否成立(Morris:次日开盘确认,保险起见等收盘)。

    direction: +1 看涨形态 / -1 看跌形态
    返回 "已确认" / "已证伪" / "待确认(最新一根)"
    """
    if i >= len(bars) - 1:
        return "待确认(最新一根)"
    nxt = bars[i + 1]
    cur = bars[i]
    body_hi, body_lo = max(cur["o"], cur["c"]), min(cur["o"], cur["c"])
    if direction > 0 and nxt["c"] > body_hi:
        return "已确认"
    if direction < 0 and nxt["c"] < body_lo:
        return "已确认"
    return "已证伪"


def detect_patterns(bars, n=5, ctx="unknown"):
    """按 Morris《蜡烛图精解》量化标准识别形态。

    与旧版差异:
      - 严格按影线/实体倍数判定(而非占比阈值)
      - 依据趋势背景区分锤子线↔上吊线、倒锤子线↔流星线
      - 孕线用实体判定,内包线用最高最低价判定(两者不同)
      - 输出附 Morris 统计优势与确认状态
    """
    res = []
    lo = max(1, len(bars) - n)
    for i in range(lo, len(bars)):
        b = bars[i]
        p = bars[i - 1] if i > 0 else None
        rng = b["h"] - b["l"]
        if rng <= 0:
            continue
        body = abs(b["c"] - b["o"]) or 1e-9      # 防零除
        up_sh = b["h"] - max(b["o"], b["c"])     # 上影
        dn_sh = min(b["o"], b["c"]) - b["l"]     # 下影
        bull = b["c"] > b["o"]

        # ---- 伞形线族(长下影、小实体、实体在顶部) ----
        # 标准: 下影 >= 2倍实体; 上影 <= 幅度10%; 实体位于区间上半部
        is_umbrella = (dn_sh >= 2.0 * body) and (up_sh <= 0.10 * rng) and \
                      (min(b["o"], b["c"]) >= b["l"] + 0.6 * rng)
        if is_umbrella:
            if ctx == "down":
                name = "锤子线"
                bias = "看涨反转(阴线锤子弱于阳线)" if not bull else "看涨反转(阳线,力度更强)"
                res.append((i, name, bias, b["l"], +1))
            elif ctx == "up":
                name = "上吊线"
                bias = "看跌反转(阴线,力度更强)" if not bull else "看跌反转(阳线上吊线弱于阴线)"
                res.append((i, name, bias, b["h"], -1))

        # ---- 倒锤子线 / 流星线(长上影、小实体、实体在底部) ----
        # 标准: 上影 >= 2倍实体(流星线>=3倍); 下影 <= 幅度10%; 实体位于区间下半部
        is_top_shadow = (up_sh >= 2.0 * body) and (dn_sh <= 0.10 * rng) and \
                        (max(b["o"], b["c"]) <= b["l"] + 0.4 * rng)
        if is_top_shadow and p is not None:
            gap_up = b["l"] > p["h"]             # 向上跳空(流星线必要条件)
            if ctx == "up" and up_sh >= 3.0 * body and gap_up:
                res.append((i, "流星线", "看跌反转(需确认,单独使用统计期望为负)", b["h"], -1))
            elif ctx == "down":
                res.append((i, "倒锤子线", "看涨反转(统计最优形态,无需确认)", b["l"], +1))

        if p is None:
            continue
        p_body = abs(p["c"] - p["o"]) or 1e-9
        p_bull = p["c"] > p["o"]
        b_hi, b_lo = max(b["o"], b["c"]), min(b["o"], b["c"])
        p_hi, p_lo = max(p["o"], p["c"]), min(p["o"], p["c"])

        # ---- 吞没形态(实体完全包覆,颜色相反,顶底不可同时相等) ----
        engulf_up = (not p_bull) and bull and (b_hi >= p_hi) and (b_lo <= p_lo) and \
                    not (b_hi == p_hi and b_lo == p_lo)
        engulf_dn = p_bull and (not bull) and (b_hi >= p_hi) and (b_lo <= p_lo) and \
                    not (b_hi == p_hi and b_lo == p_lo)
        if engulf_up and ctx == "down":
            strong = "强(前实体≤后实体70%)" if p_body <= 0.7 * body else "一般"
            res.append((i, "看涨吞没", "看涨反转(%s,建议确认)" % strong, b["c"], +1))
        elif engulf_dn and ctx == "up":
            strong = "强(前实体≤后实体70%)" if p_body <= 0.7 * body else "一般"
            res.append((i, "看跌吞没", "看跌反转(%s,必须确认)" % strong, b["c"], -1))

        # ---- 孕线 Harami(第二根实体完全包含于第一根实体,颜色相反) ----
        harami = (b_hi <= p_hi) and (b_lo >= p_lo) and \
                 not (b_hi == p_hi and b_lo == p_lo) and (bull != p_bull)
        if harami and (body <= 0.7 * p_body):
            if (not p_bull) and ctx == "down":
                res.append((i, "看涨孕线", "看涨反转(前大阴线后小实体,无需确认)", b["c"], +1))
            elif p_bull and ctx == "up":
                res.append((i, "看跌孕线", "看跌反转(前大阳线后小实体,必须确认)", b["c"], -1))

        # ---- 内包线 Inside Bar(传统定义用最高最低价,不等同孕线) ----
        if b["h"] < p["h"] and b["l"] > p["l"]:
            res.append((i, "内包线", "整理蓄势(待突破方向,顺势突破概率更高)", b["c"], 0))

    # 附加 Morris 统计与确认状态
    out = []
    for i, name, bias, price, d in res:
        st = PATTERN_STATS.get(name, {})
        conf = _confirm_state(bars, i, d) if d else "—"
        out.append({
            "idx": i, "name": name, "bias": bias, "price": round(price, 5),
            "dir": st.get("dir", "—"),
            "confirm_rule": st.get("confirm", "—"),
            "confirm_state": conf,
            "win1": st.get("win1"),
            "pnl1": st.get("pnl1"),
            "rank": st.get("rank"),
            "freq": st.get("freq", "—"),
        })
    return out


# ----------------------------- 分析主函数 -----------------------------
def analyze(bars, symbol="", tf="", lookback=120):
    bars = bars[-lookback:] if lookback else bars
    if len(bars) < 10:
        return {"error": "K 线数量不足(<10),无法可靠解读"}
    o = [b["o"] for b in bars]
    h = [b["h"] for b in bars]
    l = [b["l"] for b in bars]
    c = [b["c"] for b in bars]
    v = [b["v"] for b in bars]
    last = bars[-1]
    ema20 = ema(c, 20)
    ema50 = ema(c, 50)
    a = atr(h, l, c, 14)
    ph, pl = pivots(h, l, window=5)
    struct = structure_from_pivots(ph, pl)

    # 趋势(EMA 排列 + 价格位置)
    e20, e50, cl = ema20[-1], ema50[-1], c[-1]
    if cl > e20 > e50:
        ema_trend = "多头排列(价格>EMA20>EMA50)"
    elif cl < e20 < e50:
        ema_trend = "空头排列(价格<EMA20<EMA50)"
    elif cl > e20 and e20 < e50:
        ema_trend = "反弹(价格上穿 EMA20,但 EMA20<EMA50)"
    elif cl < e20 and e20 > e50:
        ema_trend = "回落(价格下穿 EMA20,但 EMA20>EMA50)"
    else:
        ema_trend = "均线纠缠(无明确排列)"

    # 关键位
    recent_ph = [(i, p) for i, p in ph if i >= len(bars) - 60]
    recent_pl = [(i, p) for i, p in pl if i >= len(bars) - 60]
    resist = sorted({round(p, 5) for _, p in recent_ph}, reverse=True)[:4]
    support = sorted({round(p, 5) for _, p in recent_pl})[:4]
    # 样本不足时的兜底:用近期高低点作临时关键位,结构以 EMA 趋势描述
    if not resist:
        resist = [round(max(h[-min(30, len(h)):]), 5)]
    if not support:
        support = [round(min(l[-min(30, len(l)):]), 5)]
    if struct == "样本不足":
        if "多头" in ema_trend:
            struct = "顺势偏多(摆动点样本少,以EMA为准)"
        elif "空头" in ema_trend:
            struct = "顺势偏空(摆动点样本少,以EMA为准)"
        else:
            struct = "样本不足(建议≥30根K线)"
    rnd = round_levels(cl, 5)
    # 取当前价上下最近各 2 个整数位
    rnd_near = [x for x in rnd if abs(x - cl) <= abs(rnd[0] - cl) * 3][:6] if rnd else []

    # 趋势背景(形态识别的前置条件:Morris 第二假定——先确认趋势,再识别形态)
    trend_ctx, _slope = trend_context(bars)
    ctx_source = "摆动斜率(ATR归一化)"
    # 样本不足(<21根)时用 EMA 排列兜底,保证仍能出形态,但标注降级
    if trend_ctx == "unknown":
        if "多头" in ema_trend:
            trend_ctx, ctx_source = "up", "EMA兜底(样本<21根,可靠性降级)"
        elif "空头" in ema_trend:
            trend_ctx, ctx_source = "down", "EMA兜底(样本<21根,可靠性降级)"
        else:
            trend_ctx, ctx_source = "range", "EMA兜底(样本<21根,可靠性降级)"

    # 形态(带 Morris 统计评级与确认状态,按评级降序)
    pats = detect_patterns(bars, 5, trend_ctx)
    pats.sort(key=lambda x: (x.get("rank") or 0, x["idx"]), reverse=True)

    # 形态综合提示:统计正期望 + 确认状态 双重过滤
    # 已证伪的形态即使统计占优也失效,不得推荐
    alive = [p for p in pats if p.get("confirm_state") != "已证伪"]
    dead_strong = [p for p in pats
                   if p.get("confirm_state") == "已证伪" and (p.get("pnl1") or 0) > 0]
    strong = [p for p in alive if (p.get("pnl1") or 0) > 0]
    confirmed = [p for p in strong if p.get("confirm_state") == "已确认"]
    rev_alive = [p for p in alive if p.get("dir") in ("R+", "R-")]   # 反转形态(排除整理形态)
    if confirmed:
        best = confirmed[0]
        pat_note = ("可直接跟踪:%s(第%s根,已确认,1日胜率约%s%%,净盈亏比 %s)——统计正期望且次日已验证"
                    % (best["name"], best["idx"], best["win1"], best["pnl1"]))
    elif strong:
        best = strong[0]
        pat_note = ("最强信号:%s(第%s根,1日胜率约%s%%,净盈亏比 %s,%s)——统计占优但尚未确认,等次日收盘验证"
                    % (best["name"], best["idx"], best["win1"], best["pnl1"], best["confirm_state"]))
    elif rev_alive:
        pat_note = ("检出 %d 个反转形态但均非统计正期望(pnl1≤0),按 Morris 结论须等次日确认后再动,不宜裸信号入场"
                    % len(rev_alive))
    elif alive:
        pat_note = "仅检出整理形态(内包线),无反转信号——震荡蓄势,待突破方向确认后再顺势跟进"
    else:
        pat_note = "近期无符合 Morris 标准的有效形态;无信号本身即信息——倾向顺势或观望"
    if dead_strong:
        pat_note += " | 已失效(次日证伪,勿追):" + "、".join(
            "%s@第%s根" % (p["name"], p["idx"]) for p in dead_strong)

    # 预测时效提示(Morris:时段越长,形态预测力越弱)
    horizon_note = "形态预测力随持有期衰减:" + "; ".join(
        "%d日 持续%d%%/反转%d%%" % (d, s, r) for d, s, r, _c in HORIZON_TABLE)

    # ---- 技术指标(Murphy《金融市场技术分析》框架) ----
    m_data = macd(c)
    m_state = macd_state(m_data, c)
    r_data = rsi(c, 14)
    b_data = bollinger(c, 20, 2)
    s_data = stochastic(h, l, c, 14, 3)
    chan = detect_channel(bars, min(60, len(bars)))
    classics = detect_classic(bars, trend_ctx, 8)
    gap = detect_gap(bars, min(20, len(bars)))
    rsi14 = r_data[-1] if r_data else None
    boll_last = b_data[-1] if b_data else (None, None, None)
    stoch_last = (s_data["k"][-1], s_data["d"][-1]) if s_data else (None, None)

    # 量价背离(修正:在末段窗口内定位极值索引,避免 c.index 在全表误匹配)
    divergence = ""
    win = min(20, len(c))
    if any(x > 0 for x in v) and win >= 10:
        seg_c, seg_v = c[-win:], v[-win:]
        v_mean = sum(seg_v) / len(seg_v)
        i_h = seg_c.index(max(seg_c))
        i_l = seg_c.index(min(seg_c))
        if i_h >= win - 5 and seg_v[i_h] < v_mean:
            divergence = "近 %d 根价格创新高但量能低于均值,警惕上行动能背离(反转预警)" % win
        elif i_l >= win - 5 and seg_v[i_l] < v_mean:
            divergence = "近 %d 根价格创新低但量能低于均值,警惕下行动能背离(反弹预警)" % win

    report = {
        "symbol": symbol,
        "tf": tf,
        "bars_used": len(bars),
        "last_close": round(cl, 5),
        "ema20": round(e20, 5),
        "ema50": round(e50, 5),
        "atr14": round(a, 5),
        "trend_ema": ema_trend,
        "trend_context": trend_ctx,
        "trend_ctx_source": ctx_source,
        "structure": struct,
        "resistance": [round(x, 5) for x in resist],
        "support": [round(x, 5) for x in support],
        "round_levels": [round(x, 5) for x in rnd_near],
        "patterns": pats,
        "pattern_note": pat_note,
        "horizon_note": horizon_note,
        "divergence": divergence,
        "macd": m_state,
        "rsi14": round(rsi14, 2) if rsi14 is not None else None,
        "boll": {"mid": round(boll_last[0], 5) if boll_last[0] else None,
                 "upper": round(boll_last[1], 5) if boll_last[1] else None,
                 "lower": round(boll_last[2], 5) if boll_last[2] else None},
        "stoch": {"k": round(stoch_last[0], 2) if stoch_last[0] is not None else None,
                  "d": round(stoch_last[1], 2) if stoch_last[1] is not None else None},
        "channel": chan,
        "gap": gap,
        "classic_patterns": [{"idx": i, "name": nm, "bias": bz, "price": round(pr, 5), "dir": d}
                             for i, nm, bz, pr, d in classics],
        "last_bar": {"t": last["t"], "o": last["o"], "h": last["h"], "l": last["l"], "c": last["c"], "v": last["v"]},
    }
    return report


# ----------------------------- 输出层 -----------------------------
def to_text(r):
    if "error" in r:
        return "✗ " + r["error"]
    lines = []
    lines.append(f"【K线盘面解读】{r['symbol'] or '—'} · {r['tf'] or '—'}  共 {r['bars_used']} 根")
    lines.append(f"最新收盘: {r['last_close']}   日期/序号: {r['last_bar']['t']}")
    lines.append("─" * 40)
    lines.append(f"1) 趋势(EMA): {r['trend_ema']}   EMA20={r['ema20']}  EMA50={r['ema50']}")
    ctx_map = {"up": "上升", "down": "下降", "range": "震荡", "unknown": "样本不足"}
    lines.append(f"2) 市场结构: {r['structure']}   [趋势背景: {ctx_map.get(r.get('trend_context','unknown'),'—')}"
                 f" ({r.get('trend_ctx_source','—')}) → 形态判定的前置条件]")
    lines.append(f"3) ATR(14): {r['atr14']}  (止损距离建议以 ATR 倍数表达)")
    lines.append(f"4) 阻力位: {', '.join(str(x) for x in r['resistance']) or '—'}")
    lines.append(f"5) 支撑位: {', '.join(str(x) for x in r['support']) or '—'}")
    lines.append(f"6) 整数关口: {', '.join(str(x) for x in r['round_levels']) or '—'}")
    if r["patterns"]:
        lines.append("7) 价格行为形态(Morris《蜡烛图精解》量化标准,按统计评级排序):")
        for p in r["patterns"]:
            star = ("★" * p["rank"]) if p.get("rank") else "—"
            stat = ""
            if p.get("win1") is not None:
                stat = f" | 1日胜率≈{p['win1']}% 净盈亏比{p['pnl1']} {star} | 确认:{p['confirm_rule']}→{p['confirm_state']} | 频率:{p['freq']}"
            lines.append(f"   · 第{p['idx']}根 【{p['name']}】{p['dir']} — {p['bias']} (参考价 {p['price']}){stat}")
        lines.append(f"   >> 综合: {r.get('pattern_note','')}")
        lines.append(f"   >> 时效: {r.get('horizon_note','')}")
    else:
        lines.append("7) 价格行为形态: 无符合 Morris 标准的形态")
        lines.append(f"   >> 综合: {r.get('pattern_note','')}")
    if r["divergence"]:
        lines.append(f"8) 量价提示: {r['divergence']}")

    # 9) 通道(回归通道)
    ch = r.get("channel")
    if ch:
        lines.append(f"9) 回归通道: 上轨 {ch['upper']} / 中轨 {ch['mid']} / 下轨 {ch['lower']}"
                     f" (斜率 {ch['slope']}, ±{ch['k']}σ) → {ch['state']}")

    # 9b) 跳空/窗口
    gp = r.get("gap")
    if gp:
        filled_txt = "已回补(普通/衰竭)" if gp["filled"] else "未回补(突破/中继动能)"
        lines.append(f"9b) 跳空/窗口: {gp['dir']} 幅度 {gp['size']} | {filled_txt} — {gp['note']}")

    # 10) 技术指标(Murphy 框架)
    lines.append("10) 技术指标:")
    m = r.get("macd") or {}
    if m:
        lines.append(f"    · MACD: DIF={m.get('dif')} DEA={m.get('dea')} 柱={m.get('hist')}"
                     f" [{m.get('zero')} · {m.get('cross')}]"
                     + (f" | {m['divergence']}" if m.get("divergence") else ""))
    rs = r.get("rsi14")
    if rs is not None:
        ob = " (超买≥70)" if rs >= 70 else (" (超卖≤30)" if rs <= 30 else "")
        lines.append(f"    · RSI(14)={rs}{ob}")
    bl = r.get("boll") or {}
    if bl.get("mid") is not None:
        lines.append(f"    · 布林: 中轨 {bl['mid']} / 上轨 {bl['upper']} / 下轨 {bl['lower']}")
    st = r.get("stoch") or {}
    if st.get("k") is not None:
        lines.append(f"    · 随机: %K={st['k']} %D={st['d']}"
                     + (" (超买≥80)" if st["k"] >= 80 else (" (超卖≤20)" if st["k"] <= 20 else "")))

    # 11) 经典蜡烛图形态(Murphy,补充 Morris 量化库)
    cps = r.get("classic_patterns") or []
    if cps:
        lines.append("11) 经典蜡烛图形态(补充识别集):")
        for p in cps[-8:]:
            dmap = {1: "看涨", -1: "看跌", 0: "中性"}
            lines.append(f"   · 第{p['idx']}根 【{p['name']}】{dmap.get(p['dir'], '—')} — {p['bias']} (参考价 {p['price']})")
    lines.append("─" * 40)
    lines.append("判定纪律: 以上为客观盘面事实。方向须顺宏观研判与跨市场印证;")
    lines.append("          反转形态单独使用统计期望多为负,须等确认 + 关键位共振再动手。")
    return "\n".join(lines)


def to_html(r, bars, symbol, tf):
    if "error" in r:
        return f"<html><body><h3>{r['error']}</h3></body></html>"
    # ECharts candlestick data: [open, close, low, high]
    view = bars[-max(60, r["bars_used"]) :]
    data = [[b["t"], b["o"], b["c"], b["l"], b["h"]] for b in view]
    cats = [b["t"] for b in view]
    marks = []
    for lv in r["resistance"]:
        marks.append({"yAxis": lv, "label": {"formatter": f"阻 {lv}", "color": "#ff4d4f"}, "lineStyle": {"color": "#ff4d4f"}})
    for lv in r["support"]:
        marks.append({"yAxis": lv, "label": {"formatter": f"支 {lv}", "color": "#52c41a"}, "lineStyle": {"color": "#52c41a"}})
    for lv in r["round_levels"]:
        marks.append({"yAxis": lv, "label": {"formatter": f"{lv}", "color": "#888"}, "lineStyle": {"color": "#555", "type": "dashed"}})
    ch = r.get("channel")
    if ch:
        marks.append({"yAxis": ch["upper"], "label": {"formatter": f"通道上轨 {ch['upper']}", "color": "#ffa940"},
                      "lineStyle": {"color": "#ffa940"}})
        marks.append({"yAxis": ch["mid"], "label": {"formatter": f"通道中轨 {ch['mid']}", "color": "#7df9ff"},
                      "lineStyle": {"color": "#7df9ff", "type": "dashed"}})
        marks.append({"yAxis": ch["lower"], "label": {"formatter": f"通道下轨 {ch['lower']}", "color": "#36cfc9"},
                      "lineStyle": {"color": "#36cfc9"}})
    html = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>K线盘面解读 %s %s</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>body{background:#0b0e14;color:#e6e6e6;font-family:system-ui,'Microsoft YaHei';margin:0;padding:16px}
h2{color:#7df9ff;text-shadow:0 0 8px #1b6} .box{background:#11151f;border:1px solid #1f2a3a;border-radius:10px;padding:12px;margin-top:12px}
.k{color:#7df9ff} .r{color:#ff4d4f} .g{color:#52c41a}</style></head>
<body>
<h2>K线盘面解读 · %s · %s</h2>
<div id="main" style="width:100%%;height:460px"></div>
<div class="box">%s</div>
<script>
var chart=echarts.init(document.getElementById('main'),'dark');
var data=%s; var cats=%s;
chart.setOption({backgroundColor:'#0b0e14',
 grid:{left:60,right:20,top:20,bottom:60},
 xAxis:{type:'category',data:cats,axisLabel:{color:'#888'}},
 yAxis:{scale:true,axisLabel:{color:'#888'}},
 tooltip:{trigger:'axis'},
 series:[{type:'candlestick',data:data.map(d=>[d[1],d[2],d[3],d[4]]),
  itemStyle:{color:'#ff4d4f',color0:'#52c41a',borderColor:'#ff4d4f',borderColor0:'#52c41a'},
  markLine:{symbol:'none',data:%s}}]});
</script></body></html>""" % (
        symbol, tf, symbol, tf,
        to_text(r).replace("\n", "<br>"),
        json.dumps(data, ensure_ascii=False),
        json.dumps(cats, ensure_ascii=False),
        json.dumps(marks, ensure_ascii=False),
    )
    return html


# ----------------------------- 入口 -----------------------------
def run_fetch(args):
    """--fetch 模式:从权威渠道(Twelve Data)抓取 15min/1H/4H/1D/1W 并逐周期分析。

    铁律:任何周期抓取失败只报告原因并跳过;全部失败则明确告知"无法获取权威K线数据",
    绝不编造价格。无 Key / 网络受限时引导用户改用 --csv / --text。
    """
    try:
        import kline_fetch as kf
    except ImportError:
        print("✗ 未能加载 kline_fetch 模块(请确认与 kline_read.py 同目录)")
        return

    apikey = args.api_key or os.environ.get("TWELVEDATA_API_KEY", "")
    if not apikey:
        print("✗ 未配置 Twelve Data API Key(环境变量 TWELVEDATA_API_KEY 或 --api-key)。")
        print("  免费注册 https://twelvedata.com 获取;无 Key 时本环境无法联网获取 K 线。")
        print("  替代方案:由 MT4 导出 CSV 用 --csv,或直接在对话粘贴 OHLC 用 --text。")
        return

    if not args.symbol:
        print("✗ --fetch 需要 --symbol(如 --symbol USDJPY)")
        return

    print(f"⏳ 从 Twelve Data 获取 {args.symbol} 的 15min/1H/4H/1D/1W ...")
    results = kf.fetch_multi(args.symbol, kf.STD_INTERVALS, apikey, output_size=200)
    any_ok = False
    for label, (bars, err) in results.items():
        if bars is None:
            print(f"  · {label}: ✗ 获取失败({err})")
            continue
        any_ok = True
        print(f"  · {label}: ✓ {len(bars)} 根")
        rep = analyze(bars, args.symbol, label, args.last)
        if not args.no_text:
            print("─" * 50)
            print(to_text(rep))
        if args.json:
            os.makedirs(args.out, exist_ok=True)
            jp = os.path.join(args.out, f"kline_read_{args.symbol}_{label}.json")
            with open(jp, "w", encoding="utf-8") as f:
                json.dump(rep, f, ensure_ascii=False, indent=2)
            print(f"[JSON] -> {jp}")

    if not any_ok:
        print("\n⚠️ 无法从任何权威渠道获取 K 线数据(网络受限 / 品种不支持 / Key 无效)。")
        print("   严禁自行编造或估算任何价格。请贴出 MT4 导出的 CSV(--csv)或 OHLC 文本(--text)。")


def main():
    ap = argparse.ArgumentParser(description="K线盘面解读引擎")
    ap.add_argument("--csv", help="MT4/通用 OHLCV CSV 路径")
    ap.add_argument("--text", help="粘贴 OHLC 文本(每行 date,o,h,l,c[,v])")
    ap.add_argument("--symbol", default="", help="品种名(分析及 --fetch 抓取均需)")
    ap.add_argument("--tf", default="", help="周期(仅标注 / 分析目标)")
    ap.add_argument("--last", type=int, default=120, help="仅分析最近 N 根(默认120)")
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出目录")
    ap.add_argument("--json", action="store_true", help="输出 JSON 文件")
    ap.add_argument("--html", action="store_true", help="输出 HTML 标注图")
    ap.add_argument("--no-text", action="store_true", help="不打印文本解读")
    ap.add_argument("--fetch", action="store_true",
                    help="联网抓取 K 线(需 --symbol;默认取 15min/1H/4H/1D/1W,经 Twelve Data)")
    ap.add_argument("--api-key", default=os.environ.get("TWELVEDATA_API_KEY", ""),
                    help="Twelve Data API Key(或环境变量 TWELVEDATA_API_KEY)")
    args = ap.parse_args()

    if args.fetch:
        run_fetch(args)
        return

    if args.csv:
        bars = parse_csv(args.csv)
    elif args.text:
        bars = parse_text(args.text)
    else:
        ap.print_help()
        return

    if not bars:
        print("✗ 未能解析出任何 K 线(检查 CSV 格式或 --text)")
        return

    rep = analyze(bars, args.symbol, args.tf, args.last)
    if not args.no_text:
        print(to_text(rep))

    os.makedirs(args.out, exist_ok=True)
    token = (args.symbol or "kline") + ("_" + args.tf if args.tf else "")
    if args.json:
        jp = os.path.join(args.out, f"kline_read_{token}.json")
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        print(f"\n[JSON] -> {jp}")
    if args.html:
        hp = os.path.join(args.out, f"kline_read_{token}.html")
        with open(hp, "w", encoding="utf-8") as f:
            f.write(to_html(rep, bars, args.symbol, args.tf))
        print(f"[HTML] -> {hp}")


if __name__ == "__main__":
    main()
