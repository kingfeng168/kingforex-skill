#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kline_fetch.py — 从权威渠道获取 K 线(OHLCV)历史数据 (kingforex-skill 模块九)

主源:Twelve Data (https://twelvedata.com)
  - 中国大陆可直连(已实测,无需翻墙),覆盖外汇 / 黄金 / 原油与全部周期。
  - 需 API Key:环境变量 TWELVEDATA_API_KEY 或 --api-key(免费注册 twelvedata.com)。
  - 覆盖周期:15min / 1h / 4h / 1day / 1week。

铁律(与技能整体一致):
  - 只返回真实抓取到的数据;任一源失败 / 返回空 / Key 缺失,返回 (None, 原因),绝不编造、估算或凭记忆生成任何价格。
  - 数据源不提供"方向",只提供客观 OHLC;方向仍由三维印证收敛决定。

用法:
  python kline_fetch.py --symbol USDJPY --interval 1h --api-key <KEY>
  python kline_fetch.py --symbol XAUUSD --api-key <KEY> --out "./output/xauusd.csv"
  python kline_fetch.py --symbol USOIL --json
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

TD_BASE = "https://api.twelvedata.com/time_series"

# 标准周期:(展示标签, Twelve Data interval 参数)
STD_INTERVALS = [
    ("15min", "15min"),
    ("1H", "1h"),
    ("4H", "4h"),
    ("1D", "1day"),
    ("1W", "1week"),
]

# 品种别名 → Twelve Data 标准符号
ALIASES = {
    "XAUUSD": "XAU/USD", "XAU": "XAU/USD", "GOLD": "XAU/USD", "黄金": "XAU/USD",
    "XAGUSD": "XAG/USD", "XAG": "XAG/USD", "SILVER": "XAG/USD", "白银": "XAG/USD",
    "USOIL": "WTI/USD", "WTI": "WTI/USD", "CL": "WTI/USD", "原油": "WTI/USD",
    "UKOIL": "BRENT/USD", "BRENT": "BRENT/USD", "布伦特": "BRENT/USD",
}


def normalize_symbol(sym):
    """把用户输入的品种归一化为 Twelve Data 接受的格式。"""
    s = (sym or "").strip().upper()
    if not s:
        return s
    if s in ALIASES:
        return ALIASES[s]
    if "/" in s:
        return s  # 已是 XAU/USD 形式
    # 外汇对 6 字母(如 USDJPY)→ 补斜杠 USD/JPY
    if len(s) == 6 and s.isalpha():
        return s[:3] + "/" + s[3:]
    return s


def _read_td_key():
    """从脚本同目录 .td_key 读取 Twelve Data Key(本地便利,不进 zip)。"""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".td_key")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def fetch_one(symbol, interval, apikey, output_size=200):
    """抓取单周期 K 线。

    成功:返回 bars=[{t,o,h,l,c,v}](时间正序,最新在末尾)。
    失败:返回 (None, 原因字符串)。
    """
    if not apikey:
        apikey = _read_td_key()
    if not apikey:
        return None, "缺少 API Key(TWELVEDATA_API_KEY 或 --api-key 或 scripts/.td_key)"
    sym = normalize_symbol(symbol)
    url = (f"{TD_BASE}?symbol={urllib.parse.quote(sym)}"
           f"&interval={urllib.parse.quote(interval)}"
           f"&outputsize={output_size}&apikey={urllib.parse.quote(apikey)}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code} {e.reason}"
    except Exception as e:  # 网络不可达 / 超时 / DNS
        return None, f"{type(e).__name__}: {e}"

    try:
        d = json.loads(raw)
    except Exception as e:
        return None, f"JSON 解析失败: {e}"

    # Twelve Data 业务错误:{"status":"error","message":"..."}
    if isinstance(d, dict) and d.get("status") == "error":
        return None, d.get("message", "unknown error")
    vals = d.get("values") if isinstance(d, dict) else None
    if not vals:
        return None, "返回空数据(品种不支持或区间无数据)"

    bars = []
    for v in vals:  # values 按时间倒序(最新在前)
        try:
            bars.append({
                "t": v["datetime"],
                "o": float(v["open"]),
                "h": float(v["high"]),
                "l": float(v["low"]),
                "c": float(v["close"]),
                "v": float(v.get("volume") or 0.0),
            })
        except Exception:
            continue
    if not bars:
        return None, "返回空数据"
    bars.reverse()  # 转为时间正序(旧→新),与 kline_read.analyze 一致
    return bars, None


def fetch_multi(symbol, intervals=None, apikey="", output_size=200):
    """抓取多周期。返回 {标签: (bars|None, 原因)}。"""
    if intervals is None:
        intervals = STD_INTERVALS
    return {label: fetch_one(symbol, ival, apikey, output_size) for label, ival in intervals}


def main():
    ap = argparse.ArgumentParser(description="K线抓取(Twelve Data 权威源)")
    ap.add_argument("--symbol", required=True, help="品种,如 USDJPY / XAUUSD / USOIL")
    ap.add_argument("--interval", default="1h", help="周期:15min/1h/4h/1day/1week")
    ap.add_argument("--api-key", default=os.environ.get("TWELVEDATA_API_KEY", "") or _read_td_key(),
                    help="Twelve Data API Key(或环境变量 TWELVEDATA_API_KEY 或 scripts/.td_key)")
    ap.add_argument("--out", help="输出 CSV 路径(不指定则打印屏幕)")
    ap.add_argument("--json", action="store_true", help="以 JSON 打印")
    args = ap.parse_args()

    bars, err = fetch_one(args.symbol, args.interval, args.api_key)
    if bars is None:
        print(f"✗ 获取失败:{err}")
        sys.exit(1)

    if args.out:
        import csv
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["datetime", "open", "high", "low", "close", "volume"])
            for b in bars:
                w.writerow([b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]])
        print(f"[CSV] -> {args.out} ({len(bars)} 根)")
    elif args.json:
        print(json.dumps(bars, ensure_ascii=False, indent=2))
    else:
        print(f"✓ {args.symbol} {args.interval}: {len(bars)} 根, 最新收盘 {bars[-1]['c']}")
        for b in bars[-3:]:
            print(f"  {b['t']}  O{b['o']} H{b['h']} L{b['l']} C{b['c']} V{b['v']}")


if __name__ == "__main__":
    main()
