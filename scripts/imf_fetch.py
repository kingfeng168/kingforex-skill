#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMF SDMX 3.0 Stats API 拉取脚本（仅依赖 Python 标准库，无需 pip 安装）。

面向 kingforex-skill 宏观/外汇模块。

═══════════════════════════════════════════════════════════════════════════
⚠️ 实测状态（2026-09-28，本机大陆网络）—— 请先读完再决定是否依赖本脚本
═══════════════════════════════════════════════════════════════════════════
1) 端点路径已按 IMF 官方 OpenAPI 校正（旧路径实测全部 404）：
     结构清单  GET /structure/dataflow/all/*/+                             → 200（222 个 dataflow）
     数据查询  GET /data/dataflow/{agency}/{flow}/{version}/{key}?format=jsondata
   旧路径 `/dataflow/IMF`、`/datastructure/IMF/{flow}`、`/Data/{flow}/{key}` 均已废弃。
   agency 与 version 不再手写，由 `resolve_flow()` 从结构清单实时解析（IMF 升版后无需改码）。

2) **本环境 IMF 取不到观测值**：对上述数据端点，无论用 `all`、完整维度键、
   `dimensionAtObservation=AllDimensions`、SDMX-JSON Accept 头还是 startPeriod/endPeriod，
   一律返回「结构信封 + observations = 0」（实测 COFER / BOP / CPI / IRFCL / WEO 全部如此）。
   因此本脚本检测到 0 观测会**报错退出（exit 3）**，绝不把空信封当数据落盘。

3) 旧预设 `IFS` / `DOT` 已移除：实测 IMF 全部 222 个 dataflow 中**不存在**这两个 id
   （历史遗留写法）。现存可用 id 示例：COFER / BOP / CPI / IRFCL / WEO。

4) 需要"美元储备份额 / 国际收支 / 各国宏观"时，请优先用本技能中**实测可取数**的替代源：
     - `worldbank_fetch.py`（World Bank Open Data，免 key，实测 200）
     - `bis_fetch.py`（BIS SDMX v2，免 key，实测 200：政策利率/有效汇率/全球流动性）
     - `fred_fetch.py`（FRED，需自备 key，官方一手利率与曲线）
   若后续 IMF 恢复供数，本脚本无需改动即可自动可用（0 观测检查会放行）。

用法示例:
  # 列出全部 dataflow(确认连通性 + 找数据集 ID)  ← 该端点实测可用
  python imf_fetch.py --list

  # 查某数据集维度顺序(用于写 --key)
  python imf_fetch.py --structure COFER

  # 预设快捷: cofer / bop / cpi / irfcl / weo
  python imf_fetch.py --preset cofer --out "./output/imf_cofer.json"
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

for _stream in (sys.stdout, sys.stderr):     # 中文 Windows(cp936)下输出符号不再中断
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

BASE = "https://api.imf.org/external/sdmx/3.0"

# 交易者最关心的 IMF 数据集(预设)。agency/version 由结构清单实时解析, 此处仅存回退值。
# key 默认 all(全维度); 需要用具体维度键时先用 `--structure <FLOW>` 确认维度顺序。
PRESETS = {
    "cofer": ("IMF.STA", "COFER", "7.0.1",
              "官方外汇储备币种构成:全球(World)已配置储备中美元项,用于算美元储备份额"),
    "bop":   ("IMF.STA", "BOP", "21.0.0",
              "国际收支:经常账户差额等"),
    "cpi":   ("IMF.STA", "CPI", "5.0.0",
              "消费者价格指数(各国 CPI, 用于实际利率与通胀差)"),
    "irfcl": ("IMF.STA", "IRFCL", "12.0.0",
              "国际储备与外币流动性(外储充足度)"),
    "weo":   ("IMF.RES", "WEO", "9.0.0",
              "世界经济展望宏观预测(GDP/通胀/经常账户)"),
}

STRUCTURE_PATH = "/structure/dataflow/all/*/+"
DATA_PATH = "/data/dataflow/{agency}/{flow}/{version}/{key}"


def _get(path, params=None, timeout=60, base=BASE):
    """返回 (status, text)；status 为 HTTP 码或 'ERR'。"""
    url = base.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "kingforex-skill/2.8.2"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:400]
    except Exception as e:  # noqa
        return "ERR", str(e)


def list_dataflows(base=BASE, timeout=60):
    st, raw = _get(STRUCTURE_PATH, base=base, timeout=timeout)
    if st != 200:
        print("结构清单取数失败: HTTP %s %s" % (st, raw[:300]))
        return []
    try:
        flows = json.loads(raw)["data"]["dataflows"]
    except Exception as e:
        print("无法解析结构清单 JSON: %s" % e)
        return []
    print("%-12s %-10s %-9s %s" % ("FLOW_ID", "AGENCY", "VERSION", "NAME"))
    for x in flows:
        names = x.get("names") or {}
        nm = names.get("en", "") if isinstance(names, dict) else ""
        print("%-12s %-10s %-9s %s" % (x.get("id", ""), x.get("agencyID", ""),
                                       x.get("version", ""), nm[:70]))
    print("\n共 %d 个 dataflow。" % len(flows))
    return flows


def resolve_flow(flow_id, base=BASE, timeout=60):
    """从结构清单实时解析 (agency, version, name);解析失败返回 (None, None, None)。"""
    st, raw = _get(STRUCTURE_PATH, base=base, timeout=timeout)
    if st != 200:
        return None, None, None
    try:
        for x in json.loads(raw)["data"]["dataflows"]:
            if str(x.get("id", "")).upper() == flow_id.upper():
                names = x.get("names") or {}
                return (x.get("agencyID"), x.get("version"),
                        names.get("en", "") if isinstance(names, dict) else "")
    except Exception:
        pass
    return None, None, None


def show_structure(flow, agency=None, version=None, base=BASE, timeout=60):
    """打印某 dataflow 的维度顺序(取一页数据信封里的 structures.dimensions)。"""
    if not agency:
        agency, version, _ = resolve_flow(flow, base, timeout)
        agency = agency or "IMF.STA"
        version = version or "1.0"
    st, raw = _get(DATA_PATH.format(agency=agency, flow=flow, version=version, key="all"),
                   {"format": "jsondata", "dimensionAtObservation": "AllDimensions"},
                   timeout, base)
    if st != 200:
        print("取结构失败: HTTP %s %s" % (st, raw[:300]))
        return
    try:
        dims = json.loads(raw)["data"]["structures"][0]["dimensions"]
    except Exception as e:
        print("无法解析维度信息: %s" % e)
        return
    print("Dataflow %s (%s %s) 维度顺序(key 用 '.' 连接, 未知位用空或 '*'):" % (flow, agency, version))
    order = []
    for grp in ("series", "observation"):
        for d in dims.get(grp, []):
            order.append(d.get("id"))
            print("  [%s] %-24s id=%-24s 可选值 %d 个" % (
                grp, d.get("name", "")[:24], d.get("id"), len(d.get("values", []))))
    print("\nkey = " + ".".join(str(x) for x in order))


def count_observations(payload):
    try:
        d = json.loads(payload)
        out = 0
        for ds in d.get("data", {}).get("dataSets", []) or []:
            out += len(ds.get("observations") or {})
        return out
    except Exception:
        return -1


def flatten_to_csv(payload):
    """把 SDMX-JSON 观测值摊平成 CSV(有观测值时)。返回 (csv_text, 行数)。"""
    import csv
    import io
    d = json.loads(payload)["data"]
    st = d["structures"][0]
    dims = st.get("dimensions", {})
    series_dims = dims.get("series", [])
    obs_dims = dims.get("observation", [])
    rows = []
    for ds in d.get("dataSets", []) or []:
        for skey, sval in (ds.get("series") or {}).items():
            sidx = [int(i) for i in skey.split(":")]
            head = [series_dims[i]["values"][sidx[i]].get("id") for i in range(len(sidx))]
            for okey, oval in (sval.get("observations") or {}).items():
                oidx = [int(i) for i in okey.split(":")]
                odims = [obs_dims[i]["values"][oidx[i]].get("id") for i in range(len(oidx))]
                rows.append(head + odims + list(oval))
        for okey, oval in (ds.get("observations") or {}).items():
            oidx = [int(i) for i in okey.split(":")]
            odims = [obs_dims[i]["values"][oidx[i]].get("id") for i in range(len(oidx))]
            rows.append(odims + list(oval))
    buf = io.StringIO()
    if rows:
        w = csv.writer(buf)
        w.writerow([x["id"] for x in series_dims] + [x["id"] for x in obs_dims] + ["VALUE"])
        w.writerows(rows)
    return buf.getvalue(), len(rows)


def get_data(flow, key="all", fmt="json", start=None, end=None, out=None,
             base=BASE, timeout=60, agency=None, version=None, allow_empty=False):
    if not agency or not version:
        a2, v2, _ = resolve_flow(flow, base, timeout)
        agency = agency or a2
        version = version or v2
    if not agency or not version:
        print("[错误] 无法解析 %s 的 agency/version(结构清单不可达或该 flow 不存在)。" % flow)
        print("       请先运行 `--list` 查看可用 dataflow。")
        return None
    params = {"format": "jsondata"}
    if start:
        params["startPeriod"] = start
    if end:
        params["endPeriod"] = end
    path = DATA_PATH.format(agency=agency, flow=flow, version=version, key=key or "all")
    st, text = _get(path, params, timeout, base)
    if st != 200:
        print("[错误] HTTP %s: %s" % (st, text[:300]))
        return None

    n_obs = count_observations(text)
    if n_obs <= 0:
        print("=" * 72)
        print("[无数据] IMF %s(%s %s) 返回结构信封但观测值 = %s。" % (flow, agency, version, n_obs))
        print("  实测(2026-09-28): api.imf.org 对各 flow / 各种键写法 / AllDimensions /")
        print("  SDMX-JSON Accept 头一律返回 0 观测 —— 该源当前不可供数。")
        print("  请改用本技能实测可取数的替代源:")
        print("    worldbank_fetch.py   # World Bank Open Data(免 key, 实测 200)")
        print("    bis_fetch.py         # BIS SDMX v2(免 key, 实测 200)")
        print("    fred_fetch.py        # FRED(需自备 key, 官方利率/曲线)")
        print("  如需保留原始信封用于排查, 加 --allow-empty。")
        print("=" * 72)
        if not allow_empty:
            return None
        text_to_write = text
    else:
        print("[OK] %s(%s %s) 取得 %d 个观测。" % (flow, agency, version, n_obs))
        text_to_write = text
        if fmt == "csv":
            csv_text, rows = flatten_to_csv(text)
            if rows:
                text_to_write = csv_text
                print("[OK] 已摊平为 CSV: %d 行。" % rows)

    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="") as f:
            f.write(text_to_write)
        print("已保存 %d 字符 -> %s" % (len(text_to_write), out))
    else:
        print(text_to_write[:4000])
    return text_to_write


def main():
    p = argparse.ArgumentParser(description="IMF SDMX 3.0 Stats fetcher(宏观/外汇; 见文件头实测状态)")
    p.add_argument("--base", default=BASE, help="API 基址(默认 IMF SDMX 3.0)")
    p.add_argument("--list", action="store_true", help="列出全部 dataflow(实测可用)")
    p.add_argument("--structure", metavar="FLOW", help="查询某数据集维度顺序")
    p.add_argument("--flow", help="数据集 ID,如 COFER / BOP / CPI / IRFCL / WEO")
    p.add_argument("--agency", help="机构 ID(默认自动解析, 如 IMF.STA / IMF.RES)")
    p.add_argument("--version", help="数据集版本(默认自动解析)")
    p.add_argument("--key", default="all", help="维度取值键,如 W00.NV_USD.CI_USD.SHRO_PT.A;默认 all")
    p.add_argument("--preset", choices=list(PRESETS.keys()), help="快捷预设")
    p.add_argument("--format", default="json", choices=["json", "csv"])
    p.add_argument("--start", help="起始期,如 2020 或 2024-01")
    p.add_argument("--end", help="结束期")
    p.add_argument("--out", help="输出文件路径")
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--allow-empty", action="store_true",
                   help="即使 0 观测也把原始信封写出(仅供排查, 默认拒绝)")
    args = p.parse_args()

    if args.list:
        list_dataflows(args.base, args.timeout)
        return 0
    if args.structure:
        show_structure(args.structure, args.agency, args.version, args.base, args.timeout)
        return 0

    if args.preset:
        agency, flow, ver, desc = PRESETS[args.preset]
        print("预设 %s: flow=%s(%s) 说明: %s" % (args.preset, flow, agency, desc))
        r = get_data(flow, args.key, args.format, args.start, args.end, args.out,
                     args.base, args.timeout, args.agency or agency,
                     args.version or ver, args.allow_empty)
        return 0 if r is not None else 3

    if args.flow:
        r = get_data(args.flow, args.key, args.format, args.start, args.end, args.out,
                     args.base, args.timeout, args.agency, args.version, args.allow_empty)
        return 0 if r is not None else 3

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
