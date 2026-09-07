# kingforex-skill

外汇 / 贵金属 / 大宗商品现货交易者的**宏观交易体系与纪律框架**技能。覆盖「宏观利率地基 → 盘前计划筛选 → 入场执行 → 持仓管理 → 离场 → 复盘 → 心理纪律」全链路，外加外汇 / 黄金 / 原油专项、跨市场联动、市场微观结构、风险组合管理与工具数据源九大模块。

## 核心能力

- **三维印证分析哲学**：宏观定方向（利率 / 央行 / 跨市场） → 跨市场验方向 → 盘面定时机（看大做小）。
- **多周期共振引擎**（`scripts/mtf_confluence.py`）：W（周线）+ D（日线）+ H1（1 小时）三周期 K 线，自动产出「方向共识矩阵 + 关键位融合共振区 + ATR 跨周期波动结构 + 确定性交易计划（不做模糊表述）」的 9 段深度报告（JSON + 霓虹暗色 HTML）。
- **K 线盘面解读引擎**（`scripts/kline_read.py`）：趋势背景、市场结构、EMA5/10/60 排列、ATR(14)、Morris 量化形态、趋势线、成交密集区（POC/HVN），支持 `--csv` / `--text` / `--fetch`（Twelve Data）与 `--json` / `--html`。
- **权威数据源脚本**（`scripts/*.py`）：FRED、EIA、BIS、IMF COFER、World Bank、CFTC COT、WGC/LBMA、iTick、goldprice.dev、OilPriceAPI、Jin10、FedWatch 等，全部支持 `--out ./output/xxx.csv`。
- **时间核对与数据鲜度铁律**（v1.2.2 起每次调用第一动作）：先核对当下北京时间，再取最新可用数据，输出带 `[源 | 截至 YYYY-MM-DD HH:MM TZ]` 时间戳，禁止以旧充新。
- **严格风控**：单笔 0.5%–1%，总风险 ≤ 3%–5%，连续亏损 3 次暂停；入场 / 止损 / 目标 / R 倍数表格化呈现。

## 目录结构

```
kingforex-skill/
├── SKILL.md                 # 技能主文档（体系、流程、铁律、数据源速查）
├── CHANGELOG.md             # 版本变更日志（Keep a Changelog 格式）
├── LICENSE                  # MIT
├── README.md
├── references/              # 15 份方法论参考（宏观利率 / 外汇 / 黄金 / 原油 / 跨市场 / 微观结构 / 资金管理 / 风险心理 / 多周期共振 …）
├── scripts/                 # 21 个可执行脚本（盘面解读 / 多周期共振 / 各数据源抓取 / 仓位计算）
└── assets/                  # 4 份模板（盘前计划 / 情景 / 交易日志 / 分析→策略）
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

重启 / 刷新 WorkBuddy 后，用 `@skill:kingforex-skill` 或在对话中描述「制定下一交易日交易计划 / 分析美日汇率 / 多周期共振研判黄金」等触发。

## 依赖

- Python 3.10+（脚本为标准库 + 少量常见第三方库；联网抓取走 `urllib`，无需安装客户端）。
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

> 本地便利文件（如 `scripts/.eia_key`）为单行纯文本，仅本机存在、不进入 `kingforex-skill.zip`、不写进脚本源码。重装 / 迁移技能后需重新配置。

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
```

## 免责声明

本技能仅用于**教育与研究**，所有信号、计划、结论均基于客观数值与公开数据，**不构成任何投资建议**。外汇 / 贵金属 / 大宗商品交易杠杆高、风险大，请独立判断、自担风险。

## License

[MIT](./LICENSE) © 2026 FENG.JIN
