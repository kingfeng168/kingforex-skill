#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quantgist_fetch.py — QuantGist API v1 取数脚本 (kingforex-skill 内置)

用途:为手动外汇/贵金属/大宗商品交易者拉取「事件驱动 + 地缘情报 + 情绪」层数据,
      补 BIS/EIA/IMF/World Bank 仅有宏观基本面、缺事件/情报的短板。

Base URL : https://api.quantgist.com/v1
认证     : HTTP 头 X-API-Key (格式 qg_live_xxx / qg_test_xxx)
Key 来源 : 命令行 --api-key 优先;否则读环境变量 QUANTGIST_API_KEY (不写死进脚本)。

覆盖预设(按交易价值筛选):
  calendar       今日经济日历(/v1/calendar)
  calendar_range 区间日历(/v1/calendar/range?start=&end=)       需 --start/--end
  events         历史经济事件(/v1/events)                       可选 --limit/--currency/--impact
  macro_latest   宏数据最近发布值(/v1/macro/latest?event=)      需 --alias(默认 CPI)
  macro_upcoming 宏数据下次预定发布(/v1/macro/upcoming?event=)  需 --alias
  macro_calendar 多别名发布日历(/v1/macro/calendar?events=)     需 --aliases(A,B)
  news           原始新闻流(/v1/news)                           可选 --limit
  news_radar     聚类交易情报(地缘/油价/央行意外,含 affected_assets) 可选 --lookback/--min-impact
  sentiment      情绪汇总(/v1/sentiment/summary)                ※ Starter+ 付费层,可能 402
  surprises      偏离度排名(/v1/intelligence/surprises)         ※ Starter+ 可能 402
  movers         影响力排名(/v1/intelligence/movers)            ※ Starter+ 可能 402
  commodities    商品 ETF 快照 GLD/USO(/v1/markets/commodities)
  usage          本 key 用量统计(/v1/usage)

宏别名速记(--alias/--aliases 可用): NFP CPI PCE FOMC GDP UNEMPLOYMENT RETAIL_SALES PPI ISM ECB HICP

输出: 默认 CSV(UTF-8-SIG,Excel 友好); --json 输出原始 JSON。
      --out 指定落盘路径;省略则打印到 stdout。

依赖: 仅 Python 标准库 (urllib / json / csv / argparse)。Python 3.8+。

错误处理: 401=key 无效;402=当前套餐不含该端点(需升级);429=限速;5xx=服务端/维护。
         均打印友好消息并附 docs 链接,不崩溃。
"""
import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.quantgist.com/v1"
DOCS = "https://quantgist.com/docs"

PRESETS = {
    "calendar":      ("/calendar", {}),
    "calendar_range":("/calendar/range", {}),          # 需 start/end
    "events":        ("/events", {}),
    "macro_latest":  ("/macro/latest", {}),            # 需 alias
    "macro_upcoming":("/macro/upcoming", {}),          # 需 alias
    "macro_calendar":("/macro/calendar", {}),          # 需 aliases
    "news":          ("/news", {}),
    "news_radar":    ("/news/radar", {}),
    "sentiment":     ("/sentiment/summary", {}),
    "surprises":     ("/intelligence/surprises", {}),
    "movers":        ("/intelligence/movers", {}),
    "commodities":   ("/markets/commodities", {}),
    "usage":         ("/usage", {}),
}

MACRO_ALIASES = ["NFP", "CPI", "PCE", "FOMC", "GDP", "UNEMPLOYMENT",
                 "RETAIL_SALES", "PPI", "ISM", "ECB", "HICP"]


def get_key(args):
    if args.api_key:
        return args.api_key
    ev = os.environ.get("QUANTGIST_API_KEY")
    if ev:
        return ev
    sys.stderr.write(
        "❌ 未提供 API key。用法二选一:\n"
        "   1) 环境变量:  export QUANTGIST_API_KEY='qg_live_xxx'\n"
        "   2) 命令行:    --api-key 'qg_live_xxx'\n"
        "   申请/查看: https://quantgist.com/dashboard\n"
    )
    sys.exit(2)


def build_path(preset, args):
    path, base_params = PRESETS[preset]
    params = dict(base_params)
    if preset == "calendar_range":
        if not (args.start and args.end):
            sys.stderr.write("❌ calendar_range 需要 --start 与 --end (YYYY-MM-DD)\n")
            sys.exit(2)
        params["start"] = args.start
        params["end"] = args.end
    elif preset in ("macro_latest", "macro_upcoming"):
        params["event"] = args.alias or "CPI"
    elif preset == "macro_calendar":
        if not args.aliases:
            sys.stderr.write("❌ macro_calendar 需要 --aliases (如 CPI,NFP,FOMC)\n")
            sys.exit(2)
        params["events"] = args.aliases
    elif preset == "events":
        if args.limit:
            params["limit"] = args.limit
        if args.currency:
            params["currency"] = args.currency
        if args.impact:
            params["impact"] = args.impact
    elif preset == "news":
        if args.limit:
            params["limit"] = args.limit
    elif preset == "news_radar":
        if args.lookback:
            params["lookback_hours"] = args.lookback
        if args.min_impact is not None:
            params["min_impact"] = args.min_impact
    return path, params


def fetch(path, params, api_key, timeout=30):
    url = BASE + path
    if params:
        q = "&".join("%s=%s" % (k, urllib.parse.quote(str(v))) for k, v in params.items())
        url += "?" + q
    req = urllib.request.Request(url, headers={
        "User-Agent": "kingforex-skill/quantgist_fetch",
        "X-API-Key": api_key,
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        try:
            err = json.loads(body)
            msg = err.get("error", {}).get("message") or body
        except Exception:
            msg = body
        hint = {
            401: "API key 无效或未授权 —— 检查 QUANTGIST_API_KEY / --api-key",
            402: "当前套餐不含此端点(Starter+/Pro+ 才开放)—— 需升级订阅",
            403: "禁止访问(可能 key 权限不足)",
            429: "触发速率限制 —— 稍后重试,或查看 X-RateLimit-* 头",
            503: "QuantGist 服务端维护/暂不可用 —— 稍后重试",
        }.get(e.code, "HTTP %s" % e.code)
        return None, "HTTP %s: %s | %s | docs: %s" % (e.code, hint, msg, DOCS)
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, str(e)[:200])


def extract_items(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("data", "items"):
            if isinstance(obj.get(key), list):
                return obj[key]
    return [obj] if isinstance(obj, dict) else []


def flat_row(d):
    row = {}
    for k, v in d.items():
        if isinstance(v, list):
            row[k] = ";".join(str(x) for x in v)
        elif isinstance(v, dict):
            row[k] = json.dumps(v, ensure_ascii=False)
        else:
            row[k] = "" if v is None else str(v)
    return row


def to_csv(obj, out):
    items = extract_items(obj)
    if not items:
        sys.stderr.write("⚠️ 响应中无列表数据,已输出原始 JSON 供检查。\n")
        data = json.dumps(obj, ensure_ascii=False, indent=2)
        if out:
            with open(out, "w", encoding="utf-8-sig") as f:
                f.write(data)
        else:
            print(data)
        return
    rows = [flat_row(it) for it in items]
    cols = []
    for r in rows:
        for c in r:
            if c not in cols:
                cols.append(c)
    if out:
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        sys.stderr.write("✅ CSV 已写入: %s (%d 行, %d 列)\n" % (out, len(rows), len(cols)))
    else:
        w = csv.DictWriter(sys.stdout, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(
        description="QuantGist API v1 取数 (事件/情报/情绪层), 标准库实现, 无需 pip。")
    ap.add_argument("--preset", help="预设端点: " + ", ".join(PRESETS.keys()))
    ap.add_argument("--api-key", help="QuantGist API key (或用环境变量 QUANTGIST_API_KEY)")
    ap.add_argument("--alias", help="宏别名 (macro_latest/upcoming), 默认 CPI")
    ap.add_argument("--aliases", help="多别名逗号分隔 (macro_calendar), 如 CPI,NFP,FOMC")
    ap.add_argument("--start", help="区间开始 YYYY-MM-DD (calendar_range)")
    ap.add_argument("--end", help="区间结束 YYYY-MM-DD (calendar_range)")
    ap.add_argument("--currency", help="事件筛选币种, 如 USD")
    ap.add_argument("--impact", help="事件筛选影响级别 high/medium/low")
    ap.add_argument("--limit", help="事件/新闻条数上限")
    ap.add_argument("--lookback", help="news_radar 回溯小时数, 如 72")
    ap.add_argument("--min-impact", type=float, help="news_radar 最小影响分, 如 0.6")
    ap.add_argument("--json", action="store_true", help="输出原始 JSON 而非 CSV")
    ap.add_argument("--out", help="输出文件路径 (省略则打印到 stdout)")
    ap.add_argument("--list-presets", action="store_true", help="列出所有预设后退出")
    args = ap.parse_args()

    if args.list_presets:
        for k in PRESETS:
            print(" -", k)
        return

    if not args.preset:
        ap.error("请指定 --preset (或 --list-presets 查看可选值)")

    api_key = get_key(args)
    path, params = build_path(args.preset, args)
    obj, err = fetch(path, params, api_key)
    if err:
        sys.stderr.write("❌ %s\n" % err)
        sys.exit(1)
    if args.json:
        data = json.dumps(obj, ensure_ascii=False, indent=2)
        if args.out:
            with open(args.out, "w", encoding="utf-8-sig") as f:
                f.write(data)
            sys.stderr.write("✅ JSON 已写入: %s\n" % args.out)
        else:
            print(data)
    else:
        to_csv(obj, args.out)


if __name__ == "__main__":
    main()
