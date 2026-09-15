#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sl_tp_evaluate.py — 止损 / 止盈合理性评估(持仓管理与离场纪律辅助, kingforex-skill 内置)

用途: 给定一笔持仓的 方向 / 入场 / 止损(SL) / 止盈(TP) / 当前价(可经 --symbol 自动取实时价),
      输出一套可量化的"止损止盈是否合理"判定,直接服务框架的"持仓管理 / 离场 / 纪律"环节,
      重点防止两类典型错误:
        ① 反向移动止损(盈利单把 SL 从盈利区移回入场上方/亏损侧,回吐全部浮盈);
        ② 风险收益比(R:R)崩塌(用极大风险去博极小剩余空间)。

纯标准库;当前价可选经 AllRatesToday 实时取(需 scripts/.art_key),失败不崩溃、仅提示降级。

核心指标:
  - pip 距离: 入场→SL、入场→TP、当前→SL、当前→TP
  - 初始 R:R = |入场−TP| / |入场−SL|
  - 剩余 R:R = |当前−TP| / |当前−SL|(持仓已盈利时这才是真正要盯的 R:R)
  - 浮盈(open P&L, pips 与账户货币)
  - 单笔美元风险(对比 2% 铁律): 需 --equity + --lot
  - SL 方向校验: SELL 的止损应在入场上方(防亏),BUY 在下方;盈利后 SL 应"向盈利侧移动"而非反向
  - ATR 宽度 sanity(可选 --atr): SL 距离 < 0.5×ATR 警惕扫损, > 3×ATR 警惕超仓

三级判定:
  REASONABLE   合理
  CAUTION      需谨慎(某一维度偏弱,但不致命)
  UNREASONABLE 不合理(违反纪律或 R:R 明显失衡)

用法:
  # 已知当前价,纯评估
  python sl_tp_evaluate.py --direction SELL --entry 114.573 --sl 114.90 --tp 109.781 \
        --current 110.141 --equity 574 --lot 0.02 --symbol AUDJPY --json

  # 自动取实时价(AUDJPY → AllRatesToday)
  python sl_tp_evaluate.py --direction SELL --entry 114.573 --sl 113.284 --tp 109.781 \
        --symbol AUDJPY --equity 574 --lot 0.02

  # 带 ATR 做宽度 sanity
  python sl_tp_evaluate.py --direction BUY --entry 1.0500 --sl 1.0420 --tp 1.0700 \
        --current 1.0580 --atr 0.0060 --symbol EURUSD --equity 1000 --lot 0.10
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------- pip / 价格工具 ----------------
def pip_scale(symbol):
    if not symbol:
        return None
    s = symbol.upper()
    if "JPY" in s:
        return 0.01
    if "XAU" in s or "XAG" in s:
        return 0.1
    return 0.0001


def to_pips(a, b, pip):
    return abs(a - b) / pip


def profit_side_of(direction, entry, price):
    """price 是否在盈利侧(相对 entry)。"""
    if direction == "SELL":
        return price < entry
    return price > entry  # BUY


def loss_side_of(direction, entry, price):
    if direction == "SELL":
        return price > entry
    return price < entry


# ---------------- 实时价 / USDJPY 取数(最佳努力) ----------------
def _run_fetch(args):
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, "allratestoday_fetch.py")] + args,
            capture_output=True, text=True, timeout=40,
        )
        if r.returncode != 0:
            return None
        return r.stdout
    except Exception:
        return None


def fetch_current(symbol):
    if not symbol or len(symbol) != 6:
        return None
    base, quote = symbol[:3], symbol[3:]
    out = _run_fetch(["--source", base, "--target", quote, "--json"])
    if not out:
        return None
    for line in out.split("\n"):
        line = line.strip()
        if line.startswith("["):
            try:
                arr = json.loads(out[out.index("["):])
                if isinstance(arr, list) and arr:
                    return float(arr[0].get("rate"))
            except Exception:
                pass
    return None


def fetch_usdjpy():
    out = _run_fetch(["--source", "USD", "--target", "JPY", "--json"])
    if not out:
        return None
    try:
        arr = json.loads(out[out.index("["):])
        if isinstance(arr, list) and arr:
            return float(arr[0].get("rate"))
    except Exception:
        return None
    return None


def pip_value_account_per_stdlot(symbol, account_ccy, usdjpy):
    """每标准手(100k)1 pip 对应的账户货币价值(仅完整支持账户=USD 或 quote=账户)。"""
    pip = pip_scale(symbol) or 0.0001
    quote_units = 100000.0 * pip  # 每标准手 1 pip 的报价币单位数
    if account_ccy.upper() == "USD":
        if symbol and "JPY" in symbol.upper():
            if not usdjpy:
                return None
            return quote_units / usdjpy  # JPY → USD
        if symbol and ("XAU" in symbol.upper() or "XAG" in symbol.upper()):
            return quote_units  # 报价币即 USD(XAUUSD 等)
        # 其它: 假定报价币为 USD(如 EURUSD)
        return quote_units
    # 非 USD 账户且报价币 != 账户币: 暂不支持精确换算
    if symbol and symbol[3:].upper() == account_ccy.upper():
        return quote_units
    return None


# ---------------- 主评估 ----------------
def evaluate(direction, entry, sl, tp, current, symbol, equity, lot, account_ccy, atr, pip):
    res = {"direction": direction, "entry": entry, "sl": sl, "tp": tp}
    if current is None:
        res["current"] = None
        res["current_source"] = "未提供且自动取数失败"
    else:
        res["current"] = current

    flags = []  # (level, code, text)  level: severe / warn / info

    # 方向校验
    if direction not in ("BUY", "SELL"):
        return {"error": "direction 必须为 BUY 或 SELL"}

    # pip 刻度
    if pip is None:
        pip = pip_scale(symbol)
    if pip is None:
        return {"error": "无法推断 pip 刻度: 请提供 --symbol 或 --pip"}
    res["pip_scale"] = pip

    # 基础距离
    init_risk = to_pips(entry, sl, pip)
    init_reward = to_pips(entry, tp, pip)
    res["init_risk_pips"] = round(init_risk, 1)
    res["init_reward_pips"] = round(init_reward, 1)
    res["init_rr"] = round(init_reward / init_risk, 2) if init_risk > 0 else None

    # SL / TP 方向正确性
    sl_on_loss_side = loss_side_of(direction, entry, sl)
    tp_on_profit_side = profit_side_of(direction, entry, tp)
    res["sl_on_loss_side"] = sl_on_loss_side
    res["tp_on_profit_side"] = tp_on_profit_side
    if not sl_on_loss_side:
        flags.append(("warn", "SL_SIDE",
                      "SL 位于盈利侧(%.1f pip 处): 这是跟踪/锁利止损,不是防亏止损;若价格已越过它则已平仓。" % init_risk))
    if not tp_on_profit_side:
        flags.append(("severe", "TP_SIDE",
                      "TP 不在盈利侧(与方向矛盾): BUY 的 TP 应>入场, SELL 的 TP 应<入场。"))
        return _finish(res, flags, "UNREASONABLE", "TP 方向错误,交易计划不成立。")

    # 当前价相关
    if current is not None:
        # SL 是否已触发(价格已越过 SL)
        if direction == "SELL":
            sl_triggered = (sl > entry and current >= sl) or (sl < entry and current <= sl)
        else:
            sl_triggered = (sl < entry and current <= sl) or (sl > entry and current >= sl)
        res["sl_triggered"] = sl_triggered

        if sl_triggered:
            locked_pips = (to_pips(entry, sl, pip) if profit_side_of(direction, entry, sl)
                           else -to_pips(entry, sl, pip))
            res["sl_triggered_pips"] = round(locked_pips, 1)
            flags.append(("info", "SL_TRIGGERED",
                          "价格已触及 SL(%.5f),持仓已在 %.1f pip %s 处平仓。当前价 %.5f 为平仓后市价,"
                          "剩余 R:R 不再适用——该 SL 已尽到锁利/止损职责。"
                          % (sl, abs(locked_pips), "盈利" if locked_pips > 0 else "亏损", current)))
            # 盈利侧触发=已锁利(合理);亏损侧触发=正常止损(纪律内)。跳过剩余 R:R 与反向 SL 判定。
        else:
            open_pnl = to_pips(entry, current, pip) if profit_side_of(direction, entry, current) else -to_pips(entry, current, pip)
            res["open_pnl_pips"] = round(open_pnl, 1)
            cur_to_sl = to_pips(current, sl, pip)
            cur_to_tp = to_pips(current, tp, pip)
            res["current_to_sl_pips"] = round(cur_to_sl, 1)
            res["current_to_tp_pips"] = round(cur_to_tp, 1)
            res["remaining_rr"] = round(cur_to_tp / cur_to_sl, 2) if cur_to_sl > 0 else None

            # 美元浮盈
            if equity and lot:
                usdjpy = fetch_usdjpy()
                pv = pip_value_account_per_stdlot(symbol, account_ccy, usdjpy)
                if pv is not None:
                    res["pip_value_account"] = round(pv * lot, 4)
                    res["open_pnl_account"] = round(pv * lot * open_pnl, 2)
                    res["open_pnl_pct_equity"] = round(pv * lot * open_pnl / equity * 100, 2) if equity else None

            # 关键纪律: 盈利单反向移动止损(仅当明显放弃浮盈时才判严重)
            if open_pnl > 0 and sl_on_loss_side:
                if cur_to_sl > 3 * cur_to_tp:
                    flags.append(("severe", "REVERSE_SL",
                                  "持仓已盈利 %.1f pip,但 SL(%.1f)在亏损侧且距当前 %.1f pip 是距 TP(%.1f pip)的 %.1f 倍:"
                                  "价格若回到 SL 会回吐全部浮盈并可能转亏。属反向移动止损/未 trailing,违反'盈利后向盈利侧移动 SL'铁律。"
                                  % (open_pnl, sl, cur_to_sl, cur_to_tp, cur_to_sl / cur_to_tp)))
                elif cur_to_sl > cur_to_tp:
                    flags.append(("warn", "TRAIL_SUGGEST",
                                  "持仓盈利 %.1f pip,SL 仍在亏损侧(距当前 %.1f pip > 距 TP %.1f pip): 属正常防亏止损,"
                                  "但可考虑下移 SL 至盈利侧锁定部分利润。" % (open_pnl, cur_to_sl, cur_to_tp)))

            # 剩余 R:R
            if cur_to_sl > 0 and cur_to_tp / cur_to_sl < 0.5:
                flags.append(("severe", "BAD_REMAINING_RR",
                              "剩余 R:R = %.2f (<0.5): 用 %.1f pip 风险去博最后 %.1f pip 收益,风险收益已严重失衡。"
                              % (cur_to_tp / cur_to_sl, cur_to_sl, cur_to_tp)))
            elif cur_to_sl > 0 and cur_to_tp / cur_to_sl < 1.5:
                flags.append(("warn", "LOW_REMAINING_RR",
                              "剩余 R:R = %.2f (偏低, <1.5): 持仓已深盈利时,可考虑下移 SL 锁定利润而非维持远端止损。"
                              % (cur_to_tp / cur_to_sl)))
    else:
        res["remaining_rr"] = None

    # 初始 R:R
    if res.get("init_rr") is not None and res["init_rr"] < 1:
        flags.append(("severe", "BAD_INIT_RR",
                      "初始 R:R = %.2f (<1): 建仓时风险>收益,计划本身不达标(铁律 RR≥1.5 方可交易)。" % res["init_rr"]))
    elif res.get("init_rr") is not None and res["init_rr"] < 1.5:
        flags.append(("warn", "LOW_INIT_RR", "初始 R:R = %.2f (<1.5): 未达框架 RR≥1.5 阈值。" % res["init_rr"]))

    # ATR 宽度 sanity
    if atr:
        atr_pips = to_pips(0, atr, pip)  # atr 已是价格差,转 pip
        if init_risk < 0.5 * atr_pips:
            flags.append(("warn", "SL_TIGHT",
                          "SL 距离 %.1f pip < 0.5×ATR(%.1f): 警惕正常波动被扫损。" % (init_risk, 0.5 * atr_pips)))
        if init_risk > 3 * atr_pips:
            flags.append(("warn", "SL_WIDE",
                          "SL 距离 %.1f pip > 3×ATR(%.1f): 单笔风险偏大,核对仓位是否超重。" % (init_risk, 3 * atr_pips)))

    # 2% 铁律(美元风险)
    if equity and lot:
        usdjpy = fetch_usdjpy()
        pv = pip_value_account_per_stdlot(symbol, account_ccy, usdjpy)
        if pv is not None:
            dollar_risk = pv * lot * init_risk
            res["init_dollar_risk"] = round(dollar_risk, 2)
            res["risk_pct_equity"] = round(dollar_risk / equity * 100, 2)
            if dollar_risk / equity * 100 > 2.0:
                flags.append(("severe", "OVER_RISK",
                              "单笔美元风险 $%.2f = 账户 %.2f%% > 2%% 铁律。" % (dollar_risk, dollar_risk / equity * 100)))
            elif dollar_risk / equity * 100 > 1.0:
                flags.append(("warn", "HIGH_RISK",
                              "单笔美元风险 $%.2f = 账户 %.2f%% (在 1%%–2%% 区间,需确认小账户取下限)。" % (dollar_risk, dollar_risk / equity * 100)))

    # 综合判定
    flags = [[l, c, t] for l, c, t in flags]
    if res.get("sl_triggered") and res.get("sl_triggered_pips", 0) > 0:
        # 已触发且锁利平仓: SL 尽到职责,离场纪律成立;原始建仓 sizing 提示降级为 warn
        for f in flags:
            if f[1] in ("OVER_RISK", "BAD_INIT_RR") and f[0] == "severe":
                f[0] = "warn"
                f[2] += "(已锁利平仓,离场纪律成立;此为原始建仓 sizing 提示,不影响本次 SL 合理性)"
        verdict = "REASONABLE"
    else:
        levels = [f[0] for f in flags]
        if "severe" in levels:
            verdict = "UNREASONABLE"
        elif "warn" in levels:
            verdict = "CAUTION"
        else:
            verdict = "REASONABLE"
    return _finish(res, [tuple(f) for f in flags], verdict, None)


def _finish(res, flags, verdict, hard_msg):
    res["verdict"] = verdict
    res["flags"] = [{"level": l, "code": c, "text": t} for l, c, t in flags]
    if hard_msg:
        res["hard_error"] = hard_msg
    return res


# ---------------- 输出 ----------------
def render_text(r):
    if "error" in r:
        return "[错误] %s" % r["error"]
    lines = []
    lines.append("=== 止损 / 止盈合理性评估 ===")
    lines.append("方向: %s  入场: %.5f  SL: %.5f  TP: %.5f"
                 % (r["direction"], r["entry"], r["sl"], r["tp"]))
    if r.get("current") is not None:
        lines.append("当前: %.5f  (pip 刻度 %.4f)" % (r["current"], r["pip_scale"]))
    else:
        lines.append("当前: %s" % r.get("current_source"))
    lines.append("")
    lines.append("指标:")
    lines.append("  初始风险 | 入场→SL : %s pip" % r.get("init_risk_pips"))
    lines.append("  初始收益 | 入场→TP : %s pip" % r.get("init_reward_pips"))
    lines.append("  初始 R:R         : %s" % r.get("init_rr"))
    if r.get("current") is not None:
        lines.append("  浮盈            : %s pip" % r.get("open_pnl_pips"))
        lines.append("  剩余风险 | 当前→SL : %s pip" % r.get("current_to_sl_pips"))
        lines.append("  剩余收益 | 当前→TP : %s pip" % r.get("current_to_tp_pips"))
        lines.append("  剩余 R:R         : %s" % r.get("remaining_rr"))
        if r.get("open_pnl_account") is not None:
            lines.append("  浮盈(账户币)    : $%s (%.2f%% 权益)"
                         % (r.get("open_pnl_account"), r.get("open_pnl_pct_equity")))
    if r.get("init_dollar_risk") is not None:
        lines.append("  单笔美元风险    : $%s (%.2f%% 权益)" % (r.get("init_dollar_risk"), r.get("risk_pct_equity")))
    lines.append("")
    lines.append("判定: %s" % r["verdict"])
    if r.get("hard_error"):
        lines.append("  [硬性错误] %s" % r["hard_error"])
    if r["flags"]:
        lines.append("理由:")
        for f in r["flags"]:
            tag = {"severe": "✗ 严重", "warn": "⚠ 警示", "info": "· 提示"}[f["level"]]
            lines.append("  %s [%s] %s" % (tag, f["code"], f["text"]))
    else:
        lines.append("理由: 各维度均在框架纪律范围内。")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description="止损/止盈合理性评估(持仓管理纪律辅助): 方向/入场/SL/TP/当前价 → 三级判定",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--direction", required=True, choices=["BUY", "SELL"], help="方向")
    ap.add_argument("--entry", required=True, type=float, help="入场价")
    ap.add_argument("--sl", required=True, type=float, help="止损价")
    ap.add_argument("--tp", required=True, type=float, help="止盈价")
    ap.add_argument("--current", type=float, help="当前价(省略则尝试经 --symbol 自动取实时价)")
    ap.add_argument("--symbol", help="品种,如 AUDJPY(用于自动取当前价 / USDJPY 换算)")
    ap.add_argument("--equity", type=float, help="账户权益(用于美元风险与占比)")
    ap.add_argument("--lot", type=float, help="手数(标准手,如 0.02)")
    ap.add_argument("--account-currency", default="USD", help="账户货币(默认 USD)")
    ap.add_argument("--atr", type=float, help="ATR(价格差,用于 SL 宽度 sanity)")
    ap.add_argument("--pip", type=float, help="pip 刻度(省略则按 --symbol 推断)")
    ap.add_argument("--out", help="结果落盘路径(.txt/.json 按扩展名)")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args()

    current = args.current
    if current is None and args.symbol:
        current = fetch_current(args.symbol)
        if current is None:
            print("[提示] 未能自动获取 %s 当前价,请用 --current 显式传入。" % args.symbol, file=sys.stderr)

    pip = args.pip
    r = evaluate(args.direction, args.entry, args.sl, args.tp, current,
                 args.symbol, args.equity, args.lot, args.account_currency, args.atr, pip)

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(render_text(r))
    if args.out:
        ext = os.path.splitext(args.out)[1].lower()
        with open(args.out, "w", encoding="utf-8", newline="") as f:
            if ext == ".json":
                f.write(json.dumps(r, ensure_ascii=False, indent=2))
            else:
                f.write(render_text(r))
        print("\n[已落盘] %s" % args.out, file=sys.stderr)


if __name__ == "__main__":
    main()
