# -*- coding: utf-8 -*-
"""从原始生成器 gen_report_20260914.py 提取全部每日硬编码数据 → daily_data_20260914.json
原理: 直接 import 原模块(其模块级全局即全部硬编码数据), 原样 dump 出来, 零转录误差。
原模块 import 时会跑完整生成流程(写文件/打印), 属预期副作用; openpyxl 缺失时以 SystemExit 收尾, 已捕获。
"""
import os, sys, json, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "gen_report_20260914.py")
OUT = os.path.join(HERE, "daily_data_20260914.json")

spec = importlib.util.spec_from_file_location("genrep_src", SRC)
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
except SystemExit:
    pass  # openpyxl 缺失等收尾退出, 数据已就绪

D = {
    "meta": {
        "now": m.NOW,
        "now_dt": "2026-09-14T09:34:00",
        "version": "v2.4.4",
        "badges": [
            {"text": "🔴 超级央行周: FOMC 09-17 + BoE 09-17 + BoJ 09-18", "cls": "red"},
            {"text": "Fed 加息25bp概率87% (CPI核心超预期)", "cls": "red"},
            {"text": "10Y收益率 4.95% 逼5%关口", "cls": "red"},
            {"text": "伊朗战争溢价: WTI 99.17 (+2.9%)", "cls": "yellow"},
            {"text": "本账户 AUDJPY 空单已止盈 +$62.36 (+3.72R) · 空仓", "cls": "purple"},
        ],
    },
    "account": m.ACC,
    "position": m.POS,
    "kelly": m.KELLY,
    "backtest": m.BT,
    "bt_signals": [list(x) for x in m.BT_SIGNALS],
    "r_curve": m.R_CUM,
    "stops": m.STOPS,
    "corr_high": m.CORR_HIGH,   # 引擎覆盖后的终值(作 fallback)
    "corr_low": m.CORR_LOW,
    "quotes": m.QUOTES,
    "rates": m.RATES,
    "carry": m.CARRY,
    "scores": m.SCORES,
    "cftc_gold": m.CFTC_GOLD,
    "cross": m.cross,
    "equity_dates": m.eq_dates,
    "equity_vals": m.eq_vals,
    "keylevels": m.keylevels,
    "snap_extra": m.SNAP_EXTRA,
    "snap_nokl": m.SNAP_NOKL,
    "day_theme": m.DAY_THEME,
    "macro_events": m.macro_events,
    "other7": m.OTHER7,
    "recommend5": m.RECOMMEND5,
    "discipline6": m.DISCIPLINE6,
    "cb_policy": m.CB_POLICY,
    "carry2": m.CARRY2,
    "geo_risk": m.GEO_RISK,
    "macro2": m.MACRO2,
    "cal_pub": m.CAL_PUB,
    "cal_pending": m.CAL_PENDING,
    "cal_month": m.CAL_MONTH,
    "score_subs": m.SCORE_SUBS,
    "klines": m.KD,
    "events": [
        {"name": "FOMC 决议（09-17 02:00 北京·09-16 14:00ET）", "time_iso": "2026-09-17T02:00:00", "star": 5},
        {"name": "BoJ 决议（09-18 10:00 北京·预期加息至1.25%）", "time_iso": "2026-09-18T10:00:00", "star": 5},
    ],
    "inst_config": {
        "AUDJPY": {"pip": 0.0652, "sl": 116, "px": "110.12", "note": "0.01手=1000单位, pip=0.01"},
        "USDJPY": {"pip": 0.0651, "sl": 120, "px": "153.478", "note": "0.01手=1000单位, pip=0.01"},
        "EURUSD": {"pip": 1.000, "sl": 80, "px": "1.15934", "note": "0.01手=1000单位, pip=0.0001"},
        "GBPUSD": {"pip": 1.000, "sl": 90, "px": "1.35262", "note": "0.01手=1000单位, pip=0.0001"},
        "XAUUSD": {"pip": 1.000, "sl": 40, "px": "4348.0", "note": "0.01手=1盎司, 按$1波动计"},
        "XAGUSD": {"pip": 0.500, "sl": 200, "px": "64.465", "note": "0.01手=50盎司, pip=0.01"},
        "USOIL": {"pip": 0.100, "sl": 150, "px": "96.618", "note": "0.01手=10桶, pip=0.01"},
    },
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(D, f, ensure_ascii=False, indent=2)

print("WROTE", OUT, os.path.getsize(OUT), "bytes")
print("keys:", list(D.keys()))
print("account.equity=", D["account"]["equity"], "| quotes.AUDJPY=", D["quotes"]["AUDJPY"])
print("score XAUUSD verdict=", D["scores"]["XAUUSD"]["verdict"])
