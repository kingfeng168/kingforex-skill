# -*- coding: utf-8 -*-
"""
mt5_local_kline.py —— 从本机运行中的 MT5 终端拉取日线 K 线(本地软件数据, 优先于外部 API)

定位(2026-09-29 v2.10.0 新增):
  kingforex-skill 的「今日行情分析」生成器 `gen_decision_enhanced_v256.py` 以
  `KINGFOREX_DATA/kline/kline_{SYM}_1d.csv` 为唯一盘面数据层。本脚本把**本地 MT5 软件**
  提升为该数据层的**第一优先数据源**:MT5 终端登录后, 用 MetaTrader5 Python API
  拉取真实 H1 历史, 聚合为日线, 写出生成器可直接消费的 CSV。
  MT5 拉不到的品种(如 USDKRW)由调用方回退到 Twelve Data / 外部源补齐 —— 本地优先、
  外部兜底, 绝不静默用旧快照充当最新, 绝不编造价格。

依赖: MetaTrader5 包(pip install MetaTrader5, 已含 numpy); MT5 终端需已登录账户。
输出: <KINGFOREX_DATA>/kline/kline_{SYM}_1d.csv
  列: datetime(北京日期 YYYY-MM-DD), open, high, low, close, volume
  (与 kline_fetch.py / Twelve Data 产出的生成器格式完全一致)

用法:
  python mt5_local_kline.py                       # 拉取全部 MT5 可得品种
  python mt5_local_kline.py --symbols EURUSD,USDJPY   # 指定品种
  python mt5_local_kline.py --out-dir <目录>        # 指定输出目录(默认 KINGFOREX_DATA)

退出码: 0=至少 1 个品种成功; 1=全部失败; 2=参数错; 3=依赖缺失(MT5 包未装)
"""
import os
import sys
import csv
import datetime
import argparse

try:
    import MetaTrader5 as mt5
except ImportError:
    sys.stderr.write("[mt5_local_kline] MetaTrader5 包未安装, 请 pip install MetaTrader5\n")
    sys.exit(3)

# ── 生成器所需的 7 个日线标的 ──────────────────────────────────
GEN_SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "AUDJPY", "USDKRW"]

# ── MT5 终端内可实际拉取的品种(实测; USDKRW 不在 MT5, 由外部源补齐) ──
MT5_AVAILABLE = {"XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "AUDJPY"}

# 分块拉取 H1(单次 copy_rates_range 有棒数上限, 超出返回 None; 与 mt5_pull.py 同策略)
_CHUNKS = [
    (datetime.datetime(2016, 1, 1), datetime.datetime(2019, 12, 31)),
    (datetime.datetime(2020, 1, 1), datetime.datetime(2023, 12, 31)),
    (datetime.datetime(2024, 1, 1), datetime.datetime.now()),
]


def _beijing(ts):
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.fromtimestamp(int(ts), tz)


def pull_h1(symbol):
    """拉取单品种 H1 全量历史(分块拼接), 返回 list of rows(每行 dict)。失败返回 None。"""
    if not mt5.initialize():
        sys.stderr.write("[mt5_local_kline] MT5 initialize() 失败: %s\n" % mt5.last_error())
        return None
    if not mt5.symbol_select(symbol, True):
        sys.stderr.write("[mt5_local_kline] symbol_select 失败: %s\n" % symbol)
        return None
    bars = []
    for a, b in _CHUNKS:
        r = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_H1, a, b)
        if r is not None and len(r):
            bars.extend(r)
        # 短暂间隔避免限流
        # (MetaTrader5 本地 DLL 调用无需间隔, 保留以防未来切网络模式)
    if not bars:
        return None
    return bars


def aggregate_daily(bars):
    """H1 棒 -> 日线(北京日期): open=首根开, high=max, low=min, close=末根收, volume=求和。"""
    from collections import OrderedDict
    days = OrderedDict()
    for r in bars:
        d = _beijing(r["time"]).strftime("%Y-%m-%d")
        o, h, l, c, v = float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), int(r["tick_volume"])
        if d not in days:
            days[d] = [o, h, l, c, v]
        else:
            e = days[d]
            e[1] = max(e[1], h)
            e[2] = min(e[2], l)
            e[3] = c
            e[4] += v
    return days


def write_csv(out_csv, days):
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["datetime", "open", "high", "low", "close", "volume"])
        for d, (o, h, l, c, v) in days.items():
            w.writerow([d, o, h, l, c, v])


def main():
    ap = argparse.ArgumentParser(description="从本机 MT5 拉取日线 K 线(本地软件数据, 优先于外部 API)")
    ap.add_argument("--symbols", default=",".join(sorted(MT5_AVAILABLE)),
                    help="逗号分隔的品种(默认 MT5 可得的全部生成器标的)")
    ap.add_argument("--out-dir", default=os.environ.get("KINGFOREX_DATA", "").strip() or None,
                    help="输出目录(须含 kline/ 子目录); 默认取环境变量 KINGFOREX_DATA")
    args = ap.parse_args()

    out_dir = args.out_dir
    if not out_dir:
        ap.error("需要 --out-dir 或环境变量 KINGFOREX_DATA")
    kline_dir = os.path.join(out_dir, "kline")
    os.makedirs(kline_dir, exist_ok=True)

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    unknown = [s for s in symbols if s not in MT5_AVAILABLE]
    if unknown:
        sys.stderr.write("[mt5_local_kline] 警告: 以下品种不在 MT5 可拉取集合内, 跳过: %s\n"
                         % ", ".join(unknown))
    symbols = [s for s in symbols if s in MT5_AVAILABLE]
    if not symbols:
        sys.stderr.write("[mt5_local_kline] 无有效品种可拉取\n")
        return 1

    print("[mt5_local_kline] 开始连接本机 MT5, 拉取 %d 个品种的 H1 日线..." % len(symbols),
          flush=True)
    results = {}
    for s in symbols:
        bars = pull_h1(s)
        if not bars:
            print("  %s: 失败(MT5 无数据/未登录)" % s, flush=True)
            results[s] = None
            continue
        days = aggregate_daily(bars)
        out_csv = os.path.join(kline_dir, "kline_%s_1d.csv" % s)
        write_csv(out_csv, days)
        first, last = next(iter(days)), next(reversed(days))
        print("  %s: OK  %d 根日线  %s ~ %s  ->  %s"
              % (s, len(days), first, last, out_csv), flush=True)
        results[s] = (len(days), first, last)

    ok = sum(1 for v in results.values() if v)
    print("[mt5_local_kline] 完成: %d/%d 品种成功" % (ok, len(symbols)), flush=True)
    mt5.shutdown()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())