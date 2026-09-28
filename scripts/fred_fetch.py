#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fred_fetch.py — FRED(圣路易斯联储)权威宏观/利率数据取数脚本 (kingforex-skill 内置)

用途:为手动外汇/贵金属/大宗商品交易者拉取**模块一 宏观利率地基**所需的一手数据——
      10Y 名义利率(DGS10)、10Y 实际利率(TIPS, DFII10)、10Y 盈亏平衡通胀(T10YIE)、
      收益率曲线(2s10s 利差 T10Y2Y / 短端 DGS3MO·DGS1·DGS2·DGS5)、联邦基金利率(FEDFUNDS/DFF)等。
      FRED 是美元/利率方向研判的第一手权威源,比任何二手聚合更一手。

Base URL : https://api.stlouisfed.org/fred  (FRED API v1, 公开、需免费 key)
端点     : /fred/series/observations  (取观测值)
Key 来源 : 命令行 --api-key 优先;否则环境变量 FRED_API_KEY;否则脚本同目录 .fred_key。
Key 已配置: scripts/.fred_key(本地文件,不进 zip、不进源码)。

依赖: 仅 Python 标准库(urllib / json / csv / argparse)。Python 3.8+。

错误处理: 401=key 无效; 400/404=系列不存在或参数错; 429=限速; 5xx=服务端。
         均打印友好消息,不崩溃;FRED 缺失值以 "." 表示,自动跳过。
"""

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.stlouisfed.org/fred"

# 预设:技能"宏观利率地基"常用系列(ID 取自 references/data_sources.md §1)
PRESETS = {
    "nominal_10y":   ["DGS10"],                       # 10Y 名义利率
    "real_10y":      ["DFII10"],                      # 10Y TIPS 实际利率(黄金定价第一锚)
    "breakeven_10y": ["T10YIE"],                      # 10Y 盈亏平衡通胀
    "curve_2s10s":   ["T10Y2Y"],                      # 10Y-2Y 利差(衰退/曲线倒挂信号)
    "short_end":     ["DGS3MO", "DGS1", "DGS2", "DGS5"],  # 短端收益率
    "fed_funds":     ["FEDFUNDS", "DFF"],             # 联邦基金利率(政策利率锚)
    "all_rates":     ["DGS3MO", "DGS1", "DGS2", "DGS5", "DGS10", "DGS30",
                      "DFII10", "T10YIE", "T10Y2Y", "FEDFUNDS"],  # 全曲线 + 实际/通胀/政策
}


# ── Key 读取(优先级:--api-key > 环境变量 > 脚本同目录 .fred_key) ──────────────
def _read_key():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".fred_key")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def _resolve_key(args):
    if args.api_key:
        return args.api_key
    env = os.environ.get("FRED_API_KEY", "").strip()
    if env:
        return env
    return _read_key()


# ── 单系列拉取 ─────────────────────────────────────────────────────────────────
def fetch_series(series_id, api_key, limit=None, start=None, end=None, sort_order="desc"):
    """返回 (list_of_{date,value}, error_or_None)。value 为 float 或 None(缺失)。"""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": sort_order,
    }
    if limit:
        params["limit"] = limit
    if start:
        params["observation_start"] = start
    if end:
        params["observation_end"] = end
    url = BASE + "/series/observations?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "kingforex-skill/fred_fetch"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "ignore")
        except Exception:
            pass
        if e.code == 401:
            return None, "401 Key 无效:请到 api.stlouisfed.org 重新核对 Key,并更新 scripts/.fred_key 或环境变量 FRED_API_KEY。"
        if e.code in (400, 404):
            return None, f"{e.code} 系列 '{series_id}' 不存在或参数错误({body[:160]})。"
        if e.code == 429:
            return None, "429 限速:请稍后重试。"
        return None, f"{e.code} 服务端错误({body[:160]})。"
    except urllib.error.URLError as e:
        return None, f"网络不可达: {e.reason}。"
    except Exception as e:  # noqa
        return None, f"调用异常: {repr(e)[:160]}"

    obs = d.get("observations", [])
    out = []
    for o in obs:
        v = o.get("value", ".")
        val = None if v in (".", "", None) else _to_float(v)
        out.append({"date": o.get("date"), "value": val})
    return out, None


def _to_float(s):
    try:
        return float(s)
    except Exception:
        return None


# ── 主流程 ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="FRED 宏观/利率数据取数(模块一 宏观利率地基)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--preset", choices=list(PRESETS.keys()),
                    help="预设系列组: " + " | ".join(f"{k}={','.join(v)}" for k, v in PRESETS.items()))
    ap.add_argument("--series", help="自定义系列 ID(逗号分隔,如 DGS10,DFII10)")
    ap.add_argument("--last", type=int, help="取最近 N 个观测值(默认 30)")
    ap.add_argument("--start", help="观测起始日(YYYY-MM-DD)")
    ap.add_argument("--end", help="观测结束日(YYYY-MM-DD)")
    ap.add_argument("--api-key", help="FRED Key(优先级最高);否则 FRED_API_KEY / scripts/.fred_key")
    ap.add_argument("--out", help="结果落盘路径(.csv / .json 按扩展名)")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args()

    if not args.preset and not args.series:
        print("[错误] 请指定 --preset 或 --series。", file=sys.stderr)
        sys.exit(2)

    key = _resolve_key(args)
    if not key:
        print("[错误] 未找到 FRED Key:请设置 --api-key / 环境变量 FRED_API_KEY / 或写入 scripts/.fred_key",
              file=sys.stderr)
        sys.exit(2)

    series_ids = PRESETS[args.preset] if args.preset else [s.strip() for s in args.series.split(",") if s.strip()]
    limit = args.last if args.last else (30 if not (args.start or args.end) else None)

    # 逐个拉取
    data = {}
    latest = {}
    for sid in series_ids:
        rows, err = fetch_series(sid, key, limit=limit, start=args.start, end=args.end, sort_order="desc")
        if err:
            print(f"[错误] {sid}: {err}", file=sys.stderr)
            sys.exit(1)
        # 升序便于输出与计算变化
        rows_asc = list(reversed(rows))
        data[sid] = rows_asc
        # 最新有效值 + 较上一有效值变化
        valid = [r for r in rows if r["value"] is not None]
        if valid:
            cur = valid[0]
            prev = valid[1] if len(valid) > 1 else None
            latest[sid] = {
                "date": cur["date"],
                "value": cur["value"],
                "prev": prev["value"] if prev else None,
                "delta": (cur["value"] - prev["value"]) if prev else None,
            }

    # 汇总打印
    print(f"[源: FRED | 系列: {', '.join(series_ids)}]")
    for sid in series_ids:
        L = latest.get(sid)
        if not L:
            print(f"  {sid}: 无有效数据")
            continue
        d = f"{L['delta']:+.2f}" if L["delta"] is not None else "  n/a"
        print(f"  {sid}: {L['value']:.2f}  (截至 {L['date']}, 环比 {d})")

    # 输出文件
    if args.out:
        if args.out.lower().endswith(".json"):
            payload = {"meta": {"source": "FRED", "series": series_ids,
                                "observation_start": args.start, "observation_end": args.end},
                       "latest": latest, "observations": data}
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        else:
            # 宽表 CSV:date, sid1, sid2, ...
            # 以各系列升序观测,按 date 对齐(取并集,缺失留空)
            all_dates = []
            for sid in series_ids:
                for r in data[sid]:
                    if r["date"] not in all_dates:
                        all_dates.append(r["date"])
            all_dates.sort()
            idx = {sid: {r["date"]: r["value"] for r in data[sid]} for sid in series_ids}
            with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow(["date"] + series_ids)
                for dt in all_dates:
                    w.writerow([dt] + [("" if idx[sid].get(dt) is None else f"{idx[sid][dt]:.4f}") for sid in series_ids])
        print(f"\n[已落盘] {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
