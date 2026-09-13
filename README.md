# kingforex-skill

**当前版本：v2.4.4** · [更新日志 CHANGELOG.md](CHANGELOG.md) · MIT License

> 版本号即 Git tag 号（如 tag `v2.4.4`）。本仓库自 v2.4.4 起统一版本线，不再维护独立的发布序号。

外汇 / 贵金属 / 大宗商品现货交易者的**宏观交易体系与纪律框架**技能。覆盖「宏观利率地基 → 盘前计划筛选 → 入场执行 → 持仓管理 → 离场 → 复盘 → 心理纪律」全链路，外加外汇 / 黄金 / 原油专项、跨市场联动、市场微观结构、风险组合管理与工具数据源九大模块。

## 核心能力

- **三维印证分析哲学**：宏观定方向（利率 / 央行 / 跨市场） → 跨市场验方向 → 盘面定时机（看大做小）。
- **统一计算引擎**（`scripts/calc_engine.py`）：pip 价值 / 浮盈 / 手数 / 凯利档位 / 相关性矩阵 / 四维评分 / 事件静默 / 回测 / 一致性校验，**全部单一事实来源**，禁止手算与硬编码。
- **量化指标引擎**（`scripts/quant_metrics.py`）：对数收益、年化波动率、Sharpe / Sortino、最大回撤、偏度 / 峰度 / Jarque-Bera、VaR / CVaR、EWMA、已实现波动率、Hurst 指数、滚动 Z-score、半衰期、自相关。
- **多周期共振引擎**（`scripts/mtf_confluence.py`）：W（周线）+ D（日线）+ H1（1 小时）三周期 K 线，自动产出「方向共识矩阵 + 关键位融合共振区 + ATR 跨周期波动结构 + 确定性交易计划（不做模糊表述）」的 9 段深度报告（JSON + 霓虹暗色 HTML）。
- **K 线盘面解读引擎**（`scripts/kline_read.py`）：趋势背景、市场结构、EMA5/10/60 排列、ATR(14)、Morris 量化形态、趋势线、成交密集区（POC/HVN），支持 `--csv` / `--text` / `--fetch`（Twelve Data）与 `--json` / `--html`。
- **持仓分析报告生成器**（`scripts/position_report.py`）：输入持仓与账户，自动串联行情 / K 线 / 量化 / 央行利率 / 经济日历，输出九大节 HTML + MD 报告。
- **决策增强报告生成器**（`scripts/decision_enhanced_report*.py`）：v2.3 冻结模板 → v2.4.x 数据注入，输出 **23 节 / 13 图** HTML + MD + Excel 复盘模板，含评分卡、情景预案、凯利交互计算器、相关性热力图、风险仪表盘、动态止损、信号回测、**数据一致性校验报告（10 项）**。
- **全流程编排器**（`scripts/report_agent_v3.py`）：数据采集 → 校验 → 指标 → 评分 → 决策 → 持仓管理 → 一致性校验 → 报告渲染，八步流水线一键执行。
- **权威数据源脚本**（`scripts/*.py`）：FRED、EIA、BIS、IMF COFER、World Bank、CFTC COT、WGC/LBMA、iTick、goldprice.dev、OilPriceAPI、Jin10、FedWatch 等，全部支持 `--out ./output/xxx.csv`。
- **时间核对与数据鲜度铁律**（v1.2.2 起每次调用第一动作）：先核对当下北京时间，再取最新可用数据，输出带 `[源 | 截至 YYYY-MM-DD HH:MM TZ]` 时间戳，禁止以旧充新。

## 风控与纪律铁律

| 规则 | 阈值 | 常量 |
| --- | --- | --- |
| 单笔风险 | ≤ 1%（小账户优先 0.5%） | `RISK_HARD_CAP` |
| 组合总风险 | ≤ 5% | `PORTFOLIO_CAP` |
| 事件静默 | 事件前 4 小时不开新仓 | `EVENT_SILENCE_H` |
| 议息清仓 | 议息前 24 小时清仓或最小仓 | `FOMC_CLEAR_H` |
| 最小盈亏比 | RR ≥ 1.5 方可交易 | `MIN_RR` |
| 建仓评分门槛 | 四维加权总分 ≥ 75 | `SCORE_BUILD` |
| 回测样本 | < 100 笔禁止给出年化预测 | `BACKTEST_MIN` |
| 凯利公式 | **仅作参考**，实战用半凯利，且以风险预算为准 | — |

> 连续亏损 3 次暂停交易；入场 / 止损 / 目标 / R 倍数一律表格化呈现。

## 目录结构

```
kingforex-skill/
├── SKILL.md                 # 技能主文档（体系、流程、铁律、数据源速查）
├── CHANGELOG.md             # 版本变更日志（Keep a Changelog 格式）
├── LICENSE                  # MIT
├── README.md
├── references/              # 18 份方法论参考（宏观利率 / 外汇 / 黄金 / 原油 / 跨市场 /
│                            #   微观结构 / 资金管理 / 风险心理 / 多周期共振 / 量化金融 /
│                            #   K 线解读 / 指标 / 数据源 / 持仓报告 / v3 规范 …）
├── scripts/                 # 33 个脚本（计算引擎 / 量化指标 / 盘面解读 / 多周期共振 /
│                            #   各数据源抓取 / 仓位与风控 / 报告生成器）
└── assets/                  # 6 份模板（决策增强 HTML 样例 / 持仓报告模板 / 盘前计划 /
                             #   情景 / 交易日志 / 分析→策略）
```

## 安装

将本仓库克隆或解压到 WorkBuddy 技能目录：

```bash
# 方式一：git 克隆
git clone https://github.com/kingfeng168/kingforex-skill.git \
  ~/.workbuddy/skills/kingforex-skill

# 方式二：下载 Release 中的 kingforex-skill.zip，解压到
#   ~/.workbuddy/skills/kingforex-skill/
```

重启 / 刷新 WorkBuddy 后，用 `@skill:kingforex-skill` 或在对话中描述「制定下一交易日交易计划 / 分析美日汇率 / 多周期共振研判黄金 / 已有持仓做深度诊断」等触发。

## 依赖

- Python 3.10+。脚本为标准库 + **一个可选第三方库**：
  - **`openpyxl`**（可选）—— 仅用于生成 Excel 交易复盘模板。
    ```bash
    pip install openpyxl            # 国内建议：-i https://pypi.tuna.tsinghua.edu.cn/simple
    ```
    未安装时**不会报错中断**：报告生成器会自动跳过 XLSX，HTML 与 MD 主产物照常产出，并打印一行提示。
- 联网抓取全部走 `urllib`，无需安装 HTTP 客户端。
- 部分数据源需要免费 API Key（见下文）。

## 密钥配置（用户自备，不进 zip / 不写进源码）

真实第三方 API Key 一律不落盘于可分发产物。脚本采用三级读取优先级，任选其一：

| 数据源 | 环境变量 | 脚本同目录文件 | 免费注册 |
| --- | --- | --- | --- |
| EIA（原油库存） | `EIA_API_KEY` | `scripts/.eia_key` | eia.gov |
| FRED（宏观利率） | `FRED_API_KEY` | `scripts/.fred_key` | fredaccount.stlouisfed.org |
| Twelve Data（K 线） | `TWELVEDATA_API_KEY` | `scripts/.td_key` | twelvedata.com |
| Jin10（实时行情） | `JIN10_TOKEN` | `scripts/.jin10_key` | jin10.com |
| iTick（外汇/贵金属） | `ITICK_API_KEY` | `scripts/.itick_key` | itick.org |
| goldprice.dev | `GOLDPRICE_API_KEY` | `scripts/.goldprice_key` | goldprice.dev |
| OilPriceAPI | `OILPRICEAPI_KEY` | `scripts/.oilprice_key` | oilpriceapi.com |

> 本地便利文件（如 `scripts/.eia_key`）为单行纯文本，**需自行创建**，不进入仓库、不进入 `kingforex-skill.zip`、不写进脚本源码。重装 / 迁移技能后需重新配置。

## 快速示例

```bash
# 单周期盘面解读
python scripts/kline_read.py --csv ./output/EURUSD_H1.csv --symbol EURUSD --tf H1 --last 120 --json --html --out ./output

# 多周期共振（W+D+H1 三 CSV）
python scripts/mtf_confluence.py --csv-w ./output/USDJPY_W.csv \
  --csv-d ./output/USDJPY_D.csv --csv-h1 ./output/USDJPY_H1.csv \
  --symbol USDJPY --html --json --out ./output

# 拉取宏观利率（FRED）
python scripts/fred_fetch.py --preset all_rates --last 30 --out ./output/fred_rates.csv

# 计算引擎自检（校验 pip 价值 / 浮盈 / 手数 / 凯利 / 评分 / 一致性校验）
python scripts/calc_engine.py

# 持仓分析报告
python scripts/position_report.py --symbol AUDJPY --direction SELL --lots 0.02 \
  --entry 114.573 --sl 114.900 --tp 109.781 --account 574 --risk-pct 1.0 --out-dir ./output

# 决策增强报告（需先把 6 个品种日线 CSV 放入 --out 目录，命名见脚本顶部 KD 字典）
python scripts/decision_enhanced_report_v242.py
```

## 免责声明

本技能仅用于**教育与研究**，所有信号、计划、结论均基于客观数值与公开数据，**不构成任何投资建议**。外汇 / 贵金属 / 大宗商品交易杠杆高、风险大，请独立判断、自担风险。

## License

[MIT](./LICENSE) © 2026 FENG.JIN
