---
name: kingforex-skill
agent_created: true
description: "手工外汇/贵金属/大宗商品现货交易者的宏观交易体系与纪律框架,覆盖宏观利率地基、盘前计划筛选、入场执行、持仓管理、离场策略、交易记录复盘、心理纪律全链路,以及外汇/黄金/原油专项、跨市场联动、市场微观结构、风险组合管理、工具数据源九大模块。当用户要求制定下一交易日交易计划、筛选高确定性机会、分析美债/实际利率/盈亏平衡通胀/点阵图/FedWatch/央行周期、做外汇(套息/避险/商品货币/美元微笑)或黄金(TIPS锚/金银比/央行购金)或原油(EIA/OPEC/期限结构)的宏观分析、按ATR计算止损与风险仓位、做相关性或净暴露压力测试、处理非农/FOMC/CPI/EIA事件交易、写交易日志或周月复盘,以及提及交易计划/头寸管理/止损止盈/仓位计算/复盘/不摊平/连续亏损暂停/资金管理/仓位管理/凯利公式/R倍数/回撤控制/本金保护/风险预算/破产风险/资金曲线等纪律与资金管控关键词,或要求从权威数据源(FRED/FedWatch/CFTC COT/TFF 持仓拥挤度/BIS/EIA/IMF/World Bank/QuantGist/WGC/LBMA/OPEC/金十 Jin10/金十数据/iTick/goldprice.dev/OilPriceAPI 等)获取信息、获取实时行情/快讯/财经日历(金十 Jin10)、分析最新快讯/突发消息/财经日历事件、分析持仓拥挤度/投机净头寸/多空比/降息概率/黄金供需/原油供需平衡、做期货分析(期现结构/基差/期货期限结构/期货价差/跨期价差/跨品种价差 WTI-Brent)、用 iTick 拉取外汇/贵金属/期货实时报价与 K 线、用 goldprice.dev 取现货金价、用 OilPriceAPI 取 WTI/Brent 原油实时与历史价、用 BIS SDMX v2 或 EIA v2 或 IMF SDMX 3.0 或 World Bank Open Data 或 QuantGist 或实时行情 API(Frankfurter/gold-api/US Treasury/exchangerate-api/新浪/金十 Jin10)拉取宏观/外汇/原油/事件情报/实时报价数据、把宏观分析落地为可执行交易策略、做宏观到实盘到策略的链路分析、从宏观/跨市场/盘面多维度印证分析、进行盘面分析、解读K线图或盘面、识别K线形态(锤子线/上吊线/吞没/孕线/流星线/倒锤子线/内包线/十字星/marubozu/刺透线/乌云盖顶/启明星/黄昏星/红三兵/黑三鸦)、做通道与趋势线分析、判定均线多头/空头排列与金叉死叉、解读 MACD/RSI/布林带/随机指标、识别跳空/窗口(缺口)、用 ADX 判定趋势强度、画扇形线与斐波那契回撤、识别头肩/双顶底/三角/旗形/楔形等图表形态、从MT4导出K线做技术分析、联网获取K线数据(15min/1H/4H/1D/1W)/从Twelve Data获取K线/用户已发K线数据待分析时、做多周期共振/三维印证/看大做小分析(周线+日线定方向背景、1H定进场时机)、把支撑位/阻力位/趋势线/均线系统/ATR多周期融合为共振区、要求盘面分析给出明确结论(做多/做空/不交易)且附图表与数据差异分析、用 mtf_confluence.py 做多周期共振判定时,加载本技能。"
---

# 手工交易体系(宏观 · 外汇 · 贵金属 · 商品)

## 定位

本技能把用户给定的九大模块交易体系,转化为**可执行的每日工作流 + 可检索的领域知识 + 可直接套用的模板 + 确定性计算脚本**。它不是理论讲义,而是"盘前—盘中—盘后"的完整操作手册。面向**纯手工**外汇/贵金属/大宗商品现货交易者,禁止任何自动下单逻辑,只输出计划、检查清单、计算与复盘。

## 分析主线:权威取数 → 宏观研判 → 实盘结构 → 交易策略

本技能的输出不是"观点",而是一条**可溯源、可降级、可执行**的决策链。任一环节 Gate 不通过,就降级或放弃,不得硬做:

1. **权威取数(第 0 阶)**:所有输入必须来自 `references/data_sources.md` 列出的权威渠道(FRED、FedWatch、CFTC、BIS、EIA、IMF、World Bank、QuantGist、实时行情源 Frankfurter/gold-api/US Treasury/exchangerate-api/新浪、IEA、OPEC、WGC、央行官网、用户"全球金融日报"JSON)。每条结论标注 `[源 | 截至]`;禁用未注明来源的社媒/自媒体作为方向依据。
2. **宏观研判(第一阶)**:回答利率地基三问、判定四大央行周期与宏观 Regime、定美元强弱与 risk-on/off。这是所有品种的方向地基。
3. **盘面分析(第二阶)**:在宏观定向下,用 K 线与技术结构(趋势/区间/震荡、关键位、K线形态、ATR、量价)确认"现在能不能做、怎么做"。宏观对、盘面不对,仍不入场。K 线形态部分可直接调用 `scripts/kline_read.py` 做**客观盘面解读**(自动输出趋势背景、市场结构、关键位、Morris 量化形态评级与确认状态);若用户**已发送 K 线数据**,直接读入分析;若**未发送**,可用 `--fetch` 经 Twelve Data 联网抓取 15min/1H/4H/1D/1W 五周期(需 API Key,缺失或失败则明确提示改用本地 CSV/文本,**绝不编造价格**)。
   - **多周期共振(看大做小)**:当需要做"方向 + 时机"的盘面判定时,调用 `scripts/mtf_confluence.py`,传入周线(W)+日线(D)+1小时(H1)三周期 K 线(CSV / 粘贴文本 / `--fetch`)。引擎输出方向共识矩阵、关键位融合(confluence zone,强度分级)、ATR 跨周期差异,并给出**明确结论(做多/做空/不交易)**——大周期(W+D)定方向背景、1H 定进场触发,逆大周期的单子一律"不交易"。方法学与 IMA 知识库引用见 `references/mtf_confluence.md`。
4. **交易策略(第三阶)**:把上述两层收敛为含品种/方向/触发/入场区/止损(ATR)/目标/仓位/失效条件的可执行计划,并用 `scripts/exposure.py` 做风险体检。

完整推导模板见 `assets/analysis_to_strategy_template.md`(含每阶 Gate 与降级规则)。

## 分析思路:三维印证(多维度互相印证才出手)

本技能拒绝"单一信号开仓",核心分析哲学是**三维印证**:**宏观定方向、跨市场验方向、盘面定时机**,三者层层收敛、互相印证——共振才高确定性出手,任一维度反向即降级或放弃。

- **宏观(地基)**:回答美元/利率/Regime/risk-on-off,定大方向(见 `references/macro_rates.md`)。
- **跨市场(验证)**:用 ≥2 个相关市场(如 TIPS/DXY 验黄金、铜/AUD-JPY 验澳元)确认方向是否共振,背离即警告(见 `references/cross_market.md`)。
- **盘面(时机)**:在结构合理处用 K 线/关键位/量价/ATR 找触发,且必须顺前两步方向(见 `references/ta_reading.md`)。

> 印证原则:**宏观错→全盘错;跨市场背离→不入场;盘面结构逆→不入场**。矛盾单宁可错过也不做。完整框架与决策矩阵见 `references/analysis_framework.md`。

当用户触发本技能时,先判断意图落入哪一段工作流,再按需加载 `references/` 与 `assets/`,必要时调用 `scripts/` 做确定性计算。不要把所有参考一次性灌入上下文——按当前步骤只加载相关文件。

### 前置铁律:时间核对与数据鲜度（每次调用第一动作,优先于一切研判）

- **先核对当下具体时间**:启动任何分析/取数前,必须首先确认"此刻"的**具体时间(日期 + 时分 + 时区)**,并以该时间为分析基准。严禁以会话历史里的旧时间戳、缓存文件的旧日期、或任何假设日期代替"当下"。对外口径统一用**北京时区(GMT+8)**,跨市场数据内部换算时标注原时区。
- **数据必须截止到最新**:宏观数据、经济数据、行情/报价数据,一律建立在**截至该当下时间的最新可用数据**之上——
  - 实时行情/快讯/财经日历:取"现在"的最新值,不沿用过期快照;
  - 日/周级序列(FRED、EIA、CFTC、央行、LBMA/WGC):取到最近一个已发布窗口(最近交易日/最近公布日),不得用更早的缓存假装"最新";
  - 若数据源因限流/网络暂时取不到最新值,必须**显式标注"数据截至 XXX(非最新)"**并说明原因,绝不允许静默用旧数据充当最新。
- **输出必须带已核对的时间戳**:每条数值与结论的 `[源 | 截至]` 必须填入**已核对的当下具体时间**(格式 `YYYY-MM-DD HH:MM TZ`);生成的计划/报告须在正文或文件名包含该基准时间,让阅读者一眼知道分析基准时刻。
- 该前置动作优先于一切研判——**时间错了,后面全错**。

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

**0.0 权威实证取数(第一动作)**:**先执行「前置铁律:时间核对与数据鲜度」——核对当下具体时间(北京时区),再拉取数据;所有宏观/经济/行情数据必须截止到该时刻的"最新可用"值,禁止用过期/缓存快照替代实时取数。** 随后用 `references/data_sources.md` 从权威渠道拉取当日数据——FRED 取 US10Y/10Y TIPS/盈亏平衡、CME FedWatch 取概率、CFTC 取持仓、EIA/OPEC 取原油供需、WGC 取黄金供需,或直接复用用户"全球金融日报"JSON。所有数值标注 `[源 | 截至]`,未溯源的数据不得进入后续研判。

1. 调用 `references/macro_rates.md`,先回答三个地基问题:
   - 名义利率、实际利率、通胀预期三者关系(一句话:实际利率=名义利率−通胀预期)。
   - 当前 US10Y、10Y TIPS、盈亏平衡通胀率所处的位置与方向。
   - 美联储 / 欧央行 / 日央行 / 英央行各自处在哪个货币政策周期(收紧 / 中性 / 宽松)。
2. 建立或更新**主要央行政策对比表**(目标、工具、资产负债表、前瞻指引)与**收益率曲线状态**(陡峭化 / 平坦化 / 倒挂及其对外汇商品的含义)。
3. 判断当前**宏观 regime**(四选一):增长强+通胀升 / 增长弱+通胀仍高 / 衰退预期+通胀回落 / 流动性危机避险。
4. 在交易计划模板中标注跨市场关键信号与方向(DXY、US10Y、10Y TIPS、盈亏平衡、黄金、WTI/Brent、铜、标普500、VIX、信用利差、AUD/JPY、USD/CAD、USD/CNH 的方向与背离);**本技能不单独维护看板/九宫格**,信号直接汇入交易计划与盘面研判,聚焦"验证方向 + 找触发"。
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
| `references/ta_reading.md` | 模块九 盘面分析 | **Morris 量化 K 线语言**(形态统计评级/确认机制/预测时效)、**经典日本蜡烛图形态**(十字星/纺锤/marubozu/刺透/乌云盖顶/启明星/黄昏星/红三兵/黑三鸦)、趋势/区间、关键位体系、量价、ATR、盘面分析清单 |
| `references/mtf_confluence.md` | 模块九 盘面·多周期 | **多周期共振(三维印证)方法论**:周线+日线定方向背景、1H 定进场时机;方向共识矩阵、关键位融合(confluence zone)强度分级、ATR 跨周期差异量化、明确结论分支(做多/做空/不交易)、`mtf_confluence.py` 用法与数据铁律(引用 IMA 知识库 魏强斌《外汇交易进阶》第十八阶多重时间框架 /《ATR止损法深度研究》) |
| `references/data_sources.md` | 信息溯源总纲 | 所有模块的权威取数渠道(FRED/FedWatch/CFTC/BIS/EIA/IMF/World Bank/QuantGist/实时行情 Frankfurter·gold-api·US Treasury·exchangerate-api·新浪/IEA/OPEC/WGC/央行官网)与标注纪律 |
| `references/indicators.md` | 技术指标详解 | 均线(MA/SMA/EMA/金叉死叉/多头空头排列/均线带)、ATR(真实波幅/吊灯止损/波动 regime)、MACD(DIF/DEA/柱/背离)、RSI、布林带、随机/KDJ、成交量,以及指标组合纪律与陷阱(同轴不叠加、四类正交组合) |
| `references/channels.md` | 通道与图表形态 | 趋势线、上升/下降/水平通道画法、通道交易法则、通道突破与回踩(throwback)、中线;经典形态(头肩/双顶底/三角/旗形/三角旗/楔形/圆底)及其确认与度量目标 |
| `references/risk_psychology.md` | 模块七+八 风险与心理 | 仓位计算、组合暴露、压力测试、纪律、复盘 |
| `references/money_management.md` | 模块补充 资金管控 | 仓位方法论(固定分数/凯利/R倍数)、风险预算分层、回撤降仓阶梯、连败暂停、保证金安全垫、破产风险,以及 `scripts/risk_unit.py` 用法 |
| `references/futures_analysis.md` | 期货分析(期现结构/基差/期货价差) | contango/backwardation 判定、基差与年化 carry 公式、曲线斜率、跨期价差、跨品种价差(WTI-Brent)与 z-score 偏离定位、交易含义,以及 `scripts/futures_analysis.py` 用法 |

## 模板(直接套用输出)

- `assets/trade_plan_template.md` — 次日交易计划(8 字段 + 情景预案)。
- `assets/trade_journal_template.md` — 交易日志(逐笔 + 周/月复盘)。
- *(已移除 `assets/macro_dashboard_template.md`:本技能不再维护独立看板/九宫格,跨市场信号直接汇入交易计划与盘面研判)*
- `assets/scenario_plan_template.md` — 事件日"情景—反应"预案(NFP/FOMC/CPI/EIA)。
- `assets/analysis_to_strategy_template.md` — 宏观研判→跨市场验证→实盘结构→可执行策略的三阶闭环模板(含 Gate 与降级规则)。

## 计算脚本与权威取数(确定性执行)

- `scripts/position_size.py` — 输入账户权益、单笔风险%、止损距离(ATR 或点数)、合约乘数,输出**手数**与风险金额;支持 FX / 黄金 / 原油品种参数。
- `scripts/exposure.py` — 输入多笔持仓的方向与手数,计算**组合净方向暴露**与相关性集中度,标记是否超过总资金 3%–5% 上限或形成单一美元空头暴露;附 FOMC 意外 / 美股-5% / 油价-10% 压力测试。
- `scripts/risk_unit.py` — **资金管控工具箱**(纯标准库):`kelly`(凯利/半凯利/硬封顶1%)、`expectancy`(R倍数期望值)、`drawdown`(回撤降仓查表)、`ruin`(固定分数法破产风险蒙特卡洛);把资金管控从经验变为可算数字,详见 `references/money_management.md`。
- `scripts/bis_fetch.py` — **BIS 官方统计 API(SDMX v2,无需 key)**:拉取各国央行政策利率(`WS_CBPOL`)、美元汇率(`WS_XRU`)、有效汇率(`WS_EER`)、全球流动性(`WS_GLI`),输出 CSV,供宏观利率地基与外汇研判直接使用。
- `scripts/eia_fetch.py` — **EIA v2 API(原油模块,key 由用户自备,存放于 `scripts/.eia_key`,不入 zip)**:拉取周度原油库存 `WCRSTUS1` / 汽油总库存 `WGTSTUS1` / 馏分油库存 `WDISTUS1`(千桶)、WTI `RWTC`/Brent `RBRTE` 现货价(美元/桶),输出 CSV,供原油模块与 EIA 事件交易研判直接使用(sndw 路由强制 `frequency=weekly`,系列用 `facets[series][]` 过滤;已移除无对应 ID 的 `crude_prod` 预设)。
- `scripts/fred_fetch.py` — **FRED(圣路易斯联储)宏观/利率 API v1(模块一 宏观利率地基,key 由用户自备,存放于 `scripts/.fred_key`,不入 zip)**:拉取 10Y 名义利率 `DGS10`、10Y 实际利率(TIPS) `DFII10`(黄金定价第一锚)、10Y 盈亏平衡通胀 `T10YIE`、2s10s 利差 `T10Y2Y`(曲线倒挂/衰退信号)、短端 `DGS3MO`/`DGS1`/`DGS2`/`DGS5`、联邦基金利率 `FEDFUNDS`/`DFF`、长端 `DGS30`,输出 CSV(宽表)/JSON,供美元方向、实际利率、收益率曲线研判直接使用。Key 读取优先级:`--api-key` > 环境变量 `FRED_API_KEY` > `scripts/.fred_key`。
- `scripts/imf_fetch.py` — **IMF SDMX 3.0 API(宏观/外汇,无需 key,base 可配)**:拉取 COFER 美元储备份额、IFS 实际有效汇率/官方储备/货币总量、WEO 宏观预测、BOP 国际收支、DOT 贸易方向,输出 CSV,供宏观利率地基与外汇研判直接使用(编写时 IMF 端点临时不可达,需本地 `--list` 验证连通性)。
- `scripts/worldbank_fetch.py` — **World Bank Open Data API(宏观/外汇基本面,无需 key)**:拉取实际利率 `FR.INR.RINR`、CPI 通胀 `FP.CPI.TOTL.ZG`、经常账户占 GDP `BN.CAB.XOKA.GD.ZS`、GDP 增速 `NY.GDP.MKTP.KD.ZG`、官方汇率 `PA.NUS.FCRF`、外储 `FI.RES.TOTL.CD`、政府债务 `GC.DOD.TOTL.GD.ZS`,输出 CSV,直接支撑利率平价(IRP)/套息利差、中期汇率方向与 EM 脆弱性研判(本环境实测 HTTP 200 可用)。
- `scripts/quantgist_fetch.py` — **QuantGist API v1(事件驱动/地缘情报层,需 X-API-Key)**:拉取经济日历/事件(`actual/forecast/surprise_pct`)、宏数据最近值(CPI/NFP/PCE/FOMC 等别名)、**新闻雷达 `news/radar`**(地缘/油价供给/制裁/央行意外/中东风险/OPEC 主题,含 `impact_score`、`confidence`、`affected_assets` 如 GLD/XAUUSD/CL/USO)、商品 ETF 快照(GLD/USO 实时价)、情绪/意外/影响力排名,输出 CSV,补 BIS/EIA/IMF/World Bank 只有宏观基本面、缺事件情报的短板(部分端点 Starter+ 套餐限制,返回 402 时提示升级)。
- `scripts/kline_read.py` — **K 线盘面解读引擎(双输入:①用户 MT4 导出 CSV / 粘贴文本,②`--fetch` 联网抓取,纯标准库)**:输出趋势背景(ATR 归一化摆动斜率,样本不足时 EMA 兜底)、市场结构(HH/HL/LH/LL)、EMA20/50 排列、ATR(14)、关键支撑阻力与整数关口、**Morris《蜡烛图精解》量化形态识别**(倒锤子线/上吊线/锤子线/流星线/吞没/孕线/内包线),每个形态附 **1 日胜率、净盈亏比 pnl1、★评级、确认要求与确认状态(已确认/已证伪/待确认)**,自动过滤已证伪形态;另输出**回归通道**(上/中/下轨与突破/跌破状态)、**MACD**(DIF/DEA/柱/近期金叉死叉/顶底背离)、**RSI(14)**、**布林带**(20,±2σ)、**随机 %K/%D**,以及**经典日本蜡烛图形态补充集**(十字星/纺锤/marubozu/刺透/乌云盖顶/启明星/黄昏星/红三兵/黑三鸦)。支持 `--json`(结构化)与 `--html`(ECharts K 线标注图,含通道轨线)。**`--fetch` 模式**:当用户未发送 K 线时,经 `scripts/kline_fetch.py` 从 Twelve Data 权威抓取 15min/1H/4H/1D/1W 五周期并逐周期自动分析;API Key 缺失/网络受限/品种不支持时,仅报告原因并引导改用 `--csv`/`--text`,**严禁自行编造或估算任何价格**。形态标准与统计表见 `references/ta_reading.md` 第 2 节;指标算法与信号纪律见 `references/indicators.md`;通道与图表形态见 `references/channels.md`;K 线抓取源与纪律见 `references/data_sources.md`。

- `scripts/mtf_confluence.py` — **多周期共振(三维印证)分析引擎(纯标准库,直接复用 `kline_read.analyze` + `kline_fetch.fetch_one`)**:输入 W/D/1H 三周期 K 线(CSV / 粘贴文本 / `--fetch` 联网),聚合输出**方向共识矩阵**(每周期趋势背景+EMA排列+摆动结构三方投票)、**关键位融合(confluence zone)**(三周期阻力/支撑/整数位邻近聚类,按跨周期数/测试次数定强/中/弱)、**ATR 跨周期差异量化**(日线 ATR≈几倍 1H ATR、周线 ATR≈几倍日线 ATR、波动 regime),并据"W+D 背景同向 + 1H 顺向"给出**明确结论**:做多/做空(含锚定共振区的入场/止损=结构外 1.5×ATR_1H/目标=最近共振区/R 倍数)或**不交易**(指明冲突周期)。结论文本禁用模糊词,全部基于客观数值。支持 `--json`(结构化结论)与 `--html`(**9 段深度分析报告**:执行摘要+三维共振总览+宏观/跨市场衔接+各周期深度盘面+关键位融合+ATR 跨周期波动+交易计划+风险与纪律+数据溯源,霓虹暗色版面、粘性导航、多图联动,满足 10+ 页深度输出)。方法学与 IMA 知识库引用见 `references/mtf_confluence.md`。
- `scripts/live_market_fetch.py` — **实时行情聚合 API(外汇/黄金现货实时报价,无需 key,纯标准库)**:聚合 5 个本环境实测可达、免 key 源——Frankfurter(ECB 官方日参考汇率 `fx_ref`)、gold-api.com(伦敦金 XAU 现货价 `gold`)、US Treasury Fiscal Data(美债收益率/汇率 `ust_yield`)、exchangerate-api(open.er-api.com,150+ 货币 `fx_all`)、新浪财经(USDCNY 即期 + 伦敦金 hf_XAU **真实时**,需 Referer+GBK 解码 `sina`);另支持 `--preset all` 一键聚合。输出 CSV(UTF-8-SIG)或 JSON,直接服务盘中实时报价与事件前后价格反应监控(本环境 2026-08-27 复测全部 200/GBK 实时)。
- `scripts/jin10_mcp.py` — **金十数据 Jin10 MCP 客户端(实时行情/快讯/资讯/财经日历,纯标准库)**:标准 MCP streamable-HTTP 流程(initialize→notifications/initialized→tools/list/resources/list→tools/call,协议 2025-11-25),Bearer Token 访问 `mcp.jin10.com`;覆盖 `get_quote`(XAUUSD 伦敦金/USOIL WTI/USDJPY 等实时报价)、`get_kline`(K线)、`list_flash`/`search_flash`(关键词:黄金/原油/美联储/日元/通胀/非农/日本央行/欧佩克)、`list_news`/`search_news`/`get_news`(深度资讯)、`list_calendar`(财经日历 pub_time/star/title/previous/consensus/actual/revised/affect_txt);资源 `quote://codes` 列可用品种代码。结果优先 `structuredContent`,分页统一 `cursor`/`next_cursor`/`has_more`;每日每工具限流 1500 次(北京时间自然日)。Token 经 MCP 配置或 `scripts/.jin10_key` 提供,不进 zip。
- `scripts/itick_fetch.py` — **iTick 行情(外汇/贵金属/期货 实时报价 + K 线,纯标准库)**:覆盖外汇(XAUUSD/EURUSD/USDJPY 等)、期货(黄金 GC / 原油 CL / 股指 ES 等)、股票、crypto;免费套餐 key 走 `api-free.itick.org`(限频 5 次/分钟,429 时优雅提示稍候),付费 key 用 `--base https://api.itick.org` 覆盖;认证头 `token`。`quote` 子命令取实时报价(`/forex/quote`、`/future/quote`,字段 s/p/o/h/l/v/ch/chp),`kline` 子命令取 K 线历史(`/forex/kline`、`/future/kline`,kType 支持 1m/5m/15m/30m/1h/2h/4h/1d/1w/1mo)。直接支撑**期货分析**(GC/CL 期货报价与曲线)。key 读取优先级:`--api-key` > 环境变量 `ITICK_API_KEY` > `scripts/.itick_key`(不进 zip)。
- `scripts/goldprice_fetch.py` — **goldprice.dev 现货金价(纯标准库)**:端点 `https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT`(亦支持 XAG-USD-SPOT 等);Free key 层用 `x-api-key` 头提频,免费层无需 key。⚠️ 透明说明:本构建/沙箱环境出口被 Cloudflare(错误 1010 browser signature)拦截,纯标准库 urllib 无法绕过(TLS 指纹层面限制,非代码/key 错误);脚本已对 403/Cloudflare 做友好降级,**在用户本机运行即可正常取数**,请勿据此判定 key 失效。key 读取优先级:`--api-key` > 环境变量 `GOLDPRICE_API_KEY` > `scripts/.goldprice_key`(不进 zip)。
- `scripts/oilprice_fetch.py` — **OilPriceAPI 原油实时/历史价(纯标准库)**:端点 `https://api.oilpriceapi.com/v1/prices/latest?by_code=WTI_USD`(实时)、`/v1/prices/all`(全部)、`/v1/prices/past_year?commodity=...&start_date=&end_date=`(历史,日度);认证头 `Authorization: Token <key>`(官方 SDK 1.13.0 源码确认)。常用 by_code:`WTI_USD`/`BRENT_CRUDE_USD`/`NATURAL_GAS_USD`/`HEATING_OIL_USD`/`DIESEL_USD`。直接输出 WTI-Brent 价差原料。key 读取优先级:`--api-key` > 环境变量 `OILPRICEAPI_KEY` > `scripts/.oilprice_key`(不进 zip)。
- `scripts/futures_analysis.py` — **期货分析引擎(期现结构 + 期货价差,纯标准库)**:① `basis` 子命令做**期现结构/基差分析**——输入现货价 + 多合约(标签:价:到期天数),输出每合约基差=现货−期货、基差率、年化 carry、相邻合约斜率、整体曲线 contango/backwardation 形态与交易含义;② `spread` 子命令做**期货价差分析**——跨期(近月−远月)与跨品种(如 WTI−Brent),可配合 `--series` 历史 CSV 算 z-score 定位偏离;③ `pull` 子命令直连新数据源实时分析——`--kind oil` 取 WTI/Brent(OilPriceAPI)算跨品种价差,`--kind gold` 取现货(goldprice.dev)+GC 期货(iTick)算期现结构。所有公式确定、不编造。

调用示例(用受管 Python):
`python scripts/position_size.py --equity 100000 --risk 1 --stop 35 --multiplier 10`
`python scripts/exposure.py --positions "XAUUSD:long:0.5" "AUDUSD:long:1.0" --equity 100000`
`python scripts/bis_fetch.py --preset policy_rates --last 24 --out "./output/bis_policy.csv"`
`python scripts/eia_fetch.py --preset crude_stocks --last 12 --out "./output/eia_crude.csv"`
`python scripts/imf_fetch.py --preset cofer --format csv --out "./output/imf_cofer.csv"`
`python scripts/worldbank_fetch.py --preset real_rate --country "US;CN;JP;EU" --mrnev 5 --out "./output/wb_realrate.csv"`
`python scripts/fred_fetch.py --preset all_rates --last 30 --out "./output/fred_rates.csv"   # 全曲线+实际/通胀/政策利率
`python scripts/fred_fetch.py --series DGS10,DFII10,T10YIE --last 60   # 名义/实际/盈亏平衡通胀(黄金定价锚)`
`python scripts/jin10_mcp.py quote XAUUSD                # 现货黄金实时报价(金十 MCP)`
`python scripts/jin10_mcp.py kline XAUUSD --count 20     # 黄金K线`
`python scripts/jin10_mcp.py flash --all                   # 最新快讯(全量翻页)`
`python scripts/jin10_mcp.py flash-search 美联储          # 美联储主题快讯`
`python scripts/jin10_mcp.py calendar                     # 财经日历`
`python scripts/jin10_mcp.py news-search 原油 --all       # 原油深度资讯`
`python scripts/itick_fetch.py quote --asset forex --region GB --code XAUUSD     # iTick 现货黄金实时报价`
`python scripts/itick_fetch.py quote --asset future --region US --code GC        # iTick 黄金期货 GC 实时报价`
`python scripts/itick_fetch.py quote --asset future --region US --code CL        # iTick WTI 原油期货 CL 实时报价`
`python scripts/itick_fetch.py kline --asset forex --region GB --code XAUUSD --kType 1d --limit 50   # 现货金日K线`
`python scripts/goldprice_fetch.py                                  # goldprice.dev 现货金(免费层)`
`python scripts/goldprice_fetch.py --symbol XAG-USD-SPOT            # 白银现货`
`python scripts/oilprice_fetch.py --code WTI_USD --code BRENT_CRUDE_USD   # OilPriceAPI WTI/Brent 实时`
`python scripts/oilprice_fetch.py --code WTI_USD --history --start 2026-08-01 --end 2026-09-04  # 历史`
`python scripts/futures_analysis.py basis --spot 2400 --fut 2405:2410:30 --fut 2408:2425:120   # 期现结构/基差`
`python scripts/futures_analysis.py spread --a WTI:91.97 --b BRENT:95.98   # 期货价差(WTI-Brent)`
`python scripts/futures_analysis.py pull --kind oil     # 直连 OilPriceAPI 实时算 WTI-Brent 价差`
`python scripts/futures_analysis.py pull --kind gold    # 直连 现货+GC期货 算期现结构`
`python scripts/quantgist_fetch.py --preset calendar --api-key $QUANTGIST_API_KEY`
`python scripts/quantgist_fetch.py --preset news_radar --min-impact 0.6 --api-key $QUANTGIST_API_KEY --out "./output/qg_radar.csv"`
`python scripts/quantgist_fetch.py --preset commodities --api-key $QUANTGIST_API_KEY`
`python scripts/live_market_fetch.py --preset fx_ref --from USD --to CNY,EUR,JPY --out "./output/fx_ref.csv"`
`python scripts/live_market_fetch.py --preset gold --out "./output/gold.csv"`
`python scripts/live_market_fetch.py --preset sina --list "USDCNY,hf_XAU"   # 真实时报价`
`python scripts/live_market_fetch.py --preset all --json   # 一键聚合 5 源`
- `scripts/cftc_fetch.py` — **CFTC COT/TFF 持仓拥挤度(免费·无需 key·中国可直连 cftc.gov)**:从 CFTC 官方年度历史文件(`fut_disagg_txt_YYYY.zip` 商品 / `fut_fin_txt_YYYY.zip` 外汇)解析 Managed Money(商品)或 Leveraged Funds(外汇)投机多/空/净头寸,输出**净头寸/OI、多空比 L/S、52 周历史分位(拥挤度等级:极度做多/偏拥挤做空/中性)、周环比 ΔNet/Δ净头寸-OI**;直接服务"持仓极度拥挤→反转风险"研判。支持 `--symbol GOLD/WTI/EURUSD/JPYUSD/AUDUSD/...`、`--market-code`、`--weeks`(分位窗口)、`--json`、`--from-file`(离线解析预下载文件)、`--list`(列品种);缓存到 `scripts/.cftc_cache`(默认 3 天,自动叠加前一年扩充历史)。取数铁律:只读官方公开文件,失败即报错,绝不杜撰。
- `scripts/wgc_lbma_fetch.py` — **黄金 LBMA 代理(免费·无需 key)**:经 gold-api.com 取国际现货金/银(美元/盎司,紧贴 LBMA 定盘)`--symbol XAU|XAG`;WGC 黄金供需/央行购金与 LBMA 官方定盘因无免费 JSON API,附 `--manual` 标准化 WebFetch 手工取数指引(绝不杜撰数字)。
- `scripts/opec_fetch.py` — **OPEC MOMR 原油报告(best-effort + 手工指引)**:尽力直连 OPEC 公开页抽取供需关键词,失败(网络/地域封锁,如本开发环境 opec.org 返回 403)则输出标准化 WebFetch 手工取数指引(全球需求增长/非 OPEC 供应/OPEC 产量/ORB 一揽子价);IEA MODS 为付费,附 KAPSARC 免费历史替代。绝不杜撰数字。
- `scripts/fedwatch_csv.py` — **CME FedWatch 降息/加息概率解析(手动导出桥接)**:FedWatch 无免费脚本化 API(需付费订阅 + OAuth),本脚本解析用户从 FedWatch Tool 网页**手动导出**的 CSV,转结构化"各 FOMC 会议 × 降息≥25bp/按兵不动/加息≥25bp 概率",`--json` 机器可读。附手动导出步骤。
`python scripts/cftc_fetch.py --symbol GOLD --weeks 52   # 黄金投机净头寸/52周拥挤度分位`
`python scripts/cftc_fetch.py --symbol EURUSD            # 欧元投机净头寸(杠杆基金)`
`python scripts/cftc_fetch.py --symbol AUDUSD --json     # 澳元(交易 AUDJPY 时联动)`
`python scripts/cftc_fetch.py --symbol WTI --weeks 26`
`python scripts/wgc_lbma_fetch.py --symbol XAU           # LBMA 金价现货代理(免费)`
`python scripts/opec_fetch.py --manual                   # OPEC MOMR 手工取数指引`
`python scripts/fedwatch_csv.py --csv "./output/fedwatch_2026-09-03.csv"   # FedWatch 导出CSV解析`
`python scripts/kline_read.py --csv "./output/EURUSD_H1.csv" --symbol EURUSD --tf H1 --last 120 --json --html --out "./output"`
`python scripts/kline_read.py --text "2026-08-20,1.0850,1.0890,1.0830,1.0880
2026-08-21,1.0880,1.0920,1.0860,1.0915" --symbol EURUSD --tf D1 --last 60`
`python scripts/kline_read.py --fetch --symbol USDJPY --api-key <TWELVEDATA_KEY>   # 未发K线时联网抓取15min/1H/4H/1D/1W并逐周期分析`
`python scripts/kline_read.py --fetch --symbol XAUUSD --api-key <TWELVEDATA_KEY> --json --out "./output"`
`python scripts/kline_fetch.py --symbol USOIL --interval 1h --api-key <TWELVEDATA_KEY>   # 单源单周期抓取(可输出CSV)`

# 多周期共振(三维印证):周线+日线定方向,1H 定时机 —— 输出明确做多/做空/不交易 + ECharts 图表
`python scripts/mtf_confluence.py --csv-w "./output/USDJPY_W.csv" --csv-d "./output/USDJPY_D.csv" --csv-h1 "./output/USDJPY_H1.csv" --symbol USDJPY --html --json --out "./output"`
`python scripts/mtf_confluence.py --fetch --symbol XAUUSD --api-key <TWELVEDATA_KEY> --html --json --out "./output"   # 未发K线时联网抓取 W/D/1H 并做共振判定`


## 工具与数据源集成(权威渠道)

所有取数渠道、获取方式与溯源纪律,统一见 **`references/data_sources.md`**(信息溯源总纲)。要点:

- **宏观利率**:FRED(`DGS10`/`DFII10`/`T10YIE`)、美联储官网(点阵图/SEP)、**CME FedWatch(无免费 API:用 `scripts/fedwatch_csv.py` 解析手动导出的概率 CSV)**、**IMF SDMX 3.0 API(`scripts/imf_fetch.py`:IFS 实际有效汇率 `PRX_REER`/官方储备/货币总量、WEO 宏观预测,无需 key,需本地验证连通性)**、**World Bank Open Data API(`scripts/worldbank_fetch.py`:实际利率 `FR.INR.RINR`/CPI 通胀 `FP.CPI.TOTL.ZG`/GDP 增速 `NY.GDP.MKTP.KD.ZG`/官方汇率 `PA.NUS.FCRF`,无需 key)**。
- **外汇**:**CFTC COT/TFF 持仓拥挤度(`scripts/cftc_fetch.py`:Managed Money(商品)/Leveraged Funds(外汇)投机净头寸、净头寸/OI、52 周历史分位拥挤度,免费无需 key、中国可直连 cftc.gov)**、**BIS SDMX v2 API(`scripts/bis_fetch.py`:政策利率 `WS_CBPOL` / 美元汇率 `WS_XRU` / 有效汇率 `WS_EER` / 全球流动性 `WS_GLI`,无需 key)**、**IMF SDMX 3.0 API(`scripts/imf_fetch.py`:COFER 美元储备份额——全球去美元化/美元信用结构性核心指标,无需 key,需本地验证连通性)**、**World Bank Open Data API(`scripts/worldbank_fetch.py`:实际利率 `FR.INR.RINR`/经常账户占 GDP `BN.CAB.XOKA.GD.ZS`/外储 `FI.RES.TOTL.CD`——利率平价(IRP)、中期汇率方向与 EM 脆弱性,无需 key)**、**实时行情 API(`scripts/live_market_fetch.py`:Frankfurter ECB 日参考汇率 `fx_ref`、exchangerate-api 150+ 货币 `fx_all`、新浪 USDCNY **真实时** `sina`,均无需 key)**、ECB/BoJ/BoE 官网、PBOC 中间价。
- **黄金**:World Gold Council(供需/央行购金/ETF)、LBMA 定盘、CFTC 持仓、**`scripts/wgc_lbma_fetch.py`(gold-api.com 伦敦金现货代理 `XAU`/`XAG` 免费无需 key + WGC/LBMA 手工取数指引)**、**QuantGist API(`scripts/quantgist_fetch.py`:`news/radar` 地缘主题包含 GLD/XAUUSD、商品 ETF 快照 GLD 实时价,需 X-API-Key)**、**实时行情 API(`scripts/live_market_fetch.py`:gold-api.com 伦敦金 XAU 现货价 `gold`、新浪 hf_XAU **真实时** `sina`,均无需 key)**。
- **原油**:**EIA v2 API(`scripts/eia_fetch.py`:周度库存 `WCRSTUS1` / 汽油总库存 `WGTSTUS1` / 馏分油库存 `WDISTUS1`(千桶)、WTI `RWTC`/Brent `RBRTE` 现货价(美元/桶),key 已配置 `scripts/.eia_key`)**、**`scripts/opec_fetch.py`(OPEC MOMR best-effort 直连 + WebFetch 手工取数指引:全球需求增长/非 OPEC 供应/OPEC 产量/ORB 一揽子价)**、IEA(付费 MODS,附 KAPSARC 免费历史替代)、API 补充、**QuantGist API(`scripts/quantgist_fetch.py`:`news/radar` 含 oil-supply/middle-east-risk/opec 主题与 CL/USO 受影响资产、商品 ETF 快照 USO,需 X-API-Key)**。
- **跨市场**:TradingView 图表模板、用户"全球金融日报"JSON(复用 40 品种,免重复采集)。
- **K 线历史(盘面分析用)**:当用户未发送 K 线时,**Twelve Data API(`scripts/kline_fetch.py` + `kline_read.py --fetch`)** 是中国大陆可直连、免翻墙的权威 OHLC 历史源,覆盖外汇/黄金/原油及 15min/1h/4h/1day/1week 五周期,需免费 API Key(环境变量 `TWELVEDATA_API_KEY` 或 `--api-key`)。抓取严格遵循**不编造铁律**:任一周期失败仅报告原因跳过,全部失败则明确告知"无法获取权威 K 线数据"并引导改用本地 CSV/文本,绝不估算价格。
- **事件日历**:美联储日历、Trading Economics、Investing.com、**QuantGist API(`scripts/quantgist_fetch.py`:`calendar`/`events` 含 `actual/forecast/surprise`、宏数据 `macro/latest` CPI/NFP/FOMC,需 X-API-Key)**。
- **实时行情/快讯/财经日历(金十 Jin10 MCP)**:`scripts/jin10_mcp.py`(标准 MCP 客户端,Bearer Token 访问 `mcp.jin10.com`)提供跨品种**实时行情** `get_quote`(XAUUSD 伦敦金/USOIL WTI/UKOIL 布伦特/XAGUSD 白银/USDJPY/EURUSD/USDCNH/COPPER 等,字段 open/close/high/low/volume/ups_price/ups_percent)、**K线** `get_kline`、**最新快讯** `list_flash`/`search_flash`(关键词:黄金/原油/美联储/日元/通胀/非农/日本央行/欧佩克)、**深度资讯** `list_news`/`search_news`/`get_news`、**财经日历** `list_calendar`(pub_time/star/title/previous/consensus/actual/revised/affect_txt);资源 `quote://codes` 列出可用品种代码。分页统一 `cursor`/`next_cursor`/`has_more`;每日每工具限流 1500 次(北京时间自然日),超额返回「今日该工具调用次数已达上限,请明日再试」。Token 经 MCP 配置或 `scripts/.jin10_key` 提供,不进 zip。事件前后用快讯/日历监控市场反应极佳。
- **期货分析数据源(iTick / goldprice.dev / OilPriceAPI)**:`scripts/itick_fetch.py` 取外汇/贵金属/期货实时报价与 K 线(期货 GC 黄金 / CL 原油直接支撑期现与价差分析;`api-free.itick.org` 免费层限频 5 次/分钟);`scripts/goldprice_fetch.py` 取 goldprice.dev 现货金价(`XAU-USD-SPOT`,现货端基准);`scripts/oilprice_fetch.py` 取 OilPriceAPI 的 WTI/Brent 实时与历史价(`Authorization: Token`,WTI-Brent 跨品种价差原料)。三者经 `scripts/futures_analysis.py` 的 `pull` 子命令直连聚合——`--kind oil` 实时算 WTI−Brent 价差,`--kind gold` 算黄金期现结构(现货−GC 期货基差);亦可用 `basis`/`spread` 子命令纯输入计算(期现结构 contango/backwardation、跨期/跨品种价差与 z-score 偏离)。goldprice.dev 在本构建环境被 Cloudflare 拦截(本机正常),属已知限制。
- **期货分析(期现结构 / 期货价差)**:模块四(原油)与模块三(黄金)新增期限结构研判维度——用 `scripts/futures_analysis.py` 量化基差、年化 carry、曲线形态与跨期/跨品种价差,补 EIA/OPEC 只有库存供需、缺"期现+曲线"的短板;方法学与公式见 `references/futures_analysis.md`。

铁律:结论标注 `[源 | 截至]`;社媒/自媒体仅作情绪参考,不作方向依据。

## 输出规范(强制)

- **输出交易计划时**,AI 必须严格按以下表格输出(数字必须具体,不得省略任何行):
  | 项目 | 具体数值 |
  | :--- | :--- |
  | **交易品种** | XAUUSD / EURUSD |
  | **方向** | Buy / Sell |
  | **挂单类型** | Limit / Stop |
  | **入场价格** | （精确到小数点后2位） |
  | **止损价格** | （前低/前高外扩5点，或 1.5倍 ATR） |
  | **止盈目标1** | （盈亏比 1:1，平仓50%） |
  | **止盈目标2** | （盈亏比 1:2 或 1:3，移动止损） |
  | **仓位计算参数** | 账户权益 * 1% / （入场价-止损价）* 合约乘数 = **建议开仓手数** |
  | **计划失效条件** | （例如：若1小时内未触及入场价，或价格反向突破XX，则撤单） |

  > **额外纪律提醒**:本计划仅基于当前静态数据。若挂单后遇到突发事件,请手动撤单。止损不后移,不加仓。
- **分析结论只分两种,按实际判断输出,不强行每次都给交易结论**:
  - **存在高确定性机会**(宏观/跨市场/盘面三维印证共振,且风险可控) → 按下方表格输出交易计划(可多行,每行一个机会);事件日仍套用情景预案结构。
  - **不适合交易**(三维未共振 / 信号冲突 / 重大事件窗口前流动性差 / 无合格风险收益比触发) → 直接判定输出:**【今日无交易】**。无需硬凑交易计划,空仓即结论。
- **本技能聚焦分析与交易策略制定,不维护任何数据看板/仪表盘**;跨市场信号直接汇入交易计划与盘面研判(见 `references/cross_market.md`)。
- 交易策略须以文字清晰写出入场区 / 止损 / 目标,不凭感觉开仓;盘面分析结论(结构、关键位、K线信号、ATR)见 `references/ta_reading.md`。
- **仓位计算**由 `scripts/position_size.py` 按风险%反推;挂单类型区分 Limit(限价挂单,回踩入场)与 Stop(突破/破位追单)。
- 涉及仓位/止损计算,优先调用 `scripts/` 给出精确数字,不靠心算。
- 任何结论区分"事实/数据"与"观点/概率";事件交易强调"预期差比方向更重要"。
- **时间基准与鲜度**:每条 `[源 | 截至]` 必须填入**已核对的当下具体时间**(`YYYY-MM-DD HH:MM TZ`);取数须为该时刻的最新可用值,逾期/缓存数据须显式标注"非最新"及原因,严禁静默以旧充新。分析、计划、报告文件名均应携带该基准时间。
- 不生成自动化交易代码,不代客下单;本技能只服务于手工交易者的决策与纪律。

## 密钥安全（EIA / FRED / QuantGist / Jin10）

- **EIA key**:由用户写入 `scripts/.eia_key`(脚本同目录单行纯文本),**仅本地存在、不进入 `kingforex-skill.zip`、不写进脚本源码**。读取优先级:`--api-key` > 环境变量 `EIA_API_KEY` > `scripts/.eia_key`。用户重装/迁移 skill 后需重新生成该文件或设置环境变量。
- **FRED key**(模块一 宏观利率地基,`scripts/fred_fetch.py`):由用户写入 `scripts/.fred_key`(脚本同目录单行纯文本,本地文件、不进 zip);读取优先级:`--api-key` > 环境变量 `FRED_API_KEY` > `scripts/.fred_key`。免费注册 https://fredaccount.stlouisfed.org/apikeys。
- **QuantGist key**:通过环境变量 `QUANTGIST_API_KEY` 或 `--api-key` 传入,同样不硬编码进脚本与 zip。
- **Twelve Data key**(K 线历史抓取,`scripts/kline_fetch.py` / `kline_read.py --fetch`):三种方式提供——环境变量 `TWELVEDATA_API_KEY` > `--api-key` > 脚本同目录 `scripts/.td_key`(单行纯文本,本地文件、不进 zip);读取优先级按此顺序。免费注册 https://twelvedata.com 获取。无 Key 时 `--fetch` 仅提示降级方案,绝不编造价格。
- **Jin10 MCP token**(实时行情/快讯/财经日历,`scripts/jin10_mcp.py` + MCP 客户端):Bearer Token 存于 `scripts/.jin10_key`(脚本用,单行纯文本,本地文件、不进 zip)与 MCP 配置 `headers.Authorization`(WorkBuddy MCP 客户端用);读取优先级:`--token` > 环境变量 `JIN10_TOKEN` > `scripts/.jin10_key`。不硬编码进脚本源码与 zip。
- **iTick key**(外汇/贵金属/期货行情,`scripts/itick_fetch.py`):存于 `scripts/.itick_key`(单行纯文本,本地文件、不进 zip);读取优先级:`--api-key` > 环境变量 `ITICK_API_KEY` > `scripts/.itick_key`。免费套餐走 `api-free.itick.org`(限频 5 次/分钟),付费 key 用 `--base https://api.itick.org`。
- **goldprice.dev key**(现货金价,`scripts/goldprice_fetch.py`):Free 层 key 存于 `scripts/.goldprice_key`(单行纯文本,本地文件、不进 zip);读取优先级:`--api-key` > 环境变量 `GOLDPRICE_API_KEY` > `scripts/.goldprice_key`。免费层亦可无 key 直连。
- **OilPriceAPI key**(WTI/Brent 原油价,`scripts/oilprice_fetch.py`):存于 `scripts/.oilprice_key`(单行纯文本,本地文件、不进 zip);读取优先级:`--api-key` > 环境变量 `OILPRICEAPI_KEY` > `scripts/.oilprice_key`。认证头 `Authorization: Token <key>`。
- **原则**:真实密钥(第三方 API key)一律不落盘于可分发产物(zip/源码),避免泄露;本地便利文件(`.eia_key` / `.fred_key` / `.td_key` / `.jin10_key` / `.itick_key` / `.goldprice_key` / `.oilprice_key`)由用户自行保管,打包/发布时强制排除。如怀疑泄露,立即到对应平台吊销并换新 key。
