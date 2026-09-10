#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIS SDMX v2 Stats API 拉取脚本（仅依赖 Python 标准库，无需 pip 安装）。

用法示例:
  python bis_fetch.py --list
  python bis_fetch.py --dims WS_XRU
  python bis_fetch.py --dataflow WS_CBPOL --key "M.US.*" --last 12 --out "D:/workbuddy/输出文件/bis_us_policy.csv"
  python bis_fetch.py --preset policy_rates --last 24 --out "D:/workbuddy/输出文件/bis_policy.csv"

注: JSON 返回为 SDMX 编码压缩格式（需解码），日常优先用 CSV。
"""
import urllib.request
import urllib.parse
import urllib.error
import sys
import os
import json
import argparse

BASE = "https://stats.bis.org/api/v2"
HEADERS = {
    "csv": "application/vnd.sdmx.data+csv;version=1.0.0",
    "json": "application/vnd.sdmx.data+json;version=1.0.0",
    "xml": "application/vnd.sdmx.structure+xml;version=2.1",
}

PRESETS = {
    "policy_rates": ("WS_CBPOL", "*"),
    "usd_rates": ("WS_XRU", "*"),
    "eer": ("WS_EER", "*"),
    "global_liq": ("WS_GLI", "*"),
}


def _get(path, accept, params=None, timeout=60):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"Accept": accept} if accept else {}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return f"HTTPError {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}"
    except Exception as e:  # noqa
        return f"Error: {e}"


def list_dataflows():
    # 注意: 结构类查询省略 Accept 头时服务器默认返回 JSON；
    # 不能用 data JSON 头（会 406）。
    raw = _get("/structure/dataflow/BIS/*/*", None)
    try:
        d = json.loads(raw)
        rows = [(x["id"], x.get("name", "")) for x in d["data"]["dataflows"]]
        print(f"{'DATAFLOW_ID':20s} NAME")
        for i, n in rows:
            print(f"{i:20s} {n}")
        return rows
    except Exception:
        print(raw[:1000])
        return []


def _structure_id_of(dataflow):
    """从 dataflow 清单解析真实 datastructure ID（映射非规律，必须查）。"""
    raw = _get("/structure/dataflow/BIS/*/*", None)
    try:
        d = json.loads(raw)
        for x in d["data"]["dataflows"]:
            if x["id"] == dataflow:
                urn = x.get("structure", "")
                return urn.split(":")[-1].split("(")[0]
    except Exception:
        pass
    return None


def show_dims(dataflow):
    struct = _structure_id_of(dataflow)
    if not struct:
        print(f"未找到数据集 {dataflow} 的结构映射")
        return
    raw = _get(f"/structure/datastructure/BIS/{struct}/1.0", HEADERS["xml"])
    if raw.startswith("Error") or raw.startswith("HTTPError"):
        print(raw)
        return
    import re
    dims = re.findall(r'<str:(?:Dimension|TimeDimension)[^>]*?\bid="([A-Z_]+)"\s+position="(\d+)"', raw)
    try:
        dims = sorted(set(dims), key=lambda x: int(x[1]))
    except Exception:
        pass
    print(f"Dataflow {dataflow} -> structure {struct}")
    print("维度顺序 (key 用 '.' 连接):")
    print(" . ".join(d[0] for d in dims) if dims else "(未能解析，请查看原始 XML)")
    if not dims:
        print(raw[:800])


def get_data(dataflow, key="*", fmt="csv", out=None, last=None, freq=None, area=None, timeout=60):
    path = f"/data/dataflow/BIS/{dataflow}/1.0/{key}"
    params = {}
    if last:
        params["lastNObservations"] = last
    if freq:
        params["c[FREQ]"] = freq
    if area:
        params["c[REF_AREA]"] = area
    text = _get(path, HEADERS.get(fmt, HEADERS["csv"]), params, timeout)
    if text.startswith("Error") or text.startswith("HTTPError"):
        print(text)
        return None
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已保存 {len(text)} 字符 -> {out}")
    else:
        print(text)
    return text


def main():
    p = argparse.ArgumentParser(description="BIS SDMX v2 Stats API fetcher")
    p.add_argument("--list", action="store_true", help="列出全部数据集")
    p.add_argument("--dims", metavar="DATAFLOW", help="查询某数据集维度顺序")
    p.add_argument("--dataflow", help="数据集 ID，如 WS_CBPOL")
    p.add_argument("--key", default="*", help="维度取值，如 M.US.*")
    p.add_argument("--preset", choices=list(PRESETS.keys()), help="快捷预设")
    p.add_argument("--fmt", default="csv", choices=["csv", "json", "xml"])
    p.add_argument("--out", help="输出文件路径")
    p.add_argument("--last", type=int, help="只取最近 N 期")
    p.add_argument("--freq", help="组件过滤 c[FREQ]")
    p.add_argument("--area", help="组件过滤 c[REF_AREA]")
    p.add_argument("--timeout", type=int, default=60)
    args = p.parse_args()

    if args.list:
        list_dataflows()
    elif args.dims:
        show_dims(args.dims)
    elif args.preset:
        df, key = PRESETS[args.preset]
        get_data(df, key, args.fmt, args.out, args.last, args.freq, args.area, args.timeout)
    elif args.dataflow:
        get_data(args.dataflow, args.key, args.fmt, args.out, args.last, args.freq, args.area, args.timeout)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
