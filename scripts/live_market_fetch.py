#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
live_market_fetch.py — 实时行情聚合取数脚本（kingforex-skill 内置）

整合本环境「中国大陆网络实测可达、无需 key」的实时/参考行情源：
  1. Frankfurter   (ECB 官方参考汇率, 无 key, 日更)
  2. gold-api.com  (伦敦金/现货黄金, 无 key, 秒级)
  3. US Treasury    (美国财政部 Fiscal Data: 美债收益率/汇率, 无 key)
  4. exchangerate-api (open.er-api.com, 150+ 货币, 无 key, 日更)
  5. 新浪财经        (USDCNY 即期 + 伦敦金 hf_XAU 真实时, 需 Referer + GBK 解码, 非官方)

设计原则（与 kingforex-skill 其他脚本一致）：
  - 纯标准库（urllib/json），无 pip 依赖，跨平台。
  - 所有凭证/key 走参数或环境变量，绝不硬编码。
  - 网络/HTTP 错误友好提示，不崩溃。
  - 输出 CSV(UTF-8-SIG) 或 JSON；不指定 --out 时打印到屏幕。

用法示例：
  python scripts/live_market_fetch.py --preset fx_ref --from USD --to CNY,EUR,JPY
  python scripts/live_market_fetch.py --preset gold --out "D:/workbuddy/输出文件/gold.csv"
  python scripts/live_market_fetch.py --preset ust_yield --out "D:/workbuddy/输出文件/ust.csv"
  python scripts/live_market_fetch.py --preset fx_all
  python scripts/live_market_fetch.py --preset sina --list USDCNY,hf_XAU
  python scripts/live_market_fetch.py --preset all --json
"""
import argparse
import csv
import io
import json
import sys
import urllib.error
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
SINA_REF = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"}

PRESETS = {
    "fx_ref": "Frankfurter ECB 参考汇率",
    "fx_all": "exchangerate-api 全货币",
    "gold": "gold-api.com 现货黄金 XAU",
    "ust_yield": "US Treasury 美债收益率/汇率",
    "sina": "新浪 USDCNY + 伦敦金 真实时",
    "all": "以上全部聚合",
}


def _http_get(url, headers=None, timeout=25, encoding="utf-8"):
    """返回 (ok, text_or_errmsg)。非 UTF-8(GBK) 显式指定 encoding。"""
    try:
        req = urllib.request.Request(url, headers=headers or UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        try:
            return True, raw.decode(encoding)
        except UnicodeDecodeError:
            return True, raw.decode("gbk", "ignore")
    except urllib.error.HTTPError as e:
        return False, "HTTPError %d: %s" % (e.code, e.reason)
    except Exception as e:  # noqa: BLE001 - 统一透传为字符串
        return False, "%s: %s" % (type(e).__name__, str(e)[:160])


def _emit(rows, out, as_json):
    """rows: list[dict]; 统一输出。"""
    if as_json:
        text = json.dumps(rows, ensure_ascii=False, indent=2)
    else:
        buf = io.StringIO()
        w = csv.writer(buf)
        if rows:
            w.writerow(list(rows[0].keys()))
            for r in rows:
                w.writerow([r.get(k, "") for k in rows[0].keys()])
        text = buf.getvalue()
    if out:
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            f.write(text)
        print("已写出 %d 行 -> %s" % (len(rows), out))
    else:
        print(text)


# ---------- 各预设实现 ----------

def p_fx_ref(args):
    frm = args.fr or "USD"
    to = args.to or "CNY,EUR,JPY"
    url = "https://api.frankfurter.app/latest?from=%s&to=%s" % (frm, to)
    ok, txt = _http_get(url)
    if not ok:
        return [{"error": txt}]
    try:
        d = json.loads(txt)
    except Exception as e:  # noqa: BLE001
        return [{"error": "JSON解析失败: %s" % e}]
    rows = []
    for k, v in (d.get("rates") or {}).items():
        rows.append({"source": "Frankfurter(ECB)", "base": d.get("base"),
                     "date": d.get("date"), "currency": k, "rate": v})
    return rows


def p_fx_all(args):
    url = "https://open.er-api.com/v6/latest/%s" % (args.fr or "USD")
    ok, txt = _http_get(url)
    if not ok:
        return [{"error": txt}]
    try:
        d = json.loads(txt)
    except Exception as e:  # noqa: BLE001
        return [{"error": "JSON解析失败: %s" % e}]
    rows = []
    for k, v in (d.get("rates") or {}).items():
        rows.append({"source": "exchangerate-api", "base": d.get("base_code"),
                     "updated": d.get("time_last_update_utc"), "currency": k, "rate": v})
    return rows


def p_gold(args):
    sym = args.symbol or "XAU"
    ok, txt = _http_get("https://api.gold-api.com/price/%s" % sym)
    if not ok:
        return [{"error": txt}]
    try:
        d = json.loads(txt)
    except Exception as e:  # noqa: BLE001
        return [{"error": "JSON解析失败: %s" % e}]
    return [{"source": "gold-api.com", "symbol": d.get("symbol"), "name": d.get("name"),
             "price_usd": d.get("price"), "updated": d.get("updatedAt")}]


def p_ust_yield(args):
    url = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/"
           "accounting/od/rates_of_exchange?filter=record_date:gte:2025-01-01"
           "&sort=-record_date&page[size]=%d" % (args.limit or 20))
    ok, txt = _http_get(url)
    if not ok:
        return [{"error": txt}]
    try:
        d = json.loads(txt)
    except Exception as e:  # noqa: BLE001
        return [{"error": "JSON解析失败: %s" % e}]
    rows = []
    for it in (d.get("data") or []):
        rows.append({"source": "US Treasury", "record_date": it.get("record_date"),
                     "country": it.get("country"), "currency": it.get("currency"),
                     "exchange_rate": it.get("exchange_rate")})
    return rows


def p_sina(args):
    lst = args.lst or "USDCNY,hf_XAU"
    ok, txt = _http_get("https://hq.sinajs.cn/list=%s" % lst, headers=SINA_REF)
    if not ok:
        return [{"error": txt}]
    rows = []
    for line in txt.split(";"):
        line = line.strip()
        if not line or "=" not in line:
            continue
        var, val = line.split("=", 1)
        name = var.replace("var hq_str_", "").strip()
        fields = [x for x in val.strip().strip('"').split(",") if x != ""]
        # 外汇 USDCNY: 时间,买价,卖价,中间价,... -> 价格取 fields[1]
        # 伦敦金 hf_XAU / 黄金T+D gds_AUTD: 买价,卖价,...,时间 -> 价格取 fields[0], 时间取 fields[6]
        if "XAU" in name or "AUTD" in name or "SILV" in name:
            price = fields[0] if fields else ""
            ctime = fields[6] if len(fields) > 6 else ""
        else:
            price = fields[1] if len(fields) > 1 else ""
            ctime = fields[0] if fields else ""
        rows.append({"source": "sina(实时)", "symbol": name, "last": price, "time": ctime})
    if not rows:
        return [{"error": "新浪返回为空或解析失败; 确认带 Referer 头(脚本已内置)"}]
    return rows


DISPATCH = {
    "fx_ref": p_fx_ref,
    "fx_all": p_fx_all,
    "gold": p_gold,
    "ust_yield": p_ust_yield,
    "sina": p_sina,
}


def main():
    ap = argparse.ArgumentParser(description="kingforex 实时行情聚合取数(标准库)")
    ap.add_argument("--preset", required=True, choices=list(PRESETS.keys()),
                    help="预设: " + ", ".join("%s=%s" % (k, v) for k, v in PRESETS.items()))
    ap.add_argument("--from", dest="fr", help="基准货币(用于 fx_ref/fx_all)")
    ap.add_argument("--to", help="目标货币,逗号分隔(用于 fx_ref)")
    ap.add_argument("--symbol", help="金属符号(默认 XAU)")
    ap.add_argument("--list", dest="lst", help="新浪代码列表,逗号分隔(默认 USDCNY,hf_XAU)")
    ap.add_argument("--limit", type=int, help="USTreasury 返回条数(默认 20)")
    ap.add_argument("--out", help="输出 CSV 路径(不指定则打印屏幕)")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而非 CSV")
    args = ap.parse_args()

    if args.preset == "all":
        rows = []
        for key in ["fx_ref", "fx_all", "gold", "ust_yield", "sina"]:
            rows.extend(DISPATCH[key](args))
    else:
        rows = DISPATCH[args.preset](args)
    _emit(rows, args.out, args.json)


if __name__ == "__main__":
    main()
