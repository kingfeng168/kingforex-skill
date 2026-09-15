#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
allratestoday_fetch.py — AllRatesToday 实时外汇中间价取数脚本 (kingforex-skill 内置)

用途: 为手动外汇/贵金属/大宗商品交易者拉取 **实时(约 60 秒刷新)银行间中间价**,
      直接服务"重点事件发布前后汇率反应"监控与盘中决策 —— 与 Frankfurter(ECB 每日参考汇率,
      仅工作日)形成 **实时 + 日参考** 双源互补。覆盖 160+ 法币(USD/EUR/GBP/JPY/AUD/CNY ...)。

数据源: AllRatesToday (allratestoday.com) —— 实时银行间 mid-market 汇率 API。
        - 认证: Bearer Token(免费档即 160+ 货币)。
        - 数据性质: **实时中间价,约每 60 秒刷新**(非 ECB 官方参考汇率,亦非逐笔 tick)。
        - 仅含法币,**不含 XAU 黄金 / XAG 白银**(贵金属请用 goldprice.dev / WGC-LBMA / qveris)。
        - 端点:
            GET /api/v1/rates?source=USD&target=EUR              最新一对
            GET /api/v1/rates?source=USD&target=EUR&time=YYYY-MM-DD  历史单日
            GET /api/historical-rates?source=USD&target=EUR&start_date=..&end_date=..  时间序列
        - 响应: 单对为数组 [{"rate","source","target","time"}];
                时间序列为对象 {"source","target","data":[{"date","rate","timestamp"}...]}。

Base URL : https://allratestoday.com/api
Key 配置 : 密钥存于 scripts/.art_key(单行纯文本,不进 zip、不进源码);
           读取优先级 --api-key > 环境变量 ART_KEY > scripts/.art_key。
           切勿明文外泄 Token,疑泄露即到 allratestoday.com 后台吊销换新。
依赖     : 仅 Python 标准库 (urllib / json / csv / argparse)。Python 3.8+。
错误处理 : 401=Key 无效; 429=限速; 4xx/5xx=服务端;均打印友好消息,不崩溃,绝不杜撰汇率。
"""

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://allratestoday.com/api"


def _read_key(args):
    if args.api_key:
        return args.api_key
    env = os.environ.get("ART_KEY", "").strip()
    if env:
        return env
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".art_key")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def _get_json(path, params, key, timeout=40):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"Authorization": "Bearer %s" % key,
                 "Accept": "application/json",
                 "User-Agent": "kingforex-skill/allratestoday_fetch"},
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
        if e.code == 401:
            return None, "401 Key 无效:请到 allratestoday.com 后台核对 Token,并更新 scripts/.art_key 或环境变量 ART_KEY。"
        if e.code == 429:
            return None, "429 限速:请稍后重试。"
        return None, "%d 服务端错误(%s)" % (e.code, body[:160])
    except urllib.error.URLError as e:
        return None, "网络不可达: %s。" % e.reason
    except Exception as e:  # noqa
        return None, "调用异常: %r" % (e,)


def _parse_targets(arg):
    syms = [s.strip().upper() for s in arg.split(",") if s.strip()]
    bad = [s for s in syms if s in ("XAU", "XAG", "GOLD", "SILVER")]
    if bad:
        print("[提示] AllRatesToday 仅含法币,不含 %s(贵金属请用 goldprice.dev / WGC-LBMA / qveris)。"
              % "/".join(bad), file=sys.stderr)
    return syms


def _emit_pair(rows, source, as_json, out):
    """rows: list of {target, rate, time}"""
    if as_json:
        print(json.dumps([{"source": source, "target": r["target"],
                            "rate": r["rate"], "time": r["time"]} for r in rows],
                          ensure_ascii=False, indent=2))
    else:
        print("[源: AllRatesToday | 实时银行间中间价 | source=%s]" % source)
        for r in rows:
            print("  %s->%-4s %.6f  (%s)" % (source, r["target"], r["rate"], r["time"]))
    if out:
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["source", "target", "rate", "time"])
            for r in rows:
                w.writerow([source, r["target"], "%.6f" % r["rate"], r["time"]])
        print("\n[已落盘] %s" % out, file=sys.stderr)


def _emit_series(d, as_json, out):
    src = d.get("source")
    tgt = d.get("target")
    data = d.get("data", [])
    if as_json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print("[源: AllRatesToday | 历史时间序列 | %s->%s | %d 个交易日 | %s]"
              % (src, tgt, len(data), d.get("source_api", "")))
        for row in data:
            print("  %s  %.6f" % (row.get("date"), row.get("rate")))
    if out:
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "source", "target", "rate"])
            for row in data:
                w.writerow([row.get("date"), src, tgt, "%.6f" % row.get("rate")])
        print("\n[已落盘] %s" % out, file=sys.stderr)


def fetch_latest(source, targets, key, as_json, out):
    rows = []
    for t in targets:
        params = {"source": source, "target": t}
        d, err = _get_json("/v1/rates", params, key)
        if err:
            print("[错误] %s->%s: %s" % (source, t, err), file=sys.stderr)
            sys.exit(1)
        if isinstance(d, list) and d:
            o = d[0]
            rows.append({"target": o.get("target", t), "rate": o.get("rate"), "time": o.get("time")})
        else:
            print("[错误] %s->%s: 响应为空 %s" % (source, t, d), file=sys.stderr)
            sys.exit(1)
    _emit_pair(rows, source, as_json, out)


def fetch_history_day(source, targets, date, key, as_json, out):
    rows = []
    for t in targets:
        params = {"source": source, "target": t, "time": date}
        d, err = _get_json("/v1/rates", params, key)
        if err:
            print("[错误] %s->%s @%s: %s" % (source, t, date, err), file=sys.stderr)
            sys.exit(1)
        if isinstance(d, list) and d:
            o = d[0]
            rows.append({"target": o.get("target", t), "rate": o.get("rate"), "time": o.get("time")})
        else:
            print("[错误] %s->%s @%s: 响应为空" % (source, t, date), file=sys.stderr)
            sys.exit(1)
    _emit_pair(rows, source, as_json, out)


def fetch_series(source, target, start, end, key, as_json, out):
    params = {"source": source, "target": target, "start_date": start, "end_date": end}
    d, err = _get_json("/historical-rates", params, key)
    if err:
        print("[错误] %s->%s %s..%s: %s" % (source, target, start, end, err), file=sys.stderr)
        sys.exit(1)
    _emit_series(d, as_json, out)


def main():
    ap = argparse.ArgumentParser(
        description="AllRatesToday 实时外汇中间价取数 (约 60 秒刷新, 需 Bearer Token)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--source", default="USD", help="基准货币(默认 USD)")
    ap.add_argument("--target", required=True,
                    help="目标货币,逗号分隔可一次取多对(如 EUR,JPY,AUD,CNY)")
    ap.add_argument("--time", help="历史单日 YYYY-MM-DD(与 --target 配合)")
    ap.add_argument("--history", action="store_true", help="取时间序列(需 --start/--end)")
    ap.add_argument("--start", help="时间序列起始 YYYY-MM-DD")
    ap.add_argument("--end", help="时间序列结束 YYYY-MM-DD")
    ap.add_argument("--api-key", help="AllRatesToday Token(优先级最高);否则 ART_KEY / scripts/.art_key")
    ap.add_argument("--out", help="结果落盘路径(.csv / .json 按扩展名)")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON(原始响应)")
    args = ap.parse_args()

    key = _read_key(args)
    if not key:
        print("[错误] 未找到 AllRatesToday Key:请设置 --api-key / 环境变量 ART_KEY / 或写入 scripts/.art_key",
              file=sys.stderr)
        sys.exit(2)

    targets = _parse_targets(args.target)
    if args.history:
        if not (args.start and args.end):
            print("[错误] --history 需同时指定 --start 与 --end。", file=sys.stderr)
            sys.exit(2)
        if len(targets) != 1:
            print("[错误] 时间序列模式仅支持单一 --target。", file=sys.stderr)
            sys.exit(2)
        fetch_series(args.source, targets[0], args.start, args.end, key, args.json, args.out)
    elif args.time:
        fetch_history_day(args.source, targets, args.time, key, args.json, args.out)
    else:
        fetch_latest(args.source, targets, key, args.json, args.out)


if __name__ == "__main__":
    main()
