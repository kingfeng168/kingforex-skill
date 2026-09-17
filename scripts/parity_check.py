# -*- coding: utf-8 -*-
"""参数化生成器 vs 原生成器 一致性校验 (parity): 节数 / CDN / 关键数值 / 差异定位"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG_H = os.path.join(HERE, "今日行情分析_决策增强版_2026-09-14.html")
PAR_H = os.path.join(HERE, "_paramtest", "今日行情分析_决策增强版_2026-09-14.html")
ORIG_M = os.path.join(HERE, "今日行情分析_决策增强版_2026-09-14.md")
PAR_M = os.path.join(HERE, "_paramtest", "今日行情分析_决策增强版_2026-09-14.md")

def load(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

oh, ph = load(ORIG_H), load(PAR_H)
om, pm = load(ORIG_M), load(PAR_M)

def report(name, a, b):
    print("== %s ==" % name)
    print("  size: orig=%d param=%d diff=%+d" % (len(a), len(b), len(b)-len(a)))

report("HTML", oh, ph)
report("MD  ", om, pm)

# 节数
sec_o = oh.count('class="section-title"')
sec_p = ph.count('class="section-title"')
print("  HTML 节数(section-title): orig=%d param=%d" % (sec_o, sec_p))

# CDN / 外链
cdno = len(re.findall(r'https?://', oh))
cdnp = len(re.findall(r'https?://', ph))
print("  HTML 外链(https)数: orig=%d param=%d" % (cdno, cdnp))
cdn_o = oh.count("cdn.jsdelivr.net")
cdn_p = ph.count("cdn.jsdelivr.net")
print("  HTML jsdelivr CDN数: orig=%d param=%d" % (cdn_o, cdn_p))

# MD 节数
msec_o = om.count("\n## ")
msec_p = pm.count("\n## ")
print("  MD 二级标题数: orig=%d param=%d" % (msec_o, msec_p))

# 关键数值必须同时存在于两者
KEYS = ["636.59", "109.784", "62.36", "3.72R", "110.86", "109.26", "108.00",
        "110.11", "87%", "4.95%", "65.35", "0.77%", "4.88", "21.94%", "0.0651"]
print("  关键数值存在性校验:")
for k in KEYS:
    oo = k in oh; pp = k in ph
    mark = "OK" if (oo and pp) else ("MISS_ORIG" if not oo else "MISS_PARAM")
    print("    %-10s orig=%s param=%s  %s" % (k, oo, pp, mark))

# 差异定位: 逐行 diff (HTML)
ol = oh.split("\n"); pl = ph.split("\n")
print("  HTML 行数: orig=%d param=%d" % (len(ol), len(pl)))
diffs = 0
for i in range(min(len(ol), len(pl))):
    if ol[i] != pl[i]:
        diffs += 1
        if diffs <= 12:
            print("    L%d 原: %s" % (i+1, ol[i][:120]))
            print("    L%d 参: %s" % (i+1, pl[i][:120]))
if len(ol) != len(pl):
    print("    (行数差异 %+d)" % (len(pl)-len(ol)))
print("  HTML 前 %d 处差异已列出, 总差异行=%d" % (min(diffs,12), diffs))
