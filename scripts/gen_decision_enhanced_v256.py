# -*- coding: utf-8 -*-
"""今日行情分析 v2.5.6 决策增强版 生成器 (kingforex-skill) · 2026-09-16 版
基准时间: 2026-09-16 15:45 GMT+8（数据层由 build_gen_20260916.py 注入, 渲染层继承 v2.5.2 冻结模板）
v2.5.6 授权调准（用户 2026-09-16 发出「调准格式」指令）:
  ① 第四节评分卡在 score-card 网格后新增 ECharts 评分图表（四维分组柱 + 综合总分折线 + 75分建仓虚线）;
  ② 各数据/信息节新增「数据截至」说明行（报价/K线/利率/日历/量化样本/回测样本）;
  ③ 章节序号调换: 数据一致性校验报告 = 十九、交易纪律 = 二十（纪律仍置末）。
  ④ (v2.5.6) scorechart 数值标注调准: 四维柱内部竖排显示数值(2位小数, 与四·补子项明细一致), 综合总分折线改用 2 位小数精确值(65.30 等, 与明细总分一致); v2.5.5 的 4.1 分项说明表已按用户指令撤回。
10 标的: 金/银/美元/欧元/英镑/日元/WTI原油 + 利差最大货币对(AUDJPY) + 韩元(USDKRW, 用户临时指定专项)
严格套用 kingforex-skill 决策增强版冻结模板; USDKRW 作为第 10 标接入: 快照/评分卡/K线/关键位/跨市场/宏观/综合判定 全链路统一输出。
所有 ECharts option 用 json.dumps 注入, 本地内嵌优先(离线/CDN回退)。
持仓口径: AUDJPY SELL 0.02 手 → 110.20 部分平仓 0.01 手(已实现) + 剩余 0.01 手持仓中。
"""
import os, csv, json, math, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, r"~/.workbuddy\skills\kingforex-skill\scripts")
import decision_enhanced_report_v25 as V25          # noqa: E402
import extra_sections as XS                          # noqa: E402

OUT = r"./output/2026-09-16"
NOW = "2026-09-16 15:45 GMT+8"
SKILL_CSS = "~/.workbuddy/skills/kingforex-skill/assets/decision_enhanced_sample.html"

# ---------- 账户状态 (09-15: AUDJPY 0.02 手 → 110.20 部分平仓 0.01 手, 剩余 0.01 手持仓中) ----------
USDJPY_RATE = 154.924       # USDJPY 09-16 日线(Twelve Data)
PART_CLOSE_LOT = 0.01
PART_CLOSE_PX = 110.20      # 用户实盘部分平仓价
POS_LOTS = 0.01             # 剩余持仓
POS_ENTRY = 114.573
POS_SL = 111.30             # 本次建议补挂的保护性止损(4H 摆动高点 + 1.5×4H ATR 上方)
POS_TP = 109.781
POS_CUR = 110.55409         # AUDJPY 09-16 日线(Twelve Data)
_pip_val = POS_LOTS * 1000 / USDJPY_RATE      # 每 0.01 手每 pip ≈ 0.06454
PART_PIPS = round((POS_ENTRY - PART_CLOSE_PX) / 0.01, 1)      # 437.3
PART_PNL = round(PART_PIPS * _pip_val, 2)                     # +28.24
_pips = round((POS_ENTRY - POS_CUR) / 0.01, 1)                # 剩余 401.9
POS_PNL = round(_pips * _pip_val, 2)                          # +26.86 浮盈
POS_PCT = round((POS_ENTRY - POS_CUR) / POS_ENTRY * 100, 2)
EQ_BASE = 574.23            # 部分平仓前净值
DEP = 522.0
ACC_EQUITY = round(EQ_BASE + PART_PNL, 2)     # 已实现净值 602.47
EQ_FLOAT = round(ACC_EQUITY + POS_PNL, 2)     # 含浮动 629.33
_to_tp = round((POS_CUR - POS_TP) / 0.01, 1)  # 距 TP 77.3 pips
_to_sl = round((POS_SL - POS_CUR) / 0.01, 1)  # 距保护 SL 74.6 pips
RISK_REST = round(_to_sl * _pip_val, 2)       # 5.74
RISK_REST_PCT = round(RISK_REST / ACC_EQUITY * 100, 2)   # 0.80%
# 盘中峰值: 09-14 最低 109.29, 0.02 手口径 → 峰值净值约 642.4
PEAK_EQ = 642.4
MAX_DD = round((PEAK_EQ - ACC_EQUITY) / PEAK_EQ * 100, 1)   # 6.2%
R_UNIT_PIPS = 128.9         # 原始 SL(113.284) 距离 = 1R 基准
ACC = {
    "equity": ACC_EQUITY, "deposit": DEP, "floating": POS_PNL,
    "cum_ret": round((ACC_EQUITY - DEP) / DEP * 100, 2),
    "cum_ret_float": round((EQ_FLOAT - DEP) / DEP * 100, 2),
    "max_dd": MAX_DD,
}
POS = {
    "symbol": "AUDJPY", "dir": "SELL", "lots_open": 0.02, "lots_now": POS_LOTS,
    "entry": POS_ENTRY, "sl_orig": 113.284, "sl_new": POS_SL, "tp": POS_TP,
    "cur": POS_CUR, "max_pips": _pips, "pct": POS_PCT,
    "risk_usd": RISK_REST, "risk_orig": 16.63, "risk_rest": RISK_REST,
    "risk_rest_pct": RISK_REST_PCT,
    "part_pips": PART_PIPS, "part_pnl": PART_PNL, "part_lot": PART_CLOSE_LOT,
    "part_px": PART_CLOSE_PX,
}
# ---------- 凯利 (AUDJPY 历史信号回测 60根日线 三周期共振) ----------
# f* = (p·b − q)/b = (0.625×1.85 − 0.375)/1.85 = 42.23%
KELLY = {
    "p": 62.5, "b": 1.85, "f": 42.23, "f_half": 21.11, "f_third": 14.08,
    "sl_pips": 116, "pip_val": round(_pip_val, 4), "rec_lots": 0.01, "max_loss": RISK_REST,
    "over": 0,
}
# ---------- 信号历史回测 (12笔, 样本有限仅供参考) ----------
BT = {"n": 12, "win": 8, "loss": 4, "winrate": 66.7, "pl": 1.85, "exp": 0.56,
      "max_win_streak": 4, "max_loss_streak": 2, "max_dd": 1.8, "pf": 2.62}
BT_SIGNALS = [
    ("12", "2026-09-02", "AUDJPY", "SELL", "114.573", "110.20", "+437", "+3.39R", "部分平仓·剩余0.01手持仓"),
    ("11", "2026-08-28", "USDJPY", "SELL", "155.82", "154.65", "+117", "+1.80R", "止盈"),
    ("10", "2026-08-20", "AUDJPY", "SELL", "113.02", "113.68", "-66", "-1.00R", "止损"),
    ("9",  "2026-08-12", "XAUUSD", "BUY",  "5280",    "5520",   "+240", "+2.20R", "止盈"),
    ("8",  "2026-08-05", "EURUSD", "BUY",  "1.1420",  "1.1535", "+115", "+1.65R", "止盈"),
    ("7",  "2026-07-28", "GBPUSD", "BUY",  "1.3280",  "1.3210", "-70",  "-1.00R", "止损"),
]
R_CUM = [1.0, 1.8, 2.9, 4.1, 3.3, 2.3, 3.95, 6.15, 5.15, 4.15, 5.95, 8.85]
# ---------- 动态止损方案对比（作用于剩余 0.01 手持仓） ----------
STOPS = {
    "atr":   {"name": "ATR止损", "sub": "1.5×D ATR", "lvl": "111.77", "dist": "121 pips (1.5×D ATR 0.8095)",
              "risk": round(121 * _pip_val, 2), "sweep": 18, "keep": 2, "scene": "趋势初期·破位追空"},
    "struct": {"name": "结构止损", "sub": "4H摆动高点上方", "lvl": "111.30", "dist": "75 pips (自现价 110.55)",
               "risk": round(75 * _pip_val, 2), "sweep": 26, "keep": 3, "scene": "事件周保护·震荡市"},
    "trail": {"name": "移动止损(推荐★)", "sub": "1H EMA20 跟踪下移", "lvl": "111.30→跟随下移", "dist": "动态收窄",
              "risk": RISK_REST, "sweep": 15, "keep": 5, "scene": "趋势中段(央行周后)"},
}
CORR_HIGH = [
    ("XAUUSD ↔ XAGUSD", "0.92", "黄金白银几乎同涨同跌, 不要同时做两笔"),
    ("EURUSD ↔ GBPUSD", "0.87", "欧镑高度联动, 同时做多=双倍美元空头暴露"),
    ("USDJPY ↔ AUDJPY", "0.80", "日元交叉盘共享日元端, 注意反向对冲关系"),
    ("USDKRW ↔ USDJPY", "0.71", "韩元与日元同受美元/美债端驱动, 避险期同向走强"),
]
CORR_LOW = [
    ("XAUUSD ↔ USDJPY", "-0.30", "逻辑不同源, 可组合分散风险"),
    ("XAUUSD ↔ AUDJPY", "0.02", "逻辑不同源, 可组合分散风险"),
    ("EURUSD ↔ USDJPY", "-0.55", "逻辑不同源, 可组合分散风险"),
    ("EURUSD ↔ AUDJPY", "-0.28", "逻辑不同源, 可组合分散风险"),
    ("GBPUSD ↔ USDJPY", "-0.57", "逻辑不同源, 可组合分散风险"),
    ("GBPUSD ↔ AUDJPY", "-0.28", "逻辑不同源, 可组合分散风险"),
    ("USDJPY ↔ AUDUSD", "-0.59", "逻辑不同源, 可组合分散风险"),
    ("AUDUSD ↔ AUDJPY", "0.00", "逻辑不同源, 可组合分散风险"),
    ("USDKRW ↔ XAUUSD", "-0.41", "韩元避险属性与黄金部分对冲"),
]
# ---------- 实时报价 (09-16 15:39 GMT+8 金十 / Twelve Data 日线) ----------
QUOTES = {
    "XAUUSD": (4337.29, "Twelve Data 日线"), "XAGUSD": (64.823, "金十实时"),
    "DXY": (99.55, "成分货币合成"), "EURUSD": (1.15551, "Twelve Data 日线"),
    "GBPUSD": (1.34825, "Twelve Data 日线"), "USDJPY": (154.924, "Twelve Data 日线"),
    "USOIL": (99.614, "金十实时"), "AUDUSD": (0.71361, "Twelve Data 日线"),
    "AUDJPY": (110.55409, "Twelve Data 日线(基准价)"), "USDKRW": (1364.38, "Twelve Data 日线"),
}
RATES = {"DGS3MO": 4.11, "DGS1": 4.37, "DGS2": 4.65, "DGS5": 4.80,
         "DGS10": 4.97, "DGS30": 5.34, "DFII10": 2.60, "T10YIE": 2.38,
         "T10Y2Y": 0.32, "FEDFUNDS": 3.625}
CARRY = [
    ("US 2s10s", "+0.32pp", "陡峭化(2Y 4.65% → 10Y 4.97%); 前日盘中一度触 5.025% 峰值后回落, 通胀粘性 + 融资需求仍推升长端"),
    ("AUD−JP (AUDJPY)", "+3.35pp → +3.10pp", "G10最大套息; AU 4.35% − JP 1.00%, BoJ 09-18 若加息 25bp 则收窄至 3.10%; 本轮套息平仓已于 110.20 兑现 +437.3 pips"),
    ("US−JP (USDJPY)", "+2.625pp → +2.875pp", "US 3.625% − JP 1.00%; Fed 加息 92% vs BoJ 同周加息 → 双向对冲后利差微幅走阔, USDJPY 154.92 高位"),
    ("US−KR (USDKRW)", "+0.625pp → +0.875pp", "US 3.625% − KR 3.00%; BoK 纪要显分歧(短期或不再加) + Fed 加息 92% → 美韩利差走阔 = 韩元结构性承压"),
]
SCORES = {
    "XAUUSD": {"macro":52,"tech":57,"quant":54,"sent":52,"verdict":"不建议建仓","reason":"Fed 加息92%(FOMC 今夜02:00) + 10Y 4.97%/实际利率2.60% 双压; 多头拥挤 89%分位; 日内反弹+1.04%至4338属事件前修复, 不追"},
    "XAGUSD": {"macro":50,"tech":52,"quant":46,"sent":48,"verdict":"不建议建仓","reason":"跟随黄金反弹+1.81%强于金, 但波动极端(VaR更高), 量化健康度弱, 规避"},
    "DXY":    {"macro":66,"tech":62,"quant":63,"sent":62,"verdict":"指数·非交易","reason":"美元指数非直接可交易品种; Fed 加息92%支撑, 今夜FOMC定方向, 仅作参照"},
    "EURUSD": {"macro":56,"tech":58,"quant":58,"sent":54,"verdict":"不建议建仓","reason":"ECB 紧缩(2.25%)有支撑但被美债收益率压制; FOMC 今夜双向风险, 无合格 R:R"},
    "GBPUSD": {"macro":56,"tech":58,"quant":57,"sent":55,"verdict":"观望","reason":"英8月CPI年率3.1%超预期(今日14:00公布)→BoE 09-17 维持3.75%概率上升; 但与FOMC相邻, 事件前静默"},
    "USDJPY": {"macro":62,"tech":56,"quant":54,"sent":58,"verdict":"不建议建仓","reason":"美日利差+2.625pp支撑, 但 BoJ 09-18 加息25bp预期 + 干预风险双向, 今夜FOMC事件前不新开"},
    "USOIL":  {"macro":50,"tech":54,"quant":46,"sent":52,"verdict":"不建议建仓","reason":"回落-1.31%至99.61; 投机拥挤度 97%分位极度拥挤; 今晚EIA库存(★4), 事件窗口不碰"},
    "AUDJPY": {"macro":66,"tech":68,"quant":64,"sent":62,"verdict":"持仓管理·非新开","reason":"剩余 0.01 手空单浮盈 +401.9 pips; 距TP 77.3 pips vs 距保护SL 74.6 pips → 剩余R:R 1.04 勉强及格, 仅管理不加仓, 确认保护 SL 111.30 已挂"},
    "AUDUSD": {"macro":55,"tech":54,"quant":54,"sent":53,"verdict":"观望","reason":"区间 0.706-0.722 震荡无方向; 今夜FOMC双向, 等事件落地再评估"},
    "USDKRW": {"macro":58,"tech":70,"quant":56,"sent":52,"verdict":"观望(高位·不追多)","reason":"4H 多头排列(EMA5 1364.14>EMA10 1360.15>EMA60 1350.32)且站上通道上轨1365.07; 但日内冲高1372.98回落, ATR(4H)放大至6.47, 追多赔率不合格"},
}

# ===================== 工具函数 =====================
def load_kline(path):
    rows = []
    if not os.path.exists(path): return rows
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                rows.append((r["datetime"], float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])))
            except: pass
    return rows

def ema(vals, n):
    if len(vals) < n: return vals[-1] if vals else 0
    k = 2.0/(n+1); e = vals[0]
    for v in vals[1:]: e = v*k + e*(1-k)
    return e

def atr(rows, n=14):
    if len(rows) < n+1: return 0
    trs = []
    for i in range(1, len(rows)):
        h, l, pc = rows[i][2], rows[i][3], rows[i-1][4]
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    return sum(trs[-n:])/n

def trend_str(rows):
    if len(rows) < 50: return "数据不足"
    closes = [r[4] for r in rows]
    e20, e50 = ema(closes, 20), ema(closes, 50)
    e200 = ema(closes, 200) if len(closes) >= 200 else ema(closes, len(closes))
    if e20 > e50 > e200: return "多头排列"
    if e20 < e50 < e200: return "空头排列"
    if e20 > e50: return "短多长空(震荡偏多)"
    return "短空长多(震荡偏空)"

def pearson(a, b):
    n = min(len(a), len(b))
    if n < 3: return 0
    a, b = a[:n], b[:n]
    ma, mb = sum(a)/n, sum(b)/n
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x-ma)**2 for x in a)); db = math.sqrt(sum((y-mb)**2 for y in b))
    return num/(da*db) if da*db else 0

# ===================== K线数据 (6 + USDKRW = 7 文件) =====================
KL_DIR = os.path.join(OUT, "kline")
_kd_names = {"XAUUSD": "kline_XAUUSD_1d.csv", "EURUSD": "kline_EURUSD_1d.csv",
             "GBPUSD": "kline_GBPUSD_1d.csv", "USDJPY": "kline_USDJPY_1d.csv",
             "AUDUSD": "kline_AUDUSD_1d.csv", "AUDJPY": "kline_AUDJPY_1d.csv",
             "USDKRW": "kline_USDKRW_1d.csv"}
KD = {s: os.path.join(KL_DIR, p) for s, p in _kd_names.items()}
klines = {s: load_kline(p) for s, p in KD.items()}

_missing = [s for s, _r in klines.items() if not _r]
if _missing:
    raise SystemExit("[数据缺失] 未找到以下品种的日线 CSV: %s" % (", ".join(_missing),))

def chart_candlestick(sym, rows, marklines=None, title=None):
    dates = [r[0] for r in rows]
    data = [[r[1], r[4], r[3], r[2]] for r in rows]
    ml = []
    if marklines:
        for m in marklines:
            ml.append({"name": m[0], "yAxis": m[1],
                       "lineStyle": {"color": m[2], "type": m[3], "width": 2},
                       "label": {"formatter": m[0]+": "+str(m[1])}})
    opt = {"backgroundColor": "transparent",
           "grid": {"left": 60, "right": 20, "top": 30, "bottom": 60},
           "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
           "xAxis": {"type": "category", "data": dates, "axisLine": {"lineStyle": {"color": "#3a4a6a"}},
                     "axisLabel": {"color": "#7fa9ff", "fontSize": 10}, "scale": True, "boundaryGap": False},
           "yAxis": {"scale": True, "axisLine": {"lineStyle": {"color": "#3a4a6a"}},
                     "splitLine": {"lineStyle": {"color": "rgba(127,169,255,.1)"}}, "axisLabel": {"color": "#a8b8d0"}},
           "dataZoom": [{"type": "inside", "start": 55, "end": 100},
                        {"type": "slider", "start": 55, "end": 100, "height": 18, "bottom": 20, "textStyle": {"color": "#7fa9ff"}}],
           "series": [{"type": "candlestick", "data": data,
                       "itemStyle": {"color": "#2ecc71", "color0": "#e74c3c", "borderColor": "#2ecc71", "borderColor0": "#e74c3c"},
                       "markLine": {"symbol": "none", "data": ml, "label": {"color": "#fff", "position": "end", "fontSize": 10}}}]}
    div = "chart_"+sym.replace("/", "")
    html = '<div class="chart-box"><div class="chart-title">📈 '+(title or sym)+' · 日K ('+str(len(rows))+'根)</div><div id="'+div+'" class="chart"></div></div>'
    js = "echarts.init(document.getElementById('"+div+"')).setOption("+json.dumps(opt, ensure_ascii=False)+");"
    return html, js

charts_html, charts_js = [], []
for s in ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "AUDJPY", "USDKRW"]:
    ml = None
    if s == "AUDJPY":
        ml = [("入场114.573", 114.573, "#3498db", "solid"), ("保护SL 111.30", 111.30, "#e74c3c", "dashed"),
              ("部分平仓110.20", 110.20, "#9b59b6", "dotted"),
              ("TP 109.781", 109.781, "#2ecc71", "dashed"), ("当前110.41", QUOTES["AUDJPY"][0], "#f1c40f", "solid")]
    elif s == "USDKRW":
        ml = [("通道上轨1355.49", 1355.49, "#e74c3c", "dashed"),
              ("当前1364.38", round(klines["USDKRW"][-1][4], 2), "#f1c40f", "solid"),
              ("52周低1334.63", 1334.63, "#2ecc71", "dashed")]
    h, j = chart_candlestick(s, klines[s], ml)
    charts_html.append(h); charts_js.append(j)

silver_oil_note = ('<div class="card" style="grid-column:1/-1"><div class="card-title">⚠️ XAGUSD / USOIL K线数据源暂缺</div>'
    '<div class="card-sub">Twelve Data 该品种返回 404、iTick 免费层限频返回 0 根, 按技能铁律不编造价格。'
    '以实时报价 + CFTC 持仓 + 宏观事件呈现: 白银 63.493 (金十); WTI 98.765 (金十, 日内高100.8); CFTC WTI 拥挤做多(97%分位)。</div></div>')

# ===================== 相关性矩阵 (7标的日收益) =====================
def rets(sym):
    cs = [r[4] for r in klines[sym]]
    return [(cs[i]-cs[i-1])/cs[i-1] for i in range(1, len(cs))]
corr_syms = ["XAUUSD","EURUSD","GBPUSD","USDJPY","AUDUSD","AUDJPY","USDKRW"]
ret_series = {s: rets(s) for s in corr_syms}
minlen = min(len(ret_series[s]) for s in corr_syms)
for s in corr_syms: ret_series[s] = ret_series[s][-minlen:]
corr_mat = [[round(pearson(ret_series[a], ret_series[b]), 2) for b in corr_syms] for a in corr_syms]
corr_opt = {"backgroundColor":"transparent","tooltip":{"position":"top"},
    "grid":{"left":70,"right":20,"top":20,"bottom":70},
    "xAxis":{"type":"category","data":corr_syms,"axisLabel":{"color":"#7fa9ff","rotate":30},"splitArea":{"show":True}},
    "yAxis":{"type":"category","data":corr_syms,"axisLabel":{"color":"#7fa9ff"},"splitArea":{"show":True}},
    "visualMap":{"min":-1,"max":1,"calculable":True,"orient":"horizontal","left":"center","bottom":10,
                 "inRange":{"color":["#e74c3c","#1c2541","#2ecc71"]},"textStyle":{"color":"#a8b8d0"}},
    "series":[{"type":"heatmap","data":[[i,j,corr_mat[i][j]] for i in range(len(corr_syms)) for j in range(len(corr_syms))],
               "label":{"show":True,"color":"#fff","fontSize":11}}]}

# ===================== 量化雷达 (AUDJPY持仓) =====================
def quant_block(sym):
    cs = [r[4] for r in klines[sym]]
    rs = [(cs[i]-cs[i-1])/cs[i-1] for i in range(1, len(cs))]
    n = len(rs); mu = sum(rs)/n; var = sum((x-mu)**2 for x in rs)/(n-1); sd = math.sqrt(var)
    sharpe = mu/sd*math.sqrt(252) if sd else 0
    sortino = mu/(math.sqrt(sum(x*x for x in rs if x < 0)/(sum(1 for x in rs if x < 0) or 1)))*math.sqrt(252) if sd else 0
    skew = sum((x-mu)**3 for x in rs)/n/(sd**3) if sd else 0
    def hurst(s):
        """R/S Hurst —— 对 log 价格序列计算（趋势持续性的标准口径）。
        修正 v2.4.2：原实现作用在「收益」序列上，返回值偏低且口径不符。"""
        lp = [math.log(x) for x in s if x > 0]
        lags = [l for l in (4, 8, 16, 32) if l <= len(lp) // 2]
        if len(lags) < 2:
            return 0.5
        pts = []
        for lag in lags:
            vals = []
            for start in range(0, len(lp) - lag + 1, lag):
                seg = lp[start:start+lag]
                m = sum(seg) / len(seg); cum = 0.0; mx = -1e18; mn = 1e18
                for v in seg:
                    cum += v - m; mx = max(mx, cum); mn = min(mn, cum)
                sd = math.sqrt(sum((x - m) ** 2 for x in seg) / len(seg))
                if sd > 0:
                    vals.append((mx - mn) / sd)
            if vals:
                pts.append((math.log(lag), math.log(sum(vals) / len(vals))))
        if len(pts) < 2:
            return 0.5
        n2 = len(pts); mx2 = sum(p[0] for p in pts) / n2; my2 = sum(p[1] for p in pts) / n2
        den = sum((p[0] - mx2) ** 2 for p in pts)
        return (sum((p[0] - mx2) * (p[1] - my2) for p in pts) / den) if den else 0.5
    h = hurst(cs)
    # 偏离度 Z：以「收盘价」相对 60 日窗口的均值/标准差计算（修正 v2.4.2 误用收益均值+标准误的 bug）
    w = min(60, len(cs))
    seg_px = cs[-w:]
    pm = sum(seg_px)/len(seg_px)
    pv = sum((x-pm)**2 for x in seg_px)/len(seg_px)
    psd = math.sqrt(pv)
    z = (cs[-1]-pm)/psd if psd else 0
    var95 = abs(sorted(rs)[int(0.05*n)])*100 if n > 10 else 0
    return abs(h), abs(z), abs(sharpe), abs(sortino), abs(skew), var95
h_abs, z_abs, sh_abs, so_abs, sk_abs, var95 = quant_block("AUDJPY")
# v2.5.2: 韩元(USDKRW) 独立量化样本 —— 分标的单独雷达, 不叠加
h_k, z_k, sh_k, so_k, sk_k, var95_k = quant_block("USDKRW")
_j = 1 if (klines["AUDJPY"][-1][4] - (sum(r[4] for r in klines["AUDJPY"][-60:]) / 60.0)) >= 0 else -1
Z_SIGN = "+" if _j > 0 else "-"
_jk = 1 if (klines["USDKRW"][-1][4] - (sum(r[4] for r in klines["USDKRW"][-60:]) / 60.0)) >= 0 else -1
Z_SIGN_K = "+" if _jk > 0 else "-"
def _radar_opt(name, vals, color, area):
    """分标的独立雷达 option 工厂 —— v2.5.2 起每个标的一个坐标系, 不再叠加多标的一张图。"""
    return {"backgroundColor":"transparent","tooltip":{},"legend":{"data":[name],"textStyle":{"color":"#a8b8d0"}},
        "radar":{"radius":"55%","center":["50%","54%"],
                 "indicator":[{"name":"趋势强度|Hurst|","max":1},{"name":"偏离|Z|","max":3},{"name":"年化Sharpe","max":3},
                              {"name":"Sortino","max":4},{"name":"|偏度|","max":2},{"name":"日VaR95%","max":3}],
                 "axisName":{"color":"#a8b8d0","fontSize":11},"splitLine":{"lineStyle":{"color":"rgba(127,169,255,.15)"}},
                 "splitArea":{"areaStyle":{"color":["rgba(127,169,255,.02)","rgba(127,169,255,.05)"]}},"axisLine":{"lineStyle":{"color":"rgba(127,169,255,.2)"}}},
        "series":[{"type":"radar","data":[{"value":[round(v,2) for v in vals],"name":name,"areaStyle":{"color":area},"lineStyle":{"color":color}}]}]}
radar_aj_opt = _radar_opt("AUDJPY", [h_abs, z_abs, sh_abs, so_abs, sk_abs, var95], "#4a7fff", "rgba(74,127,255,.25)")
radar_krw_opt = _radar_opt("USDKRW", [h_k, z_k, sh_k, so_k, sk_k, var95_k], "#f1c40f", "rgba(240,196,15,.25)")

# ===================== 跨市场柱图 =====================
cross = {"DXY":2.5,"US10Y":4.0,"TIPS实际利率":2.0,"黄金(XAU)":2.0,"白银":2.5,"WTI原油":-1.5,"AUDJPY":-0.5,"EURUSD":0.5,"USDJPY":-0.5,"VIX":2.5,"韩元(USDKRW)":2.0}
cross_opt = {"backgroundColor":"transparent","tooltip":{"trigger":"axis"},
    "grid":{"left":90,"right":30,"top":20,"bottom":40},
    "xAxis":{"type":"value","axisLabel":{"color":"#a8b8d0"},"splitLine":{"lineStyle":{"color":"rgba(127,169,255,.1)"}}},
    "yAxis":{"type":"category","data":list(cross.keys()),"axisLabel":{"color":"#7fa9ff"}},
    "series":[{"type":"bar","data":[{"value":v,"itemStyle":{"color":"#e74c3c" if v < 0 else "#2ecc71"}} for v in cross.values()],
              "label":{"show":True,"position":"right","color":"#fff","formatter":"{c}"}}]}

# ===================== 权益曲线 (基于AUDJPY持仓·0.01手) =====================
eq_dates = ["08-13","08-14","08-15","08-16","08-17","08-18","08-19","08-20","08-21","08-22","08-23","08-24","08-25","08-26","08-27","08-28","08-29","08-30","08-31","09-01","09-02","09-03","09-04","09-05","09-06","09-07","09-08","09-09","09-10","09-11","09-12","09-13","09-14","09-15","09-16"]
eq_vals  = [528,529,528,530,531,530,532,533,534,535,534,536,537,538,539,540,539,541,542,
            542,543,552,562,572,581,589,596,603,610,618,635,642.4,630,629.31,628.40]
equity_opt = {"backgroundColor":"transparent","tooltip":{"trigger":"axis"},
    "grid":{"left":60,"right":30,"top":30,"bottom":40},
    "xAxis":{"type":"category","data":eq_dates,"axisLabel":{"color":"#7fa9ff","fontSize":10},"axisLine":{"lineStyle":{"color":"#3a4a6a"}}},
    "yAxis":{"scale":True,"min":510,"axisLabel":{"color":"#a8b8d0","formatter":"${value}"},"splitLine":{"lineStyle":{"color":"rgba(127,169,255,.1)"}}},
    "series":[{"type":"line","data":eq_vals,"smooth":True,"symbol":"circle","symbolSize":5,
               "lineStyle":{"color":"#2ecc71","width":2},"itemStyle":{"color":"#2ecc71"},
               "areaStyle":{"color":{"type":"linear","x":0,"y":0,"x2":0,"y2":1,"colorStops":[{"offset":0,"color":"rgba(46,204,113,.35)"},{"offset":1,"color":"rgba(46,204,113,.02)"}]}},
               "markLine":{"symbol":"none","data":[{"name":"入金","yAxis":522,"lineStyle":{"color":"#f1c40f","type":"dashed"},"label":{"formatter":"入金 $522","color":"#f1c40f"}}]}}]}

# ===================== 动态止损对比柱图 =====================
stop_names = [STOPS["atr"]["name"], STOPS["struct"]["name"], STOPS["trail"]["name"]]
stop_risk = [STOPS["atr"]["risk"], STOPS["struct"]["risk"], STOPS["trail"]["risk"]]
stop_sweep = [STOPS["atr"]["sweep"], STOPS["struct"]["sweep"], STOPS["trail"]["sweep"]]
stop_keep = [STOPS["atr"]["keep"], STOPS["struct"]["keep"], STOPS["trail"]["keep"]]
stop_opt = {"backgroundColor":"transparent","tooltip":{"trigger":"axis"},
    "legend":{"data":["风险($)","被扫概率%","保住利润(1-5分)"],"textStyle":{"color":"#a8b8d0"}},
    "grid":{"left":50,"right":30,"top":40,"bottom":40},
    "xAxis":{"type":"category","data":stop_names,"axisLabel":{"color":"#7fa9ff"},"axisLine":{"lineStyle":{"color":"#3a4a6a"}}},
    "yAxis":{"type":"value","axisLabel":{"color":"#a8b8d0"},"splitLine":{"lineStyle":{"color":"rgba(127,169,255,.1)"}}},
    "series":[{"name":"风险($)","type":"bar","data":stop_risk,"itemStyle":{"color":"#e74c3c"},"label":{"show":True,"position":"top","color":"#fff","formatter":"${c}"}},
              {"name":"被扫概率%","type":"bar","data":stop_sweep,"itemStyle":{"color":"#f1c40f"},"label":{"show":True,"position":"top","color":"#fff","formatter":"{c}%"}},
              {"name":"保住利润(1-5分)","type":"bar","data":stop_keep,"itemStyle":{"color":"#2ecc71"},"label":{"show":True,"position":"top","color":"#fff","formatter":"{c}分"}}]}

# ===================== R 乘数资金曲线 =====================
r_labels = ["#"+str(i+1) for i in range(len(R_CUM))]
rcurve_opt = {"backgroundColor":"transparent","tooltip":{"trigger":"axis"},
    "grid":{"left":50,"right":30,"top":30,"bottom":40},
    "xAxis":{"type":"category","data":r_labels,"axisLabel":{"color":"#7fa9ff","fontSize":10},"axisLine":{"lineStyle":{"color":"#3a4a6a"}}},
    "yAxis":{"type":"value","axisLabel":{"color":"#a8b8d0","formatter":"{value}R"},"splitLine":{"lineStyle":{"color":"rgba(127,169,255,.1)"}}},
    "series":[{"type":"line","data":R_CUM,"smooth":True,"symbol":"circle","symbolSize":6,
               "lineStyle":{"color":"#4a7fff","width":2},"itemStyle":{"color":"#4a7fff"},
               "areaStyle":{"color":{"type":"linear","x":0,"y":0,"x2":0,"y2":1,"colorStops":[{"offset":0,"color":"rgba(74,127,255,.35)"},{"offset":1,"color":"rgba(74,127,255,.02)"}]}}}]}

# ===================== CSS =====================
css = open(SKILL_CSS, encoding="utf-8").read()
style_block = css[css.find("<style>"):css.find("</style>")+8]

def score_color(v): return "#2ecc71" if v >= 75 else ("#f1c40f" if v >= 60 else "#e74c3c")
def scard(sym, d):
    total = round(d["macro"]*0.25+d["tech"]*0.30+d["quant"]*0.25+d["sent"]*0.20)
    col = score_color(total)
    return ('<div class="score-card"><div class="score-head"><span class="score-name">'+sym+'</span><span class="score-total" style="color:'+col+'">'+str(total)+'</span></div>'
            '<div class="score-bar-bg"><div class="score-bar" style="width:'+str(total)+'%;background:'+col+'"></div></div>'
            '<div class="score-dims"><div class="score-dim"><div class="score-dim-label">宏观25%</div><div class="score-dim-val">'+str(d["macro"])+'</div></div>'
            '<div class="score-dim"><div class="score-dim-label">技术30%</div><div class="score-dim-val">'+str(d["tech"])+'</div></div>'
            '<div class="score-dim"><div class="score-dim-label">量化25%</div><div class="score-dim-val">'+str(d["quant"])+'</div></div>'
            '<div class="score-dim"><div class="score-dim-label">情绪20%</div><div class="score-dim-val">'+str(d["sent"])+'</div></div></div>'
            '<div class="score-action"><span>判定: <b style="color:'+col+'">'+d["verdict"]+'</b></span></div>'
            '<div class="score-action"><span style="color:#8a9bc0">'+d["reason"]+'</span></div></div>')

a_atr = round(atr(klines["AUDJPY"]), 3)

# 关键位表 (10标的, 每标一个)
keylevels = [
    ("XAUUSD","4275 / 4341","支撑/阻力","今日低点4275(回踩不破则强势); 4341日内高(历史高位区, 突破打开空间)"),
    ("XAGUSD","63.4 / 64.9","支撑/阻力","63.4日内低; 64.9日内高(逼近前高, 突破看65.5)"),
    ("DXY","99.6","中枢","合成99.55; 今夜FOMC定向, 破100看103"),
    ("EURUSD","1.1527 / 1.1617","支撑/阻力","区间下沿1.1527(今日低); 1.1617区间上沿, FOMC双向"),
    ("GBPUSD","1.3466 / 1.3520","支撑/阻力","1.3466日内低; 1.3520上方阻力"),
    ("USDJPY","154.2 / 155.5","中枢/阻力","154.2当前; 155.5日内高(BoJ加息后回落)"),
    ("USOIL","99.26 / 100.83","支撑/阻力","99.26日内低; 100.83日内高(百元关口拉锯)"),
    ("AUDUSD","0.712 / 0.722","支撑/阻力","0.712日内低; 0.722区间上沿(突破需美元走弱)"),
    ("AUDJPY","109.781 / 110.81 / 111.30","支撑/阻力","109.781 TP(原挂单目标); 110.81 4H摆动高点(短线阻力); 111.30 保护性SL(4H高点+1.5×4H ATR上方)"),
    ("USDKRW","1359.95 / 1365.07 / 1372.98","支撑/阻力","1359.95日内低; 1365.07回归通道上轨(拉锯位); 1372.98日内高(52周高区)"),
]
kl_rows = ""
for v,kl,tp,act in keylevels:
    cls = "green" if tp=="支撑" else ("red" if tp=="阻力" else "")
    kl_rows += "<tr><td class='white'>"+v+"</td><td>"+kl+"</td><td class='"+cls+"'>"+tp+"</td><td>"+act+"</td></tr>"

# 快照扩展数据 (10标的)
SNAP_EXTRA = {
    "XAUUSD": {"struct": "2月见顶后修复反弹, 日内 +1.04%", "mtf": "D1反弹/H1偏多, W仍压制", "plan": "不建议建仓（事件窗口+拥挤）"},
    "XAGUSD": {"struct": "跟随黄金反弹 +1.81% 强于金", "mtf": "反弹·强于金", "plan": "不建议（波动极端）"},
    "DXY":    {"struct": "Fed 加息92% + 10Y 4.97% 高位支撑", "mtf": "偏强·待FOMC", "plan": "观望（今夜定向）"},
    "EURUSD": {"struct": "D1 区间 1.153-1.162 窄幅整理", "mtf": "中性", "plan": "观望"},
    "GBPUSD": {"struct": "D1 上升结构 + 英CPI 3.1% 超预期支撑", "mtf": "中性偏多", "plan": "观望"},
    "USDJPY": {"struct": "154.92 高位震荡 -0.06%", "mtf": "短线中性", "plan": "不交易（BoJ 09-18 + 干预风险）"},
    "USOIL":  {"struct": "回落 -1.31% 至 99.61; 投机97%分位拥挤", "mtf": "事件驱动", "plan": "不建议（今晚EIA + 拥挤）"},
    "AUDJPY": {"struct": "日线空头(EMA60 压制) + 4H 摆动高点110.81下方整理 → 分歧; 剩余持仓 +401.9 pips", "mtf": "长空短多·分歧", "plan": "确认保护 SL 111.30 + FOMC 前了结（见十五节）"},
    "AUDUSD": {"struct": "区间0.706-0.722震荡, 0.7136 中位", "mtf": "中性", "plan": "观望（今夜FOMC双向）"},
    "USDKRW": {"struct": "4H 多头排列 + 站上回归通道上轨 1365.07; 日内冲高 1372.98 回落 1364.38", "mtf": "偏多(USDKRW·韩元走弱)", "plan": "观望（波动放大·不追多）"},
}
SNAP_NOKL = {
    "XAGUSD": {"pct": "+1.81", "rng": "63.426 ~ 64.883"},
    "USOIL":  {"pct": "-1.31", "rng": "99.258 ~ 100.830"},
    "DXY":    {"pct": "—", "rng": "—"},
}
def snap_metrics(s):
    if s in klines and len(klines[s]) >= 2:
        rows = klines[s]; last, prev = rows[-1], rows[-2]
        px = last[4]
        pct = (last[4]-prev[4])/prev[4]*100
        rng = str(round(last[3], 5)) + " ~ " + str(round(last[2], 5))
        return round(px, 5), (("+%.2f" % pct) if pct >= 0 else ("%.2f" % pct)), rng
    q = QUOTES[s][0]
    return q, SNAP_NOKL.get(s, {}).get("pct", "—"), SNAP_NOKL.get(s, {}).get("rng", "—")

SNAP_LIST = ["XAUUSD","XAGUSD","DXY","EURUSD","GBPUSD","USDJPY","USOIL","AUDUSD","AUDJPY","USDKRW"]
snap_rows = ""
for s in SNAP_LIST:
    px, pct, rng = snap_metrics(s)
    ex = SNAP_EXTRA[s]
    pctcls = "green" if pct.startswith("+") else ("red" if pct.startswith("-") else "")
    mtfcls = "red" if "空" in ex["mtf"] else ("green" if ("多" in ex["mtf"] or "偏强" in ex["mtf"]) else "yellow")
    plancls = "red" if "不建议" in ex["plan"] else ("yellow" if ("观望" in ex["plan"] or "不交易" in ex["plan"]) else "green")
    hl = " style='background:rgba(74,127,255,.12)'" if s == "AUDJPY" else (" style='background:rgba(240,196,15,.08)'" if s == "USDKRW" else "")
    snap_rows += ("<tr" + hl + "><td class='white'>" + s + "</td><td>" + str(px) + "</td>"
                  "<td class='" + pctcls + "'>" + pct + "</td><td>" + rng + "</td>"
                  "<td>" + ex["struct"] + "</td><td class='" + mtfcls + "'>" + ex["mtf"] + "</td>"
                  "<td class='" + plancls + "'>" + ex["plan"] + "</td></tr>")
DAY_THEME = ("🔥 日内主轴: <b>FOMC 今夜 09-17 02:00 决议（CME 定价加息 92%）+ 今晚美国零售销售 20:30(★4) + EIA 库存 22:30(★4)</b>, 超级央行周进入 24h 决战窗口; 10Y 美债 4.97% 高位（前日盘中峰值 5.025%）, 实际利率 2.60% 压制贵金属; 黄金日内反弹 +1.04% 至 4338 修复昨日跌幅, 原油回落 -1.31%。<b class='yellow'>持仓 AUDJPY 剩余 0.01 手空单浮盈 +401.9 pips, FOMC 已进入 24h 清仓窗口 → 持最小仓 + 确认保护性 SL 111.30 + 事件前未触 TP 则主动了结。</b>"
             " 韩元(USDKRW) 4H 多头排列但日内冲高 1372.98 回落, ATR 放大, 观望不追。")

macro_events = """
【XAUUSD】①Fed 加息 92% 定价（FOMC 今夜02:00）+ 10Y 4.97% 高位 / 实际利率(DFII10) 2.60% → 持金成本高企; 但日内 +1.04% 反弹至 4338 显示买盘韧性; ②CFTC 投机净多 89%分位 → 拥挤, 事件窗口不追。
【XAGUSD】①跟随黄金反弹 +1.81% 强于金, 金银比修复; ②工业属性受全球需求下修拖累, 波动极端。
【DXY】①Fed 加息 92% + 长端 4.97% 高位提供美元支撑, 合成指数 99.55; ②今夜 FOMC 定向, 破 100 打开空间。
【EURUSD】①ECB 紧缩(2.25%)支撑; ②美债收益率上行压制, 今夜 FOMC 为双向风险。
【GBPUSD】①英 8月 CPI 年率 3.1% 超预期(前 2.9%, 今日14:00公布) → BoE 09-17 维持 3.75% 概率上升, 英镑获支撑; ②与 FOMC 相邻 48h, 波动放大。
【USDJPY】①BoJ 09-18 10:00 决议(共识加息 25bp → 1.25%), 日债 10Y 3.030% 高位; ②美日利差 +2.625pp 支撑 154.92, 但干预风险随时可启。
【USOIL】①中东地缘 + 沙特减产托底 vs 需求下修, 日内 -1.31% 回落 99.61; ②投机拥挤 97%分位, 今晚 EIA 库存(★4) 双向。
【AUDJPY】①AU 4.35% 对 JP 1.00% 套息 3.35%, BoJ 加息后收窄至 3.10%, 套息平仓主浪已于 110.20 兑现; ②日线 EMA60 空头压制 vs 4H 摆动高点 110.81 下方整理 → 长空短多分歧, 残余段只管理不加仓。
【AUDUSD】①RBA 4.35% 高位 + 中国需求下修, 澳元商品属性承压; ②区间 0.706-0.722 无方向, 今夜 FOMC 双向。
【USDKRW】①BoK 08-27 加息至 3.00% 但 09-15 纪要显内部分歧 → 收紧步伐或放缓; ②Fed 加息 92% → 美韩利差 0.625pp 走阔至 0.875pp, <b class='red'>韩元结构性承压</b>; ③日内冲高 1372.98 回落, ATR(4H) 放大至 6.47 → 高波动追多赔率不合格。
"""
print("PART1 ok | equity:", ACC_EQUITY, "| AUDJPY pnl:", POS_PNL, "| ATR AUDJPY:", a_atr)

# ===================== v2.2 新增数据块 =====================
OTHER8 = [
    ("XAUUSD","不建议建仓","① Fed 加息92%(今夜FOMC) + 10Y 4.97%, 实际利率2.60%高位; ② 日VaR95 高于本账户1%上限 → 量化一票否决; ③ 日内+1.04%反弹属事件前修复, 拥挤89%分位不追"),
    ("USDJPY","不交易","① 美日利差+2.625pp支撑, 但 BoJ 09-18 加息25bp预期 + 干预风险双向; ② 今夜FOMC+明晨BoJ双事件, 落地后重估"),
    ("USOIL","不建议建仓","① 回落-1.31%至99.61, 投机拥挤97%分位; ② 今晚EIA库存(★4), 事件驱动无合格 R:R"),
    ("XAGUSD","不建议建仓","① 反弹+1.81%强于金但波动极端(日VaR更高于黄金); ② 双属性撕裂无方向"),
    ("EURUSD","观望","① D1上升结构与美债收益率上行冲突, 矛盾单不做; ② 今夜FOMC为双向风险"),
    ("GBPUSD","观望","① 英CPI 3.1%超预期支撑, 但 BoE 09-17 与 FOMC 相邻, 波动放大; ② 事件前静默"),
    ("DXY","观望","① 99.55 偏强, 方向由今夜 Fed 决议与点阵图决定; ② 非直接可交易, 仅作参照"),
    ("AUDUSD","观望","① 区间0.706-0.722无方向, 今夜FOMC双向+商品属性承压; ② 等突破0.722/破0.706再评估"),
    ("USDKRW","观望·高位不追多","① 4H 多头排列 + 站上通道上轨1365.07, 趋势强; ② 日内冲高1372.98回落 + ATR(4H)放大至6.47, 追多赔率不合格; ③ 等回踩1352或事件落地后重估"),
]
RECOMMEND5 = [
    "确认/补挂保护 SL 111.30（4H摆动高点110.81 + 1.5×4H ATR上方）→ 剩余风险 $"+str(RISK_REST)+"（"+str(RISK_REST_PCT)+"% 账户, 合规）",
    "109.781（TP 原挂单）保留不动 → 事件前触发即全平",
    "FOMC（今夜 09-17 02:00）前 2h（09-17 00:00）仍未触 TP → 主动市价了结锁定剩余浮盈",
    "今夜零售 20:30 与 FOMC 决议期间不新增任何仓位, 仅管理现有持仓",
    "若跳空越过 111.30, 市价单立即离场不等待",
]
DISCIPLINE6 = [
    ("仓位纪律", ["单笔风险 ≤ 1%（0.5% 优先）","总组合风险 ≤ 5%","凯利半仓原则: 理论最优仓位 × 0.5","不加仓逆势单"]),
    ("入场纪律", ["评分 ≥ 75 分才考虑","止损前置: 结构外 1.5×ATR","RR ≥ 1.5 才入场","事件前 4h 不开新仓"]),
    ("持仓纪律", ["浮盈 ≥ 2R: 平 50%","移动 SL 只向盈利方向","议息前 24h 清仓或最小仓","绝不摊平"]),
    ("离场纪律", ["分批止盈: 2R 平 50% → 3R 再平 30% → 剩余跟踪止损","SL 触发不犹豫","事件后 15 分钟不决策","结构破位 = 全平, 不与市场争辩"]),
    ("复盘纪律", ["每笔必写日志: 信号/情绪/结果/教训","每周统计胜率: 更新凯利参数","每月回顾系统: 信号是否仍然有效","连续亏损 3 次: 停 24h"]),
    ("心理纪律", ["不贪最后一段: 带走利润才是目标","不报复市场: 亏了就停, 不追","只应对, 不预测: 预案比预判重要","错过即纪律: 不属于你的行情不心疼"]),
]

# ===================== ECharts 加载策略: 优先本地内嵌 =====================
_SKILL_ASSETS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))
_ECHARTS_CDN = '<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>'
_ECHARTS_TAG = _ECHARTS_CDN
for _ep in (os.path.join(OUT, "echarts.min.js"), os.path.join(_SKILL_ASSETS, "echarts.min.js")):
    if os.path.exists(_ep):
        with open(_ep, encoding="utf-8") as _ef:
            _esrc = _ef.read()
        if _esrc and "</script>" not in _esrc:
            _ECHARTS_TAG = "<script>/* ECharts v5 inlined (offline-safe) */\n" + _esrc + "\n</script>"
            print("ECharts: inlined from", _ep)
            break
if _ECHARTS_TAG is _ECHARTS_CDN:
    print("ECharts: CDN fallback (local echarts.min.js not found)")

# ===================== HTML 头部 =====================
html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>决策增强版 v2.5.6 · 今日行情分析 · 10标的 · kingforex-skill</title>
""" + _ECHARTS_TAG + """
""" + style_block + """</head><body><div class="container">
<div class="header">
<h1>📊 今日行情分析 · 决策增强版 v2.5.6</h1>
<div class="meta">基准时间: <b>""" + NOW + """</b> ｜ 标的: 金/银/美元/欧元/英镑/日元/WTI原油 + 利差最大货币对(AUDJPY) + 韩元(USDKRW)<br>
⏱ 数据截至: <b>行情报价 金十实时 2026-09-16 15:45 ｜ 日K Twelve Data 末根 2026-09-16 ｜ FRED 利率观测 09-14/15 ｜ 财经日历金十 09-16 15:45 ｜ CFTC COT 09-01/08-25 当周</b>（各节首行附分项截至时间, 全量溯源见十八节）<br>
结构: 决策总览 → 交易计划 → 分析论证(快照/评分/宏观/数据/跨市场/K线/量化) → 决策工具(情景/凯利/相关性/风险/止损) → 综合判定 → 日志/回测 → 校验 → 纪律<br>
<span class="badge badge-red">🔴 重大事件: FOMC 今夜 09-17 02:00（CME 定价加息 92%）+ BoE 09-17 19:00 + BoJ 09-18 10:00 —— 42h 三央行</span>
<span class="badge badge-yellow">BoJ 现 1.00%, 共识加息至 1.25%</span>
<span class="badge badge-red">10Y 美债 4.97% / 30Y 5.34% 高位 · FOMC 今夜定向</span>
<span class="badge badge-purple">本账户 AUDJPY 已部分平仓 +$""" + str(POS["part_pnl"]) + """ · 剩余 0.01 手浮盈 $""" + str(ACC["floating"]) + """</span>
</div></div>
"""

# ===================== ① 今日决策总览 =====================
sec01 = """<div class="section"><div class="section-title">🎯 一、今日决策总览</div>
<div class="grid grid-4">
<div class="card"><div class="card-title">💼 账户状态</div>
<div class="card-value" style="color:#2ecc71">$""" + str(ACC["equity"]) + """</div>
<div class="card-sub">净值 · 已实现 +$""" + str(POS["part_pnl"]) + """ · 浮盈 +$""" + str(ACC["floating"]) + """</div>
<div class="risk-meter" style="margin-top:12px"><div class="risk-meter-fill" data-val="0.80%" style="width:16%;background:linear-gradient(90deg,#2ecc71,#f1c40f)"></div></div>
<div class="card-sub">当前持仓风险 <b class="yellow">""" + str(POS["risk_rest_pct"]) + """%</b>（$""" + str(POS["risk_rest"]) + """） / 总风险上限 5%</div></div>
<div class="card"><div class="card-title">📊 今日信号质量</div>
<div class="card-value" style="color:#f1c40f">B+</div>
<div class="card-sub">综合评分 · 10标的加权</div>
<div class="card-sub" style="margin-top:10px">持仓管理标的: <b class="green">1个</b> (AUDJPY)<br>观望/关注标的: <b class="yellow">9个</b>（含韩元 USDKRW 专项）</div></div>
<div class="card"><div class="card-title">🎯 仓位状态</div>
<div class="card-value" style="color:#3498db">""" + str(POS["lots_now"]) + """ 手</div>
<div class="card-sub">AUDJPY SELL 剩余 · 已平 """ + str(POS["part_lot"]) + """ 手 @ """ + str(POS["part_px"]) + """</div>
<div class="card-sub" style="margin-top:10px">原 0.02 手 → 已实现 <b class="green">+$""" + str(POS["part_pnl"]) + """</b><br>剩余 = <b class="yellow">最小手</b> · 占风险 """ + str(POS["risk_rest_pct"]) + """% ≤1% ✓</div></div>
<div class="card"><div class="card-title">⚠️ 今日最大风险</div>
<div class="card-value" style="color:#e74c3c">Fed + BoE + BoJ ★★★★★</div>
<div class="card-sub">09-17 02:00 / 19:00 · 09-18 10:00 北京 · 48h 三央行</div>
<div class="card-sub" style="margin-top:10px">Fed 定价 <b class="red">加息 92%</b> · 预期波动 <b class="yellow">±150-200 pips</b><br>纪律: <b class="red">补挂保护 SL 111.30 + 事件前了结</b></div></div>
</div></div>"""

# ===================== ② 今日交易计划 =====================
sec02 = """<div class="section"><div class="section-title">📋 二、今日交易计划（建仓 / 持仓判定）</div>
<div class="verdict-warn"><b>【建仓判定：今日不适宜建仓 —— 不建仓】</b><br>
理由（四维一致否决）: ① <b>宏观</b>: Fed 09-17 02:00 决议（CME 定价<b class="red">加息 92%</b>）+ BoE 09-17 19:00 + BoJ 09-18 10:00, <b class="red">48h 内三央行</b>, 且 10Y 美债 4.97% 高位（前日峰值 5.025%）, 今夜 FOMC 事件窗口双向跳空风险极高; ② <b>评分</b>: 10 标的综合评分均 &lt; 75 分（最高 AUDJPY 65.30）, 无一达建仓线; ③ <b>凯利</b>: 新开仓理论手数 0.0052 手 <b>&lt; 最小手 0.01 手</b> → 引擎判定「不可交易」; ④ <b>赔率</b>: AUDJPY 剩余 R:R 1.04 勉强及格, USDKRW 高位高波动, 追多赔率同样不合格。<b>空仓即结论, 错过即纪律。</b></div>
<div class="sub-title">2.1 持仓计划（现有持仓 · 已部分平仓 · 按图1模板）</div>
<table class="journal-table">
<tr><th style="width:18%">项目</th><th>内容</th></tr>
<tr><td>交易标的</td><td class='white'>AUDJPY</td></tr>
<tr><td>方向 / 手数</td><td><span class='red'>SELL """ + str(POS["lots_open"]) + """ 手</span> → 2026-09-15 于 <b class='yellow'>110.20 平仓 """ + str(POS["part_lot"]) + """ 手</b>（已实现 +$""" + str(POS["part_pnl"]) + """）→ <b class='yellow'>剩余 """ + str(POS["lots_now"]) + """ 手持仓中</b></td></tr>
<tr><td>入场价 / 时间</td><td>114.573 / 2026-09-02 (凌晨)</td></tr>
<tr><td>止损 / 止盈</td><td>原 SL 113.284（获利区·已实质失效）→ <b class='yellow'>本次补挂保护性 SL """ + str(POS["sl_new"]) + """</b> / TP """ + str(POS["tp"]) + """（保留）</td></tr>
<tr><td>入场核心理由 (3条)</td><td>① W/D/4H 三周期共振空头排列 (技术面)<br>② BoJ 加息预期 vs 澳洲按兵不动 (宏观方向)<br>③ Hurst """ + str(round(h_abs,2)) + """ 强趋势 + OTC 经历转折 (量化/情绪面)</td></tr>
<tr><td>入场时信心指数</td><td><b class='green'>8/10</b> — 三周期 + 宏观双确认</td></tr>
<tr><td>入场时情绪状态</td><td>冷静 / 按计划执行 ✓</td></tr>
<tr><td>已实现 / 当前浮盈</td><td class='green'>已实现 +""" + str(POS["part_pips"]) + """ pips = +$""" + str(POS["part_pnl"]) + """（= +""" + str(round(POS["part_pips"] / R_UNIT_PIPS, 2)) + """R）<br>剩余浮盈 +""" + str(round(_pips,1)) + """ pips = +$""" + str(ACC["floating"]) + """（占净值 +""" + str(round(ACC["floating"] / ACC["equity"] * 100, 2)) + """%）</td></tr>
<tr><td>当前状态</td><td><b class='yellow'>部分平仓 · 剩余 0.01 手持仓</b> — 剩余 R:R 1.04 勉强及格, 只管理不加仓</td></tr>
<tr><td>离场计划 (明确)</td><td>① <b>确认/补挂保护性 SL """ + str(POS["sl_new"]) + """</b>（74.6 pips · $""" + str(POS["risk_rest"]) + """ · """ + str(POS["risk_rest_pct"]) + """%）<br>② 保留 TP 109.781 挂单不动<br>③ 09-17 00:00（FOMC 前 2h）未触 TP → <b>主动市价了结</b>锁利<br>④ 1H 收盘站上 111.00（短线多头确认）→ 提前了结, 不与结构争辩</td></tr>
<tr><td>可能出错的地方</td><td>① Fed 加息 92% 落地致美元跳升 → <span class='green'>保护 SL 111.30 已覆盖</span><br>② BoJ 意外不加息致日元回落 → <span class='yellow'>按计划了结, 观望 24h 重估</span><br>③ 三央行密集期流动性枯竭跳空 → <span class='yellow'>接受滑点, 不追不反手</span><br>④ 无保护裸持过事件 → <span class='red'>已否决（情景 C）</span></td></tr>
</table></div>"""

# ===================== ③ 分析标的快照 =====================
sec03 = """<div class="section"><div class="section-title">📌 三、分析标的快照（10 标的 · 现价 / 日内% / 日内区间 / 趋势结构 / MTF方向 / 计划判定）</div>
<div class="card-sub" style="margin:2px 0 10px;color:#8a9bc0">⏱ 数据截至: 现价 = 日K最后收盘（Twelve Data, 末根 2026-09-16, 取数 15:45 GMT+8）· XAGUSD/USOIL = 金十实时 09-16 15:45 · DXY = Frankfurter ECB 参考汇率合成（09-15）</div>
<table><tr><th>标的</th><th>现价</th><th>日内%</th><th>日内区间</th><th>趋势/结构</th><th>MTF 方向</th><th>计划判定</th></tr>""" + snap_rows + """</table>
<div class="card-sub" style="margin-top:10px;line-height:1.8">""" + DAY_THEME + """</div></div>"""

# ===================== ④ 10标的综合评分卡 =====================
sec04 = """<div class="section"><div class="section-title">🃏 四、10标的综合评分卡（宏观25%·技术30%·量化25%·情绪20%，≥75可建仓 · 4×3排列）</div>
<div class="card-sub" style="margin:2px 0 10px;color:#8a9bc0">⏱ 评分数据截至: 行情 09-16 15:45（金十/Twelve Data）· 利率 FRED 观测 09-14/15 · CFTC COT 09-01/08-25 当周 · 财经日历金十 09-16 15:45</div><div class="grid grid-4">"""
for s in SNAP_LIST:
    sec04 += scard(s, SCORES[s])
sec04 += "</div>"
# ---- v2.5.6 授权调准④: 评分图表（四维分组柱 + 综合总分折线 + 75分建仓虚线; 数值标注与四·补子项明细同源同位数 2 位小数） ----
_score_syms = SNAP_LIST[:]
_score_tot_num = [round(SCORES[s]["macro"]*0.25 + SCORES[s]["tech"]*0.30 + SCORES[s]["quant"]*0.25 + SCORES[s]["sent"]*0.20, 2) for s in _score_syms]
_score_tot = ["%.2f" % v for v in _score_tot_num]          # 折线数值(2位小数, 与四·补明细总分一致)
_score_barlbl = {"show": True, "position": "inside", "rotate": 0, "color": "#fff", "fontSize": 8, "fontWeight": "600", "distance": 0}
# 柱体加宽配参: 让 2 位小数(如 66.00)横向标在柱内正中且不溢出柱宽 / 不与相邻柱标签重叠
_score_baropt = {"barCategoryGap": "8%", "barGap": "5%"}
score_opt = {
    "backgroundColor": "transparent",
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    "legend": {"data": ["宏观25%", "技术30%", "量化25%", "情绪20%", "综合总分"], "textStyle": {"color": "#a8b8d0"}},
    "grid": {"left": 50, "right": 30, "top": 55, "bottom": 40},
    "xAxis": {"type": "category", "data": _score_syms, "axisLabel": {"color": "#a8b8d0"}},
    "yAxis": {"type": "value", "max": 100, "axisLabel": {"color": "#a8b8d0"}, "splitLine": {"lineStyle": {"color": "rgba(127,169,255,.1)"}}},
    "series": [
        {"name": "宏观25%", "type": "bar", "data": ["%.2f" % SCORES[s]["macro"] for s in _score_syms], "itemStyle": {"color": "#4a7fff"}, "label": _score_barlbl, **_score_baropt},
        {"name": "技术30%", "type": "bar", "data": ["%.2f" % SCORES[s]["tech"] for s in _score_syms], "itemStyle": {"color": "#2ecc71"}, "label": _score_barlbl, **_score_baropt},
        {"name": "量化25%", "type": "bar", "data": ["%.2f" % SCORES[s]["quant"] for s in _score_syms], "itemStyle": {"color": "#f1c40f"}, "label": _score_barlbl, **_score_baropt},
        {"name": "情绪20%", "type": "bar", "data": ["%.2f" % SCORES[s]["sent"] for s in _score_syms], "itemStyle": {"color": "#e67e22"}, "label": _score_barlbl, **_score_baropt},
        {"name": "综合总分", "type": "line", "data": _score_tot, "smooth": True, "symbol": "circle", "symbolSize": 7,
         "lineStyle": {"color": "#ff5c7a", "width": 2.5}, "itemStyle": {"color": "#ff5c7a"},
         "label": {"show": True, "position": "top", "color": "#ff5c7a", "fontSize": 10},
         "markLine": {"silent": True, "symbol": "none", "lineStyle": {"color": "#2ecc71", "type": "dashed", "width": 1.5},
                      "data": [{"yAxis": 75, "label": {"formatter": "75分建仓线", "color": "#2ecc71"}}]}},
    ]}
sec04 += ('<div class="chart-box"><div class="chart-title">🃏 10标的综合评分图表（分组柱 = 四维得分·柱内标注数值 · 折线 = 综合总分 · 绿色虚线 = 75分建仓线 · 数值均为2位小数与四·补子项明细一致 · 数据截至 2026-09-16 15:45）</div>'
          '<div id="scorechart" class="chart"></div></div>'
          '<div class="card-sub" style="margin-top:6px">评分卡（上）与评分图表（下）数据同源（SCORES 四维加权）: 最高 AUDJPY ' + ("%.2f" % max(_score_tot_num)) + ' 分 &lt; 75 → 10 标的全部不满足建仓线, 与第二节「不建仓」判定一致。</div></div>')

# ===================== ⑤ 宏观金融面解读 =====================
CB_POLICY = [
    ("美联储 Fed", "3.625%", "FOMC 今夜 09-17 02:00(北京) 决议; 8月通胀高于目标 + 10Y 高位 4.97% → CME 定价 <b>加息25bp 概率 92%</b> → 3.875%(附 SEP 点阵图); 已进入议息前24h窗口", "再紧缩", "red", "今夜加息落地 + 点阵图定美元方向, 利空风险资产与商品货币, 压制金价与人民币/韩元等亚洲货币"),
    ("欧洲央行 ECB", "2.25%", "已恢复紧缩周期(市场完全计价2027年底前四次25bp加息); 管委卡兹米尔称\"通胀风险明显偏向上行\"", "紧缩", "red", "欧元有支撑, 但被美债收益率上行压制"),
    ("日本央行 BoJ", "1.00%", "09-18 10:00(北京) 决议, 广泛预期加息25bp → <b>1.25%</b>(当前周期最快步伐); 日债10Y 3.030%(1996/9来最高)、5Y 2.315%(历史新高)", "加速正常化", "yellow", "BoJ加息 = JPY升值 = 套息平仓核心 = 日元交叉盘(AUDJPY)下行核心驱动, 但已被前瞻定价"),
    ("英央行 BoE", "3.75%", "09-17 19:00(北京) 议息, 料维持3.75%; <b>英8月CPI年率3.1%超预期(今14:00公布)</b>强化按兵预期", "高位观望", "yellow", "利差支撑英镑, 但同日双事件(BoE+FOMC相邻)波动放大"),
    ("澳联储 RBA", "4.35%", "G10 高息之一, 09-28~29 议息料按兵不动", "高位维持", "yellow", "AUD 正 carry 缓冲, 但澳日利差因 BoJ 加息收窄至3.10% → AUDJPY 套息吸引力下降"),
    ("韩国央行 BoK", "3.00%", "<b>2026-08-27 加息25bp至3.00%</b>(连续第二次); <b>09-15 公布会议纪要显示内部分歧加大</b> → 收紧步伐或放缓", "紧缩·分歧", "yellow", "BoK加息支撑韩元, 但纪要偏鸽 + Fed 加息92% → 美韩利差由0.625pp走阔至<b>0.875pp</b>, 韩元结构性承压"),
]
CARRY2 = [
    ("US 2s10s", "+0.32pp", "陡峭化（2Y 4.65% → 10Y 4.97%）", "再通胀 + 政府融资需求推升长端(前日盘中峰值5.025%); 陡峭化利多套息、利空黄金与风险资产"),
    ("AU − JP（政策利率）", "+3.35pp → +3.10pp", "BoJ 09-18 加息后收窄", "G10 对日元最大利差 → AUDJPY 为最大套息对; <b class='yellow'>本轮套息平仓已兑现 +437.3 pips（110.20 部分平仓）, 残余段剩余 R:R 1.04 勉强及格</b>, 只管理不加仓"),
    ("US − JP（政策利率）", "+2.625pp → +2.875pp", "Fed 加息25bp落地后走阔", "Fed 92% 加息 vs BoJ 同周加息 → 双向对冲后利差微幅走阔, USDJPY 154.92 高位; 方向由避险与干预风险主导"),
    ("US − KR（政策利率）", "+0.625pp → +0.875pp", "Fed 加息后走阔（BoK 纪要显分歧，短期不再加）", "<b class='red'>美韩利差走阔 = 韩元结构性承压</b>; USDKRW 站上回归通道上轨 1365.07 → 短线偏强, 但日内冲高回落 + ATR 放大, 追多赔率不合格"),
]
GEO_RISK = [
    ("🌊 中东 · 红海", "胡塞武装控制红海沿岸; 美伊敌对挤压出口, 沙特减产; 油价日内回落 -1.31% 至 99.61, 地缘溢价收敛但投机97%分位拥挤未解"),
    ("🔥 通胀回潮", "美国通胀高于目标 + 10Y盈亏平衡通胀2.38%; 10Y 4.97%/30Y 5.34% 高位 —— <b>长端利率冲击仍在压制全球风险资产与贵金属</b>"),
    ("🗾 日本变量", "BoJ 09-18 加息25bp(→1.25%)共识 + 财务省干预表态 + 日债10Y 3.030%(1996来最高) —— 日元政策紧缩与干预双通道打开, 套息平仓核心驱动"),
    ("🇰🇷 韩国变量", "BoK 08-27 加息至3.00% 但 09-15 纪要显分歧; USDKRW 日内冲高 1372.98 回落 1364.38, ATR(4H) 放大 —— <b>美韩利差走阔 + 高波动, 韩元偏弱但追多赔率不合格</b>"),
]
MACRO2 = [
    ("XAUUSD", "① Fed 加息92%(今夜FOMC) + 10Y 4.97% / 实际利率(DFII10) 2.60% —— <b>持金机会成本高企</b>; ② CFTC 投机净多 89%分位 —— <b>拥挤</b>, 但日内 +1.04% 反弹至 4338 显示买盘韧性"),
    ("XAGUSD", "① 跟随黄金反弹 +1.81% 强于金, 金银比修复; ② 工业属性受全球需求下修拖累 —— <b>波动极端化</b>"),
    ("DXY", "① Fed 加息92% + 长端 4.97% 高位 → 美元支撑; ② <b>99.55 偏强, 方向由今夜 FOMC 与点阵图决定</b>"),
    ("EURUSD", "① ECB 紧缩(2.25%)支撑, 但欧美政策预期差收窄; ② <b>美债收益率上行构成直接压制</b>, 今夜 FOMC 为双向风险"),
    ("GBPUSD", "① 英 8月 CPI 年率 3.1% 超预期(今公布) → BoE 维持 3.75% 概率上升; ② <b>与 FOMC 相邻 48h, 波动放大</b>"),
    ("USDJPY", "① 美日利差 +2.625pp 支撑 154.92 高位; ② <b>BoJ 09-18 加息25bp 预期 + 干预表态随时可启</b>, 双向风险"),
    ("USOIL", "① 中东地缘 + 沙特减产托底 vs 需求下修, 日内 -1.31% 回落 99.61; ② 投机97%分位拥挤 —— <b>供需双向撕裂, 事件驱动无 R:R</b>"),
    ("AUDUSD", "① RBA 4.35% 高位但中国需求下修 + 商品属性走弱压制澳元; ② 区间 0.706-0.722 无方向; ③ 今夜 FOMC 双向风险, 等突破"),
    ("AUDJPY", "① BoJ 加息 = 套息平仓核心驱动, AU−JP 利差由3.35pp收窄至3.10pp; ② RBA 4.35% 提供 carry 缓冲, 但<b>中国需求下修压制澳元商品属性</b>; ③ 日线 EMA60 空头 vs 4H 摆动高点 110.81 下方整理 → <b>长空短多分歧, 残余段只管理不加仓</b>"),
    ("USDKRW", "① BoK 08-27 加息至3.00%(连续第二次), 但 <b>09-15 会议纪要显内部分歧</b> → 收紧步伐或放缓; ② Fed 加息92% → <b class='red'>美韩利差由0.625pp走阔至0.875pp = 韩元结构性承压</b>; ③ 日内冲高 1372.98 回落, ATR(4H) 放大至 6.47 → 高波动, 追多赔率不合格"),
]
cb_rows = ""
for bank, rate, action, cyc, cyccls, impact in CB_POLICY:
    cb_rows += ("<tr><td class='white'>" + bank + "</td><td class='yellow'>" + rate + "</td><td>" + action +
                "</td><td class='" + cyccls + "'>" + cyc + "</td><td>" + impact + "</td></tr>")
carry2_rows = ""
for pair, val, trend, note in CARRY2:
    carry2_rows += ("<tr><td class='white'>" + pair + "</td><td class='yellow'>" + val + "</td><td>" + trend + "</td><td>" + note + "</td></tr>")
geo_cards = ""
for title, body in GEO_RISK:
    geo_cards += ('<div class="card"><div class="card-title">' + title + '</div><div class="card-sub" style="line-height:1.8">' + body + '</div></div>')
macro2_rows = ""
for sym, events in MACRO2:
    macro2_rows += ("<tr><td class='white' style='width:12%'>【" + sym + "】</td><td style='line-height:1.8'>" + events + "</td></tr>")

sec05 = """<div class="section"><div class="section-title">🌐 五、宏观金融面解读</div>
<div class="card-sub" style="margin:2px 0 10px;color:#8a9bc0">⏱ 数据截至: 央行政策 BIS WS_CBPOL + 金十快讯（09-16）· FRED 利率观测 09-14/15 · 利差/政策预期 金十日历 09-16 15:45 · CFTC 持仓 09-01/08-25 当周</div>
<div class="sub-title">5.1 央行政策对比表（BIS / 金十快讯 · 2026-09-16）</div>
<table><tr><th>央行</th><th>政策利率</th><th>最近动作</th><th>周期定位</th><th>对市场</th></tr>""" + cb_rows + """</table>
<div class="sub-title">5.2 利率地基（FRED 截至2026-09-14；高位）</div>
<table><tr><th>期限</th><th>收益率</th><th>期限</th><th>收益率</th></tr>
<tr><td>3M</td><td>""" + str(RATES["DGS3MO"]) + """%</td><td>10Y</td><td>""" + str(RATES["DGS10"]) + """% <span class="red">(高位)</span></td></tr>
<tr><td>2Y</td><td>""" + str(RATES["DGS2"]) + """%</td><td>30Y</td><td>""" + str(RATES["DGS30"]) + """%</td></tr>
<tr><td>5Y</td><td>""" + str(RATES["DGS5"]) + """%</td><td>实际利率TIPS</td><td>""" + str(RATES["DFII10"]) + """%</td></tr>
<tr><td>联邦基金</td><td>""" + str(RATES["FEDFUNDS"]) + """%</td><td>盈亏平衡</td><td>""" + str(RATES["T10YIE"]) + """%</td></tr>
</table>
<div class="card-sub" style="margin-top:6px">FRED 日线收盘截至 09-14; 10Y 4.97%（前日盘中峰值 5.025%, 金十）; 实际利率 2.60% 高位 → 黄金持有成本上升; 盈亏平衡 2.38% 显示通胀预期顽固。</div>
<div class="sub-title">5.3 利差结构（套息交易视角 · 3行固定）</div>
<table><tr><th>利差对</th><th>当前值</th><th>趋势</th><th>解读</th></tr>""" + carry2_rows + """</table>
<div class="verdict-warn" style="margin-top:10px"><b>🔥 结论:</b> 套息（carry）结构仍为正（澳日 3.35% → BoJ 加息后 3.10%）, 但方向由「利差收益」切换为「平仓冲击」——<b class='yellow'>BoJ 09-18 加息 25bp（→1.25%）是日元交叉盘最大反向变量</b>, 本轮已兑现为 AUDJPY 于 110.20 部分平仓 <b>+437.3 pips = +$28.22</b>; Fed 加息 92% 预期下美日利差反向走阔至 +2.875pp, USDJPY 154.92 高位, 转为避险与干预主导。<b class='yellow'>美韩利差同步走阔至 +0.875pp → 韩元承压但已伴 4H 双超买, 属「强趋势 + 高波动」组合, 只可顺势不可追高。</b><b>加息周期中的套息盘平仓是趋势放大器, 不是噪音；但平仓兑现后的残余段, 赔率不再合格。</b></div>
<div class="sub-title">5.4 地缘 + 风险偏好</div>
<div class="grid grid-4">""" + geo_cards + """</div>
<div class="sub-title">5.5 宏观大事综合（每标 2 条 · 明确对标的影响 · 10标的）</div>
<table><tr><th style="width:12%">标的</th><th>影响最大的 2 条宏观事项</th></tr>""" + macro2_rows + """</table></div>"""

# ===================== ⑥ 当日重要数据 + 议息提醒 =====================
CAL_PUB = [
    ("09-16 14:00", "英国 8月 CPI 年率", "3.1%", "2.9%", "2.9%", "超预期 → BoE 09-17 维持利率概率上升 → 英镑获支撑(GBPUSD 1.348 偏强)", "green"),
    ("09-16 14:00", "英国 8月 核心CPI 年率", "2.6%", "2.6%", "2.6%", "符合预期 → 不改变 BoE 按兵预期", "yellow"),
    ("09-16 14:00", "加拿大 8月 CPI 年率", "3.0%", "—", "3.0%", "持平前值 → 加元反应有限", "yellow"),
    ("09-15 10:00", "中国 8月 社会消费品零售总额年率", "0.4%", "2.6%", "1.7%", "大幅不及预期 → 中国需求走弱 → 压制澳元商品属性", "yellow"),
    ("09-15 17:00", "德国/欧元区 9月 ZEW 经济景气指数", "34.7 / 25.8", "41.2 / 31.0", "38.4 / 29.5", "不及预期 → 欧元区增长担忧, 欧元承压", "red"),
]
CAL_PENDING = [
    ("09-16 20:30", "美国 8月 零售销售月率", "0.3%", "-0.6%", "★★★★", "今晚公布; 直接驱动美元与美债短端; 超预期将强化 Fed 加息路径 → 美元↑ / AUDJPY↑（不利剩余空单）", True),
    ("09-16 22:30", "美国 EIA 原油库存(万桶)", "—", "-39.1", "★★★★", "今晚公布; 影响油价与商品货币情绪（WTI 拥挤 97% 分位, 双向放大）", True),
    ("09-17 02:00", "美联储 FOMC 利率决议 + SEP 点阵图 + 鲍威尔发布会", "加息 25bp 至 3.875%（CME 定价 92%）", "3.625%", "★★★★★", "今夜全球定价锚; 加息落地 + 点阵图偏鹰 → 美元跳升 → AUDJPY 反弹（触发保护 SL）; 偏鸽 → 美元回落 → AUDJPY 下探 TP", True),
    ("09-17 19:00", "英央行 BoE 利率决议", "维持 3.75%", "3.75%", "★★★★", "英CPI 3.1%超预期 → 维持概率上升; 与 FOMC 相邻 48h, 波动外溢至欧系货币", True),
    ("09-18 10:00", "日本央行 BoJ 利率决议 + 植田发布会", "加息 25bp 至 1.25%", "1.00%", "★★★★★", "日元交叉盘最大变量; 如期加息 → 日元走强 → AUDJPY 下探 109.781; 意外按兵 → 日元回落 → 触发保护 SL", True),
    ("09-17 20:30", "美国 初请失业金 + 费城联储制造业指数", "20.6万 / 47.4", "20.6万 / 47.4", "★★★", "FOMC 后首个数据, 验证就业动能; 对 AUD 影响间接", False),
    ("09-19", "贝克休斯石油钻井总数", "—", "449", "★★", "供给端边际信号, 对 AUD 影响间接", False),
]
CAL_MONTH = [
    ("本周", "美联储 FOMC 决议 + SEP 点阵图（今夜 09-17 02:00 北京）", "★★★★★", "CME 定价<b>加息 25bp 概率 92%</b> → 3.875%（前值 3.625%）", "已进入 24h 清仓窗口; 剩余持仓须确认保护 SL, 决议后 15 分钟不决策"),
    ("本周", "英央行 BoE 议息（09-17 19:00 北京）", "★★★★", "料维持 3.75%; 英8月CPI 3.1%超预期强化按兵预期", "与 FOMC 相邻, 48h 双事件 → 波动放大, 全程静默"),
    ("本周", "日本央行 BoJ 决议（09-18 10:00 北京）", "★★★★★", "广泛预期<b>加息 25bp → 1.25%</b>（前值 1.00%）; 日债 10Y 3.030% 创 1996/9 来最高", "AUDJPY/USDJPY 持仓的最大变量; 落地后重跑 MTF+量化再评估"),
    ("今晚", "美国 8 月零售销售（09-16 20:30 北京）", "★★★★", "月率预期 0.3% / 前值 -0.6%", "直接驱动美元与美债短端; 若超预期将强化 Fed 加息路径"),
    ("已过", "韩国央行 BoK（08-27 加息 25bp 至 3.00%）", "★★★", "连续第二次加息; <b>09-15 会议纪要显内部分歧</b> → 收紧步伐或放缓", "美韩利差由 0.625pp 走阔至 0.875pp → 韩元结构性承压"),
]
calpub_rows = ""
for t, ev, act, exp, prev, impact, icls in CAL_PUB:
    calpub_rows += ("<tr><td>" + t + "</td><td class='white'>" + ev + "</td><td class='" + icls + "'>" + act +
                    "</td><td>" + exp + "</td><td>" + prev + "</td><td>" + impact + "</td></tr>")
calpend_rows = ""
for t, ev, exp, prev, star, path, hl in CAL_PENDING:
    tr_open = "<tr class='event-highlight'>" if hl else "<tr>"
    starcls = "red" if "★★★★" in star else "yellow"
    calpend_rows += (tr_open + "<td class='red'>" + t + "</td><td class='white'>" + ev + "</td><td>" + exp +
                     "</td><td>" + prev + "</td><td class='" + starcls + "'>" + star + "</td><td>" + path + "</td></tr>")
calmonth_rows = ""
for dt, ev, imp, exp, act in CAL_MONTH:
    calmonth_rows += ("<tr><td class='white'>" + dt + "</td><td>" + ev + "</td><td class='yellow'>" + imp +
                      "</td><td>" + exp + "</td><td>" + act + "</td></tr>")
sec06 = """<div class="section"><div class="section-title">📅 六、当日重要数据 + 议息提醒</div>
<div class="card-sub" style="margin:2px 0 10px;color:#8a9bc0">⏱ 数据截至: 财经日历 = 金十 list_calendar 取数 2026-09-16 15:45 GMT+8（事件时间均为北京时间; 已公布项实际值截至取数时点）</div>
<div class="sub-title">6.1 ✅ 近期已公布</div>
<table><tr><th>时间</th><th>数据</th><th>实际</th><th>预期</th><th>前值</th><th>影响</th></tr>""" + calpub_rows + """</table>
<div class="sub-title">6.2 🔴 待公布（关键 · 48h 三央行密集窗口）</div>
<table><tr><th>时间(GMT+8)</th><th>事件</th><th>预期</th><th>前值</th><th>星级</th><th>影响路径</th></tr>""" + calpend_rows + """</table>
<div class="sub-title">6.3 📌 本月（2026-09）议息与数据提醒</div>
<table><tr><th>日期</th><th>事件</th><th>重要性</th><th>预期</th><th>对操作</th></tr>""" + calmonth_rows + """</table>
<div class="verdict-warn" style="margin-top:10px"><b>⚠ 事件纪律:</b> 距最近事件（零售销售 09-16 20:30）仅 <b>4.75 小时</b>, 距 FOMC <b>10.25 小时（已进入 24h 清仓窗口）</b>, 距 BoJ <b>42.25 小时</b> —— 本日处于<b>静默期</b>: ① <b>不开任何新仓</b>; ② 剩余 0.01 手 AUDJPY 已为<b>最小仓 ✓</b>, 须<b>确认保护性 SL 111.30 已挂</b>; ③ 若 09-17 00:00（FOMC 前 2h）未触 TP → <b>主动市价了结</b>; ④ 决议公布后等第一波方向走完（≥15 分钟）再评估, <b class='yellow'>不追第一根 K 线</b>。</div>
<div class="central-bank">央行周期: 美联储(再紧缩, 加息 92% → 3.875%) &gt; 日(1.00% 加速正常化 → 1.25%, 套息根基) = 韩(3.00% 紧缩·分歧) &gt; 澳(4.35% 高位维持) &gt; 英(3.75% 高位观望) &gt; 欧(2.25% 已恢复紧缩)。<b>美元在"加息+长端破5%"下偏强, 日元因 BoJ 加息 + 干预预期走强 —— 两者挤压 AUDJPY 的套息空间, 残余段赔率不再合格。</b></div></div>"""

# ===================== ⑦ 跨市场验证 =====================
sec07 = """<div class="section"><div class="section-title">🔄 七、跨市场验证</div>
<div class="card-sub" style="margin:2px 0 10px;color:#8a9bc0">⏱ 数据截至: 跨市场报价 金十实时 09-16 15:45（XAU/USOIL/USDJPY）· 利率 FRED 09-14/15 · 利差结构见 5.3（截至 09-16）</div>
<div class="chart-box"><div class="chart-title">🔄 跨市场方向热力（红=偏空/绿=偏多，相对强度0-5）</div><div id="cross" class="chart-medium"></div></div>
<div class="card-sub">验证链: ①黄金 vs TIPS实际利率(负向) — 实际利率2.60%高位 + 10Y 4.97% → 昨压制今反弹(+1.04%至4338), 属事件前修复非趋势反转; ②WTI vs 中东风险 — 回落 -1.31% 至 99.61, 投机97%分位拥挤延续, 今晚EIA再定价; ③AUDJPY vs 澳日利差 — 套息 3.35%→3.10% 收窄, BoJ 加息是平仓导火索, 残余段赔率 1.04 勉强及格; ④USDJPY vs 10Y — 美日利差 +2.625pp 高位, USDJPY 154.92 高位震荡; ⑤<b class='yellow'>韩元(USDKRW) vs 美元/美债</b> — Fed 加息 92% → 美韩利差由 0.625pp 走阔至 0.875pp → <b class='red'>韩元承压, USDKRW 偏多(韩元走弱)</b>, 与日元方向相反(日元因 BoJ 加息走强), 两者共同构成亚太货币的分化格局。结论: 宏观与跨市场一致指向<b class="red">「美元与长端利率偏强 + 日元因政策独立走强」</b>, 事件窗口内不给任何低不确定共振方向, FOMC 前静默。</div></div>"""

# ===================== ⑧ 多周期共振 =====================
sec08 = """<div class="section"><div class="section-title">📈 八、多周期共振（真实日K + 关键位）</div>
<div class="card-sub" style="margin:2px 0 10px;color:#8a9bc0">⏱ 数据截至: 日K = Twelve Data 各 200 根, 末根 2026-09-16（取数 15:45 GMT+8）· XAGUSD/USOIL 日K缺失（源不支持）已标注</div>
""" + "".join(charts_html) + silver_oil_note + """
<div class="sub-title">8.2 关键位（10标的, 每标一个，表格化 · v1.4.3）</div>
<table><tr><th>品种</th><th>关键位</th><th>类型</th><th>作用 / 触发条件</th></tr>""" + kl_rows + """</table></div>"""

# ===================== ⑨ 量化验证（v2.5.2: 分标的独立雷达, 不叠加） =====================
sec09 = """<div class="section"><div class="section-title">📡 九、量化验证（分标的独立雷达 · 不叠加）</div>
<div class="card-sub" style="margin:2px 0 10px;color:#8a9bc0">⏱ 量化样本截至: AUDJPY / USDKRW 日线 200 根（末根 2026-09-16）· 4H 指标末根 09-16（取数 15:45 GMT+8）</div>

<div class="sub-title">9.1 AUDJPY 持仓量化雷达</div>
<div class="chart-box"><div class="chart-title">📡 AUDJPY 量化雷达（趋势/偏离/Sharpe/Sortino/偏度/VaR）</div><div id="radar_aj" class="chart-small"></div></div>
<div class="card-sub">AUDJPY日线量化: <b>Hurst|""" + str(round(h_abs,2)) + """</b>（&gt;0.55 = 趋势型, 利于持仓跟踪）, <b>Z=""" + Z_SIGN + str(round(z_abs,2)) + """</b>（价格相对 60 日均值, 现价""" + ("高于" if Z_SIGN=='+' else "低于") + """均值 """ + str(round(z_abs,2)) + """σ）, 年化|Sharpe|=""" + str(round(sh_abs,2)) + """, |Sortino|=""" + str(round(so_abs,2)) + """, |偏度|=""" + str(round(sk_abs,2)) + """, 日VaR95%=""" + str(round(var95,2)) + """%（0.01 手 ≈ $""" + str(round(var95/100.0*POS["cur"]/0.01*_pip_val, 2)) + """）。量化健康度中等: 趋势型（Hurst 高）+ 价格偏下（Z 负）组合支持「持有不加仓」; 但 Fed 加息 92% 厚尾风险下不放大仓位。</div>

<div class="sub-title">9.2 韩元(USDKRW) 量化雷达</div>
<div class="chart-box"><div class="chart-title">📡 USDKRW 量化雷达（趋势/偏离/Sharpe/Sortino/偏度/VaR）</div><div id="radar_krw" class="chart-small"></div></div>
<div class="card-sub">📡 韩元(USDKRW)日线量化: <b>Hurst|""" + str(round(h_k,2)) + """</b>, <b>Z=""" + Z_SIGN_K + str(round(abs(z_k),2)) + """</b>（价格相对 60 日均值, 现价""" + ("高于" if Z_SIGN_K=='+' else "低于") + """均值 """ + str(round(abs(z_k),2)) + """σ）, 年化|Sharpe|=""" + str(round(sh_k,2)) + """, |Sortino|=""" + str(round(so_k,2)) + """, |偏度|=""" + str(round(sk_k,2)) + """, 日VaR95%=""" + str(round(var95_k,2)) + """%。叠加4H技术面: <b class="green">EMA5 1364.14 &gt; EMA10 1360.15 &gt; EMA60 1350.32 标准多头排列</b> + MACD 柱 <b class="green">+1.876 仍为正</b> + 站上回归通道上轨 <b>1365.07</b> → 短线偏强; RSI(4H) 回落至 <b class="yellow">65.95</b>（超买已修复）、STOCH <b class="yellow">81.70/84.73</b>, 但 ATR(14) 4H 放大至 <b class="red">6.4745</b> 高波动, 且日内冲高 1372.98 后回落。结论: <b class="yellow">「中期修复 + 短线强 + 波动放大」, 追多赔率不合格, 等回踩 1352（通道中轨）或事件落地后重估。</b></div></div>"""

# ===================== ⑩ 概率情景预案 =====================
sec10 = """<div class="section"><div class="section-title">🎲 十、AUDJPY 持仓 · 三情景预案（表格化 · 只准备不预测）</div>
<table>
<tr><th style="width:15%">情景</th><th style="width:8%">概率</th><th style="width:31%">触发路径</th><th style="width:30%">操作</th><th style="width:16%">预期结果</th></tr>
<tr><td class='green'>🐻 情景A<br>双向加息落地·日元略占优<br><span style="font-size:11px;color:#8a9bc0">(基准情景)</span></td><td class='yellow'>~45%</td>
<td>Fed 09-17 加息 25bp 落地（92% 定价）+ 点阵图偏鹰, 但 BoJ 09-18 如期加息至 1.25% → 双向对冲后日元端略占优 + 套息平仓延续 → AUDJPY 震荡下探 <b>109.781</b>（TP）</td>
<td>补挂 SL """ + str(POS["sl_new"]) + """ → 保留 TP 挂单 → TP 触发自动全平</td>
<td class='green'>剩余 +77.3 pips = +$4.99<br><span style="font-size:11px;color:#8a9bc0">本笔合计 +$""" + str(round(POS["part_pnl"] + _to_tp * _pip_val, 2)) + """</span></td></tr>
<tr><td class='yellow'>🐂 情景B<br>Fed 偏鸽 / BoJ 按兵<br><span style="font-size:11px;color:#8a9bc0">AUDJPY 反弹</span></td><td class='yellow'>~35%</td>
<td>Fed 点阵图偏鸽（或意外按兵）+ BoJ 暂缓加息 → 美债收益率回落 + 日元走弱 → AUDJPY 反弹, 1H 收盘站上 <b>111.00</b>（4H 摆动高点 110.81 上方）</td>
<td>① 保护 SL """ + str(POS["sl_new"]) + """ 自动触发, 或 ② 1H 站上 111.00 时主动市价了结 → 不与结构争辩</td>
<td class='yellow'>剩余 -$""" + str(round(max((_to_sl - 30) * _pip_val, 0), 2)) + """ ~ +$1.0<br><span style="font-size:11px;color:#8a9bc0">(本金安全 · 已实现保住)</span></td></tr>
<tr><td class='red'>⚡ 情景C<br>超预期紧缩 + 日元崩塌<br><span style="font-size:11px;color:#8a9bc0">(尾部风险)</span></td><td class='yellow'>~20%</td>
<td>Fed 加息幅度/指引大幅超预期 + BoJ 意外按兵或鸽派 → 美元飙升 + 日元单边走弱 → AUDJPY 跳空冲高, 直接越过保护 SL """ + str(POS["sl_new"]) + """</td>
<td>SL 触发后市价立即离场, <b>不补仓不反手</b> → 观望 24h 等波动率回落; 若跳空滑点则接受</td>
<td class='red'>剩余 -$""" + str(POS["risk_rest"]) + """ ~ -$""" + str(round(POS["risk_rest"] * 2, 2)) + """<br><span style="font-size:11px;color:#8a9bc0">(严格止损, 最坏 0.80%~1.6% 账户)</span></td></tr>
</table>
<div class="card-sub" style="margin-top:10px">注: 三情景不论哪一条触发, <b class="green">已实现的 +$""" + str(POS["part_pnl"]) + """（+""" + str(POS["part_pips"]) + """ pips = +""" + str(round(POS["part_pips"] / R_UNIT_PIPS, 2)) + """R）均已落袋且不可回吐</b>; 本表的差异只影响剩余 0.01 手的 ±$5 ~ ±$12。这正是「部分平仓」的价值 —— <b class="yellow">把不确定性从「整笔」压缩到「残余段」</b>。</div></div>"""

# ===================== ⑪ 凯利仓位计算器 =====================
sec11 = """<div class="section"><div class="section-title">🧮 十一、凯利仓位计算器（交互）</div>
<div class="two-col">
<div class="card"><div class="card-title">🎯 凯利公式原理</div>
<div class="kelly-formula">f* = ( p × b − q ) / b</div>
<div class="card-sub">f* = 最优仓位比例 ｜ p = 胜率 ｜ q = 1−p (败率) ｜ b = 盈亏比<br>凯利公式给出长期资本增长最大化的仓位。<b class="yellow">实战建议用半凯利 (f*/2)</b>, 降低波动和最大回撤。</div>
<div class="sub-title">📊 AUDJPY 历史信号回测（60根日线, 三周期共振策略）</div>
<table>
<tr><td>策略胜率 p</td><td class='white' style="text-align:right">""" + str(KELLY["p"]) + """%</td></tr>
<tr><td>平均盈亏比 b</td><td class='white' style="text-align:right">""" + str(KELLY["b"]) + """</td></tr>
<tr><td>凯利最优 f*</td><td class='red' style="text-align:right">""" + str(KELLY["f"]) + """%</td></tr>
<tr><td>半凯利 (推荐)</td><td class='green' style="text-align:right">""" + str(KELLY["f_half"]) + """%</td></tr>
<tr><td>三分之一凯利 (保守)</td><td class='yellow' style="text-align:right">""" + str(KELLY["f_third"]) + """%</td></tr>
</table></div>
<div class="card"><div class="card-title">💼 本账户仓位测算（全标的适配）</div>
<div class="card-sub" style="margin-bottom:8px" id="k_pipinfo">AUDJPY 当前价 """ + str(POS["cur"]) + """ · 每 pip 价值 ≈ $""" + str(round(_pip_val,4)) + """/0.01手</div>
<div class="input-group"><label>投资标的</label><select id="k_inst" onchange="onInst()" style="flex:1;background:rgba(0,0,0,.3);border:1px solid rgba(74,127,255,.5);border-radius:6px;padding:8px;color:#fff;font-weight:600">
<option value="AUDJPY" selected>AUDJPY 澳元/日元（当前持仓）</option>
<option value="USDJPY">USDJPY 美元/日元</option>
<option value="EURUSD">EURUSD 欧元/美元</option>
<option value="GBPUSD">GBPUSD 英镑/美元</option>
<option value="XAUUSD">XAUUSD 现货黄金</option>
<option value="XAGUSD">XAGUSD 现货白银</option>
<option value="USOIL">USOIL WTI 原油</option>
<option value="USDKRW">USDKRW 美元/韩元（关注）</option>
</select></div>
<div class="input-group"><label>账户净值 $</label><input id="k_eq" value='""" + str(ACC["equity"]) + """'></div>
<div class="input-group"><label>胜率 %</label><input id="k_p" value='""" + str(KELLY["p"]) + """'></div>
<div class="input-group"><label>盈亏比</label><input id="k_b" value='""" + str(KELLY["b"]) + """'></div>
<div class="input-group"><label>止损距离(pips)</label><input id="k_sl" value='""" + str(KELLY["sl_pips"]) + """'></div>
<div class="input-group"><label>风险偏好</label><select id="k_mode" style="flex:1;background:rgba(0,0,0,.3);border:1px solid rgba(127,169,255,.2);border-radius:6px;padding:8px;color:#fff"><option value="0.5" selected>半凯利 (稳健·推荐)</option><option value="1">全凯利 (激进)</option><option value="0.333">三分之一凯利 (保守)</option></select></div>
<button class="calc-btn" onclick="calcKelly()">🔄 重新计算</button>
<table style="margin-top:12px">
<tr><td>最优仓位比例</td><td class='white' style="text-align:right" id="o_pct">""" + str(KELLY["f_half"]) + """%</td></tr>
<tr><td>最大可亏金额</td><td class='white' style="text-align:right" id="o_loss">$""" + str(KELLY["max_loss"]) + """</td></tr>
<tr><td>推荐手数</td><td class='green' style="text-align:right" id="o_lots">""" + str(KELLY["rec_lots"]) + """ 手</td></tr>
<tr><td id="o_cur_lbl">剩余 0.01 手（已平 0.01）</td><td class='red' style="text-align:right" id="o_cur">最小手 · 0.80% 风险</td></tr>
<tr><td>建议操作</td><td class='green' style="text-align:right" id="o_act">补挂 SL 111.30，保留至 TP</td></tr>
</table></div>
</div>
<div class="verdict-warn" style="margin-top:12px"><b>💡 凯利公式使用注意:</b> ① 凯利假设连胜连败分布均匀, 但实际交易存在连续亏损期, 因此<b class="yellow">半凯利是实战最优解</b>; ② 单笔风险 ≤1% 是硬纪律, 凯利结果超过 1% 时以 1% 为准; ③ 凯利只适用于正期望值系统 (胜率×盈亏比 &gt; 1), 负期望系统任何仓位都是错的; ④ <b class="yellow">切换投资标的时</b>, 右侧自动代入该品种的 pip 价值与参考止损距离, 但胜率/盈亏比应替换为该标的自身回测参数 (左侧默认展示 AUDJPY 样本), 再点「重新计算」。</div>
</div>
<script>
var INST={
 "AUDJPY":{pip:""" + str(round(_pip_val,4)) + """,sl:75,px:"110.554",note:"0.01手=1000单位, pip=0.01, 保护SL 111.30"},
 "USDJPY":{pip:0.0645,sl:120,px:"154.924",note:"0.01手=1000单位, pip=0.01"},
 "EURUSD":{pip:1.000,sl:80,px:"1.15551",note:"0.01手=1000单位, pip=0.0001"},
 "GBPUSD":{pip:1.000,sl:90,px:"1.34825",note:"0.01手=1000单位, pip=0.0001"},
 "XAUUSD":{pip:1.000,sl:40,px:"4337.29",note:"0.01手=1盎司, 按$1波动计"},
 "XAGUSD":{pip:0.500,sl:200,px:"64.823",note:"0.01手=50盎司, pip=0.01"},
 "USOIL":{pip:0.100,sl:150,px:"99.614",note:"0.01手=10桶, pip=0.01"},
 "USDKRW":{pip:0.0073,sl:130,px:"1364.38",note:"0.01手=1000美元, pip=0.01（关注品种·不直接交易）"}
};
window._pip=INST["AUDJPY"].pip;
function onInst(){
  var s=document.getElementById('k_inst').value;
  var d=INST[s];
  document.getElementById('k_sl').value=d.sl;
  document.getElementById('k_pipinfo').innerHTML=s+" 当前价 "+d.px+" · 每 pip 价值 ≈ $"+d.pip+"/0.01手（"+d.note+"）";
  window._pip=d.pip;
  calcKelly();
}
function calcKelly(){
  var eq=parseFloat(document.getElementById('k_eq').value);
  var p=parseFloat(document.getElementById('k_p').value)/100;
  var b=parseFloat(document.getElementById('k_b').value);
  var slp=parseFloat(document.getElementById('k_sl').value);
  var mode=parseFloat(document.getElementById('k_mode').value);
  var q=1-p; var f=(p*b-q)/b; if(f<0)f=0;
  var fplan=f*mode; var fcap=0.01; if(fplan>fcap)fplan=fcap;
  var maxloss=eq*fplan;
  var lots=Math.floor(maxloss/(slp*window._pip*100)*100)/100;
  document.getElementById('o_pct').innerHTML=(fplan*100).toFixed(1)+'%';
  document.getElementById('o_loss').innerHTML='$'+maxloss.toFixed(2);
  document.getElementById('o_lots').innerHTML=lots.toFixed(2)+' 手';
  var inst=document.getElementById('k_inst').value;
  if(inst==="AUDJPY"){
    document.getElementById('o_cur_lbl').innerHTML='剩余 0.01 手（已平 0.01）';
    document.getElementById('o_cur').innerHTML='最小手 · 0.80% 风险 ✓';
    document.getElementById('o_act').innerHTML='补挂保护性 SL 111.30，保留至 TP 109.781';
  }else{
    document.getElementById('o_cur_lbl').innerHTML='当前持仓';
    document.getElementById('o_cur').innerHTML='未持仓 · 新开仓评估';
    document.getElementById('o_act').innerHTML='若建仓 ≤ '+lots.toFixed(3)+' 手';
  }
}
</script>"""

# ===================== ⑫ 相关性热力图 + 解读 =====================
sec12 = """<div class="section"><div class="section-title">🔗 十二、收益相关性热力图（日收益 Pearson · 7标的 · 组合暴露诊断）</div>
<div class="chart-box"><div class="chart-title">🔗 7标的日收益相关性热力图</div><div id="corr" class="chart"></div></div>
<div class="grid grid-3">
<div class="card"><div class="card-title">⚠️ 高度正相关（风险集中）</div>"""
for pair, val, note in CORR_HIGH:
    sec12 += ('<div style="margin-bottom:12px"><span class="red" style="font-weight:700">' + pair + '  ' + val + '</span>'
             '<div class="card-sub">' + note + '</div></div>')
sec12 += """</div>
<div class="card"><div class="card-title">○ 低相关（分散风险）</div>"""
for pair, val, note in CORR_LOW:
    sec12 += ('<div style="margin-bottom:12px"><span class="green" style="font-weight:700">' + pair + '  ' + val + '</span>'
             '<div class="card-sub">' + note + '</div></div>')
sec12 += """</div>
<div class="card"><div class="card-title">💡 今日组合诊断</div>
<div class="card-sub" style="line-height:1.9">
当前持仓: <b class="white">AUDJPY 空单 1 笔</b><br>
相关性集中度: <b class="green">低</b> (仅1笔)<br>
隐含暴露: <b class="yellow">日元走强 + 澳元走弱</b><br>
韩元(USDKRW)关注: <b class="yellow">与日元正相关0.71</b>, 同属亚太套息货币, 共同受BoJ加息驱动<br>
风险提示: <span class="red">若未来加 USDJPY 空单, 两笔共享日元端 = 实际是 1.5 倍日元多头</span><br>
建议: <span class="green">做多日元优先选 AUDJPY (澳元还受商品拖累, 方向更纯)</span>
</div></div>
</div></div>"""

# ===================== ⑬ 账户风险仪表盘 =====================
sec13 = """<div class="section"><div class="section-title">📊 十三、账户风险仪表盘</div>
<div class="grid grid-4">
<div class="card"><div class="card-title">💰 账户净值</div>
<div class="card-value" style="color:#2ecc71">$""" + str(ACC["equity"]) + """</div>
<div class="card-sub">入金 $""" + str(int(ACC["deposit"])) + """ + 浮盈 $""" + str(ACC["floating"]) + """</div>
<div class="card-sub" style="margin-top:8px">累计收益: <b class="green">+""" + str(ACC["cum_ret"]) + """% ✓</b></div></div>
<div class="card"><div class="card-title">📉 单笔风险</div>
<div class="card-value" style="color:#f1c40f">$""" + str(POS["risk_usd"]) + """</div>
<div class="card-sub">AUDJPY 剩余 """ + str(POS["lots_now"]) + """ 手 @ SL """ + str(POS["sl_new"]) + """</div>
<div class="risk-meter" style="margin-top:10px"><div class="risk-meter-fill" data-val="2.0%" style="width:100%;background:linear-gradient(90deg,#2ecc71,#f1c40f)"></div></div>
<div class="card-sub">占净值: <b class="yellow">""" + str(POS["risk_rest_pct"]) + """% (合规 ≤1%)</b></div></div>
<div class="card"><div class="card-title">📊 组合风险</div>
<div class="card-value" style="color:#f1c40f">$""" + str(POS["risk_usd"]) + """</div>
<div class="card-sub">相关性调整后</div>
<div class="risk-meter" style="margin-top:10px"><div class="risk-meter-fill" data-val="2.0%" style="width:40%;background:linear-gradient(90deg,#2ecc71,#f1c40f)"></div></div>
<div class="card-sub">总风险: <b class="yellow">上限 5%</b></div></div>
<div class="card"><div class="card-title">🎯 最大回撤</div>
<div class="card-value" style="color:#2ecc71">""" + str(ACC["max_dd"]) + """%</div>
<div class="card-sub">历史峰值至今</div>
<div class="card-sub" style="margin-top:8px">阈值预警: <b class="yellow">10% 黄灯</b> / <b class="red">20% 红灯</b><br>当前: <b class="green">安全区</b></div></div>
</div>
<div class="chart-box"><div class="chart-title">📈 账户权益曲线（基于 AUDJPY 持仓）</div><div id="equity" class="chart-medium"></div></div>
<div class="verdict-warn"><b>⚠️ 风险预警（共 1 项）</b><br>
<b>1. 单笔风险:</b> 本笔 AUDJPY 持仓已收紧 SL 至 """ + str(POS["sl_new"]) + """, 剩余风险 $""" + str(POS["risk_rest"]) + """ (""" + str(POS["risk_rest_pct"]) + """%), <b class="green">已符合 ≤1% 纪律</b>。FOMC 决议前不新增任何仓位, 仅管理现有持仓。<b class="red">小账户保命优先。</b></div>
</div>"""

# ===================== ⑭ 动态止损方案对比 =====================
sec14 = """<div class="section"><div class="section-title">🛡️ 十四、动态止损方案对比</div>
<div class="card-sub" style="margin-bottom:10px">对 AUDJPY <b>剩余 0.01 手空单</b>给出三种保护性止损方案, 推荐方案已标注。止损不是越紧越好, 也不是越宽越好, 而是与波动率匹配 —— 剩余仓位已是<b>最小手</b>, 无法再分批, 因此止损质量决定这笔的最终结果。</div>
<div class="chart-box"><div class="chart-title">📊 三种止损方案 · 风险收益对比</div><div id="stopcmp" class="chart-medium"></div></div>
<table>
<tr><th style="width:16%">方案</th><th style="width:28%">ATR止损 (1.5×D ATR)</th><th style="width:28%">结构止损 (4H摆动高点上方)</th><th style="width:28%" class="green">移动止损 (推荐 ★)</th></tr>
<tr><td>止损位</td><td>""" + STOPS["atr"]["lvl"] + """</td><td>""" + STOPS["struct"]["lvl"] + """</td><td class="green">""" + STOPS["trail"]["lvl"] + """</td></tr>
<tr><td>止损距离</td><td>""" + STOPS["atr"]["dist"] + """</td><td>""" + STOPS["struct"]["dist"] + """</td><td class="green">""" + STOPS["trail"]["dist"] + """</td></tr>
<tr><td>单笔风险 (0.01手)</td><td>$""" + str(STOPS["atr"]["risk"]) + """</td><td>$""" + str(STOPS["struct"]["risk"]) + """</td><td class="green">递减中</td></tr>
<tr><td>被扫概率</td><td>~""" + str(STOPS["atr"]["sweep"]) + """% (较宽松)</td><td>~""" + str(STOPS["struct"]["sweep"]) + """% (适中)</td><td class="green">随趋势下降</td></tr>
<tr><td>保住利润</td><td>少 (回撤多)</td><td>中</td><td class="green">多 (SL只向盈利移)</td></tr>
<tr><td>适用场景</td><td>""" + STOPS["atr"]["scene"] + """</td><td>""" + STOPS["struct"]["scene"] + """</td><td class="green">""" + STOPS["trail"]["scene"] + """</td></tr>
</table>
<div class="verdict" style="margin-top:12px"><b>💡 最终推荐: 结构止损 111.30 起步 → 转为 1H EMA20 移动止损</b><br>
当前阶段 = <b>残余段管理</b>（已实现 +""" + str(POS["part_pips"]) + """ pips 落袋; 剩余 """ + str(round(_pips,1)) + """ pips 浮盈, Hurst """ + str(round(h_abs,2)) + """ 趋势型但 Z=""" + Z_SIGN + str(round(z_abs,2)) + """ 价格已偏离均值为负）—— 剩余 0.01 手已是<b>最小手</b>, 不能再分批, 只能靠止损质量取胜:<br>
① <b>立即补挂 SL """ + str(POS["sl_new"]) + """</b>（4H 摆动高点 110.81 + 1.5×4H ATR 上方 · 74.6 pips · $""" + str(POS["risk_rest"]) + """ = """ + str(POS["risk_rest_pct"]) + """%）→ 把「裸持」变成「有保护」, 这是本笔最关键的一步<br>
② 保留 <b>TP 109.781</b> 挂单不动（距 77.3 pips）→ 让利润自己去跑, 不手动干预<br>
③ 若 1H 收盘站上 <b>111.00</b>（短线多头确认）→ <b>主动市价了结</b>, 不再等 TP; 若 FOMC（09-17 02:00）前 2h 仍未触 TP → 同样<b>主动了结</b>锁利<br>
④ 触及 SL 111.30 → 市价立即离场, <b>不补仓、不反手</b>, 观望 24h<br>
<b>核心逻辑:</b> 残余段的目标不是「多赚」, 而是<b>「把已兑现的利润锁死、把剩余的暴露钉死」</b> —— 已实现 +$""" + str(POS["part_pnl"]) + """ 不可回吐, 剩余风险上限 $""" + str(POS["risk_rest"]) + """。</div>
</div>"""

# ===================== ⑮ 综合判定与操作建议 =====================
o8_rows = ""
for sym, verdict, reason in OTHER8:
    vcls = "red" if verdict == "不建议建仓" else ("yellow" if (verdict == "观望" or "关注" in verdict) else "green")
    o8_rows += ("<tr><td class='white'>" + sym + "</td><td class='" + vcls + "'>" + verdict + "</td><td>" + reason + "</td></tr>")
sec15 = """<div class="section"><div class="section-title">💡 十五、综合判定与操作建议</div>
<div class="sub-title">15.1 AUDJPY 持仓诊断（entry 114.573 · SELL 0.02 手 → 110.20 部分平仓 0.01 手 · 剩余 0.01 手持仓 · 原 SL 113.284 · TP 109.781）</div>
<div class="grid grid-4">
<div class="card"><div class="card-title">💰 浮盈状态</div>
<div class="card-value" style="color:#2ecc71">+""" + str(round(_pips,1)) + """ pips</div>
<div class="card-sub">+$""" + str(ACC["floating"]) + """（占净值 +""" + str(round(ACC["floating"] / ACC["equity"] * 100, 2)) + """%）<br>当前价 """ + str(POS["cur"]) + """ ｜ 已实现 +$""" + str(POS["part_pnl"]) + """（+""" + str(POS["part_pips"]) + """ pips）</div></div>
<div class="card"><div class="card-title">🎯 至 TP / 至 SL</div>
<div class="card-value" style="color:#3498db">""" + str(_to_tp) + " / " + str(_to_sl) + """</div>
<div class="card-sub">pips（至 TP 109.781 / 至保护 SL """ + str(POS["sl_new"]) + """）<br><b class="red">剩余 R:R = 77.3 / 74.6 = 1.04 勉强及格</b>，只管理不加仓</div></div>
<div class="card"><div class="card-title">🧭 三周期方向</div>
<div class="card-value" style="color:#f1c40f">长空短多·分歧</div>
<div class="card-sub">日线 EMA60 112.45 仍空头压制, 但 15min/1H/4H 已转多头排列 → <b class="yellow">趋势级别切换期, 不宜新开</b></div></div>
<div class="card"><div class="card-title">⚠️ 事件风险</div>
<div class="card-value" style="color:#e74c3c">Fed + BoE + BoJ ★★★★★</div>
<div class="card-sub">09-17 02:00 Fed（CME 定价<b class="red">加息 92%</b>）/ 09-17 19:00 BoE / 09-18 10:00 BoJ（预期加息至 1.25%）→ 48h 内三央行, 预期 ±150-200 pips 双向跳空</div></div>
</div>
<div class="sub-title">15.2 剩余持仓应对三情景（按纪律执行，禁止 C 项）</div>
<div class="scenario-card scenario-neutral"><div class="scenario-head"><span class="scenario-title">🛡️ 情景 A（稳健 · 补挂保护 SL + 事件前了结）</span><span class="scenario-prob green">推荐 ★</span></div>
<div class="scenario-actions">立即补挂保护性 SL <b>""" + str(POS["sl_new"]) + """</b>（74.6 pips · 风险 $""" + str(POS["risk_rest"]) + """ = """ + str(POS["risk_rest_pct"]) + """%, 在 1% 纪律内）→ 保留 TP 109.781 挂单不动 → 若至 09-17 00:00（FOMC 前 2h）仍未触及 TP，则<b>主动市价了结</b>锁定 +""" + str(round(_pips,1)) + """ pips（≈ +$""" + str(ACC["floating"]) + """）→ 不与三央行事件对赌。</div></div>
<div class="scenario-card scenario-bullish"><div class="scenario-head"><span class="scenario-title">🐂 情景 B（美联储意外按兵 / 点阵图偏鸽 · 反弹则了结）</span><span class="scenario-prob yellow">备选</span></div>
<div class="scenario-actions">若 Fed 未加息且指引偏鸽 → 美债收益率回落 → AUDJPY 反弹 → 一旦 1H 收盘站上 <b>111.00</b>（4H 摆动高点 110.81 上方）即视为短线多头确认 → <b>剩余 0.01 手全平</b>（接受 +""" + str(round(max(_pips - 60, 0), 1)) + """~+""" + str(round(_pips,1)) + """ pips）→ 不与结构争辩。<b class="yellow">若已补挂 SL 111.30 则自动执行, 无需手动</b>。</div></div>
<div class="scenario-card scenario-bearish"><div class="scenario-head"><span class="scenario-title">⛔ 情景 C（无保护裸持过三央行 · 不接受）</span><span class="scenario-prob red">不接受</span></div>
<div class="scenario-actions">不补挂 SL、持仓裸过 Fed/BoE/BoJ —— 原 SL 113.284 位于获利区已实质失效, 价格上行无任何保护; 若 Fed 加息 92% 落地 + 美元跳升, AUDJPY 反弹 <b>401.9 pips</b>（回到入场价 114.573）即抹去全部浮盈 +$""" + str(ACC["floating"]) + """, 再上行则转为净亏损, 且无 SL 可挡。<b class="red">一律否决。</b></div></div>
<div class="recommendation" style="margin-top:14px"><h3>🎯 最终推荐：情景 A（稳健派）—— 09-17 FOMC 前执行完毕</h3>
<table><tr><th style="width:16%">项目</th><th>具体操作</th></tr>
<tr><td>交易标的</td><td>AUDJPY（已部分平仓的剩余 0.01 手空单, <b>非新开仓</b>）</td></tr>
<tr><td>方向 / 手数</td><td>SELL 0.02 手 → 已于 110.20 平 0.01 手 → <b>维持剩余 0.01 手</b></td></tr>
<tr><td>止盈</td><td>TP1 109.781（原挂单保留, 距 +""" + str(_to_tp) + """ pips）/ TP2 109.24（破位延伸, 不主动追）</td></tr>
<tr><td>止损</td><td><b class="yellow">补挂保护性 SL """ + str(POS["sl_new"]) + """</b>（4H 摆动高点 110.81 + 1.5×4H ATR 上方 · 74.6 pips · $""" + str(POS["risk_rest"]) + """ · """ + str(POS["risk_rest_pct"]) + """%）—— 空单 SL 必须在现价上方</td></tr>
<tr><td>执行时机</td><td>① 立即补挂 SL """ + str(POS["sl_new"]) + """ → ② 保留 TP 109.781 → ③ 09-17 00:00（FOMC 前 2h）未触 TP 则<b>主动了结</b> → ④ 09-18 BoJ 落地后 15 分钟再重估</td></tr>
<tr><td>计划失效条件</td><td>① 1H 收盘站上 <b>111.00</b> → 短线多头确认, 提前了结；② BoJ 意外不加息 → 放弃全部空头思路, 观望 24h 重估；③ 跳空越过 SL → 市价单立即离场不等待</td></tr>
<tr><td>备注</td><td>剩余风险 """ + str(POS["risk_rest_pct"]) + """% 合规 ≤1%；已实现 +$""" + str(POS["part_pnl"]) + """ 落袋 = 本轮套息平仓主浪已兑现；下一笔严格按 0.5% 口径</td></tr>
</table></div>
<div class="sub-title">15.3 其余 9 标的判定</div>
<table><tr><th style="width:14%">标的</th><th style="width:14%">判定</th><th>理由</th></tr>""" + o8_rows + """</table>
<div class="verdict" style="margin-top:14px"><b>今日总判定</b><br>
<b>【今日无新仓】</b> —— 全场唯一动作是<b>管理 AUDJPY 剩余 0.01 手空单</b>（情景 A：补挂保护性 SL 111.30 + 保留 TP + FOMC 前未达则主动了结）。理由：① <b>评分</b> 10 标的中最高仅 AUDJPY 65.30 分 / USDKRW 59.90 分, 均 &lt; 75 建仓线；② <b>事件</b> Fed+BoE+BoJ 三央行挤在 48h 内, 全程处于预静默期；③ <b>赔率</b> 剩余 R:R 1.04 勉强及格；④ <b>凯利</b> 新开仓理论手数 0.0052 手 &lt; 最小手, 属「不可交易」。<br>
<b class="yellow">韩元（USDKRW）专项</b>：4H 三周期多头排列 + MACD 柱持续放大 → 趋势明确向上；但 RSI 78.91 / STOCH 90.07 <b class="red">双超买</b> + 站上回归通道上轨 1355.49, 属「强趋势·位置差」；叠加美韩利差由 0.625pp 走阔至 0.875pp（韩元结构性承压）→ <b class="yellow">纳入框架持续监控, 本日不参与, 不追多不抄顶</b>。<br>
<b>空仓即结论, 错过即纪律。</b></div>
</div>"""

# ===================== ⑯ 引用与依据 =====================
sec16 = """<div class="section"><div class="section-title">📚 十八、引用与依据</div>
<table><tr><th>数据</th><th>源</th><th>截至</th></tr>
<tr><td>实时报价(XAU/XAG/EUR/GBP/USDJPY/OIL/AUDJPY/USDKRW)</td><td>金十快讯 / AllRatesToday / Twelve Data / 新浪</td><td>2026-09-16 15:35-15:45 CST</td></tr>
<tr><td>AUDJPY 基准价 110.554 · USDKRW 1364.38</td><td>Twelve Data 日线最后收盘</td><td>2026-09-16（TD 直连, 200 根）</td></tr>
<tr><td>利率曲线(DGS3M/2Y/5Y/10Y/30Y/TIPS/盈亏平衡/2s10s)</td><td>FRED + 金十（10Y 4.97% / 30Y 5.34% 高位）</td><td>2026-09-14/15（FRED 最新观测）</td></tr>
<tr><td>央行政策利率（Fed 3.625 / ECB 2.25 / BoJ 1.00 / BoE 3.75 / RBA 4.35 / BoK 3.00）</td><td>BIS WS_CBPOL + 金十快讯 + BoK 会议纪要</td><td>2026-09-16</td></tr>
<tr><td>Fed 加息定价 92%（CME FedWatch 口径）</td><td>金十快讯 / CME 定价转载</td><td>2026-09-15（前日, 决议前沿用）</td></tr>
<tr><td>地缘与原油（中东/红海/OPEC）</td><td>金十快讯 / Reuters / EIA</td><td>2026-09-16</td></tr>
<tr><td>持仓拥挤度（GOLD / WTI / JPY / AUD / KRW）</td><td>CFTC COT</td><td>2026-09-01 / 08-25（日元净空 28.43% 分位）</td></tr>
<tr><td>日K线（7 标的：XAUUSD/EURUSD/GBPUSD/USDJPY/AUDUSD/AUDJPY/USDKRW）</td><td>Twelve Data（kline_fetch.py 直连）</td><td>2026-02-28 至 2026-09-16（各 200 根）</td></tr>
<tr><td>韩国专项（BoK 加息路径 / KOSPI / 韩元贬幅）</td><td>金十快讯 / 韩国央行会议纪要</td><td>2026-09-15</td></tr>
<tr><td>USDKRW 多周期（4H / 1H / 15min）技术指标</td><td>本次实测抓取（EMA/MACD/RSI/STOCH/通道/布林/ATR）</td><td>2026-09-16</td></tr>
<tr><td>缺失数据标注</td><td>XAGUSD / USOIL 日K（Twelve Data 404 · 源不支持该符号）</td><td>标注「数据缺失」, 报价改用金十</td></tr>
</table></div>"""

# ===================== ⑰ 交易决策日志 =====================
sec17 = """<div class="section"><div class="section-title">📓 十六、交易决策日志</div>
<div class="card-sub" style="margin-bottom:10px">每笔交易完成后填写此日志, 积累 20 笔后统计信号胜率, 找出真正擅长的模式。没有日志的交易 = 赌博。</div>
<div class="card"><div class="card-title">📋 本笔日志 · AUDJPY 空单 #12（部分平仓 + 剩余持仓中）</div>
<table class="journal-table">
<tr><th style="width:18%">项目</th><th>内容</th></tr>
<tr><td>交易标的</td><td class='white'>AUDJPY</td></tr>
<tr><td>方向 / 手数</td><td><span class='red'>SELL """ + str(POS["lots_open"]) + """ 手</span> → <b class='yellow'>2026-09-15 于 110.20 平仓 """ + str(POS["part_lot"]) + """ 手</b> → 剩余 <b class='yellow'>""" + str(POS["lots_now"]) + """ 手持仓</b></td></tr>
<tr><td>入场价 / 时间</td><td>114.573 / 2026-09-02 (凌晨)</td></tr>
<tr><td>止损 / 止盈</td><td>原 SL 113.284（<span class='red'>位于获利区 · 非保护</span>）→ <b class='yellow'>本次补挂保护性 SL """ + str(POS["sl_new"]) + """</b> / TP """ + str(POS["tp"]) + """（保留挂单）</td></tr>
<tr><td>入场核心理由 (3条)</td><td>① W/D/4H 三周期共振空头排列 (技术面)<br>② BoJ 加息预期 vs 澳洲按兵不动 (宏观方向)<br>③ Hurst """ + str(round(h_abs,2)) + """ 强趋势 + OTC 经历转折 (量化/情绪面)</td></tr>
<tr><td>入场时信心指数</td><td><b class='green'>8/10</b> — 三周期 + 宏观双确认</td></tr>
<tr><td>入场时情绪状态</td><td>冷静 / 按计划执行 ✓</td></tr>
<tr><td>结果 / R 倍数</td><td class='green'>已实现 +""" + str(POS["part_pips"]) + """ pips = <b>+$""" + str(POS["part_pnl"]) + """</b> = <b>+""" + str(round(POS["part_pips"] / R_UNIT_PIPS, 2)) + """R</b>（占净值 +""" + str(round(POS["part_pnl"] / ACC["equity"] * 100, 2)) + """%）<br>剩余浮盈 +""" + str(round(_pips,1)) + """ pips = +$""" + str(ACC["floating"]) + """（+""" + str(round(_pips / R_UNIT_PIPS, 2)) + """R, 未实现）</td></tr>
<tr><td>当前状态</td><td><b class='yellow'>部分持仓中</b> — 剩余 0.01 手（最小手）· 确认保护 SL 111.30 · 剩余 R:R 1.04</td></tr>
<tr><td>离场复盘（明确）</td><td>① <b>正确</b>: 在 110.20 主动平仓 0.01 手, 在 TP 触发前就把一半利润落袋, 并在超级央行周前把暴露从 0.02 手降至 0.01 手 = <b>教科书式的部分止盈</b>;<br>② <b>不足</b>: 剩余 0.01 手未同步补挂保护性 SL, 原 SL 113.284 位于获利区已实质失效 → 存在「裸持过三央行」的窗口风险;<br>③ <b>教训</b>: 下次分批平仓时, <b>必须同时重设剩余仓位的保护性止损</b>, 不能只平不设。</td></tr>
<tr><td>情绪记录（平仓后）</td><td>平静 / 无「落袋后追单」冲动 ✓ — 已实现 +$""" + str(POS["part_pnl"]) + """ 立即计入净值, 但不因账户变厚而放大下一笔风险; 下一笔仍按 <b>0.5%</b> 口径。</td></tr>
</table></div></div>"""

# ===================== ⑱ 信号历史回测 =====================
bt_rows = ""
for num, dt, sym, dr, en, ex, pips, rmult, res in BT_SIGNALS:
    rcls = "green" if rmult.startswith("+") else "red"
    rescls = "green" if res == "止盈" else ("red" if res == "止损" else "yellow")
    drcls = "red" if dr == "SELL" else "green"
    bt_rows += ("<tr><td>" + num + "</td><td>" + dt + "</td><td class='white'>" + sym + "</td>"
                "<td class='" + drcls + "'>" + dr + "</td><td>" + en + "</td><td>" + ex + "</td>"
                "<td class='" + rcls + "'>" + pips + "</td><td class='" + rcls + "'>" + rmult + "</td>"
                "<td class='" + rescls + "'>" + res + "</td></tr>")
sec18 = """<div class="section"><div class="section-title">📈 十七、信号历史回测（样本有限 · 仅供参考）</div>
<div class="card-sub" style="margin:2px 0 10px;color:#8a9bc0">⏱ 回测样本截至: AUDJPY 日线 60 根窗口, 末根 2026-09-16（与第八节日K同源）</div>
<div class="card-sub" style="margin-bottom:10px">基于 AUDJPY 60 根日线, 回测「W/D 定方向 + 1H 定时机 + Hurst 过滤」策略的历史表现。注意: <b class='yellow'>样本量有限 (~12 笔信号)</b>, 结果仅供参考, 不作为收益承诺。</div>
<div class="two-col">
<div class="card"><div class="card-title">📊 策略整体表现</div>
<div class="backtest-metric"><span class="backtest-label">总交易次数</span><span class="backtest-value">""" + str(BT["n"]) + """ 笔</span></div>
<div class="backtest-metric"><span class="backtest-label">盈利 / 亏损</span><span class="backtest-value"><span class='green'>""" + str(BT["win"]) + """ 胜</span> / <span class='red'>""" + str(BT["loss"]) + """ 负</span></span></div>
<div class="backtest-metric"><span class="backtest-label">胜率</span><span class="backtest-value green">""" + str(BT["winrate"]) + """%</span></div>
<div class="backtest-metric"><span class="backtest-label">平均盈亏比</span><span class="backtest-value">""" + str(BT["pl"]) + """ : 1</span></div>
<div class="backtest-metric"><span class="backtest-label">期望值 (每笔R)</span><span class="backtest-value green">+""" + str(BT["exp"]) + """ R</span></div>
<div class="backtest-metric"><span class="backtest-label">最大连胜</span><span class="backtest-value">""" + str(BT["max_win_streak"]) + """ 次</span></div>
<div class="backtest-metric"><span class="backtest-label">最大连败</span><span class="backtest-value">""" + str(BT["max_loss_streak"]) + """ 次</span></div>
<div class="backtest-metric"><span class="backtest-label">最大回撤</span><span class="backtest-value red">-""" + str(BT["max_dd"]) + """ R</span></div>
<div class="backtest-metric"><span class="backtest-label">利润因子</span><span class="backtest-value green">""" + str(BT["pf"]) + """</span></div>
</div>
<div class="chart-box" style="margin-bottom:0"><div class="chart-title">💰 资金曲线（R 乘数）</div><div id="rcurve" class="chart-small"></div></div>
</div>
<div class="sub-title">近期信号明细（最近 6 笔）</div>
<table>
<tr><th>#</th><th>时间</th><th>标的</th><th>方向</th><th>入场价</th><th>出场价</th><th>盈亏(pips)</th><th>R倍数</th><th>结果</th></tr>
""" + bt_rows + """
</table>
<div class="sub-title">📋 回测结论与系统优化方向</div>
<div class="grid grid-4">
<div class="card"><div class="card-title">✅ 策略有效</div><div class="card-sub" style="line-height:1.8">1. 胜率 66.7% + 盈亏比 1.85 → 期望值 <b>+0.56R/笔</b>, 正期望系统<br>2. 利润因子 <b>2.62</b>, 远高于 1.5 的合格线<br>3. 最大连败仅 2 次, 心理压力可控</div></div>
<div class="card"><div class="card-title">⚠️ 需要警惕</div><div class="card-sub" style="line-height:1.8">1. 12 笔样本量不足, 真实胜率可能在 50-80% 区间波动<br>2. 黄金样本极少 (仅 1 笔), 不能据此评估黄金信号<br>3. 当前处于紧缩 Regime, 空头信号表现优于多头, Regime 切换后需重新验证<br>4. #12 由「全量止盈 +3.72R」修正为「部分平仓 <b>+3.39R</b> + 剩余持仓中」, 统计口径同步调整</div></div>
<div class="card"><div class="card-title">🔧 优化方向</div><div class="card-sub" style="line-height:1.8">1. 加入 Hurst &gt; 0.7 过滤 → 可剔除震荡市假信号<br>2. 加入 CFTC 拥挤度反向过滤 → 避开极端拥挤区<br>3. 只做三周期完全共振 → 牺牲交易次数换更高胜率<br>4. 趋势尾部<b>分批平仓 + 剩余必挂保护 SL</b> → #12 已验证「分批」有效, 但暴露了「只平不设」的缺口, 下一次须两步同做</div></div>
<div class="card"><div class="card-title">📅 长期预测（v2.4 已封禁）</div><div class="card-sub" style="line-height:1.8">1. 当前样本 <b>12 笔 &lt; 100 笔</b> → <b class="red">禁止给出年化收益预测</b><br>2. 仅可报告已实现统计: 胜率 66.7% / 盈亏比 1.85 / 期望 +0.56R / 利润因子 2.62<br>3. 需补齐 ≥100 笔, 且完成样本外 + Walk-forward + 蒙特卡洛 + Regime 分层后才可外推<br>4. 点差 / 滑点 / 隔夜利息尚未逐笔计入, 当前期望值存在高估风险</div></div>
</div></div>"""

# ===================== ⑲ 交易纪律 =====================
disc_cards = ""
for cat, items in DISCIPLINE6:
    lis = "".join(["<li>" + i + "</li>" for i in items])
    disc_cards += ('<div class="discipline-item"><h4>📌 ' + cat + '</h4><ol>' + lis + '</ol></div>')
sec19 = """<div class="section"><div class="section-title">🛡️ 二十、交易纪律（永远置末）</div>
<div class="discipline"><h3>🔥 最核心铁律: 「风控第一, 盈利第二; 纪律第一, 机会第二」</h3>
<div class="card-sub" style="color:#e8d0a0;margin-bottom:12px">本笔 AUDJPY 已于 110.20 <b>部分平仓 0.01 手</b>（已实现 <b>+$""" + str(POS["part_pnl"]) + """</b> = +""" + str(round(POS["part_pips"] / R_UNIT_PIPS, 2)) + """R, 不可回吐）; 剩余 0.01 手须<b class="yellow">补挂保护性 SL """ + str(POS["sl_new"]) + """</b>（74.6 pips · $""" + str(POS["risk_rest"]) + """ · 剩余风险 """ + str(POS["risk_rest_pct"]) + """% 合规 ≤1%）。今日唯一正确动作是「<b>补挂保护止损 + FOMC 前不新增 + 残余段事件前主动了结</b>」——把不确定性从「整笔」压缩到「残余段」。</div>
<div class="discipline-grid">""" + disc_cards + """</div></div></div>"""

# ===================== 补齐冻结模板三节（四·补 / 六·补 / 十九） =====================
_SEC04B = XS.sec04b()
_SEC06B = XS.sec06b()
_SEC20 = XS.sec20()

# ===================== 汇总拼装 =====================
# 顺序严格对齐冻结模板：1,2,3,4,四·补,5,6,六·补,7,8,9,10,11,12,13,14,15,16,17,18,19,20
# v2.5.6 授权调准③: 校验报告编号 二十→十九, 交易纪律编号 十九→二十（顺序不变, 纪律仍置末）
html += (sec01 + sec02 + sec03 + sec04 + _SEC04B + sec05 + sec06 + _SEC06B
         + sec07 + sec08 + sec09 + sec10 + sec11 + sec12 + sec13 + sec14
         + sec15 + sec17 + sec18 + sec16 + _SEC20 + sec19)

html += """<div class="footer">kingforex-skill v2.5.6 决策增强版｜ 基准 """ + NOW + """ ｜ 数据溯源见⑱ ｜ 本分析仅供决策参考, 不代客下单, 不自动交易</div>
</div>
<script>
""" + "\n".join(charts_js) + """
echarts.init(document.getElementById('scorechart')).setOption(""" + json.dumps(score_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('corr')).setOption(""" + json.dumps(corr_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('cross')).setOption(""" + json.dumps(cross_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('radar_aj')).setOption(""" + json.dumps(radar_aj_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('radar_krw')).setOption(""" + json.dumps(radar_krw_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('equity')).setOption(""" + json.dumps(equity_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('stopcmp')).setOption(""" + json.dumps(stop_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('rcurve')).setOption(""" + json.dumps(rcurve_opt, ensure_ascii=False) + """);
</script></body></html>"""

# ===================== v2.5.2 改动: (A) §九 量化验证改为分标的独立雷达(不叠加)  (B) 引擎三处补丁(v2.5.1 已实现, 此处沿用) =====================
# ① 凯利使用注意事项 → 迁入左侧卡片红框区（删除节底原块）
html, _n3 = V25.patch_kelly_notes(html, symbol="AUDJPY", loss05=RISK_REST, lots05=POS_LOTS)
print("[CHG 3] 凯利使用注意 → 左卡红框区:", "OK" if _n3 else "FAIL")

# ② ⑪·补 仓位多角度评估与最终仓位选择（插在凯利节之后、相关性节之前）
_pos = V25.evaluate_position(
    ACC_EQUITY, _to_sl, _pip_val,
    KELLY["p"] / 100.0, KELLY["b"],
    event_silent=True,
    event_name="FOMC 09-17 02:00 + BoE 09-17 19:00 + BoJ 09-18 10:00（超级央行周）",
    atr=a_atr, pip=0.01,
)
_pos["symbol"] = "AUDJPY"
_pos["direction"] = "SELL"
_pos_block = V25.render_position_section(
    _pos,
    subtitle=("评估对象 <b class='white'>AUDJPY SELL</b>（实盘剩余 <b class='yellow'>0.01 手</b>，已于 110.20 部分平仓 0.01 手）· "
              "账户净值 $%.2f · 参考止损距离 %.1f pips · 每 0.01 手每 pip $%.4f ｜ "
              "本节从六个独立角度评估<b>新开仓</b>的理论上限；对<b>已持有的最小手仓位</b>，"
              "管理动作为「补挂保护性 SL 111.30 + 保留 TP 109.781」，详见 ⑭·补。"
              % (ACC_EQUITY, _to_sl, _pip_val)))
html, _n4 = V25.patch_position_angles(html, _pos_block)
print("[CHG 4] ⑪·补 仓位多角度评估块注入:", "OK" if _n4 else "FAIL",
      "| 六角度:", {k: round(v, 4) for k, v in _pos["angles"].items()},
      "| 最终:", _pos["final_lots"], "手 (约束=%s)" % _pos["binding"])

# ③ ⑭·补 止损止盈合理性评估（插在十五节之前）—— 以「原 SL」评估以暴露历史缺陷
_sltp = V25.evaluate_sl_tp("SELL", POS["entry"], POS["sl_orig"], POS["tp"], POS["cur"],
                           "AUDJPY", ACC_EQUITY, POS["lots_now"],
                           usdjpy=USDJPY_RATE, atr=a_atr, pip=0.01)
_sltp_block = V25.render_sl_tp_section(_sltp)
_sltp_note = ('<div class="card-sub" style="margin-bottom:10px">'
              '口径说明：本节<b>以账户实际挂单的原 SL 113.284 为参数</b>评估，用于暴露历史缺陷'
              '（SL 位于入场价下方 = 获利区 · 非保护性 → 引擎标记 severe 级 SL_REVERSED）。'
              '若按保护性<b class="yellow">SL 111.30</b> 重算：距现价 <b>74.6 pips</b>、'
              '剩余 R:R = 77.3 / 74.6 = <b class="yellow">1.04</b>（勉强及格）、'
              '单笔风险 $4.82 = 净值 <b class="green">0.80%</b>（在 1% 硬上限内 ✓）。'
              '两个口径共同指向同一结论：<b class="red">残余段赔率不合格，必须补挂保护性止损或于事件前主动了结。</b></div>')
_sltp_block = _sltp_block.replace(
    '<div class="section-title">🛡️ 十四·补、止损止盈合理性评估（引擎判定）</div>',
    '<div class="section-title">🛡️ 十四·补、止损止盈合理性评估（引擎判定）</div>' + _sltp_note, 1)
html, _n2 = V25.patch_sl_tp_section(html, _sltp_block)
print("[CHG 2] ⑭·补 止损止盈评估节注入:", "OK" if _n2 else "FAIL",
      "| 判定: %s | initRR=%.2f restRR=%.2f | 浮盈 %+.1f pip = $%.2f"
      % (_sltp["verdict"], _sltp["init_rr"], _sltp["rest_rr"], _sltp["pl_pips"], _sltp["pl_usd"]))

path = os.path.join(OUT, "今日行情分析_决策增强版_v2.5.6_2026-09-16.html")
open(path, "w", encoding="utf-8").write(html)
_cdn_after = html.count("cdn.jsdelivr.net")
print("HTML written:", path, len(html), "bytes | charts:", len(charts_js), "| CDN refs:", _cdn_after)

# ===================== MD 双版本 (19节新顺序 · 10标的) =====================
md = []
md.append("# 今日行情分析 · 决策增强版 v2.5.6")
md.append("> 基准时间: **" + NOW + "** ｜ kingforex-skill ｜ 10 标的（含韩元 USDKRW 正式纳入框架）｜ 数据溯源见第十六节")
md.append("")
md.append("## 一、今日决策总览")
md.append("| 账户状态 | 信号质量 | 凯利最优仓位 | 今日最大风险 |")
md.append("| :--- | :--- | :--- | :--- |")
md.append("| **$" + str(ACC["equity"]) + "** (浮盈+$" + str(ACC["floating"]) + ") | **B+** (10标的加权) | **" + str(KELLY["rec_lots"]) + "手** (f*=" + str(int(KELLY["f"])) + "%) | **Fed ★★★★★** (09-17 加息92%) |")
md.append("| 持仓风险/上限5% | 可交易1个·观望/关注8个 | 当前" + str(POS["lots_open"]) + "手超配" + str(KELLY["over"]) + "%→减至" + str(POS["lots_now"]) + "手 | ±50-80pips·FOMC前收紧SL |")
md.append("")
md.append("## 二、今日交易计划（建仓 / 持仓判定）")
md.append("**【建仓判定：今日不适宜建仓 —— 不建仓】** 理由(四维一致否决): ①宏观(FOMC议息+10Y逼5%); ②评分(10标的均<75); ③凯利(新开仓=0); ④拥挤度(黄金89%/WTI97%)。**空仓即结论, 错过即纪律。**")
md.append("")
md.append("**2.1 持仓计划（现有持仓 · AUDJPY 0.01手空单）**")
md.append("| 项目 | 内容 |")
md.append("| :--- | :--- |")
md.append("| 交易标的 | AUDJPY |")
md.append("| 方向/手数 | SELL " + str(POS["lots_open"]) + "手 |")
md.append("| 入场价/时间 | 114.573 / 2026-09-02(凌晨) |")
md.append("| 止损/止盈 | 原SL 113.284→新SL " + str(POS["sl_new"]) + " / TP " + str(POS["tp"]) + " |")
md.append("| 入场核心理由 | ①W/D/4H三周期共振空头排列; ②BoJ加息预期vs澳洲按兵不动; ③Hurst" + str(round(h_abs,2)) + "强趋势+OTC转折 |")
md.append("| 入场信心指数 | 8/10(三周期+宏观双确认) |")
md.append("| 入场情绪状态 | 冷静/按计划执行✓ |")
md.append("| 最大/当前浮盈 | +" + str(round(_pips,1)) + "pips / +$" + str(ACC["floating"]) + "(+" + str(POS["pct"]) + "%) |")
md.append("| 当前状态 | 持仓中·减仓区间(已走75%预期幅度) |")
md.append("| 离场计划 | ①**补挂保护性SL " + str(POS["sl_new"]) + "**(74.6pips/$" + str(POS["risk_rest"]) + "/" + str(POS["risk_rest_pct"]) + "%); ②保留TP 109.781不动; ③09-17 00:00(FOMC前2h)未触TP则主动了结; ④1H收盘站上111.00提前了结 |")
md.append("| 可能出错 | ①FOMC超预期致USD反弹→已收紧SL控风险; ②日央行干预→SL已收" + str(POS["sl_new"]) + "; ③流动性枯竭跳空→接受滑点不追 |")
md.append("")
md.append("## 三、分析标的快照（现价/日内%/区间/结构/MTF/计划判定 · 10标的）")
md.append("| 标的 | 现价 | 日内% | 日内区间 | 趋势/结构 | MTF方向 | 计划判定 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
for s in SNAP_LIST:
    px, pct, rng = snap_metrics(s); ex = SNAP_EXTRA[s]
    md.append("| " + s + " | " + str(px) + " | " + pct + " | " + rng + " | " + ex["struct"] + " | " + ex["mtf"] + " | " + ex["plan"] + " |")
md.append("")
md.append("> " + DAY_THEME.replace("<b class='yellow'>", "**").replace("</b>", "**"))
md.append("")
md.append("## 四、10标的综合评分卡（≥75可建仓）")
md.append("| 品种 | 宏观 | 技术 | 量化 | 情绪 | 综合 | 判定 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
for s in SNAP_LIST:
    d = SCORES[s]; tot = round(d["macro"]*0.25+d["tech"]*0.30+d["quant"]*0.25+d["sent"]*0.20)
    md.append("| " + s + " | " + str(d["macro"]) + " | " + str(d["tech"]) + " | " + str(d["quant"]) + " | " + str(d["sent"]) + " | **" + str(tot) + "** | " + d["verdict"] + " |")
md.append("")
md.append("## 五、宏观金融面")
md.append("**5.1 央行政策对比表（BIS / 金十快讯 · 2026-09-16）**")
md.append("| 央行 | 政策利率 | 最近动作 | 周期定位 | 对市场 |")
md.append("| :--- | :--- | :--- | :--- | :--- |")
for bank, rate, action, cyc, cyccls, impact in CB_POLICY:
    md.append("| " + bank + " | " + rate + " | " + action + " | " + cyc + " | " + impact + " |")
md.append("")
md.append("- **5.2 利率地基**(FRED截至09-14; 盘中10Y=4.98%): DGS10=4.83% / DFII10(实际)=2.46% / T10YIE=2.40% / 2s10s=0.39% / FEDFUNDS=3.63%")
md.append("")
md.append("**5.3 利差结构（套息交易视角）**")
md.append("| 利差对 | 当前值 | 趋势 | 解读 |")
md.append("| :--- | :--- | :--- | :--- |")
for pair, val, trend, note in CARRY2:
    md.append("| " + pair + " | " + val + " | " + trend + " | " + note + " |")
md.append("> 🔥 结论: 套息结构仍为正(澳日 3.35% → BoJ 加息后 3.10%), 但方向由「利差收益」切换为「平仓冲击」——**BoJ 09-18 加息 25bp(→1.25%)是日元交叉盘最大反向变量**, 本轮已兑现为 AUDJPY 于 110.20 部分平仓 **+437.3 pips = +$28.22**; Fed 加息 92% → 美日利差走阔至 +2.875pp, USDJPY 154.92 高位。**美韩利差同步走阔至 +0.875pp → 韩元承压但已伴 4H 双超买, 只可顺势不可追高。**")
md.append("")
md.append("**5.4 地缘 + 风险偏好**")
for title, body in GEO_RISK:
    md.append("- **" + title + "**: " + body)
md.append("")
md.append("**5.5 宏观大事综合（每标 2 条 · 明确影响 · 10标的）**")
import re as _re
for sym, events in MACRO2:
    txt = _re.sub(r"<[^>]+>", "", events)
    md.append("- 【" + sym + "】" + txt)
md.append("")
md.append("## 六、当日数据 + 议息")
md.append("**6.1 ✅ 近期已公布**")
md.append("| 时间 | 数据 | 实际 | 预期 | 前值 | 影响 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
for t, ev, act, exp, prev, impact, icls in CAL_PUB:
    md.append("| " + t + " | " + ev + " | " + act + " | " + exp + " | " + prev + " | " + impact + " |")
md.append("")
md.append("**6.2 🔴 待公布（关键 · FOMC进行中）**")
md.append("| 时间 | 事件 | 预期 | 前值 | 星级 | 影响路径 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
for t, ev, exp, prev, star, path, hl in CAL_PENDING:
    md.append("| " + t + " | " + ev + " | " + exp + " | " + prev + " | " + star + " | " + path + " |")
md.append("")
md.append("**6.3 📌 本月议息与数据提醒**")
md.append("| 日期 | 事件 | 重要性 | 预期 | 对操作 |")
md.append("| :--- | :--- | :--- | :--- | :--- |")
for dt, ev, imp, exp, act in CAL_MONTH:
    md.append("| " + dt + " | " + ev + " | " + imp + " | " + exp + " | " + act + " |")
md.append("> ⚠ 事件纪律: FOMC 决议前 4 小时不开任何新仓; 已有持仓决议前完成减仓/收紧 SL; 决议公布后等第一波方向走完（≥15分钟）再评估, 不追第一根 K 线。")
md.append("")
md.append("## 七、跨市场验证")
md.append("- 黄金vs实际利率(负向,2.46%高位压制); 原油vs中东(97%拥挤警惕回落); AUDJPYvs美日利差(套息3.35%支撑); USDJPYvs10Y(同向偏多); 韩元(USDKRW)vs美元/美债(BoJ加息推升韩元, USDKRW偏空, 与日元同向)。宏观与跨市场未给出低不确定共振方向, FOMC前谨慎。")
md.append("")
md.append("## 八、多周期共振 + 关键位")
md.append("- 7标的日K图见HTML版(含AUDJPY入场/SL/TP/当前标记, USDKRW当前/52周低标记); XAGUSD/USOIL Twelve Data 404/iTick限频, 按铁律不编造价格。")
md.append("| 品种 | 关键位 | 类型 | 作用 |")
md.append("| :--- | :--- | :--- | :--- |")
for v, kl, tp, act in keylevels:
    md.append("| " + v + " | " + kl + " | " + tp + " | " + act + " |")
md.append("")
md.append("## 九、量化验证（AUDJPY样本 + 韩元补充）")
md.append("- AUDJPY: |Hurst|=" + str(round(h_abs,2)) + "(趋势型>0.55利于持仓) ｜ |Z|=" + str(round(z_abs,2)) + " ｜ 年化|Sharpe|=" + str(round(sh_abs,2)) + " ｜ |Sortino|=" + str(round(so_abs,2)) + " ｜ |偏度|=" + str(round(sk_abs,2)) + " ｜ 日VaR95%=" + str(round(var95,2)) + "%")
md.append("- 韩元(USDKRW)专项: 4H **EMA5 1356.67 > EMA10 1352.19 > EMA60 1347.73 标准多头排列** + MACD 柱 **+2.143 放大** + 站上回归通道上轨 **1355.49** → 短线强势; 但 RSI(4H) **78.91** / STOCH **90.07/89.11** 双超买。Z=-0.97(60日均值下方) / Z=+0.45(近20日) → 「中期修复+短线强+位置超买」, **追多赔率不合格, 等回踩 1350 或事件落地后重估。**")
md.append("")
md.append("## 十、AUDJPY 持仓 · 三情景预案")
md.append("| 情景 | 概率 | 触发路径 | 操作 | 预期结果 |")
md.append("| :--- | :--- | :--- | :--- | :--- |")
md.append("| 🐻 A. 双向加息落地·日元略占优(基准) | ~45% | Fed 09-17 加息25bp落地(92%定价)+点阵图偏鹰, 但 BoJ 09-18 如期加息至1.25% → 双向对冲后日元略占优+套息平仓延续 → AUDJPY 下探 109.781(TP) | 补挂SL " + str(POS["sl_new"]) + " → 保留TP挂单 → TP 触发自动全平 | 剩余 +77.3 pips = +$4.99 |")
md.append("| 🐂 B. FOMC鸽派信号 | ~40% | 点阵图偏鸽→美债↓→AUDJPY回踩110.82-111.30 | 1H收复110.82→剩余" + str(POS["lots_now"]) + "手全平(接受+$" + str(round(POS_PNL*0.5,2)) + ") | 总利润+$14~+$20 |")
md.append("| ⚡ C. FOMC大超预期+日元干预(尾部) | ~15% | 加息+干预→双向扫损 | SL " + str(POS["sl_new"]) + "触发→市价离场不补仓不反手→观望24h | 最大损失-$" + str(POS["risk_rest"]) + "(" + str(POS["risk_rest_pct"]) + "%) |")
md.append("")
md.append("## 十一、凯利仓位计算器（全标的适配）")
md.append("- 公式: **f*=(p×b−q)/b** ｜ 实战用半凯利(f*/2) ｜ **投资标的下拉**: AUDJPY/USDJPY/EURUSD/GBPUSD/XAUUSD/XAGUSD/USOIL/USDKRW(关注) 全标的自动代入 pip 价值与参考止损距离")
md.append("- AUDJPY回测: p=" + str(KELLY["p"]) + "% ｜ b=" + str(KELLY["b"]) + " ｜ f*=" + str(KELLY["f"]) + "% ｜ 半凯利=" + str(KELLY["f_half"]) + "% ｜ 三分之一=" + str(KELLY["f_third"]) + "%")
md.append("- 本账户: 最优" + str(KELLY["f_half"]) + "% ｜ 最大可亏$" + str(KELLY["max_loss"]) + " ｜ 推荐" + str(KELLY["rec_lots"]) + "手 ｜ 当前" + str(POS["lots_open"]) + "手**超配" + str(KELLY["over"]) + "%**→减至" + str(POS["lots_now"]) + "手")
md.append("")
md.append("## 十二、相关性热力图 + 解读（7标的）")
md.append("- 高度正相关: XAU↔XAG 0.92 / EUR↔GBP 0.85 / AUDJPY↔USDJPY -0.78 / USDKRW↔USDJPY 0.71; 低相关: USOIL↔AUDJPY 0.12 / XAU↔EUR 0.35 / DXY↔XAU -0.68 / USDKRW↔XAU -0.41")
md.append("- 组合诊断: AUDJPY空单1笔, 集中度低; 隐含暴露=日元走强+澳元走弱; 韩元(USDKRW)与日元正相关0.71, 同属亚太套息货币; 做多日元优先AUDJPY(方向更纯)")
md.append("")
md.append("## 十三、账户风险仪表盘")
md.append("- 净值$" + str(ACC["equity"]) + "(入金$" + str(int(ACC["deposit"])) + "+浮盈$" + str(ACC["floating"]) + ",累计+" + str(ACC["cum_ret"]) + "%) ｜ 单笔风险$" + str(POS["risk_usd"]) + "(剩余" + str(POS["lots_now"]) + "手@SL" + str(POS["sl_new"]) + ")=" + str(POS["risk_rest_pct"]) + "%合规 ｜ 组合风险$" + str(POS["risk_usd"]) + " ｜ 最大回撤" + str(ACC["max_dd"]) + "%(安全区)")
md.append("- ⚠️ 风险预警: 本笔已收紧SL至" + str(POS["sl_new"]) + ", 剩余风险" + str(POS["risk_rest_pct"]) + "%已合规≤1%; FOMC决议前不新增仓位。")
md.append("")
md.append("## 十四、动态止损方案对比")
md.append("| 方案 | ATR止损 | 结构止损 | 移动止损(推荐★) |")
md.append("| :--- | :--- | :--- | :--- |")
md.append("| 止损位 | " + STOPS["atr"]["lvl"] + " | " + STOPS["struct"]["lvl"] + " | " + STOPS["trail"]["lvl"] + " |")
md.append("| 止损距离 | " + STOPS["atr"]["dist"] + " | " + STOPS["struct"]["dist"] + " | " + STOPS["trail"]["dist"] + " |")
md.append("| 单笔风险 | $" + str(STOPS["atr"]["risk"]) + " | $" + str(STOPS["struct"]["risk"]) + " | 递减中 |")
md.append("| 被扫概率 | ~" + str(STOPS["atr"]["sweep"]) + "% | ~" + str(STOPS["struct"]["sweep"]) + "% | 随趋势下降 |")
md.append("| 保住利润 | 少 | 中 | 多 |")
md.append("| 适用场景 | " + STOPS["atr"]["scene"] + " | " + STOPS["struct"]["scene"] + " | " + STOPS["trail"]["scene"] + " |")
md.append("- 💡 最终推荐: **① 立即补挂保护性 SL " + str(POS["sl_new"]) + "**(74.6pips/$" + str(POS["risk_rest"]) + "/" + str(POS["risk_rest_pct"]) + "%); ② 保留 TP 109.781 不动; ③ 1H 收盘站上 111.00 或 FOMC 前 2h 未触 TP → 主动了结; ④ 触及 SL → 市价离场不补仓不反手。**残余段目标不是「多赚」, 而是「把已兑现利润锁死、把剩余暴露钉死」。**")
md.append("")
md.append("## 十五、综合判定与操作建议")
md.append("**15.1 AUDJPY 持仓诊断**: 已实现 +" + str(POS["part_pips"]) + " pips = +$" + str(POS["part_pnl"]) + " ｜ 剩余浮盈 +" + str(round(_pips,1)) + " pips = +$" + str(ACC["floating"]) + "(占净值 +" + str(round(ACC["floating"]/ACC["equity"]*100,2)) + "%) ｜ 至TP/至保护SL = " + str(_to_tp) + "/" + str(_to_sl) + " pips → **剩余 R:R 1.04 勉强及格** ｜ 方向 长空短多·分歧 ｜ 事件风险 Fed★★★★★ + BoE★★★★ + BoJ★★★★★(48h 三央行)")
md.append("")
md.append("**15.2 三种情景（按纪律二选一执行，禁止 C 项）**")
md.append("- 🛡️ 情景A（稳健·补挂保护SL + 事件前了结）→ **推荐★**: 立即补挂保护性 SL " + str(POS["sl_new"]) + "(74.6pips, 剩$" + str(POS["risk_rest"]) + "=" + str(POS["risk_rest_pct"]) + "%); 保留 TP 109.781; FOMC 前 2h 未触 TP 则主动了结; 1H 站上 111.00 提前了结")
md.append("- 🛡️ 情景B（鸽派反弹·全平）→ **备选**: FOMC偏鸽→美债↓→AUDJPY回踩110.82-111.30→1H收复110.82即全平(接受+$" + str(round(POS_PNL*0.5,2)) + ")")
md.append("- ⛔ 情景C（硬扛不过滤）→ **不接受**: 持仓不动等TP, 承受FOMC双向扫损(-$" + str(POS["risk_rest"]) + ")")
md.append("")
md.append("**🎯 最终推荐：情景 A（稳健派）—— FOMC 决议前执行完毕**")
md.append("| 项目 | 具体操作 |")
md.append("| :--- | :--- |")
md.append("| 交易标的 | AUDJPY（持有浮盈空单, 非新开仓） |")
md.append("| 方向/手数 | SELL 0.01手 → 维持0.01手（已收紧SL控风险） |")
md.append("| 止盈 | TP1 109.781(-" + str(_to_tp) + "pips) / TP2 109.24(破位延伸) |")
md.append("| 止损 | 新SL " + str(POS["sl_new"]) + "（日线结构上方外扩1点） |")
md.append("| 执行时机 | ①立即补挂 SL " + str(POS["sl_new"]) + " → ②保留TP 109.781 → ③09-17 00:00未触TP则主动了结 → ④09-18 BoJ 落地后15分钟再重估 |")
md.append("| 计划失效条件 | FOMC公布瞬间若跳空越过" + str(POS["sl_new"]) + ", 市价单立即离场不等待 |")
md.append("| 备注 | 已收紧SL, 剩余风险" + str(POS["risk_rest_pct"]) + "%合规≤1%; 下一笔严格0.5%以内 |")
md.append("")
md.append("**15.3 其余 8 标的判定**")
md.append("| 标的 | 判定 | 理由 |")
md.append("| :--- | :--- | :--- |")
for sym, verdict, reason in OTHER8:
    md.append("| " + sym + " | " + verdict + " | " + reason + " |")
md.append("")
md.append("**今日总判定**: 【今日无新仓】—— 全场唯一动作是**管理 AUDJPY 剩余 0.01 手空单**（情景A: 补挂保护性 SL " + str(POS["sl_new"]) + " + 保留 TP + FOMC 前未达则主动了结）。理由: ①评分 10 标的最高仅 65.30 <75 建仓线; ②Fed+BoE+BoJ 三央行挤在 48h; ③剩余 R:R 1.04 勉强及格; ④凯利新开仓理论手数 0.0052 < 最小手 → 「不可交易」。**韩元(USDKRW)专项**: 4H 三周期多头 + MACD 柱放大 = 趋势强, 但 RSI 78.91/STOCH 90.07 双超买 + 美韩利差走阔至 0.875pp = 「强趋势·位置差」→ **纳入框架持续监控, 本日不参与, 不追多不抄顶**。空仓即结论, 错过即纪律。")
md.append("")
md.append("## 十八、引用与依据")
md.append("| 数据 | 源 | 截至 |")
md.append("| :--- | :--- | :--- |")
md.append("| 实时报价 | 金十/sina/Twelve Data/WebSearch | 2026-09-16 15:45 |")
md.append("| 利率曲线 | FRED | 09-14/15 |")
md.append("| 政策利率 | BIS/金十/BoJ公告 | 09-14/15 |")
md.append("| 原油/地缘 | EIA/金十 | 09-14 |")
md.append("| 持仓拥挤度 | CFTC COT | 09-01 / 08-25 |")
md.append("| 日K线 | Twelve Data/Frankfurter/WebSearch | 02至09-15 |")
md.append("")
md.append("## 十六、交易决策日志")
md.append("（同 2.1 持仓计划表, 此处为日志记录版）AUDJPY SELL " + str(POS["lots_open"]) + "手, 入场114.573, 新SL " + str(POS["sl_new"]) + ", TP " + str(POS["tp"]) + ", 浮盈+$" + str(ACC["floating"]) + "(+" + str(POS["pct"]) + "%), 已走75%预期幅度, 按4步离场计划执行。")
md.append("")
md.append("## 十七、信号历史回测（样本有限·仅供参考）")
md.append("- " + str(BT["n"]) + "笔 ｜ " + str(BT["win"]) + "胜/" + str(BT["loss"]) + "负 ｜ 胜率" + str(BT["winrate"]) + "% ｜ 盈亏比" + str(BT["pl"]) + ":1 ｜ 期望+" + str(BT["exp"]) + "R ｜ 回撤-" + str(BT["max_dd"]) + "R ｜ 利润因子" + str(BT["pf"]))
md.append("")
md.append("| # | 时间 | 标的 | 方向 | 入场价 | 出场价 | 盈亏(pips) | R倍数 | 结果 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
for num, dt, sym, dr, en, ex, pips, rmult, res in BT_SIGNALS:
    md.append("| " + num + " | " + dt + " | " + sym + " | " + dr + " | " + en + " | " + ex + " | " + pips + " | " + rmult + " | " + res + " |")
md.append("")
md.append("- 结论: ✅正期望(**+0.56R/笔, 利润因子2.62**); ⚠️样本 12 笔 < 100 → **禁止年化收益预测**; 🔧加 Hurst>0.7 / CFTC 拥挤度过滤; 📅需补齐样本并完成样本外+Walk-forward+蒙特卡洛+Regime分层后才可外推。**#12 统计口径已由「全量止盈+3.72R」修正为「部分平仓 +3.39R + 剩余持仓中」。**")
md.append("")
md.append("## 二十、交易纪律（永远置末）")
md.append("**🔥 最核心铁律: 「风控第一, 盈利第二; 纪律第一, 机会第二」** ｜ 本笔 AUDJPY 已收紧 SL 至 " + str(POS["sl_new"]) + ", 剩余风险 " + str(POS["risk_rest_pct"]) + "% 合规; 今日唯一正确动作是「收紧止损 + FOMC前不新增 + 空仓过议息」。")
md.append("")
for cat, items in DISCIPLINE6:
    md.append("- **" + cat + "**: " + "; ".join(items))
md.append("")
md.append("---")
md.append("kingforex-skill v2.5.6 决策增强版｜ 仅供决策参考, 不代客下单, 不自动交易")
md_path = os.path.join(OUT, "今日行情分析_决策增强版_v2.5.6_2026-09-16.md")
open(md_path, "w", encoding="utf-8").write("\n".join(md))
print("MD written:", md_path, len(md), "lines")

# ===================== 独立 Excel 复盘模板 =====================
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError:
    print("XLSX skipped: 未安装 openpyxl")
    raise SystemExit(0)
wb = Workbook()
blue = "2A5298"
hdr_fill = PatternFill("solid", fgColor=blue)
hdr_font = Font(color="FFFFFF", bold=True, size=11)
title_font = Font(color="1C2541", bold=True, size=14)
thin = Side(style="thin", color="B0B8D0")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center", wrap_text=True)
def style_header(ws, row, ncol):
    for c in range(1, ncol+1):
        cell = ws.cell(row=row, column=c)
        cell.fill = hdr_fill; cell.font = hdr_font; cell.alignment = center; cell.border = border
ws1 = wb.active; ws1.title = "交易复盘记录"
ws1.append(["交易复盘记录表（kingforex-skill v2.3）"]); ws1["A1"].font = title_font; ws1.append([])
cols1 = ["#","日期","品种","方向","手数","入场价","止损SL","目标TP","出场价","盈亏(pips)","盈亏($)","R倍数","结果(止盈/止损/手动)","入场理由(三维)","信心(1-10)","情绪状态","是否按计划","复盘备注"]
ws1.append(cols1); style_header(ws1, 3, len(cols1))
ws1.append(["12","2026-09-02","AUDJPY","SELL",0.02,114.573,POS["sl_new"],109.781,"部分平仓(110.20平0.01手)+剩余0.01手持仓","+"+str(POS["part_pips"])+" / 剩余+"+str(round(_pips,1)),"+"+str(POS["part_pnl"])+" / 浮动+"+str(ACC["floating"]),"+3.39R","已实现+剩余","W/D/4H三周期共振+BoJ加息预期vs澳洲按兵不动+Hurst"+str(round(h_abs,2))+"强趋势",8,"冷静/按计划","是","补挂保护性SL "+str(POS["sl_new"])+", 事件前未触TP则主动了结"])
for c in range(1, len(cols1)+1):
    ws1.cell(row=4, column=c).border = border; ws1.cell(row=4, column=c).alignment = left
    ws1.cell(row=4, column=c).fill = PatternFill("solid", fgColor="FFF3CD")
for i in range(5, 24):
    for c in range(1, len(cols1)+1): ws1.cell(row=i, column=c).border = border
for i, w in enumerate([4,11,9,7,7,9,9,9,9,10,9,8,14,30,8,12,10,24], 1):
    ws1.column_dimensions[chr(64+i) if i <= 26 else "A"].width = w
ws1.freeze_panes = "A4"
ws2 = wb.create_sheet("R乘数统计")
ws2.append(["策略信号统计（样本期: 2026-07 ~ 2026-09, 三周期共振策略）"]); ws2["A1"].font = title_font; ws2.append([])
ws2.append(["指标","数值"]); style_header(ws2, 3, 2)
for k, v in [("总交易次数","12 笔"),("盈利/亏损","8 胜 / 4 负"),("胜率","66.7%"),("平均盈亏比","1.85 : 1"),("期望值(每笔R)","+0.57 R"),("最大连胜","4 次"),("最大连败","2 次"),("最大回撤","-1.8 R"),("利润因子","2.75")]:
    ws2.append([k, v]); ws2.cell(row=ws2.max_row, column=1).border = border; ws2.cell(row=ws2.max_row, column=1).alignment = left
    ws2.cell(row=ws2.max_row, column=2).border = border; ws2.cell(row=ws2.max_row, column=2).alignment = center
ws2.append([])
ws2.append(["#","时间","标的","方向","入场价","出场价","盈亏(pips)","R倍数","结果"]); style_header(ws2, ws2.max_row, 9)
for num, dt, sym, dr, en, ex, pips, rmult, res in BT_SIGNALS:
    ws2.append([num, dt, sym, dr, en, ex, pips, rmult, res])
    for c in range(1, 10):
        ws2.cell(row=ws2.max_row, column=c).border = border; ws2.cell(row=ws2.max_row, column=c).alignment = center if c != 1 else left
ws2.column_dimensions["A"].width = 16; ws2.column_dimensions["B"].width = 14
for col in "CDEFGHI": ws2.column_dimensions[col].width = 11
ws3 = wb.create_sheet("复盘问题清单")
ws3.append(["每笔交易复盘 10 问（收盘后必填）"]); ws3["A1"].font = title_font; ws3.append([])
ws3.append(["#","复盘问题","我的回答"]); style_header(ws3, 3, 3)
for q in ["1. 这笔交易是否严格遵循了事前计划？(入场/止损/目标是否事先确定)","2. 入场时三维(宏观/跨市场/盘面)是否真正共振？还是仅凭单一信号？","3. 仓位是否符合凯利/1%纪律？是否存在超配？","4. 止损是否前置设定？是否被执行？还是移动/取消了止损？","5. 入场时的情绪状态如何？(冷静/FOMO/报复性/过度自信)","6. 这笔交易的R倍数是多少？符合系统的正期望吗？","7. 离场是按计划(止盈/止损)还是情绪化操作？","8. 如果重来一次, 哪个环节可以做得更好？","9. 这笔交易暴露了什么认知盲区或坏习惯？","10. 是否需要更新交易系统/检查清单？更新哪一条？"]:
    ws3.append([q.split(".")[0], q, ""])
    ws3.cell(row=ws3.max_row, column=1).border = border; ws3.cell(row=ws3.max_row, column=1).alignment = center
    ws3.cell(row=ws3.max_row, column=2).border = border; ws3.cell(row=ws3.max_row, column=2).alignment = left
    ws3.cell(row=ws3.max_row, column=3).border = border
ws3.column_dimensions["A"].width = 4; ws3.column_dimensions["B"].width = 55; ws3.column_dimensions["C"].width = 45
ws4 = wb.create_sheet("每周复盘汇总")
ws4.append(["每周交易复盘汇总"]); ws4["A1"].font = title_font; ws4.append([])
cols4 = ["周次","交易笔数","胜/负","胜率%","总R","平均每笔R","最大单笔盈利R","最大单笔亏损R","是否遵守纪律","本周最大教训","下周改进点"]
ws4.append(cols4); style_header(ws4, 3, len(cols4))
for i in range(4, 10):
    for c in range(1, len(cols4)+1): ws4.cell(row=i, column=c).border = border
for i, w in enumerate([8,9,8,8,8,11,13,13,12,28,28], 1):
    ws4.column_dimensions[chr(64+i)].width = w
xl_path = os.path.join(OUT, "交易复盘模板_v2.5.6.xlsx")
wb.save(xl_path)
print("XLSX written:", xl_path)
