#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parity_check.py — 两份报告产物的结构与数值一致性比对(生成器回归用)

用途: 比对同一模板在两个版本(如改动前 / 改动后)产出的 HTML+MD, 检查节数、图表容器、
CDN 引用、关键数值与逐行差异, 用于确认「报告格式零漂移」。

2026-09-28 修复: 原实现把 4 个样本路径写死在 scripts/ 与 scripts/_paramtest/ 下
(该目录从未随仓库分发), 导致克隆后运行必然 FileNotFoundError。现改为命令行传参,
并提供 --dir 模式(自动挑目录内最新的两份报告)。

用法:
  # 指定两份 HTML(+可选同名 MD)
  python parity_check.py --orig ./output/old.html --param ./output/new.html

  # 自动挑目录里最新的两份 今日行情分析_*.html
  python parity_check.py --dir ./output

  # 只看指定关键数值是否同时存在
  python parity_check.py --orig a.html --param b.html --keys 636.59,109.784,0.0651
"""
import argparse
import glob
import os
import re
import sys

for _stream in (sys.stdout, sys.stderr):     # 中文 Windows(cp936)下输出符号不再中断
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass


def load(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def pick_latest(dirpath):
    """取目录内最新的两份 今日行情分析_*.html(按修改时间倒序)。"""
    files = sorted(glob.glob(os.path.join(dirpath, "**", "*行情分析*.html"), recursive=True),
                   key=os.path.getmtime, reverse=True)
    if len(files) < 2:
        raise SystemExit("[错误] %s 下不足两份 今日行情分析*.html, 无法比对" % dirpath)
    return files[1], files[0]           # (较早, 较新)


def nums(text):
    """提取数值字面量(≥2 位小数), 用于「关键数值是否都还在」的粗比对。"""
    return set(re.findall(r"\d+\.\d{2,}", text))


def main():
    ap = argparse.ArgumentParser(description="报告产物一致性比对(节数/CDN/数值/逐行差异)")
    ap.add_argument("--orig", help="基准产物(改动前)")
    ap.add_argument("--param", help="对照产物(改动后)")
    ap.add_argument("--dir", help="自动取该目录内最新两份 今日行情分析*.html 作比对")
    ap.add_argument("--keys", help="额外指定的关键数值, 逗号分隔(必须两者都出现)")
    ap.add_argument("--max-diff", type=int, default=12, help="最多列出多少处逐行差异")
    args = ap.parse_args()

    if args.dir:
        a, b = pick_latest(args.dir)
    elif args.orig and args.param:
        a, b = args.orig, args.param
    else:
        ap.error("需提供 --orig 与 --param, 或 --dir")
    for p in (a, b):
        if not os.path.isfile(p):
            raise SystemExit("[错误] 文件不存在: %s" % p)

    ha, hb = load(a), load(b)
    print("=" * 68)
    print("基准 : %s (%d 字节)" % (os.path.basename(a), len(ha)))
    print("对照 : %s (%d 字节)" % (os.path.basename(b), len(hb)))
    print("字节差: %+d" % (len(hb) - len(ha)))
    print("-" * 68)

    def cnt(t, pat):
        return len(re.findall(pat, t))

    checks = [
        ("HTML 节标题 section-title", r'class="section-title"'),
        ("score-card 卡片", r'class="score-card'),
        ("ECharts 图表容器", r'id="chart_|id="scorechart|id="corr"|id="cross"|id="equity"'),
        ("echarts.init 调用", r"echarts\.init\("),
        ("CDN 引用 cdn.jsdelivr.net", r"cdn\.jsdelivr\.net"),
        ("https 外链", r"https?://"),
    ]
    ok = True
    for name, pat in checks:
        ca, cb = cnt(ha, pat), cnt(hb, pat)
        same = (ca == cb)
        if name.startswith("CDN") and cb != 0:
            same = False
        if name.startswith("echarts.init") and cb < 1:
            same = False
        ok &= same
        print("  %-26s 基准 %-4d 对照 %-4d %s" % (name, ca, cb, "OK" if same else "✗ 不一致"))

    # MD 同名文件(可选)
    ma, mb = os.path.splitext(a)[0] + ".md", os.path.splitext(b)[0] + ".md"
    if os.path.isfile(ma) and os.path.isfile(mb):
        ta, tb = load(ma), load(mb)
        print("  %-26s 基准 %-4d 对照 %-4d" % ("MD 二级标题",
                                              ta.count("\n## "), tb.count("\n## ")))

    # 关键数值
    keys = [k.strip() for k in (args.keys or "").split(",") if k.strip()]
    na, nb = nums(ha), nums(hb)
    lost = sorted(na - nb)
    print("-" * 68)
    print("数值字面量(≥2 位小数): 基准 %d 个, 对照 %d 个, 对照中缺失 %d 个" % (len(na), len(nb), len(lost)))
    if lost:
        print("  缺失示例: %s" % ", ".join(lost[:10]))
    for k in keys:
        oa, ob = (k in ha), (k in hb)
        st = "OK" if (oa and ob) else ("仅基准有" if oa else "仅对照有/都无")
        if not (oa and ob):
            ok = False
        print("  指定关键值 %-12s 基准=%-5s 对照=%-5s %s" % (k, oa, ob, st))

    # 逐行差异
    la, lb = ha.splitlines(), hb.splitlines()
    diffs = [i for i in range(min(len(la), len(lb))) if la[i] != lb[i]]
    print("-" * 68)
    print("HTML 行数: 基准 %d, 对照 %d, 逐行差异 %d 处" % (len(la), len(lb), len(diffs)))
    for i in diffs[:args.max_diff]:
        print("  L%-5d 基准: %s" % (i + 1, la[i][:110]))
        print("  L%-5d 对照: %s" % (i + 1, lb[i][:110]))
    if len(diffs) > args.max_diff:
        print("  ... 其余 %d 处略" % (len(diffs) - args.max_diff))

    print("=" * 68)
    print("结论: %s" % ("✓ 结构一致(可视为格式零漂移)" if ok else "✗ 存在结构/数值差异, 请核对上面标 ✗ 的项"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
