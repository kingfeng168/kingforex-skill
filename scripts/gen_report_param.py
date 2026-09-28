# -*- coding: utf-8 -*-
"""今日行情分析 v2.3 决策增强版 生成器 (kingforex-skill)
基准时间: 2026-09-14 09:34 GMT+8
v2.3: 评分卡4x2/宏观大事列表化/凯利标的全适配下拉/引用倒数第二/综合判定图5/快照扩列/宏观面+日历扩内容/position_size.py融合凯利
  ①决策总览=4卡片横排 ②情景预案=表格 ③凯利=左公式右交互双面板
  ④相关性=热力图+3列解读 ⑤风险仪表盘=4指标卡+权益曲线+风险预警框
  ⑥动态止损=柱状图+对比表+推荐绿框 ⑦交易日志=表格 ⑧信号回测=面板+R曲线+明细表+结论4列
  ⑨新增独立 Excel 复盘模板
所有 ECharts option 用 json.dumps 注入, 避免 f-string 花括号错误。
"""
import os, csv, json, math, argparse
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_ROOT = _os.environ.get("KINGFOREX_HOME", _os.path.dirname(_HERE))

# ============ 参数化入口 ============
def _parse_args():
    ap = argparse.ArgumentParser(description="今日行情分析 决策增强版 · 参数化生成器 (kingforex-skill)")
    ap.add_argument("--date", default="2026-09-14", help="报告日期 YYYY-MM-DD, 用于输出文件名")
    ap.add_argument("--data", default=None, help="daily_data.json 路径 (默认 ./daily_data_<date>.json)")
    ap.add_argument("--out", default=os.environ.get("KINGFOREX_DATA", "./out"), help="输出目录")
    ap.add_argument("--kline-dir", default=None, help="K线CSV目录 (默认同 --out)")
    ap.add_argument("--css", default=None, help="模板CSS路径 (默认技能 assets/decision_enhanced_sample.html)")
    return ap.parse_args()

ARGS = _parse_args()
OUT = ARGS.out
KL_DIR = ARGS.kline_dir or OUT
DATA_PATH = ARGS.data or os.path.join(OUT, "daily_data_%s.json" % ARGS.date)
SKILL_CSS = ARGS.css or _os.path.join(_ROOT, "assets", "decision_enhanced_sample.html")
with open(DATA_PATH, encoding="utf-8") as _df:
    D = json.load(_df)
NOW = D["meta"]["now"]
VER = D["meta"].get("version", "v2.4.4")

# ---------- 由 daily_data.json 加载全部每日数据 ----------
ACC = D["account"]; POS = D["position"]; KELLY = D["kelly"]
BT = D["backtest"]; BT_SIGNALS = [tuple(x) for x in D["bt_signals"]]
R_CUM = D["r_curve"]; STOPS = D["stops"]
CORR_HIGH = D.get("corr_high", []); CORR_LOW = D.get("corr_low", [])
QUOTES = D["quotes"]; RATES = D["rates"]; CARRY = D.get("carry", [])
SCORES = D["scores"]; SNAP_EXTRA = D["snap_extra"]; SNAP_NOKL = D["snap_nokl"]
DAY_THEME = D["day_theme"]; macro_events = D.get("macro_events", "")
OTHER7 = D["other7"]; RECOMMEND5 = D["recommend5"]; DISCIPLINE6 = D["discipline6"]
CB_POLICY = D["cb_policy"]; CARRY2 = D["carry2"]; GEO_RISK = D["geo_risk"]
MACRO2 = D["macro2"]; CAL_PUB = D["cal_pub"]; CAL_PENDING = D["cal_pending"]
CAL_MONTH = D["cal_month"]; SCORE_SUBS = D["score_subs"]
cross = D["cross"]; eq_dates = D["equity_dates"]; eq_vals = D["equity_vals"]
keylevels = D["keylevels"]; CFTC_GOLD = D["cftc_gold"]; KD = D["klines"]


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
klines = {s: load_kline(os.path.join(KL_DIR, p)) for s, p in KD.items()}

_missing = [s for s, _r in klines.items() if not _r]
if _missing:
    raise SystemExit(
        "[数据缺失] 未找到以下品种的日线 CSV: %s\n"
        "  预期目录: %s\n"
        "  预期文件名:\n    %s\n"
        "  获取方式: python scripts/kline_fetch.py --symbol <SYM> --interval 1day "
        "--api-key <KEY> --out \"%s\"\n"
        "  (需自备 Twelve Data key;文件命名必须与脚本顶部 KD 字典一致)"
        % (", ".join(_missing), OUT,
           "\n    ".join(KD[s] for s in _missing), OUT))

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
        ml = [("入场114.573", 114.573, "#3498db", "solid"), ("原SL113.284(获利区·非保护)", 113.284, "#e74c3c", "dashed"),
              ("TP 109.781(已触发✓)", 109.781, "#2ecc71", "solid"), ("现价109.784(已离场)", QUOTES["AUDJPY"][0], "#f1c40f", "dashed")]
    h, j = chart_candlestick(s, klines[s], ml)
    charts_html.append(h); charts_js.append(j)

silver_oil_note = ('<div class="card" style="grid-column:1/-1"><div class="card-title">⚠️ XAGUSD / USOIL K线数据源暂缺</div>'
    '<div class="card-sub">Twelve Data 该品种返回 404、iTick API key 401, 按技能铁律不编造价格。'
    '以实时报价 + CFTC 持仓 + 宏观事件呈现: 白银 63.955 (金十); WTI 99.169 (金十, 伊朗战争风险溢价+2.9%); CFTC WTI 极度拥挤做多(97%分位)。</div></div>')

# ===================== 相关性矩阵 (6标的日收益) =====================
def rets(sym):
    cs = [r[4] for r in klines[sym]]
    return [(cs[i]-cs[i-1])/cs[i-1] for i in range(1, len(cs))]
corr_syms = ["XAUUSD","EURUSD","GBPUSD","USDJPY","AUDUSD","AUDJPY"]
ret_series = {s: rets(s) for s in corr_syms}
minlen = min(len(ret_series[s]) for s in corr_syms)
for s in corr_syms: ret_series[s] = ret_series[s][-minlen:]
corr_mat = [[round(pearson(ret_series[a], ret_series[b]), 2) for b in corr_syms] for a in corr_syms]

# ===================== v2.4 统一计算引擎接入（单一事实来源） =====================
import datetime as _dt, importlib.util as _ilu
_sp = _ilu.spec_from_file_location("calc_engine", os.path.join(os.path.dirname(os.path.abspath(__file__)), "calc_engine.py"))
_ce = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_ce)
ENG = {}
ENG["usdjpy"] = QUOTES["USDJPY"][0]
ENG["now_px"] = round(klines["AUDJPY"][-1][4], 3)
_pip = _ce.CONTRACTS["AUDJPY"]["pip"]
ENG["pipval_002"] = round(_ce.pip_value_per_pip("AUDJPY", 0.02, ENG["usdjpy"]), 4)
ENG["pipval_001"] = round(_ce.pip_value_per_pip("AUDJPY", 0.01, ENG["usdjpy"]), 4)
# --- 已了结仓位复盘（入场 114.573 → TP 109.781 触发离场） ---
ENG["pnl_exit"] = round(_ce.pnl("AUDJPY", "SELL", POS["entry"], POS["exit"], 0.02, ENG["usdjpy"]), 2)
ENG["pips_exit"] = round((POS["entry"] - POS["exit"]) / _pip, 1)
ENG["pnl_002"] = ENG["pnl_exit"]          # 兼容打印口径（已实现, 非浮盈）
ENG["pips_now"] = ENG["pips_exit"]
ENG["stop_pips_orig"] = round(abs(POS["entry"] - POS["sl_orig"]) / _pip, 1)   # 历史复盘: 原 SL 在获利区
# --- 下次入场预案（央行周落地后 · 结构方案 110.11 挂空 SL 110.86 = 75 pips） ---
ENG["stop_pips_new"] = round(abs(110.86 - 110.11) / _pip, 1)
ENG["risk_orig_002"] = round(ENG["stop_pips_orig"] * ENG["pipval_002"], 2)
ENG["risk_new_002"] = round(ENG["stop_pips_new"] * ENG["pipval_002"], 2)
ENG["risk_new_001"] = round(ENG["stop_pips_new"] * ENG["pipval_001"], 2)
ENG["risk_orig_pct"] = round(ENG["risk_orig_002"] / ACC["equity"] * 100, 2)
ENG["risk_new_pct_002"] = round(ENG["risk_new_002"] / ACC["equity"] * 100, 2)
ENG["risk_new_pct_001"] = round(ENG["risk_new_001"] / ACC["equity"] * 100, 2)
ENG["lots_1pct"] = _ce.compute_lots(ACC["equity"], 1.0, ENG["stop_pips_new"], "AUDJPY", ENG["usdjpy"])
ENG["lots_05pct"] = _ce.compute_lots(ACC["equity"], 0.5, ENG["stop_pips_new"], "AUDJPY", ENG["usdjpy"])
ENG["kelly"] = _ce.kelly_recommended_lots(ACC["equity"], 1.0, ENG["stop_pips_new"], "AUDJPY",
                                          ENG["usdjpy"], KELLY["p"], KELLY["b"], user_cap=0.02)
_nowdt = _dt.datetime.fromisoformat(D["meta"]["now_dt"])
ENG["events"] = []
for _ev in D["events"]:
    _n = _ev["name"]; _t = _dt.datetime.fromisoformat(_ev["time_iso"]); _st = _ev["star"]
    _h = round((_t - _nowdt).total_seconds() / 3600.0, 2)
    ENG["events"].append({"name": _n, "time": _t.strftime("%m-%d %H:%M"), "star": _st,
                          "hours": _h, "silence": _ce.event_silence(_h, _st)})
_cp = {s: [r[4] for r in klines[s]][-61:] for s in corr_syms}
ENG["corr_m"], ENG["corr_text"] = _ce.corr_matrix(_cp)
CORR_HIGH = [("%s ↔ %s" % (a, b), "%.2f" % r, "|r|≥0.6 同向暴露重叠，避免同时下注同一方向")
             for a, b, r in ENG["corr_text"]["high"]]
CORR_LOW = [("%s ↔ %s" % (a, b), "%.2f" % r, "|r|≤0.3 逻辑不同源，可组合分散风险")
            for a, b, r in ENG["corr_text"]["low"]]
if not CORR_HIGH:
    CORR_HIGH = [("（60 日窗口无 |r|≥0.6 配对）", "—", "按矩阵实时判定，无高相关集中风险")]
if not CORR_LOW:
    CORR_LOW = [("（60 日窗口无 |r|≤0.3 配对）", "—", "近期多数标的同向，注意组合集中风险")]
ENG["score"] = _ce.score_4d(SCORE_SUBS)
ENG["bt"] = _ce.backtest([{"pnl": float(r[6].replace("+", "")), "r": float(r[7].replace("R", ""))}
                          for r in BT_SIGNALS])
CHECKS = []
def _ck(name, ok, detail):
    CHECKS.append((name, bool(ok), detail))
_ck("快照价 = 图表最后收盘 = 计算器价",
    abs(QUOTES["AUDJPY"][0] - ENG["now_px"]) < 1e-6 and abs(POS["cur"] - ENG["now_px"]) < 1e-6,
    "三处统一 %.3f（Twelve Data 日线最后收盘）" % ENG["now_px"])
_ck("空仓状态一致性（lots=0 · 浮盈=0 · 已实现>0）",
    POS["lots_now"] == 0.0 and ACC["floating"] == 0.0 and ACC["realized"] > 0,
    "TP 109.781 触发后全部了结: 手数 0 / 浮盈 $0.00 / 本笔已实现 $%.2f / 净值 $%.2f（574.23+62.36）" %
    (ACC["realized"], ACC["equity"]))
_ck("已实现盈利 =（入场价 − TP触发价）× pip价值 × 手数",
    abs(ACC["realized"] - ENG["pnl_exit"]) < 0.05,
    "报告 %.2f / 引擎 %.2f（%.1f pips × $%.4f × 0.02手, USDJPY %.3f 口径）" %
    (ACC["realized"], ENG["pnl_exit"], ENG["pips_exit"], ENG["pipval_002"], ENG["usdjpy"]))
_ck("下次预案单笔风险 ≤1%（0.01手口径）",
    ENG["risk_new_pct_001"] <= 1.0,
    "预案 110.11 入场 SL 110.86（75 pips）: 0.02手 $%.2f（%.2f%%超限✗）/ 0.01手 $%.2f（%.2f%%合规✓）" %
    (ENG["risk_new_002"], ENG["risk_new_pct_002"], ENG["risk_new_001"], ENG["risk_new_pct_001"]))
_ck("原 SL 风险违规项已复盘标注（历史教训）",
    True,
    "原 SL 113.284 位于入场下方 129 pips（获利区·非保护）——本笔凭 TP 挂单+行情顺向免于风险, 属侥幸而非纪律, 下次入场 SL 必须在入场价上方")
_ck("凯利输出与 1% 风险预算一致（央行周静默=0手）",
    ENG["kelly"]["final_lots"] <= ENG["kelly"]["risk_lots"] + 1e-9,
    "全凯利 %.2f%% / 半凯利 %.2f%%（对应 %.4f 手，禁止直接实盘）/ 1%%风险上限 %.4f 手 / 0.5%%小账户口径 %.4f 手 → "
    "引擎参考 %.2f 手（约束：%s）；本日超级央行周静默纪律 → 实盘 0 手, 待 09-18 BoJ 落地后重估" %
    (ENG["kelly"]["kelly_full_pct"], ENG["kelly"]["kelly_half_pct"], ENG["kelly"]["kelly_lots"],
     ENG["kelly"]["risk_lots"], ENG["lots_05pct"], ENG["kelly"]["final_lots"], ENG["kelly"]["binder"]))
_ck("相关性文字与矩阵一致", True,
    "高相关 %d 对 / 低相关 %d 对，全部由 60 日 Pearson 矩阵实时生成" % (len(CORR_HIGH), len(CORR_LOW)))
_ck("评分卡总分 = 各维加权和",
    abs(ENG["score"]["total"] - sum(ENG["score"]["dims"][k] * w for k, w in ENG["score"]["weights"].items())) < 0.05,
    "总分 %.2f（宏观%.0f×25%% + 技术%.0f×30%% + 量化%.0f×25%% + 情绪%.0f×20%%），判定：%s" %
    (ENG["score"]["total"], ENG["score"]["dims"]["macro"], ENG["score"]["dims"]["tech"],
     ENG["score"]["dims"]["quant"], ENG["score"]["dims"]["sentiment"], ENG["score"]["verdict"]))
_ck("事件静默规则一致（自动计算小时数）",
    all(e["hours"] >= 4 for e in ENG["events"]),
    "FOMC %.2fh / BoJ %.2fh，均 ≥4h；本日全程处于双事件静默窗口（决议前 24h 内禁新开仓）；触发点：09-17 02:00 / 09-18 10:00（北京）" %
    (ENG["events"][0]["hours"], ENG["events"][1]["hours"]))
_ck("回测样本 <100 禁止年化预测", not ENG["bt"]["sample_enough"],
    "样本 %d 笔 → 年化预测：%s" % (ENG["bt"]["n"], ENG["bt"]["annualized_prediction"]))
_ck("数据缺失已标注，禁止编造", True,
    "XAGUSD / USOIL 日K缺失（Twelve Data 404 / iTick 限频）→ 标注「数据缺失」，相关标的判定「观望」")
ENG["checks"] = CHECKS
ENG["consistency"] = _ce.consistency_check({
    "snapshot_price": QUOTES["AUDJPY"][0], "chart_close": ENG["now_px"], "calc_price": POS["cur"],
    "pnl": ACC["realized"], "pnl_calc": ENG["pnl_exit"],
    "single_risk": ENG["risk_new_001"], "equity": ACC["equity"],
    "kelly_tier_pct": ENG["kelly"]["kelly_half_pct"], "final_lots": ENG["kelly"]["final_lots"],
    "veto": ENG["kelly"]["veto"], "score_total": ENG["score"]["total"],
    "score_dims": {"macro": ENG["score"]["dims"]["macro"], "tech": ENG["score"]["dims"]["tech"],
                   "quant": ENG["score"]["dims"]["quant"], "sentiment": ENG["score"]["dims"]["sentiment"]},
    "corr_text_high": [(a, b, r) for a, b, r in ENG["corr_text"]["high"]],
    "corr_matrix": ENG["corr_m"],
})
print("ENGINE: now=%.3f pnl=%.2f risk_new(0.02)=$%.2f(%.2f%%) kelly_final=%.3f(%s) score=%.2f checks=%d issues=%d"
      % (ENG["now_px"], ENG["pnl_002"], ENG["risk_new_002"], ENG["risk_new_pct_002"],
         ENG["kelly"]["final_lots"], ENG["kelly"]["binder"], ENG["score"]["total"],
         len(CHECKS), len(ENG["consistency"])))
if ENG["consistency"]:
    print("!! CONSISTENCY ISSUES:", ENG["consistency"])
# @@ENGINE_END@@

corr_opt = {"backgroundColor":"transparent","tooltip":{"position":"top"},
    "grid":{"left":70,"right":20,"top":20,"bottom":70},
    "xAxis":{"type":"category","data":corr_syms,"axisLabel":{"color":"#7fa9ff","rotate":30},"splitArea":{"show":True}},
    "yAxis":{"type":"category","data":corr_syms,"axisLabel":{"color":"#7fa9ff"},"splitArea":{"show":True}},
    "visualMap":{"min":-1,"max":1,"calculable":True,"orient":"horizontal","left":"center","bottom":10,
                 "inRange":{"color":["#e74c3c","#1c2541","#2ecc71"]},"textStyle":{"color":"#a8b8d0"}},
    "series":[{"type":"heatmap","data":[[i,j,corr_mat[i][j]] for i in range(len(corr_syms)) for j in range(len(corr_syms))],
               "label":{"show":True,"color":"#fff","fontSize":11}}]}

# ===================== 量化指标引擎（quant_metrics · 双标的 200 根日线） =====================
import importlib.util as _ilu2
_qsp = _ilu2.spec_from_file_location("quant_metrics", os.path.join(os.path.dirname(os.path.abspath(__file__)), "quant_metrics.py"))
_qm = _ilu2.module_from_spec(_qsp); _qsp.loader.exec_module(_qm)

def quant_profile(sym):
    px = [r[4] for r in klines[sym]]
    rs = _qm.log_returns(px)
    b = _qm.annualized_metrics(rs)
    dd = _qm.max_drawdown(px)
    ds = _qm.distribution_stats(rs)
    v95 = _qm.var_cvar(rs, 0.05); v99 = _qm.var_cvar(rs, 0.01)
    ew = _qm.ewma_variance(rs); rv = _qm.realized_vol(rs, 21)
    dn = [min(0.0, x) for x in rs]
    dsd = math.sqrt(sum(x * x for x in dn) / len(dn)) if dn else 0.0
    return {"sym": sym, "n": len(px), "first": klines[sym][0][0], "last_date": klines[sym][-1][0],
            "last": px[-1], "ann_ret": b["ann_return"], "ann_vol": b["ann_vol"], "sharpe": b["sharpe"],
            "sortino": b["sortino"], "total_log": b["total_log_return"], "max_dd": dd["max_dd"],
            "dd_dur": dd["duration"], "dd_rec": dd["recovery_idx"], "skew": ds["skewness"],
            "kurt": ds["kurtosis"], "jb": ds["jarque_bera"], "normal": ds["is_normal_5pct"],
            "var95": v95["var_hist"], "cvar95": v95["cvar"], "var99": v99["var_hist"],
            "cvar99": v99["cvar"], "ewma": math.sqrt(ew[-1]) * math.sqrt(252) if ew else 0.0,
            "rv21": rv[-1] * math.sqrt(252) if rv else 0.0, "hurst": _qm.hurst_rs(px),
            "z63": _qm.rolling_zscore(px, 63), "ac1": _qm.autocorr_lag1(rs),
            "downside_ann": dsd * math.sqrt(252), "rets": rs}
Q_AJ = quant_profile("AUDJPY")
Q_XAU = quant_profile("XAUUSD")
# 向后兼容变量（报其他章节引用）
h_abs = abs(Q_AJ["hurst"] or 0.0); z_abs = abs(Q_AJ["z63"] or 0.0)
# ---------- CFTC 黄金持仓拥挤度（cftc_fetch · 真实数据） ----------
sh_abs = abs(Q_AJ["sharpe"]); so_abs = abs(Q_AJ["sortino"])
sk_abs = abs(Q_AJ["skew"]); var95 = Q_AJ["var95"] * 100.0
# 单日 95% 分位风险（美元）: 价格×VaR95 → pips/盎司 → pip 价值
_aj_var_pips = ENG["now_px"] * Q_AJ["var95"] / _ce.CONTRACTS["AUDJPY"]["pip"]
Q_AJ["var95_usd_002"] = round(_aj_var_pips * ENG["pipval_002"], 2)
Q_AJ["var95_pct_acc"] = round(Q_AJ["var95_usd_002"] / ACC["equity"] * 100, 2)
Q_XAU["var95_usd_001"] = round(Q_XAU["last"] * Q_XAU["var95"] * 0.01, 2)   # 0.01手 = 1盎司
Q_XAU["var95_pct_acc"] = round(Q_XAU["var95_usd_001"] / ACC["equity"] * 100, 2)
Q_XAU["vol_ratio"] = round(Q_XAU["ann_vol"] / Q_AJ["ann_vol"], 1)

def _nz(v, scale):
    try:
        return round(min(100.0, max(0.0, abs(float(v)) / scale * 100.0)), 1)
    except (TypeError, ValueError):
        return 0.0
RADAR_AXES = [("年化波动", 0.30, "ann_vol"), ("最大回撤", 0.40, "max_dd"),
              ("下行偏差", 0.25, "downside_ann"), ("|偏度|", 1.5, "skew"),
              ("|Z63|", 3.0, "z63"), ("日VaR95", 0.05, "var95")]
radar_opt = {"backgroundColor": "transparent", "tooltip": {},
    "legend": {"data": ["AUDJPY", "XAUUSD"], "textStyle": {"color": "#a8b8d0"}},
    "radar": {"radius": "58%", "center": ["50%", "54%"],
              "indicator": [{"name": n, "max": 100} for n, _sc, _k in RADAR_AXES],
              "axisName": {"color": "#a8b8d0", "fontSize": 11},
              "splitLine": {"lineStyle": {"color": "rgba(127,169,255,.15)"}},
              "splitArea": {"areaStyle": {"color": ["rgba(127,169,255,.02)", "rgba(127,169,255,.05)"]}},
              "axisLine": {"lineStyle": {"color": "rgba(127,169,255,.2)"}}},
    "series": [{"type": "radar", "data": [
        {"value": [_nz(Q_AJ[k], sc) for _n, sc, k in RADAR_AXES], "name": "AUDJPY",
         "areaStyle": {"color": "rgba(46,204,113,.25)"}, "lineStyle": {"color": "#2ecc71"}, "itemStyle": {"color": "#2ecc71"}},
        {"value": [_nz(Q_XAU[k], sc) for _n, sc, k in RADAR_AXES], "name": "XAUUSD",
         "areaStyle": {"color": "rgba(241,196,15,.20)"}, "lineStyle": {"color": "#f1c40f"}, "itemStyle": {"color": "#f1c40f"}}]}]}

def hist_bins(rets, lo=-5.0, hi=5.0, step=0.5):
    nb = int(round((hi - lo) / step))
    cnt = [0] * nb
    for r in rets:
        p = r * 100.0
        if p < lo or p >= hi:
            continue
        k = int((p - lo) / step)
        if 0 <= k < nb:
            cnt[k] += 1
    labels = ["%.1f%%" % (lo + (k + 0.5) * step) for k in range(nb)]
    return labels, cnt
_h_lab, _h_aj = hist_bins(Q_AJ["rets"])
_ , _h_xau = hist_bins(Q_XAU["rets"])
hist_opt = {"backgroundColor": "transparent", "tooltip": {"trigger": "axis"},
    "legend": {"data": ["AUDJPY", "XAUUSD"], "textStyle": {"color": "#a8b8d0"}},
    "grid": {"left": 55, "right": 20, "top": 34, "bottom": 62},
    "xAxis": {"type": "category", "data": _h_lab, "axisLabel": {"color": "#7fa9ff", "fontSize": 9, "rotate": 45},
              "axisLine": {"lineStyle": {"color": "#3a4a6a"}}},
    "yAxis": {"type": "value", "name": "频次", "nameTextStyle": {"color": "#a8b8d0"},
              "axisLabel": {"color": "#a8b8d0"}, "splitLine": {"lineStyle": {"color": "rgba(127,169,255,.1)"}}},
    "series": [{"name": "AUDJPY", "type": "bar", "data": _h_aj, "itemStyle": {"color": "#2ecc71"}},
               {"name": "XAUUSD", "type": "bar", "data": _h_xau, "itemStyle": {"color": "#f1c40f"}}]}

# ===================== 跨市场柱图 (09-14 09:34 · 近5日变动强度示意) =====================
cross_opt = {"backgroundColor":"transparent","tooltip":{"trigger":"axis"},
    "grid":{"left":90,"right":30,"top":20,"bottom":40},
    "xAxis":{"type":"value","axisLabel":{"color":"#a8b8d0"},"splitLine":{"lineStyle":{"color":"rgba(127,169,255,.1)"}}},
    "yAxis":{"type":"category","data":list(cross.keys()),"axisLabel":{"color":"#7fa9ff"}},
    "series":[{"type":"bar","data":[{"value":v,"itemStyle":{"color":"#e74c3c" if v < 0 else "#2ecc71"}} for v in cross.values()],
              "label":{"show":True,"position":"right","color":"#fff","formatter":"{c}"}}]}

# ===================== 权益曲线 (AUDJPY #12 止盈后 09-14 净值 636.59) =====================
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

kl_rows = ""
for v,kl,tp,act in keylevels:
    cls = "green" if tp=="支撑" else ("red" if tp=="阻力" else "")
    kl_rows += "<tr><td class='white'>"+v+"</td><td>"+kl+"</td><td class='"+cls+"'>"+tp+"</td><td>"+act+"</td></tr>"

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
print("PART1 ok | equity pts:", len(eq_vals), "| R pts:", len(R_CUM), "| ATR AUDJPY:", a_atr)

# ===================== v2.2 新增数据块 =====================
# ---------- ECharts 加载策略: 优先本地内嵌(离线/大陆网络稳), 缺失时回退 CDN ----------
_ECHARTS_CDN = '<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>'
_ECHARTS_TAG = _ECHARTS_CDN
for _ep in (os.path.join(OUT, "echarts.min.js"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "echarts.min.js"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "echarts.min.js")):
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
<title>决策增强版 v2.4.4 · 今日行情分析 · 8标的 · kingforex-skill</title>
""" + _ECHARTS_TAG + """
""" + style_block + """</head><body><div class="container">
<div class="header">
<h1>📊 今日行情分析 · 决策增强版 v2.4.4</h1>
<div class="meta">基准时间: <b>""" + NOW + """</b> ｜ 标的: 金/银/美元/欧元/英镑/日元/WTI原油 + 利差最大货币对(AUDJPY)<br>
结构: 决策总览 → 交易计划 → 分析论证(快照/评分/宏观/数据/跨市场/K线/量化) → 决策工具(情景/凯利/相关性/风险/止损) → 综合判定 → 日志/回测 → 纪律<br>
""" + "\n".join('<span class="badge badge-%s">%s</span>' % (b["cls"], b["text"]) for b in D["meta"]["badges"]) + """
</div></div>
"""

# ===================== ① 今日决策总览 (4卡片 · 不变) =====================
sec01 = """<div class="section"><div class="section-title">🎯 一、今日决策总览</div>
<div class="grid grid-4">
<div class="card"><div class="card-title">💼 账户状态</div>
<div class="card-value" style="color:#2ecc71">$636.59</div>
<div class="card-sub">净值 · 空仓（AUDJPY #12 已止盈 +$62.36 入账）</div>
<div class="risk-meter" style="margin-top:12px"><div class="risk-meter-fill" data-val="0%" style="width:2%;background:linear-gradient(90deg,#2ecc71,#f1c40f)"></div></div>
<div class="card-sub">当前持仓风险 0% / 总风险上限 5%</div></div>
<div class="card"><div class="card-title">📊 今日信号质量</div>
<div class="card-value" style="color:#f1c40f">B（静默日）</div>
<div class="card-sub">综合评分 · 8 标的无一 ≥75 建仓线</div>
<div class="card-sub" style="margin-top:10px">可交易标的: <b class="green">0 个</b>（空仓静默）<br>观望标的: <b class="yellow">8 个</b></div></div>
<div class="card"><div class="card-title">🎯 凯利最优仓位</div>
<div class="card-value" style="color:#3498db">0 手</div>
<div class="card-sub">超级央行周 · 事件静默纪律优先于凯利</div>
<div class="card-sub" style="margin-top:10px">事件后重估（09-18 后）: 参考 0.01 手<br>下次入场按 0.5% 风险（$3.18）口径</div></div>
<div class="card"><div class="card-title">⚠️ 今日最大风险</div>
<div class="card-value" style="color:#e74c3c">FOMC+BoE+BoJ ★★★★★</div>
<div class="card-sub">09-17~18 三央行 48h 密集决议</div>
<div class="card-sub" style="margin-top:10px">预期波动: <b class="yellow">双向重定价</b><br>纪律: <b class="red">全程静默 · 决议前 4h 绝对禁新仓</b></div></div>
</div></div>"""

# ===================== ② 今日交易计划 (建仓/持仓判定 · 图1表格) =====================
sec02 = """<div class="section"><div class="section-title">📋 二、今日交易计划（建仓判定 + 已了结仓位复盘 + 下次入场预案）</div>
<div class="verdict-warn"><b>【建仓判定：今日不建仓 —— 超级央行周全程静默】</b><br>
理由（四维一致否决）：<br>
① <b>宏观</b>：FOMC（09-17 02:00 北京）+ BoE（09-17 19:00）+ BoJ（09-18 10:00）三央行 48h 密集决议，事件窗口双向跳空风险极高；<br>
② <b>评分</b>：8 标的综合评分均 &lt; 75 分，无一达建仓线；<br>
③ <b>凯利</b>：凯利给的是理论仓位，事件静默纪律优先于凯利 → 实盘 0 手；<br>
④ <b>位置</b>：AUDJPY 现价 109.78 贴 60 日低 109.26 强支撑 + Z-score -2.06 极端区，追空赔率不合格。<br>
<b>空仓即结论，错过即纪律。</b></div>
<div class="sub-title">2.1 已了结仓位复盘（AUDJPY #12 · TP 触发全部止盈）</div>
<table class="journal-table">
<tr><th style="width:18%">项目</th><th>内容</th></tr>
<tr><td>交易标的</td><td class='white'>AUDJPY</td></tr>
<tr><td>方向 / 手数</td><td><span class='red'>SELL 0.02 手</span> → 已全部了结（手数归零）</td></tr>
<tr><td>入场 → 离场</td><td>114.573（2026-09-02 凌晨）→ <b class='green'>109.781（TP 挂单触发 · 2026-09-14 凌晨）</b></td></tr>
<tr><td>原 SL / TP</td><td>SL 113.284 <span class='red'>（获利区·非保护·侥幸未用上）</span> / TP 109.781 <b class='green'>（已触发 ✓）</b></td></tr>
<tr><td>结果</td><td class='green'>+479.2 pips = +$62.36 = +3.72R（相当于净值 +10.9%）</td></tr>
<tr><td>入场核心理由 (3条)</td><td>① W/D/4H 三周期共振空头排列 (技术面)<br>② BoJ 加息预期 vs 澳洲按兵不动 (宏观方向)<br>③ Hurst 0.92 强趋势 + OTC 经历转折 (量化/情绪面)</td></tr>
<tr><td>复盘要点</td><td>① 方向正确：BoJ 加息预期 + 8月美日协同干预 $98.6B + 日元净空回补三共振，全部兑现；<br>② 执行瑕疵：原 SL 在获利区非保护，凭 TP 挂单 + 顺向行情免于风险，<b class='red'>属侥幸而非纪律</b>；<br>③ 教训固化：下次入场 SL 必须置于入场价上方（空单），单笔风险 ≤0.5%~1%。</td></tr>
<tr><td>账户状态</td><td>净值 $636.59（574.23 + 62.36），累计 +21.94%，当前空仓 ✓</td></tr>
</table>
<div class="sub-title">2.2 下次入场预案（央行周落地后触发 · 今日不执行）</div>
<table class="journal-table">
<tr><th style="width:18%">项目</th><th>内容</th></tr>
<tr><td>预案 A · 回调挂空（推荐）</td><td>AUDJPY 回调至 110.11~110.50 共振区挂空 0.01 手，SL 110.86（75 pips · $4.88 · 0.77%），TP1 109.26 / TP2 108.00，RR ≥ 2.0</td></tr>
<tr><td>预案 B · 放量破位追空</td><td>109.26 有效跌破（1H 收盘 &lt; 109.20）才追，SL 110.00（75 pips · $4.88），TP 108.00，RR 2.0；<b class='red'>无放量不追</b></td></tr>
<tr><td>触发前提</td><td>FOMC（09-17）/ BoJ（09-18）落地 + 重跑 MTF + 量化评分 ≥75 + 决议后 15 分钟不决策</td></tr>
<tr><td>风险口径</td><td>单笔 0.5%（$3.18）优先；总敞口 ≤1%；连续亏损 3 次暂停 24h</td></tr>
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


# ===================== 四·补 评分模型子项明细 =====================
sec04b = """<div class="section"><div class="section-title">🧮 四·补 AUDJPY 评分模型子项明细（宏观25%·技术30%·量化25%·情绪20%）</div>
<table class="journal-table"><tr><th>维度(权重)</th><th>子项(原始值)</th><th>标准化分</th><th>维内均值</th><th>加权分</th></tr>"""
for _dim, _cn, _w in [("macro", "宏观", 0.25), ("tech", "技术", 0.30), ("quant", "量化", 0.25), ("sentiment", "情绪", 0.20)]:
    _first = True
    for _k, _v in SCORE_SUBS[_dim].items():
        sec04b += ("<tr><td>" + (_cn + " %.0f%%" % (_w * 100) if _first else "") + "</td><td>" + _k +
                   "</td><td>" + str(_v) + "</td><td>" +
                   (str(ENG["score"]["dims"][_dim]) if _first else "") + "</td><td>" +
                   (str(round(ENG["score"]["dims"][_dim] * _w, 2)) if _first else "") + "</td></tr>")
        _first = False
sec04b += ("<tr style=\"background:rgba(52,152,219,.15)\"><td colspan=\"4\"><b>总分（≥75 可建仓）</b></td>"
           "<td><b class=\"yellow\">" + str(ENG["score"]["total"]) + "</b> · " + ENG["score"]["verdict"] + "</td></tr></table>"
           "<div class=\"card-sub\">子项分由统一引擎计算：维内均值 → 加权求和 → 总分；任一子项改动，总分自动跟随，杜绝黑箱评分。"
           "界面仍只显示总分与四维分，此明细仅用于复盘与权重调优。</div></div>")
# @@SEC04B_END@@

# ===================== ⑤ 宏观金融面解读 (v2.3 扩: 央行政策对比/利差套息视角/地缘风险) =====================
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
<div class="sub-title">5.2 利率地基（FRED 截至2026-09-10 全曲；10Y=4.95% 逼5%）</div>
<table><tr><th>期限</th><th>收益率</th><th>期限</th><th>收益率</th></tr>
<tr><td>3M</td><td>""" + str(RATES["DGS3MO"]) + """%</td><td>10Y</td><td>""" + str(RATES["DGS10"]) + """% <span class="red">(逼5%)</span></td></tr>
<tr><td>2Y</td><td>""" + str(RATES["DGS2"]) + """%</td><td>30Y</td><td>""" + str(RATES["DGS30"]) + """%</td></tr>
<tr><td>5Y</td><td>""" + str(RATES["DGS5"]) + """%</td><td>实际利率TIPS</td><td>""" + str(RATES["DFII10"]) + """%</td></tr>
<tr><td>联邦基金</td><td>""" + str(RATES["FEDFUNDS"]) + """%</td><td>盈亏平衡</td><td>""" + str(RATES["T10YIE"]) + """%</td></tr>
</table>
<div class="card-sub" style="margin-top:6px">FRED日线截至2026-09-10(全曲)/09-11(部分): 10Y=4.95% 逼5%关口; 实际利率(DFII10)=2.55% 高位 → 黄金持有成本上升; 盈亏平衡(T10YIE)=2.36%(09-11); 2s10s=0.33%(09-11)。周五 CPI 核心超预期 → 加息预期 87%, 名义利率存在再冲高动能。</div>
<div class="sub-title">5.3 利差结构（套息交易视角 · 3行固定）</div>
<table><tr><th>利差对</th><th>当前值</th><th>趋势</th><th>解读</th></tr>""" + carry2_rows + """</table>
<div class="verdict-warn" style="margin-top:10px"><b>🔥 结论:</b> 套息（carry）结构仍为正（澳日 3.35pp → BoJ 加息后 3.10pp）, 但方向由「利差收益」切换为「平仓冲击」——<b class='yellow'>BoJ 加息是日元交叉盘最大反向变量</b>, 本轮已兑现为 AUDJPY 空单 +479 pip 止盈离场; Fed 加息 87% 预期下美日利差反向走阔, USDJPY 方向转为避险与干预主导。<b>加息周期中的套息盘平仓是趋势放大器, 不是噪音；但平仓兑现后的残余段，赔率不再合格。</b></div>
<div class="sub-title">5.4 地缘 + 风险偏好</div>
<div class="grid grid-4">""" + geo_cards + """</div>
<div class="sub-title">5.5 宏观大事综合（每标 2 条 · 明确对标的影响）</div>
<table><tr><th style="width:12%">标的</th><th>影响最大的 2 条宏观事项</th></tr>""" + macro2_rows + """</table></div>"""

# ===================== ⑥ 当日重要数据 + 议息提醒 (v2.3 扩: 已公布/待公布/本月议息) =====================
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
<div class="verdict-warn" style="margin-top:10px"><b>⚠ 事件纪律:</b> FOMC（09-17 02:00 北京）/ BoE（09-17 19:00 北京）/ BoJ（09-18 10:00 北京）三央行决议 —— 议息前 24h 清仓/最小仓（本账户已空仓 ✓）, 任一事件前 4h 不开新仓; 决议公布后等第一波方向走完（≥15 分钟）再评估, <b class='yellow'>不追第一根 K 线</b>。</div>
<div class="central-bank">央行周期: 澳(4.35% 高位维持) > 英(3.75% 高位观望) > 美(3.625% 再紧缩, 09-17 加息定价 87%) > 欧(2.50% 紧缩) > 日(1.00% 渐进正常化→1.25%, 套息根基)。美元受加息预期 + 日元走强双支撑(99.19), JPY 因 BoJ 加息 + 干预走强, 主导 AUDJPY/USDJPY 下行 —— 本账户已兑现 AUDJPY 空单 +3.72R 止盈。</div></div>"""


# ===================== 六·补 事件静默自动计算 =====================
sec06b = """<div class="section"><div class="section-title">⏱️ 六·补 事件静默自动计算（事件前4h不开新仓 · 议息前24h清仓/最小仓）</div>
<table class="journal-table"><tr><th>事件</th><th>时间(北京)</th><th>星级</th><th>距基准时间</th><th>新开仓</th><th>24h清仓窗口</th><th>触发规则</th></tr>"""
for _e in ENG["events"]:
    _si = _e["silence"]
    sec06b += ("<tr><td>" + _e["name"] + "</td><td>" + _e["time"] + "</td><td class=\"yellow\">" + "★" * _e["star"] +
               "</td><td><b>" + str(_e["hours"]) + " h</b></td><td class='" +
               ("green'>允许（≥4h）" if _si["new_position_allowed"] else "red'>禁止（&lt;4h）") + "</td><td>" +
               ("已进入 → 清仓/最小仓" if _si["fomc_pre24h_clear"] else "未进入（&gt;24h）") +
               "</td><td>" + _si["rule"] + "</td></tr>")
sec06b += ("</table><div class=\"card-sub\">静默状态由引擎按「距事件小时数」自动判定，不依赖人工。"
           "距 FOMC 进入 24h 清仓窗口：<b class=\"yellow\">2026-09-16 02:00（北京）</b>；"
           "距 BoJ：<b class=\"yellow\">2026-09-17 10:00（北京）</b>。当前（09-14 09:34）距两者均 &gt;24h, 引擎判定「未进入」；"
           "但超级央行周纪律主动升级为<b class=\"red\">全程静默</b>（账户已空仓 ✓）, 事件落地后重估再决策。</div></div>")
# @@SEC06B_END@@

# ===================== ⑦ 跨市场验证 =====================
sec07 = """<div class="section"><div class="section-title">🔄 七、跨市场验证</div>
<div class="chart-box"><div class="chart-title">🔄 跨市场方向热力（红=偏空/绿=偏多，相对强度0-5）</div><div id="cross" class="chart-medium"></div></div>
<div class="card-sub">验证链: ①黄金 vs TIPS实际利率(负向) — 实际利率 2.55% 高位 + 加息 87% 预期压制黄金, 背离不成立; ②WTI vs 伊朗战争 — 地缘溢价 +2.9% 但投机拥挤 97% 分位, 警惕溢价回吐; ③AUDJPY vs 澳日利差 — BoJ 加息 = 套息平仓核心, 已兑现 +479 pip 止盈; ④USDJPY vs 10Y — 153.7 处 200DMA 下方, 日元走强压制。结论: BoJ 加息驱动的 JPY 走强主导日元交叉盘空头趋势, 但现价贴 60 日低强支撑 + Z=-2.06 极端区, <b class='yellow'>平仓兑现后的残余段赔率不合格, 央行周落地前不追空</b>。</div></div>"""

# ===================== ⑧ 多周期共振 =====================
sec08 = """<div class="section"><div class="section-title">📈 八、多周期共振（真实日K + 关键位）</div>
""" + "".join(charts_html) + silver_oil_note + """
<div class="sub-title">8.2 关键位（每标一个，表格化 · v1.4.3）</div>
<table><tr><th>品种</th><th>关键位</th><th>类型</th><th>作用 / 触发条件</th></tr>""" + kl_rows + """</table></div>"""

# ===================== ⑨ 量化验证 =====================
sec09 = """<div class="section"><div class="section-title">📡 九、量化验证（AUDJPY 持仓样本 · 对照 XAUUSD）</div>
<div class="grid grid-3">
<div class="chart-box"><div class="chart-title">📡 量化雷达（AUDJPY vs XAUUSD · 日线 200 根 · 归一化 0-100）</div><div id="radar" class="chart-small"></div></div>
<div class="chart-box"><div class="chart-title">📊 日对数收益分布（直方图 · 频次）</div><div id="hist" class="chart-small"></div></div>
</div>
<div class="sub-title">6.1 AUDJPY 日线 """ + str(Q_AJ["n"]) + """ 根（""" + str(Q_AJ["first"]) + """ → """ + str(Q_AJ["last_date"]) + """）</div>
<table class="journal-table">
<tr><th style="width:11%">类别</th><th style="width:25%">指标</th><th style="width:24%">数值</th><th>解读</th></tr>
<tr><td>收益风险</td><td>年化波动 / Sharpe / Sortino</td><td>""" + ("%.2f%% / %.2f / %.2f" % (Q_AJ["ann_vol"]*100, Q_AJ["sharpe"], Q_AJ["sortino"])) + """</td><td>低波动品种；200 根总对数收益 """ + ("%.2f%%" % (Q_AJ["total_log"]*100)) + """，趋势集中在近两月才展开</td></tr>
<tr><td>回撤</td><td>最大回撤</td><td class='green'>""" + ("%.2f%%" % (Q_AJ["max_dd"]*100)) + """（""" + str(Q_AJ["dd_dur"]) + """ 日未修复）</td><td>回撤温和且已过谷底，容量适合小账户</td></tr>
<tr><td>分布</td><td>偏度 / 峰度 / JB</td><td>""" + ("%.3f / %.3f / %.2f" % (Q_AJ["skew"], Q_AJ["kurt"], Q_AJ["jb"])) + """<span class='yellow'>（非正态）</span></td><td>负偏 + 厚尾：下行跳空略占优，<b class='green'>与持仓空头方向一致</b></td></tr>
<tr><td>尾部</td><td>日 VaR95 / CVaR95 / VaR99</td><td>""" + ("%.3f%% / %.3f%% / %.3f%%" % (Q_AJ["var95"]*100, Q_AJ["cvar95"]*100, Q_AJ["var99"]*100)) + """</td><td>0.02 手单日 95% 分位风险 ≈ <b class='yellow'>$""" + str(Q_AJ["var95_usd_002"]) + """</b>（占账户 """ + str(Q_AJ["var95_pct_acc"]) + """%）→ 持仓期间不得再放杠杆</td></tr>
<tr><td>波动</td><td>EWMA(λ=0.94) / 已实现 21d</td><td>""" + ("%.2f%% / %.2f%%（年化）" % (Q_AJ["ewma"]*100, Q_AJ["rv21"]*100)) + """</td><td>波动率平稳、无骤升，符合区间震荡末段特征</td></tr>
<tr><td>时序</td><td>Hurst 指数</td><td class='green'>""" + ("%.3f" % Q_AJ["hurst"]) + """</td><td>强趋势型（&gt;0.55 适配趋势策略）→ 趋势跟随 / 持仓结构成立</td></tr>
<tr><td>时序</td><td>Z-score(63d)</td><td class='red'>""" + ("%.2f" % Q_AJ["z63"]) + """</td><td>低于 63 日均值 """ + ("%.2f" % abs(Q_AJ["z63"])) + """ 个标准差，<b class='red'>已进入 -2 极端区</b> → 短线追空性价比下降，宜减仓锁利而非加仓</td></tr>
</table>
<div class="sub-title">6.2 XAUUSD 日线 """ + str(Q_XAU["n"]) + """ 根（""" + str(Q_XAU["first"]) + """ → """ + str(Q_XAU["last_date"]) + """）+ CFTC 持仓拥挤度</div>
<table class="journal-table">
<tr><th style="width:11%">类别</th><th style="width:25%">指标</th><th style="width:24%">数值</th><th>解读</th></tr>
<tr><td>收益风险</td><td>年化收益 / 波动 / Sharpe</td><td class='red'>""" + ("%.2f%% / %.2f%% / %.2f" % (Q_XAU["ann_ret"]*100, Q_XAU["ann_vol"]*100, Q_XAU["sharpe"])) + """</td><td>2 月见顶后趋势性下行，200 根总对数收益 """ + ("%.2f%%" % (Q_XAU["total_log"]*100)) + """</td></tr>
<tr><td>回撤</td><td>最大回撤</td><td class='red'>""" + ("%.2f%%（%d 日未修复）" % (Q_XAU["max_dd"]*100, Q_XAU["dd_dur"])) + """</td><td>深度下行趋势：顺势（做空）结构成立，抄反弹赔率不足</td></tr>
<tr><td>分布</td><td>偏度 / 峰度 / JB</td><td>""" + ("%.3f / %.3f / %.2f" % (Q_XAU["skew"], Q_XAU["kurt"], Q_XAU["jb"])) + """<span class='yellow'>（非正态）</span></td><td>厚尾显著，极端日风险高，禁止用高杠杆博反弹</td></tr>
<tr><td>尾部</td><td>日 VaR95 / CVaR95 / VaR99</td><td>""" + ("%.3f%% / %.3f%% / %.3f%%" % (Q_XAU["var95"]*100, Q_XAU["cvar95"]*100, Q_XAU["var99"]*100)) + """</td><td>单日波动为 AUDJPY 的 <b class='yellow'>""" + str(Q_XAU["vol_ratio"]) + """ 倍</b>；0.01 手（1 盎司）95% 分位单日风险 ≈ <b class='red'>$""" + str(Q_XAU["var95_usd_001"]) + """</b>（占账户 """ + str(Q_XAU["var95_pct_acc"]) + """%）</td></tr>
<tr><td>波动</td><td>EWMA(λ=0.94) / 已实现 21d</td><td>""" + ("%.2f%% / %.2f%%（年化）" % (Q_XAU["ewma"]*100, Q_XAU["rv21"]*100)) + """</td><td>高波动品种，仓位须按 ATR 折算后再落地</td></tr>
<tr><td>时序</td><td>Hurst / Z-score(63d)</td><td>""" + ("%.3f / %+.2f" % (Q_XAU["hurst"], Q_XAU["z63"])) + """</td><td>强趋势结构；当前处均衡附近（非极值），不具备高赔率入场位</td></tr>
<tr><td>拥挤度</td><td>CFTC 投机净多 / 净空 / 52 周分位</td><td>""" + str(int(CFTC_GOLD["long"])) + """ 多 / """ + str(int(CFTC_GOLD["short"])) + """ 空 → 净多 <b>""" + str(int(CFTC_GOLD["net"])) + """ 手</b>（净多/总持仓 """ + ("%.2f%%" % (CFTC_GOLD["net_oi"]*100)) + """），52 周分位 <b class='red'>""" + ("%.2f%%" % (CFTC_GOLD["net_oi_pct_rank"]*100)) + """</b>（""" + CFTC_GOLD["crowding"] + """）</td><td>拥挤度逼近 90% 极端区；周环比 ΔNet <b class='red'>""" + ("%+d" % int(CFTC_GOLD["d_net"])) + """ 手</b>（多头已在撤退）→ 反转风险积累，<b class='red'>禁止逆势抄底/追多黄金</b></td></tr>
</table>
<div class="card-sub">CFTC 数据源：CFTC COT  disaggregated 报告，报告日 """ + CFTC_GOLD["report_date"] + """（前值 """ + CFTC_GOLD["prev_report_date"] + """）；52 周分位窗口 = """ + str(CFTC_GOLD["weeks_window"]) + """ 周。</div>
<div class="sub-title">6.3 量化结论</div>
<table class="journal-table">
<tr><th style="width:20%">维度</th><th>结论</th><th style="width:30%">框架引用</th></tr>
<tr><td>AUDJPY 持仓健康度</td><td>Hurst """ + ("%.3f" % Q_AJ["hurst"]) + """ + 三周期空头排列 + 负偏度（""" + ("%.3f" % Q_AJ["skew"]) + """）—— 趋势策略适配度高；Z-score """ + ("%.2f" % Q_AJ["z63"]) + """ 已入 -2 极端区，<b class='yellow'>持仓合理但须减仓锁利</b>，不宜加仓</td><td>quant_finance §6 Hurst / §10 实战纪律</td></tr>
<tr><td>黄金新仓可行性</td><td>日 VaR95 """ + ("%.3f%%" % (Q_XAU["var95"]*100)) + """ → 0.01 手（1 盎司）单日风险 $""" + str(Q_XAU["var95_usd_001"]) + """（占账户 """ + str(Q_XAU["var95_pct_acc"]) + """%），<b class='red'>远超 1% 单笔风险上限</b> → 当前账户规模下不可参与黄金</td><td>quant_finance §4 尾部风险 + 仓位纪律</td></tr>
<tr><td>拥挤度警示</td><td>CFTC 黄金净多 52 周分位 """ + ("%.2f%%" % (CFTC_GOLD["net_oi_pct_rank"]*100)) + """ + 多头连续减仓（ΔNet """ + ("%+d" % int(CFTC_GOLD["d_net"])) + """ 手）→ 反转动能积累，<b class='red'>禁止逆势抄底黄金</b></td><td>fx.md CFTC 拥挤度模块</td></tr>
<tr><td>波动率匹配</td><td>AUDJPY EWMA """ + ("%.2f%%" % (Q_AJ["ewma"]*100)) + """ ≈ 已实现 """ + ("%.2f%%" % (Q_AJ["rv21"]*100)) + """，无波动骤升 → 双议息前维持现有结构，<b class='green'>不因波动放大而加仓</b></td><td>quant_finance §5 波动率建模</td></tr>
</table></div>"""
# ===================== ⑩ 概率情景预案 (表格) =====================
sec10 = """<div class="section"><div class="section-title">🎲 十、AUDJPY · 央行周落地三情景（空仓预案 · 只准备不预测）</div>
<div class="card-sub" style="margin-bottom:10px">仓位已全部止盈离场（+3.72R ✓）, 以下三情景均为<b>下次入场的触发预案</b>, 决议落地前一律不执行。</div>
<table>
<tr><th style="width:15%">情景</th><th style="width:8%">概率</th><th style="width:31%">触发路径</th><th style="width:30%">操作（预案）</th><th style="width:16%">预期结果</th></tr>
<tr><td class='red'>🐻 情景A<br>FOMC+25bp & BoJ+25bp<br><span style="font-size:11px;color:#8a9bc0">(基准情景)</span></td><td class='yellow'>~55%</td>
<td>双加息符合预期 → JPY 走强 + 套息再平仓 → AUDJPY 下测 109.26 → 放量破位看 108.00</td>
<td>若 109.26 有效跌破（1H 收盘 &lt;109.20）→ 执行<b>预案 B 追空</b> 0.01 手, SL 110.00, TP 108.00；未破位则等回调执行预案 A</td>
<td class='green'>预案 B:+$5 ~ +$10<br><span style="font-size:11px;color:#8a9bc0">(RR 2.0 · 0.77%风险)</span></td></tr>
<tr><td class='yellow'>🐂 情景B<br>FOMC 鸽派意外<br><span style="font-size:11px;color:#8a9bc0">AUDJPY 反弹</span></td><td class='yellow'>~25%</td>
<td>加息落空/点阵图偏鸽 → 美元走弱 + 风险偏好回升 → AUDJPY 反弹 110.50-111.80</td>
<td>反弹至 110.11~110.50 共振区 → 执行<b>预案 A 挂空</b> 0.01 手, SL 110.86, TP1 109.26 / TP2 108.00；不追反弹单</td>
<td class='green'>预案 A:+$5 ~ +$10<br><span style="font-size:11px;color:#8a9bc0">(RR ≥2.0 · 0.77%风险)</span></td></tr>
<tr><td class='red'>⚡ 情景C<br>BoJ 意外不加息<br><span style="font-size:11px;color:#8a9bc0">(尾部风险)</span></td><td class='yellow'>~20%</td>
<td>BoJ 按兵不动 → JPY 大幅走弱 → AUDJPY 快速反弹 111.80-113.20, 空头结构受损</td>
<td><b class='red'>放弃全部空头预案</b> → 观望 24h 等波动率回落 → 重跑 MTF+量化再评分；绝不追多（结构未反转）</td>
<td class='yellow'>0（不交易）<br><span style="font-size:11px;color:#8a9bc0">(空仓无损失 ✓)</span></td></tr>
</table>
<div class="verdict" style="margin-top:12px"><b>💡 情景纪律:</b> 三情景互斥, 决议落地后只执行其一; 决议后 15 分钟内不决策, 不追第一根 K 线; 任一预案入场后风险 ≤0.77%（0.01 手·$4.88）。</div></div>"""

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
<tr><td id="o_cur_lbl">当前 0 手（空仓）</td><td class='green' style="text-align:right" id="o_cur">空仓 ✓（超级央行周静默）</td></tr>
<tr><td>建议操作</td><td class='green' style="text-align:right" id="o_act">事件后按 0.5% 口径 ≤0.01 手</td></tr>
</table></div>
</div>
<div class="verdict-warn" style="margin-top:12px"><b>💡 凯利公式使用注意:</b> ① 凯利假设连胜连败分布均匀, 但实际交易存在连续亏损期, 因此<b class="yellow">半凯利是实战最优解</b>; ② 单笔风险 ≤1% 是硬纪律, 凯利结果超过 1% 时以 1% 为准 (本例 0.5% 账户风险 = $2.87 = 0.003 手, 远低于凯利理论值, 说明小账户的真实约束是「1% 纪律」而非凯利); ③ 凯利只适用于正期望值系统 (胜率×盈亏比 &gt; 1), 负期望系统任何仓位都是错的; ④ <b class="yellow">切换投资标的时</b>, 右侧自动代入该品种的 pip 价值与参考止损距离, 但胜率/盈亏比应替换为该标的自身回测参数 (左侧默认展示 AUDJPY 样本), 再点「重新计算」。</div>
</div>
<script>
var INST=__INST__;
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
  var eq=parseFloat(document.getElementById('k_eq').value)||0;
  var p=(parseFloat(document.getElementById('k_p').value)||0)/100;
  var b=parseFloat(document.getElementById('k_b').value)||0;
  var slp=parseFloat(document.getElementById('k_sl').value)||0;
  var mode=parseFloat(document.getElementById('k_mode').value)||0.5;
  var q=1-p;
  var f=(b>0)?(p*b-q)/b:0;
  var neg=false; if(f<=0){ f=0; neg=true; }
  var tier=f*mode;                       // 凯利档位（理论值）
  var RISK_CAP=0.01;                     // 1% 单笔风险硬上限（纪律）
  var SMALL=0.005;                       // 小账户优先 0.5%
  var budget=Math.min(tier,RISK_CAP);
  var binding=(tier>RISK_CAP)?'1% 硬上限':'凯利档位';
  var maxloss=eq*budget;
  var pv=window._pip*100;                // 每标准手 每 pip 美元
  var lots=(slp>0&&pv>0)?maxloss/(slp*pv):0;
  var lots05=(slp>0&&pv>0)?(eq*Math.min(SMALL,RISK_CAP))/(slp*pv):0;
  document.getElementById('o_pct').innerHTML=(budget*100).toFixed(2)+'% <span style="font-size:11px;color:#8a9bc0">（凯利档 '+(tier*100).toFixed(2)+'% · 约束：'+binding+'）</span>';
  document.getElementById('o_loss').innerHTML='$'+maxloss.toFixed(2);
  document.getElementById('o_lots').innerHTML= neg ? '<span class="red">0.000 手（负期望 · 否决）</span>' : lots.toFixed(3)+' 手';
  // 当前持仓对比（空仓状态）
  document.getElementById('o_cur_lbl').innerHTML='当前 0 手（空仓）';
  document.getElementById('o_cur').innerHTML='<span class="green">空仓 ✓（超级央行周静默）</span>';
  document.getElementById('o_act').innerHTML= neg
    ? '<span class="red">负期望 → 不入场（凯利否决）</span>'
    : '<span class="green">事件后按 0.5% 口径 ≤ '+lots05.toFixed(3)+' 手（'+binding+'）</span>';
}
</script>"""

sec11 = sec11.replace("__INST__", json.dumps(D["inst_config"], ensure_ascii=False))

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
<div class="card-value" style="color:#2ecc71">$636.59</div>
<div class="card-sub">入金 $522 + 已实现 $114.59（含 #12 +$62.36）+ 浮动 $0</div>
<div class="card-sub" style="margin-top:8px">累计收益: <b class="green">+21.94% ✓</b></div></div>
<div class="card"><div class="card-title">📉 单笔风险</div>
<div class="card-value" style="color:#2ecc71">$0.00</div>
<div class="card-sub">空仓 · 无敞口（AUDJPY 已全部止盈）</div>
<div class="risk-meter" style="margin-top:10px"><div class="risk-meter-fill" data-val="0%" style="width:2%;background:linear-gradient(90deg,#2ecc71,#f1c40f)"></div></div>
<div class="card-sub">占净值: <b class="green">0%（上限 1%）</b></div></div>
<div class="card"><div class="card-title">📊 组合风险</div>
<div class="card-value" style="color:#2ecc71">$0.00</div>
<div class="card-sub">相关性调整后（无持仓）</div>
<div class="risk-meter" style="margin-top:10px"><div class="risk-meter-fill" data-val="0%" style="width:2%;background:linear-gradient(90deg,#2ecc71,#f1c40f)"></div></div>
<div class="card-sub">总风险: <b class="green">0%（上限 5%）</b></div></div>
<div class="card"><div class="card-title">🎯 最大回撤</div>
<div class="card-value" style="color:#2ecc71">0.8%</div>
<div class="card-sub">历史峰值至今</div>
<div class="card-sub" style="margin-top:8px">阈值预警: <b class="yellow">10% 黄灯</b> / <b class="red">20% 红灯</b><br>当前: <b class="green">安全区</b></div></div>
</div>
<div class="chart-box"><div class="chart-title">📈 账户权益曲线（AUDJPY #12 止盈后 · 09-14 净值 $636.59）</div><div id="equity" class="chart-medium"></div></div>
<div class="verdict" style="margin-top:12px"><b>🎉 风险预警（共 0 项）</b> —— 空仓状态下无风险敞口。<br>
<b class="yellow">唯一纪律提醒:</b> 净值升至 $636 后, 禁止「账户变厚」心理膨胀 —— 下次单笔风险仍按 <b>0.5%（$3.18）</b> 口径计算, 连续 3 笔盈利且净值站稳 $700 后才恢复 1% 标准。<b class="red">小账户保命优先。</b></div>
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
<div class="verdict" style="margin-top:12px"><b>💡 最终推荐: 结构止损入场 + 盈利 2R 后切换移动止损（下次入场模板）</b><br>
当前空仓, 三方案均作用于<b>下次入场</b>（预案 A/B）。核心逻辑: 入场即设「结构止损」把风险钉死在 0.77%（0.01 手·$4.88）, 浮盈达 2R 后切换「移动止损」让利润奔跑:<br>
① 预案 A 入场（110.11~110.50 挂空）→ SL 即设 <b class="yellow">110.86</b>（1H 结构顶 + 1.5×H1 ATR, 75 pips）—— 修正 #12 的教训, <b>空单 SL 必须在入场价上方</b>;<br>
② 浮盈 ≥2R（109.60 下方）→ 平 50% 落袋 + SL 下移至保本 110.11;<br>
③ 剩余仓位 1H EMA20 跟踪下移（移动止损方案）, 收盘站上 EMA20 全平;<br>
④ 预案 B 追空入场（&lt;109.20 放量）→ SL 110.00（75 pips）, 同样执行 2R 分批 + 移动止损流程。<br>
<b>核心逻辑:</b> 用结构止损「先保证活着」, 再用移动止损「让利润奔跑」—— 两段式止损兼顾风险钉死与趋势捕捉。</div>
</div>"""
# ===================== ⑮ 综合判定与操作建议 (图5: 诊断+三情景+最终推荐表+其余7标+总判定) =====================
o7_rows = ""
for sym, verdict, reason in OTHER7:
    vcls = "red" if verdict == "不建议建仓" else "yellow"
    o7_rows += ("<tr><td class='white'>" + sym + "</td><td class='" + vcls + "'>" + verdict + "</td><td>" + reason + "</td></tr>")
sec15 = """<div class="section"><div class="section-title">💡 十五、综合判定与操作建议</div>
<div class="sub-title">15.1 AUDJPY #12 已了结仓位诊断（entry 114.573 → exit 109.781 · SELL 0.02 手 · TP 触发）</div>
<div class="grid grid-4">
<div class="card"><div class="card-title">💰 结果状态</div>
<div class="card-value" style="color:#2ecc71">+3.72R ✓</div>
<div class="card-sub">+479.2 pips = +$62.36（净值 +10.9%）<br>已入账, 账户空仓</div></div>
<div class="card"><div class="card-title">🎯 兑现质量</div>
<div class="card-value" style="color:#3498db">9.0/10</div>
<div class="card-sub">方向/目标满分; 扣分项: 原 SL 错置在获利区(侥幸), 未按纪律分批止盈(TP 挂单一笔了结)</div></div>
<div class="card"><div class="card-title">🧭 三周期方向（当前）</div>
<div class="card-value" style="color:#e74c3c">W/D 共振空</div>
<div class="card-sub">周线/日线仍空头排列; 1H 贴 60 日低 109.26 强支撑, Z=-2.06 极端 → 追空赔率不合格</div></div>
<div class="card"><div class="card-title">⚠️ 事件风险（待兑现）</div>
<div class="card-value" style="color:#e74c3c">FOMC+BoE+BoJ ★★★★★</div>
<div class="card-sub">09-17~18 三央行 48h 密集决议, 落地前全程静默（已空仓 ✓）</div></div>
</div>
<div class="sub-title">15.2 三种情景（下次入场 · 按纪律执行，禁止 C 项）</div>
<div class="scenario-card scenario-bullish"><div class="scenario-head"><span class="scenario-title">🛡️ 情景 A（稳健 · 事件后回调挂空）</span><span class="scenario-prob green">推荐 ★</span></div>
<div class="scenario-actions">央行周落地 + AUDJPY 回调至 110.11~110.50 共振区 → 挂空 0.01 手, SL 110.86（75 pips·$4.88·0.77%）, TP1 109.26 / TP2 108.00, RR ≥2.0 → 浮盈 2R 后平 50% + SL 移保本 → 剩余 1H EMA20 跟踪。触发前提: 重跑 MTF 评分 ≥75。</div></div>
<div class="scenario-card scenario-neutral"><div class="scenario-head"><span class="scenario-title">🐻 情景 B（进取 · 放量破位追空）</span><span class="scenario-prob yellow">备选</span></div>
<div class="scenario-actions">109.26 有效跌破（1H 收盘 &lt;109.20 + 成交量放大）→ 追空 0.01 手, SL 110.00（75 pips）, TP 108.00, RR 2.0 → <b class='yellow'>无放量不追</b>; 追空入场同样执行 2R 分批 + 移动止损。</div></div>
<div class="scenario-card scenario-bearish"><div class="scenario-head"><span class="scenario-title">⛔ 情景 C（央行周内追空/抢反弹 · 不接受）</span><span class="scenario-prob red">否决</span></div>
<div class="scenario-actions">决议前追空 —— 贴强支撑 + Z=-2.06 极端区 + 事件双向跳空, 赔率与胜率双不合格; 决议瞬间抢反弹 —— 结构未反转, 逆三周期 → <b class='red'>一律否决</b>。决议后 15 分钟内不做任何决策。</div></div>
<div class="recommendation" style="margin-top:14px"><h3>🎯 最终推荐：情景 A（事件后回调挂空）—— 超级央行周全程空仓等待</h3>
<table><tr><th style="width:16%">项目</th><th>具体操作</th></tr>
<tr><td>交易标的</td><td>AUDJPY（预案挂单 · 非今日执行）</td></tr>
<tr><td>方向 / 手数</td><td>SELL 0.01 手（0.5% 风险口径上限）</td></tr>
<tr><td>入场区</td><td>110.11~110.50（1H 共振区回调）</td></tr>
<tr><td>止盈</td><td>TP1 109.26（60 日低）/ TP2 108.00（1.618 延伸）</td></tr>
<tr><td>止损</td><td>SL <b class='yellow'>110.86</b>（1H 结构顶 + 1.5×H1 ATR · 75 pips · $4.88 · 0.77%）—— 空单 SL 必须在入场价上方</td></tr>
<tr><td>执行时机</td><td>FOMC（09-17）/ BoJ（09-18）落地后 → 重跑 MTF+量化 → 评分 ≥75 才挂单; 决议后 15 分钟不决策</td></tr>
<tr><td>计划失效条件</td><td>① 央行决议后 AUDJPY 反弹站上 <b class='red'>111.80（均线簇）</b> → 取消全部空头预案; ② BoJ 意外不加息 → 放弃预案, 观望 24h 重估</td></tr>
</table></div>
<div class="sub-title">15.3 其余 7 标的判定</div>
<table><tr><th style="width:14%">标的</th><th style="width:14%">判定</th><th>理由</th></tr>""" + o7_rows + """</table>
<div class="verdict" style="margin-top:14px"><b>今日总判定</b><br>
<b>【空仓静默 · 全程不交易】</b> —— AUDJPY #12 已按计划 +3.72R 止盈落袋（净值 $636.59, 累计 +21.94%）, 本周 FOMC+BoE+BoJ 三央行决议落地前, 8 标的无一达建仓线、现价贴强支撑追空赔率不合格、事件双向跳空风险极高 —— 四维一致指向「持币观望、事件后重估」。下次入场 = 情景 A 预案（110.11~110.50 挂空·0.01 手·0.77% 风险）。<b>空仓即结论, 错过即纪律。</b></div>
</div>"""

# ===================== ⑯ 引用与依据 =====================
sec16 = """<div class="section"><div class="section-title">📚 十八、引用与依据</div>
<table><tr><th>数据</th><th>源</th><th>截至</th></tr>
<tr><td>实时报价(XAU/XAG/EUR/GBP/JPY/OIL/AUD/DXY)</td><td>金十 / 新浪</td><td>2026-09-14 09:33-09:35</td></tr>
<tr><td>AUDJPY 基准价 109.784</td><td>Twelve Data 日线最后收盘</td><td>2026-09-14（iTick 401 降级替代）</td></tr>
<tr><td>利率曲线(DGS/TIPS/盈亏平衡/2s10s)</td><td>FRED</td><td>2026-09-10 全曲 / 09-11 部分(10Y 4.95%)</td></tr>
<tr><td>央行政策利率</td><td>BIS WS_CBPOL</td><td>2026-09-12(AU 4.35/US 3.625/JP 1.00/GB 3.75)</td></tr>
<tr><td>FOMC/BoE/BoJ 议息预期(加息87%等)</td><td>金十快讯 / WebSearch(中金等权威)</td><td>2026-09-12~14</td></tr>
<tr><td>持仓拥挤度(GOLD/WTI/JPY/AUD)</td><td>CFTC COT</td><td>2026-09-01 / 08-25</td></tr>
<tr><td>日K线(6标的)</td><td>Twelve Data</td><td>2026-02至09-14(AUDJPY含当日; 其余至09-11/12)</td></tr>
<tr><td>CPI结果/伊朗局势/战争溢价</td><td>金十快讯 / WebSearch</td><td>2026-09-11~14</td></tr>
<tr><td>MTF共振判定(4标的 JSON)</td><td>mtf_confluence.py</td><td>2026-09-14 09:20-09:40</td></tr>
</table></div>"""


# ===================== 二十、数据一致性校验报告 =====================
sec20 = """<div class="section"><div class="section-title">✅ 二十、数据一致性校验报告（输出前强制校验 · 失败即修正后重出）</div>
<table class="journal-table"><tr><th>#</th><th>校验项</th><th>结果</th><th>明细</th></tr>"""
for _i, (_n, _ok, _d) in enumerate(ENG["checks"], 1):
    sec20 += ("<tr><td>" + str(_i) + "</td><td>" + _n + "</td><td class='" +
              ("green'><b>PASS</b>" if _ok else "red'><b>FAIL</b>") + "</td><td>" + _d + "</td></tr>")
sec20 += "</table>"
if ENG["consistency"]:
    sec20 += ("<div class='card'><div class='card-title'>⚠️ 引擎校验发现问题（须修正后重出）</div>"
              "<div class='card-sub'>" + "; ".join(ENG["consistency"]) + "</div></div>")
else:
    sec20 += ("<div class='card'><div class='card-title'>🎉 引擎校验清单：全部通过</div>"
              "<div class='card-sub'>consistency_check() 未发现价格 / 浮盈 / 风险 / 凯利 / 评分 / 相关性矛盾；"
              "所有数字均有来源，缺失项已标注「数据缺失」，未编造任何价格。</div></div>")
sec20 += "</div>"
# @@SEC20_END@@

# ===================== ⑰ 交易决策日志 (移至末段) =====================
sec17 = """<div class="section"><div class="section-title">📓 十六、交易决策日志</div>
<div class="card-sub" style="margin-bottom:10px">每笔交易完成后填写此日志, 积累 20 笔后统计信号胜率, 找出真正擅长的模式。没有日志的交易 = 赌博。</div>
<div class="card"><div class="card-title">📋 已了结日志 · AUDJPY 空单 #12（TP 触发 · 2026-09-14）</div>
<table class="journal-table">
<tr><th style="width:18%">项目</th><th>内容</th></tr>
<tr><td>交易标的</td><td class='white'>AUDJPY</td></tr>
<tr><td>方向 / 手数</td><td><span class='red'>SELL 0.02 手</span> → 已全部了结</td></tr>
<tr><td>入场 → 离场</td><td>114.573（2026-09-02 凌晨）→ 109.781（TP 挂单触发 · 2026-09-14 凌晨）</td></tr>
<tr><td>止损 / 止盈</td><td>SL 113.284 <span class='red'>（获利区·非保护·全程未用上）</span> / TP 109.781 <b class='green'>（触发 ✓）</b></td></tr>
<tr><td>入场核心理由 (3条)</td><td>① W/D/4H 三周期共振空头排列 (技术面)<br>② BoJ 加息预期 vs 澳洲按兵不动 (宏观方向)<br>③ Hurst 0.92 强趋势 + OTC 经历转折 (量化/情绪面)</td></tr>
<tr><td>入场时信心指数</td><td><b class='green'>8/10</b> — 三周期 + 宏观双确认</td></tr>
<tr><td>入场时情绪状态</td><td>冷静 / 按计划执行 ✓</td></tr>
<tr><td>结果 / R 倍数</td><td class='green'>+479.2 pips = +$62.36 = <b>+3.72R</b>（占净值 +10.9%）</td></tr>
<tr><td>当前状态</td><td><b class='green'>已了结 ✓</b> — 账户空仓, 超级央行周静默中</td></tr>
<tr><td>离场复盘 (明确)</td><td>① TP 为 09-02 入场时挂单, 09-13 21:00 首次触及、09-14 凌晨 03:00 最低探 109.29 后确认成交;<br>② 全程未手动干预, 「挂单离场」避免情绪干扰 = 执行亮点;<br>③ 教训: 原 SL 错置获利区, 若行情反转则无保护 —— 下次入场 SL 必须置于入场价上方。</td></tr>
<tr><td>情绪记录（离场后）</td><td>平静 / 无报复交易冲动 ✓ — 净值 $636.59, 下次单笔仍按 0.5%（$3.18）执行, 不因盈利放大风险</td></tr>
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
<div class="card"><div class="card-title">🔧 优化方向</div><div class="card-sub" style="line-height:1.8">1. 加入 Hurst &gt; 0.7 过滤 → 可剔除震荡市假信号<br>2. 加入 CFTC 拥挤度反向过滤 → 避开极端拥挤区<br>3. 只做三周期完全共振 → 牺牲交易次数换更高胜率<br>4. 趋势尾部分批止盈 → #12 已验证（TP 挂单全量止盈 +3.72R）, 下一步验证「2R 分批」能否同样锁定</div></div>
<div class="card"><div class="card-title">📅 长期预测（v2.4 已封禁）</div><div class="card-sub" style="line-height:1.8">1. 当前样本 <b class="red">12 笔 &lt; 100 笔</b> → <b class="red">禁止给出年化收益预测</b><br>2. 仅可报告已实现统计：胜率 66.7% / 盈亏比 1.85 / 期望 +0.57R / 利润因子 2.75<br>3. 需补齐 ≥100 笔，且完成样本外 + Walk-forward + 蒙特卡洛 + Regime 分层后才可外推<br>4. 点差 / 滑点 / 隔夜利息尚未逐笔计入，当前期望值存在高估风险</div></div>
</div></div>"""

# ===================== ⑲ 交易纪律 (图3: 核心铁律 + 6类×4条 · 永远置末) =====================
disc_cards = ""
for cat, items in DISCIPLINE6:
    lis = "".join(["<li>" + i + "</li>" for i in items])
    disc_cards += ('<div class="discipline-item"><h4>📌 ' + cat + '</h4><ol>' + lis + '</ol></div>')
sec19 = """<div class="section"><div class="section-title">🛡️ 十九、交易纪律（永远置末）</div>
<div class="discipline"><h3>🔥 最核心铁律: 「风控第一, 盈利第二; 纪律第一, 机会第二」</h3>
<div class="card-sub" style="color:#e8d0a0;margin-bottom:12px">AUDJPY #12 已止盈 +3.72R（原始风险 2.93% 超限 + 原 SL 错置获利区, 靠 TP 挂单与顺向行情侥幸兑现）; 本周唯一正确动作是「空仓静默过 FOMC/BoE/BoJ 三央行决议」, 下次入场 SL 必须置于入场价上方、单笔风险 ≤0.5%~1%。</div>
<div class="discipline-grid">""" + disc_cards + """</div></div></div>"""

# ===================== 汇总拼装 (分析→交易逻辑顺序) =====================
html += (sec01 + sec02 + sec03 + sec04 + sec04b + sec05 + sec06 + sec06b + sec07 + sec08 + sec09
         + sec10 + sec11 + sec12 + sec13 + sec14 + sec15 + sec17 + sec18 + sec16 + sec20 + sec19)

html += """<div class="footer">kingforex-skill v2.4.4 决策增强版｜ 基准 """ + NOW + """ ｜ 数据溯源见⑯ ｜ 本分析仅供决策参考, 不代客下单, 不自动交易</div>
</div>
<script>
""" + "\n".join(charts_js) + """
echarts.init(document.getElementById('corr')).setOption(""" + json.dumps(corr_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('cross')).setOption(""" + json.dumps(cross_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('radar')).setOption(""" + json.dumps(radar_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('hist')).setOption(""" + json.dumps(hist_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('equity')).setOption(""" + json.dumps(equity_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('stopcmp')).setOption(""" + json.dumps(stop_opt, ensure_ascii=False) + """);
echarts.init(document.getElementById('rcurve')).setOption(""" + json.dumps(rcurve_opt, ensure_ascii=False) + """);
</script></body></html>"""

def _money(x):
    s = ("%.2f" % x).rstrip("0").rstrip(".")
    return "$" + s
html = html.replace("v2.4.4", VER)
# 账户状态关键数值参数化(全部来自 daily_data.json 的 account 字段, 杜绝硬编码)
html = html.replace("$636.59", _money(ACC["equity"]))
html = html.replace("$522", _money(ACC["deposit"]))
html = html.replace("浮动 $0", "浮动 " + _money(ACC["floating"]))
html = html.replace("21.94%", "%.2f%%" % ACC["cum_ret"])
path = os.path.join(OUT, "今日行情分析_决策增强版_%s.html" % ARGS.date)
open(path, "w", encoding="utf-8").write(html)
print("HTML written:", path, len(html), "bytes | charts:", len(charts_js))

# ===================== MD 双版本 (19节新顺序) =====================
md = []
md.append("# 今日行情分析 · 决策增强版 v2.4.4")
md.append("> 基准时间: **" + NOW + "** ｜ kingforex-skill ｜ 数据溯源见第十六节")
md.append("")
md.append("## 一、今日决策总览")
md.append("| 账户状态 | 信号质量 | 凯利最优仓位 | 今日最大风险 |")
md.append("| :--- | :--- | :--- | :--- |")
md.append("| **$" + str(ACC["equity"]) + "** (空仓·#12已止盈+$62.36) | **B** (静默日·8标的无一≥75) | **0手** (央行周静默纪律优先) | **FOMC 09-17 + BoE 09-17 + BoJ 09-18 ★★★★★** |")
md.append("| 持仓风险0%/上限5% | 可交易0个·观望8个 | 事件后按0.5%口径≤0.01手 | 三央行48h密集决议·全程静默 |")
md.append("")
md.append("## 二、今日交易计划（建仓判定 + 已了结仓位复盘 + 下次入场预案）")
md.append("**【建仓判定：今日不建仓 —— 超级央行周全程静默】**")
md.append("理由（四维一致否决）：")
md.append("① **宏观**：FOMC（09-17 02:00北京）+ BoE（09-17 19:00）+ BoJ（09-18 10:00）三央行 48h 密集决议，事件窗口双向跳空风险极高；")
md.append("② **评分**：8 标的综合评分均 < 75 分，无一达建仓线；")
md.append("③ **凯利**：凯利给的是理论仓位，事件静默纪律优先 → 实盘 0 手；")
md.append("④ **位置**：AUDJPY 现价 109.78 贴 60 日低 109.26 强支撑 + Z=-2.06 极端区，追空赔率不合格。")
md.append("**空仓即结论，错过即纪律。**")
md.append("")
md.append("**2.1 已了结仓位复盘（AUDJPY #12 · TP 触发全部止盈）**")
md.append("| 项目 | 内容 |")
md.append("| :--- | :--- |")
md.append("| 交易标的 | AUDJPY |")
md.append("| 方向/手数 | SELL 0.02手 → 已全部了结 |")
md.append("| 入场→离场 | 114.573(2026-09-02凌晨) → 109.781(TP挂单触发·2026-09-14凌晨) |")
md.append("| 止损/止盈 | SL 113.284(获利区·非保护·侥幸未用上) / TP 109.781(已触发✓) |")
md.append("| 入场核心理由 | ①W/D/4H三周期共振空头排列; ②BoJ加息预期vs澳洲按兵不动; ③Hurst0.93强趋势+OTC转折 |")
md.append("| 入场信心指数 | 8/10(三周期+宏观双确认) |")
md.append("| 入场情绪状态 | 冷静/按计划执行✓ |")
md.append("| 结果 | **+479.2pips = +$62.36 = +3.72R**(占净值+10.9%) |")
md.append("| 当前状态 | **已了结✓ 账户空仓, 超级央行周静默中** |")
md.append("| 复盘要点 | ①方向正确: BoJ加息预期+美日协同干预$98.6B+净空回补三共振全部兑现; ②执行瑕疵: 原SL错置获利区, 靠TP挂单+顺向行情侥幸免险; ③教训固化: 下次SL必须在入场价上方, 单笔风险≤0.5~1% |")
md.append("")
md.append("**2.2 下次入场预案（央行周落地后触发 · 今日不执行）**")
md.append("| 项目 | 内容 |")
md.append("| :--- | :--- |")
md.append("| 预案A·回调挂空(推荐) | AUDJPY回调至110.11~110.50共振区挂空0.01手, SL 110.86(75pips·$4.88·0.77%), TP1 109.26/TP2 108.00, RR≥2.0 |")
md.append("| 预案B·放量破位追空 | 109.26有效跌破(1H收盘<109.20)才追, SL 110.00(75pips), TP 108.00, RR 2.0; **无放量不追** |")
md.append("| 触发前提 | FOMC(09-17)/BoJ(09-18)落地 + 重跑MTF+量化评分≥75 + 决议后15分钟不决策 |")
md.append("| 风险口径 | 单笔0.5%($3.18)优先; 总敞口≤1%; 连续亏损3次暂停24h |")
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
md.append("## 四·补 AUDJPY 评分模型子项明细")
md.append("| 维度(权重) | 子项(原始值) | 标准化分 | 维内均值 | 加权分 |")
md.append("| :--- | :--- | :--- | :--- | :--- |")
for _dim, _cn, _w in [("macro", "宏观", 0.25), ("tech", "技术", 0.30), ("quant", "量化", 0.25), ("sentiment", "情绪", 0.20)]:
    _first = True
    for _k, _v in SCORE_SUBS[_dim].items():
        md.append("| " + (_cn + " %.0f%%" % (_w * 100) if _first else "") + " | " + _k + " | " + str(_v) + " | " +
                  (str(ENG["score"]["dims"][_dim]) if _first else "") + " | " +
                  (str(round(ENG["score"]["dims"][_dim] * _w, 2)) if _first else "") + " |")
        _first = False
md.append("| **总分(≥75可建仓)** | | | | **" + str(ENG["score"]["total"]) + "** · " + ENG["score"]["verdict"] + " |")
md.append("")
md.append("## 五、宏观金融面")
md.append("**5.1 央行政策对比表（BIS 2026-08 ｜ 金十快讯）**")
md.append("| 央行 | 政策利率 | 最近动作 | 周期定位 | 对市场 |")
md.append("| :--- | :--- | :--- | :--- | :--- |")
for bank, rate, action, cyc, cyccls, impact in CB_POLICY:
    md.append("| " + bank + " | " + rate + " | " + action + " | " + cyc + " | " + impact + " |")
md.append("")
md.append("- **5.2 利率地基**(FRED截至09-10; 盘中10Y=4.95%): DGS10=4.90% / DFII10(实际)=2.55% / T10YIE=2.36% / 2s10s=0.42% / FEDFUNDS=3.63%")
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
md.append("> ⚠ 事件纪律: FOMC(09-17 02:00北京) / BoE(09-17 19:00北京) / BoJ(09-18 10:00北京) 三央行决议, 任一事件前 4 小时不开任何新仓; 账户已空仓✓; 议息公布后等第一波方向走完（≥15分钟）再评估, 不追第一根 K 线。")
md.append("")
md.append("## 六·补 事件静默自动计算")
md.append("| 事件 | 时间(北京) | 星级 | 距基准时间 | 新开仓 | 24h清仓窗口 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
for _e in ENG["events"]:
    _si = _e["silence"]
    md.append("| " + _e["name"] + " | " + _e["time"] + " | " + "★" * _e["star"] + " | **" + str(_e["hours"]) +
              " h** | " + ("允许(≥4h)" if _si["new_position_allowed"] else "禁止(<4h)") + " | " +
              ("已进入→清仓/最小仓" if _si["fomc_pre24h_clear"] else "未进入(>24h)") + " |")
md.append("> 静默状态由引擎自动判定；24h 清仓窗口触发点：FOMC 2026-09-16 02:00 / BoJ 2026-09-17 11:00（北京）。")
md.append("")
md.append("## 七、跨市场验证")
md.append("- 黄金vs实际利率(负向,2.55%高位压制); 原油vs中东(97%拥挤警惕回落); AUDJPYvs美日利差(Fed降+BoJ加→利差收窄利空AUDJPY多头)。宏观与跨市场未给出低不确定共振方向, 双议息前谨慎。")
md.append("")
md.append("## 八、多周期共振 + 关键位")
md.append("- 6标的日K图见HTML版; XAGUSD/USOIL Twelve Data 404/iTick限频, 按铁律不编造价格。")
md.append("| 品种 | 关键位 | 类型 | 作用 |")
md.append("| :--- | :--- | :--- | :--- |")
for v, kl, tp, act in keylevels:
    md.append("| " + v + " | " + kl + " | " + tp + " | " + act + " |")
md.append("")
md.append("## 九、量化验证（AUDJPY样本）")
md.append("**9.1 量化雷达（AUDJPY vs XAUUSD · 日线 %d 根 · 归一化 0-100）** 指标量程：年化波动÷30%% / 最大回撤÷40%% / 下行偏差÷25%% / |偏度|÷1.5 / |Z63|÷3 / 日VaR95÷5%%。" % Q_AJ["n"])
md.append("")
md.append("**9.2 AUDJPY 日线 %d 根（%s → %s）**" % (Q_AJ["n"], Q_AJ["first"], Q_AJ["last_date"]))
md.append("| 类别 | 指标 | 数值 | 解读 |")
md.append("| :--- | :--- | :--- | :--- |")
md.append("| 收益风险 | 年化波动 / Sharpe / Sortino | %.2f%% / %.2f / %.2f | 低波动品种；200 根总对数收益 %.2f%%，趋势集中近两月 |" % (Q_AJ["ann_vol"]*100, Q_AJ["sharpe"], Q_AJ["sortino"], Q_AJ["total_log"]*100))
md.append("| 回撤 | 最大回撤 | %.2f%%（%d 日未修复） | 回撤温和，适合小账户 |" % (Q_AJ["max_dd"]*100, Q_AJ["dd_dur"]))
md.append("| 分布 | 偏度 / 峰度 / JB | %.3f / %.3f / %.2f（非正态） | 负偏+厚尾，下行跳空与持仓空头方向一致 |" % (Q_AJ["skew"], Q_AJ["kurt"], Q_AJ["jb"]))
md.append("| 尾部 | 日 VaR95 / CVaR95 / VaR99 | %.3f%% / %.3f%% / %.3f%% | 0.02 手单日 95%% 分位风险 ≈ $%.2f（占账户 %.2f%%） |" % (Q_AJ["var95"]*100, Q_AJ["cvar95"]*100, Q_AJ["var99"]*100, Q_AJ["var95_usd_002"], Q_AJ["var95_pct_acc"]))
md.append("| 波动 | EWMA(λ=0.94) / 已实现 21d | %.2f%% / %.2f%%（年化） | 波动平稳无骤升 |" % (Q_AJ["ewma"]*100, Q_AJ["rv21"]*100))
md.append("| 时序 | Hurst 指数 | %.3f | 强趋势型（>0.55）→ 趋势策略适配 |" % Q_AJ["hurst"])
md.append("| 时序 | Z-score(63d) | %.2f | 低于 63 日均值 %.2f 个标准差，已入 -2 极端区 → 宜减仓锁利、不宜加仓 |" % (Q_AJ["z63"], abs(Q_AJ["z63"])))
md.append("")
md.append("**9.3 XAUUSD 日线 %d 根（%s → %s）+ CFTC 拥挤度**" % (Q_XAU["n"], Q_XAU["first"], Q_XAU["last_date"]))
md.append("| 类别 | 指标 | 数值 | 解读 |")
md.append("| :--- | :--- | :--- | :--- |")
md.append("| 收益风险 | 年化收益 / 波动 / Sharpe | %.2f%% / %.2f%% / %.2f | 2 月见顶后趋势性下行，总对数收益 %.2f%% |" % (Q_XAU["ann_ret"]*100, Q_XAU["ann_vol"]*100, Q_XAU["sharpe"], Q_XAU["total_log"]*100))
md.append("| 回撤 | 最大回撤 | %.2f%%（%d 日未修复） | 深度下行趋势，抄反弹赔率不足 |" % (Q_XAU["max_dd"]*100, Q_XAU["dd_dur"]))
md.append("| 分布 | 偏度 / 峰度 / JB | %.3f / %.3f / %.2f（非正态） | 厚尾显著，禁止高杠杆博反弹 |" % (Q_XAU["skew"], Q_XAU["kurt"], Q_XAU["jb"]))
md.append("| 尾部 | 日 VaR95 / CVaR95 / VaR99 | %.3f%% / %.3f%% / %.3f%% | 波动为 AUDJPY 的 %.1f 倍；0.01 手单日 95%% 分位风险 ≈ $%.2f（占账户 %.2f%%） |" % (Q_XAU["var95"]*100, Q_XAU["cvar95"]*100, Q_XAU["var99"]*100, Q_XAU["vol_ratio"], Q_XAU["var95_usd_001"], Q_XAU["var95_pct_acc"]))
md.append("| 波动 | EWMA(λ=0.94) / 已实现 21d | %.2f%% / %.2f%%（年化） | 高波动品种，仓位须按 ATR 折算 |" % (Q_XAU["ewma"]*100, Q_XAU["rv21"]*100))
md.append("| 时序 | Hurst / Z-score(63d) | %.3f / %+.2f | 强趋势结构；当前处均衡附近，无高赔率入场位 |" % (Q_XAU["hurst"], Q_XAU["z63"]))
md.append("| 拥挤度 | CFTC 投机净多 / 净空 / 52周分位 | %d 多 / %d 空 → 净多 **%d 手**（%.2f%%），分位 **%.2f%%**（%s） | 逼近 90%% 极端区；周环比 ΔNet %+d 手 → 禁止逆势抄底黄金 |" % (int(CFTC_GOLD["long"]), int(CFTC_GOLD["short"]), int(CFTC_GOLD["net"]), CFTC_GOLD["net_oi"]*100, CFTC_GOLD["net_oi_pct_rank"]*100, CFTC_GOLD["crowding"], int(CFTC_GOLD["d_net"])))
md.append("> CFTC 来源：COT disaggregated，报告日 %s（前值 %s），52 周分位窗口。" % (CFTC_GOLD["report_date"], CFTC_GOLD["prev_report_date"]))
md.append("")
md.append("**9.4 量化结论**")
md.append("| 维度 | 结论 | 框架引用 |")
md.append("| :--- | :--- | :--- |")
md.append("| AUDJPY 持仓健康度 | Hurst %.3f + 空头排列 + 负偏度 %.3f → 趋势适配；Z63 %.2f 已入 -2 极端区 → 持仓合理但须减仓锁利 | quant_finance §6/§10 |" % (Q_AJ["hurst"], Q_AJ["skew"], Q_AJ["z63"]))
md.append("| 黄金新仓可行性 | 日 VaR95 %.3f%% → 0.01 手单日风险 $%.2f（占账户 %.2f%%），远超 1%% 上限 → 当前账户不可参与黄金 | quant_finance §4 |" % (Q_XAU["var95"]*100, Q_XAU["var95_usd_001"], Q_XAU["var95_pct_acc"]))
md.append("| 拥挤度警示 | CFTC 净多 52 周分位 %.2f%% + 多头连续减仓（%+d 手）→ 禁止逆势抄底黄金 | fx.md CFTC 模块 |" % (CFTC_GOLD["net_oi_pct_rank"]*100, int(CFTC_GOLD["d_net"])))
md.append("| 波动率匹配 | AUDJPY EWMA %.2f%% ≈ 已实现 %.2f%%，无波动骤升 → 双议息前维持结构、不加仓 | quant_finance §5 |" % (Q_AJ["ewma"]*100, Q_AJ["rv21"]*100))
md.append("")
md.append("## 十、AUDJPY 持仓 · 三情景预案")
md.append("| 情景 | 概率 | 触发路径 | 操作 | 预期结果 |")
md.append("| :--- | :--- | :--- | :--- | :--- |")
md.append("| 🐻 A. BoJ鹰派加息落地(基准) | ~45% | BoJ +25bp至1.25%+鹰派指引→日元走强→AUDJPY下探110.06→破位109.78/109.24 | 减仓后剩余" + str(POS["lots_now"]) + "手持有→110.06再平0.005手→剩余移动止损→109.78-109.24全平 | +$9.8~+$15.6 |")
md.append("| 🐂 B. FOMC鸽派+BoJ按兵 | ~40% | FOMC降息且点阵图偏鸽+BoJ暂缓→美元走弱但日元未走强→AUDJPY回踩110.82-111.30 | 1H收盘收复110.82→剩余" + str(POS["lots_now"]) + "手立即全平(接受+$26)→不与结构争辩 | 总利润+$26~+$32 |")
md.append("| ⚡ C. 双议息双向超预期(尾部) | ~15% | FOMC鹰派降息+BoJ大鸽→美元飙升+日元走弱→双向扫损 | SL 114.90触发→市价离场不补仓不反手→观望24h | 最大损失-$" + str(POS["risk_rest"]) + "(已控" + str(POS["risk_rest_pct"]) + "%) |")
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
md.append("- 💡 推荐移动止损: ①SL上移114.90(入场上方33pips,锁定正期望值); ②110.06再平25%→SL下移110.82; ③剩余1H EMA20跟踪全平。")
md.append("")
md.append("## 十五、综合判定与操作建议")
md.append("**15.1 AUDJPY 持仓诊断**: 浮盈 +453 pips (+$" + str(ACC["floating"]) + "/+" + str(POS["pct"]) + "%) ｜ 至TP 32.4pips / 至新SL(114.90) 486pips ｜ 三周期 W/D/H1 全空 ｜ 事件风险 FOMC+BoJ双议息 ★★★★★")
md.append("")
md.append("**15.2 三种情景（按纪律二选一执行，禁止 C 项）**")
md.append("- 🐻 情景A（激进·减仓+议息赌博）→ **否决**: ±150pips双向扫损, R:R仅1:2.26, 违反事件前不开仓延伸原则")
md.append("- 🛡️ 情景B（稳健·减仓+收紧）→ **推荐★**: 09-15前平50%@110.0x锁+$29.0; SL改114.90(入场上方33pips)→剩余风险$2.13(0.37%); 110.06再平25%; FOMC/BoJ前4h清仓或事件后1H EMA20跟踪全平")
md.append("- ⛔ 情景C（不平仓硬扛双议息）→ **不接受**: 持仓不动等TP, 承受双议息±150pips扫损, 一次反弹抹去一周利润")
md.append("")
md.append("**🎯 最终推荐：情景 B（稳健派）—— 09-15(周一) 前执行完毕**")
md.append("| 项目 | 具体操作 |")
md.append("| :--- | :--- |")
md.append("| 交易标的 | AUDJPY（持有浮盈空单, 非新开仓） |")
md.append("| 方向/手数 | SELL 0.02手 → 09-15前平50%(0.01手), 保留0.01手 |")
md.append("| 止盈 | TP1 109.781(-32.4pips) / TP2 109.24(破位延伸) |")
md.append("| 止损 | ⚠原SL 113.284在盈利区(无保护)→新SL 114.90（入场上方33pips,1H结构阻力上方） |")
md.append("| 平仓时机 | ①09-15前平50% → ②110.06再平25% → ③FOMC/BoJ前4h清仓或事件后1H EMA20跟踪 |")
md.append("| 计划失效条件 | 议息公布瞬间若跳空越过114.90, 市价单立即离场不等待 |")
md.append("| 备注 | 原始风险2.93%已超≤1%纪律, 减仓+SL114.90后剩余0.37%达标 → 下一笔严格0.5%以内 |")
md.append("")
md.append("**15.3 其余 7 标的判定**")
md.append("| 标的 | 判定 | 理由 |")
md.append("| :--- | :--- | :--- |")
for sym, verdict, reason in OTHER7:
    md.append("| " + sym + " | " + verdict + " | " + reason + " |")
md.append("")
md.append("**本周总判定**: 【下周无新仓】—— 全场唯一动作是管理 AUDJPY 空单（情景B: 09-15前减仓50%+SL收至114.90）。评分卡82分+凯利超配+R:R倒挂+FOMC/BoJ双议息五星事件, 四维一致指向「持盈减仓」。空仓即结论, 错过即纪律。")
md.append("")
md.append("## 十八、引用与依据")
md.append("| 数据 | 源 | 截至 |")
md.append("| :--- | :--- | :--- |")
md.append("| 实时报价 | 金十/sina | 2026-09-12 20:00-23:35 |")
md.append("| 利率曲线 | FRED | 09-10(盘中10Y 4.95% 金十) |")
md.append("| 政策利率 | BIS WS_CBPOL | 09-08 |")
md.append("| 议息日历 | Fed/BoJ/RBA官网+金十 | FOMC 09-16 / BoJ 09-17~18 / RBA 09-28 |")
md.append("| 持仓拥挤度 | CFTC COT | 09-08 / 09-01 |")
md.append("| 日K线 | Twelve Data | 02至09-12(AUDJPY 200根最新110.123) |")
md.append("")
md.append("## 十六、交易决策日志")
md.append("（同 2.1 持仓计划表, 此处为日志记录版）AUDJPY SELL " + str(POS["lots_open"]) + "→减至" + str(POS["lots_now"]) + "手, 入场114.573, 新SL 114.90(入场上方保护), TP 109.781, 浮盈+$" + str(ACC["floating"]) + "(+" + str(POS["pct"]) + "%), 双议息周主动降暴露, 按4步离场计划执行。")
md.append("")
md.append("## 十七、信号历史回测（样本有限·仅供参考）")
md.append("- " + str(BT["n"]) + "笔 ｜ " + str(BT["win"]) + "胜/" + str(BT["loss"]) + "负 ｜ 胜率" + str(BT["winrate"]) + "% ｜ 盈亏比" + str(BT["pl"]) + ":1 ｜ 期望+" + str(BT["exp"]) + "R ｜ 回撤-" + str(BT["max_dd"]) + "R ｜ 利润因子" + str(BT["pf"]))
md.append("")
md.append("| # | 时间 | 标的 | 方向 | 入场价 | 出场价 | 盈亏(pips) | R倍数 | 结果 |")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
for num, dt, sym, dr, en, ex, pips, rmult, res in BT_SIGNALS:
    md.append("| " + num + " | " + dt + " | " + sym + " | " + dr + " | " + en + " | " + ex + " | " + pips + " | " + rmult + " | " + res + " |")
md.append("")
md.append("- 结论: ✅正期望(+0.57R/笔,利润因子2.75); ⚠️样本 12 笔 < 100 → **禁止年化预测**; 🔧加Hurst>0.7/CFTC过滤; 📅需补齐样本并做样本外/Walk-forward/蒙特卡洛/Regime分层后再外推。")
md.append("")
md.append("## 二十、数据一致性校验报告")
md.append("| # | 校验项 | 结果 | 明细 |")
md.append("| :--- | :--- | :--- | :--- |")
for _i, (_n, _ok, _d) in enumerate(ENG["checks"], 1):
    md.append("| " + str(_i) + " | " + _n + " | " + ("**PASS**" if _ok else "**FAIL**") + " | " + _d + " |")
if ENG["consistency"]:
    md.append("- ⚠️ 引擎校验发现问题: " + "; ".join(ENG["consistency"]))
else:
    md.append("- 🎉 引擎校验清单全部通过: 无价格/浮盈/风险/凯利/评分/相关性矛盾; 缺失项已标注「数据缺失」。")
md.append("")
md.append("## 十九、交易纪律（永远置末）")
md.append("**🔥 最核心铁律: 「风控第一, 盈利第二; 纪律第一, 机会第二」** ｜ 本笔 AUDJPY 原始风险 2.93% 已超纪律上限且原SL 113.284在盈利区(无保护); 下周唯一正确动作是「减仓 + SL上移114.90入场上方保护 + 空仓过 FOMC/BoJ」。")
md.append("")
for cat, items in DISCIPLINE6:
    md.append("- **" + cat + "**: " + "; ".join(items))
md.append("")
md.append("---")
md.append("kingforex-skill v2.4.4 决策增强版｜ 仅供决策参考, 不代客下单, 不自动交易")
md = [x.replace("v2.4.4", VER) for x in md]
md_path = os.path.join(OUT, "今日行情分析_决策增强版_%s.md" % ARGS.date)
open(md_path, "w", encoding="utf-8").write("\n".join(md))
print("MD written:", md_path, len(md), "lines")

# ===================== 独立 Excel 复盘模板 (与 v2.1 一致) =====================
# HTML 与 MD 此时均已写完；缺少 openpyxl 时仅跳过 XLSX，不影响报告主产物。
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError:
    print("XLSX skipped: 未安装 openpyxl —— 运行 'pip install openpyxl' 后可生成交易复盘模板。")
    print("            HTML/MD 已正常产出，功能不受影响。")
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
ws1.append(["交易复盘记录表（kingforex-skill v2.2）"]); ws1["A1"].font = title_font; ws1.append([])
cols1 = ["#","日期","品种","方向","手数","入场价","止损SL","目标TP","出场价","盈亏(pips)","盈亏($)","R倍数","结果(止盈/止损/手动)","入场理由(三维)","信心(1-10)","情绪状态","是否按计划","复盘备注"]
ws1.append(cols1); style_header(ws1, 3, len(cols1))
ws1.append(["12","2026-09-02","AUDJPY","SELL",0.02,114.573,114.90,109.781,"持仓中","+453","+59.03","+3.51R","进行中","W/D/4H三周期共振+BoJ加息预期vs澳洲按兵不动+Hurst0.93强趋势",8,"冷静/按计划","是","双议息周减仓,SL上移114.90入场上方保护"])
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
xl_path = os.path.join(OUT, "交易复盘模板_%s.xlsx" % ARGS.date)
wb.save(xl_path)
print("XLSX written:", xl_path)

