#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wgc_lbma_fetch.py — 黄金(LBMA/WGC)相关取数（免费代理 + 手工流程）

数据源与可行性（取数铁律：绝不杜撰，失败即报错/提示）：
  1) LBMA 金价代理（脚本可直连，免费，无需密钥）：
       https://api.gold-api.com/price/XAU  → 国际现货金(美元/盎司)，紧贴 LBMA 定盘
       https://api.gold-api.com/price/XAG  → 国际现货银
     本脚本主路径即取此项，作为 LBMA 定盘的实时近似。
  2) WGC 黄金供需（Gold Demand Trends 等）：
       gold.org/goldhub 仅有图表/HTML/xlsx 下载，无免费 JSON API。
       → 走 WebFetch 手工取（见下方 MANUAL 段落），本脚本输出标准化指引。
  3) LBMA 官方定盘价(AM/PM)：lbma.org.uk 可达，但页面为 JS 渲染、无免费 API。
       → 同上，靠 WebFetch 或 gold-api 现货代理近似。

用法：
  python wgc_lbma_fetch.py                 # 默认取 XAU 现货(美元/盎司)
  python wgc_lbma_fetch.py --symbol XAG   # 取白银
  python wgc_lbma_fetch.py --manual        # 打印 WGC/LBMA 手工取数指引（不联网）
"""

import argparse
import json
import sys
import urllib.request

GOLD_API = "https://api.gold-api.com/price/{symbol}"

MANUAL_WGC = """\
[WGC / LBMA 手工取数指引]（WebFetch 或浏览器）
  · WGC 黄金需求趋势(Gold Demand Trends)：
      https://www.gold.org/goldhub/data/gold-demand-by-country
      提取：全球/央行/ETF 季度黄金需求吨数、同比变化。
  · WGC 每日金价/数据面板：
      https://www.gold.org/goldhub/data
  · LBMA 官方定盘价(AM/PM)：
      https://www.lbma.org.uk/market-data/statistics
      提取：LBMA Gold Price AM / PM（美元/盎司）。
  说明：以上站点无免费 JSON API，需用 WebFetch 抓取页面表格或下载 xlsx 后人工读值。
        实时交易参考请以本脚本的 gold-api 现货代理（紧贴 LBMA）为准。
"""


def fetch_price(symbol):
    url = GOLD_API.format(symbol=symbol.upper())
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data


def to_text(d):
    unit = "美元/盎司" if d.get("currency") == "USD" else d.get("currency", "")
    lines = [
        f"LBMA 金价代理（{d.get('name', d.get('symbol'))}）",
        "-" * 44,
        f"现价     : {d.get('price')} {unit}",
        f"更新时间 : {d.get('updatedAt', '—')}",
        "=" * 44,
        "注：为国际现货金，紧贴 LBMA 定盘；非官方定盘价。",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="黄金(LBMA/WGC)取数：现货代理 + 手工指引")
    ap.add_argument("--symbol", default="XAU", help="XAU(金,默认) / XAG(银)")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--manual", action="store_true", help="仅打印 WGC/LBMA 手工取数指引")
    args = ap.parse_args()

    if args.manual:
        print(MANUAL_WGC)
        return

    try:
        d = fetch_price(args.symbol)
    except Exception as e:  # noqa: BLE001
        print(f"[错误] 现货代理获取失败: {e}\n\n{MANUAL_WGC}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(to_text(d))
        print()
        print(MANUAL_WGC)


if __name__ == "__main__":
    main()
