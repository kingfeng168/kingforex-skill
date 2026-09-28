#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jev 判断工具客户端（kingforex-skill）— Typesafe Jev

====================================================================
⚠️ 角色定位（最重要）
--------------------------------------------------------------------
Jev **不是聊天模型,不生成文本**,也**不是行情数据源**。
它是一个**结构化判断引擎**:你输入一段状态(State)+ 一组类型化问题(Questions),
它返回带置信度的结构化判断(noul / choice / score)。

在本技能交易场景中的分工:
  - 你(策略/分析):负责理解需求、解读市场、给出方向判断与分析结论。
  - Jev:负责**审计 / 门控 / 校准**——验证你的方向判断是否自洽、信号置信度是否足够、
         当前状态是否值得出手。它是**审计员,不是信号源**。
  - 代码:根据 Jev 返回的置信度,按预设阈值决定提交/降仓/放弃;并强制执行硬性风控。

100 倍杠杆铁律:**Jev 的输出永远是"信息"不是"命令"。低置信度直接丢弃;
任何实盘订单提交前,必须经过独立的程序化风控(保证金/当日亏损上限/单笔亏损上限),
Jev 的"安全"判断不能覆盖这些硬边界。**

社区回测:直接把 Jev 当信号源的方向命中率约 49.3%(跑输随机),官方标记为"高风险场景,慎用"。
====================================================================

调用方式(本脚本实现 HTTP API;MCP 工具 evaluate/judge 亦可,同一 Key)
--------------------------------------------------------------------
  POST https://api.typesafe.ai/v1/systemone
  Authorization: Bearer <TYPESAFE_API_KEY>     # = scripts/.jev_key 内容
  Content-Type: application/json
  Body: { "model": "jev-latest", "state": <obj/str>, "questions": { <id>: <question> } }
  返回: { "answers": { <id>: { noul | choice+probabilities+confidence | score+legend+confidence } } }

三种提问原语
--------------------------------------------------------------------
  noul   : 是/否判断  -> answers[id].noul ∈ [0,1](近1强肯定,近0强否定,近0.5=各半)
  choice : 选项选择  -> answers[id].choice + .probabilities + .confidence
  score  : 有序量表  -> answers[id].score(可小数) + .legend + .confidence

Key 读取优先级(与技能其他源一致)
--------------------------------------------------------------------
  --api-key  >  环境变量 JEV_API_KEY  >  脚本同目录 scripts/.jev_key(单行纯文本,不进 zip)

用法
--------------------------------------------------------------------
  # 连通性自检
  python scripts/jev_fetch.py probe
  # 通用判断:自构 state + questions(JSON 文件)
  python scripts/jev_fetch.py evaluate --state-file state.json --questions-file q.json
  # 100 倍杠杆审计门控(内置 4 个标准问题,用户只需提供 state.json)
  python scripts/jev_fetch.py audit --state-file state.json
  # 切换认证头/模型(一般无需)
  python scripts/jev_fetch.py evaluate --state-file state.json --questions-file q.json --model jev-latest
"""

import argparse
import io
import json
import os
import sys
import urllib.request
import urllib.error

_HERE = os.path.dirname(os.path.abspath(__file__))

BASE_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"

# ── 100 倍杠杆场景:保守阈值(来自 Jev 规格;未用本品种历史数据校准前不得下调) ──
# 字段: (原语, 阈值, 方向). noul/score 为"≥阈值通过";choice 为"选中项 confidence≥阈值 且非 none"。
THRESHOLDS = {
    "direction_coherent": ("noul", 0.80, "方向一致性审计:通过才提交"),
    "market_clarity": ("score", 2.5, "市场清晰度:低于则放弃或降至 1/3 仓"),
    "safe_to_execute": ("noul", 0.85, "安全窗口门控:未过不执行"),
    "best_pair": ("choice", 0.80, "品种选择:未过不交易"),
    "news_impact": ("noul", 0.75, "新闻/情绪影响:未过不纳入决策"),
}

# ── 审计门控内置的 4 个标准问题(方向一致性 / 清晰度 / 安全窗口 / 品种选择) ──
QUESTIONS_AUDIT = {
    "direction_coherent": {
        "type": "noul",
        "instructions": "基于提供的 State(当前市场状态与策略给出的方向判断及依据),该方向判断是否与其自身依据清晰自洽、不存在内在矛盾?",
        "criteria": {
            "true": "方向明确(做多或做空),且依据中的技术/基本面信息支持该方向,无矛盾信号。",
            "false": "方向模糊、依据与方向矛盾,或依据中存在未解决的关键冲突。",
        },
    },
    "market_clarity": {
        "type": "score",
        "instructions": "当前市场状态对交易决策的清晰程度:趋势是否明确、信号是否一致、噪音是否可控。",
        "levels": ["极度混乱", "混乱", "中性", "较清晰", "高度清晰"],
        "criteria": [
            "极度混乱:趋势反转频繁、信号互相矛盾、噪音极高。",
            "混乱:多空拉锯、信号不一致。",
            "中性:方向可作、但需谨慎。",
            "较清晰:趋势明确、信号大体一致。",
            "高度清晰:趋势与信号高度一致、噪音可控。",
        ],
    },
    "safe_to_execute": {
        "type": "noul",
        "instructions": "基于 State 中的市场状态和当前策略方向,在 100 倍杠杆下,当前是否为执行该方向交易的安全窗口?",
        "criteria": {
            "true": "市场流动性充足、无重大数据窗口即将到来、波动率处于可接受范围、方向信号清晰。",
            "false": "存在重大数据窗口、波动率异常放大、流动性不足,或方向信号模糊。",
        },
    },
    "best_pair": {
        "type": "choice",
        "instructions": "基于当前市场状态,外汇/黄金/WTI 中哪个品种的交易机会最明确?",
        "criteria": {
            "forex": "外汇品种趋势明确、信号一致。",
            "gold": "黄金受地缘或利率驱动,方向信号清晰。",
            "wti": "原油受库存或供给事件驱动,方向信号清晰。",
            "none": "均不满足交易条件。",
        },
    },
}


# ───────────────────────────────────────────────────────────────────────────
# Key / HTTP
# ───────────────────────────────────────────────────────────────────────────
def _read_key(args_key):
    """优先级: --api-key > JEV_API_KEY > scripts/.jev_key(不进 zip)。"""
    if args_key:
        return args_key.strip()
    env = os.environ.get("JEV_API_KEY", "").strip()
    if env:
        return env
    p = os.path.join(_HERE, ".jev_key")
    if os.path.isfile(p):
        try:
            with io.open(p, "r", encoding="utf-8") as f:
                v = f.read().strip()
            if v:
                return v
        except Exception:
            pass
    return ""


def _call(api_key, state, questions, model=DEFAULT_MODEL, timeout=60, base=BASE_URL):
    payload = json.dumps({"model": model, "state": state, "questions": questions}).encode("utf-8")
    req = urllib.request.Request(
        base,
        data=payload,
        headers={"Authorization": "Bearer %s" % api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(400).decode("utf-8", "replace")
        except Exception:
            pass
        raise RuntimeError("HTTP %s %s: %s" % (e.code, e.reason, body))
    except urllib.error.URLError as e:
        raise RuntimeError("连接失败: %s" % e.reason)


# ───────────────────────────────────────────────────────────────────────────
# 问题构造助手(可选,便于脚本内拼装)
# ───────────────────────────────────────────────────────────────────────────
def noul_q(instructions, criteria_true, criteria_false):
    return {"type": "noul", "instructions": instructions,
            "criteria": {"true": criteria_true, "false": criteria_false}}


def choice_q(instructions, criteria_map):
    return {"type": "choice", "instructions": instructions, "criteria": criteria_map}


def score_q(instructions, levels):
    return {"type": "score", "instructions": instructions, "levels": levels}


# ───────────────────────────────────────────────────────────────────────────
# 结果解读 / 门控
# ───────────────────────────────────────────────────────────────────────────
def _fmt_answer(qid, ans):
    kind = ans.get("type") or _infer(ans)
    if kind == "noul" or "noul" in ans:
        return "noul=%.2f" % float(ans["noul"])
    if kind == "choice" or "choice" in ans:
        c = ans.get("choice")
        conf = ans.get("confidence")
        probs = ans.get("probabilities", {})
        top = " / ".join("%s=%.2f" % (k, float(v)) for k, v in
                         sorted(probs.items(), key=lambda x: -float(x[1]))[:3]) if probs else ""
        return "choice=%s conf=%.2f  [%s]" % (c, float(conf or 0), top)
    if kind == "score" or "score" in ans:
        sc = ans.get("score")
        leg = ans.get("legend", {})
        conf = ans.get("confidence")
        return "score=%.2f  legend=%s  conf=%.2f" % (float(sc or 0), leg, float(conf or 0))
    return json.dumps(ans, ensure_ascii=False)


def _infer(ans):
    if "noul" in ans:
        return "noul"
    if "choice" in ans:
        return "choice"
    if "score" in ans:
        return "score"
    return "unknown"


def _gate_check(qid, ans):
    """按 THRESHOLDS 判定单题是否通过。返回 (passed:bool, detail:str)。"""
    if qid not in THRESHOLDS:
        return None, "(无阈值,仅展示)"
    kind, thr, _ = THRESHOLDS[qid]
    if kind == "noul":
        v = float(ans.get("noul", 0))
        return v >= thr, "noul=%.2f ≥ %.2f ? %s" % (v, thr, v >= thr)
    if kind == "score":
        v = float(ans.get("score", 0))
        return v >= thr, "score=%.2f ≥ %.2f ? %s" % (v, thr, v >= thr)
    if kind == "choice":
        c = ans.get("choice")
        conf = float(ans.get("confidence", 0))
        ok = (conf >= thr) and (c != "none")
        return ok, "choice=%s conf=%.2f ≥ %.2f 且非 none ? %s" % (c, conf, thr, ok)
    return None, "(未知原语)"


# ───────────────────────────────────────────────────────────────────────────
# 子命令
# ───────────────────────────────────────────────────────────────────────────
def _load_json_arg(inline, path, name):
    if inline is not None:
        return json.loads(inline)
    if path:
        with io.open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise SystemExit("✗ 缺少 %s(用 --%s 传入 JSON 字符串,或 --%s-file 指定文件)" %
                     (name, name, name))


def _cmd_probe(key):
    if not key:
        print("⚠ 未配置 Key(环境变量 JEV_API_KEY / scripts/.jev_key / --api-key);仍尝试连通性。")
    try:
        out = _call(key, {"probe": True},
                    {"_ping": noul_q("若服务可达,回答 1。", "可达", "不可达")})
        print("✓ 连通成功 HTTP 200")
        print("  返回:", json.dumps(out, ensure_ascii=False)[:400])
        return 0
    except Exception as e:  # noqa: BLE001
        print("✗ 连通失败: %s" % e)
        return 1


def _cmd_evaluate(args, key):
    state = _load_json_arg(args.state, args.state_file, "state")
    questions = _load_json_arg(args.questions, args.questions_file, "questions")
    try:
        out = _call(key, state, questions, model=args.model)
    except Exception as e:  # noqa: BLE001
        print("✗ 调用失败: %s" % e)
        return 1
    answers = out.get("answers", out)
    print("==== Jev 判断结果(仅供参考,非命令) ====")
    for qid, ans in answers.items():
        print("[%s] %s" % (qid, _fmt_answer(qid, ans)))
    if args.gate:
        print("\n---- 100 倍杠杆门控(仅对已登记阈值的问题) ----")
        all_pass = True
        for qid, ans in answers.items():
            g = _gate_check(qid, ans)
            if g[0] is None:
                continue
            all_pass = all_pass and g[0]
            print("  %s: %s -> %s" % (qid, "PASS" if g[0] else "FAIL", g[1]))
        print("\n  综合门控: %s" % ("✅ 全部通过(仍须独立程序化风控复核)" if all_pass else "❌ 未全部通过 -> 放弃/重新评估"))
    return 0


def _cmd_audit(args, key):
    state = _load_json_arg(args.state, args.state_file, "state")
    questions = QUESTIONS_AUDIT
    try:
        out = _call(key, state, questions, model=args.model)
    except Exception as e:  # noqa: BLE001
        print("✗ 调用失败: %s" % e)
        return 1
    answers = out.get("answers", out)
    print("=" * 64)
    print("Jev 100 倍杠杆审计门控(State 由用户构造,Questions 内置)")
    print("=" * 64)
    results = []
    for qid, ans in answers.items():
        print("\n[%s] %s" % (qid, _fmt_answer(qid, ans)))
        g = _gate_check(qid, ans)
        if g[0] is None:
            print("   (无内置阈值)")
            continue
        results.append(g[0])
        print("   门控: %s  (%s)" % ("✅ PASS" if g[0] else "❌ FAIL", g[1]))
    overall = all(results) if results else False
    print("\n" + "=" * 64)
    print("综合决策: %s" % ("✅ 审计通过(可进入独立程序化风控复核,再决定是否出手)"
                            if overall else "❌ 审计未通过 -> 放弃交易 / 重新评估(宁可错过,不可做错)"))
    print("=" * 64)
    print("⚠️ 提醒:Jev 输出是信息不是命令;本审计不替代硬性风控(单笔≤1%/当日≤3%/连亏3笔熔断/"
          "重大数据窗口禁开仓/隔夜敞口约束)。未用本品种历史数据校准前,阈值维持保守设置。")
    return 0 if overall else 2


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="jev_fetch.py",
        description="Typesafe Jev 判断工具客户端(审计/门控/校准;非行情源、非信号源)",
    )
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("probe", help="连通性自检(POST 最小请求)")

    pe = sub.add_parser("evaluate", aliases=["judge"], help="通用判断:自构 state + questions")
    pe.add_argument("--state", help="State(JSON 字符串)")
    pe.add_argument("--state-file", help="State(JSON 文件)")
    pe.add_argument("--questions", help="Questions(JSON 字符串,以问题 ID 为键)")
    pe.add_argument("--questions-file", help="Questions(JSON 文件)")
    pe.add_argument("--api-key", help="TYPESAFE_API_KEY(或设 JEV_API_KEY / scripts/.jev_key)")
    pe.add_argument("--model", default=DEFAULT_MODEL)
    pe.add_argument("--gate", action="store_true", help="对已知阈值问题输出门控判定")

    pa = sub.add_parser("audit", help="100 倍杠杆审计门控(内置 4 题,需 --state-file)")
    pa.add_argument("--state", help="State(JSON 字符串)")
    pa.add_argument("--state-file", help="State(JSON 文件,必填)")
    pa.add_argument("--api-key", help="TYPESAFE_API_KEY(或设 JEV_API_KEY / scripts/.jev_key)")
    pa.add_argument("--model", default=DEFAULT_MODEL)

    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 0
    key = _read_key(getattr(args, "api_key", None))
    if args.cmd == "probe":
        return _cmd_probe(key)
    if args.cmd in ("evaluate", "judge"):
        return _cmd_evaluate(args, key)
    if args.cmd == "audit":
        return _cmd_audit(args, key)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
