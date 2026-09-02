---
name: kingforex-skill
agent_created: true
description: "手工外汇/贵金属/大宗商品现货交易者的宏观交易体系与纪律框架,覆盖宏观利率地基、盘前计划筛选、入场执行、持仓管理、离场策略、交易记录复盘、心理纪律全链路,以及外汇/黄金/原油专项、跨市场联动、市场微观结构、风险组合管理、工具数据源九大模块。当用户要求制定下一交易日交易计划、筛选高确定性机会、分析美债/实际利率/盈亏平衡通胀/点阵图/FedWatch/央行周期、做外汇(套息/避险/商品货币/美元微笑)或黄金(TIPS锚/金银比/央行购金)或原油(EIA/OPEC/期限结构)的宏观分析、搭建或更新跨市场宏观仪表盘、按ATR计算止损与风险仓位、做相关性或净暴露压力测试、处理非农/FOMC/CPI/EIA事件交易、写交易日志或周月复盘,以及提及交易计划/头寸管理/止损止盈/仓位计算/复盘/不摊平/连续亏损暂停等纪律关键词,或要求从权威数据源(FRED/FedWatch/CFTC/BIS/EIA/IMF/World Bank/QuantGist/WGC等)获取信息、用 BIS SDMX v2 或 EIA v2 或 IMF SDMX 3.0 或 World Bank Open Data 或 QuantGist 或实时行情 API(Frankfurter/gold-api/US Treasury/exchangerate-api/新浪)拉取宏观/外汇/原油/事件情报/实时报价数据、把宏观分析落地为可执行交易策略、做宏观到实盘到策略的链路分析、从宏观/跨市场/盘面多维度印证分析、进行盘面分析时,加载本技能。"
---

# 手工交易体系(宏观 · 外汇 · 贵金属 · 商品)

## 定位

本技能把用户给定的九大模块交易体系,转化为**可执行的每日工作流 + 可检索的领域知识 + 可直接套用的模板 + 确定性计算脚本**。它不是理论讲义,而是"盘前—盘中—盘后"的完整操作手册。面向**纯手工**外汇/贵金属/大宗商品现货交易者,禁止任何自动下单逻辑,只输出计划、检查清单、计算与复盘。

## 分析主线:权威取数 → 宏观研判 → 实盘结构 → 交易策略

本技能的输出不是"观点",而是一条**可溯源、可降级、可执行**的决策链。任一环节 Gate 不通过,就降级或放弃,不得硬做:

1. **权威取数(第 0 阶)**:所有输入必须来自 `references/data_sources.md` 列出的权威渠道(FRED、FedWatch、CFTC、BIS、EIA、IMF、World Bank、QuantGist、实时行情源 Frankfurter/gold-api/US Treasury/exchangerate-api/新浪、IEA、OPEC、WGC、央行官网、用户"全球金融日报"JSON)。每条结论标注 `[源 | 截至]`;禁用未注明来源的社媒/自媒体作为方向依据。
2. **宏观研判(第一阶)**:回答利率地基三问、判定四大央行周期与宏观 Regime、定美元强弱与 risk-on/off。这是所有品种的方向地基。
3. **盘面分析(第二阶)**:在宏观定向下,用 K 线与技术结构(趋势/区间/震荡、关键位、K线形态、ATR、量价)确认"现在能不能做、怎么做"。宏观对、盘面不对,仍不入场。
4. **交易策略(第三阶)**:把上述两层收敛为含品种/方向/触发/入场区/止损(ATR)/目标/仓位/失效条件的可执行计划,并用 `scripts/exposure.py` 做风险体检。

完整推导模板见 `assets/analysis_to_strategy_template.md`(含每阶 Gate 与降级规则)。

## 分析思路:三维印证(多维度互相印证才出手)

本技能拒绝"单一信号开仓",核心分析哲学是**三维印证**:**宏观定方向、跨市场验方向、盘面定时机**,三者层层收敛、互相印证——共振才高确定性出手,任一维度反向即降级或放弃。

- **宏观(地基)**:回答美元/利率/Regime/risk-on-off,定大方向(见 `references/macro_rates.md`)。
- **跨市场(验证)**:用 ≥2 个相关市场(如 TIPS/DXY 验黄金、铜/AUD-JPY 验澳元)确认方向是否共振,背离即警告(见 `references/cross_market.md`)。
- **盘面(时机)**:在结构合理处用 K 线/关键位/量价/ATR 找触发,且必须顺前两步方向(见 `references/ta_reading.md`)。

> 印证原则:**宏观错→全盘错;跨市场背离→不入场;盘面结构逆→不入场**。矛盾单宁可错过也不做。完整框架与决策矩阵见 `references/analysis_framework.md`。

当用户触发本技能时,先判断意图落入哪一段工作流,再按需加载 `references/` 与 `assets/`,必要时调用 `scripts/` 做确定性计算。不要把所有参考一次性灌入上下文——按当前步骤只加载相关文件。

## 核心原则(Top 10,优先掌握)

每次调用都先默念这十条,按顺序它们是纪律优先级:

1. **提前写交易计划:没有计划不开单。**
2. **先设止损再入场:永远控制单笔风险。**
3. **按 ATR 设置止损:让市场波动决定止损距离,而非固定 20 点。**
4. **分批止盈 + 移动止损:保护利润,不坐过山车。**
5. **单笔风险 0.5%–1%:活下来才有机会。**
6. **相关性风险控制:避免同一宏观暴露(如同时多黄金+多澳元+多原油=单一美元空头)。**
7. **重大事件前空仓或减仓:不赌数据。**
8. **每天写交易日志:执行评分 + 情绪记录。**
9. **每周绩效归因:知道钱怎么赚、怎么亏。**
10. **连续亏损 3 次暂停交易:强制冷静期。**

## 每日交易工作流

### 步骤 0 — 盘前准备(前一日晚间 / 当日亚盘前)

目标:产出**次日交易计划**,绝不在盘中临时决定方向。

**0.0 权威实证取数(第一动作)**:先用 `references/data_sources.md` 从权威渠道拉取当日数据——FRED 取 US10Y/10Y TIPS/盈亏平衡、CME FedWatch 取概率、CFTC 取持仓、EIA/OPEC 取原油供需、WGC 取黄金供需,或直接复用用户"全球金融日报"JSON。所有数值标注 `[源 | 截至]`,未溯源的数据不得进入后续研判。

1. 调用 `references/macro_rates.md`,先回答三个地基问题:
   - 名义利率、实际利率、通胀预期三者关系(一句话:实际利率=名义利率−通胀预期)。
   - 当前 US10Y、10Y TIPS、盈亏平衡通胀率所处的位置与方向。
   - 美联储 / 欧央行 / 日央行 / 英央行各自处在哪个货币政策周期(收紧 / 中性 / 宽松)。
2. 建立或更新**主要央行政策对比表**(目标、工具、资产负债表、前瞻指引)与**收益率曲线状态**(陡峭化 / 平坦化 / 倒挂及其对外汇商品的含义)。
3. 判断当前**宏观 regime**(四选一):增长强+通胀升 / 增长弱+通胀仍高 / 衰退预期+通胀回落 / 流动性危机避险。
4. 用 `assets/macro_dashboard_template.md` 更新跨市场仪表盘九宫格:
   DXY、US10Y、10Y TIPS、盈亏平衡通胀、黄金、WTI、Brent、铜、标普500、VIX、信用利差、AUD/JPY、USD/CAD、USD/CNH。
5. 判断今天是 **risk-on 还是 risk-off**,并标记当日**经济日历**高风险事件(非农、CPI、FOMC、PMI、EIA)。

### 步骤 1 — 计划与筛选

产出一份**交易计划**,每份至少包含 8 字段:品种、方向、触发条件、入场区域、止损、目标、仓位、失效条件。

1. 用宏观背景**过滤方向**:美元偏强时,避免逆势做多商品货币(澳元、纽元、加元)。
2. 识别当前**市场结构**:趋势 / 区间 / 无序震荡——不同结构用不同执行方式(见步骤 3)。
3. 提前标出**关键位**:前高前低、结构位、成交密集区(POC)、整数关口。
4. 筛选 **1–3 个高确定性机会**,不要同时盯 10 个品种。
5. 为每笔制定**情景预案**:"如果 A 发生就做多,如果 B 发生就放弃"。
6. 明确**今天不交易**的条件:重大数据前、流动性差时段、情绪混乱时。
   - 盘面分析(结构 / K线 / 关键位 / 量价)方法见 `references/ta_reading.md`。

> 套用 `assets/trade_plan_template.md` 输出计划;事件日套用 `assets/scenario_plan_template.md`。
> **宏观到策略的完整推导**(含跨市场验证 Gate 与降级规则)见 `assets/analysis_to_strategy_template.md`,本步骤是其"第三–五阶"的落地。

### 步骤 2 — 入场执行

先读 `references/microstructure.md` 的执行细则;盘面结构清晰、止损前置即可入场(见 `references/ta_reading.md`)。"看大做小":大周期(日线/4H)定方向与关键位,小周期(1H/15m)定结构与触发。

1. **订单类型选择**:
   - 突破交易 → 用**止损单(Stop Order)挂单入场**,不等突破后追市价。
   - 回调交易 → 用**限价单(Limit Order)挂单入场**,不追价。
2. **真假突破识别**:突破后是否快速收回区间、量能/动能是否配合;假突破(快速收回)反向操作或放弃。
3. **止损前置**:入场前确定止损,放在结构外;止损距离由 **ATR 动态决定**(调用 `scripts/position_size.py`)。
4. **禁止动作**:重要数据公布前 5 分钟不用市价单;流动性差时段避免市价入场(控滑点,必要时限价)。
5. **手工下单顺序**:先设止损,再入场。
6. **纪律**:能接受"错过行情",不因为怕错过而降低入场标准。

### 步骤 3 — 持仓管理

1. 持仓后保持客观,不因浮盈浮亏改变原计划。
2. **移动止损规则**:如价格突破 20 EMA 后将止损移至入场价(保本)。
3. **分批止盈**:到达第一目标平 50%,剩余仓位移动止损。
4. **主动离场 vs 被动止损**提前定义清楚。
5. **绝不摊平亏损**:亏损单绝不加仓;盈利后才考虑是否加仓。
6. 记录持仓关键信息:价格触及关键位时的反应。
7. **隔夜持仓**:评估隔夜风险、库存费、跳空风险;同时持仓不超过 2–3 个高相关品种。
8. 根据波动调整持仓时间:震荡市缩短,趋势市延长。

### 步骤 4 — 离场策略

1. 提前设定止盈目标,来源:前高前低、斐波那契扩展、通道上轨、结构目标。
2. **时间止损**:持仓 N 小时未按预期走则离场(如 4 小时)。
3. **保本止损**:盈利达一定幅度后,止损移至成本价;避免"盈利拿成亏损"。
4. 识别止损被扫后反转的情况,制定再入场规则。
5. 重大事件前主动减仓/离场,避免跳空风险。
6. 接受"不完美出场":不追求卖在最高、买在最低。
7. 记录离场理由,分"按计划"与"临时决定"。

### 步骤 5 — 交易记录与复盘

每笔必记字段(用 `assets/trade_journal_template.md`):日期、品种、方向、手数、入场价、止损、目标、离场价、盈亏、持仓时间、入场理由(技术/宏观/跨市场/盘感)、离场理由、情绪状态、执行评分 1–5。

- **每周复盘**:胜率、盈亏比、期望值、最大回撤、连续亏损次数;绩效归因(系统信号 vs 临时决定)。
- **每月复盘**:最赚钱/最亏钱的交易类型,强化或剔除。
- 检查反复犯的错误,据复盘调整计划,不重复同样错误。

### 步骤 6 — 心理与纪律(贯穿全程)

- 等待自己的信号,不勉强交易;亏损是交易一部分,不报复性交易。
- 每天交易不超过 3–5 笔,避免过度交易与"怕错过"追单。
- 盈利后保持谨慎(不因连胜放大仓位),亏损后保持冷静(不降标准回本)。
- 接受"错过行情"不后悔;坚持计划不因盘中波动改方向。
- 区分"好的亏损"(按计划止损)与"坏的亏损"(违反计划)。
- 愤怒/兴奋/恐惧时远离键盘;每天 5 分钟情绪记录。

## 事件驱动手册(盘中应对)

详见 `references/risk_psychology.md` 的事件章节,要点:

- **非农(NFP)**:提前设双向挂单或完全空仓,不追单。
- **FOMC**:等声明+新闻发布会,看第一波方向,再决定是否参与第二波。
- **突破行情**:确认后等回踩不破再入场,不追高。
- **假突破**:价格快速收回区间内,反向操作或放弃。
- **区间震荡**:区间边缘反向,止损放区间外。
- **单边趋势**:只顺趋势,回调至均线/结构位入场。
- **流动性扫荡**:识别大资金打止损后反向,避免被扫。
- **时段**:欧/美盘重叠波动大适突破;亚盘波动小适观望/区间。
- 行情快时减少交易,行情清晰时增加。

## 参考知识库(按需加载)

| 文件 | 覆盖模块 | 何时加载 |
|------|----------|----------|
| `references/analysis_framework.md` | 分析思路 · 三维印证 | 任何分析起步;先建立"宏观→跨市场→盘面"印证框架再动手 |
| `references/macro_rates.md` | 模块一 + 宏观地基 | 步骤0、任何利率/央行/曲线/利差问题 |
| `references/fx.md` | 模块二 外汇 | USD/JPY、AUD、CAD、套息、美元微笑、CFTC 拥挤度 |
| `references/gold.md` | 模块三 黄金 | TIPS 锚、金银比、央行购金、季节性、地缘 |
| `references/oil.md` | 模块四 原油 | EIA 库存、OPEC+、期限结构、WTI-Brent、裂解价差 |
| `references/cross_market.md` | 模块五 跨市场 | risk-on/off、regime、滚动相关性、铜金比/油金比/金银比 |
| `references/microstructure.md` | 模块六 微观结构 | Volume Profile、订单流、流动性扫荡、事件执行 |
| `references/ta_reading.md` | 模块九 盘面分析 | K线语言、趋势/区间、关键位体系、量价、ATR、盘面分析清单 |
| `references/data_sources.md` | 信息溯源总纲 | 所有模块的权威取数渠道(FRED/FedWatch/CFTC/BIS/EIA/IMF/World Bank/QuantGist/实时行情 Frankfurter·gold-api·US Treasury·exchangerate-api·新浪/IEA/OPEC/WGC/央行官网)与标注纪律 |
| `references/risk_psychology.md` | 模块七+八 风险与心理 | 仓位计算、组合暴露、压力测试、纪律、复盘 |

## 模板(直接套用输出)

- `assets/trade_plan_template.md` — 次日交易计划(8 字段 + 情景预案)。
- `assets/trade_journal_template.md` — 交易日志(逐笔 + 周/月复盘)。
- `assets/macro_dashboard_template.md` — 跨市场宏观仪表盘九宫格 + 央行对比表。
- `assets/scenario_plan_template.md` — 事件日"情景—反应"预案(NFP/FOMC/CPI/EIA)。
- `assets/analysis_to_strategy_template.md` — 宏观研判→跨市场验证→实盘结构→可执行策略的三阶闭环模板(含 Gate 与降级规则)。

## 计算脚本与权威取数(确定性执行)

- `scripts/position_size.py` — 输入账户权益、单笔风险%、止损距离(ATR 或点数)、合约乘数,输出**手数**与风险金额;支持 FX / 黄金 / 原油品种参数。
- `scripts/exposure.py` — 输入多笔持仓的方向与手数,计算**组合净方向暴露**与相关性集中度,标记是否超过总资金 3%–5% 上限或形成单一美元空头暴露;附 FOMC 意外 / 美股-5% / 油价-10% 压力测试。
- `scripts/bis_fetch.py` — **BIS 官方统计 API(SDMX v2,无需 key)**:拉取各国央行政策利率(`WS_CBPOL`)、美元汇率(`WS_XRU`)、有效汇率(`WS_EER`)、全球流动性(`WS_GLI`),输出 CSV,供宏观利率地基与外汇研判直接使用。
- `scripts/eia_fetch.py` — **EIA v2 API(原油模块,key 已配置于 `scripts/.eia_key`,不入 zip)**:拉取周度原油库存 `WCRSTUS1` / 汽油总库存 `WGTSTUS1` / 馏分油库存 `WDISTUS1`(千桶)、WTI `RWTC`/Brent `RBRTE` 现货价(美元/桶),输出 CSV,供原油模块与 EIA 事件交易研判直接使用(sndw 路由强制 `frequency=weekly`,系列用 `facets[series][]` 过滤;已移除无对应 ID 的 `crude_prod` 预设)。
- `scripts/imf_fetch.py` — **IMF SDMX 3.0 API(宏观/外汇,无需 key,base 可配)**:拉取 COFER 美元储备份额、IFS 实际有效汇率/官方储备/货币总量、WEO 宏观预测、BOP 国际收支、DOT 贸易方向,输出 CSV,供宏观利率地基与外汇研判直接使用(编写时 IMF 端点临时不可达,需本地 `--list` 验证连通性)。
- `scripts/worldbank_fetch.py` — **World Bank Open Data API(宏观/外汇基本面,无需 key)**:拉取实际利率 `FR.INR.RINR`、CPI 通胀 `FP.CPI.TOTL.ZG`、经常账户占 GDP `BN.CAB.XOKA.GD.ZS`、GDP 增速 `NY.GDP.MKTP.KD.ZG`、官方汇率 `PA.NUS.FCRF`、外储 `FI.RES.TOTL.CD`、政府债务 `GC.DOD.TOTL.GD.ZS`,输出 CSV,直接支撑利率平价(IRP)/套息利差、中期汇率方向与 EM 脆弱性研判(本环境实测 HTTP 200 可用)。
- `scripts/quantgist_fetch.py` — **QuantGist API v1(事件驱动/地缘情报层,需 X-API-Key)**:拉取经济日历/事件(`actual/forecast/surprise_pct`)、宏数据最近值(CPI/NFP/PCE/FOMC 等别名)、**新闻雷达 `news/radar`**(地缘/油价供给/制裁/央行意外/中东风险/OPEC 主题,含 `impact_score`、`confidence`、`affected_assets` 如 GLD/XAUUSD/CL/USO)、商品 ETF 快照(GLD/USO 实时价)、情绪/意外/影响力排名,输出 CSV,补 BIS/EIA/IMF/World Bank 只有宏观基本面、缺事件情报的短板(部分端点 Starter+ 套餐限制,返回 402 时提示升级)。
- `scripts/live_market_fetch.py` — **实时行情聚合 API(外汇/黄金现货实时报价,无需 key,纯标准库)**:聚合 5 个本环境实测可达、免 key 源——Frankfurter(ECB 官方日参考汇率 `fx_ref`)、gold-api.com(伦敦金 XAU 现货价 `gold`)、US Treasury Fiscal Data(美债收益率/汇率 `ust_yield`)、exchangerate-api(open.er-api.com,150+ 货币 `fx_all`)、新浪财经(USDCNY 即期 + 伦敦金 hf_XAU **真实时**,需 Referer+GBK 解码 `sina`);另支持 `--preset all` 一键聚合。输出 CSV(UTF-8-SIG)或 JSON,直接服务盘中实时报价与事件前后价格反应监控(本环境 2026-08-27 复测全部 200/GBK 实时)。

调用示例(用受管 Python):
`python scripts/position_size.py --equity 100000 --risk 1 --stop 35 --multiplier 10`
`python scripts/exposure.py --positions "XAUUSD:long:0.5" "AUDUSD:long:1.0" --equity 100000`
`python scripts/bis_fetch.py --preset policy_rates --last 24 --out "./output/bis_policy.csv"`
`python scripts/eia_fetch.py --preset crude_stocks --last 12 --out "./output/eia_crude.csv"`
`python scripts/imf_fetch.py --preset cofer --format csv --out "./output/imf_cofer.csv"`
`python scripts/worldbank_fetch.py --preset real_rate --country "US;CN;JP;EU" --mrnev 5 --out "./output/wb_realrate.csv"`
`python scripts/quantgist_fetch.py --preset calendar --api-key $QUANTGIST_API_KEY`
`python scripts/quantgist_fetch.py --preset news_radar --min-impact 0.6 --api-key $QUANTGIST_API_KEY --out "./output/qg_radar.csv"`
`python scripts/quantgist_fetch.py --preset commodities --api-key $QUANTGIST_API_KEY`
`python scripts/live_market_fetch.py --preset fx_ref --from USD --to CNY,EUR,JPY --out "./output/fx_ref.csv"`
`python scripts/live_market_fetch.py --preset gold --out "./output/gold.csv"`
`python scripts/live_market_fetch.py --preset sina --list "USDCNY,hf_XAU"   # 真实时报价`
`python scripts/live_market_fetch.py --preset all --json   # 一键聚合 5 源`

## 工具与数据源集成(权威渠道)

所有取数渠道、获取方式与溯源纪律,统一见 **`references/data_sources.md`**(信息溯源总纲)。要点:

- **宏观利率**:FRED(`DGS10`/`DFII10`/`T10YIE`)、美联储官网(点阵图/SEP)、CME FedWatch、**IMF SDMX 3.0 API(`scripts/imf_fetch.py`:IFS 实际有效汇率 `PRX_REER`/官方储备/货币总量、WEO 宏观预测,无需 key,需本地验证连通性)**、**World Bank Open Data API(`scripts/worldbank_fetch.py`:实际利率 `FR.INR.RINR`/CPI 通胀 `FP.CPI.TOTL.ZG`/GDP 增速 `NY.GDP.MKTP.KD.ZG`/官方汇率 `PA.NUS.FCRF`,无需 key)**。
- **外汇**:CFTC COT/TFF(持仓拥挤度)、**BIS SDMX v2 API(`scripts/bis_fetch.py`:政策利率 `WS_CBPOL` / 美元汇率 `WS_XRU` / 有效汇率 `WS_EER` / 全球流动性 `WS_GLI`,无需 key)**、**IMF SDMX 3.0 API(`scripts/imf_fetch.py`:COFER 美元储备份额——全球去美元化/美元信用结构性核心指标,无需 key,需本地验证连通性)**、**World Bank Open Data API(`scripts/worldbank_fetch.py`:实际利率 `FR.INR.RINR`/经常账户占 GDP `BN.CAB.XOKA.GD.ZS`/外储 `FI.RES.TOTL.CD`——利率平价(IRP)、中期汇率方向与 EM 脆弱性,无需 key)**、**实时行情 API(`scripts/live_market_fetch.py`:Frankfurter ECB 日参考汇率 `fx_ref`、exchangerate-api 150+ 货币 `fx_all`、新浪 USDCNY **真实时** `sina`,均无需 key)**、ECB/BoJ/BoE 官网、PBOC 中间价。
- **黄金**:World Gold Council(供需/央行购金/ETF)、LBMA 定盘、CFTC 持仓、**QuantGist API(`scripts/quantgist_fetch.py`:`news/radar` 地缘主题包含 GLD/XAUUSD、商品 ETF 快照 GLD 实时价,需 X-API-Key)**、**实时行情 API(`scripts/live_market_fetch.py`:gold-api.com 伦敦金 XAU 现货价 `gold`、新浪 hf_XAU **真实时** `sina`,均无需 key)**。
- **原油**:**EIA v2 API(`scripts/eia_fetch.py`:周度库存 `WCRSTUS1` / 汽油总库存 `WGTSTUS1` / 馏分油库存 `WDISTUS1`(千桶)、WTI `RWTC`/Brent `RBRTE` 现货价(美元/桶),key 已配置 `scripts/.eia_key`)**、IEA、OPEC(MOMR)、API 补充、**QuantGist API(`scripts/quantgist_fetch.py`:`news/radar` 含 oil-supply/middle-east-risk/opec 主题与 CL/USO 受影响资产、商品 ETF 快照 USO,需 X-API-Key)**。
- **跨市场**:TradingView 图表模板、用户"全球金融日报"JSON(复用 40 品种,免重复采集)。
- **事件日历**:美联储日历、Trading Economics、Investing.com、**QuantGist API(`scripts/quantgist_fetch.py`:`calendar`/`events` 含 `actual/forecast/surprise`、宏数据 `macro/latest` CPI/NFP/FOMC,需 X-API-Key)**。

铁律:结论标注 `[源 | 截至]`;社媒/自媒体仅作情绪参考,不作方向依据。

## 输出规范

- 输出交易计划用 `assets/trade_plan_template.md` 结构;事件日用情景预案结构。
- 交易策略须以文字清晰写出入场区 / 止损 / 目标,不凭感觉开仓;盘面分析结论(结构、关键位、K线信号、ATR)见 `references/ta_reading.md`。
- 涉及仓位/止损计算,优先调用 `scripts/` 给出精确数字,不靠心算。
- 任何结论区分"事实/数据"与"观点/概率";事件交易强调"预期差比方向更重要"。
- 不生成自动化交易代码,不代客下单;本技能只服务于手工交易者的决策与纪律。

## 密钥安全（EIA / QuantGist）

- **EIA key**:已写入 `scripts/.eia_key`(脚本同目录单行纯文本),**仅本地存在、不进入 `kingforex-skill.zip`、不写进脚本源码**。读取优先级:`--api-key` > 环境变量 `EIA_API_KEY` > `scripts/.eia_key`。用户重装/迁移 skill 后需重新生成该文件或设置环境变量。
- **QuantGist key**:通过环境变量 `QUANTGIST_API_KEY` 或 `--api-key` 传入,同样不硬编码进脚本与 zip。
- **原则**:真实密钥(第三方 API key)一律不落盘于可分发产物(zip/源码),避免泄露;本地便利文件(`.eia_key`)由用户自行保管。如怀疑泄露,立即到对应平台吊销并换新 key。
