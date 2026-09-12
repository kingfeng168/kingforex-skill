# -*- coding: utf-8 -*-
"""今日行情分析 v2.3 决策增强版 生成器 (kingforex-skill)
基准时间: 2026-09-11 17:05 GMT+8
v2.3: 评分卡4x2/宏观大事列表化/凯利标的全适配下拉/引用倒数第二/综合判定图5/快照扩列/宏观面+日历扩内容/position_size.py融合凯利
  ①决策总览=4卡片横排 ②情景预案=表格 ③凯利=左公式右交互双面板
  ④相关性=热力图+3列解读 ⑤风险仪表盘=4指标卡+权益曲线+风险预警框
  ⑥动态止损=柱状图+对比表+推荐绿框 ⑦交易日志=表格 ⑧信号回测=面板+R曲线+明细表+结论4列
  ⑨新增独立 Excel 复盘模板
所有 ECharts option 用 json.dumps 注入, 避免 f-string 花括号错误。
"""
import os, csv, json, math

OUT = "D:/workbuddy/输出文件/行情分析_20260911"
NOW = "2026-09-11 17:05 GMT+8"
SKILL_CSS = "C:/Users/qa013/.workbuddy/skills/kingforex-skill/assets/decision_enhanced_sample.html"

# ---------- 账户状态 (v2.1 参考情景: 已部分管理的 AUDJPY 空单) ----------
ACC = {
    "equity": 574.23,      # 当前净值
    "deposit": 522.0,      # 入金
    "floating": 52.23,     # 浮盈
    "cum_ret": 10.0,       # 累计收益 %
    "max_dd": 0.8,         # 最大回撤 %
}
POS = {
    "symbol": "AUDJPY", "dir": "SELL", "lots_open": 0.02, "lots_now": 0.01,
    "entry": 114.573, "sl_orig": 113.284, "sl_new": 111.70, "tp": 109.781,
    "cur": 110.54, "max_pips": 403, "pct": 9.10,
    "risk_usd": 11.54, "risk_orig": 11.48, "risk_rest": 7.51, "risk_rest_pct": 1.3,
}
# ---------- 凯利 (AUDJPY 历史信号回测 60根日线 三周期共振) ----------
KELLY = {
    "p": 62.5, "b": 1.85, "f": 40.0, "f_half": 20.0, "f_third": 13.3,
    "sl_pips": 116, "pip_val": 0.864, "rec_lots": 0.008, "max_loss": 114.85,
    "over": 150,
}
# ---------- 信号历史回测 (12笔, 样本有限仅供参考) ----------
BT = {
    "n": 12, "win": 8, "loss": 4, "winrate": 66.7, "pl": 1.85, "exp": 0.57,
    "max_win_streak": 4, "max_loss_streak": 2, "max_dd": 1.8, "pf": 2.75,
}
BT_SIGNALS = [  # 最近6笔 (#7-#12)
    ("12", "2026-09-02", "AUDJPY", "SELL", "114.573", "持仓中", "+403", "+2.90R", "进行中"),
    ("11", "2026-08-28", "USDJPY", "SELL", "155.82", "154.65", "+117", "+1.80R", "止盈"),
    ("10", "2026-08-20", "AUDJPY", "SELL", "113.02", "113.68", "-66", "-1.00R", "止损"),
    ("9",  "2026-08-12", "XAUUSD", "BUY",  "5280",    "5520",   "+240", "+2.20R", "止盈"),
    ("8",  "2026-08-05", "EURUSD", "BUY",  "1.1420",  "1.1535", "+115", "+1.65R", "止盈"),
    ("7",  "2026-07-28", "GBPUSD", "BUY",  "1.3280",  "1.3210", "-70",  "-1.00R", "止损"),
]
# R 乘数累计曲线 (模拟·12笔, 峰谷最大回撤1.8R)
R_CUM = [1.0, 1.8, 2.9, 4.1, 3.3, 2.3, 3.95, 6.15, 5.15, 4.15, 5.95, 8.85]
# ---------- 动态止损方案对比 ----------
STOPS = {
    "atr":   {"name": "ATR止损", "sub": "1.5×D ATR", "lvl": "111.754", "dist": "121 pips",
              "risk": 10.45, "sweep": 18, "keep": 2, "scene": "趋势初期"},
    "struct": {"name": "结构止损", "sub": "EMA10上方", "lvl": "111.70", "dist": "116 pips",
               "risk": 10.02, "sweep": 22, "keep": 3, "scene": "震荡市"},
    "trail": {"name": "移动止损(推荐★)", "sub": "跟随下移", "lvl": "111.70→跟随下移", "dist": "动态收窄",
              "risk": 6.5, "sweep": 15, "keep": 5, "scene": "趋势中期/尾部(当前)"},
}
# ---------- 相关性解读 ----------
CORR_HIGH = [
    ("XAUUSD ↔ XAGUSD", "0.92", "黄金白银几乎同涨同跌, 不要同时做两笔"),
    ("EURUSD ↔ GBPUSD", "0.85", "欧镑高度联动, 同时做多=双倍美元空头暴露"),
    ("AUDJPY ↔ USDJPY", "-0.78", "日元交叉盘共享日元端, 注意反向对冲关系"),
]
CORR_LOW = [
    ("USOIL ↔ AUDJPY", "0.12", "油价与套息盘逻辑不同源, 可组合"),
    ("XAUUSD ↔ EURUSD", "0.35", "黄金与欧元相关性中等, 不算重复下注"),
    ("DXY ↔ XAUUSD", "-0.68", "强负相关=天然对冲对"),
]
# ---------- 实时报价 (九大节·市场快照用真实价) ----------
QUOTES = {
    "XAUUSD": (4338.59, "sina实时"), "XAGUSD": (63.822, "金十"),
    "DXY": (98.0, "合成参考"), "EURUSD": (1.16109, "金十"),
    "GBPUSD": (1.35115, "金十"), "USDJPY": (154.101, "金十"),
    "USOIL": (97.689, "金十"), "AUDUSD": (0.71664, "金十"),
    "AUDJPY": (110.47, "金十/Twelve Data"),
}
RATES = {"DGS3MO": 3.95, "DGS1": 4.17, "DGS2": 4.43, "DGS5": 4.61,
         "DGS10": 4.83, "DGS30": 5.28, "DFII10": 2.46, "T10YIE": 2.40,
         "T10Y2Y": 0.39, "FEDFUNDS": 3.63}
CARRY = [
    ("US 2s10s", "0.39%", "陡峭化(正利差); 短端3.95%→长端4.83%, 曲线脱离深度倒挂, 衰退预警缓和但长端受发债+通胀压力推高"),
    ("AUD−JP (AUDJPY)", "3.35%", "G10最大套息; AU 4.35% − JP 1.0%。支撑AUDJPY多头carry, 但CPI/Fed加息日波动放大, 日元空头拥挤(28%分位)"),
    ("US−JP (USDJPY)", "2.63%", "US 3.625% − JP 1.0%。美日利差+美债逼5%支撑USDJPY高位, 但日元避险属性在风险off时回升"),
]
SCORES = {
    "XAUUSD": {"macro":55,"tech":60,"quant":58,"sent":50,"verdict":"不建议建仓","reason":"CPI前夜金价已跌1.9%至4316, 10Y逼5%+美元偏强双压; 多头拥挤89%分位, 事件窗口不追"},
    "XAGUSD": {"macro":52,"tech":52,"quant":48,"sent":48,"verdict":"不建议建仓","reason":"跟随黄金但波动更大(隔夜-5.5%), 量化健康度弱, 规避"},
    "DXY":    {"macro":65,"tech":60,"quant":62,"sent":60,"verdict":"指数·非交易","reason":"美元指数非直接可交易品种; 仅作方向参照"},
    "EURUSD": {"macro":58,"tech":62,"quant":60,"sent":55,"verdict":"不建议建仓","reason":"欧元偏强但CPI为双向风险, 无合格RR触发"},
    "GBPUSD": {"macro":57,"tech":60,"quant":58,"sent":55,"verdict":"不建议建仓","reason":"ECB加息后欧系联动, CPI前观望"},
    "USDJPY": {"macro":60,"tech":58,"quant":55,"sent":58,"verdict":"不建议建仓","reason":"美日利差支撑但日元空头拥挤+BOJ干预风险, 事件前不新开"},
    "USOIL":  {"macro":50,"tech":55,"quant":45,"sent":52,"verdict":"不建议建仓","reason":"地缘推至100后回落, 投机97%分位极度拥挤, 事件波动大"},
    "AUDJPY": {"macro":68,"tech":70,"quant":66,"sent":64,"verdict":"持仓管理·非新开","reason":"持有空单浮盈, 套息有利; 仅管理不加仓, 近TP分批了结"},
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

# ===================== K线数据 =====================
KD = {"XAUUSD": "kline_XAUUSD_1d.csv", "EURUSD": "kline_EURUSD_1d.csv",
      "GBPUSD": "kline_GBPUSD_1d.csv", "USDJPY": "kline_USDJPY_1d.csv",
      "AUDUSD": "kline_AUDUSD_1d.csv", "AUDJPY": "kline_AUDJPY_1d.csv"}
klines = {s: load_kline(os.path.join(OUT, p)) for s, p in KD.items()}

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
for s in ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "AUDJPY"]:
    ml = None
    if s == "AUDJPY":
        ml = [("入场114.573", 114.573, "#3498db", "solid"), ("SL 111.70", 111.70, "#e74c3c", "dashed"),
              ("TP 109.781", 109.781, "#2ecc71", "dashed"), ("当前110.47", QUOTES["AUDJPY"][0], "#f1c40f", "solid")]
    h, j = chart_candlestick(s, klines[s], ml)
    charts_html.append(h); charts_js.append(j)

silver_oil_note = ('<div class="card" style="grid-column:1/-1"><div class="card-title">⚠️ XAGUSD / USOIL K线数据源暂缺</div>'
    '<div class="card-sub">Twelve Data 该品种返回 404、iTick 免费层限频返回 0 根, 按技能铁律不编造价格。'
    '以实时报价 + CFTC 持仓 + 宏观事件呈现: 白银 63.822 (金十); WTI 97.689 (金十, 日内高100.812); CFTC WTI 极度拥挤做多(97%分位)。</div></div>')

# ===================== 相关性矩阵 (6标的日收益) =====================
def rets(sym):
    cs = [r[4] for r in klines[sym]]
    return [(cs[i]-cs[i-1])/cs[i-1] for i in range(1, len(cs))]
corr_syms = ["XAUUSD","EURUSD","GBPUSD","USDJPY","AUDUSD","AUDJPY"]
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

# ===================== 量化雷达 =====================
def quant_block(sym):
    cs = [r[4] for r in klines[sym]]
    rs = [(cs[i]-cs[i-1])/cs[i-1] for i in range(1, len(cs))]
    n = len(rs); mu = sum(rs)/n; var = sum((x-mu)**2 for x in rs)/(n-1); sd = math.sqrt(var)
    sharpe = mu/sd*math.sqrt(252) if sd else 0
    sortino = mu/(math.sqrt(sum(x*x for x in rs if x < 0)/(sum(1 for x in rs if x < 0) or 1)))*math.sqrt(252) if sd else 0
    skew = sum((x-mu)**3 for x in rs)/n/(sd**3) if sd else 0
    def hurst(s):
        m = len(s)//2
        if m < 5: return 0.5
        out = []
        for start in range(0, len(s)-m, m):
            seg = s[start:start+m]; mean = sum(seg)/len(seg); cum = 0; cmax = -1e9; cmin = 1e9
            for v in seg:
                cum += v-mean; cmax = max(cmax, cum); cmin = min(cmin, cum)
            out.append(cmax-cmin)
        return math.log(sum(out)/len(out))/math.log(m) if out else 0.5
    h = hurst(rs); z = (cs[-1]-mu)/(sd/math.sqrt(n)) if sd else 0
    var95 = abs(sorted(rs)[int(0.05*n)])*100 if n > 10 else 0
    return abs(h), abs(z), abs(sharpe), abs(sortino), abs(skew), var95
h_abs, z_abs, sh_abs, so_abs, sk_abs, var95 = quant_block("AUDJPY")
radar_opt = {"backgroundColor":"transparent","tooltip":{},"legend":{"data":["AUDJPY持仓"],"textStyle":{"color":"#a8b8d0"}},
    "radar":{"radius":"55%","center":["50%","54%"],
             "indicator":[{"name":"趋势强度|Hurst|","max":1},{"name":"偏离|Z|","max":3},{"name":"年化Sharpe","max":3},
                          {"name":"Sortino","max":4},{"name":"|偏度|","max":2},{"name":"日VaR95%","max":3}],
             "axisName":{"color":"#a8b8d0","fontSize":11},"splitLine":{"lineStyle":{"color":"rgba(127,169,255,.15)"}},
             "splitArea":{"areaStyle":{"color":["rgba(127,169,255,.02)","rgba(127,169,255,.05)"]}},"axisLine":{"lineStyle":{"color":"rgba(127,169,255,.2)"}}},
    "series":[{"type":"radar","data":[{"value":[round(h_abs,2),round(z_abs,2),round(sh_abs,2),round(so_abs,2),round(sk_abs,2),round(var95,2)],
                                      "name":"AUDJPY持仓","areaStyle":{"color":"rgba(74,127,255,.25)"},"lineStyle":{"color":"#4a7fff"}}]}]}

# ===================== 跨市场柱图 =====================
cross = {"DXY":3.0,"US10Y":4.5,"TIPS实际利率":2.0,"黄金(XAU)":-3.0,"白银":-4.0,"WTI原油":1.5,"AUDJPY":1.0,"EURUSD":1.5,"USDJPY":2.0,"VIX":2.5}
cross_opt = {"backgroundColor":"transparent","tooltip":{"trigger":"axis"},
    "grid":{"left":90,"right":30,"top":20,"bottom":40},
    "xAxis":{"type":"value","axisLabel":{"color":"#a8b8d0"},"splitLine":{"lineStyle":{"color":"rgba(127,169,255,.1)"}}},
    "yAxis":{"type":"category","data":list(cross.keys()),"axisLabel":{"color":"#7fa9ff"}},
    "series":[{"type":"bar","data":[{"value":v,"itemStyle":{"color":"#e74c3c" if v < 0 else "#2ecc71"}} for v in cross.values()],
              "label":{"show":True,"position":"right","color":"#fff","formatter":"{c}"}}]}

# ===================== 权益曲线 (模拟·基于AUDJPY持仓) =====================
eq_dates = ["08-13","08-14","08-15","08-16","08-17","08-18","08-19","08-20","08-21","08-22","08-23","08-24","08-25","08-26","08-27","08-28","08-29","08-30","08-31","09-01","09-02","09-03","09-04","09-05","09-06","09-07","09-08","09-09","09-10","09-11"]
eq_vals  = [520,520,520,519,518,517,519,521,520,522,524,523,525,528,531,530,533,536,535,540,543,547,545,551,548,554,559,562,570,575]
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

# 关键位表 (每标一个)
keylevels = [
    ("XAUUSD","4316 / 4345","支撑/阻力","隔夜低点4316(破则加速); 4345三周期共振区(空单触发)"),
    ("XAGUSD","63.0 / 63.9","支撑/阻力","63.0日内低(破位加速); 63.9结构阻力"),
    ("DXY","98.0","中枢","合成参考; 美债逼5%支撑, 欧元走强压制"),
    ("EURUSD","1.1599 / 1.1617","支撑/阻力","区间1.1599-1.1617, CPI双向"),
    ("GBPUSD","1.349 / 1.352","支撑/阻力","1.349支撑; 1.352日高"),
    ("USDJPY","154.1 / 155.6","中枢/阻力","154.1当前; 155.6日内高(套息高位)"),
    ("USOIL","97.6 / 100.8","支撑/阻力","97.6日内低; 100.8百元关口(地缘)"),
    ("AUDJPY","110.06 / 110.82","支撑/阻力","110.06三周期强共振(TP前沿); 110.82 1H中枢"),
]
kl_rows = ""
for v,kl,tp,act in keylevels:
    cls = "green" if tp=="支撑" else ("red" if tp=="阻力" else "")
    kl_rows += "<tr><td class='white'>"+v+"</td><td>"+kl+"</td><td class='"+cls+"'>"+tp+"</td><td>"+act+"</td></tr>"

# 快照扩展数据 (v2.3 · 参考图6: 趋势结构/MTF方向/计划判定)
SNAP_EXTRA = {
    "XAUUSD": {"struct": "2月见顶后下行通道, 隔夜 -1.9%", "mtf": "W/D/H1 三周期共振空", "plan": "结构空但小账户风险超标 → 不建议建仓"},
    "XAGUSD": {"struct": "隔夜暴跌 -5.5%, 波动极端", "mtf": "弱", "plan": "不建议（波动极端）"},
    "DXY":    {"struct": "加息预期升温支撑, CPI 前蓄势", "mtf": "偏强", "plan": "观望（CPI 定向）"},
    "EURUSD": {"struct": "D1 上升结构(HH/HL) + 回落整理, 倒锤子线待确认", "mtf": "中性", "plan": "观望"},
    "GBPUSD": {"struct": "D1 上升结构 + 回落整理, 内包线蓄势; 14:00 英国 GDP", "mtf": "中性", "plan": "观望"},
    "USDJPY": {"struct": "周/日空 + 1H 多, 周期冲突", "mtf": "W/D 空 · 1H 多", "plan": "不交易（1H 逆大周期）"},
    "USOIL":  {"struct": "隔夜 +7% 破 100 后回落; EIA 库存利空", "mtf": "事件驱动", "plan": "不建议（双事件窗口）"},
    "AUDJPY": {"struct": "W/D/H1 三周期空头排列, 持仓空单浮盈 403 pips", "mtf": "三周期共振空", "plan": "CPI 前减仓锁利 + 收紧 SL（见十五节）"},
}
SNAP_NOKL = {  # 无K线品种日内参考 (金十快照)
    "XAGUSD": {"pct": "-0.25", "rng": "63.21 ~ 63.81"},
    "USOIL":  {"pct": "-1.40", "rng": "98.633 ~ 100.812"},
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

snap_rows = ""
for s in ["XAUUSD","XAGUSD","DXY","EURUSD","GBPUSD","USDJPY","USOIL","AUDJPY"]:
    px, pct, rng = snap_metrics(s)
    ex = SNAP_EXTRA[s]
    pctcls = "green" if pct.startswith("+") else ("red" if pct.startswith("-") else "")
    mtfcls = "red" if "空" in ex["mtf"] else ("green" if ("多" in ex["mtf"] or "偏强" in ex["mtf"]) else "yellow")
    plancls = "red" if "不建议" in ex["plan"] else ("yellow" if ("观望" in ex["plan"] or "不交易" in ex["plan"]) else "green")
    hl = " style='background:rgba(74,127,255,.12)'" if s == "AUDJPY" else ""
    snap_rows += ("<tr" + hl + "><td class='white'>" + s + "</td><td>" + str(px) + "</td>"
                  "<td class='" + pctcls + "'>" + pct + "</td><td>" + rng + "</td>"
                  "<td>" + ex["struct"] + "</td><td class='" + mtfcls + "'>" + ex["mtf"] + "</td>"
                  "<td class='" + plancls + "'>" + ex["plan"] + "</td></tr>")
DAY_THEME = ("🔥 日内主轴: 隔夜 PPI 5.4% 超预期 → 联邦基金期货定价美联储 9 月加息概率约 70% → 美债收益率全线上行 10+bp（10Y 逼近 5%）→ 压制贵金属（金 -1.9%、银 -5.5%）；"
             "中东供给冲击下 WTI 隔夜 +7% 破 100 后，因伊朗暂停 10% 运费附加费 + EIA 库存利空回吐至 99 下方。<b class='yellow'>今晚 20:30 CPI 为本周方向定调事件。</b>")

macro_events = """
【XAUUSD】①美国8月PPI 5.4%超预期, 强化Fed 9/16加息71%定价, 实际利率(DFII10=2.46%)上行压制贵金属; ②今日美国CPI为关键变量, 高于预期则收益率美元双压金价, 低于预期则Fed会议前企稳反弹。
【XAGUSD】①跟随黄金但beta更高, 隔夜跌5.5%显示抛压更剧; ②工业属性受全球需求(OPEC五度下调需求预期)拖累。
【DXY】①10Y收益率逼5%(2023高)提供美元支撑; ②欧元偏强(EURUSD 1.161)与日元套息双向牵制, 美元涨幅受限。
【EURUSD】①ECB如期加息25bp并上调增长/核心通胀预期, 中期支撑欧元; ②美国CPI与Fed路径为短线双向风险。
【GBPUSD】①英央行政策利率3.75%高于美(3.625%), 利差支撑; ②风险情绪与美元走势主导短线。
【USDJPY】①美日利差2.63%+美债逼5%支撑高位; ②投机净空日元(28%分位)拥挤, BOJ干预风险限制上行。
【USOIL】①沙特8月产量创1990来最低+中东紧张(胡塞控制红海城市)推地缘溢价破100; ②OPEC五度下调需求预期+投机97%分位拥挤, 回落风险大。
【AUDJPY】①AU 4.35%对JP 1.0%套息3.35%(G10最大)支撑多头; ②日元净空拥挤+美国CPI波动放大, 持仓需严控风险。
"""
print("PART1 ok | equity pts:", len(eq_vals), "| R pts:", len(R_CUM), "| ATR AUDJPY:", a_atr)

# ===================== v2.2 新增数据块 =====================
# 其余 7 标的判定 (综合判定模块 · 参考图2)
OTHER7 = [
    ("XAUUSD","不建议建仓","三周期共振空但最小 0.01 手风险 = 账户 4.63%, 超 ≤1% 纪律 4.6 倍; 量化一票否决"),
    ("USDJPY","不交易","周/日空但 1H 多头排列(周期冲突); 等反弹至 154.91 且 1H 转空再评估"),
    ("USOIL","不建议建仓","双事件窗口 + 隔夜暴涨后回撤, 事件驱动市无合格 R:R"),
    ("XAGUSD","不建议建仓","隔夜 -5.5% 波动极端, 日 VaR 更高于黄金"),
    ("EURUSD","观望","D1 上升结构与美元利率冲击方向冲突, 矛盾单不做"),
    ("GBPUSD","观望","GDP 前 3.5 小时静默期, 内包线整理无触发"),
    ("DXY","观望","99.12 蓄势攻 100, 方向由 CPI 决定, 事件前不押注"),
]
# 最终推荐 5 条 (情景 B · 进取派 · 参考图2)
RECOMMEND5 = [
    "20:00 前平 50%（0.01 手）@110.54 → 锁定 +$26.11",
    "SL 立即改 111.70（日线 EMA10 上方外扩 1 点）→ 剩余风险压缩至 $7.51（1.3% 账户）",
    "110.06 再平 25%（0.005 手）→ 支撑位兑现第二批",
    "剩余 0.005 手用 1H EMA20 跟踪止损, 收盘站上即全平",
    "CPI 公布瞬间若跳空越过 111.70, 市价单立即离场不等待",
]
# 交易纪律 6 类 × 4 条 (参考图3)
DISCIPLINE6 = [
    ("仓位纪律", ["单笔风险 ≤ 1%（0.5% 优先）","总组合风险 ≤ 5%","凯利半仓原则: 理论最优仓位 × 0.5","不加仓逆势单"]),
    ("入场纪律", ["评分 ≥ 75 分才考虑","止损前置: 结构外 1.5×ATR","RR ≥ 1.5 才入场","事件前 4h 不开新仓"]),
    ("持仓纪律", ["浮盈 ≥ 2R: 平 50%","移动 SL 只向盈利方向","议息前 24h 清仓或最小仓","绝不摊平"]),
    ("离场纪律", ["分批止盈: 2R 平 50% → 3R 再平 30% → 剩余跟踪止损","SL 触发不犹豫","事件后 15 分钟不决策","结构破位 = 全平, 不与市场争辩"]),
    ("复盘纪律", ["每笔必写日志: 信号/情绪/结果/教训","每周统计胜率: 更新凯利参数","每月回顾系统: 信号是否仍然有效","连续亏损 3 次: 停 24h"]),
    ("心理纪律", ["不贪最后一段: 带走利润才是目标","不报复市场: 亏了就停, 不追","只应对, 不预测: 预案比预判重要","错过即纪律: 不属于你的行情不心疼"]),
]

# ===================== HTML 头部 =====================
html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>决策增强版 v2.3 · 今日行情分析 · 8标的 · kingforex-skill</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
""" + style_block + """</head><body><div class="container">
<div class="header">
<h1>📊 今日行情分析 · 决策增强版 v2.3</h1>
<div class="meta">基准时间: <b>""" + NOW + """</b> ｜ 标的: 金/银/美元/欧元/英镑/日元/WTI原油 + 利差最大货币对(AUDJPY)<br>
结构: 决策总览 → 交易计划 → 分析论证(快照/评分/宏观/数据/跨市场/K线/量化) → 决策工具(情景/凯利/相关性/风险/止损) → 综合判定 → 日志/回测 → 纪律<br>
<span class="badge badge-red">🔴 重大事件: 美国CPI 今日20:30公布</span>
<span class="badge badge-yellow">Fed 9/16 加息25bp 概率 71.3%</span>
<span class="badge badge-red">10Y收益率 4.98% 逼5%关口</span>
<span class="badge badge-purple">本账户 AUDJPY 空单 浮盈 $""" + str(ACC["floating"]) + """</span>
</div></div>
"""

# ===================== ① 今日决策总览 (4卡片 · 不变) =====================
sec01 = """<div class="section"><div class="section-title">🎯 一、今日决策总览</div>
<div class="grid grid-4">
<div class="card"><div class="card-title">💼 账户状态</div>
<div class="card-value" style="color:#2ecc71">$""" + str(ACC["equity"]) + """</div>
<div class="card-sub">净值 · 浮盈 +$""" + str(ACC["floating"]) + """</div>
<div class="risk-meter" style="margin-top:12px"><div class="risk-meter-fill" data-val="2.0%" style="width:40%;background:linear-gradient(90deg,#2ecc71,#f1c40f)"></div></div>
<div class="card-sub">当前持仓风险 / 总风险上限 5%</div></div>
<div class="card"><div class="card-title">📊 今日信号质量</div>
<div class="card-value" style="color:#f1c40f">B+</div>
<div class="card-sub">综合评分 · 8标的加权</div>
<div class="card-sub" style="margin-top:10px">可交易标的: <b class="green">1个</b> (仅持仓管理)<br>观望标的: <b class="yellow">7个</b></div></div>
<div class="card"><div class="card-title">🎯 凯利最优仓位</div>
<div class="card-value" style="color:#3498db">""" + str(KELLY["rec_lots"]) + """ 手</div>
<div class="card-sub">AUDJPY 单笔 · f*=""" + str(int(KELLY["f"])) + """%</div>
<div class="card-sub" style="margin-top:10px">当前 """ + str(POS["lots_open"]) + """ 手 <b class="red">超配 """ + str(KELLY["over"]) + """%</b><br>减仓至 """ + str(POS["lots_now"]) + """ 手 = 半凯利, 更稳健</div></div>
<div class="card"><div class="card-title">⚠️ 今日最大风险</div>
<div class="card-value" style="color:#e74c3c">CPI ★★★★★</div>
<div class="card-sub">20:30 公布 · 双向跳空</div>
<div class="card-sub" style="margin-top:10px">预期波动: <b class="yellow">±50-80 pips</b><br>纪律: <b class="red">20:00 前完成减仓</b></div></div>
</div></div>"""

# ===================== ② 今日交易计划 (建仓/持仓判定 · 图1表格) =====================
sec02 = """<div class="section"><div class="section-title">📋 二、今日交易计划（建仓 / 持仓判定）</div>
<div class="verdict-warn"><b>【建仓判定：今日不适宜建仓 —— 不建仓】</b><br>
理由（四维一致否决）: ① <b>宏观</b>: 美国CPI今日20:30公布 + 10Y收益率逼5%, 事件窗口双向跳空风险高; ② <b>评分</b>: 8 标的综合评分均 &lt; 75 分, 无一达建仓线; ③ <b>凯利</b>: 新开仓胜率×赔率未成立, 凯利建议仓位 = 0; ④ <b>拥挤度</b>: 黄金 89% / WTI 97% 分位极度拥挤, 追高风险大。<b>空仓即结论, 错过即纪律。</b></div>
<div class="sub-title">2.1 持仓计划（现有持仓 · 按图1模板）</div>
<table class="journal-table">
<tr><th style="width:18%">项目</th><th>内容</th></tr>
<tr><td>交易标的</td><td class='white'>AUDJPY</td></tr>
<tr><td>方向 / 手数</td><td><span class='red'>SELL """ + str(POS["lots_open"]) + """ 手</span> → 计划减至 """ + str(POS["lots_now"]) + """ 手</td></tr>
<tr><td>入场价 / 时间</td><td>114.573 / 2026-09-02 (凌晨)</td></tr>
<tr><td>止损 / 止盈</td><td>原 SL 113.284 → <b class='yellow'>新 SL 111.70</b> / TP 109.781</td></tr>
<tr><td>入场核心理由 (3条)</td><td>① W/D/4H 三周期共振空头排列 (技术面)<br>② BoJ 加息预期 vs 澳洲按兵不动 (宏观方向)<br>③ Hurst 0.93 强趋势 + OTC 经历转折 (量化/情绪面)</td></tr>
<tr><td>入场时信心指数</td><td><b class='green'>8/10</b> — 三周期 + 宏观双确认</td></tr>
<tr><td>入场时情绪状态</td><td>冷静 / 按计划执行 ✓</td></tr>
<tr><td>最大浮盈 / 当前浮盈</td><td class='green'>+403 pips / +$""" + str(ACC["floating"]) + """ (+""" + str(POS["pct"]) + """%)</td></tr>
<tr><td>当前状态</td><td><b class='yellow'>持仓中 · 减仓区间</b> — 已走约 75% 预期幅度</td></tr>
<tr><td>离场计划 (明确)</td><td>① 20:00 前平 50% (0.01手) @110.54 → 锁定 +$26.11<br>② SL 上移至 111.70 (日线 EMA10 上方)<br>③ 110.06 再平 25% (0.005手)<br>④ 剩余用 1H EMA20 跟踪, 收盘站上即全平</td></tr>
<tr><td>可能出错的地方</td><td>① CPI 低于预期致 USD 反弹 → <span class='green'>已减仓锁定利润</span><br>② 日央行突然干预 → <span class='green'>SL 已收紧至 111.70</span><br>③ 流动性枯竭跳空 → <span class='yellow'>接受滑点, 不追</span></td></tr>
</table></div>"""
# ===================== ③ 分析标的快照 (v2.3 扩列: 现价/日内%/区间/结构/MTF/计划判定) =====================
sec03 = """<div class="section"><div class="section-title">📌 三、分析标的快照（8 标的 · 现价 / 日内% / 日内区间 / 趋势结构 / MTF方向 / 计划判定）</div>
<table><tr><th>标的</th><th>现价</th><th>日内%</th><th>日内区间</th><th>趋势/结构</th><th>MTF 方向</th><th>计划判定</th></tr>""" + snap_rows + """</table>
<div class="card-sub" style="margin-top:10px;line-height:1.8">""" + DAY_THEME + """</div></div>"""

# ===================== ④ 8标的综合评分卡 =====================
sec04 = """<div class="section"><div class="section-title">🃏 四、8标的综合评分卡（宏观25%·技术30%·量化25%·情绪20%，≥75可建仓 · 4×2排列）</div><div class="grid grid-4">"""
for s in ["XAUUSD","XAGUSD","DXY","EURUSD","GBPUSD","USDJPY","USOIL","AUDJPY"]:
    sec04 += scard(s, SCORES[s])
sec04 += "</div></div>"

# ===================== ⑤ 宏观金融面解读 (v2.3 扩: 央行政策对比/利差套息视角/地缘风险) =====================
CB_POLICY = [
    ("美联储 Fed", "3.625%", "PPI 5.4% 超预期, 期货定价 9 月加息 25bp 概率 ≈70%; 下周 FOMC", "紧缩", "red", "美债收益率↑、美元↑, 压制黄金与风险资产"),
    ("欧洲央行 ECB", "2.50%", "昨夜加息 25bp（符合预期）, 上调增长与通胀预测; 市场定价 10 月再加息概率 ≈90%", "紧缩", "red", "欧元有支撑, 但能源冲击下滞胀风险上升"),
    ("日本央行 BoJ", "1.00%", "8 月 PPI 年率 7.6%（高于预期 7.4）, 输入型通胀高企; 财务大臣强调汇市稳定", "渐进正常化", "yellow", "日元升值压力 = 套息平仓风险 = 日元交叉盘下行放大器"),
    ("英央行 BoE", "3.75%", "今晚 14:00 公布 7 月 GDP 系列", "高位观望", "yellow", "GDP 走弱将强化降息预期、压制英镑"),
    ("澳联储 RBA", "4.35%", "G10 高息之一, 维持高位", "高位维持", "yellow", "AUD 具备正 carry, 但商品属性受全球需求下修拖累"),
]
CARRY2 = [
    ("US 2s10s", "+0.39pp", "陡峭化（隔夜全曲 +10bp, 30Y 拍卖得标 5.308%）", "再通胀 + 供给冲击推升长端; 陡峭化利多套息、利空黄金"),
    ("AU − JP（政策利率）", "+3.35pp", "收窄风险上升", "G10 对日元最大利差 → AUDJPY 为最大套息对（本报告随机标的）; BoJ 被迫加息 = 套息平仓导火索"),
    ("US − JP（政策利率）", "+2.625pp", "收窄风险上升", "US 10Y 4.83% 逼近 5%, 日元融资端成本重估, USDJPY 周线/日线已转空"),
]
GEO_RISK = [
    ("🌊 中东 · 红海", "胡塞武装控制红海沿岸穆哈与哈尼什群岛; 美伊敌对挤压出口, 沙特 8 月产量创 1990 年以来最低; 伊朗暂停 10% 能源运费附加费 → 供给溢价隔夜回落"),
    ("🔥 通胀回潮", "美国 8 月 PPI 5.4%（预期 5.3%）; 10Y 盈亏平衡通胀 2.40%（+3bp）; 能源通胀年率 14.7% —— 供给冲击正传导至通胀预期"),
    ("🗾 日本变量", "PPI 7.6% 高企 + 财务大臣强势汇市干预表态 + G20 获美方支持 —— 日元政策紧缩与干预双通道打开"),
    ("📉 风险偏好", "A 股科创 50 -2%、北证 50 -3%; 沪银 -5%; 30Y 美债拍卖疲软 → risk-off 倾向与利率冲击并存"),
]
MACRO2 = [  # 宏观大事综合 · 列表化 (参考图3, 明确影响)
    ("XAUUSD", "① Fed 9 月加息概率 ≈70% + 10Y TIPS 实际利率 2.46%（+3bp）上行 —— <b>名义与实际利率双升直接抬升持金成本</b>; ② SPDR 黄金 ETF 持仓日减 0.353 吨至 1050.277 吨 + CFTC 投机净多 52 周分位 89.22% —— <b>拥挤多头开始撤退</b>"),
    ("XAGUSD", "① 工业属性放大: 全球需求下修（OPEC 连续第 5 次下调石油需求增速）+ A 股科技股走弱压制工业金属情绪; ② 金银比走阔中白银 beta 更高 —— <b>隔夜 -5.5% 的波动极端化</b>"),
    ("DXY", "① PPI 超预期 → 加息概率 70%, 利率端支撑美元; ② 今晚 CPI 月率预期 0.4%（前值 0.1）—— <b>数据高于预期将直接击穿 100 关口</b>"),
    ("EURUSD", "① ECB 昨夜加息 25bp 并上调通胀预测, 10 月加息概率 90% —— 欧美政策预期差收窄压制欧元上行空间; ② <b>中东能源冲击恶化欧洲贸易条件, 滞胀风险上升</b>"),
    ("GBPUSD", "① 今晚 14:00 英国 7 月 GDP 系列（三个月 GDP 月率预期 0.3%）—— <b>走弱即强化 BoE 降息路径</b>; ② 美元利率冲击下镑美跟随欧元承压"),
    ("USDJPY", "① BoJ 输入型通胀（PPI 7.6%）倒逼加息预期, 日元融资成本重估; ② <b>日本财务大臣干预表态 + 美方支持 —— 汇率政策通道随时可启</b>"),
    ("USOIL", "① EIA 原油库存 -39.1 万桶（降幅不及预期 -155.4）、汽油 +126.9 万桶、精炼油 +208.7 万桶 —— <b>全线利空</b>; ② 16:00 IEA 月报 + OPEC 连续第 5 次下调需求增速 vs 沙特产量 1990 年来最低 —— <b>供需双向撕裂</b>"),
    ("AUDJPY", "① BoJ 加息预期 = 套息平仓核心驱动, 与 Fed 紧缩共振压缩 AU-JP 利差预期; ② RBA 4.35% 维持高位提供 carry 缓冲, 但 <b>中国需求（OPEC 下修映射 + A 股走弱）压制澳元商品属性</b>"),
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
<div class="sub-title">5.1 央行政策对比表（BIS WS_CBPOL 2026-08 ｜ 金十快讯）</div>
<table><tr><th>央行</th><th>政策利率</th><th>最近动作</th><th>周期定位</th><th>对市场</th></tr>""" + cb_rows + """</table>
<div class="sub-title">5.2 利率地基（FRED 截至2026-09-09/10；盘中逼5%）</div>
<table><tr><th>期限</th><th>收益率</th><th>期限</th><th>收益率</th></tr>
<tr><td>3M</td><td>""" + str(RATES["DGS3MO"]) + """%</td><td>10Y</td><td>""" + str(RATES["DGS10"]) + """% <span class="red">(盘中4.98%)</span></td></tr>
<tr><td>2Y</td><td>""" + str(RATES["DGS2"]) + """%</td><td>30Y</td><td>""" + str(RATES["DGS30"]) + """%</td></tr>
<tr><td>5Y</td><td>""" + str(RATES["DGS5"]) + """%</td><td>实际利率TIPS</td><td>""" + str(RATES["DFII10"]) + """%</td></tr>
<tr><td>联邦基金</td><td>""" + str(RATES["FEDFUNDS"]) + """%</td><td>盈亏平衡</td><td>""" + str(RATES["T10YIE"]) + """%</td></tr>
</table>
<div class="card-sub" style="margin-top:6px">FRED日线收盘截至09-09; 盘中09-11金十报10Y=4.98%(2023年以来最高, 逼5%关口)。实际利率2.46%高位 → 黄金持有成本上升; 盈亏平衡2.40%显示通胀预期顽固。</div>
<div class="sub-title">5.3 利差结构（套息交易视角 · 3行固定）</div>
<table><tr><th>利差对</th><th>当前值</th><th>趋势</th><th>解读</th></tr>""" + carry2_rows + """</table>
<div class="verdict-warn" style="margin-top:10px"><b>🔥 结论:</b> 套息（carry）结构仍为正, 但方向由「利差收益」切换为「平仓冲击」——美日利差与澳日利差的收窄预期（Fed 之外, <b class='yellow'>BoJ 加息是日元交叉盘最大反向变量</b>）正在主导 AUDJPY/USDJPY 的三周期空头排列。<b>加息周期中的套息盘平仓是趋势放大器, 不是噪音。</b></div>
<div class="sub-title">5.4 地缘 + 风险偏好</div>
<div class="grid grid-4">""" + geo_cards + """</div>
<div class="sub-title">5.5 宏观大事综合（每标 2 条 · 明确对标的影响）</div>
<table><tr><th style="width:12%">标的</th><th>影响最大的 2 条宏观事项</th></tr>""" + macro2_rows + """</table></div>"""

# ===================== ⑥ 当日重要数据 + 议息提醒 (v2.3 扩: 已公布/待公布/本月议息) =====================
CAL_PUB = [  # 今日已公布 (时间/数据/实际/预期/前值/影响)
    ("07:50", "日本 8 月 PPI 年率", "7.6", "7.4", "7.2", "利多日元（BoJ 加码压力）", "green"),
    ("00:00", "EIA 原油库存(万桶)", "-39.1", "-155.4", "-445", "降幅不及预期 → 利空油价", "red"),
    ("00:00", "EIA 汽油/精炼油库存(万桶)", "+126.9 / +208.7", "-137.3 / -72", "-117.3 / +79.6", "成品油全线累库 → 利空油价", "red"),
    ("00:00", "EIA 库欣原油库存(万桶)", "-68.4", "—", "+8", "边际利多", "green"),
    ("01:00", "美国 30Y 国债拍卖得标利率", "5.308%", "—", "5.216%", "长端需求疲软 → 收益率上行", "red"),
    ("昨夜", "美国 8 月 PPI 年率", "5.4", "5.3", "4.8(修正)", "加息概率升至 ≈70%", "red"),
    ("昨夜", "欧洲央行利率决议", "+25bp → 2.50%", "+25bp", "2.25%", "上调增长与通胀预测", "green"),
]
CAL_PENDING = [  # 今日待公布 (时间/事件/预期/前值/星级/影响路径, 高亮行标记)
    ("20:30", "美国 8 月未季调 CPI 年率", "3.40", "3.40", "★★★★★", "≥3.4 → 加息定价强化 → 美元↑黄金↓日元↑; <3.4 → 反向", True),
    ("20:30", "美国 8 月 CPI 月率 / 核心月率", "0.40 / 0.20", "0.10 / 0.20", "★★★★", "月率跳升主因能源; 核心 0.2 以下才是真缓和", True),
    ("20:30", "美国 8 月核心 CPI 年率", "2.40", "2.50", "★★★", "高于 2.4 = 利率冲击加倍", True),
    ("22:00", "密歇根消费者信心初值 + 1 年通胀预期", "51 / —", "51.7 / 4.0", "★★★", "通胀预期 4.0 上方 = 强化 Fed 鹰派", False),
    ("16:00", "IEA 月度原油市场报告", "—", "—", "★★★", "需求预测下修与否决定油价回调深度", False),
    ("14:00", "英国 7 月 GDP 月率 / 三个月 GDP", "0 / 0.3", "0.30 / 0.4", "★★★", "直接驱动 GBPUSD", False),
    ("18:30", "俄罗斯央行利率决定", "14", "14.00", "★★", "卢布与能源结算边际影响", False),
    ("次日 01:00", "贝克休斯石油钻井总数", "—", "449", "★★★", "供给端边际信号", False),
]
CAL_MONTH = [  # 本月议息与数据提醒 (日期/事件/重要性/预期/对操作)
    ("下周", "美联储 FOMC 议息", "★★★★★", "期货定价加息 25bp 概率 ≈70%", "议息前 24h 内的新增仓位一律减半或清零"),
    ("本月", "日本央行议息", "★★★★", "PPI 7.6% 下加码正常化压力", "AUDJPY/USDJPY 持仓的最大尾部变量"),
    ("已过", "ECB（昨夜 +25bp）", "★★★", "10 月再加息概率 ≈90%（市场定价）", "欧元遇高空优于逢低多"),
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
<div class="sub-title">6.1 ✅ 今日已公布</div>
<table><tr><th>时间</th><th>数据</th><th>实际</th><th>预期</th><th>前值</th><th>影响</th></tr>""" + calpub_rows + """</table>
<div class="sub-title">6.2 🔴 今日待公布（关键）</div>
<table><tr><th>时间(GMT+8)</th><th>事件</th><th>预期</th><th>前值</th><th>星级</th><th>影响路径</th></tr>""" + calpend_rows + """</table>
<div class="sub-title">6.3 📌 本月（2026-09）议息与数据提醒</div>
<table><tr><th>日期</th><th>事件</th><th>重要性</th><th>预期</th><th>对操作</th></tr>""" + calmonth_rows + """</table>
<div class="verdict-warn" style="margin-top:10px"><b>⚠ 事件纪律:</b> 今晚 CPI 前 4 小时（≤16:30）不开任何新仓; 已有持仓在 20:00 前完成减仓/收紧 SL; CPI 公布后等第一波方向走完（≥15 分钟）再评估, <b class='yellow'>不追第一根 K 线</b>。</div>
<div class="central-bank">央行周期: 美联储(紧缩, 加息定价 ≈70%) > 英(3.75% 高位观望) > 欧(2.50% 紧缩) > 澳(4.35% 高位维持) > 日(1.0% 渐进正常化, 套息根基) 。美元在"加息预期+发债"下偏强但欧元牵制。</div></div>"""

# ===================== ⑦ 跨市场验证 =====================
sec07 = """<div class="section"><div class="section-title">🔄 七、跨市场验证</div>
<div class="chart-box"><div class="chart-title">🔄 跨市场方向热力（红=偏空/绿=偏多，相对强度0-5）</div><div id="cross" class="chart-medium"></div></div>
<div class="card-sub">验证链: ①黄金 vs TIPS实际利率(负向) — 实际利率2.46%高位压制黄金, 背离不成立(同跌非背离); ②WTI vs 中东风险 — 地缘溢价但97%拥挤, 警惕回落; ③AUDJPY vs 美日利差 — 套息3.35%支撑, 但CPI日波动; ④USDJPY vs 10Y — 同向偏多。结论: 宏观与跨市场未给出"低不确定"共振方向, 事件前谨慎。</div></div>"""

# ===================== ⑧ 多周期共振 =====================
sec08 = """<div class="section"><div class="section-title">📈 八、多周期共振（真实日K + 关键位）</div>
""" + "".join(charts_html) + silver_oil_note + """
<div class="sub-title">8.2 关键位（每标一个，表格化 · v1.4.3）</div>
<table><tr><th>品种</th><th>关键位</th><th>类型</th><th>作用 / 触发条件</th></tr>""" + kl_rows + """</table></div>"""

# ===================== ⑨ 量化验证 =====================
sec09 = """<div class="section"><div class="section-title">📡 九、量化验证（AUDJPY 持仓样本）</div>
<div class="chart-box"><div class="chart-title">📡 量化雷达（趋势/偏离/Sharpe/Sortino/偏度/VaR）</div><div id="radar" class="chart-small"></div></div>
<div class="card-sub">AUDJPY日线量化: |Hurst|=""" + str(round(h_abs,2)) + """ (趋势型>0.55利于持仓), |Z|=""" + str(round(z_abs,2)) + """, 年化|Sharpe|=""" + str(round(sh_abs,2)) + """, |Sortino|=""" + str(round(so_abs,2)) + """, |偏度|=""" + str(round(sk_abs,2)) + """, 日VaR95%=""" + str(round(var95,2)) + """%。量化健康度中等, 支持"持有不加仓"判定; 厚尾风险(CPI)下不放大仓位。</div></div>"""
# ===================== ⑩ 概率情景预案 (表格) =====================
sec10 = """<div class="section"><div class="section-title">🎲 十、AUDJPY 持仓 · 三情景预案（表格化 · 只准备不预测）</div>
<table>
<tr><th style="width:15%">情景</th><th style="width:8%">概率</th><th style="width:31%">触发路径</th><th style="width:30%">操作</th><th style="width:16%">预期结果</th></tr>
<tr><td class='red'>🐻 情景A<br>CPI超预期→加息强化<br><span style="font-size:11px;color:#8a9bc0">(基准情景)</span></td><td class='yellow'>~45%</td>
<td>CPI≥3.4% → 美债收益率↑ → 美元↑ + 套息继续平仓 → AUDJPY 下探 110.06 → 破位看 109.78/109.24</td>
<td>减仓后剩余 """ + str(POS["lots_now"]) + """ 手持有 → 110.06 再平 0.005 手 → 剩余移动止损 → 109.78-109.24 全平</td>
<td class='green'>+$9.8 ~ +$15.6<br><span style="font-size:11px;color:#8a9bc0">(剩余仓位)</span></td></tr>
<tr><td class='yellow'>🐂 情景B<br>CPI低于预期→加息降温<br><span style="font-size:11px;color:#8a9bc0">AUDJPY反弹</span></td><td class='yellow'>~40%</td>
<td>CPI&lt;3.4% 且核心&lt;2.4% → 美债收益率↓ → 风险资产反弹 → AUDJPY 回踩 110.82-111.30</td>
<td>1H 收盘收复 110.82 → 剩余 """ + str(POS["lots_now"]) + """ 手立即全平 (接受 +$26 总利润) → 不与结构争辩</td>
<td class='green'>总利润锁定 +$26 ~ +$32<br><span style="font-size:11px;color:#8a9bc0">(已减仓50%保住了)</span></td></tr>
<tr><td class='red'>⚡ 情景C<br>CPI大超预期+日元干预<br><span style="font-size:11px;color:#8a9bc0">(尾部风险)</span></td><td class='yellow'>~15%</td>
<td>CPI≥3.6% → 美元飙升 + 日本财务省进场干预 → AUDJPY 双向扫损, 波动率 V 型</td>
<td>SL 111.70 被触发 → 市价立即离场, 不补仓不反手 → 观望 24h 等波动率回落</td>
<td class='red'>最大损失 -$""" + str(POS["risk_rest"]) + """<br><span style="font-size:11px;color:#8a9bc0">(已减仓控制在 """ + str(POS["risk_rest_pct"]) + """% 账户内)</span></td></tr>
</table></div>"""

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
<div class="card-sub" style="margin-bottom:8px" id="k_pipinfo">AUDJPY 当前价 """ + str(POS["cur"]) + """ · 每 pip 价值 ≈ $""" + str(KELLY["pip_val"]) + """/0.01手</div>
<div class="input-group"><label>投资标的</label><select id="k_inst" onchange="onInst()" style="flex:1;background:rgba(0,0,0,.3);border:1px solid rgba(74,127,255,.5);border-radius:6px;padding:8px;color:#fff;font-weight:600">
<option value="AUDJPY" selected>AUDJPY 澳元/日元（当前持仓）</option>
<option value="USDJPY">USDJPY 美元/日元</option>
<option value="EURUSD">EURUSD 欧元/美元</option>
<option value="GBPUSD">GBPUSD 英镑/美元</option>
<option value="XAUUSD">XAUUSD 现货黄金</option>
<option value="XAGUSD">XAGUSD 现货白银</option>
<option value="USOIL">USOIL WTI 原油</option>
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
<tr><td id="o_cur_lbl">当前 """ + str(POS["lots_open"]) + """ 手</td><td class='red' style="text-align:right" id="o_cur">超配 """ + str(KELLY["over"]) + """% ⚠</td></tr>
<tr><td>建议操作</td><td class='green' style="text-align:right" id="o_act">减至 """ + str(POS["lots_now"]) + """ 手 (接近半凯利)</td></tr>
</table></div>
</div>
<div class="verdict-warn" style="margin-top:12px"><b>💡 凯利公式使用注意:</b> ① 凯利假设连胜连败分布均匀, 但实际交易存在连续亏损期, 因此<b class="yellow">半凯利是实战最优解</b>; ② 单笔风险 ≤1% 是硬纪律, 凯利结果超过 1% 时以 1% 为准 (本例 0.5% 账户风险 = $2.87 = 0.003 手, 远低于凯利理论值, 说明小账户的真实约束是「1% 纪律」而非凯利); ③ 凯利只适用于正期望值系统 (胜率×盈亏比 &gt; 1), 负期望系统任何仓位都是错的; ④ <b class="yellow">切换投资标的时</b>, 右侧自动代入该品种的 pip 价值与参考止损距离, 但胜率/盈亏比应替换为该标的自身回测参数 (左侧默认展示 AUDJPY 样本), 再点「重新计算」。</div>
</div>
<script>
var INST={
 "AUDJPY":{pip:0.864,sl:116,px:"110.54",note:"0.01手=1000单位, pip=0.01"},
 "USDJPY":{pip:0.650,sl:120,px:"154.10",note:"0.01手=1000单位, pip=0.01"},
 "EURUSD":{pip:1.000,sl:80,px:"1.16067",note:"0.01手=1000单位, pip=0.0001"},
 "GBPUSD":{pip:1.000,sl:90,px:"1.35041",note:"0.01手=1000单位, pip=0.0001"},
 "XAUUSD":{pip:1.000,sl:40,px:"4335.84",note:"0.01手=1盎司, 按$1波动计"},
 "XAGUSD":{pip:0.500,sl:200,px:"63.82",note:"0.01手=50盎司, pip=0.01"},
 "USOIL":{pip:0.100,sl:150,px:"97.69",note:"0.01手=10桶, pip=0.01"}
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
  var lots=maxloss/(slp*window._pip*100);
  document.getElementById('o_pct').innerHTML=(fplan*100).toFixed(1)+'%';
  document.getElementById('o_loss').innerHTML='$'+maxloss.toFixed(2);
  document.getElementById('o_lots').innerHTML=lots.toFixed(3)+' 手';
  var inst=document.getElementById('k_inst').value;
  if(inst==="AUDJPY"){
    document.getElementById('o_cur_lbl').innerHTML='当前 0.02 手';
    document.getElementById('o_cur').innerHTML='超配 150% ⚠';
    document.getElementById('o_act').innerHTML='减至 0.01 手 (接近半凯利)';
  }else{
    document.getElementById('o_cur_lbl').innerHTML='当前持仓';
    document.getElementById('o_cur').innerHTML='未持仓 · 新开仓评估';
    document.getElementById('o_act').innerHTML='若建仓 ≤ '+lots.toFixed(3)+' 手';
  }
}
</script>"""

# ===================== ⑫ 相关性热力图 + 解读 =====================
sec12 = """<div class="section"><div class="section-title">🔗 十二、收益相关性热力图（60日收益 Pearson · 组合暴露诊断）</div>
<div class="chart-box"><div class="chart-title">🔗 6标的日收益相关性热力图</div><div id="corr" class="chart"></div></div>
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
<div class="card-sub">占净值: <b class="yellow">上限 1%</b></div></div>
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
<div class="chart-box"><div class="chart-title">📈 账户权益曲线（模拟 · 基于 AUDJPY 持仓）</div><div id="equity" class="chart-medium"></div></div>
<div class="verdict-warn"><b>⚠️ 风险预警（共 1 项）</b><br>
<b>1. 单笔风险超标:</b> 本笔 AUDJPY 原始风险 2% ($""" + str(POS["risk_orig"]) + """), 已超 ≤1% 纪律。减仓 50% 后剩余风险 $""" + str(POS["risk_rest"]) + """ (""" + str(POS["risk_rest_pct"]) + """%), 仍略超。<b class="yellow">建议下一笔交易严格控制在 0.5% 以内</b>, 用两到三笔盈利把账户做上 $600+, 再恢复 1% 标准。<b class="red">小账户保命优先。</b></div>
</div>"""

# ===================== ⑭ 动态止损方案对比 =====================
sec14 = """<div class="section"><div class="section-title">🛡️ 十四、动态止损方案对比</div>
<div class="card-sub" style="margin-bottom:10px">对 AUDJPY 持仓给出三种止损方案, 推荐方案已标注。止损不是越紧越好, 也不是越宽越好, 而是与波动率匹配。</div>
<div class="chart-box"><div class="chart-title">📊 三种止损方案 · 风险收益对比</div><div id="stopcmp" class="chart-medium"></div></div>
<table>
<tr><th style="width:16%">方案</th><th style="width:28%">ATR止损 (1.5×D ATR)</th><th style="width:28%">结构止损 (EMA10上方)</th><th style="width:28%" class="green">移动止损 (推荐 ★)</th></tr>
<tr><td>止损位</td><td>""" + STOPS["atr"]["lvl"] + """</td><td>""" + STOPS["struct"]["lvl"] + """</td><td class="green">""" + STOPS["trail"]["lvl"] + """</td></tr>
<tr><td>止损距离</td><td>""" + STOPS["atr"]["dist"] + """</td><td>""" + STOPS["struct"]["dist"] + """</td><td class="green">""" + STOPS["trail"]["dist"] + """</td></tr>
<tr><td>单笔风险 (0.01手)</td><td>$""" + str(STOPS["atr"]["risk"]) + """</td><td>$""" + str(STOPS["struct"]["risk"]) + """</td><td class="green">递减中</td></tr>
<tr><td>被扫概率</td><td>~""" + str(STOPS["atr"]["sweep"]) + """% (较宽松)</td><td>~""" + str(STOPS["struct"]["sweep"]) + """% (适中)</td><td class="green">随趋势下降</td></tr>
<tr><td>保住利润</td><td>少 (回撤多)</td><td>中</td><td class="green">多 (SL只向盈利移)</td></tr>
<tr><td>适用场景</td><td>""" + STOPS["atr"]["scene"] + """</td><td>""" + STOPS["struct"]["scene"] + """</td><td class="green">""" + STOPS["trail"]["scene"] + """</td></tr>
</table>
<div class="verdict" style="margin-top:12px"><b>💡 最终推荐: 移动止损方案</b><br>
当前阶段 = <b>趋势尾部</b> (已走 403 pips, Hurst 0.93 但 Z -1.81), 最合适的是移动止损 + 分批止盈组合:<br>
① 立即将 SL 从 113.284 上移至 <b class="yellow">111.70</b> (日线 EMA10 上方 1 点) → 锁定 $26 利润的 50% 部分<br>
② 价格触及 <b class="yellow">110.06</b> 再平 25% → SL 下移至 110.82 (1H 中枢)<br>
③ 剩余仓位用 <b class="yellow">1H EMA20</b> 跟踪止损, 收盘站上 EMA20 即全平<br>
<b>核心逻辑:</b> 趋势尾部用移动止损"让利润奔跑", 同时分批止盈"把钱装进口袋", 两者结合兼顾趋势延续和利润保护。</div>
</div>"""
# ===================== ⑮ 综合判定与操作建议 (图5: 诊断+三情景+最终推荐表+其余7标+总判定) =====================
o7_rows = ""
for sym, verdict, reason in OTHER7:
    vcls = "red" if verdict == "不建议建仓" else "yellow"
    o7_rows += ("<tr><td class='white'>" + sym + "</td><td class='" + vcls + "'>" + verdict + "</td><td>" + reason + "</td></tr>")
sec15 = """<div class="section"><div class="section-title">💡 十五、综合判定与操作建议</div>
<div class="sub-title">15.1 AUDJPY 持仓诊断（entry 114.573 · SELL 0.02 手 · 原 SL 113.284 · TP 109.781）</div>
<div class="grid grid-4">
<div class="card"><div class="card-title">💰 浮盈状态</div>
<div class="card-value" style="color:#2ecc71">+403.3 pips</div>
<div class="card-sub">+$""" + str(ACC["floating"]) + """ (+""" + str(POS["pct"]) + """%)<br>当前价 """ + str(POS["cur"]) + """</div></div>
<div class="card"><div class="card-title">🎯 至 TP / 至原 SL</div>
<div class="card-value" style="color:#3498db">75.9 / 274.4</div>
<div class="card-sub">pips（至 TP 109.781 / 至原 SL 113.284）<br>新 SL 已收紧至 111.70</div></div>
<div class="card"><div class="card-title">🧭 三周期方向</div>
<div class="card-value" style="color:#e74c3c">W/D/H1 全空</div>
<div class="card-sub">周线/日线/1H 三周期共振空头排列, 趋势完整</div></div>
<div class="card"><div class="card-title">⚠️ 事件风险</div>
<div class="card-value" style="color:#e74c3c">CPI ★★★★★</div>
<div class="card-sub">今晚 20:30 公布 · 预期 ±50-80 pips 双向跳空</div></div>
</div>
<div class="sub-title">15.2 三种情景（按纪律二选一执行，禁止 C 项）</div>
<div class="scenario-card scenario-neutral"><div class="scenario-head"><span class="scenario-title">🐻 情景 A（激进 · 减仓+CPI 赌博）</span><span class="scenario-prob yellow">否决</span></div>
<div class="scenario-actions">持仓过 CPI 赌方向 —— 预期 ±150 pips 双向扫损, 剩余利润 $26.11 vs 潜在亏损 $11.54 → R:R 仅 1:2.26; 违反「事件前 4h 不开新仓」延伸原则 → <b class='red'>否决</b>。</div></div>
<div class="scenario-card scenario-bullish"><div class="scenario-head"><span class="scenario-title">🛡️ 情景 B（稳健 · 减仓+收紧）</span><span class="scenario-prob green">推荐 ★</span></div>
<div class="scenario-actions">20:00 前平 50%（0.01 手）@110.54 → 锁 +$26.11; SL 改 111.70（EMA10 上方 1 点）→ 剩余风险 $7.51（1.3%）; 110.06 再平 25% → TP1 109.78-109.24; 剩余 0.005 手 1H EMA20 跟踪 → 收盘站上全平。</div></div>
<div class="scenario-card scenario-bearish"><div class="scenario-head"><span class="scenario-title">⛔ 情景 C（不平仓硬扛 · 不接受）</span><span class="scenario-prob red">不接受</span></div>
<div class="scenario-actions">持仓不动等待 TP, 承受 CPI 双向 150 pips 扫损风险（-$11.54）→ 当前至 TP 仅 70 pips 的概率结构下, 一次反弹即抹去一周利润。</div></div>
<div class="recommendation" style="margin-top:14px"><h3>🎯 最终推荐：情景 B（进取派）—— 20:00 前执行完毕</h3>
<table><tr><th style="width:16%">项目</th><th>具体操作</th></tr>
<tr><td>交易标的</td><td>AUDJPY（持有浮盈空单, 非新开仓）</td></tr>
<tr><td>方向 / 手数</td><td>SELL 0.02 手 → 20:00 前平 50%（0.01 手）, 保留 0.01 手</td></tr>
<tr><td>止盈</td><td>TP1 109.781（三周期共振目标, -75.9 pips）/ TP2 109.24（破位延伸）</td></tr>
<tr><td>止损</td><td>新 SL <b class='yellow'>111.70</b>（日线 EMA10 上方外扩 1 点）</td></tr>
<tr><td>平仓时机</td><td>① 20:00 前平 50% → ② 110.06 再平 25% → ③ 剩余 1H EMA20 跟踪</td></tr>
<tr><td>计划失效条件</td><td>CPI 公布瞬间若跳空越过 111.70, <b class='red'>市价单立即离场不等待</b></td></tr>
<tr><td>备注</td><td>本笔原始风险 2% 已超 ≤1% 纪律, 减仓后剩余 1.3% 仍略超 → <b class='yellow'>下一笔严格 0.5% 以内</b></td></tr>
</table></div>
<div class="sub-title">15.3 其余 7 标的判定</div>
<table><tr><th style="width:14%">标的</th><th style="width:14%">判定</th><th>理由</th></tr>""" + o7_rows + """</table>
<div class="verdict" style="margin-top:14px"><b>今日总判定</b><br>
<b>【今日无新仓】</b> —— 全场唯一动作是管理 AUDJPY 空单（情景 B：减仓 50% + SL 收至 111.70）。评分卡 82 分 + 凯利超配 + R:R 倒挂 + CPI 五星事件, 四维一致指向「持盈减仓」。<b>空仓即结论, 错过即纪律。</b></div>
</div>"""

# ===================== ⑯ 引用与依据 =====================
sec16 = """<div class="section"><div class="section-title">📚 十八、引用与依据</div>
<table><tr><th>数据</th><th>源</th><th>截至</th></tr>
<tr><td>实时报价(XAU/XAG/EUR/GBP/JPY/OIL/AUD)</td><td>金十 / sina</td><td>2026-09-11 13:38-16:05</td></tr>
<tr><td>利率曲线(DGS/TIPS/盈亏平衡/2s10s)</td><td>FRED</td><td>2026-09-09/10(盘中10Y 4.98% 金十)</td></tr>
<tr><td>央行政策利率</td><td>BIS WS_CBPOL</td><td>2026-09-08</td></tr>
<tr><td>原油库存/地缘</td><td>EIA / 金十快讯</td><td>2026-09-04 / 09-11</td></tr>
<tr><td>持仓拥挤度(GOLD/WTI/JPY/AUD)</td><td>CFTC COT</td><td>2026-09-01 / 08-25</td></tr>
<tr><td>日K线(6标的)</td><td>Twelve Data</td><td>2026-02至09-11</td></tr>
<tr><td>宏观事件(CPI/Fed/PPI/ECB)</td><td>金十快讯</td><td>2026-09-11</td></tr>
</table></div>"""

# ===================== ⑰ 交易决策日志 (移至末段) =====================
sec17 = """<div class="section"><div class="section-title">📓 十六、交易决策日志</div>
<div class="card-sub" style="margin-bottom:10px">每笔交易完成后填写此日志, 积累 20 笔后统计信号胜率, 找出真正擅长的模式。没有日志的交易 = 赌博。</div>
<div class="card"><div class="card-title">📋 当前持仓日志 · AUDJPY 空单（进行中）</div>
<table class="journal-table">
<tr><th style="width:18%">项目</th><th>内容</th></tr>
<tr><td>交易标的</td><td class='white'>AUDJPY</td></tr>
<tr><td>方向 / 手数</td><td><span class='red'>SELL """ + str(POS["lots_open"]) + """ 手</span> → 计划减至 """ + str(POS["lots_now"]) + """ 手</td></tr>
<tr><td>入场价 / 时间</td><td>114.573 / 2026-09-02 (凌晨)</td></tr>
<tr><td>止损 / 止盈</td><td>原 SL 113.284 → <b class='yellow'>新 SL 111.70</b> / TP 109.781</td></tr>
<tr><td>入场核心理由 (3条)</td><td>① W/D/4H 三周期共振空头排列 (技术面)<br>② BoJ 加息预期 vs 澳洲按兵不动 (宏观方向)<br>③ Hurst 0.93 强趋势 + OTC 经历转折 (量化/情绪面)</td></tr>
<tr><td>入场时信心指数</td><td><b class='green'>8/10</b> — 三周期 + 宏观双确认</td></tr>
<tr><td>入场时情绪状态</td><td>冷静 / 按计划执行 ✓</td></tr>
<tr><td>最大浮盈 / 当前浮盈</td><td class='green'>+403 pips / +$""" + str(ACC["floating"]) + """ (+""" + str(POS["pct"]) + """%)</td></tr>
<tr><td>当前状态</td><td><b class='yellow'>持仓中 · 减仓区间</b> — 已走约 75% 预期幅度</td></tr>
<tr><td>离场计划 (明确)</td><td>① 20:00 前平 50% (0.01手) @110.54 → 锁定 +$26.11<br>② SL 上移至 111.70 (日线 EMA10 上方)<br>③ 110.06 再平 25% (0.005手)<br>④ 剩余用 1H EMA20 跟踪, 收盘站上即全平</td></tr>
<tr><td>可能出错的地方</td><td>① CPI 低于预期致 USD 反弹 → <span class='green'>已减仓锁定利润</span><br>② 日央行突然干预 → <span class='green'>SL 已收紧至 111.70</span><br>③ 流动性枯竭跳空 → <span class='yellow'>接受滑点, 不追</span></td></tr>
</table></div></div>"""

# ===================== ⑱ 信号历史回测 (移至末段) =====================
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
<div class="card"><div class="card-title">✅ 策略有效</div><div class="card-sub" style="line-height:1.8">1. 胜率 66.7% + 盈亏比 1.85 → 期望值 +0.57R/笔, 正期望系统<br>2. 利润因子 2.75, 远高于 1.5 的合格线<br>3. 最大连败仅 2 次, 心理压力可控</div></div>
<div class="card"><div class="card-title">⚠️ 需要警惕</div><div class="card-sub" style="line-height:1.8">1. 12 笔样本量不足, 真实胜率可能在 50-80% 区间波动<br>2. 黄金样本极少 (仅 1 笔), 不能据此评估黄金信号<br>3. 当前处于紧缩 Regime, 空头信号表现优于多头, Regime 切换后需重新验证</div></div>
<div class="card"><div class="card-title">🔧 优化方向</div><div class="card-sub" style="line-height:1.8">1. 加入 Hurst &gt; 0.7 过滤 → 可剔除震荡市假信号<br>2. 加入 CFTC 拥挤度反向过滤 → 避开极端拥挤区<br>3. 只做三周期完全共振 → 牺牲交易次数换更高胜率<br>4. 趋势尾部减仓 → 当前这一笔正在验证此规则</div></div>
<div class="card"><div class="card-title">📅 长期预测</div><div class="card-sub" style="line-height:1.8">1. 按 1% 风险/笔, 月均 4-6 笔信号估算<br>2. 月预期收益: 4 × 0.57R = +2.28% ~ +3.42%<br>3. 年化预期: +27% ~ +41% (半凯利下)<br>4. 最大回撤预期: -5% ~ -8% (3-4 次连败)</div></div>
</div></div>"""

# ===================== ⑲ 交易纪律 (图3: 核心铁律 + 6类×4条 · 永远置末) =====================
disc_cards = ""
for cat, items in DISCIPLINE6:
    lis = "".join(["<li>" + i + "</li>" for i in items])
    disc_cards += ('<div class="discipline-item"><h4>📌 ' + cat + '</h4><ol>' + lis + '</ol></div>')
sec19 = """<div class="section"><div class="section-title">🛡️ 十九、交易纪律（永远置末）</div>
<div class="discipline"><h3>🔥 最核心铁律: 「风控第一, 盈利第二; 纪律第一, 机会第二」</h3>
<div class="card-sub" style="color:#e8d0a0;margin-bottom:12px">本笔 AUDJPY 原始风险 2% 已超纪律上限; 今日唯一正确动作是「减仓 + 收紧止损 + 空仓过 CPI」。</div>
<div class="discipline-grid">""" + disc_cards + """</div></div></div>"""

# ===================== 汇总拼装 (分析→交易逻辑顺序) =====================
html += (sec01 + sec02 + sec03 + sec04 + sec05 + sec06 + sec07 + sec08 + sec09
         + sec10 + sec11 + sec12 + sec13 + sec14 + sec15 + sec17 + sec18 + sec16 + sec19)

html += """<div class="footer">kingforex-skill v2.3 决策增强版｜ 基准 """ + NOW + """ ｜ 数据溯源见⑯ ｜ 本分析仅供决策参考, 不代客下单, 不自动交易</div>
</div>
<script>
""" + "\n".join(charts_js) + """
echarts.init(document.getElementById('corr')).setOption(""" + json.dumps(corr_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('cross')).setOption(""" + json.dumps(cross_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('radar')).setOption(""" + json.dumps(radar_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('equity')).setOption(""" + json.dumps(equity_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('stopcmp')).setOption(""" + json.dumps(stop_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('rcurve')).setOption(""" + json.dumps(rcurve_opt, ensure_ascii=False) + """);
</script></body></html>"""

path = os.path.join(OUT, "今日行情分析_决策增强版_v2.3_2026-09-11.html")
open(path, "w", encoding="utf-8").write(html)
print("HTML written:", path, len(html), "bytes | charts:", len(charts_js))

# ===================== MD 双版本 (19节新顺序) =====================
md = []
md.append("# 今日行情分析 · 决策增强版 v2.3")
md.append("> 基准时间: **" + NOW + "** ｜ kingforex-skill ｜ 数据溯源见第十六节")
md.append("")
md.append("## 一、今日决策总览")
md.append("| 账户状态 | 信号质量 | 凯利最优仓位 | 今日最大风险 |")
md.append("| :--- | :--- | :--- | :--- |")
md.append("| **$" + str(ACC["equity"]) + "** (浮盈+$" + str(ACC["floating"]) + ") | **B+** (8标的加权) | **" + str(KELLY["rec_lots"]) + "手** (f*=" + str(int(KELLY["f"])) + "%) | **CPI ★★★★★** (20:30) |")
md.append("| 持仓风险/上限5% | 可交易1个·观望7个 | 当前" + str(POS["lots_open"]) + "手超配" + str(KELLY["over"]) + "%→减至" + str(POS["lots_now"]) + "手 | ±50-80pips·20:00前减仓 |")
md.append("")
md.append("## 二、今日交易计划（建仓 / 持仓判定）")
md.append("**【建仓判定：今日不适宜建仓 —— 不建仓】** 理由(四维一致否决): ①宏观(CPI事件+10Y逼5%); ②评分(8标的均<75); ③凯利(新开仓=0); ④拥挤度(黄金89%/WTI97%)。**空仓即结论, 错过即纪律。**")
md.append("")
md.append("**2.1 持仓计划（现有持仓）**")
md.append("| 项目 | 内容 |")
md.append("| :--- | :--- |")
md.append("| 交易标的 | AUDJPY |")
md.append("| 方向/手数 | SELL " + str(POS["lots_open"]) + "手 → 计划减至" + str(POS["lots_now"]) + "手 |")
md.append("| 入场价/时间 | 114.573 / 2026-09-02(凌晨) |")
md.append("| 止损/止盈 | 原SL 113.284→新SL 111.70 / TP 109.781 |")
md.append("| 入场核心理由 | ①W/D/4H三周期共振空头排列; ②BoJ加息预期vs澳洲按兵不动; ③Hurst0.93强趋势+OTC转折 |")
md.append("| 入场信心指数 | 8/10(三周期+宏观双确认) |")
md.append("| 入场情绪状态 | 冷静/按计划执行✓ |")
md.append("| 最大/当前浮盈 | +403pips / +$" + str(ACC["floating"]) + "(+" + str(POS["pct"]) + "%) |")
md.append("| 当前状态 | 持仓中·减仓区间(已走75%预期幅度) |")
md.append("| 离场计划 | ①20:00前平50%@110.54锁定+$26.11; ②SL上移111.70; ③110.06再平25%; ④剩余1H EMA20跟踪全平 |")
md.append("| 可能出错 | ①CPI低于预期致USD反弹→已减仓锁利; ②日央行干预→SL已收紧111.70; ③流动性枯竭跳空→接受滑点不追 |")
md.append("")
md.append("## 三、分析标的快照（现价/日内%/区间/结构/MTF/计划判定）")
md.append("| 标的 | 现价 | 日内% | 日内区间 | 趋势/结构 | MTF方向 | 计划判定 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
for s in ["XAUUSD","XAGUSD","DXY","EURUSD","GBPUSD","USDJPY","USOIL","AUDJPY"]:
    px, pct, rng = snap_metrics(s); ex = SNAP_EXTRA[s]
    md.append("| " + s + " | " + str(px) + " | " + pct + " | " + rng + " | " + ex["struct"] + " | " + ex["mtf"] + " | " + ex["plan"] + " |")
md.append("")
md.append("> " + DAY_THEME.replace("<b class='yellow'>", "**").replace("</b>", "**"))
md.append("")
md.append("## 四、8标的综合评分卡（≥75可建仓）")
md.append("| 品种 | 宏观 | 技术 | 量化 | 情绪 | 综合 | 判定 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
for s in ["XAUUSD","XAGUSD","DXY","EURUSD","GBPUSD","USDJPY","USOIL","AUDJPY"]:
    d = SCORES[s]; tot = round(d["macro"]*0.25+d["tech"]*0.30+d["quant"]*0.25+d["sent"]*0.20)
    md.append("| " + s + " | " + str(d["macro"]) + " | " + str(d["tech"]) + " | " + str(d["quant"]) + " | " + str(d["sent"]) + " | **" + str(tot) + "** | " + d["verdict"] + " |")
md.append("")
md.append("## 五、宏观金融面")
md.append("**5.1 央行政策对比表（BIS 2026-08 ｜ 金十快讯）**")
md.append("| 央行 | 政策利率 | 最近动作 | 周期定位 | 对市场 |")
md.append("| :--- | :--- | :--- | :--- | :--- |")
for bank, rate, action, cyc, cyccls, impact in CB_POLICY:
    md.append("| " + bank + " | " + rate + " | " + action + " | " + cyc + " | " + impact + " |")
md.append("")
md.append("- **5.2 利率地基**(FRED截至09-09/10; 盘中10Y=4.98%): DGS10=4.83% / DFII10(实际)=2.46% / T10YIE=2.40% / 2s10s=0.39% / FEDFUNDS=3.63%")
md.append("")
md.append("**5.3 利差结构（套息交易视角）**")
md.append("| 利差对 | 当前值 | 趋势 | 解读 |")
md.append("| :--- | :--- | :--- | :--- |")
for pair, val, trend, note in CARRY2:
    md.append("| " + pair + " | " + val + " | " + trend + " | " + note + " |")
md.append("> 🔥 结论: 套息结构仍为正, 但方向由「利差收益」切换为「平仓冲击」——BoJ 加息是日元交叉盘最大反向变量, 主导 AUDJPY/USDJPY 三周期空头排列。加息周期中的套息盘平仓是趋势放大器, 不是噪音。")
md.append("")
md.append("**5.4 地缘 + 风险偏好**")
for title, body in GEO_RISK:
    md.append("- **" + title + "**: " + body)
md.append("")
md.append("**5.5 宏观大事综合（每标 2 条 · 明确影响）**")
import re as _re
for sym, events in MACRO2:
    txt = _re.sub(r"<[^>]+>", "", events)
    md.append("- 【" + sym + "】" + txt)
md.append("")
md.append("## 六、当日数据 + 议息")
md.append("**6.1 ✅ 今日已公布**")
md.append("| 时间 | 数据 | 实际 | 预期 | 前值 | 影响 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
for t, ev, act, exp, prev, impact, icls in CAL_PUB:
    md.append("| " + t + " | " + ev + " | " + act + " | " + exp + " | " + prev + " | " + impact + " |")
md.append("")
md.append("**6.2 🔴 今日待公布（关键）**")
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
md.append("> ⚠ 事件纪律: 今晚 CPI 前 4 小时（≤16:30）不开任何新仓; 已有持仓 20:00 前完成减仓/收紧 SL; CPI 公布后等第一波方向走完（≥15分钟）再评估, 不追第一根 K 线。")
md.append("")
md.append("## 七、跨市场验证")
md.append("- 黄金vs实际利率(负向,2.46%高位压制); 原油vs中东(97%拥挤警惕回落); AUDJPYvs美日利差(套息3.35%支撑)。宏观与跨市场未给出低不确定共振方向, 事件前谨慎。")
md.append("")
md.append("## 八、多周期共振 + 关键位")
md.append("- 6标的日K图见HTML版; XAGUSD/USOIL Twelve Data 404/iTick限频, 按铁律不编造价格。")
md.append("| 品种 | 关键位 | 类型 | 作用 |")
md.append("| :--- | :--- | :--- | :--- |")
for v, kl, tp, act in keylevels:
    md.append("| " + v + " | " + kl + " | " + tp + " | " + act + " |")
md.append("")
md.append("## 九、量化验证（AUDJPY样本）")
md.append("- |Hurst|=" + str(round(h_abs,2)) + "(趋势型>0.55利于持仓) ｜ |Z|=" + str(round(z_abs,2)) + " ｜ 年化|Sharpe|=" + str(round(sh_abs,2)) + " ｜ |Sortino|=" + str(round(so_abs,2)) + " ｜ |偏度|=" + str(round(sk_abs,2)) + " ｜ 日VaR95%=" + str(round(var95,2)) + "%")
md.append("")
md.append("## 十、AUDJPY 持仓 · 三情景预案")
md.append("| 情景 | 概率 | 触发路径 | 操作 | 预期结果 |")
md.append("| :--- | :--- | :--- | :--- | :--- |")
md.append("| 🐻 A. CPI超预期(基准) | ~45% | CPI≥3.4%→美债收益率↑→AUDJPY下探110.06→破位109.78/109.24 | 减仓后剩余" + str(POS["lots_now"]) + "手持有→110.06再平0.005手→剩余移动止损→109.78-109.24全平 | +$9.8~+$15.6 |")
md.append("| 🐂 B. CPI低于预期 | ~40% | CPI<3.4%且核心<2.4%→美债收益率↓→AUDJPY回踩110.82-111.30 | 1H收盘收复110.82→剩余" + str(POS["lots_now"]) + "手立即全平(接受+$26)→不与结构争辩 | 总利润+$26~+$32 |")
md.append("| ⚡ C. CPI大超预期+日元干预(尾部) | ~15% | CPI≥3.6%→美元飙升+日本干预→双向扫损 | SL 111.70触发→市价离场不补仓不反手→观望24h | 最大损失-$" + str(POS["risk_rest"]) + "(已控" + str(POS["risk_rest_pct"]) + "%) |")
md.append("")
md.append("## 十一、凯利仓位计算器（全标的适配）")
md.append("- 公式: **f*=(p×b−q)/b** ｜ 实战用半凯利(f*/2) ｜ **投资标的下拉选择框**: AUDJPY/USDJPY/EURUSD/GBPUSD/XAUUSD/XAGUSD/USOIL 全标的自动代入 pip 价值与参考止损距离, 切换后点「重新计算」")
md.append("- AUDJPY回测: p=" + str(KELLY["p"]) + "% ｜ b=" + str(KELLY["b"]) + " ｜ f*=" + str(KELLY["f"]) + "% ｜ 半凯利=" + str(KELLY["f_half"]) + "% ｜ 三分之一=" + str(KELLY["f_third"]) + "%")
md.append("- 本账户: 最优" + str(KELLY["f_half"]) + "% ｜ 最大可亏$" + str(KELLY["max_loss"]) + " ｜ 推荐" + str(KELLY["rec_lots"]) + "手 ｜ 当前" + str(POS["lots_open"]) + "手**超配" + str(KELLY["over"]) + "%**→减至" + str(POS["lots_now"]) + "手")
md.append("")
md.append("## 十二、相关性热力图 + 解读")
md.append("- 高度正相关: XAU↔XAG 0.92 / EUR↔GBP 0.85 / AUDJPY↔USDJPY -0.78; 低相关: USOIL↔AUDJPY 0.12 / XAU↔EUR 0.35 / DXY↔XAU -0.68")
md.append("- 组合诊断: AUDJPY空单1笔, 集中度低; 隐含暴露=日元走强+澳元走弱; 做多日元优先AUDJPY(方向更纯)")
md.append("")
md.append("## 十三、账户风险仪表盘")
md.append("- 净值$" + str(ACC["equity"]) + "(入金$" + str(int(ACC["deposit"])) + "+浮盈$" + str(ACC["floating"]) + ",累计+" + str(ACC["cum_ret"]) + "%) ｜ 单笔风险$" + str(POS["risk_usd"]) + "(剩余" + str(POS["lots_now"]) + "手@SL" + str(POS["sl_new"]) + ") ｜ 组合风险$" + str(POS["risk_usd"]) + " ｜ 最大回撤" + str(ACC["max_dd"]) + "%(安全区)")
md.append("- ⚠️ 风险预警: 单笔风险原始2%($" + str(POS["risk_orig"]) + ")超≤1%纪律, 减仓后剩余$" + str(POS["risk_rest"]) + "(" + str(POS["risk_rest_pct"]) + "%)仍略超 → 下一笔严格≤0.5%, 做上$600+再恢复1%。")
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
md.append("- 💡 推荐移动止损: ①SL上移111.70锁定$26利润50%; ②110.06再平25%→SL下移110.82; ③剩余1H EMA20跟踪全平。")
md.append("")
md.append("## 十五、综合判定与操作建议")
md.append("**15.1 AUDJPY 持仓诊断**: 浮盈 +403.3 pips (+$" + str(ACC["floating"]) + "/+" + str(POS["pct"]) + "%) ｜ 至TP/至原SL = 75.9/274.4 pips ｜ 三周期 W/D/H1 全空 ｜ 事件风险 CPI ★★★★★")
md.append("")
md.append("**15.2 三种情景（按纪律二选一执行，禁止 C 项）**")
md.append("- 🐻 情景A（激进·减仓+CPI赌博）→ **否决**: ±150pips双向扫损, R:R仅1:2.26, 违反事件前不开仓延伸原则")
md.append("- 🛡️ 情景B（稳健·减仓+收紧）→ **推荐★**: 20:00前平50%@110.54锁+$26.11; SL改111.70→剩余风险$7.51(1.3%); 110.06再平25%; 剩余1H EMA20跟踪全平")
md.append("- ⛔ 情景C（不平仓硬扛）→ **不接受**: 持仓不动等TP, 承受CPI双向150pips扫损(-$11.54), 一次反弹抹去一周利润")
md.append("")
md.append("**🎯 最终推荐：情景 B（进取派）—— 20:00 前执行完毕**")
md.append("| 项目 | 具体操作 |")
md.append("| :--- | :--- |")
md.append("| 交易标的 | AUDJPY（持有浮盈空单, 非新开仓） |")
md.append("| 方向/手数 | SELL 0.02手 → 20:00前平50%(0.01手), 保留0.01手 |")
md.append("| 止盈 | TP1 109.781(-75.9pips) / TP2 109.24(破位延伸) |")
md.append("| 止损 | 新SL 111.70（日线EMA10上方外扩1点） |")
md.append("| 平仓时机 | ①20:00前平50% → ②110.06再平25% → ③剩余1H EMA20跟踪 |")
md.append("| 计划失效条件 | CPI公布瞬间若跳空越过111.70, 市价单立即离场不等待 |")
md.append("| 备注 | 原始风险2%已超≤1%纪律, 减仓后1.3%仍略超 → 下一笔严格0.5%以内 |")
md.append("")
md.append("**15.3 其余 7 标的判定**")
md.append("| 标的 | 判定 | 理由 |")
md.append("| :--- | :--- | :--- |")
for sym, verdict, reason in OTHER7:
    md.append("| " + sym + " | " + verdict + " | " + reason + " |")
md.append("")
md.append("**今日总判定**: 【今日无新仓】—— 全场唯一动作是管理 AUDJPY 空单（情景B: 减仓50%+SL收至111.70）。评分卡82分+凯利超配+R:R倒挂+CPI五星事件, 四维一致指向「持盈减仓」。空仓即结论, 错过即纪律。")
md.append("")
md.append("## 十八、引用与依据")
md.append("| 数据 | 源 | 截至 |")
md.append("| :--- | :--- | :--- |")
md.append("| 实时报价 | 金十/sina | 2026-09-11 13:38-16:05 |")
md.append("| 利率曲线 | FRED | 09-09/10(盘中10Y 4.98% 金十) |")
md.append("| 政策利率 | BIS WS_CBPOL | 09-08 |")
md.append("| 原油/地缘 | EIA/金十 | 09-04 / 09-11 |")
md.append("| 持仓拥挤度 | CFTC COT | 09-01 / 08-25 |")
md.append("| 日K线 | Twelve Data | 02至09-11 |")
md.append("")
md.append("## 十六、交易决策日志")
md.append("（同 2.1 持仓计划表, 此处为日志记录版）AUDJPY SELL " + str(POS["lots_open"]) + "→减至" + str(POS["lots_now"]) + "手, 入场114.573, 新SL 111.70, TP 109.781, 浮盈+$" + str(ACC["floating"]) + "(+" + str(POS["pct"]) + "%), 已走75%预期幅度, 按4步离场计划执行。")
md.append("")
md.append("## 十七、信号历史回测（样本有限·仅供参考）")
md.append("- " + str(BT["n"]) + "笔 ｜ " + str(BT["win"]) + "胜/" + str(BT["loss"]) + "负 ｜ 胜率" + str(BT["winrate"]) + "% ｜ 盈亏比" + str(BT["pl"]) + ":1 ｜ 期望+" + str(BT["exp"]) + "R ｜ 回撤-" + str(BT["max_dd"]) + "R ｜ 利润因子" + str(BT["pf"]))
md.append("")
md.append("| # | 时间 | 标的 | 方向 | 入场价 | 出场价 | 盈亏(pips) | R倍数 | 结果 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
for num, dt, sym, dr, en, ex, pips, rmult, res in BT_SIGNALS:
    md.append("| " + num + " | " + dt + " | " + sym + " | " + dr + " | " + en + " | " + ex + " | " + pips + " | " + rmult + " | " + res + " |")
md.append("")
md.append("- 结论: ✅正期望(+0.57R/笔,利润因子2.75); ⚠️样本不足; 🔧加Hurst>0.7/CFTC过滤; 📅月均4-6笔,月预期+2.28%~+3.42%,年化+27%~+41%。")
md.append("")
md.append("## 十九、交易纪律（永远置末）")
md.append("**🔥 最核心铁律: 「风控第一, 盈利第二; 纪律第一, 机会第二」** ｜ 本笔 AUDJPY 原始风险 2% 已超纪律上限; 今日唯一正确动作是「减仓 + 收紧止损 + 空仓过 CPI」。")
md.append("")
for cat, items in DISCIPLINE6:
    md.append("- **" + cat + "**: " + "; ".join(items))
md.append("")
md.append("---")
md.append("kingforex-skill v2.3 决策增强版｜ 仅供决策参考, 不代客下单, 不自动交易")
md_path = os.path.join(OUT, "今日行情分析_决策增强版_v2.3_2026-09-11.md")
open(md_path, "w", encoding="utf-8").write("\n".join(md))
print("MD written:", md_path, len(md), "lines")

# ===================== 独立 Excel 复盘模板 (与 v2.1 一致) =====================
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
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
ws1.append(["交易复盘记录表（kingforex-skill v2.2）"]); ws1["A1"].font = title_font; ws1.append([])
cols1 = ["#","日期","品种","方向","手数","入场价","止损SL","目标TP","出场价","盈亏(pips)","盈亏($)","R倍数","结果(止盈/止损/手动)","入场理由(三维)","信心(1-10)","情绪状态","是否按计划","复盘备注"]
ws1.append(cols1); style_header(ws1, 3, len(cols1))
ws1.append(["12","2026-09-02","AUDJPY","SELL",0.02,114.573,111.70,109.781,"持仓中","+403","+52.23","+2.90R","进行中","W/D/4H三周期共振+BoJ加息预期vs澳洲按兵不动+Hurst0.93强趋势",8,"冷静/按计划","是","趋势尾部减仓,移动止损111.70"])
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
xl_path = os.path.join(OUT, "交易复盘模板_v2.3.xlsx")
wb.save(xl_path)
print("XLSX written:", xl_path)

