#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EIA v2 Stats API 拉取脚本（仅依赖 Python 标准库，无需 pip 安装）。

面向 kingforex-skill 原油模块：拉取 EIA 周度/日度原油与成品油供需数据。
EIA v2 API 需免费 key —— 注册 https://www.eia.gov/opendata/ 获取；
可用环境变量 EIA_API_KEY 传入、把 key 单行写入脚本同目录 .eia_key 文件，
或用 --api-key 显式传入(优先级: --api-key > 环境变量 > .eia_key)。

用法示例:
  # 美国商业原油库存最近 12 周（预设）
  python eia_fetch.py --preset crude_stocks --api-key YOURKEY --last 12 \
      --out "./output/eia_crude_stocks.csv"

  # 直接指定路由 + 系列(sndw 路由必须带 --freq weekly)
  python eia_fetch.py --route petroleum/sum/sndw --series WCRSTUS1 --freq weekly \
      --api-key YOURKEY --last 24 --out "./output/eia_crude.csv"

  # 发现某路由下全部可用 series（找对的 ID，sndw 需 --freq）
  python eia_fetch.py --route petroleum/sum/sndw --api-key YOURKEY --freq weekly --list-series

  # 列出内置预设
  python eia_fetch.py --routes
"""
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import json
import argparse

BASE = "https://api.eia.gov/v2"

# 原油模块常用预设：(路由, 系列ID, 频率, 中文说明)
# 注意: sndw(周度供需) 路由强制要求 frequency 参数; spt/data(现货价) 为日度。
# 系列过滤必须用 facets[series][]=XXX，直接用 series= 参数会返回 HTTP 400。
# 经实测校准(2026-08)，crude_stocks/gas_stocks(WGTSTUS1 总汽油)/dist_stocks 均为
# 千桶单位；WTI=RWTC、Brent=RBRTE。crude_prod 周度序列在 sndw 路由下无对应 ID，已移除。
PRESETS = {
    "crude_stocks": ("petroleum/sum/sndw", "WCRSTUS1", "weekly", "美国商业原油库存(千桶)"),
    "gas_stocks":   ("petroleum/sum/sndw", "WGTSTUS1", "weekly", "美国汽油总库存(千桶)"),
    "dist_stocks":  ("petroleum/sum/sndw", "WDISTUS1", "weekly", "美国馏分油库存(千桶)"),
    "wti":          ("petroleum/pri/spt/data", "RWTC", "daily", "WTI 库欣现货价(美元/桶)"),
    "brent":        ("petroleum/pri/spt/data", "RBRTE", "daily", "Brent 现货价(美元/桶)"),
}


def _read_local_key():
    """从脚本同目录的 .eia_key 文件读取 key(本地便利，不进 zip/不进脚本)。"""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".eia_key")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def _get(route, api_key, freq=None, series=None, length=None, timeout=60):
    """拉取 EIA v2 路由的 data 端点，返回解析后的 dict 列表。

    freq:   频率(weekly/daily 等)。sndw 路由强制需要，缺省会返回空。
    series: 若给出，用 facets[series][]=XXX 定点取单一系列，减少传输并避免 400。
    length: 若给出，按 period 倒序取最近 N 期(EIA 默认分页上限 5000，日度序列
            若不倒序会只取到最旧的一页，导致拿不到最新数据)。
    """
    url = f"{BASE}/{route}/data"
    params = {"api_key": api_key}
    if freq:
        params["frequency"] = freq
    if series:
        # 用 facet 定点取数，比拉全量再 Python 过滤更稳(series= 参数会 400)
        params["facets[series][]"] = series
    if length:
        # 倒序 + 限制长度，确保拿到的是“最近 N 期”而非最旧一页
        params["sort[0][column]"] = "period"
        params["sort[0][direction]"] = "DESC"
        params["length"] = length
    url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:400]
        return f"HTTPError {e.code}: {body}"
    except Exception as e:  # noqa
        return f"Error: {e}"
    try:
        d = json.loads(raw)
        resp = d.get("response", {})
        # 优先取扁平 data 列表; 若为空但存在嵌套 series[].data[] 则展开(兼容不同信封形态)
        data = resp.get("data", [])
        if not data and isinstance(resp.get("series"), list):
            for s in resp["series"]:
                for r in s.get("data", []):
                    row = dict(r)
                    row.setdefault("series", s.get("series_id"))
                    data.append(row)
        return data
    except Exception as e:  # noqa
        return f"JSONError: {e} | {raw[:300]}"


def _to_csv(rows, out):
    """把行字典列表写成 CSV（列取所有键的并集）。"""
    if not rows:
        return "无数据行"
    cols = []
    for row in rows:
        for k in row.keys():
            if k not in cols:
                cols.append(k)
    lines = [",".join(cols)]
    for row in rows:
        lines.append(",".join(_csv_cell(row.get(c, "")) for c in cols))
    text = "\n".join(lines)
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        return f"已保存 {len(rows)} 行 -> {out}"
    return text


def _csv_cell(v):
    if v is None:
        return ""
    s = str(v)
    if "," in s or '"' in s or "\n" in s:
        s = '"' + s.replace('"', '""') + '"'
    return s


def list_series(route, api_key, freq=None):
    rows = _get(route, api_key, freq)
    if isinstance(rows, str):
        print(rows)
        return
    seen = {}
    for r in rows:
        sid = r.get("series", "")
        desc = r.get("series-description", r.get("description", ""))
        if sid and sid not in seen:
            seen[sid] = desc
    print(f"路由 {route} 下可用 series (共 {len(seen)} 个):")
    for sid, desc in sorted(seen.items()):
        print(f"  {sid:12s} {desc}")


def fetch(route, series, api_key, last=None, freq=None, out=None):
    # length=last 时 _get 已按 period 倒序取最近 N 期; 这里再升序整理便于阅读
    rows = _get(route, api_key, freq, series, length=last)
    if isinstance(rows, str):
        print(rows)
        return None
    # facet 已定点过滤; 此处再做一次保险匹配(无 facet 直接 --route 时仍有效)
    if series:
        rows = [r for r in rows if str(r.get("series", "")).upper() == series.upper()]
    # 按 period 升序输出(倒序请求只是为了保证“最近 N 期”不被分页截断)
    rows.sort(key=lambda r: str(r.get("period", "")))
    msg = _to_csv(rows, out)
    print(msg)
    return rows


def main():
    p = argparse.ArgumentParser(description="EIA v2 Stats API fetcher (原油模块)")
    p.add_argument("--routes", action="store_true", help="列出内置预设")
    p.add_argument("--route", help="API 路由，如 petroleum/sum/sndw")
    p.add_argument("--series", help="系列 ID，如 WCRSTUS1（不填则取路由全部）")
    p.add_argument("--preset", choices=list(PRESETS.keys()), help="快捷预设")
    p.add_argument("--api-key", help="EIA API key（或设环境变量 EIA_API_KEY）")
    p.add_argument("--freq", help="频率过滤，如 weekly / daily")
    p.add_argument("--list-series", action="store_true", help="列出路由下全部 series")
    p.add_argument("--out", help="输出 CSV 路径")
    p.add_argument("--last", type=int, help="只取最近 N 期")
    p.add_argument("--timeout", type=int, default=60)
    args = p.parse_args()

    api_key = args.api_key or os.environ.get("EIA_API_KEY") or _read_local_key()

    if args.routes:
        print("内置预设:")
        for k, (rt, sid, fr, desc) in PRESETS.items():
            print(f"  {k:14s} {rt:24s} {sid:12s} {fr:7s} {desc}")
        return
    if args.list_series:
        if not args.route:
            print("需配合 --route 使用")
            return
        if not api_key:
            print("需要 --api-key 或环境变量 EIA_API_KEY")
            return
        # list_series 需要 frequency 才能返回数据(sndw 路由强制); 默认 weekly
        list_series(args.route, api_key, args.freq or "weekly")
        return
    if args.preset:
        rt, sid, fr, _ = PRESETS[args.preset]
        if not api_key:
            print("需要 --api-key 或环境变量 EIA_API_KEY（免费注册 https://www.eia.gov/opendata/）")
            return
        # 预设自带频率; 若用户显式 --freq 则覆盖
        fetch(rt, sid, api_key, args.last, args.freq or fr, args.out)
    elif args.route:
        if not api_key:
            print("需要 --api-key 或环境变量 EIA_API_KEY")
            return
        fetch(args.route, args.series, api_key, args.last, args.freq, args.out)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
