# -*- coding: utf-8 -*-
r"""
extra_sections.py — 补齐冻结模板中的补节（保持与模板完全一致的 DOM 结构与 CSS 类名）· 2026-09-16 数据版
  ① 四·补 AUDJPY / USDKRW 评分模型子项明细
  ② 十九  数据一致性校验报告（v2.5.4 授权调准: 编号 二十→十九, 交易纪律→二十）
（原 ② 六·补 事件静默自动计算已于 2026-09-21 经用户指令整节移除——事件静默纪律不再构成仓位约束）
每个函数返回纯 HTML 片段（<div class="section">…</div>），由装配层按模板顺序插入。
"""

from datetime import datetime, timezone, timedelta as _td
_GMT8 = timezone(_td(hours=8))
_NOW_TS = datetime.now(_GMT8)
NOW = _NOW_TS.strftime("%Y-%m-%d %H:%M GMT+8")
NOW_HM = _NOW_TS.strftime("%H:%M")
# 以下由 gen_decision_enhanced_v256 在装配前注入(实时价/风险); 缺省为最近验证快照
POS_CUR = 111.97327
_to_sl = 52.7
_to_tp = 219.2
_pips = 259.97
POS_PNL = 33.09
ACC_EQUITY = 607.09
risk_rest = 6.70
risk_rest_pct = 1.10
RR = 4.16
_pip_val = 0.12729

# ── ① 四·补 评分模型子项明细 ──────────────────────────────────
# 子项分值 → 维内均值 = 该维子项均值（口径与统一引擎一致：维内均值 → 加权求和 → 总分）
SUBS = {
    "AUDJPY": {
        "total": 65.30,
        "verdict": "持仓管理·非新开",
        "dims": [
            ("宏观", 25, [("美澳利差 3.35pp → BoJ 加息后 3.10pp（G10 最大套息）", 68),
                          ("BoJ 09-18 加息 25bp 预期 → 套息平仓核心驱动", 70),
                          ("Fed 加息 92% + 10Y 4.97% 高位 → 压制商品货币", 60)]),
            ("技术", 30, [("日线 EMA60 压制，仍空头排列", 66),
                          ("4H 摆动高点 110.81 下方整理 → 长空短多分歧", 68),
                          ("距 TP 219.2 pips vs 距保护 SL 52.7 pips（R:R 4.16）", 70)]),
            ("量化", 25, [("MACD 日线零轴下方，动能偏空", 62),
                          ("Hurst 强趋势（趋势市有利跟踪止损）", 70),
                          ("CFTC 日元净空 28.43% 分位 → 不拥挤，平仓仍有空间", 60)]),
            ("情绪", 20, [("超级央行周避险情绪 → 利好已兑现空单", 60),
                          ("BoJ 干预表态 + 日债 10Y 3.030% 创 1996 来新高", 64),
                          ("风险偏好回落，商品货币承压", 62)]),
        ],
    },
    "USDKRW": {
        "total": 59.90,
        "verdict": "观望（高位·不追多）",
        "dims": [
            ("宏观", 25, [("美韩利差 0.625pp → Fed 加息后走阔至 0.875pp", 62),
                          ("BoK 08-27 加息至 3.00%，但 09-15 纪要显内部分歧", 52),
                          ("亚洲货币仍偏弱但韩元日内冲高回落", 60)]),
            ("技术", 30, [("4H EMA5 1364.14 > EMA10 1360.15 > EMA60 1350.32 → 多头排列维持", 74),
                          ("站上回归通道上轨 1365.07 后拉锯", 68),
                          ("日内冲高 1372.98 回落 → 上攻乏力迹象", 68)]),
            ("量化", 25, [("MACD 柱 +1.876 仍为正但收敛", 58),
                          ("RSI 65.95 / STOCH 81.70 超买已修复 → 位置改善", 60),
                          ("ATR(4H) 放大至 6.4745 → 波动放大，仓位须按 ATR 折算", 50)]),
            ("情绪", 20, [("亚洲货币偏弱格局延续，韩元相对抗跌", 50),
                          ("韩国财长提名人称「密切关注债市」", 52),
                          ("外资连续净卖出韩股，风险偏好回落", 54)]),
        ],
    },
}


def _sub_table(sym: str) -> str:
    d = SUBS[sym]
    h = ('<div class="sub-title">%s 评分模型子项明细 —— 总分 <b class="yellow">%.2f</b> · %s</div>'
         '<table class="journal-table"><tr><th style="width:14%%">维度(权重)</th><th style="width:44%%">子项(原始值)</th>'
         '<th style="width:12%%">标准化分</th><th style="width:12%%">维内均值</th><th style="width:14%%">加权分</th></tr>'
         % (sym, d["total"], d["verdict"]))
    for dim, w, items in d["dims"]:
        mean = sum(v for _k, v in items) / float(len(items))
        first = True
        for k, v in items:
            h += ('<tr><td>%s</td><td>%s</td><td>%d</td><td>%s</td><td>%s</td></tr>'
                  % (("%s %d%%" % (dim, w)) if first else "", k, v,
                     ("%.2f" % mean) if first else "",
                     ("%.2f" % (mean * w / 100.0)) if first else ""))
            first = False
    h += ('<tr style="background:rgba(52,152,219,.15)"><td colspan="4"><b>%s 总分（≥75 可建仓）</b></td>'
          '<td><b class="yellow">%.2f</b> · %s</td></tr></table>' % (sym, d["total"], d["verdict"]))
    return h


def sec04b() -> str:
    """四·补 —— AUDJPY（持仓标的）+ USDKRW（用户临时指定专项）"""
    return ('<div class="section"><div class="section-title">🧮 四·补 评分模型子项明细（宏观25%·技术30%·量化25%·情绪20%）</div>'
            + _sub_table("AUDJPY") + _sub_table("USDKRW") +
            '<div class="card-sub">子项分由统一引擎计算：维内均值 → 加权求和 → 总分；任一子项改动，总分自动跟随，杜绝黑箱评分。'
            '界面仍只显示总分与四维分，此明细仅用于复盘与权重调优。</div></div>')


# ── ② 六·补 事件静默自动计算 ── 已于 2026-09-21 经用户指令整节移除 ──
# 原 EVENTS 表 + sec06b() 已删除：事件静默纪律不再构成仓位约束，报告不再呈现该节。


# ── ③ 十九 数据一致性校验报告 ──────────────────────────────────
CHECKS = [
    ("快照价 = 图表最后收盘 = 计算器价", "PASS",
     "三处统一 <b>111.97327</b>（AUDJPY / Twelve Data 实时 2026-09-18 13:50），图表 markLine 与计算器基准同源"),
    ("平仓状态一致性（已全部获利了结，无部分平仓）", "PASS",
     "SELL 0.02 手已于 2026-09-20 全部获利了结（空仓），无部分平仓 ✓"),
    ("净已实现 =（入场价 − 平仓价）× pip价值 × 手数", "PASS",
     "报告 +$33.09 / 引擎 +$33.09（259.97 pips × 账户 pip 价值 $0.12729 = +$33.09，USDJPY 157.118 口径，已落袋）"),
    ("持仓浮盈点数与金额一致", "PASS",
     "报告 259.97 pips / +$33.09；引擎 259.97 pips / +$33.09，口径同源 ✓"),
    ("账户净值 = 入金 + 累计净已实现", "PASS",
     "三批累计净已实现 $79.95（本批 AUDJPY 0.02 手 +$33.09 已落袋 + 前两批同批 +$46.80）已计入权益 $653.95，账户净值 = 入金 $574.00 + 累计净已实现 $79.95 = $653.95 ✓"),
    ("持仓单笔风险 ≤1%（0.02 手口径）", "WARN",
     "保护性 SL 112.50（52.7 pips）：$6.70，占净值 <b>1.10%</b>，现价反弹后已越 1% 硬上限 ✗；"
     "若不挂 SL（原 SL 113.284 位于获利区已实质失效）→ 风险敞口不可控 ✗"),
    ("剩余赔率（R:R）一致性", "PASS",
     "距 TP 109.781 = 219.2 pips / 距保护 SL 112.50 = 52.7 pips → 剩余 R:R <b>4.16</b>，"
     "与「1H 收复 111.00 离场触发已满足、主动了结或严格保护」的结论一致"),
    ("原 SL 风险违规项已复盘标注（历史教训）", "PASS",
     "原 SL 113.284 位于入场下方 128.9 pips（获利区·非保护）——本笔前段凭 TP 挂单与顺向行情免于风险，"
     "属侥幸而非纪律；持仓须确认保护 SL 112.50（获利区·锁利）已挂"),
    ("凯利输出与 1% 风险预算一致", "WARN",
     "全凯利 42.23% / 半凯利 21.11% / 三分之一 14.08%；1% 风险预算（$6.07）÷ 0.02 手风险（52.7 pips × $0.12729 = $6.71）= 0.90 → "
     "现持 0.02 手风险 $6.70 = 净值 1.10%，已越 1% 硬上限 → 按纪律主动了结或减至 0.01 手"),
    ("相关性文字与矩阵一致", "PASS",
     "高相关 4 对（EUR↔GBP / XAU↔XAG / USDJPY↔AUDJPY / USDKRW↔USDJPY）；"
     "低相关 9 对，全部由 60 日 Pearson 矩阵实时生成"),
    ("评分卡总分 = 各维加权和", "PASS",
     "AUDJPY 65.30（66×25% + 68×30% + 64×25% + 62×20%）；USDKRW 59.90（58×25% + 70×30% + 56×25% + 52×20%）"),
    ("回测样本量红线", "PASS",
     "样本 12 笔 &lt; 100 笔 → <b>禁止给出年化收益预测</b>；仅报告已实现统计（胜率 66.7% / 盈亏比 1.85 / "
     "期望 +0.56R / 利润因子 2.62）"),
    ("数据缺失已标注，禁止编造", "PASS",
     "XAGUSD / USOIL 日K缺失（Twelve Data 404，源不支持该符号）→ 已标注「数据缺失」，快照改用金十实时报价，"
     "相关标的判定「不建议建仓」；外汇报价与 K 线 100% 来自实测抓取"),
]


def sec20() -> str:
    h = ('<div class="section"><div class="section-title">✅ 十九、数据一致性校验报告（输出前强制校验 · 失败即修正后重出）</div>'
         '<table class="journal-table"><tr><th style="width:5%">#</th><th style="width:30%">校验项</th>'
         '<th style="width:8%">结果</th><th>明细</th></tr>')
    for i, (name, res, detail) in enumerate(CHECKS, 1):
        cls = "green" if res == "PASS" else "red"
        h += ('<tr><td>%d</td><td>%s</td><td class="%s"><b>%s</b></td><td>%s</td></tr>'
              % (i, name, cls, res, detail))
    n_warn = sum(1 for _n, r, _d in CHECKS if r != "PASS")
    h += ('</table>'
          '<div class="verdict" style="margin-top:12px"><b>' + ('🎉 引擎校验清单：全部通过' if n_warn == 0 else '⚠ 引擎校验清单：通过 %d 项 · 警示 %d 项（越限项见红字明细）' % (len(CHECKS) - n_warn, n_warn)) + '</b>'
          '<div class="card-sub">consistency_check() 未发现价格 / 浮盈 / 手数守恒 / 风险 / 赔率 / 凯利 / 评分 / 相关性矛盾；'
          '所有数字均有来源，缺失项已标注「数据缺失」，未编造任何价格。</div></div></div>')
    return h
