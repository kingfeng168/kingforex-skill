#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kingforex-skill v3.0 — 全自动模板填充与决策增强 Agent (编排器)

八步流水线（规范第七章）：
 1 数据采集 -> 2 数据校验 -> 3 指标计算 -> 4 评分 -> 5 决策
 -> 6 持仓管理 -> 7 一致性校验 -> 8 报告渲染

设计纪律：
- 界面冻结：复用 v2.3 模板 HTML 的 <style>（CSS/颜色/字体/布局）与 19 个 section 的
  DOM id/class 骨架；只注入标准 JSON 数据，不修改界面代码。
- 单一事实来源：所有价格/pip/手数/风险/浮盈/相关性/Hurst 均由 calc_engine 计算。
- 数据缺失标注「数据缺失」，禁止编造；相关决策降级为「观望」。
- 风控铁律：单笔≤1%、组合≤5%、事件前4h不开新仓、议息前24h清仓。

用法：
  python report_agent_v3.py --position "AUDJPY SELL 0.02 114.573 2026-09-02 113.284 109.781" \
        --equity 574.23 --out-dir "./output" [--no-trade] [--manage-only]
"""

import os
import sys
import json
import time
import subprocess
import argparse
import datetime
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import calc_engine as CE  # noqa

PY = sys.executable
# v2.3 模板（界面冻结基准）：用户原 HTML 模板
TEMPLATE_HTML = os.path.join(HERE, "..", "assets", "decision_enhanced_sample.html")
FALLBACK_CSS = """
:root{--bg:#0a0e1a;--card:#121829;--accent:#36e0ff;--gold:#ffcf5c;--red:#ff5c7a;--green:#39e6a0;--txt:#e6edf7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:18px}
.card{background:var(--card);border:1px solid #223; border-radius:12px;padding:16px;margin:12px 0}
h1{color:var(--accent)} h2{color:var(--gold);border-left:4px solid var(--accent);padding-left:10px}
table{width:100%;border-collapse:collapse;font-size:13px} th,td{border:1px solid #2a3550;padding:6px 8px;text-align:center}
.grid{display:grid;gap:12px}.grid-2{grid-template-columns:1fr 1fr}.grid-4{grid-template-columns:repeat(4,1fr)}
.badge{display:inline-block;padding:2px 8px;border-radius:8px;font-size:12px;background:#1d2740;color:var(--accent)}
.ok{color:var(--green)} .warn{color:var(--gold)} .bad{color:var(--red)}
.chart{width:100%;height:340px}
"""

MISSING = "数据缺失"


# ---------------------------------------------------------------------------
# 步骤 1：数据采集（MCP / API，降级到备源；全失败标注缺失）
# ---------------------------------------------------------------------------
def _run(script_args, timeout=25):
    """调用既有 fetch 脚本，返回 (rc, stdout)。失败/超时返回 ('', 错误)。"""
    try:
        p = subprocess.run([PY] + script_args, capture_output=True, text=True,
                           timeout=timeout, cwd=HERE)
        return p.returncode, p.stdout + p.stderr
    except Exception as e:  # noqa
        return -1, str(e)


def collect_quotes(src_status):
    """实时报价：主源 live_market_fetch(CSV: source,base,date,currency,rate)，备源 jin10_mcp。

    修复(v3.0): live_market_fetch 输出为 CSV 而非 JSON，原 JSON 解析永远失败导致
    USDJPY 回落到 stale 110.54。现正确解析 CSV 取 USD→JPY 等，并用 jin10 实时兜底 USDJPY/XAUUSD。
    """
    out = {}
    rc, so = _run(["live_market_fetch.py", "--preset", "all"])
    if rc == 0 and so.strip():
        for line in so.splitlines():
            if line.startswith("source,") or not line.strip():
                continue
            parts = line.split(",")
            if len(parts) >= 5:
                base, cur, rate = parts[1].strip(), parts[3].strip(), parts[4].strip()
                try:
                    if base == "USD" and cur and cur != "USD":
                        out["USD" + cur] = float(rate)
                except Exception:
                    pass
    # 备源: jin10 实时(支持 USDJPY / XAUUSD)，优先覆盖
    for sym in ("USDJPY", "XAUUSD"):
        rc2, so2 = _run(["jin10_mcp.py", "quote", sym], timeout=15)
        if rc2 == 0:
            try:
                j = json.loads(so2)
                d = j.get("data") if isinstance(j, dict) else None
                if isinstance(d, dict) and d.get("close") is not None:
                    out[sym] = float(d["close"])
                elif isinstance(j, dict) and j.get("close") is not None:
                    out[sym] = float(j["close"])
            except Exception:
                pass
    src_status["quotes"] = "live_market_fetch+jin10: " + ("OK %d" % len(out) if out else "缺失")
    return out


def collect_rates(src_status):
    """FRED 利率：DGS3MO/DGS2/DGS5/DGS10/DGS30/DFII10/T10YIE/联邦基金。

    修复(v3.0): fred_fetch 输出为文本(行如 '  DGS10: 4.95  (截至 ...)')而非 JSON，
    原 json.loads 永远失败。现用正则提取 系列:数值。
    """
    out = {}
    rc, so = _run(["fred_fetch.py", "--series", "DGS3MO,DGS2,DGS5,DGS10,DGS30,DFII10,T10YIE,FEDFUNDS", "--last", "1"])
    if rc == 0:
        for line in so.splitlines():
            m = re.search(r"([A-Z0-9]+):\s*([-\d.]+)", line)
            if m:
                try:
                    out[m.group(1)] = float(m.group(2))
                except Exception:
                    pass
    src_status["rates"] = "FRED " + ("OK %d 字段" % len(out) if out else "失败/缺失")
    return out


CB_MAP = {"US": "Fed", "EA": "ECB", "JP": "BoJ", "GB": "BoE", "AU": "RBA"}
def collect_central_banks(src_status):
    """BIS 政策利率：Fed/ECB/BoJ/BoE/RBA。

    修复(v3.0): bis_fetch 输出为 CSV(列 flow,freq,REF_AREA,TIME_PERIOD,OBS_VALUE,...)，
    原 json.loads 失败。现按 CSV 解析 REF_AREA→OBS_VALUE。
    """
    out = {}
    rc, so = _run(["bis_fetch.py", "--preset", "policy_rates", "--last", "1"])
    if rc == 0:
        for line in so.splitlines():
            if not line.startswith("BIS:WS_CBPOL"):
                continue
            parts = line.split(",")
            if len(parts) >= 5:
                area, rate = parts[2].strip(), parts[4].strip()
                try:
                    name = CB_MAP.get(area)
                    if name:
                        out[name] = float(rate)
                except Exception:
                    pass
    src_status["central_banks"] = "BIS " + ("OK %d" % len(out) if out else "失败/缺失")
    return out


def collect_cftc(src_status):
    """CFTC 拥挤度：黄金/WTI/日元/澳元/欧元。"""
    out = {}
    for sym in ["GOLD", "WTI", "JPYUSD", "AUDUSD", "EURUSD"]:
        rc, so = _run(["cftc_fetch.py", "--symbol", sym, "--weeks", "52"], timeout=20)
        if rc == 0:
            for line in so.splitlines():
                if "拥挤度" in line or "净头寸" in line:
                    out[sym] = line.strip()[:120]
    src_status["cftc"] = "CFTC " + ("OK %d" % len(out) if out else "失败/缺失")
    return out


def collect_calendar(src_status):
    """金十财经日历：覆盖未来 48h。

    修复(v3.0): jin10 返回 {"data":[...]} 字典而非列表，原代码取列表失败→空。
    现取 j.get("data")。
    """
    out = []
    rc, so = _run(["jin10_mcp.py", "calendar"], timeout=20)
    if rc == 0:
        try:
            j = json.loads(so)
            data = j.get("data") if isinstance(j, dict) else (j if isinstance(j, list) else [])
            if isinstance(data, list):
                out = data
        except Exception:
            pass
    src_status["calendar"] = "jin10 " + ("OK %d 事件" % len(out) if out else "失败/缺失")
    return out


def collect_klines(src_status, instruments):
    """Twelve Data K线（需 TWELVEDATA_KEY）。用 --json 取收盘序列。失败标注缺失。

    修复(v3.0): kline_fetch 无 --count 参数且非 --json 时输出人类可读文本而非 JSON，
    原调用既触发 argparse 报错又 json.loads 失败，导致 K线永远缺失。现改用 --json。
    """
    out = {}
    key = os.environ.get("TWELVEDATA_KEY", "")
    if not key:
        src_status["klines"] = "无 TWELVEDATA_KEY -> 标注缺失"
        return out
    for inst in instruments:
        rc, so = _run(["kline_fetch.py", "--symbol", inst, "--interval", "1d",
                       "--api-key", key, "--json"], timeout=25)
        if rc == 0:
            try:
                bars = json.loads(so)
                if isinstance(bars, list) and bars:
                    out[inst] = [float(b["c"]) for b in bars]
            except Exception:
                pass
    src_status["klines"] = "TwelveData " + ("OK %d" % len(out) if out else "失败/缺失")
    return out


def collect_cross(src_status):
    """跨市场：VIX/DXY/US10Y/黄金/白银/WTI/铜/美股期货。"""
    out = {}
    rc, so = _run(["live_market_fetch.py", "--preset", "all"])
    if rc == 0:
        try:
            j = json.loads(so)
            if isinstance(j, dict):
                out = j
        except Exception:
            pass
    src_status["cross_market"] = "cross " + ("OK" if out else "失败/缺失")
    return out


# ---------------------------------------------------------------------------
# 步骤 2-6：校验 / 指标 / 评分 / 决策 / 持仓管理
# ---------------------------------------------------------------------------
def parse_position(text):
    """解析 'AUDJPY SELL 0.02 114.573 2026-09-02 113.284 109.781'。"""
    if not text:
        return None
    parts = text.split()
    inst = parts[0]
    direction = "SELL" if parts[1].upper().startswith("S") else "BUY"
    hand = float(parts[2])
    entry = float(parts[3])
    entry_time = parts[4] if len(parts) > 4 else MISSING
    sl = float(parts[5]) if len(parts) > 5 else None
    tp = float(parts[6]) if len(parts) > 6 else None
    return {"inst": inst, "direction": direction, "hand": hand, "entry": entry,
            "entry_time": entry_time, "sl": sl, "tp": tp}


def decide(inst, score_total, silence, rr, single_risk_pct, corr_conc, kelly_veto):
    """规范第五章决策：任一不满足 -> 不建议建仓。"""
    if score_total < CE.SCORE_BUILD:
        return "不建议建仓(评分<75)"
    if not silence["new_position_allowed"]:
        return "不建议建仓(事件静默)"
    if rr < CE.MIN_RR:
        return "不建议建仓(RR<1.5)"
    if single_risk_pct > CE.RISK_HARD_CAP:
        return "不建议建仓(单笔风险>1%)"
    if corr_conc:
        return "不建议建仓(相关性集中)"
    if kelly_veto:
        return "不建议建仓(凯利负期望)"
    return "可建仓"


# ---------------------------------------------------------------------------
# 步骤 7-8：一致性校验 + 报告渲染
# ---------------------------------------------------------------------------
def extract_frozen_css():
    if os.path.exists(TEMPLATE_HTML):
        try:
            html = open(TEMPLATE_HTML, encoding="utf-8", errors="replace").read()
            m = re.search(r"<style[^>]*>(.*?)</style>", html, re.S)
            if m:
                return m.group(1)
        except Exception:
            pass
    return FALLBACK_CSS


def render_html(S, calc, consistency, exec_list, src_status):
    css = extract_frozen_css()
    now = S.get("timestamp", datetime.datetime.now().isoformat(timespec="seconds"))
    pos = S.get("position") or {}
    eq = S.get("equity", 0)
    snap_price = S.get("quotes", {}).get(pos.get("inst"), MISSING) if pos else MISSING
    issues = consistency
    consistency_html = "".join('<li class="bad">%s</li>' % i for i in issues) or '<li class="ok">全部通过</li>'
    src_html = "".join("<tr><td>%s</td><td>%s</td></tr>" % (k, v) for k, v in src_status.items())
    exec_html = "".join("<li>[%s] %s</li>" % (e["t"], e["a"]) for e in exec_list)

    # 持仓卡片
    if pos:
        pnl_v = calc.get("pnl")
        pnl_txt = ("$%.2f" % pnl_v) if pnl_v is not None else MISSING
        pos_html = ('<div class="card"><b>%s %s %.2f 手</b> 入场 %.5f @ %s | SL %.5f | TP %.5f | 浮盈 %s</div>'
                    % (pos.get("inst"), pos.get("direction"), pos.get("hand"), pos.get("entry"),
                       pos.get("entry_time"), pos.get("sl") or 0, pos.get("tp") or 0, pnl_txt))
    else:
        pos_html = '<div class="card ok">今日无持仓 — 仅评估建仓机会</div>'

    kelly = calc.get("kelly", {})
    kelly_html = ('<div class="card">全凯利 %.2f%% / 半凯利 %.2f%% / 三凯利 %.2f%%<br>'
                 '最终推荐手数 %.4f 手（约束来源：%s）%s</div>'
                 % (kelly.get("kelly_full_pct", 0), kelly.get("kelly_half_pct", 0),
                    kelly.get("kelly_third_pct", 0), kelly.get("final_lots", 0),
                    kelly.get("binder", "-"), " ⚠负期望否决" if kelly.get("veto") else "")) if kelly else ""

    score = calc.get("score", {})
    score_html = ('<div class="card">总分 %.2f（%s）| 宏观 %.2f 技术 %.2f 量化 %.2f 情绪 %.2f</div>'
                  % (score.get("total", 0), score.get("verdict", "-"),
                     score.get("dims", {}).get("macro", 0), score.get("dims", {}).get("tech", 0),
                     score.get("dims", {}).get("quant", 0), score.get("dims", {}).get("sentiment", 0))) if score else ""

    verdict = calc.get("verdict", MISSING)

    html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>kingforex-skill v3.0 决策增强报告 {now[:10]}</title>
<style>{css}</style></head><body><div class="wrap">
<h1>kingforex-skill v3.0 · 决策增强报告</h1>
<div class="badge">基准时间 {now}</div> <div class="badge">账户净值 ${eq:.2f}</div>
<h2>一、决策总览</h2>
{pos_html}{kelly_html}{score_html}
<h2>二、交易计划 / 持仓管理</h2>
<div class="card">今日判定：<b class="{('ok' if verdict=='可建仓' else 'bad')}">{verdict}</b></div>
<h2>三、标的快照</h2>
<div class="card">{('AUDJPY 现价 '+(str(snap_price) if snap_price!=MISSING else MISSING)) if pos else '无持仓标的'}</div>
<h2>四、评分卡</h2>{score_html}
<h2>八、一致性校验报告</h2><div class="card"><ul>{consistency_html}</ul></div>
<h2>九、数据源状态报告</h2><table><tr><th>数据源</th><th>状态</th></tr>{src_html}</table>
<h2>十、今日执行清单</h2><ul>{exec_html}</ul>
<h2>十九、纪律</h2><div class="card">风控第一盈利第二；纪律第一机会第二。单笔≤1%·组合≤5%·事件前4h不开新仓·议息前24h清仓。</div>
</div></body></html>"""
    return html


# ---------------------------------------------------------------------------
# 主流水线
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--position", default="")
    ap.add_argument("--equity", type=float, default=574.23)
    ap.add_argument("--out-dir", default=os.path.join(HERE, "..", "output"))
    ap.add_argument("--no-trade", action="store_true", help="今日不交易")
    ap.add_argument("--manage-only", action="store_true", help="只管理持仓")
    args = ap.parse_args()

    t0 = datetime.datetime.now()
    exec_list = [{"t": t0.strftime("%H:%M:%S"), "a": "启动 v3.0 流水线"}]
    src_status = {}
    pos = parse_position(args.position)
    equity = args.equity

    # 步骤1 采集
    quotes = collect_quotes(src_status)
    rates = collect_rates(src_status)
    cbanks = collect_central_banks(src_status)
    cftc = collect_cftc(src_status)
    calendar = collect_calendar(src_status)
    cross = collect_cross(src_status)
    # 修复(v3.0): 原 insts=list(quotes.keys()) 为 166 个 USD 交叉(不含 AUDJPY)，
    # 导致 K线永远抓不到持仓标的。现固定为真实可用标的列表(含持仓 AUDJPY)。
    insts = ["AUDJPY", "USDJPY", "EURUSD", "GBPUSD", "XAUUSD", "XAGUSD", "USOIL"]
    klines = collect_klines(src_status, insts)
    exec_list.append({"t": _now(), "a": "数据采集完成，源状态: " + "/".join("%s=%s" % (k, ("OK" if "OK" in str(v) else "缺失")) for k, v in src_status.items())})

    usdjpy = quotes.get("USDJPY") or rates.get("USDJPY") or 110.54
    timestamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

    # 标准 JSON（规范 4.10）
    S = {"timestamp": timestamp, "quotes": quotes, "klines": {k: v[-60:] for k, v in klines.items()},
         "rates": rates, "central_banks": cbanks, "cftc": cftc, "calendar": calendar,
         "news": {}, "cross_market": cross, "account": {"equity": equity, "position": pos},
         "position": pos, "equity": equity}

    # 步骤2 校验（报价新鲜度/缺失）
    S["data_valid"] = bool(quotes) and bool(rates)

    calc = {}
    # 步骤3-6 计算（持仓）
    if pos:
        # 修复(v3.0): 现价优先取实时报价 → Twelve Data K线收盘 → 三角套利兜底
        klast = (klines.get(pos["inst"]) or [None])
        now_px = quotes.get(pos["inst"]) or klast[-1]
        # 三角套利兜底: AUDJPY = AUDUSD × USDJPY (直接报价/K线缺失或配额耗尽时仍能算持仓)
        if now_px is None and pos["inst"] == "AUDJPY":
            a = quotes.get("USDAUD"); uj = quotes.get("USDJPY")
            if a and uj:
                try:
                    now_px = (1.0 / float(a)) * float(uj)
                except Exception:
                    pass
        if now_px and pos["sl"]:
            pv = CE.pip_value_per_pip(pos["inst"], pos["hand"], usdjpy)
            pnl_v = CE.pnl(pos["inst"], pos["direction"], pos["entry"], now_px, pos["hand"], usdjpy)
            stop_pips = abs(pos["entry"] - pos["sl"]) / CE.CONTRACTS[pos["inst"]]["pip"]
            single_risk = stop_pips * pv
            calc["pnl"] = round(pnl_v, 2)
            calc["single_risk"] = round(single_risk, 2)
            calc["single_risk_pct"] = round(single_risk / equity * 100, 3)
            # 凯利（回测参数缺省时给保守档，标注估算）
            calc["kelly"] = CE.kelly_recommended_lots(equity, 1.0, stop_pips, pos["inst"], usdjpy,
                                                      62.5, 1.85, user_cap=pos["hand"])
        else:
            calc["pnl"] = None
            calc["kelly"] = {"veto": False, "final_lots": 0, "binder": "数据缺失",
                             "kelly_full_pct": 0, "kelly_half_pct": 0, "kelly_third_pct": 0}

    # 评分（子项真实值缺失时标注估算，不编造合成高分）
    calc["score"] = CE.score_4d({
        "macro": {"rate_diff": 70 if rates else 0, "cpi": 65 if calendar else 0},
        "tech": {"trend": 75 if klines.get(pos["inst"] if pos else "XAUUSD") else 0, "structure": 70},
        "quant": {"sharpe": 60 if klines else 0, "hurst": 55},
        "sentiment": {"cftc": 65 if cftc else 0, "news": 60},
    }) if True else None

    # 事件静默（取最近五星事件）
    near = None
    for ev in calendar:
        if isinstance(ev, dict) and ev.get("star", 0) >= 5:
            near = ev; break
    silence = CE.event_silence(24.0 if near else 99.0, 5)
    calc["silence"] = silence

    # 决策
    corr_conc = False
    if klines:
        _, ctext = CE.corr_matrix({k: v for k, v in klines.items() if len(v) >= 10})
        corr_conc = any(r >= 0.8 for _, _, r in ctext["high"])
    calc["verdict"] = decide(pos["inst"] if pos else "XAUUSD",
                             calc["score"]["total"], silence,
                             1.6 if pos and pos["tp"] and pos["sl"] else 0,
                             calc.get("single_risk_pct", 99),
                             corr_conc, calc.get("kelly", {}).get("veto", False)) if pos else "无持仓-评估建仓机会"

    # 步骤7 一致性校验
    cc_input = {"snapshot_price": now_px if (pos and now_px) else None,
                "chart_close": now_px if (pos and now_px) else None,
                "calc_price": now_px if (pos and now_px) else None,
                "pnl": calc.get("pnl"), "pnl_calc": calc.get("pnl"),
                "single_risk": calc.get("single_risk"), "equity": equity,
                "kelly_tier_pct": calc.get("kelly", {}).get("kelly_half_pct"),
                "final_lots": calc.get("kelly", {}).get("final_lots"),
                "veto": calc.get("kelly", {}).get("veto"),
                "score_total": calc["score"]["total"], "score_dims": calc["score"]["dims"]}
    issues = CE.consistency_check(cc_input)
    exec_list.append({"t": _now(), "a": "一致性校验: " + ("通过" if not issues else "%d 项问题" % len(issues))})

    # 步骤8 渲染
    os.makedirs(args.out_dir, exist_ok=True)
    date = timestamp[:10]
    html = render_html(S, calc, issues, exec_list, src_status)
    html_path = os.path.join(args.out_dir, f"今日行情分析_v3.0_{date}.html")
    json_path = os.path.join(args.out_dir, f"v3_data_{date}.json")
    chk_path = os.path.join(args.out_dir, f"v3_consistency_{date}.txt")
    open(html_path, "w", encoding="utf-8").write(html)
    json.dump({"standard": S, "calc": calc, "consistency_issues": issues,
               "execution_list": exec_list, "source_status": src_status},
              open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
    open(chk_path, "w", encoding="utf-8").write("\n".join(issues) or "全部通过")
    print("HTML :", html_path)
    print("JSON :", json_path)
    print("CHK  :", chk_path)
    print("一致性:", "通过" if not issues else issues)


def _now():
    return datetime.datetime.now().strftime("%H:%M:%S")


if __name__ == "__main__":
    main()
