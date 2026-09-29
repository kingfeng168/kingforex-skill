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

名义本金口径(2026-09-28 修复):
  旧版把"每手名义本金"硬编码为 XAUUSD=200000 / XAGUSD=140000 / WTI=75000(隐含金价
  $2000、银价 $28),而实际报价已到金 $4300 / 银 $64 / WTI $97,导致黄金风险金额被低估
  约 2.2 倍、白银约 2.4 倍。现改为 名义本金 = 实时价 × 每标准手合约单位,并遵守本技能
  「绝不杜撰价格」铁律:取不到价且未用 --price 指定时**直接报错**,不用内置假价顶替。

  价格来源优先级:--price SYM=VAL(手工,最高) > 免费源自动取数(gold-api 金/银、
  Frankfurter 外汇) > 报错。--no-fetch 可禁用自动取数。
"""
import argparse
import json
import sys
import urllib.request

# 中文 Windows(cp936 控制台)下,输出含 ⚠/✓ 等字符会抛 UnicodeEncodeError 并中断
# (2026-09-28 修复)。改为不可编码字符降级替换,不改变控制台原生编码,中文照常显示。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

# 品种档案: (资产类别, usd_beta, 每标准手合约单位)
#   usd_beta : 做多1手对美元净方向的系数(+1 做多=做多美元, -1 做多=做空美元, -0.5 商品类部分)
#   合约单位 : 每标准手的标的单位数(FX=100000 基础货币, XAU=100oz, XAG=5000oz,
#              WTI/Brent=1000桶, HG=25000磅);名义本金 = 实时价 × 合约单位
INSTRUMENT_PROFILE = {
    "xauusd": ("贵金属", -1.0, 100.0),
    "xagusd": ("贵金属", -1.0, 5000.0),
    "wti":    ("原油",  -0.5, 1000.0),
    "brent":  ("原油",  -0.5, 1000.0),
    "hg":     ("铜",    -0.5, 25000.0),
    "eurusd": ("外汇",  -1.0, 100000.0),
    "gbpusd": ("外汇",  -1.0, 100000.0),
    "audusd": ("外汇",  -1.0, 100000.0),
    "nzdusd": ("外汇",  -1.0, 100000.0),
    "usdjpy": ("外汇",  +1.0, 100000.0),
    "usdcad": ("外汇",  +1.0, 100000.0),
    "usdchf": ("外汇",  +1.0, 100000.0),
    "usdcnh": ("外汇",  +1.0, 100000.0),
    # 2026-09-28 新增:本技能主力品种(原缺失 → parse_positions 直接 ValueError 抛栈)
    "audjpy": ("外汇",  -1.0, 100000.0),
    "nzdjpy": ("外汇",  -1.0, 100000.0),
}

# 压力测试情景: 各资产类别在该情景下的价格冲击 (%)
STRESS_SCENARIOS = {
    "美股单日 -5% (Risk-off)": {"外汇": -1.5, "贵金属": +2.0, "原油": -4.0, "铜": -3.0},
    "FOMC 意外加息 50bp":      {"外汇": +1.5, "贵金属": -2.5, "原油": -1.5, "铜": -1.0},
    "油价单日 -10%":           {"外汇":  0.0, "贵金属": +0.5, "原油": -10.0, "铜": -2.0},
}


# ---------------- 价格解析(名义本金用) ----------------
def price_symbol_for(sym):
    """该品种名义本金折算所需的报价标的。

    - USD 为基础货币(usdjpy/usdcad/...):名义本金固定 = 合约单位 USD,无需价格
    - 交叉盘(audjpy/nzdjpy):折算基础货币的美元价 → AUDUSD / NZDUSD
    - 其余(含 xxxusd 与贵金属/原油):即其自身报价
    """
    s = sym.upper()
    if s.startswith("USD") and len(s) == 6:
        return None
    if s.endswith("JPY") and len(s) == 6:
        return s[:3] + "USD"
    return s


def _http_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "kingforex-skill/2.10.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_price(price_sym):
    """尽力从免费源取价:贵金属走 gold-api.com,外汇走 Frankfurter(ECB)。失败返回 None。"""
    s = price_sym.upper()
    try:
        if s in ("XAUUSD", "XAGUSD"):
            d = _http_json("https://api.gold-api.com/price/" + s[:3])
            return float(d["price"])
    except Exception:
        pass
    try:
        if s.endswith("USD") and len(s) == 6:
            base = s[:3]
            d = _http_json("https://api.frankfurter.dev/v1/latest?base=USD&symbols=" + base)
            rate = float(d["rates"][base])       # 1 USD = rate BASE
            if rate:
                return 1.0 / rate
    except Exception:
        pass
    return None


def resolve_prices(positions, overrides, allow_fetch):
    """返回 {price_sym: (价格, 来源)};取不到的标的不进字典,由 main 统一报错。"""
    need = []
    for p in positions:
        ps = price_symbol_for(p["sym"])
        if ps and ps not in need:
            need.append(ps)
    out = {}
    for ps in need:
        key = ps.upper()
        if key in overrides:
            out[ps] = (overrides[key], "手工 --price")
            continue
        if allow_fetch:
            px = fetch_price(ps)
            if px is not None:
                out[ps] = (px, "实时取数")
    return out


def notional_usd(sym, price):
    """每标准手名义本金(USD)。USD 基础货币品种无需价格。"""
    _cls, _beta, units = INSTRUMENT_PROFILE[sym]
    if price_symbol_for(sym) is None:
        return units
    if price is None:
        return None
    return units * price


# ══════════════════════════════════════════════════════════════════════════
# 开仓前组合闸门(2026-09-28 新增)
# ══════════════════════════════════════════════════════════════════════════
# 修复动因: 本技能此前只有"事后净方向计算", 纪律里写着"禁止多黄金+多澳元+多原油
# (单一美元空头)"却**没有任何脚本在开仓前拦截**。现提供 --check-new:
# 把待开仓与现有持仓合并后逐条判定, 不通过则 exit 3, 可直接作为 agent 的下单前闸门。
#
# 阈值一律取 calc_engine(唯一事实来源), 取不到时用下面同值兜底。
GATE_FALLBACK = {"single_risk_pct": 1.0,     # 单笔风险硬上限
                 "small_account_pct": 0.5,   # 小账户保守口径
                 "portfolio_risk_pct": 5.0,  # 组合总风险上限
                 "net_usd_warn": 2.0,        # 净美元 β 汇总 提示线
                 "net_usd_fail": 3.0,        # 净美元 β 汇总 否决线
                 "same_side_warn": 3,        # 同向暴露笔数 提示线
                 "same_side_fail": 4}        # 同向暴露笔数 否决线


def _gate_thresholds():
    t = dict(GATE_FALLBACK)
    try:
        import calc_engine as CE
        t["single_risk_pct"] = float(getattr(CE, "RISK_HARD_CAP", t["single_risk_pct"]))
        t["portfolio_risk_pct"] = float(getattr(CE, "PORTFOLIO_CAP", t["portfolio_risk_pct"]))
    except Exception:
        pass
    return t


def _row_metrics(p, prices, equity):
    """单笔的 {symbol, notional, risk_pct, beta_contrib, price_src}。"""
    ps = price_symbol_for(p["sym"])
    px, src = prices.get(ps, (None, "固定(USD 基础货币)")) if ps else (None, "固定(USD 基础货币)")
    notional = notional_usd(p["sym"], px)
    _cls, beta, _u = INSTRUMENT_PROFILE[p["sym"]]
    risk_pct = None
    if p.get("stop_pct") is not None and equity:
        risk_pct = abs(p["size"]) * notional * (p["stop_pct"] / 100.0) / equity * 100.0
    return {"symbol": p["sym"].upper(), "side": p["side"], "size": p["size"],
            "notional": notional, "beta": p["sign"] * beta * p["size"],
            "risk_pct": risk_pct, "price_src": src}


def check_gate(equity, existing, candidate, prices, t=None):
    """开仓前闸门: 返回 {verdict, exit_code, checks:[{level,code,text}], suggest_lots}。

    verdict ∈ PASS / REJECT；exit_code: 0=PASS, 3=REJECT。
    candidate 可为 None(只检查现有组合)。
    """
    t = t or _gate_thresholds()
    rows = [_row_metrics(p, prices, equity) for p in existing]
    if candidate is not None:
        rows.append(_row_metrics(candidate, prices, equity))
    checks = []

    def add(level, code, text):
        checks.append({"level": level, "code": code, "text": text})

    # 1) 单笔风险(仅对带止损% 的仓位可算)
    known = [r for r in rows if r["risk_pct"] is not None]
    if candidate is not None and candidate.get("stop_pct") is None:
        add("warn", "NO_STOP",
            "待开仓未提供止损%%, 无法核算单笔风险 —— 请用 品种:方向:手数:止损%% 形式重试。")
    if candidate is not None and candidate.get("stop_pct") is not None:
        cr = rows[-1]["risk_pct"]
        if cr > t["single_risk_pct"] + 1e-9:
            add("fail", "OVER_RISK",
                "单笔风险 %.2f%% > 硬上限 %.1f%%（待开仓 %s %s %.2f 手）"
                % (cr, t["single_risk_pct"], candidate["sym"].upper(), candidate["side"], candidate["size"]))
        elif cr > t["small_account_pct"] + 1e-9:
            add("warn", "HIGH_RISK",
                "单笔风险 %.2f%% 在 %.1f%%–%.1f%% 区间, 小账户应取下限。"
                % (cr, t["small_account_pct"], t["single_risk_pct"]))
        else:
            add("pass", "RISK_OK", "单笔风险 %.2f%% ≤ %.1f%%。" % (cr, t["single_risk_pct"]))

    # 2) 组合总风险
    if known:
        tot = sum(r["risk_pct"] for r in known)
        if tot > t["portfolio_risk_pct"] + 1e-9:
            add("fail", "OVER_PORTFOLIO",
                "组合总风险 %.2f%% > 上限 %.1f%%（含待开仓）。" % (tot, t["portfolio_risk_pct"]))
        elif tot > t["portfolio_risk_pct"] * 0.8:
            add("warn", "NEAR_PORTFOLIO",
                "组合总风险 %.2f%% 已接近上限 %.1f%%。" % (tot, t["portfolio_risk_pct"]))
        else:
            add("pass", "PORTFOLIO_OK",
                "组合总风险 %.2f%% ≤ %.1f%%。" % (tot, t["portfolio_risk_pct"]))
    else:
        add("warn", "NO_RISK_DATA", "没有任何仓位带止损%%, 组合总风险无法核算。")

    # 3) 净美元方向暴露(相关性陷阱)
    net = sum(r["beta"] for r in rows)
    if abs(net) >= t["net_usd_fail"]:
        add("fail", "USD_CONCENTRATION",
            "净美元 β 汇总 %.2f 已达否决线 %.1f —— 多笔同向宏观暴露(如多金+多澳+多油=单一美元空头)。"
            % (net, t["net_usd_fail"]))
    elif abs(net) >= t["net_usd_warn"]:
        add("warn", "USD_TILT",
            "净美元 β 汇总 %.2f 超过提示线 %.1f, 需降低总仓位或加对冲。" % (net, t["net_usd_warn"]))
    else:
        add("pass", "USD_OK", "净美元 β 汇总 %.2f 在容忍范围内。" % net)

    # 4) 同向暴露笔数
    neg = sum(1 for r in rows if r["beta"] < 0)
    pos = sum(1 for r in rows if r["beta"] > 0)
    same = max(neg, pos)
    if same >= t["same_side_fail"]:
        add("fail", "SAME_SIDE",
            "同向暴露 %d 笔 ≥ 否决线 %d（做空美元 %d / 做多美元 %d）。"
            % (same, t["same_side_fail"], neg, pos))
    elif same >= t["same_side_warn"]:
        add("warn", "SAME_SIDE_WARN",
            "同向暴露 %d 笔已达提示线 %d（做空美元 %d / 做多美元 %d）。"
            % (same, t["same_side_warn"], neg, pos))
    else:
        add("pass", "SAME_SIDE_OK", "同向暴露 %d 笔, 分散度可接受。" % same)

    # 5) 建议最大手数(按硬上限反推, 需要止损%)
    suggest = None
    if candidate is not None and candidate.get("stop_pct"):
        r = rows[-1]
        per_lot_risk = abs(r["notional"]) * (candidate["stop_pct"] / 100.0)
        if per_lot_risk > 0:
            budget = equity * t["single_risk_pct"] / 100.0
            raw = budget / per_lot_risk
            suggest = max(0.0, int(raw * 100) / 100.0)
            add("info", "SUGGEST_LOTS",
                "按单笔 %.1f%% 上限反推, 该品种/止损距离下最大可开 **%.2f 手**（当前 %.2f 手）。"
                % (t["single_risk_pct"], suggest, candidate["size"]))

    fails = [c for c in checks if c["level"] == "fail"]
    verdict = "REJECT" if fails else "PASS"
    return {"verdict": verdict, "exit_code": 3 if fails else 0,
            "checks": checks, "suggest_lots": suggest, "net_usd": net,
            "total_risk_pct": (sum(r["risk_pct"] for r in known) if known else None)}


def _print_gate(gate):
    print()
    print("=" * 62)
    print("开仓前组合闸门 (--check-new)")
    print("-" * 62)
    icon = {"pass": "✓", "warn": "⚠", "fail": "✗", "info": "·"}
    for c in gate["checks"]:
        print("  %s [%s] %s" % (icon.get(c["level"], "?"), c["code"], c["text"]))
    print("-" * 62)
    if gate["verdict"] == "PASS":
        print("  结论: ✓ 通过 —— 允许建仓")
    else:
        print("  结论: ✗ 拒绝 —— 存在 %d 条否决项, 禁止建仓"
              % sum(1 for c in gate["checks"] if c["level"] == "fail"))
    print("=" * 62)



def parse_positions(items):
    out = []
    for s in items:
        parts = s.split(":")
        if len(parts) < 3:
            raise ValueError(f"持仓格式错误: {s} (应为 品种:方向:手数[:止损%])")
        sym = parts[0].lower()
        side = parts[1].lower()
        try:
            size = float(parts[2])
            stop_pct = float(parts[3]) if len(parts) > 3 and parts[3] else None
        except ValueError:
            raise ValueError(f"手数/止损%%须为数字: {s}")
        if side not in ("long", "short"):
            raise ValueError(f"方向须为 long/short: {s}")
        if sym not in INSTRUMENT_PROFILE:
            raise ValueError(f"未登记品种: {sym} (可用: {', '.join(sorted(INSTRUMENT_PROFILE))})")
        sign = 1.0 if side == "long" else -1.0
        out.append({"sym": sym, "side": side, "size": size, "sign": sign, "stop_pct": stop_pct})
    return out


def main():
    ap = argparse.ArgumentParser(description="组合净暴露与相关性风险计算器")
    ap.add_argument("--equity", type=float, required=True, help="账户权益(USD)")
    ap.add_argument("--positions", nargs="+", required=True, help="持仓列表")
    ap.add_argument("--max-risk", type=float, default=5.0,
                    help="总风险暴露上限 %% (基于止损%%), 默认 5")
    ap.add_argument("--price", action="append", default=[],
                    help="手工指定折算价, 形如 --price XAUUSD=4310 --price AUDUSD=0.663")
    ap.add_argument("--no-fetch", action="store_true", help="禁用自动取数(只用 --price)")
    ap.add_argument("--check-new", action="append", default=[], metavar="POS",
                    help="开仓前闸门: 待开仓 品种:方向:手数[:止损%%], 可重复。"
                         "通过 exit 0, 否决 exit 3")
    args = ap.parse_args()

    overrides = {}
    for item in args.price:
        if "=" not in item:
            print(f"[参数错误] --price 须为 SYM=VALUE 形式: {item}")
            return 2
        k, v = item.split("=", 1)
        try:
            overrides[k.strip().upper()] = float(v)
        except ValueError:
            print(f"[参数错误] --price 数值无效: {item}")
            return 2

    try:
        positions = parse_positions(args.positions)
    except ValueError as e:
        print(f"[参数错误] {e}")
        return 2

    prices = resolve_prices(positions, overrides, not args.no_fetch)
    missing = []
    for p in positions:
        ps = price_symbol_for(p["sym"])
        if ps and ps not in prices:
            missing.append(ps)
    if missing:
        print("[缺少折算价] 以下品种需要实时价才能计算名义本金/风险, "
              "但自动取数失败或已被 --no-fetch 禁用:")
        for m in sorted(set(missing)):
            print(f"    --price {m}=<价格>")
        print("  (本工具遵守「绝不杜撰价格」铁律, 不用内置假价顶替; 请手工传入或检查网络)")
        return 3

    print("=" * 62)
    print("持仓明细")
    print("-" * 62)
    net_usd = 0.0
    gross_notional = 0.0
    total_risk = 0.0
    has_risk = False
    beta_signs = []
    for p in positions:
        cls, beta, _units = INSTRUMENT_PROFILE[p["sym"]]
        ps = price_symbol_for(p["sym"])
        px, src = prices.get(ps, (None, "固定(USD 基础货币)")) if ps else (None, "固定(USD 基础货币)")
        notional = notional_usd(p["sym"], px)
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
        px_note = "" if ps is None else f"  [{ps} {px:g} · {src}]"
        print(f"  {p['sym'].upper():8} {p['side']:5} {p['size']:>6.2f}手  "
              f"名义${notional:,.0f}  USDβ={contrib:+.2f}{risk_note}{px_note}")
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
            cls, _beta, _units = INSTRUMENT_PROFILE[p["sym"]]
            ps = price_symbol_for(p["sym"])
            px = prices.get(ps, (None, None))[0] if ps else None
            notional = notional_usd(p["sym"], px)
            shock = shocks.get(cls, 0.0)
            pnl += p["sign"] * p["size"] * notional * (shock / 100.0)
        pnl_pct = pnl / args.equity * 100.0
        print(f"  {name:30} 组合≈{pnl_pct:+.2f}%")
    print("=" * 62)
    print("纪律提示: 同时持仓 ≤2–3 个高相关品种; 相关性集中时主动降仓。")

    # ── 开仓前闸门 ──
    if args.check_new:
        try:
            cands = parse_positions(args.check_new)
        except ValueError as e:
            print(f"[参数错误] --check-new: {e}")
            return 2
        # 待开仓所需的折算价也要解析到
        cand_prices = resolve_prices(cands, overrides, not args.no_fetch)
        for k, v in cand_prices.items():
            prices.setdefault(k, v)
        allp = parse_positions(args.positions)
        gate = check_gate(args.equity, allp, cands[0] if cands else None, prices)
        _print_gate(gate)
        return gate["exit_code"]

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
