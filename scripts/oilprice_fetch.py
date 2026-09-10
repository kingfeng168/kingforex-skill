#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OilPriceAPI 油价拉取脚本（仅依赖 Python 标准库,无需 pip 安装）。

面向 kingforex-skill 原油模块:拉取 WTI / Brent / 天然气等实时与历史油价。
端点(2026-09 官方 SDK 源码实测):
  实时: GET https://api.oilpriceapi.com/v1/prices/latest?by_code=WTI_USD
  全部: GET https://api.oilpriceapi.com/v1/prices/all
  历史: GET https://api.oilpriceapi.com/v1/prices/past_year?commodity=WTI_USD&interval=daily&start_date=&end_date=
认证: 请求头 Authorization: Token <key>(从官方 Python SDK 1.13.0 源码确认)。

常用 by_code:
  WTI_USD / BRENT_CRUDE_USD / NATURAL_GAS_USD / HEATING_OIL_USD / DIESEL_USD

用法示例:
  python oilprice_fetch.py --code WTI_USD
  python oilprice_fetch.py --code WTI_USD --code BRENT_CRUDE_USD      # 多品种(批量,逗号或多次)
  python oilprice_fetch.py --code WTI_USD --history --start 2026-08-01 --end 2026-09-04
  python oilprice_fetch.py --code BRENT_CRUDE_USD --out "D:/workbuddy/输出文件/brent.json"

key 读取优先级: --api-key > 环境变量 OILPRICEAPI_KEY > scripts/.oilprice_key(本地,不进 zip)。
"""
import urllib.request
import urllib.error
import urllib.parse
import os
import sys
import json
import argparse

BASE = "https://api.oilpriceapi.com"

# 默认关注的品种(原油模块核心)
DEFAULT_CODES = ["WTI_USD", "BRENT_CRUDE_USD"]


def _read_local_key():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".oilprice_key")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def _get(path, api_key, params, timeout=30):
    url = f"{BASE}{path}?" + urllib.parse.urlencode(params)
    headers = {
        "accept": "application/json",
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:400]
        if e.code == 401:
            return {"_error": "auth", "detail": "key 无效/吊销;请检查 .oilprice_key 或 --api-key"}
        if e.code == 429:
            return {"_error": "rate_limit", "detail": "触发限频(60 次/60 秒),请稍候重试"}
        return {"_error": f"HTTP {e.code}", "detail": body}
    except Exception as e:  # noqa
        return {"_error": type(e).__name__, "detail": str(e)}


def _norm_row(d):
    """兼容 price / value 两种字段命名(不同 SDK 版本)。"""
    if not isinstance(d, dict):
        return d
    return {
        "code": d.get("code") or d.get("commodity"),
        "price": d.get("price", d.get("value")),
        "currency": d.get("currency", "USD"),
        "unit": d.get("unit", "barrel"),
        "created_at": d.get("created_at") or d.get("timestamp"),
    }


def fetch_latest(codes, api_key):
    params = {"by_code": ",".join(codes)}
    d = _get("/v1/prices/latest", api_key, params)
    if "_error" in d:
        return d
    data = d.get("data", d)
    rows = data.get("prices", []) if isinstance(data, dict) and "prices" in data else (
        data if isinstance(data, list) else [data])
    return [_norm_row(r) for r in rows]


def fetch_history(code, api_key, start, end, interval="daily", per_page=100):
    params = {"commodity": code, "interval": interval, "page": 1, "per_page": per_page, "by_type": "spot_price"}
    if start:
        params["start_date"] = start
    if end:
        params["end_date"] = end
    d = _get("/v1/prices/past_year", api_key, params)
    if "_error" in d:
        return d
    data = d.get("data", d)
    rows = data.get("prices", []) if isinstance(data, dict) and "prices" in data else (
        data if isinstance(data, list) else [])
    return [_norm_row(r) for r in rows]


def main():
    p = argparse.ArgumentParser(description="OilPriceAPI 油价拉取")
    p.add_argument("--code", action="append", default=None, help="by_code,如 WTI_USD;可多次或逗号分隔")
    p.add_argument("--history", action="store_true", help="拉历史(默认实时)")
    p.add_argument("--start", help="历史开始日期 YYYY-MM-DD")
    p.add_argument("--end", help="历史结束日期 YYYY-MM-DD")
    p.add_argument("--interval", default="daily")
    p.add_argument("--per-page", type=int, default=100)
    p.add_argument("--all", action="store_true", help="拉取账户全部可用品种")
    p.add_argument("--api-key")
    p.add_argument("--out", help="输出 JSON 路径")
    args = p.parse_args()

    api_key = args.api_key or os.environ.get("OILPRICEAPI_KEY") or _read_local_key()
    if not api_key:
        print("需要 --api-key 或环境变量 OILPRICEAPI_KEY 或 scripts/.oilprice_key")
        sys.exit(1)

    if args.all:
        d = _get("/v1/prices/all", api_key, {})
        if "_error" in d:
            print(f"[错误] {d['_error']}: {d['detail']}")
            sys.exit(1)
        data = d.get("data", d)
        result = [_norm_row(r) for r in (data if isinstance(data, list) else data.get("prices", []))]
    elif args.history:
        codes = args.code or DEFAULT_CODES
        result = {}
        for c in codes:
            rows = fetch_history(c, api_key, args.start, args.end, args.interval, args.per_page)
            if isinstance(rows, dict) and "_error" in rows:
                result[c] = rows
            else:
                result[c] = rows
    else:
        codes = args.code or DEFAULT_CODES
        result = fetch_latest(codes, api_key)
        if isinstance(result, dict) and "_error" in result:
            print(f"[错误] {result['_error']}: {result['detail']}")
            sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"已保存 -> {args.out}")


if __name__ == "__main__":
    main()
