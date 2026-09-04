#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
opec_fetch.py — OPEC 原油市场报告(MOMR)取数（best-effort + 手工流程）

可行性与取数铁律：
  · OPEC 官网(opec.org)的 MOMR（Monthly Oil Market Report）以 HTML/PDF 发布，
    无免费 JSON API；IEA 的 MODS 原油市场报告为付费（€9200+）。
  · 本脚本"尽力而为"：尝试直连 OPEC 公开数据页，成功则抽取关键表；
    失败（如网络/地域封锁）则输出标准化手工取数指引，绝不杜撰数字。
  · 从部分网络环境直连 opec.org 会被拦截（本开发环境返回 403），
    此时请按下方 MANUAL 用 WebFetch 或浏览器手动取数。

重点提取字段（供需平衡研判用）：
  - 全球石油需求增长预测(万桶/日，YoY)
  - 非 OPEC 供应增长预测
  - OPEC 原油产量 / 减产履约情况
  - OPEC 一揽子油价(ORB)

用法：
  python opec_fetch.py            # 尝试直连 + 输出指引
  python opec_fetch.py --manual   # 仅打印手工取数指引（不联网）
"""

import argparse
import sys
import urllib.request

# 尽力尝试的公开页面（可能随官网改版变动）
CANDIDATE_URLS = [
    "https://www.opec.org/opec_web/en/data_graphs/40.htm",          # MOMR 数据图
    "https://www.opec.org/opec_web/en/publications/338.htm",        # MOMR 出版物
    "https://www.opec.org/opec_web/en/data_graphs/21626.htm",       # 一揽子油价
]

MANUAL = """\
[OPEC / IEA 原油报告 手工取数指引]（WebFetch 或浏览器）
  · OPEC MOMR（月度石油市场报告）：
      https://www.opec.org/opec_web/en/publications/338.htm
      提取：全球需求增长、非OPEC供应、OPEC产量、Call on OPEC。
  · OPEC 一揽子油价(ORB)日报：
      https://www.opec.org/opec_web/en/data_graphs/21626.htm
  · IEA 原油市场报告(MODS，付费)：
      https://www.iea.org/reports/oil-market-report
      免费替代：KAPSARC 提供 IEA 石油市场历史数据(2001–2016)数据集。
  说明：上述站点无免费 JSON API；如需脚本化，建议用 WebFetch 抓取页面表格，
        或由用户下载 PDF/xlsx 后人工读值，再填入交易计划。
"""


def try_fetch():
    last_err = None
    for url in CANDIDATE_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                html = r.read().decode("utf-8", errors="replace")
            return url, html
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise RuntimeError(f"所有 OPEC 公开页均不可达（最后错误: {last_err}）")


def main():
    ap = argparse.ArgumentParser(description="OPEC 原油市场报告取数（best-effort）")
    ap.add_argument("--manual", action="store_true", help="仅打印手工取数指引")
    args = ap.parse_args()

    if args.manual:
        print(MANUAL)
        return

    try:
        url, html = try_fetch()
    except Exception as e:  # noqa: BLE001
        print(f"[提示] 自动取数失败: {e}\n\n{MANUAL}", file=sys.stderr)
        sys.exit(0)

    # 尽力抽取：寻找含 "mb/d"、"million barrels"、"demand" 等关键字的片段
    import re
    snippets = re.findall(r".{0,80}(mb/d|million barrels|demand|supply|ORB).{0,80}", html, re.I)
    print(f"[opec] 已获取页面: {url}（长度 {len(html)} 字符）")
    print("推测关键字段片段（需人工确认上下文）：")
    for s in snippets[:15]:
        print("  -", s.strip())
    print("\n" + MANUAL)


if __name__ == "__main__":
    main()
