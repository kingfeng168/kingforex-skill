# -*- coding: utf-8 -*-
"""把硬编码快照版 gen_report_20260914.py 重构为参数化版 gen_report_param.py。
策略: 保留全部 1562 行装配逻辑不变, 仅 (1) 顶部注入 argparse+JSON 加载桥;
(2) 删去所有每日硬编码数据块(由桥从 daily_data.json 注入); (3) 事件/INST/输出文件名/版本/徽章参数化。
原文件保持不变(归档)。
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "gen_report_20260914.py")
DST = os.path.join(HERE, "gen_report_param.py")

with open(SRC, encoding="utf-8") as f:
    s = f.read()

# ---------- (1) 顶部参数化入口 + 数据桥 ----------
HEADER_OLD = (
    'import os, csv, json, math\n'
    '\n'
    'OUT = "./output"\n'
    'NOW = "2026-09-14 09:34 GMT+8"\n'
    'SKILL_CSS = "~/.workbuddy/skills/kingforex-skill/assets/decision_enhanced_sample.html"\n'
)
HEADER_NEW = '''import os, csv, json, math, argparse

# ============ 参数化入口 ============
def _parse_args():
    ap = argparse.ArgumentParser(description="今日行情分析 决策增强版 · 参数化生成器 (kingforex-skill)")
    ap.add_argument("--date", default="2026-09-14", help="报告日期 YYYY-MM-DD, 用于输出文件名")
    ap.add_argument("--data", default=None, help="daily_data.json 路径 (默认 ./daily_data_<date>.json)")
    ap.add_argument("--out", default="./output", help="输出目录")
    ap.add_argument("--kline-dir", default=None, help="K线CSV目录 (默认同 --out)")
    ap.add_argument("--css", default=None, help="模板CSS路径 (默认技能 assets/decision_enhanced_sample.html)")
    return ap.parse_args()

ARGS = _parse_args()
OUT = ARGS.out
KL_DIR = ARGS.kline_dir or OUT
DATA_PATH = ARGS.data or os.path.join(OUT, "daily_data_%s.json" % ARGS.date)
SKILL_CSS = ARGS.css or "~/.workbuddy/skills/kingforex-skill/assets/decision_enhanced_sample.html"
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

'''
assert HEADER_OLD in s, "HEADER_OLD not found"
s = s.replace(HEADER_OLD, HEADER_NEW, 1)

# ---------- (2) 删除每日硬编码数据块 (由桥注入) ----------
def delete_span(src, start, end):
    i = src.index(start)
    j = src.index(end, i)
    return src[:i] + src[j:]

spans = [
    ("# ---------- 账户状态", "# ===================== 工具函数 ====================="),
    ("# 快照扩展数据", "def snap_metrics(s):"),
    ("DAY_THEME = (", 'print("PART1 ok'),
    ("# 其余 7 标的判定", "# ---------- ECharts 加载策略"),
    ("CB_POLICY = [", 'cb_rows = ""'),
    ("CAL_PUB = [", 'calpub_rows = ""'),
    ('cross = {"DXY"', "cross_opt = {"),
    ("eq_dates = [", "equity_opt = {"),
    ("# 关键位表", 'kl_rows = ""'),
    ("CFTC_GOLD = {", "sh_abs = abs"),
    ("SCORE_SUBS = {", 'ENG["score"] = _ce.score_4d'),
    ('KD = {"XAUUSD"', "klines = {"),
]
for start, end in spans:
    assert start in s, "start missing: %r" % start
    assert end in s, "end missing: %r" % end
    s = delete_span(s, start, end)

# ---------- (3) klines 加载目录: OUT -> KL_DIR ----------
s = s.replace("os.path.join(OUT, p)", "os.path.join(KL_DIR, p)")

# ---------- (4) 事件循环改迭代 daily_data.json ----------
EVENTS_OLD = (
    '_nowdt = _dt.datetime(2026, 9, 14, 9, 34)\n'
    'ENG["events"] = []\n'
    'for _n, _t, _st in [("FOMC 决议（09-17 02:00 北京·09-16 14:00ET）", _dt.datetime(2026, 9, 17, 2, 0), 5),\n'
    '                    ("BoJ 决议（09-18 10:00 北京·预期加息至1.25%）", _dt.datetime(2026, 9, 18, 10, 0), 5)]:\n'
    '    _h = round((_t - _nowdt).total_seconds() / 3600.0, 2)\n'
    '    ENG["events"].append({"name": _n, "time": _t.strftime("%m-%d %H:%M"), "star": _st,\n'
    '                          "hours": _h, "silence": _ce.event_silence(_h, _st)})\n'
)
EVENTS_NEW = (
    '_nowdt = _dt.datetime.fromisoformat(D["meta"]["now_dt"])\n'
    'ENG["events"] = []\n'
    'for _ev in D["events"]:\n'
    '    _n = _ev["name"]; _t = _dt.datetime.fromisoformat(_ev["time_iso"]); _st = _ev["star"]\n'
    '    _h = round((_t - _nowdt).total_seconds() / 3600.0, 2)\n'
    '    ENG["events"].append({"name": _n, "time": _t.strftime("%m-%d %H:%M"), "star": _st,\n'
    '                          "hours": _h, "silence": _ce.event_silence(_h, _st)})\n'
)
assert EVENTS_OLD in s, "EVENTS_OLD not found"
s = s.replace(EVENTS_OLD, EVENTS_NEW, 1)

# ---------- (5) 凯利计算器 INST 配置 -> 由 JSON 注入 ----------
s = re.sub(r"var INST=\{.*?\n\};", "var INST=__INST__;", s, flags=re.DOTALL)
assert "var INST=__INST__;" in s, "INST placeholder failed"
s = s.replace(
    '\n# ===================== ⑫',
    '\nsec11 = sec11.replace("__INST__", json.dumps(D["inst_config"], ensure_ascii=False))\n'
    '\n# ===================== ⑫',
    1,
)

# ---------- (6) 头部徽章 -> 由 JSON 渲染 ----------
BADGES_OLD = (
    '<span class="badge badge-red">🔴 超级央行周: FOMC 09-17 + BoE 09-17 + BoJ 09-18</span>\n'
    '<span class="badge badge-red">Fed 加息25bp概率87% (CPI核心超预期)</span>\n'
    '<span class="badge badge-red">10Y收益率 4.95% 逼5%关口</span>\n'
    '<span class="badge badge-yellow">伊朗战争溢价: WTI 99.17 (+2.9%)</span>\n'
    '<span class="badge badge-purple">本账户 AUDJPY 空单已止盈 +$62.36 (+3.72R) · 空仓</span>\n'
)
BADGES_NEW = (
    '""" + "\\n".join(\'<span class="badge badge-%s">%s</span>\' % (b["cls"], b["text"]) '
    'for b in D["meta"]["badges"]) + """\n'
)
assert BADGES_OLD in s, "BADGES_OLD not found"
s = s.replace(BADGES_OLD, BADGES_NEW, 1)

# ---------- (7) 输出文件名按 --date ----------
s = s.replace('"今日行情分析_决策增强版_2026-09-14.html"', '"今日行情分析_决策增强版_%s.html" % ARGS.date')
s = s.replace('"今日行情分析_决策增强版_2026-09-14.md"', '"今日行情分析_决策增强版_%s.md" % ARGS.date')
s = s.replace('"交易复盘模板_2026-09-14.xlsx"', '"交易复盘模板_%s.xlsx" % ARGS.date')

# ---------- (8) 版本号按 meta.version 运行时替换 ----------
s = s.replace(
    'path = os.path.join(OUT, "今日行情分析_决策增强版_%s.html" % ARGS.date)',
    'html = html.replace("v2.4.4", VER)\npath = os.path.join(OUT, "今日行情分析_决策增强版_%s.html" % ARGS.date)',
    1,
)
s = s.replace(
    'md_path = os.path.join(OUT, "今日行情分析_决策增强版_%s.md" % ARGS.date)',
    'md = [x.replace("v2.4.4", VER) for x in md]\nmd_path = os.path.join(OUT, "今日行情分析_决策增强版_%s.md" % ARGS.date)',
    1,
)

with open(DST, "w", encoding="utf-8") as f:
    f.write(s)
print("WROTE", DST, os.path.getsize(DST), "bytes")
print("remaining literal '2026-09-14' count:", s.count("2026-09-14"))
print("remaining '超级央行周' literal count:", s.count("🔴 超级央行周"))
