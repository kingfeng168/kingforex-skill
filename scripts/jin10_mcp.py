#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jin10(金十数据) MCP 财经数据客户端 —— 标准 MCP streamable-HTTP 流程(纯标准库)。

标准流程:  initialize -> notifications/initialized -> tools/list / resources/list -> tools/call
推荐协议版本: 2025-11-25
结果读取:  优先 result.structuredContent; result.content 仅作可读文本补充
列表分页:  请求参数 cursor; 响应字段 data.next_cursor / data.has_more

已验证可用工具:
  get_quote({code})            指定品种实时行情
  get_kline({code,time?,count?})  指定品种K线
  list_flash({cursor?})        最新快讯列表
  search_flash({keyword})      按关键词搜索快讯
  list_news({cursor?})         最新资讯列表
  search_news({keyword,cursor?})  按关键词搜索资讯
  get_news({id})               单篇资讯详情
  list_calendar({})            财经日历数据
资源:
  quote://codes                支持的报价品种代码列表

Token 读取优先级: --token > 环境变量 JIN10_TOKEN > scripts/.jin10_key(单行纯文本,不进 zip)
绝不硬编码 Token 到脚本源码或分发产物。
"""
import argparse, json, os, sys, urllib.request, urllib.error

SERVER = "https://mcp.jin10.com/mcp"
PROTOCOL = "2025-11-25"
CLIENT = {"name": "kingforex-skill-jin10", "version": "1.0.0"}


def _read_token(args):
    if getattr(args, "token", None):
        return args.token.strip()
    env = os.environ.get("JIN10_TOKEN")
    if env:
        return env.strip()
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".jin10_key")
    if os.path.isfile(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


class MCPClient:
    def __init__(self, token):
        self.token = token
        self.session = None  # Mcp-Session-Id

    def _post(self, method, params=None, notification=False):
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if not notification:
            # 简单自增 id
            if not hasattr(self, "_id"):
                self._id = 0
            self._id += 1
            payload["id"] = self._id
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(SERVER, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        req.add_header("Authorization", f"Bearer {self.token}")
        if self.session:
            req.add_header("Mcp-Session-Id", self.session)
        try:
            resp = urllib.request.urlopen(req, timeout=40)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            raise RuntimeError(f"HTTP {e.code}: {body[:500]}")
        except Exception as e:
            raise RuntimeError(f"网络错误: {e}")
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
            "protocolVersion": PROTOCOL,
            "capabilities": {},
            "clientInfo": CLIENT,
        })

    def initialized(self):
        self._post("notifications/initialized", notification=True)

    def tools_list(self):
        return self._post("tools/list", {})

    def resources_list(self):
        return self._post("resources/list", {})

    def resources_read(self, uri):
        return self._post("resources/read", {"uri": uri})

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


def _extract(result):
    """优先 structuredContent; 否则回退到 result 自身(含 content/contents)。"""
    if result is None:
        raise RuntimeError("空响应")
    if isinstance(result, dict) and "error" in result and result.get("error"):
        raise RuntimeError(f"JSON-RPC error: {result['error']}")
    res = result.get("result", result) if isinstance(result, dict) else result
    if not isinstance(res, dict):
        return res
    if res.get("isError"):
        txt = _content_text(res.get("content"))
        raise RuntimeError(f"工具业务错误: {txt}")
    if "structuredContent" in res:
        return res["structuredContent"]
    return res  # 回退:含 content/contents


def _content_text(content):
    if not content:
        return ""
    return "\n".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")


def _paginate(client, name, first_args, all_pages):
    items = []
    cursor = None
    while True:
        args = dict(first_args) if first_args else {}
        if cursor:
            args["cursor"] = cursor
        r = client.tools_call(name, args)
        sc = _extract(r)
        data = sc.get("data", {}) if isinstance(sc, dict) else {}
        items.extend(data.get("items", []))
        if not all_pages:
            break
        nxt = data.get("next_cursor")
        if not data.get("has_more") or not nxt:
            break
        cursor = nxt
    return items


def _out(obj, args):
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if getattr(args, "out", None):
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已写出: {args.out}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description="Jin10(金十数据) MCP 客户端")
    ap.add_argument("--token")
    ap.add_argument("--out", help="将结果 JSON 写到文件")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("quote"); p.add_argument("code")
    p = sub.add_parser("kline"); p.add_argument("code"); p.add_argument("--time"); p.add_argument("--count", type=int)
    p = sub.add_parser("flash"); p.add_argument("--cursor"); p.add_argument("--all", action="store_true")
    p = sub.add_parser("flash-search"); p.add_argument("keyword"); p.add_argument("--cursor"); p.add_argument("--all", action="store_true")
    p = sub.add_parser("news"); p.add_argument("--cursor"); p.add_argument("--all", action="store_true")
    p = sub.add_parser("news-search"); p.add_argument("keyword"); p.add_argument("--cursor"); p.add_argument("--all", action="store_true")
    p = sub.add_parser("news-get"); p.add_argument("id")
    p = sub.add_parser("calendar")
    p = sub.add_parser("codes")
    sub.add_parser("tools")
    sub.add_parser("resources")

    args = ap.parse_args()
    token = _read_token(args)
    if not token:
        sys.stderr.write("ERROR: 未找到 Jin10 Token。请通过 --token / 环境变量 JIN10_TOKEN / scripts/.jin10_key 提供。\n")
        sys.exit(2)

    client = MCPClient(token)
    try:
        hi = client.initialize()
        client.initialized()
    except Exception as e:
        sys.stderr.write(f"MCP 握手失败: {e}\n")
        sys.exit(3)

    cmd = args.cmd
    try:
        if cmd == "quote":
            r = client.tools_call("get_quote", {"code": args.code})
            _out(_extract(r), args)
        elif cmd == "kline":
            a = {"code": args.code}
            if args.time: a["time"] = args.time
            if args.count: a["count"] = args.count
            r = client.tools_call("get_kline", a)
            _out(_extract(r), args)
        elif cmd == "flash":
            items = _paginate(client, "list_flash", {"cursor": args.cursor} if args.cursor else {}, args.all)
            _out(items if args.all else _extract(client.tools_call("list_flash", {"cursor": args.cursor} if args.cursor else {})), args)
        elif cmd == "flash-search":
            items = _paginate(client, "search_flash", {"keyword": args.keyword, "cursor": args.cursor} if args.cursor else {"keyword": args.keyword}, args.all)
            _out(items if args.all else _extract(client.tools_call("search_flash", {"keyword": args.keyword, **({"cursor": args.cursor} if args.cursor else {})})), args)
        elif cmd == "news":
            items = _paginate(client, "list_news", {"cursor": args.cursor} if args.cursor else {}, args.all)
            _out(items if args.all else _extract(client.tools_call("list_news", {"cursor": args.cursor} if args.cursor else {})), args)
        elif cmd == "news-search":
            items = _paginate(client, "search_news", {"keyword": args.keyword, "cursor": args.cursor} if args.cursor else {"keyword": args.keyword}, args.all)
            _out(items if args.all else _extract(client.tools_call("search_news", {"keyword": args.keyword, **({"cursor": args.cursor} if args.cursor else {})})), args)
        elif cmd == "news-get":
            r = client.tools_call("get_news", {"id": args.id})
            _out(_extract(r), args)
        elif cmd == "calendar":
            r = client.tools_call("list_calendar", {})
            _out(_extract(r), args)
        elif cmd == "codes":
            r = client.resources_read("quote://codes")
            _out(_extract(r), args)
        elif cmd == "tools":
            r = client.tools_list()
            _out(_extract(r), args)
        elif cmd == "resources":
            r = client.resources_list()
            _out(_extract(r), args)
    except Exception as e:
        sys.stderr.write(f"调用失败: {e}\n")
        sys.exit(4)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except Exception:
            pass
