#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qveris MCP 金融数据市场客户端 —— kingforex 取数封装(纯标准库,无需 pip)。

qveris 是金融数据**工具市场(MCP 网关)**,非直接数据源。调用流程:
  discover(query) -> inspect(tool_ids) -> probe(免費报价) -> call(计费执行)
call 必须带: tool_id + search_id(注意: search_id 在 discover 结果**顶层**,非工具层级)
            + params_to_tool(真实参数包,路径参数如 symbol 放其内)

已验证可用工具(tool_id 可能随版本微调,脚本优先 discover 动态获取,以下为 2026-09 实测稳定值):
  - 金银现货 : commodity_price_api.rates.live.retrieve.v2.46f86b4e  (params: symbol=xau|xag)
  - 外汇日线 : alphavantage.fx_daily.retrieve.v1.7aca3c4a
  - 外汇实时 : eodhd.live_data.real_time.retrieve.v1.b60a4285
  - FRED 宏观 : stlouisfed_fred.* (discover 按系列名/ID 动态取)

Token 读取优先级: --api-key > 环境变量 QVERIS_API_KEY > scripts/.qveris_key > ~/.workbuddy/mcp.json
                  (mcpServers.qveris.headers.Authorization 的 Bearer token)
绝不硬编码 Token 到脚本源码或分发产物。

计费: 单次 call ~9.55 credits(2026-09 实测),账户额度 1000;用尽前关注 `credits` 子命令。
取数铁律: 任一 call 失败/超时/返空,仅报告原因并跳过该品种,**绝不编造、估算或凭记忆生成任何价格**。
"""
import argparse, json, os, sys, urllib.request, urllib.error

SERVER = "https://mcp.qveris.ai/mcp"
PROTOCOL = "2024-11-05"
CLIENT = {"name": "kingforex-skill-qveris", "version": "1.0.0"}

# 已知稳定 tool_id(2026-09 验证);discover 会动态刷新覆盖
KNOWN = {
    "spot": "commodity_price_api.rates.live.retrieve.v2.46f86b4e",
    "fx_daily": "alphavantage.fx_daily.retrieve.v1.7aca3c4a",
    "fx_live": "eodhd.live_data.real_time.retrieve.v1.b60a4285",
}


def _read_token(args):
    if getattr(args, "api_key", None):
        return args.api_key.strip()
    env = os.environ.get("QVERIS_API_KEY")
    if env:
        return env.strip()
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".qveris_key")
    if os.path.isfile(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    # 回退:从用户级 mcp.json 解析 qveris 的 Authorization Bearer
    mcp = os.path.expanduser("~/.workbuddy/mcp.json")
    if os.path.isfile(mcp):
        try:
            with open(mcp, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            auth = cfg.get("mcpServers", {}).get("qveris", {}).get("headers", {}).get("Authorization", "")
            if auth.startswith("Bearer "):
                return auth[len("Bearer "):].strip()
        except Exception:
            pass
    return None


class MCPClient:
    def __init__(self, token):
        self.token = token
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
        return self._post("initialize", {"protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": CLIENT})

    def initialized(self):
        self._post("notifications/initialized", notification=True)

    def tools_list(self):
        return self._post("tools/list", {})

    def tools_call(self, name, arguments=None):
        return self._post("tools/call", {"name": name, "arguments": arguments or {}})

    # --- qveris 市场专用封装 ---
    def discover(self, query):
        return self.tools_call("discover", {"query": query})

    def inspect(self, tool_ids):
        if isinstance(tool_ids, str):
            tool_ids = [tool_ids]
        return self.tools_call("inspect", {"tool_ids": tool_ids})

    def probe(self, tool_id, search_id, params_to_tool=None):
        return self.tools_call("probe", {"tool_id": tool_id, "search_id": search_id, "params_to_tool": params_to_tool or {}})

    def call(self, tool_id, search_id, params_to_tool=None):
        return self.tools_call("call", {"tool_id": tool_id, "search_id": search_id, "params_to_tool": params_to_tool or {}})


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
    return "\n".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")


def _extract(result):
    """解析 tools/call 结果:优先 content[].text(JSON) -> structuredContent -> 自身。"""
    if result is None:
        raise RuntimeError("空响应")
    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError(f"JSON-RPC error: {result['error']}")
    res = result.get("result", result) if isinstance(result, dict) else result
    if not isinstance(res, dict):
        return res
    if res.get("isError"):
        raise RuntimeError(f"工具业务错误: {_content_text(res.get('content'))}")
    if "content" in res:
        txt = _content_text(res.get("content"))
        try:
            return json.loads(txt)
        except Exception:
            return {"_raw": txt}
    if "structuredContent" in res:
        return res["structuredContent"]
    return res


def _pick_tool(discovered, preferred_id=None, prefer_keyword=None):
    """从 discover 结果选取 tool_id,返回 (tool_id, search_id)。"""
    d = discovered if isinstance(discovered, dict) else {}
    search_id = d.get("search_id")
    tools = d.get("results") or d.get("tools") or []
    target = None
    if preferred_id:
        for t in tools:
            if (t.get("tool_id") or "") == preferred_id:
                target = t; break
        if target is None:
            target = {"tool_id": preferred_id}  # discover 未命中则直接用已知 id(仍需 search_id)
    elif prefer_keyword:
        for t in tools:
            nm = (t.get("name") or "").lower()
            tid = (t.get("tool_id") or "").lower()
            if prefer_keyword in nm or prefer_keyword in tid:
                target = t; break
    if target is None and tools:
        target = tools[0]
    if target is None:
        raise RuntimeError("discover 未返回任何工具")
    return target.get("tool_id"), search_id


def _extract_payload(r):
    """从 qveris call 信封中抽取工具真实返回数据(dict)。

    qveris 大结果会被截断:小结果在 result.data;超长结果在 result.truncated_content(JSON 字符串)
    或提供 result.full_content_file_url(需另行下载);此处优先 data,其次 truncated_content。
    """
    if not isinstance(r, dict):
        return r
    res = r.get("result") or {}
    if isinstance(res, dict) and isinstance(res.get("data"), dict):
        return res["data"]
    if isinstance(res, dict) and res.get("truncated_content"):
        try:
            return json.loads(res["truncated_content"])
        except Exception:
            return {"_truncated": res["truncated_content"][:500]}
    if isinstance(res, dict) and res.get("full_content_file_url"):
        return {"_full_url": res["full_content_file_url"], "status_code": res.get("status_code")}
    return res


def _flatten_av_timeseries(payload, last_n=None):
    """Alpha Vantage 'Time Series FX (Daily)' 等 -> 升序 [(date,o,h,l,c)]。"""
    ts_key = None
    for k in payload:
        if "Time Series" in k:
            ts_key = k; break
    if not ts_key:
        return None
    rows = []
    for date, ohlc in payload[ts_key].items():
        rows.append((
            date,
            ohlc.get("1. open") or ohlc.get("open"),
            ohlc.get("2. high") or ohlc.get("high"),
            ohlc.get("3. low") or ohlc.get("low"),
            ohlc.get("4. close") or ohlc.get("close"),
        ))
    rows.sort(key=lambda x: x[0])
    if last_n:
        rows = rows[-last_n:]
    return rows



# ---------------- 高层命令 ----------------

def cmd_spot(client, args):
    """金银现货: commodity_price_api.rates.live (symbol=xau|xag)。"""
    sym = args.symbol.lower()
    d = _extract(client.discover("live gold silver spot price XAU XAG OTC"))
    tid, sid = _pick_tool(d, preferred_id=args.tool_id or KNOWN["spot"])
    r = _extract(client.call(tid, sid, {"symbol": sym}))
    data = _extract_payload(r)
    if not data.get("success", True):
        raise RuntimeError(f"数据源返回失败: {data}")
    rates = data.get("rates", {})
    row = rates.get(sym.upper()) or rates.get(sym)
    if not row:
        raise RuntimeError(f"未返回 {sym.upper()} 价格; 可用键: {list(rates.keys())}")
    meta = data.get("metadata", {}).get(sym.upper()) or {}
    out = {
        "symbol": sym.upper(),
        "rate": row.get("rate"),
        "bid": row.get("bid"),
        "ask": row.get("ask"),
        "unit": meta.get("unit"),
        "quote": meta.get("quote"),
        "timestamp": data.get("timestamp"),
        "source": "qveris:commodity_price_api.rates.live",
        "cost_credits": r.get("cost"),
    }
    return out


def cmd_fx(client, args):
    """外汇: 日线(fx_daily, from/to_symbol)或实时(live, EODHD symbol=XXX.FOREX)。"""
    sym = args.symbol.upper()
    if len(sym) != 6:
        raise RuntimeError(f"外汇符号需为 6 字母(如 USDJPY / AUDJPY), 收到: {sym}")
    from_sym, to_sym = sym[:3], sym[3:]
    d = _extract(client.discover(f"forex {args.kind} OHLC {sym} historical candles"))
    if args.kind == "daily":
        tid, sid = _pick_tool(d, preferred_id=KNOWN["fx_daily"])
        params = {"function": "FX_DAILY", "from_symbol": from_sym, "to_symbol": to_sym}
        # 固定 compact(100 根):full 会触发 qveris 截断 Alpha Vantage 超长 JSON 导致解析失败;
        # 100 根日线已覆盖 RSI14/MA20/50/200,足够 swing 级 TA。args.last 仅用于在 100 内截取。
        params["outputsize"] = "compact"
    else:  # live
        tid, sid = _pick_tool(d, preferred_id=KNOWN["fx_live"])
        params = {"symbol": f"{sym}.FOREX"}
    r = _extract(client.call(tid, sid, params))
    payload = _extract_payload(r)
    meta = payload.get("Meta Data", {}) if isinstance(payload, dict) else {}
    rows = _flatten_av_timeseries(payload, args.last) if args.kind == "daily" else None
    out = {
        "symbol": sym, "kind": args.kind, "meta": meta,
        "last": rows[-1] if rows else None, "bars": len(rows) if rows else None,
        "source": "qveris", "cost_credits": r.get("cost"),
    }
    if args.csv and rows:
        import csv as _csv
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = _csv.writer(f)
            w.writerow(["Date", "Open", "High", "Low", "Close"])
            for dt, o, h, l, c in rows:
                w.writerow([dt, o, h, l, c])
        out["csv_written"] = args.csv
    else:
        out["payload"] = payload
    return out


def cmd_fred(client, args):
    """FRED 宏观系列: 按 series ID discover 动态取 stlouisfed_fred 工具。"""
    series = args.series.upper()
    d = _extract(client.discover(f"FRED series {series} observations"))
    tid, sid = _pick_tool(d, prefer_keyword="stlouisfed_fred")
    # 参数名未知,先 probe 取 schema(免費)
    pr = _extract(client.probe(tid, sid, {"series_id": series}))
    params = {"series_id": series}
    if args.last:
        params["limit"] = args.last
    r = _extract(client.call(tid, sid, params))
    return {"series": series, "raw": r, "source": "qveris:stlouisfed_fred", "cost_credits": r.get("cost")}


def cmd_discover(client, args):
    d = _extract(client.discover(args.query))
    tools = d.get("results") or d.get("tools") or []
    out = {"search_id": d.get("search_id"), "total": d.get("total"), "hits": []}
    for t in tools[: args.top]:
        out["hits"].append({
            "tool_id": t.get("tool_id"),
            "name": t.get("name"),
            "expected_cost": t.get("expected_cost"),
            "success_rate": (t.get("stats") or {}).get("success_rate"),
        })
    return out


def cmd_inspect(client, args):
    return _extract(client.inspect(args.tool_id))


def cmd_probe(client, args):
    params = json.loads(args.params) if args.params else {}
    d = _extract(client.discover(args.query)) if args.query else None
    sid = d.get("search_id") if d else args.search_id
    return _extract(client.probe(args.tool_id, sid, params))


def cmd_call(client, args):
    params = json.loads(args.params) if args.params else {}
    return _extract(client.call(args.tool_id, args.search_id, params))


def cmd_credits(client, args):
    return _extract(client.tools_call("credits_ledger", {}))


def _out(obj, args):
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if getattr(args, "out", None):
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已写出: {args.out}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description="qveris MCP 金融数据市场客户端(kingforex)")
    ap.add_argument("--api-key", help="qveris Bearer token")
    ap.add_argument("--out", help="结果 JSON 写到文件")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("spot"); p.add_argument("--symbol", required=True, help="XAU 或 XAG(金银)")
    p.add_argument("--tool-id", help="覆盖工具 ID")
    p = sub.add_parser("fx"); p.add_argument("--symbol", required=True, help="如 USDJPY/EURUSD/AUDJPY")
    p.add_argument("--kind", choices=["daily", "live"], default="daily"); p.add_argument("--last", type=int)
    p.add_argument("--csv", help="将日线时间序列扁平化为 CSV(Date,Open,High,Low,Close) 写入该路径")
    p = sub.add_parser("fred"); p.add_argument("--series", required=True, help="FRED 系列 ID, 如 DGS10")
    p.add_argument("--last", type=int)
    p = sub.add_parser("discover"); p.add_argument("--query", required=True); p.add_argument("--top", type=int, default=8)
    p = sub.add_parser("inspect"); p.add_argument("--tool-id", required=True)
    p = sub.add_parser("probe"); p.add_argument("--tool-id", required=True); p.add_argument("--search-id")
    p.add_argument("--query"); p.add_argument("--params", help='JSON 字符串, 如 {"symbol":"xag"}')
    p = sub.add_parser("call"); p.add_argument("--tool-id", required=True); p.add_argument("--search-id", required=True)
    p.add_argument("--params", help="JSON 字符串")
    sub.add_parser("credits")
    sub.add_parser("tools")

    args = ap.parse_args()
    token = _read_token(args)
    if not token:
        sys.stderr.write("ERROR: 未找到 qveris Token。请通过 --api-key / 环境变量 QVERIS_API_KEY / scripts/.qveris_key / ~/.workbuddy/mcp.json 提供。\n")
        sys.exit(2)

    client = MCPClient(token)
    try:
        client.initialize()
        client.initialized()
    except Exception as e:
        sys.stderr.write(f"MCP 握手失败: {e}\n")
        sys.exit(3)

    try:
        if args.cmd == "spot":
            _out(cmd_spot(client, args), args)
        elif args.cmd == "fx":
            _out(cmd_fx(client, args), args)
        elif args.cmd == "fred":
            _out(cmd_fred(client, args), args)
        elif args.cmd == "discover":
            _out(cmd_discover(client, args), args)
        elif args.cmd == "inspect":
            _out(cmd_inspect(client, args), args)
        elif args.cmd == "probe":
            _out(cmd_probe(client, args), args)
        elif args.cmd == "call":
            _out(cmd_call(client, args), args)
        elif args.cmd == "credits":
            _out(cmd_credits(client, args), args)
        elif args.cmd == "tools":
            _out(_extract(client.tools_list()), args)
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
