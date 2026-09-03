# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [1.2.0] — 2026-09-03

### 新增

- **`scripts/kline_fetch.py`**（157 行，纯标准库）：从 **Twelve Data** 权威抓取 K 线历史（中国大陆可直连、免翻墙），覆盖外汇/黄金/原油与 `15min / 1h / 4h / 1day / 1week` 五周期。
- **`scripts/kline_read.py --fetch` 模式**：用户未发送 K 线时自动联网抓取五周期并逐周期分析；API Key 缺失 / 网络受限 / 品种不支持仅报告原因并跳过，全部失败明确提示「无法获取权威 K 线数据」并引导改用本地 CSV/文本，**严禁编造价格**。
- `references/ta_reading.md`：补充 Murphy《金融市场技术分析》三个缺口——§2.8 跳空与窗口（普通/突破/中继/衰竭 + 4 条通用规则）；`scripts/kline_read.py` 新增 `detect_gap()` 识别最近跳空方向/幅度/是否回补。
- `references/indicators.md`：§9 ADX/DMI（趋势强度四档读法 + 纪律）、§10 补充指标（OBV/CCI/Parabolic SAR）。
- `references/channels.md`：§5 扇形线（1/3·2/3·3/3 回撤射线）、§6 回撤比例与斐波（33/50/66% + 0.382/0.5/0.618）。

### 变更

- **输出规范收敛为双分支**：存在高确定性机会（宏观/跨市场/盘面三维印证共振 + 风险可控）才出交易计划（精确 9 行表格）；否则直接判定 **【今日无交易】**，不强行每次给交易结论。
- **移除数据看板要求**：本技能聚焦分析与交易策略制定，跨市场信号直接汇入交易计划与盘面研判；删除 `assets/macro_dashboard_template.md`，相关文档措辞同步清理。
- `SKILL.md`：description 增补触发词（跳空/窗口、ADX、扇形线、斐波回撤、头肩/双顶底/三角/旗形/楔形）；脚本清单、调用示例、数据源集成「K 线历史」条、密钥安全（Twelve Data key 不入 zip）同步更新。
- `references/data_sources.md` §7.7：由「免费 K 线基本不可用」改写为「双路径 + 取数铁律」（MT4 CSV 主输入 + Twelve Data 权威联网抓取），附降级提示。

### 修复

- 无（相对 1.1.0 的功能增量，上一版 `--text` 6 列解析问题已在 1.1.0 修复）。

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
