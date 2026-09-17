# daily_data.json 数据契约（报告生成器参数化驱动）

> 配套 `scripts/gen_report_param.py` —— 今日行情分析·决策增强版 的**参数化入口**。
> 本文件定义 `daily_data.json` 的全部字段。每日只需填一份 `daily_data_<YYYY-MM-DD>.json`，
> 再跑 `gen_report_param.py --date <日期> --data <json> --kline-dir <csv目录> --out <输出目录>`
> 即可产出与「硬编码快照版」完全一致的 HTML/MD/XLSX，**零硬编码、零转录误差**。

## 一、顶层结构（37 个 key）

| 分组 | key | 类型 | 说明 |
|------|-----|------|------|
| 元信息 | `meta` | dict | `now`(展示用基准时间字符串) / `now_dt`(ISO, 用于事件循环) / `version`(报告版本戳, 注入标题与页脚) / `badges`(5 个 `{cls,text}` 头部徽章) |
| 账户 | `account` | dict | `equity` / `deposit` / `floating` / `realized` / `cum_ret`(%) / `max_dd`(%)。账户卡片与权益曲线由此渲染 |
| 持仓 | `position` | dict | `entry` / `sl` / `tp` / `sl_orig` / `sl_new` / `exit` / `cur` / `lots_open` / `lots_now` / `risk_usd` / `pct` 等（当前/历史持仓与风控计算） |
| 凯利 | `kelly` | dict | `pip_val` 等凯利计算器输入 |
| 回测 | `backtest` | dict | `bt_*` 信号回测指标 |
| 回测信号 | `bt_signals` | list | `[[name, pips, ...], ...]`（代码内转 tuple） |
| 权益曲线 | `r_curve` | list | 累计 R 序列 |
| 止损 | `stops` | list | 动态止损柱状图数据 |
| 相关性 | `corr_high` / `corr_low` | list | 高/低相关标的对（可选，缺失则空） |
| 报价 | `quotes` | dict | 8 标的实时报价 `{SYM: [price, ...]}`（金/银/美元/欧元/英镑/日元/WTI + AUDJPY） |
| 利率 | `rates` | dict | 关键利率（DGS10 等） |
| 利差 | `carry` | list | 套利/利差数据（可选） |
| 评分 | `scores` | dict | 8 标的四维分 + verdict |
| CFTC | `cftc_gold` | dict | 黄金持仓数据 |
| 交叉 | `cross` | dict | 跨市场交叉读数 |
| 权益日期/值 | `equity_dates` / `equity_vals` | list | 权益曲线横轴/纵轴 |
| 关键位 | `keylevels` | dict | 各标的支撑/阻力 |
| 快照扩展 | `snap_extra` / `snap_nokl` | dict/list | 分析论证节扩展内容 |
| 当日主题 | `day_theme` | dict | 当日结构/叙事主题 |
| 宏观事件 | `macro_events` | str | 宏观事件（当前版本未直接渲染，保留兼容） |
| 列表类 | `other7` / `recommend5` / `discipline6` | list | 其他观察 7 条 / 推荐 5 条 / 纪律 6 条 |
| 央行/利差/地缘/宏观 | `cb_policy` / `carry2` / `geo_risk` / `macro2` | dict/list | 宏观论证节素材 |
| 日历 | `cal_pub` / `cal_pending` / `cal_month` | list | 已公布 / 待公布 / 当月财经日历 |
| 评分附注 | `score_subs` | list | 评分卡子项 |
| K线 | `klines` | dict | `KD` 字典：`{SYM: "kline_<SYM>_1d.csv"}`，指向本地 CSV |
| 事件 | `events` | list | `[{name, time_iso, star}]` 重大事件（FOMC/BoJ 等），驱动事件倒计时循环 |
| 凯利配置 | `inst_config` | dict | 凯利计算器 `INST` JS 对象源（各品种 pip/sl/px/note） |

## 二、K 线 CSV 约定（`klines` 指向的文件）

- 列：`datetime,open,high,low,close`（首行表头）。
- `datetime` 用 `YYYY-MM-DD`（UTC 日）。
- 来源：goldprice.dev `/v1/bars`（黄金/白银）、Twelve Data（外汇/原油）等；
  运行 `python scripts/goldprice_fetch.py --history --symbol XAU-USD-SPOT --from <d1> --to <d2> --out-dir <csv目录>` 直出 `kline_XAUUSD_1d.csv`。
- 缺失任一 CSV 则生成器直接 `SystemExit` 并提示获取方式（不编造价格）。

## 三、每日填写铁律

1. **只改 `daily_data.json`，绝不改 `gen_report_param.py` 的装配逻辑** —— 保证格式与历史报告冻结一致。
2. `meta.now` / `meta.now_dt` / `meta.version` 必须同步当日；`version` 决定报告标题/页脚版本戳。
3. `account.*` 必须反映**当日真实账户状态**（净值/入金/浮盈/已实现/累计%）；卡片与权益曲线全部由它渲染。
4. `events[].time_iso` 用 ISO 8601；`star` 为重要度（★ 数量）。
5. `klines` 各 CSV 须覆盖至**最新交易日**，否则 K 线图 stale。
6. 取数失败 → 在对应字段标注「数据缺失」并降级，**严禁编造价格/评分**（技能铁律）。

## 四、从静态快照生成契约（一次性迁移）

- `scripts/build_daily_json.py`：`importlib` 导入原快照模块 → `json.dump` 全部全局 → 零手工转录。
- `scripts/transform_to_param.py`：删除快照顶部硬编码块、注入 JSON 加载桥 → 生成 `gen_report_param.py`。
- `scripts/parity_check.py`：与原报告逐项比对（字节/节数/外链/CDN/二级标题/关键数值），确保重构零漂移。

## 五、09-14 样例

`scripts/daily_data_20260914.json` 为 37 key 全量样例（真实 09-14 数据），可直接复现
`今日行情分析_决策增强版_2026-09-14.{html,md,xlsx}`，亦作 schema 参考。
开放分发前如需脱敏，可将 `account` 数值替换为占位值（仅影响示例，不影响字段结构）。
