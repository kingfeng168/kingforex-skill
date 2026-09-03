# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] — 2026-09-03

### 新增

- **`scripts/kline_read.py`**（641 行）：K 线盘面解读引擎。
  - 输入：MT4/MT5 导出的 CSV，或 `--text` 直接粘贴 OHLC（分隔符支持逗号 / 分号 / 制表符 / 空格，
    列数自适应，`date,time,o,h,l,c[,v]` 与纯 `o,h,l,c` 均可，可直接粘贴 MT4 剪贴板内容）；
    输出：文本 / `--json` / `--html`（ECharts K 线标注图）。
  - 自动产出趋势背景（ATR 归一化摆动斜率，样本不足时 EMA 兜底并标注降级）、市场结构（HH/HL/LH/LL）、
    EMA20/50 排列、ATR(14)、关键支撑阻力与整数关口、量价背离。
  - 形态识别采用 Greg Morris《蜡烛图精解》量化标准（倒锤子线 / 上吊线 / 锤子线 / 流星线 / 吞没 / 孕线 / 内包线），
    每个形态附带 1 日胜率、净盈亏比 `pnl1`、★评级、确认要求与确认状态（已确认 / 已证伪 / 待确认），
    **已证伪形态自动剔除**。
  - 趋势不明确时不输出反转形态（Morris 核心约束）；震荡市仅输出整理形态并提示待突破。

### 变更

- `references/ta_reading.md`：第 2 节重写为 Morris 量化 K 线框架（三条基本假定、形态评级表、
  识别标准、确认机制、预测时效）；第 8 节「每笔必填」清单由 6 项扩至 9 项，新增「形态 `pnl1` 是否为正」
  与「是否已证伪」两道强制卡点。
- `references/data_sources.md`：新增 7.7 节——K 线数据源可用性实测（新浪 / 东财 / Yahoo / stooq 均不可用）
  与 MT4 导出步骤；7.2 节 EIA 段落同步。
- `SKILL.md`：description 触发词、分析主线第二阶（盘面分析）、脚本清单、调用示例均同步；
  末尾新增「密钥安全」小节。
- `README.md` / `LICENSE`（MIT）/ `.gitignore`：开源文档规范化；`.gitignore` 排除 `.eia_key`、
  `*.key`、`.env`、`*.zip`、`__pycache__`。

### 修复

- `scripts/eia_fetch.py`：文档措辞修正（密钥读取优先级说明统一）。
- `scripts/kline_read.py`：`--text` 粘贴路径原先只认严格的 5 列 `date,o,h,l,c`，
  MT4 剪贴板常见的 6 列 `date,time,o,h,l,c` 会被整行跳过（静默解析出 0 根 K 线）。
  现改为按「第一个数字列之前的所有列合并为时间标签」自适应解析，并新增严格数字正则
  `NUM_RE`（旧 `_is_num` 会把 `2026-08-01` 误判为数字，导致首列日期被当成开盘价）。
  已补 7 项回归：6 列 / 5 列 / 制表符 / 纯 OHLC / 带表头 / CSV / 震荡市不误报。

## [1.0.0] — 2026-09-02

初始发布：九大模块宏观交易体系与纪律框架，含 8 个取数与计算脚本
（`position_size` / `exposure` / `bis_fetch` / `eia_fetch` / `imf_fetch` / `worldbank_fetch` /
`quantgist_fetch` / `live_market_fetch`）、10 份领域参考、5 套输出模板。
