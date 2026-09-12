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

凯利融合(v2.3 新增, --winrate + --payoff 启用):
    f*          = (p × b − q) / b   # 全凯利最优仓位比例; p=胜率, q=1−p, b=盈亏比
    半凯利      = f* / 2            # 实战推荐档(降低波动与最大回撤)
    三分之一    = f* / 3            # 保守档
    有效风险%   = min(纪律风险%, 凯利档%, 1% 硬封顶)   # 三重约束取最小
    说明: 凯利给"理论最优", 纪律给"硬约束", 二者取小——小账户真实约束通常是 1% 纪律而非凯利。
          若 f* ≤ 0(负期望/无优势), 直接拒绝开仓。

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

    # 凯利融合:胜率 62.5% + 盈亏比 1.85,半凯利与 1% 纪律取小
    python position_size.py --equity 574.23 --risk 1 --stop 116 --contract 1000 \
        --winrate 62.5 --payoff 1.85 --kelly-mode half
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
    ap.add_argument("--winrate", type=float, default=None,
                    help="历史胜率 p(%%), 配合 --payoff 启用凯利融合")
    ap.add_argument("--payoff", type=float, default=None,
                    help="平均盈亏比 b(如 1.85), 配合 --winrate 启用凯利融合")
    ap.add_argument("--kelly-mode", type=str, default="half",
                    choices=["full", "half", "third"],
                    help="凯利采用档位: full=全凯利, half=半凯利(默认·实战推荐), third=三分之一凯利")
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

    # ---------- 凯利融合 (v2.3): 胜率+盈亏比 → 凯利档 → 与纪律风险%取小 ----------
    kelly = None
    eff_risk = args.risk
    if (args.winrate is None) != (args.payoff is None):
        ap.error("凯利融合需同时提供 --winrate 与 --payoff")
    if args.winrate is not None and args.payoff is not None:
        p = args.winrate / 100.0
        b = args.payoff
        q = 1.0 - p
        f_full = (p * b - q) / b if b > 0 else 0.0
        f_full = max(f_full, 0.0)
        f_half = f_full / 2.0
        f_third = f_full / 3.0
        if f_full <= 0:
            print("=" * 52)
            print(f"凯利否决: f* = (p·b−q)/b = {f_full*100:.2f}% ≤ 0 → 负期望/无优势系统, 任何仓位都是错的。")
            print("结论: 建议手数 0.00 手 (不开仓)。")
            print("=" * 52)
            return
        f_use = {"full": f_full, "half": f_half, "third": f_third}[args.kelly_mode]
        kelly_pct = f_use * 100.0
        # 三重约束取最小: 用户纪律风险% / 凯利档% / 1% 硬封顶
        eff_risk = min(args.risk, kelly_pct, 1.0)
        # 判定约束来源
        if eff_risk == 1.0 and args.risk >= 1.0 and kelly_pct >= 1.0:
            binder = "1% 硬纪律"
        elif kelly_pct <= args.risk and kelly_pct <= 1.0:
            binder = f"凯利({args.kelly_mode})"
        else:
            binder = "纪律风险%"
        kelly = (f_full, f_half, f_third, kelly_pct, binder)

    risk_amount = args.equity * (eff_risk / 100.0)
    risk_per_lot = stop * contract * quote_rate          # 账户币/每手
    if risk_per_lot <= 0:
        ap.error("止损距离必须为正数")
    lots = risk_amount / risk_per_lot

    print("=" * 52)
    print(f"账户权益      : {args.equity:,.2f}")
    if kelly:
        f_full, f_half, f_third, kelly_pct, binder = kelly
        print("凯利融合      : f*=(p·b−q)/b")
        print(f"  全凯利 f*    : {f_full*100:.2f}%")
        print(f"  半凯利 f*/2  : {f_half*100:.2f}%  (实战推荐)")
        print(f"  三分之一 f*/3: {f_third*100:.2f}%")
        print(f"  采用档 {args.kelly_mode} → 凯利仓位 {kelly_pct:.2f}% 账户")
        print(f"有效风险%     : {eff_risk:.3f}%  = min(纪律 {args.risk}%, 凯利 {kelly_pct:.2f}%, 硬封顶 1%) ← {binder} 约束")
    else:
        print(f"单笔风险      : {args.risk}%  →  {risk_amount:,.2f} (账户币)")
    print(f"风险金额      : {risk_amount:,.2f} (账户币)")
    print(f"止损距离      : {stop_src}")
    print(f"每手风险      : {risk_per_lot:,.2f} (账户币/手)")
    print(f"合约规模      : {contract:,.0f} / 手")
    print(f"报价币→账户币 : {quote_rate}")
    print("-" * 52)
    print(f"建议手数      : {lots:.2f} 手")
    print(f"  (取整向下到 0.01 手: {math.floor(lots*100)/100:.2f} 手)")
    print(f"  (取整向下到 0.1 手 : {math.floor(lots*10)/10:.1f} 手)")
    print("=" * 52)
    if kelly:
        print("凯利提示: ①半凯利是实战最优解(降波动/回撤); ②单笔风险≤1%是硬纪律, 凯利超1%以1%为准; ③凯利只适用正期望系统(胜率×盈亏比>1)。")
    print("纪律提示: 单笔风险 ≤1%, 回撤后降至 0.5%; 止损放结构外。")

if __name__ == "__main__":
    main()
