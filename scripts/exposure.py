#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组合净暴露与相关性风险计算器(Portfolio Exposure & Correlation Risk)

输入多笔持仓,计算:
  1) 组合净美元方向暴露(USD beta 汇总) → 识别"单一美元空头/多头"集中风险
  2) 总风险暴露 %(若提供每笔止损%) → 对照 3%–5% 上限(用户铁律)
  3) 相关性集中度:同符号 beta 的笔数 → 是否过度集中
  4) 杠杆参考:总名义暴露 %(gross notional / equity)
  5) 压力测试:美股 -5% / FOMC 意外加息 50bp / 油价 -10% 情景下的组合 PnL(%)

纯标准库,无外部依赖。

用法:
  python exposure.py --equity 100000 \
      --positions "XAUUSD:long:0.5:1.5" "AUDUSD:long:1.0:1.2" "USDCAD:short:0.8:1.0"

  每笔格式: 品种:方向(long/short):手数[:止损占价格%]
  方向含义: long=做多该品种, short=做空该品种
  止损%   : 止损距离 ÷ 入场价 ×100(如黄金 2500 止损 35 → 1.4); 省略则不计算风险%
"""
import argparse

# 品种档案: (资产类别, usd_beta, 每手名义本金 USD)
#   usd_beta: 做多1手对美元净方向的系数(+1 做多=做多美元, -1 做多=做空美元, -0.5 商品类部分)
#   每手名义本金: 用于风险%/压力测试估算(取常规报价近似)
INSTRUMENT_PROFILE = {
    "xauusd": ("贵金属", -1.0, 200000.0),
    "xagusd": ("贵金属", -1.0, 140000.0),
    "wti":    ("原油",  -0.5,  75000.0),
    "brent":  ("原油",  -0.5,  75000.0),
    "hg":     ("铜",    -0.5, 105000.0),
    "eurusd": ("外汇",  -1.0, 100000.0),
    "gbpusd": ("外汇",  -1.0, 100000.0),
    "audusd": ("外汇",  -1.0, 100000.0),
    "nzdusd": ("外汇",  -1.0, 100000.0),
    "usdjpy": ("外汇",  +1.0, 100000.0),
    "usdcad": ("外汇",  +1.0, 100000.0),
    "usdchf": ("外汇",  +1.0, 100000.0),
    "usdcnh": ("外汇",  +1.0, 100000.0),
}

# 压力测试情景: 各资产类别在该情景下的价格冲击 (%)
STRESS_SCENARIOS = {
    "美股单日 -5% (Risk-off)": {"外汇": -1.5, "贵金属": +2.0, "原油": -4.0, "铜": -3.0},
    "FOMC 意外加息 50bp":      {"外汇": +1.5, "贵金属": -2.5, "原油": -1.5, "铜": -1.0},
    "油价单日 -10%":           {"外汇":  0.0, "贵金属": +0.5, "原油": -10.0, "铜": -2.0},
}


def parse_positions(items):
    out = []
    for s in items:
        parts = s.split(":")
        if len(parts) < 3:
            raise ValueError(f"持仓格式错误: {s} (应为 品种:方向:手数[:止损%])")
        sym = parts[0].lower()
        side = parts[1].lower()
        size = float(parts[2])
        stop_pct = float(parts[3]) if len(parts) > 3 and parts[3] else None
        if side not in ("long", "short"):
            raise ValueError(f"方向须为 long/short: {s}")
        if sym not in INSTRUMENT_PROFILE:
            raise ValueError(f"未登记品种: {sym}")
        sign = 1.0 if side == "long" else -1.0
        out.append({"sym": sym, "side": side, "size": size, "sign": sign, "stop_pct": stop_pct})
    return out


def main():
    ap = argparse.ArgumentParser(description="组合净暴露与相关性风险计算器")
    ap.add_argument("--equity", type=float, required=True, help="账户权益(USD)")
    ap.add_argument("--positions", nargs="+", required=True, help="持仓列表")
    ap.add_argument("--max-risk", type=float, default=5.0,
                    help="总风险暴露上限 %% (基于止损%), 默认 5")
    args = ap.parse_args()

    positions = parse_positions(args.positions)

    print("=" * 62)
    print("持仓明细")
    print("-" * 62)
    net_usd = 0.0
    gross_notional = 0.0
    total_risk = 0.0
    has_risk = False
    beta_signs = []
    for p in positions:
        cls, beta, notional = INSTRUMENT_PROFILE[p["sym"]]
        contrib = p["sign"] * beta * p["size"]
        net_usd += contrib
        beta_signs.append(contrib)
        gross_notional += p["size"] * notional
        risk_note = ""
        if p["stop_pct"] is not None:
            has_risk = True
            r = abs(p["size"]) * notional * (p["stop_pct"] / 100.0) / args.equity * 100.0
            total_risk += r
            risk_note = f"  风险≈{r:.2f}%"
        print(f"  {p['sym'].upper():8} {p['side']:5} {p['size']:>6.2f}手  "
              f"USDβ={contrib:+.2f}{risk_note}")
    print("-" * 62)

    # 净美元暴露
    print(f"组合净美元方向暴露(β汇总): {net_usd:+.2f}")
    if net_usd < -1.0:
        print("  ⚠ 净做空美元 — 多黄金+多商品货币叠加属单一美元空头暴露(相关性陷阱)")
    elif net_usd > 1.0:
        print("  ⚠ 净做多美元 — 注意美元反向(risk-on)的集中风险")
    else:
        print("  ✓ 美元方向基本中性")

    # 相关性集中度
    neg = sum(1 for b in beta_signs if b < 0)
    pos = sum(1 for b in beta_signs if b > 0)
    print(f"方向分布: 做空美元 {neg} 笔 / 做多美元 {pos} 笔")
    if (neg >= 2 and pos == 0) or (pos >= 2 and neg == 0):
        print("  ⚠ 高度集中: 多笔同方向宏观暴露, 降低总仓位或加入对冲")

    # 总风险暴露(基于止损)
    if has_risk:
        flag = "⚠ 超上限!" if total_risk > args.max_risk else "✓ 在限额内"
        print(f"总风险暴露≈{total_risk:.2f}%  (上限 {args.max_risk}%)  {flag}")
    else:
        print("总风险暴露: 未提供止损% (用 品种:方向:手数:止损% 可计算)")

    # 杠杆参考(名义, 仅提示, 不对杠杆型 FX 报警)
    notional_pct = gross_notional / args.equity * 100.0
    print(f"杠杆参考(总名义暴露≈{notional_pct:.0f}%, 杠杆型外汇天然较高, 看风险%为准)")

    # 压力测试
    print("-" * 62)
    print("压力测试(情景组合 PnL, 单位:权益 %)")
    for name, shocks in STRESS_SCENARIOS.items():
        pnl = 0.0
        for p in positions:
            cls, _, notional = INSTRUMENT_PROFILE[p["sym"]]
            shock = shocks.get(cls, 0.0)
            pnl += p["sign"] * p["size"] * notional * (shock / 100.0)
        pnl_pct = pnl / args.equity * 100.0
        print(f"  {name:30} 组合≈{pnl_pct:+.2f}%")
    print("=" * 62)
    print("纪律提示: 同时持仓 ≤2–3 个高相关品种; 相关性集中时主动降仓。")


if __name__ == "__main__":
    main()
