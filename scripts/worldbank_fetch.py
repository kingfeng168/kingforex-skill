#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
World Bank Open Data API 拉取脚本（仅依赖 Python 标准库，无需 pip 安装）。

专为 kingforex-skill 适配:聚焦**外汇 / 贵金属 / 大宗商品交易的宏观基本面**——
  · 实际利率(FR.INR.RINR)、CPI 通胀(FP.CPI.TOTL.ZG) → 利率平价(IRP)/套息利差
  · 经常账户占 GDP(BN.CAB.XOKA.GD.ZS)              → 中期汇率方向
  · GDP 增速(NY.GDP.MKTP.KD.ZG)                    → 全球 / 新兴增长 Regime
  · 官方汇率(PA.NUS.FCRF)、外储(FI.RES.TOTL.CD)    → EM 脆弱性 / 干预能力
  · 政府债务占 GDP(GC.DOD.TOTL.GD.ZS)              → 主权 / 货币风险

Base: https://api.worldbank.org/v2  (公开、无需 key)
返回 JSON 二元数组 [header, data]; 指定 --out 时落盘扁平化 CSV(UTF-8-SIG,Excel 友好)。

注意:World Bank 商品价格(Pink Sheet,原 PX.LND.* 系列)当前已不在该 API 标准路由下
提供(返回 Invalid value),故本脚本不纳入商品价预设;原油价请用 EIA API、金价请用 WGC/LBMA。

用法示例:
  python worldbank_fetch.py --list-indicators "inflation"
  python worldbank_fetch.py --list-countries
  python worldbank_fetch.py --preset real_rate --country US;CN;JP;EU --mrnev 5 --out "D:/workbuddy/输出文件/wb_realrate.csv"
  python worldbank_fetch.py --preset current_account_pct --country US;CN --date 2015:2025
  python worldbank_fetch.py --indicator NY.GDP.MKTP.KD.ZG --country WLD --mrnev 10
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import os
import time
import argparse
import csv

BASE = "https://api.worldbank.org/v2"

# 交易相关预设(指标 ID → 含义)
PRESETS = {
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",          # GDP 实际增速(全球/EM 增长 Regime)
    "gdp": "NY.GDP.MKTP.CD",                     # GDP 现价(美元)
    "gdp_pc": "NY.GDP.PCAP.CD",                  # 人均 GDP(美元)
    "cpi_inflation": "FP.CPI.TOTL.ZG",           # CPI 通胀率(通胀差→IRP)
    "gdp_deflator": "NY.GDP.DEFL.KD.ZG",         # GDP 平减指数通胀
    "real_rate": "FR.INR.RINR",                  # 实际利率(实际利差→套息/IRP)★
    "current_account": "BN.CAB.XOKA.CD",         # 经常账户余额(现值美元)
    "current_account_pct": "BN.CAB.XOKA.GD.ZS",  # 经常账户占 GDP%(中期汇率驱动)★
    "fx_rate": "PA.NUS.FCRF",                    # 官方汇率(年均值,本币/美元)
    "gov_debt_pct": "GC.DOD.TOTL.GD.ZS",         # 政府债务占 GDP%(主权/货币风险)
    "fx_reserves": "FI.RES.TOTL.CD",             # 总储备(含黄金,现值美元)
    "fx_reserves_xgold": "FI.RES.XGLD.CD",       # 总储备(除黄金)
    "exports": "NE.EXP.GNFS.CD",                 # 商品服务出口(现值美元)
    "imports": "NE.IMP.GNFS.CD",                 # 商品服务进口(现值美元)
}


def _get_json(url, retries=3, timeout=60):
    """请求 JSON;遇到 WB 单元素错误数组(HTTP 200 但 [{"message":...}])时透传,便于上层解析。"""
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "wb-fetch/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8")
            if not raw.strip():
                raise ValueError("empty response")
            return json.loads(raw)
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", "ignore")
                j = json.loads(body)
                if isinstance(j, list) and j and isinstance(j[0], dict) and "message" in j[0]:
                    return j  # 透传 API 错误,由 _flatten 处理
            except Exception:
                pass
            last_err = e
            time.sleep(1.0 * (attempt + 1))
        except Exception as e:  # noqa
            last_err = e
            time.sleep(1.0 * (attempt + 1))
    print(f"请求失败(重试{retries}次): {last_err}\nURL: {url}")
    return None


def _flatten(resp):
    """返回观测列表; resp 应为 [header, data] 或 WB 单元素错误数组。"""
    if resp is None:
        return None, "网络请求失败"
    # WB 错误格式:单元素列表 [{"message":[{"value":"..."}]}]
    if isinstance(resp, list) and len(resp) == 1 and isinstance(resp[0], dict) and "message" in resp[0]:
        msgs = resp[0].get("message", [])
        return None, "API错误: " + "; ".join(m.get("value", str(m)) for m in msgs)
    if not isinstance(resp, list) or len(resp) < 2:
        return None, "返回结构异常"
    header, data = resp[0], resp[1]
    if isinstance(header, dict) and "message" in header:
        msgs = header.get("message", [])
        return None, "API错误: " + "; ".join(m.get("value", str(m)) for m in msgs)
    if data is None:
        return [], "无数据(指标或国家码可能无效)"
    return data, None


def list_indicators(query=None, per_page=50, max_pages=40, limit=40):
    # 注意: WB /indicator 无服务端 q= 搜索, 列表按 ID 固定排序;
    # 带搜索词时需逐页拉取并在客户端过滤(上限 max_pages 页以控制耗时)。
    if not query:
        url = f"{BASE}/indicator?format=json&per_page={per_page}"
        resp = _get_json(url)
        if resp is None:
            return
        data = resp[1] or []
        print(f"指标全库总数: {resp[0].get('total')}; 本页显示 {len(data)} 条")
        for i in data:
            print(f"{i['id']:28s} | {i.get('name','')}")
        return
    found = []
    pg = 0
    resp = None
    while len(found) < limit and pg < max_pages:
        pg += 1
        url = f"{BASE}/indicator?format=json&per_page=1000&page={pg}"
        resp = _get_json(url)
        if resp is None:
            return
        data = resp[1] or []
        if not data:
            break
        q = query.lower()
        for i in data:
            if q in (i.get("name", "") + i.get("id", "")).lower():
                found.append(i)
    total = resp[0].get("total") if resp else "?"
    print(f"指标全库总数: {total}; 检索前 {pg} 页, 匹配 {len(found)} 条(显示前 {limit})")
    for i in found[:limit]:
        print(f"{i['id']:28s} | {i.get('name','')}")


def list_countries(per_page=50):
    url = f"{BASE}/country?format=json&per_page={per_page}"
    resp = _get_json(url)
    if resp is None:
        return
    data = resp[1] or []
    print(f"国家/地区总数: {resp[0].get('total')}; 本页显示 {len(data)} 条")
    for c in data:
        print(f"{c['id']:4s} {c.get('iso2Code',''):3s} | {c.get('name',''):40s} | {c.get('region',{}).get('value','')}")


def get_data(indicator, countries="US", date=None, mrnev=None, per_page=32000,
             page=1, out=None):
    url = f"{BASE}/country/{countries}/indicator/{indicator}?format=json"
    params = {"per_page": per_page, "page": page}
    if date:
        params["date"] = date
    if mrnev:
        params["mrnev"] = mrnev
    url += "&" + urllib.parse.urlencode(params)
    resp = _get_json(url)
    data, err = _flatten(resp)
    if err:
        print(err)
        return None
    if not data:
        print("无观测数据")
        return None

    rows = []
    for o in data:
        rows.append({
            "indicator_id": o.get("indicator", {}).get("id", ""),
            "indicator_name": o.get("indicator", {}).get("value", ""),
            "country_id": o.get("country", {}).get("id", ""),
            "country_name": o.get("country", {}).get("value", ""),
            "iso3": o.get("countryiso3code", ""),
            "date": o.get("date", ""),
            "value": o.get("value", ""),
            "unit": o.get("unit", ""),
            "obs_status": o.get("obs_status", ""),
        })
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        cols = ["indicator_id", "indicator_name", "country_id", "country_name",
                "iso3", "date", "value", "unit", "obs_status"]
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        print(f"已保存 {len(rows)} 行 -> {out}")
    else:
        for r in rows:
            print(f"{r['country_id']:4s} {r['date']:6s} {r['value']}")
    return rows


def main():
    p = argparse.ArgumentParser(description="World Bank Open Data API fetcher (kingforex-skill)")
    p.add_argument("--list-indicators", metavar="QUERY", nargs="?", const="", help="列出指标(可带搜索词)")
    p.add_argument("--list-countries", action="store_true", help="列出国家/地区")
    p.add_argument("--indicator", help="指标 ID，如 NY.GDP.MKTP.CD")
    p.add_argument("--country", default="US", help="国家 ISO2/ISO3，多国用 ; 分隔，如 US;CN;JP;WLD")
    p.add_argument("--preset", choices=list(PRESETS.keys()), help="快捷指标(交易相关)")
    p.add_argument("--date", help="年份区间 YYYY:YYYY 或单年")
    p.add_argument("--mrnev", type=int, help="最近 N 个非空值")
    p.add_argument("--per-page", type=int, default=32000)
    p.add_argument("--out", help="输出 CSV 路径(UTF-8-SIG)")
    args = p.parse_args()

    if args.list_indicators is not None:
        list_indicators(args.list_indicators or None)
    elif args.list_countries:
        list_countries()
    elif args.preset:
        get_data(PRESETS[args.preset], args.country, args.date, args.mrnev, args.per_page, 1, args.out)
    elif args.indicator:
        get_data(args.indicator, args.country, args.date, args.mrnev, args.per_page, 1, args.out)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
