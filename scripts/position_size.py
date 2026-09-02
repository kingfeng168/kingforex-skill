#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险仓位计算器(Risk-based Position Size Calculator)

按"单笔风险 = 总资金 × 风险%"与"止损距离(优先 ATR)"反推可开手数。
纯标准库实现,无外部依赖。

公式:
    风险金额      = 权益 × 风险%
    每手风险(账户币) = 止损距离(报价币) × 合约规模 × 报价币→账户币汇率
    手数          = 风险金额 ÷ 每手风险

用法示例:
    # 黄金:权益10万,风险1%,止损35美元,1标准手=100盎司,报价即美元
    python position_size.py --equity 100000 --risk 1 --stop 35 --contract 100

    # EURUSD:权益5万,风险0.5%,止损35点(0.0035),1标准手=100000,报价美元
    python position_size.py --equity 50000 --risk 0.5 --stop 0.0035 --contract 100000

    # 用 ATR 推导止损:ATR=0.0021,乘子1.5 → 止损=0.00315
    python position_size.py --equity 50000 --risk 1 --atr 0.0021 --atr-mult 1.5 --contract 100000

    # 预设品种快捷方式
    python position_size.py --equity 100000 --risk 1 --stop 35 --instrument xauusd
    python position_size.py --equity 50000 --risk 1 --atr 0.0021 --atr-mult 1.5 --instrument eurusd
"""
import argparse
import math

# 预设品种:合约规模(每手单位数) 与 默认报价币→账户币汇率
INSTRUMENTS = {
    "xauusd":  {"contract": 100,    "quote_rate": 1.0,  "note": "黄金 1 标准手=100 盎司, 报价 USD"},
    "xagusd":  {"contract": 5000,   "quote_rate": 1.0,  "note": "白银 1 标准手=5000 盎司, 报价 USD"},
    "wti":     {"contract": 1000,   "quote_rate": 1.0,  "note": "WTI 原油 1 标准手=1000 桶, 报价 USD"},
    "brent":   {"contract": 1000,   "quote_rate": 1.0,  "note": "Brent 原油 1 标准手=1000 桶, 报价 USD"},
    "hg":      {"contract": 25000,  "quote_rate": 1.0,  "note": "铜 1 标准手=25000 磅, 报价 USD"},
    "eurusd":  {"contract": 100000, "quote_rate": 1.0,  "note": "欧元 1 标准手=100000, 报价 USD"},
    "gbpusd":  {"contract": 100000, "quote_rate": 1.0,  "note": "英镑 1 标准手=100000, 报价 USD"},
    "audusd":  {"contract": 100000, "quote_rate": 1.0,  "note": "澳元 1 标准手=100000, 报价 USD"},
    "usdjpy":  {"contract": 100000, "quote_rate": 0.0063,"note": "美日 1 标准手=100000(报价 JPY, P&L 需÷USDJPY 转 USD → quote_rate≈1/现价≈0.0063)"},
    "usdcad":  {"contract": 100000, "quote_rate": 0.74, "note": "美加 1 标准手=100000(报价 CAD, P&L 需÷USDCAD 转 USD → quote_rate≈1/现价≈0.74)"},
}

def main():
    ap = argparse.ArgumentParser(description="风险仓位计算器")
    ap.add_argument("--equity", type=float, required=True, help="账户权益(账户币种, 默认 USD)")
    ap.add_argument("--risk", type=float, default=1.0, help="单笔风险百分比, 默认 1 (即 1%%)")
    ap.add_argument("--stop", type=float, default=None, help="止损距离(报价币价格单位)")
    ap.add_argument("--contract", type=float, default=None, help="每手合约规模(单位数)")
    ap.add_argument("--quote-rate", type=float, default=None, help="报价币→账户币汇率, 默认 1")
    ap.add_argument("--atr", type=float, default=None, help="ATR 值(报价币)")
    ap.add_argument("--atr-mult", type=float, default=1.5, help="ATR 止损乘子, 默认 1.5")
    ap.add_argument("--instrument", type=str, default=None,
                    help="预设品种: " + "/".join(INSTRUMENTS.keys()))
    args = ap.parse_args()

    # 解析预设品种
    contract = args.contract
    quote_rate = args.quote_rate if args.quote_rate else 1.0
    if args.instrument:
        inst = INSTRUMENTS.get(args.instrument.lower())
        if not inst:
            ap.error(f"未知品种 {args.instrument}, 可选: {', '.join(INSTRUMENTS)}")
        contract = inst["contract"]
        quote_rate = inst["quote_rate"]
        print(f"[预设 {args.instrument.upper()}] {inst['note']}")
    if contract is None:
        ap.error("必须提供 --contract 或 --instrument")

    # 止损距离:优先显式 --stop, 否则由 ATR 推导
    if args.stop is not None:
        stop = args.stop
        stop_src = f"显式止损 {stop}"
    elif args.atr is not None:
        stop = args.atr * args.atr_mult
        stop_src = f"ATR {args.atr} × {args.atr_mult} = {stop:.5f}"
    else:
        ap.error("需提供 --stop 或 --atr")

    risk_amount = args.equity * (args.risk / 100.0)
    risk_per_lot = stop * contract * quote_rate          # 账户币/每手
    if risk_per_lot <= 0:
        ap.error("止损距离必须为正数")
    lots = risk_amount / risk_per_lot

    print("=" * 52)
    print(f"账户权益      : {args.equity:,.2f}")
    print(f"单笔风险      : {args.risk}%  →  {risk_amount:,.2f} (账户币)")
    print(f"止损距离      : {stop_src}")
    print(f"每手风险      : {risk_per_lot:,.2f} (账户币/手)")
    print(f"合约规模      : {contract:,.0f} / 手")
    print(f"报价币→账户币 : {quote_rate}")
    print("-" * 52)
    print(f"建议手数      : {lots:.2f} 手")
    print(f"  (取整向下到 0.01 手: {math.floor(lots*100)/100:.2f} 手)")
    print(f"  (取整向下到 0.1 手 : {math.floor(lots*10)/10:.1f} 手)")
    print("=" * 52)
    print("纪律提示: 单笔风险 ≤1%, 回撤后降至 0.5%; 止损放结构外。")

if __name__ == "__main__":
    main()
