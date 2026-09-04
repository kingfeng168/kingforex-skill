#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cftc_fetch.py — CFTC COT / TFF 持仓拥挤度抓取（免费 · 无需密钥 · 中国可直连）

数据源（官方，免费，无需 API Key）：
  1) 分类持仓报告（Disaggregated，期货仅）— 覆盖商品（黄金/白银/铜/WTI/天然气等）
     文件：https://www.cftc.gov/files/dea/history/fut_disagg_txt_YYYY.zip  →  f_year.txt
     投机代理类别 = Managed Money（管理基金）
  2) 金融期货交易者报告（TFF，期货仅）— 覆盖外汇（EUR/USD、JPY、AUD 等）、利率、股指
     文件：https://www.cftc.gov/files/dea/history/fut_fin_txt_YYYY.zip    →  FinFutYY.txt
     投机代理类别 = Leveraged Funds（杠杆基金）

输出指标（持仓拥挤度核心）：
  - 投机净头寸  Net = SpecLong - SpecShort
  - 净头寸/OI   Net/OI（占未平仓比重，剔除规模因素）
  - 多空比      Long/Short（极端值 = 拥挤）
  - 投机多/空占 OI 百分比
  - 历史分位    最新 Net/OI 在可回溯窗口（默认 52 周）内的百分位 → 拥挤度等级
  - 周环比变化  ΔNet、ΔNet/OI

取数铁律：
  - 本脚本只读取 CFTC 官方公开文件，绝不杜撰数据；联网失败/解析失败返回明确错误并退出。
  - 文件较大（年度约 1–5 MB zip / 解压 10–30 MB），默认缓存到本地，仅过期（默认 3 天）才重新下载。

用法：
  python cftc_fetch.py --symbol GOLD
  python cftc_fetch.py --symbol EURUSD --json
  python cftc_fetch.py --market-code 067651          # WTI
  python cftc_fetch.py --symbol WTI --weeks 26        # 缩短分位窗口
  python cftc_fetch.py --from-file /path/f_year.txt --report disagg --market-code 088691   # 离线/预下载
  python cftc_fetch.py --list                         # 列出支持的品种
"""

import argparse
import csv
import io
import os
import sys
import urllib.request
import zipfile
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# 品种映射：别名 -> (报告类型, CFTC 合约代码, 显示名, 投机类别键)
#   report: "disagg" = 分类持仓(商品)；"fin" = TFF 金融(外汇/利率/股指)
#   spec:   "mm" = Managed Money；"lf" = Leveraged Funds
# ---------------------------------------------------------------------------
MARKETS = {
    # --- 商品（分类持仓报告 / Managed Money）---
    "GOLD":   ("disagg", "088691", "黄金 COMEX",            "mm"),
    "XAU":    ("disagg", "088691", "黄金 COMEX",            "mm"),
    "SILVER": ("disagg", "084691", "白银 COMEX",            "mm"),
    "XAG":    ("disagg", "084691", "白银 COMEX",            "mm"),
    "COPPER": ("disagg", "085692", "铜 COMEX(高品位)",       "mm"),
    "HG":     ("disagg", "085692", "铜 COMEX(高品位)",       "mm"),
    "WTI":    ("disagg", "067651", "WTI 原油 NYMEX",         "mm"),
    "CL":     ("disagg", "067651", "WTI 原油 NYMEX",         "mm"),
    "BRENT":  ("disagg", "067651", "WTI 原油 NYMEX(近似)",   "mm"),  # 分类报告无 Brent 单独代码，以 WTI 近似
    "NATGAS": ("disagg", "023651", "天然气 NYMEX",          "mm"),
    "NG":     ("disagg", "023651", "天然气 NYMEX",          "mm"),
    "PLATINUM": ("disagg", "091691", "铂金 NYMEX",          "mm"),
    "PALLADIUM": ("disagg", "093691", "钯金 NYMEX",         "mm"),
    "CORN":   ("disagg", "002602", "玉米 CBOT",             "mm"),
    "WHEAT":  ("disagg", "001602", "小麦 CBOT",             "mm"),
    "SOYBEAN":("disagg", "005602", "大豆 CBOT",             "mm"),
    # --- 外汇 / 利率 / 股指（TFF 金融报告 / Leveraged Funds）---
    "EURUSD": ("fin", "099741", "欧元/美元 CME",           "lf"),
    "JPYUSD": ("fin", "097741", "日元/美元 CME",            "lf"),
    "GBPUSD": ("fin", "096742", "英镑/美元 CME",            "lf"),
    "AUDUSD": ("fin", "232741", "澳元/美元 CME",            "lf"),
    "CADUSD": ("fin", "090741", "加元/美元 CME",            "lf"),
    "CHFUSD": ("fin", "092741", "瑞郎/美元 CME",            "lf"),
    "NZDUSD": ("fin", "112741", "纽元/美元 CME",            "lf"),
    "MXNUSD": ("fin", "095741", "墨西哥比索/美元 CME",      "lf"),
    "US10Y":  ("fin", "213659", "美国 10 年国债 CME",        "lf"),
    "US2Y":   ("fin", "213659", "美国 2 年国债 CME",         "lf"),  # 同为国债期货代码族，近似
    "SP500":  ("fin", "138741", "标普 500 指数 CME",         "lf"),
    "NASDAQ": ("fin", "209742", "纳斯达克 100 指数 CME",     "lf"),
    "DJIA":   ("fin", "099641", "道琼斯指数 CME",            "lf"),
}

BASE_URL = "https://www.cftc.gov/files/dea/history/{file}_YYYY.zip"
DISAGG_FILE = "fut_disagg_txt"
FIN_FILE = "fut_fin_txt"

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cftc_cache")
CACHE_MAX_AGE_DAYS = 3


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def _to_num(s):
    """将 CFTC 字段转为数字；'.' / 空 / 空格 视为 None。"""
    if s is None:
        return None
    s = s.strip()
    if s in ("", ".", "-"):
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _num(v, nd=2):
    return "—" if v is None else f"{v:.{nd}f}"


def _pct(v, nd=2):
    return "—" if v is None else f"{v * 100:.{nd}f}%"


# ---------------------------------------------------------------------------
# 下载 / 读取
# ---------------------------------------------------------------------------
def _download_zip(report, year, force=False):
    """下载年度 zip 到缓存，返回解压后的 txt 路径。"""
    if report == "disagg":
        file_tag = DISAGG_FILE
        inner = "f_year.txt"
    else:
        file_tag = FIN_FILE
        inner = "FinFutYY.txt"

    os.makedirs(CACHE_DIR, exist_ok=True)
    zip_path = os.path.join(CACHE_DIR, f"{file_tag}_{year}.zip")
    txt_path = os.path.join(CACHE_DIR, f"{file_tag}_{year}.txt")

    need_download = force or not os.path.exists(zip_path)
    if not need_download and (datetime.now() - datetime.fromtimestamp(os.path.getmtime(zip_path))).days < CACHE_MAX_AGE_DAYS:
        need_download = False

    if need_download:
        url = BASE_URL.format(file=file_tag).replace("YYYY", str(year))
        print(f"[cftc] 下载 {url} ...", file=sys.stderr)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            with open(zip_path, "wb") as f:
                f.write(data)
        except Exception as e:  # noqa: BLE001
            # 当年文件可能尚未生成（年初）—尝试上一年
            if year > 2006:
                print(f"[cftc] 当年文件下载失败({e})，尝试上一年 {year-1}", file=sys.stderr)
                return _download_zip(report, year - 1, force=force)
            raise RuntimeError(f"下载 CFTC 文件失败: {e}")

    # 解压（若 txt 不存在或 zip 比 txt 新）
    if not os.path.exists(txt_path) or os.path.getmtime(zip_path) > os.path.getmtime(txt_path):
        with zipfile.ZipFile(zip_path) as z:
            # 找到内部 txt
            name = next((n for n in z.namelist() if n.lower().endswith(".txt")), None)
            if not name:
                raise RuntimeError("zip 内未找到 txt 文件")
            with z.open(name) as src, open(txt_path, "wb") as dst:
                dst.write(src.read())
    return txt_path


def _read_local(path):
    if not os.path.exists(path):
        raise RuntimeError(f"本地文件不存在: {path}")
    return path


# ---------------------------------------------------------------------------
# 解析
# ---------------------------------------------------------------------------
def _field_map(report):
    """返回 (投机多头列名, 投机空头列名, 投机价差列名, OI列名, 投机多%列名, 投机空%列名, 投机多交易商, 投机空交易商, 日期列名, 名称列名, 合约代码列名)。"""
    if report == "disagg":
        return (
            "M_Money_Positions_Long_All", "M_Money_Positions_Short_All", "M_Money_Positions_Spread_All",
            "Open_Interest_All",
            "Pct_of_OI_M_Money_Long_All", "Pct_of_OI_M_Money_Short_All",
            "Traders_M_Money_Long_All", "Traders_M_Money_Short_All",
            "Report_Date_as_YYYY-MM-DD", "Market_and_Exchange_Names", "CFTC_Contract_Market_Code",
        )
    else:
        return (
            "Lev_Money_Positions_Long_All", "Lev_Money_Positions_Short_All", "Lev_Money_Positions_Spread_All",
            "Open_Interest_All",
            "Pct_of_OI_Lev_Money_Long_All", "Pct_of_OI_Lev_Money_Short_All",
            "Traders_Lev_Money_Long_All", "Traders_Lev_Money_Short_All",
            "Report_Date_as_YYYY-MM-DD", "Market_and_Exchange_Names", "CFTC_Contract_Market_Code",
        )


def parse_market(txt_path, report, market_code, weeks=52):
    """解析指定市场代码的所有历史周，返回按日期升序的记录列表（每个含计算指标）。"""
    (c_long, c_short, c_spread, c_oi, c_pl, c_ps, c_tl, c_ts, c_date, c_name, c_code) = _field_map(report)

    rows = []
    with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        # 校验关键列存在
        missing = [c for c in (c_long, c_short, c_oi, c_date, c_code) if c not in (reader.fieldnames or [])]
        if missing:
            raise RuntimeError(f"文件列缺失: {missing}；可能报告类型不匹配（disagg/fin）。")
        for r in reader:
            if (r.get(c_code) or "").strip() != market_code:
                continue
            dt = r.get(c_date, "").strip()
            try:
                d = datetime.strptime(dt, "%Y-%m-%d")
            except ValueError:
                continue
            long_ = _to_num(r.get(c_long))
            short_ = _to_num(r.get(c_short))
            spread_ = _to_num(r.get(c_spread))
            oi = _to_num(r.get(c_oi))
            if long_ is None or short_ is None or oi is None or oi <= 0:
                continue
            net = long_ - short_
            net_oi = net / oi
            ls = (long_ / short_) if short_ else None
            # Pct_of_OI_* 列在文件中已是百分数(37.3 表示 37.3%)，转成小数以便 _pct() 统一处理
            lp = _to_num(r.get(c_pl))
            sp = _to_num(r.get(c_ps))
            rows.append({
                "date": d,
                "date_s": dt,
                "name": (r.get(c_name) or "").strip(),
                "oi": oi,
                "long": long_,
                "short": short_,
                "spread": spread_,
                "net": net,
                "net_oi": net_oi,
                "ls": ls,
                "long_pct": (lp / 100.0) if lp is not None else None,
                "short_pct": (sp / 100.0) if sp is not None else None,
                "traders_long": _to_num(r.get(c_tl)),
                "traders_short": _to_num(r.get(c_ts)),
            })

    if not rows:
        raise RuntimeError(f"未在文件中找到市场代码 {market_code} 的数据（可能该品种不在本报告内）。")

    rows.sort(key=lambda x: x["date"])
    return rows


def _percentile_rank(history, value):
    """value 在 history 列表中的百分位（0–1），含自身。"""
    if not history:
        return None
    below = sum(1 for h in history if h < value)
    return (below + 0.5) / len(history)


def _crowding_label(pct):
    """根据净头寸/OI 历史分位给出拥挤度等级。"""
    if pct is None:
        return "—"
    if pct >= 0.90:
        return "极度拥挤·做多"
    if pct >= 0.75:
        return "偏拥挤·做多"
    if pct <= 0.10:
        return "极度拥挤·做空"
    if pct <= 0.25:
        return "偏拥挤·做空"
    return "中性"


# ---------------------------------------------------------------------------
# 汇总
# ---------------------------------------------------------------------------
def summarize(rows, weeks=52):
    latest = rows[-1]
    window = rows[-weeks:] if len(rows) >= weeks else rows
    hist_net_oi = [r["net_oi"] for r in window[:-1]]  # 剔除最新，用于分位
    pct = _percentile_rank(hist_net_oi, latest["net_oi"]) if len(window) > 1 else None

    prev = rows[-2] if len(rows) >= 2 else None
    d_net = (latest["net"] - prev["net"]) if prev else None
    d_net_oi = (latest["net_oi"] - prev["net_oi"]) if prev else None
    d_long = (latest["long"] - prev["long"]) if prev else None
    d_short = (latest["short"] - prev["short"]) if prev else None

    return {
        "name": latest["name"],
        "report_date": latest["date_s"],
        "oi": latest["oi"],
        "long": latest["long"],
        "short": latest["short"],
        "spread": latest["spread"],
        "net": latest["net"],
        "net_oi": latest["net_oi"],
        "ls": latest["ls"],
        "long_pct": latest["long_pct"],
        "short_pct": latest["short_pct"],
        "traders_long": latest["traders_long"],
        "traders_short": latest["traders_short"],
        "weeks_window": len(window),
        "net_oi_pct_rank": pct,
        "crowding": _crowding_label(pct),
        "prev_report_date": prev["date_s"] if prev else None,
        "d_net": d_net,
        "d_net_oi": d_net_oi,
        "d_long": d_long,
        "d_short": d_short,
    }


def to_text(s):
    lines = []
    lines.append(f"CFTC 持仓拥挤度 — {s['name']}")
    lines.append(f"报告日期: {s['report_date']}  (回溯窗口 {s['weeks_window']} 周)")
    lines.append("-" * 52)
    lines.append(f"未平仓(OI)        : {_num(s['oi'], 0)} 手")
    lines.append(f"投机多头          : {_num(s['long'], 0)} 手  ({_pct(s['long_pct'])})")
    lines.append(f"投机空头          : {_num(s['short'], 0)} 手  ({_pct(s['short_pct'])})")
    lines.append(f"投机价差          : {_num(s['spread'], 0)} 手")
    lines.append(f"投机净头寸 Net    : {_num(s['net'], 0)} 手")
    lines.append(f"净头寸/OI         : {_pct(s['net_oi'])}")
    lines.append(f"多空比 L/S        : {_num(s['ls'], 2)}")
    lines.append(f"历史分位(Net/OI)  : {_pct(s['net_oi_pct_rank'])}  →  {s['crowding']}")
    lines.append(f"投机交易商(多/空) : {_num(s['traders_long'], 0)} / {_num(s['traders_short'], 0)}")
    if s["prev_report_date"]:
        lines.append("-" * 52)
        lines.append(f"周环比 (vs {s['prev_report_date']}):")
        lines.append(f"  ΔNet           : {_num(s['d_net'], 0)} 手")
        lines.append(f"  Δ净头寸/OI     : {_pct(s['d_net_oi'])}")
        lines.append(f"  Δ多头 / Δ空头  : {_num(s['d_long'], 0)} / {_num(s['d_short'], 0)} 手")
    lines.append("=" * 52)
    lines.append("解读：净头寸/OI 历史分位 ≥90% = 投机极度做多(拥挤,警惕反转)；")
    lines.append("      ≤10% = 投机极度做空(拥挤,警惕轧空)；中性区间跟随趋势。")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def fetch(symbol=None, market_code=None, report=None, weeks=52, from_file=None, as_json=False, force=False):
    # 解析目标市场
    if market_code and report:
        mkt = (report, market_code, "自定义", "mm" if report == "disagg" else "lf")
    elif symbol:
        key = symbol.upper()
        if key not in MARKETS:
            raise RuntimeError(f"未知品种 '{symbol}'；可用: " + ", ".join(sorted(MARKETS.keys())))
        mkt = MARKETS[key]
    else:
        raise RuntimeError("必须提供 --symbol 或 --market-code+--report")

    report_type, code, label, _spec = mkt

    # 数据来源
    if from_file:
        txt_path = _read_local(from_file)
        # 本地文件需由用户指定 report 类型
        if not report:
            report_type = "disagg" if "f_year" in os.path.basename(from_file) else "fin"
        rows = parse_market(txt_path, report_type, code, weeks=weeks)
    else:
        year = datetime.now().year
        txt_path = _download_zip(report_type, year, force=force)
        rows = parse_market(txt_path, report_type, code, weeks=weeks)
        # 当前年样本不足窗口时，叠加上一年以扩充历史分位
        if len(rows) < weeks and year > 2007:
            try:
                p2 = _download_zip(report_type, year - 1, force=force)
                rows2 = parse_market(p2, report_type, code, weeks=weeks)
                seen = set()
                merged = []
                for r in rows + rows2:
                    if r["date_s"] not in seen:
                        seen.add(r["date_s"])
                        merged.append(r)
                merged.sort(key=lambda x: x["date"])
                rows = merged
            except Exception as e:  # noqa: BLE001
                print(f"[cftc] 上一年历史加载失败，使用当前年数据: {e}", file=sys.stderr)

    s = summarize(rows, weeks=weeks)
    s["symbol"] = symbol.upper() if symbol else code
    s["market_code"] = code
    s["report_type"] = report_type
    return s


def main():
    ap = argparse.ArgumentParser(description="CFTC COT/TFF 持仓拥挤度抓取（免费·无需密钥）")
    ap.add_argument("--symbol", help="品种别名，如 GOLD / WTI / EURUSD / JPYUSD / AUDUSD")
    ap.add_argument("--market-code", help="CFTC 合约代码，如 088691(黄金) / 067651(WTI) / 099741(EURUSD)")
    ap.add_argument("--report", choices=["disagg", "fin"], help="报告类型（配合 --market-code 或 --from-file）")
    ap.add_argument("--weeks", type=int, default=52, help="历史分位回溯窗口（周），默认 52")
    ap.add_argument("--from-file", help="直接解析本地 txt（f_year.txt 或 FinFutYY.txt），离线/预下载用")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--list", action="store_true", help="列出支持的品种")
    ap.add_argument("--force", action="store_true", help="强制重新下载（忽略缓存）")
    args = ap.parse_args()

    if args.list:
        print("支持品种 (--symbol):")
        for k in sorted(MARKETS.keys()):
            rt, code, name, _ = MARKETS[k]
            print(f"  {k:8s} -> {name:22s} [{rt}] code={code}")
        return

    try:
        s = fetch(symbol=args.symbol, market_code=args.market_code,
                  report=args.report, weeks=args.weeks, from_file=args.from_file,
                  as_json=args.json, force=args.force)
    except Exception as e:  # noqa: BLE001
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        import json
        print(json.dumps(s, ensure_ascii=False, indent=2, default=str))
    else:
        print(to_text(s))


if __name__ == "__main__":
    main()
