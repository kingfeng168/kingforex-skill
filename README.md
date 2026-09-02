# kingforex-skill

手工外汇 / 贵金属 / 大宗商品现货交易者的**宏观交易体系与纪律框架**。面向纯手动交易者，禁止任何自动下单逻辑，只输出计划、检查清单、计算与复盘。

本技能把一套完整的九大模块交易体系，转化为「可执行的每日工作流 + 可检索的领域知识 + 可直接套用的模板 + 确定性计算脚本」——它是「盘前—盘中—盘后」的完整操作手册，而非理论讲义。

## 核心定位

一条**可溯源、可降级、可执行**的决策链：

```
权威取数(第0阶) → 宏观研判(第一阶) → 盘面分析(第二阶) → 交易策略(第三阶)
```

任一环节 Gate 不通过，就降级或放弃，不得硬做。核心分析哲学是**三维印证**：宏观定方向、跨市场验方向、盘面定时机，三者共振才出手，任一维度反向即降级。

## 覆盖的九大模块

1. 宏观利率地基（名义/实际利率、盈亏平衡通胀、四大央行周期、Regime 判定）
2. 盘前计划筛选（方向过滤、结构识别、关键位、情景预案）
3. 入场执行（触发条件、ATR 止损、仓位计算）
4. 持仓管理（分批止盈、移动止损、事件降险）
5. 离场策略（目标/失效条件、纪律离场）
6. 交易记录复盘（执行评分、情绪记录、周月归因）
7. 心理纪律（连续亏损暂停、不摊平等 Top 10 原则）
8. 外汇 / 黄金 / 原油专项（套息/避险/商品货币、TIPS 锚/金银比、EIA/OPEC/期限结构）
9. 跨市场联动、市场微观结构、风险组合管理、工具数据源

## 目录结构

```
kingforex-skill/
├── SKILL.md                          # 主入口：工作流 + 触发说明
├── references/                       # 按需加载的领域知识
│   ├── macro_rates.md                #   宏观利率地基
│   ├── analysis_framework.md         #   分析框架与决策矩阵
│   ├── cross_market.md               #   跨市场联动
│   ├── fx.md / gold.md / oil.md      #   外汇 / 黄金 / 原油专项
│   ├── microstructure.md             #   市场微观结构
│   ├── ta_reading.md                 #   盘面技术分析
│   ├── risk_psychology.md            #   风险与心理纪律
│   └── data_sources.md               #   权威数据源清单
├── assets/                           # 输出模板
│   ├── trade_plan_template.md        #   交易计划模板
│   ├── macro_dashboard_template.md   #   宏观仪表盘九宫格
│   ├── analysis_to_strategy_template.md
│   ├── scenario_plan_template.md     #   情景预案模板
│   └── trade_journal_template.md     #   交易日志模板
└── scripts/                          # 确定性计算 / 取数脚本（零第三方依赖）
    ├── position_size.py              #   仓位计算（ATR 止损）
    ├── exposure.py                   #   风险暴露 / 相关性体检
    ├── bis_fetch.py                  #   BIS SDMX v2 数据
    ├── eia_fetch.py                  #   EIA v2 原油库存 / 现货价
    ├── imf_fetch.py                  #   IMF SDMX 3.0（COFER 等）
    ├── worldbank_fetch.py            #   World Bank Open Data
    ├── quantgist_fetch.py            #   QuantGist 日历 / 新闻雷达 / 商品快照
    └── live_market_fetch.py          #   实时行情（Frankfurter / gold-api / 新浪等）
```

## 安装

本技能面向 WorkBuddy。安装方式：

1. 将 `kingforex-skill` 目录复制（或克隆本仓库）到用户技能目录：
   - Windows：`C:\Users\<用户名>\.workbuddy\skills\`
   - macOS / Linux：`~/.workbuddy/skills/`
2. 或直接下载 Release 中的 `kingforex-skill.zip` 解压到上述目录。
3. 重启或刷新 WorkBuddy，技能即可被自动识别与触发。

## 脚本依赖

所有 `scripts/` 脚本**仅使用 Python 标准库**（`urllib`、`json`、`argparse`、`csv` 等），无需 `pip install` 任何第三方包。要求 Python 3.8+。

## 密钥配置

真实第三方 API 密钥一律不落盘于本仓库，避免泄露。

- **EIA API key**：从 <https://www.eia.gov/opendata/> 免费注册。读取优先级：
  `--api-key` 参数 > 环境变量 `EIA_API_KEY` > `scripts/.eia_key`（脚本同目录单行纯文本，本地自建，已加入 `.gitignore`）。
- **QuantGist API key**：通过环境变量 `QUANTGIST_API_KEY` 或 `--api-key` 传入，格式 `qg_live_xxx`。

示例：

```bash
# EIA 原油库存
python scripts/eia_fetch.py --preset crude_stocks --last 12 --api-key YOUR_EIA_KEY

# QuantGist 财经日历
QUANTGIST_API_KEY=qg_live_xxx python scripts/quantgist_fetch.py --preset calendar
```

## 权威数据源

所有输入均要求来自权威渠道：FRED、CME FedWatch、CFTC COT、BIS、EIA、IMF、World Bank、OPEC、WGC、各国央行官网、QuantGist，以及实时行情源（Frankfurter / gold-api / US Treasury / exchangerate-api / 新浪）。完整清单与用法见 `references/data_sources.md`。

## 免责声明

本技能为**教育与研究工具**，输出内容不构成任何投资建议。外汇、贵金属与大宗商品交易具有高风险，可能造成本金全部损失。使用者须独立判断并自担全部风险。

## License

[MIT](./LICENSE)
