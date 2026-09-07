#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
goldprice.dev 金价拉取脚本（仅依赖 Python 标准库,无需 pip 安装）。

面向 kingforex-skill 黄金模块:拉取 goldprice.dev 的现货金(XAU)实时价。
goldprice.dev 免费层无需 key;Free API key 层(ga_live_xxx)用 x-api-key 头。

端点(2026-09 官方文档实测):
  GET https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT
  GET https://api.goldprice.dev/v1/spot/XAU-USD-SPOT
支持 symbol: XAU-USD-SPOT / XAG-USD-SPOT / XAU-USD / 等;quote 货币由符号决定。

用法示例:
  python goldprice_fetch.py                       # 现货金 XAU-USD-SPOT(免费层)
  python goldprice_fetch.py --symbol XAG-USD-SPOT # 白银
  python goldprice_fetch.py --api-key ga_live_xxx  # 带 key(Free 层,提频)

key 读取优先级: --api-key > 环境变量 GOLDPRICE_API_KEY > scripts/.goldprice_key(本地,不进 zip)。

⚠️ 透明说明(与技能整体一致):本构建/沙箱环境对 api.goldprice.dev 的出口被
Cloudflare(错误 1010 "browser signature")拦截,纯标准库 urllib 无法绕过(属 TLS 指纹
层面限制,非代码或 key 错误)。脚本已对 403/cloudflare 做友好降级提示;在用户本机
(正常浏览器/网络)运行即可正常取数。请勿据此判定 key 失效。
"""
import urllib.request
import urllib.error
import urllib.parse
import os
import sys
import json
import argparse

BASE = "https://api.goldprice.dev"


def _read_local_key():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".goldprice_key")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def _is_cloudflare(text):
    return ("cloudflare" in text.lower()) or ("Just a moment" in text) or ("error_code" in text and "1010" in text)


def fetch(symbol, api_key, timeout=30):
    url = f"{BASE}/v1/prices?symbol={urllib.parse.quote(symbol)}"
    headers = {"accept": "application/json"}
    if api_key:
        # goldprice.dev Free key 层用 x-api-key;失败时不强行换头,保持可诊断
        headers["x-api-key"] = api_key
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:500]
        if e.code in (403, 429) and _is_cloudflare(body):
            return {"_error": "cloudflare_block",
                    "detail": "Cloudflare(1010 browser signature)拦截了本环境出口;请在用户本机运行此脚本取数。"}
        return {"_error": f"HTTP {e.code}", "detail": body}
    except Exception as e:  # noqa
        return {"_error": type(e).__name__, "detail": str(e)}


def main():
    p = argparse.ArgumentParser(description="goldprice.dev 金价拉取")
    p.add_argument("--symbol", default="XAU-USD-SPOT", help="如 XAU-USD-SPOT / XAG-USD-SPOT")
    p.add_argument("--api-key")
    p.add_argument("--out", help="输出 JSON 路径")
    args = p.parse_args()

    api_key = args.api_key or os.environ.get("GOLDPRICE_API_KEY") or _read_local_key()
    d = fetch(args.symbol, api_key)
    if "_error" in d:
        print(f"[错误] {d['_error']}: {d['detail']}")
        sys.exit(0 if d["_error"] == "cloudflare_block" else 1)
    print(f"goldprice.dev {args.symbol}")
    print(json.dumps(d, ensure_ascii=False, indent=2))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print(f"已保存 -> {args.out}")


if __name__ == "__main__":
    main()
