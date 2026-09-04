#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fedwatch_csv.py — CME FedWatch 降息/加息概率 CSV 解析（手动导出的桥接工具）

重要前提（取数铁律）：
  CME FedWatch Tool 没有免费的脚本化 API（需付费订阅 + OAuth）。本脚本
  **不** 联网抓取 FedWatch，而是解析用户从 FedWatch Tool 网页手动导出的 CSV，
  把"会议日期 × 目标利率"的概率矩阵转成结构化文本/JSON，便于交易前快速研判。

手动导出步骤（在浏览器完成）：
  1) 打开 https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html
  2) 在概率表中点击目标 FOMC 会议（或"Download"/"Export"按钮）
  3) 将导出的 CSV 保存到本地（如 fedwatch_2026-09-03.csv）
  4) 运行：python fedwatch_csv.py --csv fedwatch_2026-09-03.csv
  （或用 --json 输出机器可读结果）

预期 CSV 形态（CME 导出常见宽表）：
  - 表头行含会议日期（如 2026/09/17、17 Sep 2026、September 17, 2026）
  - 首列含目标利率或变动标签（如 3.75-4.00%、CUT 25、HIKE 25）
  - 表体为对应概率（百分比）

解析策略（鲁棒、不过度假设）：
  1) 自动检测哪些是"会议日期"列、哪些是"目标利率/变动"行。
  2) 取每个会议日期下，变动标签含 CUT/HOLD/HIKE（或目标利率相对当前）的概率。
  3) 若无法识别标准结构，则原样转储矩阵，便于人工/AI 二次判读（绝不杜撰）。

注意：若你持有 CME 付费 DataMine/FedWatch API 订阅，可改用官方接口；本脚本
      仅覆盖"免费手动导出"这一最可达路径。
"""

import argparse
import csv
import json
import re
import sys

DATE_RE = re.compile(r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})|(\d{1,2}\s*[A-Za-z]{3,9}\s*\d{4})|([A-Za-z]{3,9}\s+\d{1,2},?\s*\d{4})")
PCT_RE = re.compile(r"^-?\d+(\.\d+)?%?$")
CUT_RE = re.compile(r"cut|lower|decrease|-25|-50", re.I)
HIKE_RE = re.compile(r"hike|raise|increase|\+25|\+50", re.I)
HOLD_RE = re.compile(r"hold|unchanged|no change|0 ?bp|0basis", re.I)


def _is_date_cell(s):
    return bool(s) and bool(DATE_RE.search(s.strip()))


def _is_pct(s):
    if not s:
        return False
    t = s.strip().rstrip("%")
    try:
        float(t)
        return True
    except ValueError:
        return False


def _to_pct(s):
    try:
        return float(str(s).strip().rstrip("%"))
    except ValueError:
        return None


def parse(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if any(c.strip() for c in r)]

    if not rows:
        raise RuntimeError("CSV 为空")

    # 识别表头：含最多日期单元格的那一行
    header_idx = 0
    best = -1
    for i, r in enumerate(rows[:6]):
        cnt = sum(1 for c in r if _is_date_cell(c))
        if cnt > best:
            best = cnt
            header_idx = i
    header = rows[header_idx]
    date_cols = [i for i, c in enumerate(header) if _is_date_cell(c)]
    label_col = 0 if date_cols and date_cols[0] != 0 else (1 if len(header) > 1 else 0)

    if not date_cols:
        # 无法识别标准结构 → 原样转储
        return {"format": "unrecognized", "raw": rows}

    meetings = []
    for dc in date_cols:
        meeting = {"date": header[dc].strip(), "outcomes": []}
        for r in rows[header_idx + 1:]:
            if dc >= len(r):
                continue
            label = r[label_col].strip() if label_col < len(r) else ""
            val = _to_pct(r[dc])
            if val is None:
                continue
            kind = "hold"
            if CUT_RE.search(label):
                kind = "cut"
            elif HIKE_RE.search(label):
                kind = "hike"
            elif HOLD_RE.search(label):
                kind = "hold"
            meeting["outcomes"].append({"label": label, "prob_pct": val, "kind": kind})
        # 仅保留有概率的会议
        if meeting["outcomes"]:
            meetings.append(meeting)

    if not meetings:
        return {"format": "unrecognized", "raw": rows}

    return {"format": "matrix", "meetings": meetings}


def summarize(parsed):
    if parsed.get("format") != "matrix":
        return None
    lines = ["CME FedWatch 概率解析（手动导出 CSV）", "=" * 52]
    for m in parsed["meetings"]:
        lines.append(f"\n会议: {m['date']}")
        # 按 kind 聚合：取该会议下各 kind 的最大概率（通常每个 kind 一行）
        agg = {}
        for o in m["outcomes"]:
            agg.setdefault(o["kind"], []).append(o)
        for kind in ("cut", "hold", "hike"):
            items = agg.get(kind)
            if not items:
                continue
            # 取概率最高的一行作为代表
            top = max(items, key=lambda x: x["prob_pct"])
            name = {"cut": "降息≥25bp", "hold": "按兵不动", "hike": "加息≥25bp"}[kind]
            lines.append(f"  {name:10s}: {top['prob_pct']:.1f}%   ({top['label']})")
    lines.append("\n" + "=" * 52)
    lines.append("说明：以上为手动导出数据的结构化呈现，未做任何插值或推算。")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="CME FedWatch 导出 CSV 概率解析")
    ap.add_argument("--csv", required=True, help="FedWatch 导出的 CSV 文件路径")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    try:
        parsed = parse(args.csv)
    except Exception as e:  # noqa: BLE001
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    else:
        txt = summarize(parsed)
        if txt:
            print(txt)
        else:
            print("[提示] 未能识别标准 FedWatch 矩阵结构，已转储原始 CSV 供人工/AI 判读：")
            for r in parsed.get("raw", []):
                print(" | ".join(r))


if __name__ == "__main__":
    main()
