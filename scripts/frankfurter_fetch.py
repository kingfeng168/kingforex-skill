#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
frankfurter_fetch.py — Frankfurter 免费外汇参考汇率取数脚本 (kingforex-skill 内置)

用途: 为手动外汇/贵金属/大宗商品交易者拉取 **法币交叉汇率**(EUR/GBP/JPY/AUD/CNY 等),
      作为 live_market_fetch 中 Frankfurter 预设(ECB 官方日参考汇率)的 **独立、可脚本化** 入口,
      便于批量取数、历史回溯、时间序列分析,直接喂入跨市场 / 利率平价 / 套息研判。

数据源: Frankfurter (frankfurter.dev) —— 由欧洲央行(ECB)官方每日参考汇率驱动的开源公共 API。
        - 无认证、无 key、无明确请求上限(仅基础防滥用)。
        - 数据性质: **ECB 每日参考汇率**,仅工作日更新(非实时 tick)。
        - 仅含法币,**不含 XAU 黄金 / XAG 白银**(贵金属请用 goldprice.dev / WGC-LBMA / qveris)。
        - 端点:
            GET /v1/latest?base=USD&symbols=EUR,GBP,JPY       最近一个工作日
            GET /v1/2026-01-02?base=USD&symbols=EUR,GBP       指定单日
            GET /v1/2025-12-29..2026-01-05?base=USD&symbols=.. 时间序列区间
            GET /v1/currencies                               货币代码 -> 名称
        - 历史回溯区间: ECB 参考汇率自 1999-01-04 起(含欧元诞生前按固定折算率的合成序列)。

Base URL : https://api.frankfurter.dev/v1   (注意: 旧 .app 域名已 301 重定向失效,须统一用 .dev)
依赖     : 仅 Python 标准库 (urllib / json / csv / argparse)。Python 3.8+。
错误处理 : 401/403 极少见(无 key); 404=该日期为周末/节假日无 ECB 数据; 429=限速; 5xx=服务端。
          均打印友好消息,不崩溃;取数失败仅报告原因并退出(绝不杜撰汇率)。
"""

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.frankfurter.dev/v1"

# FX 交易者常用法币预设(未指定 --symbols 时的默认取数集合)
DEFAULT_SYMBOLS = ["EUR", "GBP", "JPY", "AUD", "CNY", "CHF", "CAD", "NZD"]


def _get_json(path, params=None, timeout=40):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "kingforex-skill/frankfurter_fetch",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "ignore")
        except Exception:
            pass
        if e.code == 404:
            return None, "404 该日期无 ECB 参考汇率(周末/节假日),请换工作日或缩短区间(%s)" % body[:120]
        if e.code in (401, 403):
            return None, "%d 鉴权被拒(本接口本应无需 key,可能被限流或地址变更)" % e.code
        if e.code == 429:
            return None, "429 限速:请稍后重试。"
        return None, "%d 服务端错误(%s)" % (e.code, body[:120])
    except urllib.error.URLError as e:
        return None, "网络不可达: %s。" % e.reason
    except Exception as e:  # noqa
        return None, "调用异常: %r" % (e,)


def _parse_symbols(arg):
    if not arg:
        return list(DEFAULT_SYMBOLS)
    syms = [s.strip().upper() for s in arg.split(",") if s.strip()]
    bad = [s for s in syms if s in ("XAU", "XAG", "GOLD", "SILVER")]
    if bad:
        print("[提示] Frankfurter 仅含法币,不含 %s(贵金属请用 goldprice.dev / WGC-LBMA / qveris)。"
              % "/".join(bad), file=sys.stderr)
    return syms


def fetch_latest(base, symbols, amount, out, as_json):
    params = {"base": base, "symbols": ",".join(symbols), "amount": amount}
    d, err = _get_json("/latest", params)
    if err:
        print("[错误] %s" % err, file=sys.stderr)
        sys.exit(1)
    _emit(d, symbols, out, as_json, mode="single")


def fetch_date(date, base, symbols, amount, out, as_json):
    params = {"base": base, "symbols": ",".join(symbols), "amount": amount}
    d, err = _get_json("/" + date, params)
    if err:
        print("[错误] %s" % err, file=sys.stderr)
        sys.exit(1)
    _emit(d, symbols, out, as_json, mode="single")


def fetch_timeseries(start, end, base, symbols, amount, out, as_json):
    params = {"base": base, "symbols": ",".join(symbols), "amount": amount}
    d, err = _get_json("/" + start + ".." + end, params)
    if err:
        print("[错误] %s" % err, file=sys.stderr)
        sys.exit(1)
    _emit(d, symbols, out, as_json, mode="series")


def fetch_currencies(out, as_json):
    d, err = _get_json("/currencies")
    if err:
        print("[错误] %s" % err, file=sys.stderr)
        sys.exit(1)
    if as_json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print("[源: Frankfurter | 货币列表, 共 %d 种]" % len(d))
        for code in sorted(d.keys()):
            print("  %-4s %s" % (code, d[code]))
    if out:
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["code", "name"])
            for code in sorted(d.keys()):
                w.writerow([code, d[code]])
        print("\n[已落盘] %s" % out, file=sys.stderr)


def _emit(d, symbols, out, as_json, mode):
    if as_json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    elif mode == "single":
        date = d.get("date")
        base = d.get("base")
        rates = d.get("rates", {})
        print("[源: Frankfurter | ECB 每日参考汇率 | 截至 %s | base=%s | amount=%s]"
              % (date, base, d.get("amount")))
        for s in symbols:
            v = rates.get(s)
            print("  %-4s %.4f" % (s, v) if v is not None else "  %-4s (无数据)" % s)
    else:
        start = d.get("start_date")
        end = d.get("end_date")
        rates = d.get("rates", {})
        print("[源: Frankfurter | ECB 参考汇率时间序列 | %s .. %s | base=%s | %d 个交易日]"
              % (start, end, d.get("base"), len(rates)))
        ds = sorted(rates.keys())
        if ds:
            print("  首 %s: %s" % (ds[0], _fmt(rates[ds[0]], symbols)))
            print("  尾 %s: %s" % (ds[-1], _fmt(rates[ds[-1]], symbols)))
    if out:
        _write_csv(d, symbols, out, mode)


def _fmt(rate_map, symbols):
    return "  ".join("%s=%.4f" % (s, rate_map[s]) for s in symbols if s in rate_map)


def _write_csv(d, symbols, out, mode):
    if mode == "single":
        rows = [(d.get("date"), d.get("base"), d.get("rates", {}))]
    else:
        rates = d.get("rates", {})
        rows = [(dt, d.get("base"), rates[dt]) for dt in sorted(rates.keys())]
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "base"] + symbols)
        for dt, base, rm in rows:
            w.writerow([dt, base] + [("" if s not in rm else "%.6f" % rm[s]) for s in symbols])
    print("\n[已落盘] %s" % out, file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(
        description="Frankfurter 免费外汇参考汇率取数 (ECB 每日参考汇率, 无需 key)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--base", default="USD", help="基准货币(默认 USD)")
    ap.add_argument("--symbols",
                    help="目标货币,逗号分隔(默认 FX 常用 8 币种: EUR,GBP,JPY,AUD,CNY,CHF,CAD,NZD)")
    ap.add_argument("--amount", type=float, default=1.0, help="换算金额(默认 1.0)")
    ap.add_argument("--date", help="指定单日 YYYY-MM-DD(历史单日)")
    ap.add_argument("--from", dest="start", help="时间序列起始 YYYY-MM-DD")
    ap.add_argument("--to", dest="end", help="时间序列结束 YYYY-MM-DD")
    ap.add_argument("--currencies", action="store_true", help="列出全部支持货币代码")
    ap.add_argument("--out", help="结果落盘路径(.csv / .json 按扩展名)")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON(原始响应)")
    args = ap.parse_args()

    if args.currencies:
        fetch_currencies(args.out, args.json)
        return
    symbols = _parse_symbols(args.symbols)
    if args.start and args.end:
        fetch_timeseries(args.start, args.end, args.base, symbols, args.amount, args.out, args.json)
    elif args.date:
        fetch_date(args.date, args.base, symbols, args.amount, args.out, args.json)
    else:
        fetch_latest(args.base, symbols, args.amount, args.out, args.json)


if __name__ == "__main__":
    main()
