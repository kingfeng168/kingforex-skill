#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货分析工具:期现结构分析(基差/期限结构) + 期货价差分析(跨期/跨品种)。

仅依赖 Python 标准库。可纯输入计算,亦可 --pull 直连新数据源(iTick / goldprice.dev /
OilPriceAPI)实时取数后分析。

=== 一、期现结构分析(spot-futures structure / basis) ===
输入:现货价 spot + N 个期货合约定价(含到期天数或年份)。
输出每个合约:
  - 基差 basis = spot − futures(>0 该合约处于 back; <0 处于 contango)
  - 基差率 = basis / spot × 100%
  - 年化carry = (futures − spot)/spot × 365/days × 100%(>0 贴水市场/持有成本; <0 升水/便利收益)
  - 相邻合约斜率(年化%)→ 整体曲线形态 contango / backwardation
交易含义:contango 利于"卖近买远"的滚动收益为负(展期亏损);backwardation 利于"买近卖远"。

=== 二、期货价差分析(futures spread) ===
1) 跨期价差(calendar spread):near 与 far 两合约价差 = near − far。
   >0 = 该段 back(近月溢价); <0 = contango(远月溢价)。
2) 跨品种价差(inter-commodity):如 WTI − Brent。可配合历史序列算 z-score 定位偏离。

用法示例:
  # 期现结构:现货金 2400,期货 GC 2405=2410(30天) GC 2408=2425(120天)
  python futures_analysis.py basis --spot 2400 --fut 2405:2410:30 --fut 2408:2425:120
  # 跨期价差:近月 2410 远月 2425
  python futures_analysis.py spread --near M1:2410 --far M2:2425
  # 跨品种:WTI vs Brent(可传 --series 历史CSV算 z)
  python futures_analysis.py spread --a WTI:91.97 --b BRENT:95.98
  # 直连实时:原油 WTI-Brent 价差(OilPriceAPI)
  python futures_analysis.py pull --kind oil
  # 直连实时:黄金期现结构(goldprice.dev 现货 + iTick GC 期货)
  python futures_analysis.py pull --kind gold
"""
import os
import sys
import json
import argparse
from datetime import datetime, timezone


def _parse_fut(s):
    """LABEL:PRICE[:DAYS] 或 LABEL:PRICE[:YYYY-MM-DD]。返回 (label, price, days)。"""
    parts = s.split(":")
    label = parts[0]
    price = float(parts[1])
    if len(parts) >= 3 and parts[2]:
        try:
            days = float(parts[2])
        except ValueError:
            # 视为日期
            d = datetime.strptime(parts[2], "%Y-%m-%d")
            days = (d - datetime.now()).days
        # 若 >1000 视为"年"(如 0.25 年),转天数
        if days > 1000:
            days = days * 365.0
    else:
        days = 0.0
    return label, price, days


def _classify(slope_pct):
    if slope_pct > 0.5:
        return "contango(升水/远期溢价)"
    if slope_pct < -0.5:
        return "backwardation(贴水/近月溢价)"
    return "flat(平"


def analyze_basis(spot, futs):
    """futs: [(label, price, days), ...] 按 days 升序。"""
    futs = sorted(futs, key=lambda x: x[2])
    rows = []
    prev = None
    for label, price, days in futs:
        basis = spot - price
        basis_pct = basis / spot * 100 if spot else 0
        carry = (price - spot) / spot * (365.0 / days) * 100 if (spot and days > 0) else None
        row = {
            "contract": label, "futures": price, "days_to_maturity": days,
            "basis": round(basis, 4), "basis_pct": round(basis_pct, 4),
            "annualized_carry_pct": round(carry, 4) if carry is not None else None,
            "state": "back(贴水)" if basis > 0 else ("contango(升水)" if basis < 0 else "par(平价)"),
        }
        if prev is not None:
            p_label, p_price, p_days = prev
            ddays = days - p_days
            slope_pct = (price - p_price) / p_price * (365.0 / ddays) * 100 if (p_price and ddays > 0) else 0
            row["segment_slope_annual_pct"] = round(slope_pct, 4)
            row["segment_state"] = _classify(slope_pct)
        else:
            row["segment_slope_annual_pct"] = None
            row["segment_state"] = None
        rows.append(row)
        prev = (label, price, days)
    # 整体形态:首末合约斜率
    overall = None
    if len(rows) >= 2:
        a, b = futs[0], futs[-1]
        ddays = b[2] - a[2]
        slope = (b[1] - a[1]) / a[1] * (365.0 / ddays) * 100 if (a[1] and ddays > 0) else 0
        overall = {"first": a[0], "last": b[0], "curve_slope_annual_pct": round(slope, 4),
                   "structure": _classify(slope)}
    return {"spot": spot, "contracts": rows, "overall": overall}


def analyze_spread(near_label, near_price, far_label, far_price, series=None):
    spread = near_price - far_price
    ratio = near_price / far_price if far_price else None
    res = {
        "near": {"label": near_label, "price": near_price},
        "far": {"label": far_label, "price": far_price},
        "spread": round(spread, 4),
        "ratio": round(ratio, 4) if ratio else None,
        "type": "calendar(跨期)" if _same_family(near_label, far_label) else "inter-commodity(跨品种)",
        "state": ("back(近月溢价)" if spread > 0 else ("contango(远月溢价)" if spread < 0 else "par")),
    }
    if series:
        import statistics
        vals = [float(x) for x in series]
        mean = statistics.mean(vals)
        sd = statistics.pstdev(vals) if len(vals) > 1 else 0
        z = (spread - mean) / sd if sd else 0
        res["zscore_vs_history"] = round(z, 3)
        res["history_mean"] = round(mean, 4)
        res["history_sd"] = round(sd, 4)
        res["read"] = "偏高(考虑空 near/多 far)" if z > 1.5 else ("偏低(考虑多 near/空 far)" if z < -1.5 else "中性区间")
    return res


def _same_family(a, b):
    # 粗略:标签数字/字母前缀一致视为同品种跨期
    return a.split()[0][:3].upper() == b.split()[0][:3].upper()


def _pull_oil():
    """实时原油:WTI vs Brent(OilPriceAPI)。"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import oilprice_fetch as op
    key = op._read_local_key()
    if not key:
        return {"_error": "no_key", "detail": "缺 OilPriceAPI key(.oilprice_key / --api-key / OILPRICEAPI_KEY)"}
    wti = op.fetch_latest(["WTI_USD"], key)
    brent = op.fetch_latest(["BRENT_CRUDE_USD"], key)
    if isinstance(wti, dict) and "_error" in wti:
        return wti
    if isinstance(brent, dict) and "_error" in brent:
        return brent
    wp = wti[0]["price"]; bp = brent[0]["price"]
    sp = analyze_spread("WTI_USD", wp, "BRENT_CRUDE_USD", bp)
    sp["note"] = "WTI−Brent 价差(美元/桶);常态为负(WTI 贴水),极端负值常对应美国增产/库欣累库。"
    sp["as_of"] = wti[0].get("created_at")
    return sp


def _pull_gold():
    """实时黄金:现货(goldprice.dev) vs 期货 GC(iTick)。"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import goldprice_fetch as gp
    import itick_fetch as it
    gkey = gp._read_local_key()
    spot = None
    if gkey:
        d = gp.fetch("XAU-USD-SPOT", gkey)
        if isinstance(d, dict) and "price" in d:
            spot = float(d["price"])
    ikey = it._read_local_key()
    fut = None
    if ikey:
        fd = it._get("/future/quote", ikey, it.DEFAULT_BASE, {"region": "US", "code": "GC"})
        if isinstance(fd, dict) and "data" in fd:
            fut = float(fd["data"].get("p") or fd["data"].get("price"))
    if spot is None or fut is None:
        miss = []
        if spot is None: miss.append("现货(goldprice.dev 未取到/Cloudflare 拦截)")
        if fut is None: miss.append("期货 GC(iTick 未取到/限频)")
        return {"_error": "partial", "detail": "; ".join(miss),
                "spot": spot, "futures_GC": fut,
                "hint": "可改用 basis 子命令手动传入 --spot / --fut"}
    res = analyze_basis(spot, [("GC_front", fut, 30)])
    res["note"] = "黄金期现结构:单一近月合约视角(基差=现货−GC期货);完整曲线需多合约 --fut 输入。"
    res["as_of"] = datetime.now(timezone.utc).isoformat()
    return res


def main():
    p = argparse.ArgumentParser(description="期货分析:期现结构 + 期货价差")
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("basis", help="期现结构/基差")
    pb.add_argument("--spot", type=float, required=True)
    pb.add_argument("--fut", action="append", required=True, help="LABEL:PRICE[:DAYS|YYYY-MM-DD],可多次")
    pb.add_argument("--json", action="store_true")

    ps = sub.add_parser("spread", help="期货价差(跨期/跨品种)")
    ps.add_argument("--near", help="LABEL:PRICE")
    ps.add_argument("--far", help="LABEL:PRICE")
    ps.add_argument("--a", help="跨品种 A: LABEL:PRICE")
    ps.add_argument("--b", help="跨品种 B: LABEL:PRICE")
    ps.add_argument("--series", help="历史价差 CSV/文本(每行一个值)算 z-score")
    ps.add_argument("--json", action="store_true")

    pp = sub.add_parser("pull", help="直连实时数据源分析")
    pp.add_argument("--kind", required=True, choices=["oil", "gold"])

    args = p.parse_args()

    if args.cmd == "basis":
        futs = [_parse_fut(x) for x in args.fut]
        res = analyze_basis(args.spot, futs)
    elif args.cmd == "spread":
        if args.near and args.far:
            nl, np_ = args.near.split(":"); fl, fp_ = args.far.split(":")
            series = _load_series(args.series) if args.series else None
            res = analyze_spread(nl, float(np_), fl, float(fp_), series)
        elif args.a and args.b:
            al, ap = args.a.split(":"); bl, bp = args.b.split(":")
            series = _load_series(args.series) if args.series else None
            res = analyze_spread(al, float(ap), bl, float(bp), series)
        else:
            print("需提供 --near/--far 或 --a/--b"); sys.exit(1)
    elif args.cmd == "pull":
        res = _pull_oil() if args.kind == "oil" else _pull_gold()
    else:
        sys.exit(1)

    if isinstance(res, dict) and "_error" in res:
        print(f"[提示] {res['_error']}: {res.get('detail')}")
        if "hint" in res: print("  " + res["hint"])
        print(json.dumps({k: v for k, v in res.items() if k != "_error"}, ensure_ascii=False, indent=2))
        sys.exit(0)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if not (args.cmd == "basis" and args.json) and not (args.cmd == "spread" and args.json):
        _print_summary(args.cmd, res)


def _load_series(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().strip(",")
            if line and line.replace(".", "").replace("-", "").isdigit():
                out.append(float(line))
    return out


def _print_summary(cmd, res):
    print("\n--- 研判摘要 ---")
    if cmd == "basis":
        ov = res.get("overall")
        if ov:
            print(f"曲线形态: {ov['structure']} (首 {ov['first']}→末 {ov['last']} 年化斜率 {ov['curve_slope_annual_pct']}%)")
        for c in res["contracts"]:
            print(f"  {c['contract']}: 期货={c['futures']} 基差={c['basis']}({c['basis_pct']}%) {c['state']}"
                  + (f" 年化carry={c['annualized_carry_pct']}%" if c['annualized_carry_pct'] is not None else ""))
    elif cmd == "spread":
        print(f"类型: {res['type']}  价差={res['spread']}  状态={res['state']}")
        if "zscore_vs_history" in res:
            print(f"  z={res['zscore_vs_history']} (均值 {res['history_mean']}, sd {res['history_sd']}) → {res['read']}")
        if "note" in res:
            print("  " + res["note"])


if __name__ == "__main__":
    main()
