# kingforex-skill

**当前版本：v2.9.0** · [更新日志 CHANGELOG.md](CHANGELOG.md) · MIT License

> 版本号即 Git tag 号（如 tag `v2.9.0`）。本仓库自 v2.4.4 起统一版本线，不再维护独立的发布序号。
> **v2.9.0 为「一致性修复版」**：修正风控数值口径（单笔风险 1%／黄金 pip／名义本金）、修复中文 Windows 崩溃与 `--out-dir`、校正失效数据源（IMF/QuantGist/财政部口径）、新增**开仓前组合闸门**与**报告数据鲜度门禁**、Hurst 改用 DFA-1 + 显著性带。**报告格式未变**，冻结基线仍为 **v2.5.6**（23 节 / 15 图 / CDN 0）。

外汇 / 贵金属 / 大宗商品现货交易者的**宏观交易体系与纪律框架**技能。覆盖「宏观利率地基 → 盘前计划筛选 → 入场执行 → 持仓管理 → 离场 → 复盘 → 心理纪律」全链路，外加外汇 / 黄金 / 原油专项、跨市场联动、市场微观结构、风险组合管理与工具数据源九大模块。

## 核心能力

- **三维印证分析哲学**：宏观定方向（利率 / 央行 / 跨市场） → 跨市场验方向 → 盘面定时机（看大做小）。
- **统一计算引擎**（`scripts/calc_engine.py`）：pip 价值 / 浮盈 / 手数 / 凯利档位 / 相关性矩阵 / 四维评分 / 回测 / 一致性校验（事件静默纪律已于 2026-09-21 经用户指令移除），**全部单一事实来源**，禁止手算与硬编码。
- **量化指标引擎**（`scripts/quant_metrics.py`）：对数收益、年化波动率、Sharpe / Sortino、最大回撤、偏度 / 峰度 / Jarque-Bera、VaR / CVaR、EWMA、已实现波动率、Hurst 指数、滚动 Z-score、半衰期、自相关。
- **多周期共振引擎**（`scripts/mtf_confluence.py`）：W（周线）+ D（日线）+ H1（1 小时）三周期 K 线，自动产出「方向共识矩阵 + 关键位融合共振区 + ATR 跨周期波动结构 + 确定性交易计划（不做模糊表述）」的 9 段深度报告（JSON + 霓虹暗色 HTML）。
- **K 线盘面解读引擎**（`scripts/kline_read.py`）：趋势背景、市场结构、EMA5/10/60 排列、ATR(14)、Morris 量化形态、趋势线、成交密集区（POC/HVN），支持 `--csv` / `--text` / `--fetch`（Twelve Data）与 `--json` / `--html`。
- **持仓分析报告生成器**（`scripts/position_report.py`）：输入持仓与账户，自动串联行情 / K 线 / 量化 / 央行利率 / 经济日历，输出九大节 HTML + MD 报告。
- **决策增强报告生成器**（`scripts/decision_enhanced_report*.py`）：**v2.5.0 冻结模板 + 锚点 patch** —— 以用户确认版 HTML 为唯一骨架，**严禁调整格式**，`str.replace()` 三处锚点注入，模板零改写；输出 **23 节 / 15 图** HTML，含评分卡、情景预案、凯利交互计算器、**仓位多角度评估（六角度收敛 + 唯一绿色最终仓位表）**、**止损止盈合理性评估（REASONABLE / CAUTION / UNREASONABLE 三级判定）**、相关性热力图、风险仪表盘、动态止损、信号回测、**数据一致性校验报告（10 项）**。v2.3 冻结模板 → v2.4.x 数据注入路线转为历史归档。
- **止损/止盈合理性评估引擎**（`scripts/sl_tp_evaluate.py`）：pip 距离、**初始 R:R vs 剩余 R:R**、浮盈、单笔美元风险、SL 方向校验、ATR 宽度 sanity，输出三级判定 + 八类缺陷分级（`SL_REVERSED` / `TRAIL_SUGGEST` / `REST_RR_BROKEN` / `REST_RR_LOW` / `BAD_INIT_RR` / `OVER_RISK` / `OVER_1PCT` / `SL_TOO_TIGHT` / `SL_TOO_WIDE`）。重点防范反向移动止损与剩余 R:R 崩塌。
- **权威数据源脚本**（`scripts/*.py`）：FRED、EIA、BIS、IMF COFER、World Bank、CFTC COT、WGC/LBMA、Frankfurter、AllRatesToday、goldprice.dev、OilPriceAPI、Jin10、**华尔街见闻 WSCN**、FedWatch 等，全部支持 `--out ./output/xxx.csv`。
- **双资讯源交叉验证**：金十 Jin10（实时快闪 / 报价 / 财经日历，高频速报）+ 华尔街见闻 WSCN（全球资讯深度摘要 / 事件因果归因 / A 股异动逻辑，中低频解读）。`scripts/wscn_fetch.py relevant` 按六类交易关键关键词自动打分排序，快速定位事件驱动线索。
- **时间核对与数据鲜度铁律**（v1.2.2 起每次调用第一动作）：先核对当下北京时间，再取最新可用数据，输出带 `[源 | 截至 YYYY-MM-DD HH:MM TZ]` 时间戳，禁止以旧充新。

## 风控与纪律铁律

| 规则 | 阈值 | 常量 |
| --- | --- | --- |
| 单笔风险 | ≤ 1%（小账户优先 0.5%） | `RISK_HARD_CAP` |
| 组合总风险 | ≤ 5% | `PORTFOLIO_CAP` |
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
├── references/              # 19 份方法论参考(含 trigger_guide.md 触发词总表)（宏观利率 / 外汇 / 黄金 / 原油 / 跨市场 /
│                            #   微观结构 / 资金管理 / 风险心理 / 多周期共振 / 量化金融 /
│                            #   K 线解读 / 指标 / 数据源 / 持仓报告 / v3 规范 …）
├── scripts/                 # 36 个活跃脚本(另 4 个旧工具归档于 _archive/)（计算引擎 / 量化指标 / 盘面解读 / 多周期共振 /
│                            #   各数据源抓取 / 仓位与风控 / 止损止盈评估 / 报告生成器）
└── assets/                  # 11 个文件(模板 + echarts.min.js)（决策增强冻结模板 / 决策增强样例 / 持仓报告模板 /
                             #   盘前计划 / 情景 / 交易日志 / 分析→策略）
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
| AllRatesToday（实时中间价） | `ART_KEY` | `scripts/.art_key` | allratestoday.com |
| goldprice.dev | `GOLDPRICE_API_KEY` | `scripts/.goldprice_key` | goldprice.dev |
| OilPriceAPI | `OILPRICEAPI_KEY` | `scripts/.oilprice_key` | oilpriceapi.com |
| Jev（Typesafe 判断工具） | `JEV_API_KEY`(=TYPESAFE_API_KEY) | `scripts/.jev_key` | api.typesafe.ai |
| 华尔街见闻 WSCN（第二资讯源） | `WSCN_API_KEY` | `scripts/.wscn_key` | — |
| QuantGist（事件/情报，**当前服务端 502 不可用**） | `QUANTGIST_API_KEY` | `scripts/.quantgist_key` | quantgist.com |
| qveris MCP（金融数据市场，按调用计费） | `QVERIS_API_KEY` | `scripts/.qveris_key` | — |

> 本地便利文件（如 `scripts/.eia_key`）为单行纯文本，**需自行创建**，不进入仓库、不进入 `kingforex-skill.zip`、不写进脚本源码。重装 / 迁移技能后需重新配置。

> **凭据读取范围披露（2026-09-28 补充）**：`scripts/qveris_fetch.py` 在本技能自有的
> `--api-key` / `QVERIS_API_KEY` / `scripts/.qveris_key` 之外，还会回退读取 WorkBuddy MCP 客户端的
> 用户级配置 `~/.workbuddy/mcp.json`，并从中取出 `mcpServers.qveris.headers.Authorization` 的
> Bearer token。该读取**仅限 qveris 条目、仅用于 qveris 请求、不外传**；如不希望脚本读到该文件，
> 请改用 `scripts/.qveris_key` 并把 `mcp.json` 中的对应条目移出脚本可读范围。

## v2.9.0 快速开始（安装后三条命令即可验证可用）

```bash
# 1) 计算引擎自检（风控常量 / pip 口径 / 凯利 / 评分）
python scripts/calc_engine.py

# 2) 盘面解读（纯本地, 不需要任何 key）
python scripts/kline_read.py --csv ./output/EURUSD_D1.csv --symbol EURUSD --tf D1 --last 200 --html --out ./output

# 3) 量化体检（Hurst 用 DFA-1 + 自助法随机游走带判定）
python scripts/quant_metrics.py --csv ./output/EURUSD_D1.csv --date-col datetime --price-col close --json
```

**下单前必过闸门**（v2.9.0 新增，通过 exit 0 / 否决 exit 3）：

```bash
python scripts/exposure.py --equity 574 \
  --positions "AUDJPY:short:0.02:2.85" \
  --check-new "XAUUSD:long:0.01:1.5"
```

## v2.9.0 主要变更（完整见 CHANGELOG）

| 类别 | 变更 |
| --- | --- |
| 风控口径 | 单笔风险统一 **1%**（文档与代码同源 `calc_engine.RISK_HARD_CAP`）；黄金/白银 pip 与每 pip 美元价值统一走 `calc_engine.CONTRACTS`（此前黄金风险被放大 **1000 倍**） |
| 组合风险 | `exposure.py` 名义本金改为 **实时价 × 合约单位**（此前硬编码，黄金低估 2.1 倍）；新增 **`--check-new` 开仓前闸门** |
| 脚本清理 | 6 个依赖已删文件/写死路径的历史脚本已处理: `parity_check.py` 改为命令行传参可正常使用, 其余 4 个归档至 `scripts/_archive/legacy_dev_tools/`(不再随包分发) |
| 可运行性 | 修复中文 Windows(cp936) 崩溃（旗舰入口/`kline_read`/`sl_tp_evaluate`/`exposure`）；修复 `position_report.py --out-dir` 崩溃与路径被忽略；活跃脚本 cp936 崩溃项 **0** |
| 数据鲜度 | 旗舰生成器新增 **数据鲜度门禁**：数据基准日取自日K末根，溯源行日期不一致即**拒绝写出**（消除"页头今天、正文旧日期"）；删除机器私有兜底路径；缺 `scripts/.td_key` 时**拒绝回退硬编码旧价** |
| 数据源 | IMF 端点按实测校正并**显式报"0 观测不可供数"**；QuantGist 加 **502 预检**；财政部 `ust_yield` 口径更正（原为记账汇率）；Frankfurter 域名统一；清除指向已删脚本 `itick_fetch.py` 的失效文档 |
| 量化 | Hurst 改用 **DFA-1**（实测随机游走均值 0.505；旧 R/S 为 0.984）+ **自助法随机游走带**判显著；`--json` 不再把 list/str 吞成 null 并转纯 ASCII |
| 隐私 | `.gitignore` 覆盖个人财务数据产物；README 披露 qveris 读取 `~/.workbuddy/mcp.json` 的行为；ECharts CDN 回退版本统一 5.5.1 |

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

# 决策增强报告（v2.5.6 冻结模板 · 数据层替换，严禁调整格式）
# 前置: 设 KINGFOREX_DATA=<已存在目录> 且其 kline/ 下有 7 个日线 CSV
python scripts/gen_decision_enhanced_v256.py

# 止损/止盈合理性评估
python scripts/sl_tp_evaluate.py --direction SELL --entry 114.573 --sl 113.284 \
  --tp 109.781 --symbol AUDJPY --equity 574 --lot 0.02
```

## 免责声明

本技能仅用于**教育与研究**，所有信号、计划、结论均基于客观数值与公开数据，**不构成任何投资建议**。外汇 / 贵金属 / 大宗商品交易杠杆高、风险大，请独立判断、自担风险。

## License

[MIT](./LICENSE) © 2026 FENG.JIN
