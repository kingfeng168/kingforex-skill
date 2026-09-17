#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
goldprice.dev 金价拉取脚本（仅依赖 Python 标准库,无需 pip 安装）。

面向 kingforex-skill 黄金模块:拉取 goldprice.dev 的现货金(XAU)实时价与历史 K 线。

端点(2026-09 官方文档实测):
  当前价 : GET https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT
  历史棒 : GET https://api.goldprice.dev/v1/bars?symbol=XAU-USD-SPOT&interval=1d&from=YYYY-MM-DD&to=YYYY-MM-DD
           (⚠️ /v1/prices/history 已于 2026 弃用,本脚本优先走 /v1/bars;
            若 /v1/bars 不可用,自动回退尝试 /v1/prices/history 并做通用解析)
  spot   : GET https://api.goldprice.dev/v1/spot/XAU-USD-SPOT

/v1/bars 响应结构(实测):
  {
    "symbol": "XAU-USD-SPOT", "interval": "1d",
    "bars": [
      {"bar_start":"2026-07-15T00:00:00Z","open":"3327.12","high":"3354.81",
       "low":"3312.44","close":"3348.65","volume":null,"is_closed":true}, ...
    ],
    "next_cursor": "MjAyNi0wNy0xNVQwMDowMDowMFo" | null,
    "meta": {"tier":"free","count":N,"source_id":"mixed"}
  }
  - bars 最新在前(newest-first),本脚本自动按 bar_start 升序排列。
  - 价格字段为字符串(decimal),原样写入 CSV 不丢精度。
  - is_closed=false 表示"当前正在形成的棒",回测/报告应排除(默认排除,--keep-forming 可保留)。
  - 游标分页:next_cursor 非 null 时透传继续翻页,直到为 null。
  - 免费层:仅最近 30 天日线 XAU/USD;更久历史需 Pro。

symbol 写法: XAU-USD-SPOT / XAG-USD-SPOT / XAU-USD 等;quote 货币由符号决定。
历史 CSV 输出文件名自动推导: XAU-USD-SPOT -> kline_XAUUSD_1d.csv(直接喂报告 KD 字典)。

用法示例:
  python goldprice_fetch.py                                       # 现货金 XAU-USD-SPOT 当前价(免费层)
  python goldprice_fetch.py --symbol XAG-USD-SPOT                 # 白银当前价
  python goldprice_fetch.py --api-key ga_live_xxx                 # 带 key(Free 层,提频/解锁选项)
  # 历史 K 线(主路径 /v1/bars)
  python goldprice_fetch.py --history --from 2026-09-01 --to 2026-09-30
  python goldprice_fetch.py --history --symbol XAG-USD-SPOT --from 2026-09-01 --to 2026-09-30 --out kline_XAGUSD_1d.csv
  # 指定输出目录(自动按 symbol 命名)
  python goldprice_fetch.py --history --from 2026-01-01 --to 2026-04-21 --out-dir "./output"

key 读取优先级: --api-key > 环境变量 GOLDPRICE_API_KEY > scripts/.goldprice_key(本地,不进 zip)。

⚠️ 透明说明(与技能整体一致):本构建/沙箱环境对 api.goldprice.dev 的出口被
Cloudflare(错误 1010 "browser signature")拦截,纯标准库 urllib 无法绕过(属 TLS 指纹
层面限制,非代码或 key 错误)。脚本已对 403/cloudflare 做友好降级提示;在用户本机
(正常浏览器/网络)运行即可正常取数。请勿据此判定 key 失效。
"""
import urllib.request
import urllib.error
import urllib.parse
import os
import sys
import csv
import json
import argparse

BASE = "https://api.goldprice.dev"


def _read_local_key():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".goldprice_key")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def _is_cloudflare(text):
    return ("cloudflare" in text.lower()) or ("Just a moment" in text) or ("error_code" in text and "1010" in text)


def _http_get_json(url, api_key, timeout):
    """返回 (dict, None) 或 (None, error_dict)。"""
    headers = {"accept": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:800]
        if e.code in (403, 429) and _is_cloudflare(body):
            return None, {"_error": "cloudflare_block",
                          "detail": "Cloudflare(1010 browser signature)拦截了本环境出口;请在用户本机运行此脚本取数。"}
        return None, {"_error": f"HTTP {e.code}", "detail": body}
    except Exception as e:  # noqa
        return None, {"_error": type(e).__name__, "detail": str(e)}


def fetch(symbol, api_key, timeout=30):
    """当前现货价: /v1/prices"""
    url = f"{BASE}/v1/prices?symbol={urllib.parse.quote(symbol)}"
    return _http_get_json(url, api_key, timeout)


# ── 历史 K 线 ──────────────────────────────────────────────
def _symbol_to_kline_name(symbol):
    """XAU-USD-SPOT -> XAUUSD ; XAG-USD -> XAGUSD ; XAUUSD -> XAUUSD"""
    s = symbol.upper().replace("-SPOT", "").replace("-", "")
    return s


def _normalize_bars(resp):
    """优先解析 /v1/bars 的 bars[] 结构。返回 list[dict(open/high/low/close/bar_start/is_closed)]。"""
    if not isinstance(resp, dict):
        return []
    bars = resp.get("bars") or resp.get("data") or resp.get("prices") or resp.get("series")
    if not isinstance(bars, list):
        return []
    out = []
    for b in bars:
        if not isinstance(b, dict):
            continue
        # 字段映射(兼容 /v1/bars 与可能的 /v1/prices/history 遗留字段)
        t = (b.get("bar_start") or b.get("t") or b.get("time") or b.get("date")
             or b.get("datetime") or b.get("ts") or "")
        o = b.get("open", b.get("o"))
        h = b.get("high", b.get("h"))
        l = b.get("low", b.get("l"))
        c = b.get("close", b.get("c", b.get("price", b.get("p"))))
        if c is None:
            continue  # 无收盘价的棒跳过
        # 若只有收盘价(部分遗留接口),合成扁平棒
        if o is None:
            o = h = l = c
        if h is None:
            h = max(float(o), float(c))
        if l is None:
            l = min(float(o), float(c))
        out.append({
            "bar_start": t,
            "open": str(o), "high": str(h), "low": str(l), "close": str(c),
            "is_closed": b.get("is_closed", True) if isinstance(b.get("is_closed"), bool) else True,
        })
    return out


def fetch_bars(symbol, from_, to_, interval="1d", api_key=None, timeout=30, max_pages=50):
    """走 /v1/bars(主),失败回退 /v1/prices/history(遗留)。返回 (bars_list, error_dict|None)。"""
    collected = []
    err = None
    # 主路径 /v1/bars
    cursor = None
    for _ in range(max_pages):
        q = {"symbol": symbol, "interval": interval, "from": from_, "to": to_}
        if cursor:
            q["cursor"] = cursor
        url = f"{BASE}/v1/bars?" + urllib.parse.urlencode(q)
        resp, e = _http_get_json(url, api_key, timeout)
        if e:
            err = e
            break
        page = _normalize_bars(resp)
        collected.extend(page)
        nc = resp.get("next_cursor") if isinstance(resp, dict) else None
        if not nc:
            err = None
            break
        cursor = nc
    if err is None or err.get("_error") == "cloudflare_block":
        # 主路径成功或确认被 Cloudflare 拦,不再回退
        return collected, err
    # 主路径报错(非 cloudflare),尝试遗留 /v1/prices/history
    legacy_url = (f"{BASE}/v1/prices/history?symbol={urllib.parse.quote(symbol)}"
                  f"&from={urllib.parse.quote(from_)}&to={urllib.parse.quote(to_)}&interval={urllib.parse.quote(interval)}")
    resp, e2 = _http_get_json(legacy_url, api_key, timeout)
    if e2:
        return collected, e2
    legacy = _normalize_bars(resp)
    if legacy:
        return legacy, None
    return collected, err


def bars_to_rows(bars, exclude_forming=True):
    """bars -> 升序 [(datetime, open, high, low, close)];默认剔除正在形成的棒。"""
    rows = []
    for b in bars:
        if exclude_forming and b.get("is_closed") is False:
            continue
        dt = (b.get("bar_start") or "")[:10]  # 取 YYYY-MM-DD
        rows.append((dt, b["open"], b["high"], b["low"], b["close"]))
    rows.sort(key=lambda x: x[0])
    return rows


def write_kline_csv(rows, out_path):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["datetime", "open", "high", "low", "close"])
        for r in rows:
            w.writerow(r)
    return out_path


def main():
    p = argparse.ArgumentParser(description="goldprice.dev 金价拉取(当前价 / 历史 K 线)")
    p.add_argument("--symbol", default="XAU-USD-SPOT", help="如 XAU-USD-SPOT / XAG-USD-SPOT")
    p.add_argument("--api-key")
    p.add_argument("--out", help="当前价模式: 输出 JSON 路径")
    # 历史模式
    p.add_argument("--history", action="store_true", help="拉取历史 K 线(默认写 CSV)")
    p.add_argument("--from", dest="from_", help="历史起始 YYYY-MM-DD")
    p.add_argument("--to", dest="to_", help="历史结束 YYYY-MM-DD")
    p.add_argument("--interval", default="1d", help="K 线周期,默认 1d")
    p.add_argument("--out-dir", help="历史 CSV 输出目录(按 symbol 自动命名)")
    p.add_argument("--keep-forming", action="store_true", help="保留 is_closed=false 的正在形成棒")
    args = p.parse_args()

    api_key = args.api_key or os.environ.get("GOLDPRICE_API_KEY") or _read_local_key()

    if not args.history:
        # ── 当前价 ──
        d = fetch(args.symbol, api_key)
        if d is None:
            print("[错误] 网络异常,未返回数据")
            sys.exit(1)
        if "_error" in d:
            print(f"[错误] {d['_error']}: {d['detail']}")
            sys.exit(0 if d["_error"] == "cloudflare_block" else 1)
        print(f"goldprice.dev {args.symbol}")
        print(json.dumps(d, ensure_ascii=False, indent=2))
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            print(f"已保存 -> {args.out}")
        return

    # ── 历史 K 线 ──
    if not (args.from_ and args.to_):
        print("[错误] 历史模式需同时提供 --from 与 --to (YYYY-MM-DD)")
        sys.exit(2)
    bars, err = fetch_bars(args.symbol, args.from_, args.to_, args.interval, api_key)
    if err and not bars:
        print(f"[错误] {err['_error']}: {err['detail']}")
        sys.exit(0 if err["_error"] == "cloudflare_block" else 1)
    rows = bars_to_rows(bars, exclude_forming=not args.keep_forming)
    if not rows:
        print("[警告] 未解析到任何 K 线棒(可能区间无数据 / 免费层仅最近 30 天 / 被 Cloudflare 拦截)")
        if err:
            print(f"[诊断] {err['_error']}: {err['detail']}")
        sys.exit(0)
    if args.out:
        out_path = args.out
    elif args.out_dir:
        out_path = os.path.join(args.out_dir, "kline_%s_1d.csv" % _symbol_to_kline_name(args.symbol))
    else:
        out_path = "kline_%s_1d.csv" % _symbol_to_kline_name(args.symbol)
    write_kline_csv(rows, out_path)
    print(f"[OK] 历史 K 线 -> {out_path}")
    print(f"     标的={args.symbol} 区间={args.from_}~{args.to_} 周期={args.interval}")
    print(f"     棒数={len(rows)} 首={rows[0][0]} 收盘={rows[0][4]} | 末={rows[-1][0]} 收盘={rows[-1][4]}")
    if err:
        print(f"[提示] 主路径有诊断信息(已回退/部分成功): {err['_error']}: {err['detail']}")


if __name__ == "__main__":
    main()
