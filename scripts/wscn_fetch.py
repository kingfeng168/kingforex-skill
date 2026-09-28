#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""华尔街见闻 MCP 客户端 —— kingforex 资讯取数封装(纯标准库,无需 pip)。

服务端: xgbmcp-market-data v0.1.0 (streamable-http)
端点  : https://xgb-mcp-api.xuangubao.cn/mcp
必需头: Authorization: Bearer <key>  +  X-WMCP-Client: wbwscn   ← 两者缺一即 401/403

三个只读工具(2026-09-17 实测可用):
  get_wscn_global_articles       全球资讯列表(date, 默认当天, 仅近两个月)
  get_wscn_global_article_detail 单篇正文(date + id, 两者必填)
  get_large_stocks               A股大涨股异动(date, 默认当天, 仅近两个月)

Token 读取优先级: --api-key > 环境变量 WSCN_API_KEY > scripts/.wscn_key
                  > ~/.workbuddy/connectors/<uuid>/mcp.json 中 connector:wscnmcp-token 的
                    ${WSCN_API_KEY} 引用(仅提示,不解析密文)
绝不硬编码 Token 到脚本源码或分发产物。

定位: 本模块是 kingforex 的**第二资讯源**,与金十数据(jin10 MCP)互补:
  - 金十  → 实时快闪、报价、财经日历(高频、速报)
  - 见闻  → 全球资讯深度摘要 + 异动逻辑归因(中低频、含因果链)
用途: 为宏观大事、地缘风险、原油供应冲击等事件提供**交叉验证**,不替代金十。

取数铁律: 任一调用失败/超时/返空,仅报告原因并跳过该条,**绝不编造、估算或凭记忆生成任何资讯内容**。
"""
import argparse
import datetime
import io
import json
import os
import sys
import urllib.error
import urllib.request

SERVER = "https://xgb-mcp-api.xuangubao.cn/mcp"
PROTOCOL = "2024-11-05"
CLIENT = {"name": "kingforex-skill-wscn", "version": "1.0.0"}
CLIENT_HEADER = "wbwscn"

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.environ.get("KINGFOREX_HOME", os.path.dirname(_HERE))
_DATA = os.environ.get("KINGFOREX_DATA", os.path.join(_ROOT, "KingForex数据", "output"))


# ---------------------------------------------------------------------------
# Token 解析
# ---------------------------------------------------------------------------
def _read_token(args=None):
    if args is not None and getattr(args, "api_key", None):
        return args.api_key.strip()
    env = os.environ.get("WSCN_API_KEY")
    if env:
        return env.strip()
    p = os.path.join(_HERE, ".wscn_key")
    if os.path.isfile(p):
        with io.open(p, encoding="utf-8") as f:
            return f.read().strip()
    return None


# ---------------------------------------------------------------------------
# MCP 客户端
# ---------------------------------------------------------------------------
class MCPClient:
    def __init__(self, token, timeout=30):
        self.token = token
        self.timeout = timeout
        self.session = None
        self._id = 0

    def _post(self, method, params=None, notification=False):
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if not notification:
            self._id += 1
            payload["id"] = self._id
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(SERVER, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        req.add_header("Authorization", "Bearer " + self.token)
        # 该头是华尔街见闻网关的必需标识,缺失会被拒绝
        req.add_header("X-WMCP-Client", CLIENT_HEADER)
        if self.session:
            req.add_header("Mcp-Session-Id", self.session)
        try:
            resp = urllib.request.urlopen(req, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            raise RuntimeError("HTTP %s: %s" % (e.code, body[:400]))
        except Exception as e:
            raise RuntimeError("网络错误: %s" % e)
        sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
        if sid:
            self.session = sid
        ctype = resp.headers.get("Content-Type", "")
        raw = resp.read().decode("utf-8", "replace")
        if "text/event-stream" in ctype:
            return _parse_sse(raw)
        if not raw.strip():
            return None
        return json.loads(raw)

    def initialize(self):
        return self._post("initialize", {
            "protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": CLIENT})

    def initialized(self):
        self._post("notifications/initialized", notification=True)

    def tools_list(self):
        return self._post("tools/list", {})

    def tools_call(self, name, arguments=None):
        return self._post("tools/call", {"name": name, "arguments": arguments or {}})


def _parse_sse(raw):
    last = None
    for block in raw.split("\n\n"):
        data_line = None
        for line in block.split("\n"):
            if line.startswith("data:"):
                data_line = line[len("data:"):].strip()
        if data_line:
            try:
                last = json.loads(data_line)
            except Exception:
                pass
    return last


def _content_text(content):
    if not content:
        return ""
    return "\n".join(c.get("text", "") for c in content
                     if isinstance(c, dict) and c.get("type") == "text")


def _extract(result):
    """解析 tools/call 结果: content[].text(JSON 串) -> structuredContent -> 自身。"""
    if result is None:
        raise RuntimeError("空响应")
    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError("JSON-RPC error: %s" % result["error"])
    res = result.get("result", result) if isinstance(result, dict) else result
    if not isinstance(res, dict):
        return res
    if res.get("isError"):
        raise RuntimeError("工具业务错误: %s" % _content_text(res.get("content")))
    if "content" in res:
        txt = _content_text(res.get("content"))
        try:
            return json.loads(txt)
        except Exception:
            return {"_raw": txt}
    if "structuredContent" in res:
        return res["structuredContent"]
    return res


# ---------------------------------------------------------------------------
# 业务封装
# ---------------------------------------------------------------------------
class WSCN:
    def __init__(self, token, timeout=30):
        self.c = MCPClient(token, timeout=timeout)
        self.c.initialize()
        try:
            self.c.initialized()
        except Exception:
            pass

    def global_articles(self, date=None):
        """全球资讯列表(不含正文)。返回 list[dict]。"""
        args = {}
        if date:
            args["date"] = date
        d = _extract(self.c.tools_call("get_wscn_global_articles", args))
        if isinstance(d, dict):
            return d.get("articles", []) or []
        return d if isinstance(d, list) else []

    def article_detail(self, date, article_id):
        """单篇正文。date 与 id 均为必填。"""
        d = _extract(self.c.tools_call("get_wscn_global_article_detail",
                                       {"date": date, "id": int(article_id)}))
        return d

    def large_stocks(self, date=None):
        """A股大涨股异动板块。返回 list[dict]。"""
        args = {}
        if date:
            args["date"] = date
        d = _extract(self.c.tools_call("get_large_stocks", args))
        if isinstance(d, dict):
            return d.get("plates", []) or []
        return d if isinstance(d, list) else []


# ---------------------------------------------------------------------------
# 事件关键词 —— 与外汇/贵金属/大宗交易直接相关
# ---------------------------------------------------------------------------
KEYWORDS = [
    # 央行 / 货币政策
    "美联储", "Fed", "鲍威尔", "加息", "降息", "利率决议", "点阵图", "缩表", "扩表",
    "欧央行", "ECB", "拉加德", "日本央行", "BOJ", "植田", "央行", "议息",
    # 汇率 / 美元
    "美元指数", "人民币", "日元", "欧元", "英镑", "澳元", "汇率", "中间价", "外汇",
    # 贵金属
    "黄金", "金价", "白银", "银价", "贵金属", "央行购金", "实际利率",
    # 原油 / 能源 / 地缘
    "原油", "油价", "布伦特", "WTI", "OPEC", "欧佩克", "减产", "增产",
    "霍尔木兹", "管道", "无人机", "袭击", "制裁", "地缘", "红海", "胡塞",
    # 通胀 / 就业 / 宏观
    "CPI", "通胀", "PCE", "非农", "失业率", "GDP", "PMI", "零售", "国债收益率",
    # 风险
    "关税", "贸易", "衰退", "避险", "VIX", "评级",
]


def rank_articles(articles, keywords=None, top=None):
    """按事件相关度排序:命中关键词越多越靠前,同分按时间倒序。"""
    kws = keywords if keywords is not None else KEYWORDS
    scored = []
    for a in articles:
        if not isinstance(a, dict):
            continue
        blob = "%s %s" % (a.get("title", ""), a.get("summary", ""))
        hits = [k for k in kws if k in blob]
        scored.append((len(hits), a.get("displayTime", 0) or 0, hits, a))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    out = []
    for n, _t, hits, a in scored:
        item = dict(a)
        item["_hits"] = hits
        item["_score"] = n
        out.append(item)
    if top:
        out = out[:top]
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _out(obj, path=None):
    txt = json.dumps(obj, ensure_ascii=False, indent=2)
    if path:
        d = os.path.dirname(os.path.abspath(path))
        if d and not os.path.isdir(d):
            os.makedirs(d)
        io.open(path, "w", encoding="utf-8", newline="").write(txt)
        print("已写入: %s (%d 字节)" % (path, os.path.getsize(path)))
    else:
        print(txt)


def main():
    # 全局参数同时注册到主解析器与各子解析器(父解析器共享)，
    # 这样 `--date` 放在子命令前后都能识别。
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--api-key", default=None, help="覆盖 .wscn_key")
    common.add_argument("--date", default=None, help="日期 YYYY-MM-DD(默认当天)")
    common.add_argument("--out", default=None, help="JSON 输出路径")
    common.add_argument("--timeout", type=int, default=30)
    common.add_argument("--top", type=int, default=15, help="relevant 返回条数(默认 15)")

    ap = argparse.ArgumentParser(
        description="华尔街见闻 MCP 取数 —— kingforex-skill 第二资讯源",
        parents=[common])
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("articles", parents=[common], help="全球资讯列表")
    sub.add_parser("relevant", parents=[common], help="按交易事件相关度排序的资讯(推荐)")

    p_det = sub.add_parser("detail", parents=[common], help="单篇正文")
    p_det.add_argument("aid", type=int, help="文章 ID")

    sub.add_parser("stocks", parents=[common], help="A股大涨股异动")
    sub.add_parser("probe", parents=[common], help="连通性 + 工具清单自检")

    args = ap.parse_args()

    token = _read_token(args)
    if not token:
        print("[错误] 未找到华尔街见闻 API Key。")
        print("       请设置环境变量 WSCN_API_KEY，或把 Key 写入 scripts/.wscn_key")
        return 2

    try:
        w = WSCN(token, timeout=args.timeout)
    except Exception as e:
        print("[连接失败] %s" % e)
        return 1

    cmd = args.cmd or "relevant"
    date = args.date or datetime.date.today().isoformat()

    try:
        if cmd == "probe":
            tl = w.c.tools_list()
            res = tl.get("result", tl) if isinstance(tl, dict) else {}
            tools = res.get("tools", []) if isinstance(res, dict) else []
            print("连接成功 -> %s" % SERVER)
            print("服务端: %s" % res.get("serverInfo", {}))
            print("工具数: %d" % len(tools))
            for t in tools:
                print("  - %s" % t.get("name"))
            return 0

        if cmd == "articles":
            arts = w.global_articles(date)
            print("日期 %s · 资讯 %d 条" % (date, len(arts)))
            _out(arts, args.out)
            return 0

        if cmd == "relevant":
            arts = w.global_articles(date)
            ranked = rank_articles(arts, top=args.top)
            hot = [a for a in ranked if a["_score"] > 0]
            print("日期 %s · 全量 %d 条 · 命中交易事件 %d 条 · 输出前 %d 条"
                  % (date, len(arts), len(hot), len(ranked)))
            print()
            for i, a in enumerate(ranked, 1):
                mark = "★%d" % a["_score"] if a["_score"] else " ·"
                print("%2d %s %s" % (i, mark, a.get("title", "")))
                if a["_hits"]:
                    print("      命中: %s" % " ".join(a["_hits"][:8]))
            _out(ranked, args.out)
            return 0

        if cmd == "detail":
            d = w.article_detail(args.date, args.aid)
            _out(d, args.out)
            return 0

        if cmd == "stocks":
            plates = w.large_stocks(date)
            total = sum(len(p.get("stocks", [])) for p in plates if isinstance(p, dict))
            print("日期 %s · 异动板块 %d 个 · 个股 %d 只" % (date, len(plates), total))
            _out(plates, args.out)
            return 0

    except Exception as e:
        print("[取数失败] %s" % e)
        print("  提示: 该 MCP 仅提供近两个月数据; date 格式须为 YYYY-MM-DD。")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
