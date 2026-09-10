#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMF SDMX 3.0 Stats API 拉取脚本（仅依赖 Python 标准库，无需 pip 安装）。

面向 kingforex-skill 宏观/外汇模块：拉取 IMF 权威宏观与储备数据。
基址默认 https://api.imf.org/external/sdmx/3.0（用户提供的 IMF SDMX 3.0 API），
可用 --base 覆盖（如切换到 https://sdmxcentral.imf.org/sdmx/v3 等镜像/备用节点）。

⚠️ 透明说明:本脚本编写时,构建环境对 api.imf.org 的 SDMX 3.0 端点返回 502/404
（同一环境对 BIS SDMX 端点返回 200,可判定为 IMF 服务端临时不可达或路径调整）。
脚本严格按 SDMX 3.0 REST 标准与用户提供的基址编写,请在本地用 `python imf_fetch.py --list`
确认连通性与实际 dataflow 列表后再正式取数;若 IMF 调整路径,用 --base 指向可用节点。

用法示例:
  # 列出全部 dataflow(确认连通性 + 找数据集 ID)
  python imf_fetch.py --list

  # 查某数据集维度顺序(写 key 前必做)
  python imf_fetch.py --structure COFER

  # 拉 COFER 世界美元储备份额相关序列(示例 key,需以 --structure 确认为准)
  python imf_fetch.py --flow COFER --key "W00.AEZF.USD" --format csv --start 2020 \
      --out "D:/workbuddy/输出文件/imf_cofer_usd.csv"

  # 预设快捷:cofer / ifs / bop / dot
  python imf_fetch.py --preset cofer --format csv --out "D:/workbuddy/输出文件/imf_cofer.csv"
"""
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import json
import argparse

BASE = "https://api.imf.org/external/sdmx/3.0"

# 交易者最关心的 IMF 数据集(预设)。key 仅为示例,必须经 --structure 确认维度顺序。
PRESETS = {
    "cofer": ("COFER", "W00.AEZF.USD",
              "官方外汇储备币种构成:全球(World)已配置储备中美元项,用于算美元储备份额"),
    "ifs":   ("IFS", "USA.PRX_REER_LOP",
              "国际金融统计:实际有效汇率(REER)等宏观序列"),
    "bop":   ("BOP", "W00.BABL_CDA",
              "国际收支:经常账户差额等"),
    "dot":   ("DOT", "W00.US.TXG_FOB",
              "贸易方向:全球从美国的进口等双边贸易流"),
}


def _get(path, params=None, timeout=60, base=BASE):
    url = base.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return f"HTTPError {e.code}: {e.read().decode('utf-8', 'ignore')[:400]}"
    except Exception as e:  # noqa
        return f"Error: {e}"


def list_dataflows(base=BASE):
    raw = _get("/dataflow/IMF", base=base)
    if raw.startswith(("Error", "HTTPError")):
        print(raw)
        return
    try:
        d = json.loads(raw)
        flows = d.get("data", {}).get("dataflows") or d.get("dataflows") or []
        print(f"{'DATAFLOW_ID':16s} NAME")
        for x in flows:
            print(f"{str(x.get('id','')):16s} {x.get('name','')}")
    except Exception:
        print("无法解析 JSON,原始返回前 1200 字符:")
        print(raw[:1200])


def show_structure(flow, base=BASE):
    raw = _get(f"/datastructure/IMF/{flow}", base=base)
    if raw.startswith(("Error", "HTTPError")):
        print(raw)
        return
    try:
        d = json.loads(raw)
        # 尝试从 SDMX-JSON 结构消息提取维度
        dims = []
        def walk(o):
            if isinstance(o, dict):
                if "id" in o and ("position" in o or o.get("role") == "dimension"):
                    dims.append((o.get("id"), o.get("position")))
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(d)
        if dims:
            dims = sorted(set(dims), key=lambda x: (x[1] is None, x[1]))
            print(f"Dataflow {flow} 维度顺序 (key 用 '.' 连接):")
            print(" . ".join(x[0] for x in dims if x[0]))
        else:
            print("未能自动解析维度,原始返回前 1000 字符:")
            print(raw[:1000])
    except Exception:
        print("无法解析 JSON,原始返回前 1000 字符:")
        print(raw[:1000])


def get_data(flow, key="*", fmt="csv", start=None, end=None, out=None, base=BASE, timeout=60):
    params = {"format": fmt}
    if start:
        params["startPeriod"] = start
    if end:
        params["endPeriod"] = end
    text = _get(f"/Data/{flow}/{key}", params, timeout, base)
    if text.startswith(("Error", "HTTPError")):
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
    p = argparse.ArgumentParser(description="IMF SDMX 3.0 Stats API fetcher (宏观/外汇)")
    p.add_argument("--base", default=BASE, help="API 基址(默认 IMF SDMX 3.0)")
    p.add_argument("--list", action="store_true", help="列出全部 dataflow")
    p.add_argument("--structure", metavar="FLOW", help="查询某数据集维度顺序")
    p.add_argument("--flow", help="数据集 ID,如 COFER / IFS / BOP / DOT")
    p.add_argument("--key", default="*", help="维度取值键,如 W00.AEZF.USD")
    p.add_argument("--preset", choices=list(PRESETS.keys()), help="快捷预设")
    p.add_argument("--format", default="csv", choices=["csv", "json"])
    p.add_argument("--start", help="起始期,如 2020 或 2020-Q1")
    p.add_argument("--end", help="结束期")
    p.add_argument("--out", help="输出文件路径")
    p.add_argument("--timeout", type=int, default=60)
    args = p.parse_args()

    if args.list:
        list_dataflows(args.base)
    elif args.structure:
        show_structure(args.structure, args.base)
    elif args.preset:
        flow, key, desc = PRESETS[args.preset]
        print(f"预设 {args.preset}: flow={flow} 示例key={key}")
        print(f"说明: {desc}")
        print("注意:示例 key 须经 `python imf_fetch.py --structure {flow}` 确认维度顺序后再用。")
        get_data(flow, key, args.format, args.start, args.end, args.out, args.base, args.timeout)
    elif args.flow:
        get_data(args.flow, args.key, args.format, args.start, args.end, args.out, args.base, args.timeout)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
