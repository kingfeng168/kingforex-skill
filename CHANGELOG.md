# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [1.4.0] — 2026-09-04

### 新增

- **`scripts/fred_fetch.py`**（FRED 圣路易斯联储宏观/利率 API v1，纯标准库）：模块一「宏观利率地基」核心一手源。拉取 `DGS10`(10Y 名义利率)、`DFII10`(10Y TIPS 实际利率·黄金定价第一锚)、`T10YIE`(10Y 盈亏平衡通胀)、`T10Y2Y`(2s10s 利差·曲线倒挂/衰退信号)、短端 `DGS3MO`/`DGS1`/`DGS2`/`DGS5`、长端 `DGS30`、政策利率 `FEDFUNDS`/`DFF`；7 个 preset（`nominal_10y` / `real_10y` / `breakeven_10y` / `curve_2s10s` / `short_end` / `fed_funds` / `all_rates`）；`--out` 落盘 `.csv`(宽表)/`.json`；缺失值 `.` 自动转空；401=Key 无效 / 400·404=系列不存在 / 429=限速 均优雅降级，**绝不杜撰**。
- **三源密钥本地化（齐备）**：EIA（原油）、Twelve Data（K 线）、FRED（宏观利率）三枚 key 分别存于 `scripts/.eia_key` / `.td_key` / `.fred_key`（本地文件、不进 zip）；读取优先级统一为 `--api-key` > 环境变量 > 本地文件。

### 变更

- `SKILL.md`：密钥安全节增补 FRED；脚本清单新增 `fred_fetch.py`；数据源集成「宏观利率(FRED)」条目。
- `references/data_sources.md`：**新增第 7.10 节 FRED API**（Base / 权威价值 / preset↔系列映射 / 用法 / bash 示例），第 1 节表格 FRED 行补系列与脚本引用。

### 修复

- 无（纯增量）。

## [1.3.0] — 2026-09-03

### 新增

- **`scripts/cftc_fetch.py`**（CFTC COT/TFF 持仓拥挤度，纯标准库）：从 CFTC 官方年度历史文件（`fut_disagg_txt_YYYY.zip` 商品 / `fut_fin_txt_YYYY.zip` 外汇）解析 Managed Money（商品）或 Leveraged Funds（外汇）投机多/空/净头寸；输出**净头寸/OI、多空比 L/S、52 周历史分位（拥挤度等级：极度做多≥90% / 偏拥挤做空≤25% / 中性）、周环比 ΔNet / Δ净头寸-OI**。**免 key、中国可直连 cftc.gov**（2026-09 实测 HTTP 200；Socrata API 在部分网络被拦截，故用官方静态文件兜底）。支持 `--symbol` 别名（GOLD/WTI/EURUSD/JPYUSD/AUDUSD/…）、`--market-code`、`--weeks`、`--json`、`--from-file` 离线解析、`--list`。
- **`scripts/wgc_lbma_fetch.py`**（黄金 LBMA 代理，纯标准库）：经 gold-api.com 取国际现货金/银（美元/盎司，紧贴 LBMA 定盘，免 key）；WGC 黄金供需/央行购金与 LBMA 官方定盘无免费 JSON API，附 `--manual` 标准化 WebFetch 手工取数指引。
- **`scripts/opec_fetch.py`**（OPEC MOMR 原油报告，纯标准库）：尽力直连 OPEC 公开页抽取供需关键词，失败（网络/地域封锁，如开发环境 `opec.org` 返回 403）则输出标准化 WebFetch 手工取数指引（全球需求增长/非 OPEC 供应/OPEC 产量/ORB 一揽子价）；IEA MODS 付费，附 KAPSARC 免费历史替代。
- **`scripts/fedwatch_csv.py`**（CME FedWatch 降息/加息概率，纯标准库）：FedWatch 无免费脚本化 API（需付费订阅 + OAuth），解析用户从 FedWatch Tool 网页手动导出的 CSV，转结构化「各 FOMC 会议 × 降息≥25bp/按兵不动/加息≥25bp 概率」，`--json` 机器可读。

### 变更

- `SKILL.md`：description 增补触发词（持仓拥挤度/CFTC COT/TFF/投机净头寸/OPEC MOMR/WGC 供需/LBMA 定盘）；脚本清单新增 4 个脚本与调用示例；数据源集成「外汇(CFTC 拥挤度)/黄金(WGC/LBMA 代理)/原油(OPEC)/宏观利率(FedWatch 无免费 API 用 CSV 桥接)」条目标注可行性。
- `references/data_sources.md`：第 1/2/3/4 节表格更新 CFTC/FedWatch/WGC/LBMA/OPEC/IEA 获取方式；**新增第 7.8 节**统一说明四类数据脚本化可行性（✅ 免费直连 / ⚠️ best-effort / ⚠️ 无免费 API 手动桥接）与取数铁律；第 7 节开头脚本计数更新为「十余个」。
- `README.md`：目录树新增 4 个脚本（总数 15）；新增「权威取数脚本」专节；密钥配置表补 Twelve Data / FedWatch；更新日志补 v1.3.0。

### 修复

- 无（纯增量）。取数铁律一致：**失败即报错/降级，绝不杜撰数字**。

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
