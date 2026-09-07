#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iTick 行情拉取脚本（仅依赖 Python 标准库，无需 pip 安装）。

面向 kingforex-skill 外汇 / 贵金属 / 期货模块：拉取 iTick 实时报价与 K 线历史。
iTick 覆盖外汇、贵金属(XAUUSD 等)、期货(黄金 GC / 原油 CL / 股指等)、股票、crypto。
免费套餐 key 走 api-free.itick.org（限频 5 次/分钟）；付费 key 走 api.itick.org。

用法示例:
  # 现货黄金实时报价(外汇模块,region=GB)
  python itick_fetch.py quote --asset forex --region GB --code XAUUSD
  # 黄金期货 GC 实时报价(期货模块,region=US)
  python itick_fetch.py quote --asset future --region US --code GC
  # WTI 原油期货实时报价
  python itick_fetch.py quote --asset future --region US --code CL
  # 现货黄金日 K 线最近 5 根(kType=1 日;1m=0,5m=4,1h=7,1d=1)
  python itick_fetch.py kline --asset forex --region GB --code XAUUSD --kType 1 --limit 5
  # 黄金期货 K 线
  python itick_fetch.py kline --asset future --region US --code GC --kType 7 --limit 50

key 读取优先级: --api-key > 环境变量 ITICK_API_KEY > scripts/.itick_key（本地文件,不进 zip）。
"""
import urllib.request
import urllib.error
import urllib.parse
import os
import sys
import json
import argparse
import time

# 免费套餐默认主机;付费 key 用 --base https://api.itick.org 覆盖
DEFAULT_BASE = "https://api-free.itick.org"

# region 约定:外汇/贵金属=GB,期货/美股/原油=US,港股=HK
REGION_DEFAULT = {"forex": "GB", "future": "US", "stock": "HK", "crypto": "US", "index": "US"}

# kType(period) 映射: iTick 用数字枚举
K_TYPE = {
    "1m": 0, "5m": 4, "15m": 5, "30m": 6, "1h": 7, "2h": 8,
    "4h": 9, "1d": 1, "1w": 2, "1mo": 3,
}
K_TYPE_REV = {v: k for k, v in K_TYPE.items()}


def _read_local_key():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".itick_key")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def _get(path, api_key, base, params, timeout=30):
    url = f"{base}{path}?" + urllib.parse.urlencode(params)
    headers = {"accept": "application/json", "token": api_key}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:400]
        if e.code == 429:
            return {"_error": "rate_limit", "detail": "iTick 免费套餐限频 5 次/分钟,请稍候重试"}
        return {"_error": f"HTTP {e.code}", "detail": body}
    except Exception as e:  # noqa
        return {"_error": type(e).__name__, "detail": str(e)}


def _norm_quote(data):
    """把 quote data 字典整理为可读行。"""
    if not isinstance(data, dict):
        return None
    out = {}
    for k in ("s", "code", "symbol", "p", "price", "ld", "o", "open", "h", "high",
              "l", "low", "c", "close", "v", "volume", "tu", "ch", "change",
              "chp", "change_percent", "t", "ts", "r", "region", "type"):
        if k in data:
            out[k] = data[k]
    return out


def cmd_quote(args):
    base = args.base
    api_key = args.api_key or os.environ.get("ITICK_API_KEY") or _read_local_key()
    if not api_key:
        print("需要 --api-key 或环境变量 ITICK_API_KEY 或 scripts/.itick_key")
        return None
    region = args.region or REGION_DEFAULT.get(args.asset, "US")
    path = f"/{args.asset}/quote"
    params = {"region": region, "code": args.code}
    d = _get(path, api_key, base, params)
    if "_error" in d:
        print(f"[错误] {d['_error']}: {d['detail']}")
        return None
    # iTick 返回 {"code":0,"msg":null,"data":{...}}
    data = d.get("data", d)
    norm = _norm_quote(data)
    print(f"iTick {args.asset} 报价  region={region} code={args.code}")
    print(json.dumps(norm if norm else data, ensure_ascii=False, indent=2))
    return norm if norm else data


def cmd_kline(args):
    base = args.base
    api_key = args.api_key or os.environ.get("ITICK_API_KEY") or _read_local_key()
    if not api_key:
        print("需要 --api-key 或环境变量 ITICK_API_KEY 或 scripts/.itick_key")
        return None
    region = args.region or REGION_DEFAULT.get(args.asset, "US")
    path = f"/{args.asset}/kline"
    if args.kType in K_TYPE:
        ktype = K_TYPE[args.kType]
    else:
        try:
            ktype = int(args.kType)
        except ValueError:
            print(f"未知 kType={args.kType};可用: {', '.join(K_TYPE)} 或数字")
            return None
    params = {"region": region, "code": args.code, "kType": ktype, "limit": args.limit}
    if args.et:
        params["et"] = args.et
    d = _get(path, api_key, base, params)
    if "_error" in d:
        print(f"[错误] {d['_error']}: {d['detail']}")
        return None
    rows = d.get("data", [])
    if not isinstance(rows, list):
        rows = [rows]
    print(f"iTick {args.asset} K线  region={region} code={args.code} kType={args.kType} 共 {len(rows)} 根")
    # 输出精简 OHLCV
    out = []
    for r in rows:
        out.append({
            "t": r.get("t"),
            "o": r.get("o"), "h": r.get("h"), "l": r.get("l"), "c": r.get("c"),
            "v": r.get("v"), "tu": r.get("tu"),
        })
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out


def main():
    p = argparse.ArgumentParser(description="iTick 行情拉取(外汇/贵金属/期货)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pq = sub.add_parser("quote", help="实时报价")
    pq.add_argument("--asset", default="forex", choices=["forex", "future", "stock", "crypto", "index"])
    pq.add_argument("--region")
    pq.add_argument("--code", required=True, help="标的代码,如 XAUUSD / GC / CL / ES")
    pq.add_argument("--api-key")
    pq.add_argument("--base", default=DEFAULT_BASE)
    pq.set_defaults(func=cmd_quote)

    pk = sub.add_parser("kline", help="K线历史")
    pk.add_argument("--asset", default="forex", choices=["forex", "future", "stock", "crypto", "index"])
    pk.add_argument("--region")
    pk.add_argument("--code", required=True)
    pk.add_argument("--kType", default="1d", help="周期:1m/5m/15m/30m/1h/2h/4h/1d/1w/1mo 或数字")
    pk.add_argument("--limit", type=int, default=20, help="根数(最大 500)")
    pk.add_argument("--et", help="结束时间戳(毫秒,可选)")
    pk.add_argument("--api-key")
    pk.add_argument("--base", default=DEFAULT_BASE)
    pk.set_defaults(func=cmd_kline)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
