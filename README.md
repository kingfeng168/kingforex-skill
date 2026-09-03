# kingforex-skill

> 手工外汇 / 贵金属 / 大宗商品现货交易者的**宏观交易体系与纪律框架** —— 把交易体系固化为「盘前计划 → 盘中执行 → 盘后复盘」的可执行工作流、可检索领域知识、可直接套用模板与确定性计算脚本。

它是一个给 AI Agent（如 WorkBuddy / Claude Code）加载的 **Skill**，不是交易信号生成器，**不产生任何自动下单逻辑**。它只输出：交易计划、检查清单、确定性计算与复盘结论。

---

## 为什么需要它

主观交易最大的敌人不是看错方向，而是**没有根据地开仓、凭感觉设止损、亏损后摊平、连续亏损后加码**。本技能把这些失效模式写进硬规则：

- **三维印证才出手**：宏观定方向 → 跨市场验方向 → 盘面定时机。任一维度反向即降级或放弃。
- **纪律优先级 Top 10**：提前写计划、先设止损再入场、按 ATR 定止损、单笔风险 0.5%–1%、相关性风控、事件前减仓、每天写日志、每周归因、**连续亏损 3 次强制暂停**。
- **数据必须溯源**：每条结论标注 `[源 | 截至]`，禁用未注明来源的社媒/自媒体作为方向依据。
- **不猜点位，只算数字**：止损距离、手数、净暴露、压力测试全部由脚本计算。

---

## 九大模块

| 模块 | 内容 | 文件 |
|---|---|---|
| 一 | 宏观利率地基（名义/实际利率、通胀预期、央行周期、收益率曲线、Regime） | `references/macro_rates.md` |
| 二 | 外汇专项（套息、避险、商品货币、美元微笑、CFTC 持仓） | `references/fx.md` |
| 三 | 黄金专项（TIPS 锚、金银比、央行购金） | `references/gold.md` |
| 四 | 原油专项（EIA、OPEC、期限结构） | `references/oil.md` |
| 五 | 跨市场联动（TIPS/DXY 验黄金、铜/AUD-JPY 验澳元） | `references/cross_market.md` |
| 六 | 市场微观结构（流动性、时段、点差、滑点） | `references/microstructure.md` |
| 七 | 风险与组合管理（仓位、净暴露、压力测试） | `references/risk_psychology.md` |
| 八 | 心理纪律与复盘 | `references/risk_psychology.md` |
| 九 | 盘面分析（Morris 量化 K 线、趋势/区间、关键位、ATR、量价） | `references/ta_reading.md` |

外加：`references/analysis_framework.md`（三维印证决策矩阵）、`references/data_sources.md`（信息溯源总纲）。

---

## 目录结构

```
kingforex-skill/
├── SKILL.md                 # 技能入口：定位、工作流、原则、脚本清单
├── references/              # 领域知识（按需加载，不要一次全读）
│   ├── analysis_framework.md
│   ├── cross_market.md
│   ├── data_sources.md
│   ├── fx.md
│   ├── gold.md
│   ├── macro_rates.md
│   ├── microstructure.md
│   ├── oil.md
│   ├── risk_psychology.md
│   └── ta_reading.md
├── assets/                  # 输出模板（直接套用）
│   ├── analysis_to_strategy_template.md
│   ├── macro_dashboard_template.md
│   ├── scenario_plan_template.md
│   ├── trade_journal_template.md
│   └── trade_plan_template.md
└── scripts/                 # 9 个确定性脚本（纯 Python 标准库，零第三方依赖）
    ├── position_size.py     # ATR 止损 → 手数
    ├── exposure.py          # 组合净暴露 + 相关性集中度 + 压力测试
    ├── kline_read.py        # K 线盘面解读引擎（MT4 CSV / 粘贴文本 → 文本/JSON/HTML）
    ├── bis_fetch.py         # BIS SDMX v2：央行政策利率、有效汇率（免 key）
    ├── eia_fetch.py         # EIA v2：原油/汽油/馏分油库存、WTI/Brent（需 key）
    ├── imf_fetch.py         # IMF SDMX 3.0：COFER 美元储备份额、IFS、WEO（免 key）
    ├── worldbank_fetch.py   # World Bank：实际利率、CPI、经常账户、外储（免 key）
    ├── quantgist_fetch.py   # QuantGist：事件日历、新闻雷达、商品 ETF（需 key）
    └── live_market_fetch.py # 实时行情聚合：5 个免 key 源（外汇/黄金/美债）
```

---

## 安装

### 方式一：Skill 形式（推荐）

```bash
# 下载 Release 的 kingforex-skill.zip，解压后：
cp -r kingforex-skill ~/.workbuddy/skills/     # WorkBuddy
# 或
cp -r kingforex-skill ~/.claude/skills/        # Claude Code
```

### 方式二：直接 clone

```bash
git clone https://github.com/<owner>/kingforex-skill.git
```

之后在对话中提到「交易计划」「ATR 止损」「EIA 库存」「K 线形态」等关键词，Agent 会自动加载本技能。

---

## 依赖

- **Python 3.8+**（脚本仅用标准库：`urllib`、`argparse`、`json`、`csv`、`math`、`statistics`，无需 `pip install`）
- 无需 pandas / numpy / requests

---

## 快速上手

```bash
# 1) 用 ATR 算手数：账户 10 万，单笔风险 1%，止损 35 点
python scripts/position_size.py --equity 100000 --risk 1 --stop 35 --multiplier 10

# 2) 组合暴露体检：是否形成了「单一美元空头」
python scripts/exposure.py --positions "XAUUSD:long:0.5" "AUDUSD:long:1.0" --equity 100000

# 3) 盘面解读：把 MT4 的 EURUSD H1 导出为 CSV，直接得到结构化结论
python scripts/kline_read.py --csv ./output/EURUSD_H1.csv \
    --symbol EURUSD --tf H1 --last 120 --json --html --out ./output

# 4) 免 key 宏观取数
python scripts/bis_fetch.py        --preset policy_rates --last 24 --out ./output/bis_policy.csv
python scripts/worldbank_fetch.py  --preset real_rate --country "US;CN;JP;EU" --mrnev 5 --out ./output/wb.csv
python scripts/live_market_fetch.py --preset gold --out ./output/gold.csv
```

---

## K 线盘面解读（`scripts/kline_read.py`）

这是本技能最有特点的一环：**K 线形态不是看图说话，而是有统计依据的**。

形态识别标准与评级来自 Greg Morris《蜡烛图精解》的大样本统计（7,275 只股票 / 1,460 万个交易日），核心结论被写进了引擎：

| 结论 | 含义 |
|---|---|
| **顶部形态可靠，底部形态不可靠** | 上吊线净盈亏比 **+1.32**（★4）；锤子线 **−0.57**（★1）。顶部信号比底部信号可信得多。 |
| **多数形态胜率只有 41%–50%** | 反转形态靠**赔率**而非胜率盈利，所以必须等确认信号，不能见形态就进。 |
| **必须先定趋势，再认形态** | 同一根长下影 K 线：上升趋势中叫**上吊线（看跌）**，下降趋势中叫**锤子线（看涨）**。趋势不明时引擎**不输出反转形态**。 |

输出包含：趋势背景（ATR 归一化摆动斜率，样本不足自动 EMA 兜底并标注降级）、市场结构（HH/HL/LH/LL）、EMA20/50 排列、ATR(14)、支撑阻力与整数关口、形态列表（每个附 1 日胜率 / 净盈亏比 / ★评级 / 确认要求 / 确认状态），并**自动剔除已证伪形态**。

支持 `--text` 直接粘贴 OHLC，无需文件：

```bash
python scripts/kline_read.py --text "2026-08-20,1.0850,1.0890,1.0830,1.0880
2026-08-21,1.0880,1.0920,1.0860,1.0915" --symbol EURUSD --tf D1
```

### 为什么用 MT4 导出 CSV 而不是实时接口

实测结论：**公开的免费 K 线接口基本不可用**（新浪旧接口下线、东财 push2his 被墙、Yahoo 403、stooq 返回 JS 挑战页）。因此引擎以 **MT4/MT5 导出的 CSV 为主输入**，零网络依赖、数据与你实盘完全一致。详见 `references/data_sources.md` 第 7.7 节。

---

## 密钥配置

脚本**不硬编码任何密钥**，也不在源码里存 key。读取优先级统一为：`--api-key` 参数 > 环境变量 > 本地文件。

| 数据源 | 是否必需 | 配置方式 |
|---|---|---|
| BIS / IMF / World Bank / 实时行情 | 免 key | 无需配置 |
| EIA（原油库存） | 需 key | 免费申请 https://www.eia.gov/opendata/register.php<br>任选其一：<br>`export EIA_API_KEY=your_key`<br>或 `echo your_key > scripts/.eia_key`<br>或 `--api-key your_key` |
| QuantGist（事件/新闻雷达） | 需 key | `export QUANTGIST_API_KEY=your_key` 或 `--api-key your_key` |

`scripts/.eia_key` 与 `__pycache__/` 已在 `.gitignore` 中排除，**不会被提交**。

---

## 免责声明

本技能仅供学习与研究使用，**不构成任何投资建议**。它不包含、也不会生成自动交易代码或代客下单逻辑。所有输出（交易计划、形态评级、仓位建议）均为决策辅助，最终交易决策与后果由使用者自行承担。

金融市场高风险，杠杆产品可能导致本金全部损失。请务必：先用模拟盘验证，再考虑实盘；单笔风险控制在可承受范围内；连续亏损时按纪律强制暂停。

---

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)。

- **v1.1.0**（2026-09-03）：新增 `scripts/kline_read.py` K 线盘面解读引擎（Morris 量化形态评级）；
  `references/ta_reading.md` 重写为统计框架；新增 MT4 导出指引。
- **v1.0.0**（2026-09-02）：初始发布，九大模块 + 8 个取数与计算脚本。

## License

[MIT](LICENSE) © 2026 kingfeng168
