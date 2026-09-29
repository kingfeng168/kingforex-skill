# 权威数据源速查(信息溯源总纲)

> **本技能铁律:所有宏观与实盘结论必须溯源到权威渠道。**
> 决策依据优先级:**一手官方源(央行/统计局/国际组织)> 权威聚合平台 > 社媒/自媒体**。
> 社媒与自媒体观点仅可作为"市场情绪参考",**不得作为方向依据**。每一阶分析结论都应标注来源与数据截至时间。

---

## 0. 通用原则

- **一手优先**:央行官网、各国统计局、国际组织(IMF/BIS/OECD/IEA/WGC)发布的数据,优先于任何二手解读。
- **免费优先**:下列源绝大多数免费;付费源(如 Wind/Refinitiv/Bloomberg)仅作标注,不要求。
- **标注格式**:每条结论附 `[源:xxx | 截至:YYYY-MM-DD]`,事件时点以官方日历为准,不臆测。
- **可复现**:能用 API/JSON 取得的,优先用 `scripts/` 内置脚本(BIS/EIA/IMF/World Bank/QuantGist/实时行情 等)拉取(见第 7 节),避免手动录入误差。

---

## 1. 宏观与利率(对应 `macro_rates.md`)

| 数据源 | 权威性 | 关键内容 / 系列 ID | 更新频率 | 获取方式 |
|--------|--------|--------------------|----------|----------|
| **FRED**(圣路易斯联储) `fred.stlouisfed.org` | 官方一手 | `DGS10`(10Y 名义利率)、`DFII10`(10Y TIPS 实际利率)、`T10YIE`(10Y 盈亏平衡通胀)、`T10Y2Y`(2s10s 利差)、`DGS3MO/DGS1/DGS2/DGS5/DGS30`(收益率曲线)、`FEDFUNDS/DFF`(政策利率) | 日频 | **脚本** `scripts/fred_fetch.py`(key 由用户自备,存放于 `scripts/.fred_key`,详见第 7.10 节);亦支持网页 / 公开 API(免费 key:`fredaccount.stlouisfed.org/apikeys`) |
| **美联储官网** `federalreserve.gov` | 官方一手 | SEP 经济预测摘要(含点阵图 Dot Plot)、FOMC 声明、鲍威尔发布会讲稿 | 每次会议 | 网页(经济预测摘要 / monetary policy) |
| **CME FedWatch** `cmegroup.com`(FedWatch Tool) | 市场隐含 | 联邦基金期货隐含的加息/降息概率路径 | 实时 | **无免费 API(需付费订阅 + OAuth)**;用 `scripts/fedwatch_csv.py` 解析网页手动导出的概率 CSV(详见第 7.8 节) |
| **克利夫兰联储 Inflation Expectations** `clevelandfed.org` | 官方一手 | 未来通胀预期模型 | 日/周 | 网页 |
| **IMF** `imf.org`(SDMX 3.0 API) | 国际组织一手 | ⚠️ **2026-09-28 实测:结构可取但观测值恒为 0,当前不可供数**(旧 id `IFS`/`DOT` 亦不存在);替代见 World Bank / BIS / FRED | 月/季 | **脚本** `scripts/imf_fetch.py`(详见 §7.3) |
| **World Bank** `worldbank.org`(Open Data API v2) | 国际组织一手 | 实际利率 `FR.INR.RINR`、CPI 通胀 `FP.CPI.TOTL.ZG`、GDP 增速 `NY.GDP.MKTP.KD.ZG`、官方汇率 `PA.NUS.FCRF`——利率平价(IRP)/套息利差、通胀差、增长 Regime | 年(多数) | **脚本** `scripts/worldbank_fetch.py`(详见第 7 节) |
| **QuantGist** `quantgist.com`(API v1) | 聚合一手 | 经济日历/事件(`actual/forecast/surprise_pct`)、宏数据最近值(CPI/NFP/PCE/FOMC)、新闻雷达(地缘/油价/央行意外)、商品 ETF 快照(GL/USO)、情绪/意外排名 | 实时/日 | **脚本** `scripts/quantgist_fetch.py`(需 X-API-Key,详见第 7 节) |
| **实时行情源(聚合,无需 key)** `Frankfurter/gold-api/US Treasury/exchangerate-api/新浪` | 实时/参考报价 | Frankfurter(ECB 官方日参考汇率)、gold-api.com(伦敦金 XAU 现货价,秒级)、US Treasury Fiscal Data(美债收益率/汇率)、exchangerate-api(150+ 货币)、新浪(USDCNY 即期 + 伦敦金 hf_XAU **真实时**)——盘中实时报价、事件前后价格反应监控 | 实时/日 | **脚本** `scripts/live_market_fetch.py`(详见第 7 节,均无需 key) |

---

## 2. 外汇(对应 `fx.md`)

| 数据源 | 权威性 | 关键内容 | 更新频率 | 获取方式 |
|--------|--------|----------|----------|----------|
| **CFTC COT / TFF** `cftc.gov`(或 `cot.futures.io`) | 官方一手 | 持仓拥挤度;TFF(Traders in Financial Futures)报告覆盖欧元、日元、英镑、澳元等金融期货投机净头寸 | 每周五发布(截至周二) | **脚本** `scripts/cftc_fetch.py`(免费·无需 key·中国可直连;详见第 7.8 节);也可网页/CSV |
| **BIS** `bis.org`(SDMX v2 API) | 国际组织一手 | 各国央行政策利率(`WS_CBPOL`)、美元汇率(`WS_XRU`)、有效汇率(`WS_EER`)、全球流动性(`WS_GLI`) | 月/季 | **脚本** `scripts/bis_fetch.py`(无需 key);详见第 7 节 |
| **IMF COFER** `imf.org`(SDMX 3.0 API) | 国际组织一手 | ⚠️ **当前不可供数(实测 0 观测)**:官方外汇储备币种构成——美元储备份额;恢复供数后可直接使用 | 季(年度详细) | **脚本** `scripts/imf_fetch.py`;详见 §7.3 |
| **World Bank** `worldbank.org`(Open Data API v2) | 国际组织一手 | 经常账户占 GDP(`BN.CAB.XOKA.GD.ZS`——中期汇率方向)、实际利率(`FR.INR.RINR`——套息/IRP)、外储(`FI.RES.TOTL.CD`——EM 脆弱性/干预能力)、政府债务(`GC.DOD.TOTL.GD.ZS`) | 年 | **脚本** `scripts/worldbank_fetch.py`;详见第 7 节 |
| **QuantGist** `quantgist.com`(API v1) | 聚合一手 | 经济事件 `affected_symbols` 含 EURUSD/USDJPY/GBPUSD 等、新闻雷达地缘主题(iran-war/oil-supply/middle-east-risk)、情绪/意外排名 | 实时 | **脚本** `scripts/quantgist_fetch.py`(需 X-API-Key,详见第 7 节) |
| **实时行情源(聚合,无需 key)** | 实时/参考报价 | Frankfurter(ECB 日参考汇率)、exchangerate-api(150+ 货币)、新浪(USDCNY **真实时** 即期)——盘中即期报价直达、事件前后汇率反应 | 实时/日 | **脚本** `scripts/live_market_fetch.py`(详见第 7 节,无需 key) |
| **ECB 官网** `ecb.europa.eu` | 官方一手 | 货币政策声明、利率决议、前瞻指引 | 每次会议 | 网页 |
| **BoJ 官网** `boj.or.jp` | 官方一手 | 政策利率、YCC/正常化进程、日元展望 | 每次会议 | 网页 |
| **BoE 官网** `bankofengland.co.uk` | 官方一手 | 利率决议、通胀报告、前瞻指引 | 每次会议 | 网页 |
| **PBOC / 外管局** `pbc.gov.cn` `safe.gov.cn` | 官方一手 | 人民币中间价、跨境资本流动 | 日频 | 网页 |
| **qveris MCP 市场(金银/外汇/宏观)** `mcp.qveris.ai` | 聚合市场(按调用计费) | 金银现货 XAU/XAG(`commodity_price_api.rates.live`,**填补白银 XAGUSD 缺口**)、外汇日线(`alphavantage.fx_daily`,USDJPY/EURUSD/AUDJPY 等,**无 Twelve Data 的 429 限频**)、外汇实时(`eodhd`,`XXX.FOREX`)、FRED 全系列(`stlouisfed_fred.*`)、央行利率 | 实时/日 | **脚本** `scripts/qveris_fetch.py`(详见第 7.16 节;Bearer token 读 `~/.workbuddy/mcp.json`,单次 ~1–9.55 credits,额度 1000) |
| **华尔街见闻 WSCN MCP** `xgb-mcp-api.xuangubao.cn` | 官方资讯(第二源) | 全球财经资讯**深度摘要 + 事件因果归因**、A 股大涨股异动逻辑——**与金十互补**(金十=速报,见闻=解读) | 日频 | **脚本** `scripts/wscn_fetch.py`(详见第 7.19 节;需 `.wscn_key` 且必须带 `X-WMCP-Client: wbwscn` 头,仅近两个月) |
| **美元指数 DXY** | 市场基准 | ICE 美元指数(一篮子 6 货币) | 实时 | TradingView / Yahoo / 经纪商终端 |

---

## 3. 黄金(对应 `gold.md`)

| 数据源 | 权威性 | 关键内容 | 更新频率 | 获取方式 |
|--------|--------|----------|----------|----------|
| **World Gold Council** `gold.org` | 行业权威一手 | 《Gold Demand Trends》季度报告、央行购金(官方部门统计)、ETF 流量、供需平衡 | 季度 / 月 | **脚本** `scripts/wgc_lbma_fetch.py`(`--manual` 标准化 WebFetch 手工指引);网页/报告下载 |
| **LBMA** `lbma.org.uk` | 行业基准 | 伦敦金银定盘价、贵金属清算数据 | 日频 | **脚本** `scripts/wgc_lbma_fetch.py`(gold-api.com 现货代理 `XAU`/`XAG`,免费无需 key);官方定盘需 `--manual` 手工取 |
| **CFTC COT**(见第 2 节) | 官方一手 | 黄金投机净头寸(拥挤度) | 周 | 同第 2 节 |
| **10Y TIPS**(FRED `DFII10`) | 官方一手 | 黄金定价第一锚(实际利率) | 日频 | 见第 1 节 |
| **gold-api.com / 新浪**(实时行情源) | 聚合参考 | 伦敦金 XAU 现货价(gold-api 秒级)、新浪 hf_XAU **真实时**(含黄金 T+D gds_AUTD)——盘中金价与事件前后反应 | 实时 | **脚本** `scripts/live_market_fetch.py`(`gold` / `sina` 预设,无需 key) |
| **qveris MCP 市场(金银现货)** `mcp.qveris.ai` | 聚合市场(计费) | **XAU + XAG 同接口现货价**(T.oz,含 bid/ask 代理,OTC 实时源)——**专门补 Twelve Data 免费层 XAGUSD=404 的白银缺口** | 实时 | **脚本** `scripts/qveris_fetch.py spot --symbol XAG\|XAU`(详见第 7.16 节;单次 ~9.55 credits) |

---

## 4. 原油(对应 `oil.md`)

| 数据源 | 权威性 | 关键内容 | 更新频率 | 获取方式 |
|--------|--------|----------|----------|----------|
| **EIA** `eia.gov`(v2 API) | 官方一手 | 周度库存(原油 `WCRSTUS1` / 汽油总 `WGTSTUS1` / 馏分油 `WDISTUS1`,千桶)、WTI `RWTC`/Brent `RBRTE` 现货价(美元/桶) | 周三(库存) | **脚本** `scripts/eia_fetch.py`(key 需自备,可存于 `scripts/.eia_key`);详见第 7.2 节 |
| **IEA** `iea.org` | 国际组织一手 | 月度石油市场报告(MOMR 同类)、全球需求预测、库存 | 月 | 网页 / 报告(**付费 MODS**;免费历史替代 KAPSARC);`scripts/opec_fetch.py` 附指引 |
| **OPEC** `opec.org` | 官方一手 | 月度石油市场报告、产量配额、执行率、闲置产能 | 月 | **脚本** `scripts/opec_fetch.py`(best-effort 直连 + WebFetch 手工指引,详见第 7.8 节);网页/报告 |
| **API**(美国石油协会) | 行业一手 | 周度库存补充(公布早于 EIA) | 周二 | 网页 |
| **期货期限结构**(CME NYMEX / ICE) | 市场基准 | WTI-Brent 价差、Contango/Backwardation | 实时 | 经纪商 / TradingView |

---

## 5. 跨市场联动(对应 `cross_market.md`)

| 数据源 | 权威性 | 关键内容 | 获取方式 |
|--------|--------|----------|----------|
| **TradingView** `tradingview.com` | 市场基准 | 跨市场图表模板、VIX、信用利差(ICE/BofA)、AUD/JPY、USD/CAD、USD/CNH | 网页 / 模板 |
| **用户"全球金融日报"系统** | 自用一手 | 已覆盖 40 品种的 JSON/HTML(`daily_data.json`),可直接作为本技能宏观研判输入源,**避免重复采集** | 读取 `./output/financial-dashboard/daily_data.json` |
| **中国信贷脉冲** | 一手派生 | 社融增量 / GDP(PBOC),领先铜、澳元、人民币 3–6 个月 | PBOC 网页 / CEIC / Wind |

---

## 6. 经济日历(事件时点,对应事件手册)

| 数据源 | 内容 | 获取方式 |
|--------|------|----------|
| **美联储日历** `federalreserve.gov` | FOMC / 官员讲话时点 | 网页 |
| **Trading Economics** `tradingeconomics.com` | 全球宏观事件(非农/CPI/PMI/EIA 等)时点与预期值 | 网页 / API |
| **Investing.com 财经日历** | 多资产事件日历 | 网页 |

> 事件交易铁律:**以官方日历公布的时点为基准,不臆测;预期差比方向更重要。**

---

## 7. 获取方式与工具（含本技能内置脚本）

本技能在 `scripts/` 随包提供十余个**标准库实现、无需 pip 安装**的取数脚本,直接拉取权威源、输出 CSV/文本,供研判与交易计划复用:

### 7.1 BIS 官方统计 API（SDMX v2,无需 key）

- **Base**:`https://stats.bis.org/api/v2`,SDMX RESTful 2.1.0,公开、无需认证。
- **权威价值**:各国央行政策利率、美元汇率、有效汇率、全球流动性——直接补强"宏观利率地基"与"外汇",比二手聚合更一手。
- **常用 dataflow**:`WS_CBPOL`(政策利率)、`WS_XRU`(美元汇率)、`WS_EER`(有效汇率)、`WS_GLI`(全球流动性)。维度顺序须先查(`--dims`)。
- **脚本**:`scripts/bis_fetch.py`

```bash
# 拉美国政策利率最近 12 期
python scripts/bis_fetch.py --dataflow WS_CBPOL --key "M.US.*" --last 12 --out "./output/bis_us_policy_rate.csv"
# 预设快捷:policy_rates / usd_rates / eer / global_liq
python scripts/bis_fetch.py --preset policy_rates --last 24 --out "./output/bis_policy.csv"
python scripts/bis_fetch.py --list          # 列出全部数据集
python scripts/bis_fetch.py --dims WS_XRU   # 查维度顺序
```

### 7.2 EIA v2 API（原油模块,key 需自备）

- **Base**:`https://api.eia.gov/v2`,免费 key 注册 https://www.eia.gov/opendata/。
- **Key 配置**:需自备 key 并写入 `scripts/.eia_key`(本地文件,**不进 zip**、不进脚本源码);读取优先级 `--api-key` > 环境变量 `EIA_API_KEY` > `scripts/.eia_key`。重装/迁移 skill 后需重设(见 SKILL.md 末尾"密钥安全")。
- **权威价值**:周度原油/汽油/馏分油库存、WTI/Brent 现货价——原油模块(模块四)的核心一手源,直接驱动 EIA 周三库存事件交易研判。
- **常用路由/系列(2026-08 实测校准)**:
  - `petroleum/sum/sndw`(周度供需,**强制需要 `frequency=weekly`**):原油库存 `WCRSTUS1`、汽油总库存 `WGTSTUS1`、馏分油库存 `WDISTUS1`(单位均为千桶)。
  - `petroleum/pri/spt/data`(现货价,日度 `frequency=daily`):WTI 库欣 `RWTC`、Brent `RBRTE`(美元/桶)。
  - ⚠️ 系列过滤必须用 `facets[series][]=XXX`(脚本已内置),直接用 `series=` 参数会返回 HTTP 400;`crude_prod`(周度产量)在该路由下无对应 ID,已从预设移除。
- **脚本**:`scripts/eia_fetch.py`(标准库;预设 `crude_stocks/gas_stocks/dist_stocks/wti/brent`;`--last N` 自动按 period 倒序取最近 N 期,规避 EIA 5000 行分页截断)。

```bash
# 美国商业原油库存最近 12 周(需先自备 key,脚本自动读同目录 .eia_key)
python scripts/eia_fetch.py --preset crude_stocks --last 12 --out "./output/eia_crude_stocks.csv"
# 汽油总库存 / 馏分油库存 / WTI / Brent
python scripts/eia_fetch.py --preset gas_stocks --last 12
python scripts/eia_fetch.py --preset dist_stocks --last 12
python scripts/eia_fetch.py --preset wti --last 30
python scripts/eia_fetch.py --preset brent --last 30
# 直接指定路由+系列(sndw 必须带 --freq weekly)
python scripts/eia_fetch.py --route petroleum/sum/sndw --series WCRSTUS1 --freq weekly --last 24 --out "./output/eia_crude.csv"
```

### 7.3 IMF SDMX 3.0 API（宏观 / 外汇）—— ⚠️ 2026-09-28 实测：结构可取，**数据不可供**

- **Base**:`https://api.imf.org/external/sdmx/3.0`(备用节点 `https://sdmxcentral.imf.org/sdmx/v3` 实测 TLS 连接被关闭)。
- **✅ 已修正的正确路径**(旧路径 `/dataflow/IMF`、`/datastructure/IMF/{flow}`、`/Data/{flow}/{key}` 实测**全部 404**,已废弃):
  - 结构清单:`GET /structure/dataflow/all/*/+` → **200**,返回 **222** 个 dataflow(含 agencyID 与 version)。
  - 数据查询:`GET /data/dataflow/{agency}/{flow}/{version}/{key}?format=jsondata`(key 用 `all` 表全维度)。
- **❌ 当前不可供数(实测)**:上述数据端点对 `all`、完整维度键、`dimensionAtObservation=AllDimensions`、
  SDMX-JSON `Accept` 头、`startPeriod/endPeriod` **一律返回"结构信封 + observations = 0"**
  (COFER / BOP / CPI / IRFCL / WEO 全部如此)。`format=csv` 亦被忽略(仍返回 JSON)。
- **❌ 两个旧预设不存在**:`IFS` 与 `DOT` 在 IMF 全部 222 个 dataflow 中**查无此 id**(历史遗留写法,
  已从脚本移除)。现存可用 id 示例:`COFER`(IMF.STA 7.0.1)、`BOP`(IMF.STA 21.0.0)、
  `CPI`(IMF.STA 5.0.0)、`IRFCL`(IMF.STA 12.0.0)、`WEO`(IMF.RES 9.0.0)。
- **脚本**:`scripts/imf_fetch.py`(`--list` 列 dataflow 实测可用;`--structure` 查维度;`--flow/--key` 取数;
  预设 `cofer/bop/cpi/irfcl/weo`)。agency 与 version 由结构清单**实时解析**(IMF 升版无需改码)。
  检测到 0 观测即 **exit 3 并给出替代源**,绝不把空信封当数据落盘。

```bash
# 列 dataflow(实测可用, 用它核对 flow id 与版本)
python scripts/imf_fetch.py --list
# 查 COFER 维度顺序
python scripts/imf_fetch.py --structure COFER
# 取数(当前会 exit 3 并提示"无观测值"; IMF 恢复供数后本命令自动可用)
python scripts/imf_fetch.py --preset cofer --out "./output/imf_cofer.json"
```

> ⚠️ **结论:在 IMF 恢复供数前,不要用它做投资决策依据。** 同一信息改用本技能实测可取数的源:
> `worldbank_fetch.py`(World Bank,免 key,实测 200)、`bis_fetch.py`(BIS SDMX v2,免 key,实测 200,
> 含政策利率/有效汇率/全球流动性)、`fred_fetch.py`(FRED,需自备 key,官方利率与曲线)。

### 7.4 World Bank Open Data API（宏观 / 外汇基本面,无需 key）

- **Base**:`https://api.worldbank.org/v2`,公开、无需认证(本环境实测 HTTP 200 可用)。
- **权威价值**:实际利率 `FR.INR.RINR` 与 CPI 通胀 `FP.CPI.TOTL.ZG` 构成**实际/名义利差**,直接驱动利率平价(IRP)与套息交易;经常账户占 GDP `BN.CAB.XOKA.GD.ZS` 是**中期汇率方向**的经典基本面;GDP 增速 `NY.GDP.MKTP.KD.ZG` 刻画全球/新兴增长 Regime;官方汇率 `PA.NUS.FCRF`、外储 `FI.RES.TOTL.CD`、政府债务 `GC.DOD.TOTL.GD.ZS` 用于 EM 脆弱性与主权/货币风险研判。
- **常用预设**:`real_rate`(实际利率)、`cpi_inflation`(CPI 通胀)、`current_account_pct`(经常账户%GDP)、`gdp_growth`(GDP 增速)、`fx_rate`(官方汇率)、`fx_reserves`(总储备含黄金)、`gov_debt_pct`(政府债务%GDP)。
- **脚本**:`scripts/worldbank_fetch.py`(标准库;`--list-indicators` 搜索指标、`--list-countries` 列国家码、`--preset/--indicator` 取数、`--country` 多国用 `;` 分隔、`--mrnev` 最近 N 个非空值、`--date` 年份区间、`--out` 落 CSV)。

```bash
# 多国实际利率最近 5 期(套息/IRP 利差)
python scripts/worldbank_fetch.py --preset real_rate --country "US;CN;JP;EU" --mrnev 5 --out "./output/wb_realrate.csv"
# 中美经常账户占 GDP(2015–2025,中期汇率方向)
python scripts/worldbank_fetch.py --preset current_account_pct --country "US;CN" --date 2015:2025
# 发现指标 ID / 国家码
python scripts/worldbank_fetch.py --list-indicators "real interest"
python scripts/worldbank_fetch.py --list-countries
```

> ⚠️ 说明:World Bank 商品价格(Pink Sheet,原 `PX.LND.*` 系列)当前已不在该 API 标准路由下提供(返回 Invalid value),故本脚本不纳入商品价预设;原油价请用 `scripts/eia_fetch.py`、金价请用 WGC/LBMA。

### 7.5 QuantGist API v1（事件驱动 / 地缘情报层,需 X-API-Key）

- **Base**:`https://api.quantgist.com/v1`,认证头 `X-API-Key`(格式 `qg_live_xxx`);key 从环境变量 `QUANTGIST_API_KEY` 或 `--api-key` 传入(不写死进脚本)。
- **权威价值**:补 BIS/EIA/IMF/World Bank 只有宏观基本面、缺"事件驱动 + 地缘情报"的短板——经济日历/事件(含 `actual/forecast/surprise_pct`)、宏数据最近值(CPI/NFP/PCE/FOMC 等别名)、**新闻雷达 `news/radar`**(地缘/油价供给/制裁/央行意外/中东风险/OPEC 等主题包,带 `impact_score`、`confidence`、`affected_assets` 如 GLD/XAUUSD/CL/USO)、商品 ETF 快照(GLD/USO 实时价)、情绪/意外/影响力排名。
- **常用预设**:`calendar`(今日日历)、`events`(历史事件)、`macro_latest`(宏最近值)、`news_radar`(地缘情报)、`commodities`(GLD/USO)、`sentiment`/`surprises`/`movers`(Starter+ 套餐限制,可能 402)。
- **脚本**:`scripts/quantgist_fetch.py`(标准库;`--preset` 选端点、`--alias` 宏别名、`--lookback/--min-impact` 雷达参数、`--json` 原始输出、`--out` 落 CSV)。

```bash
# 今日经济日历(含 EIA 原油库存、USD 影响)
python scripts/quantgist_fetch.py --preset calendar --api-key $QUANTGIST_API_KEY
# 地缘/油价情报(最小影响分 0.6,affected_assets 含 GLD/XAUUSD/CL)
python scripts/quantgist_fetch.py --preset news_radar --min-impact 0.6 --api-key $QUANTGIST_API_KEY --out "./output/qg_radar.csv"
# 商品 ETF 快照(金价 GLD / 油价 USO 代理)
python scripts/quantgist_fetch.py --preset commodities --api-key $QUANTGIST_API_KEY
```

> ⚠️ 说明:`sentiment`/`surprises`/`movers` 属 Starter+ 付费层,免费套餐返回 402;脚本已优雅提示"需升级订阅"。`news/radar`、`calendar`、`macro/latest`、`commodities` 等核心端点免费可用(本环境实测 key 有效、HTTP 200)。

### 7.6 实时行情聚合 API（外汇 / 黄金现货实时报价,无需 key）

- **整合源**(均为本环境 2026-08-27 实测可达、免 key、纯标准库):
  - **Frankfurter** `api.frankfurter.dev`(ECB 官方参考汇率,日更,无 key / 限流宽松)——预设 `fx_ref`。
    (2026-09-28 更正:旧域 `api.frankfurter.app` **实测仍可用且返回一致**,并非"301 失效";本技能统一用 `.dev`。)
  - **gold-api.com** `api.gold-api.com`(伦敦金 XAU 现货价,秒级更新,无 key)——预设 `gold`。
  - **US Treasury Fiscal Data** `api.fiscaldata.treasury.gov`——预设 `ust_yield`
    (2026-09-28 口径更正:该预设改用 `v2/accounting/od/avg_interest_rates` = **存量国债平均利率(月度)**;
    旧实现调的是 `v1/rates_of_exchange` = 外币折算**记账汇率**,完全不含收益率,属误标。
    该系列**仍非市场收益率曲线**;10Y/2s10s/TIPS 实际利率请用 `fred_fetch.py`。
    记账汇率改由新预设 `ust_fx` 单独提供)。
  - **exchangerate-api** `open.er-api.com`(150+ 货币,日更,无 key / 1500 req-月)——预设 `fx_all`。
  - **新浪财经** `hq.sinajs.cn`(USDCNY 即期 + 伦敦金 hf_XAU **真实时**,非官方,需 `Referer: finance.sina.com.cn` + GBK 解码)——预设 `sina`。
- **权威价值**:补宏观源(日/月频)缺"盘中实时报价"的短板——外汇即期(USDCNY/USDCNH)、伦敦金现货、美债收益率,直接服务"重点事件发布前后价格反应"监控与盘中决策;无需 key、无成本、本环境直达。
- **常用预设**:`fx_ref`(ECB 参考汇率)、`fx_all`(全货币)、`gold`(伦敦金 XAU)、`ust_yield`(美债/汇率)、`sina`(真实时外汇+黄金)、`all`(一键聚合 5 源)。
- **脚本**:`scripts/live_market_fetch.py`(标准库;`--preset` 选源、`--from/--to` 货币、`--symbol` 金属、`--list` 新浪代码、`--limit` 条数、`--out` 落 CSV、`--json` 原始输出)。

```bash
# ECB 参考汇率(USD→CNY/EUR/JPY)
python scripts/live_market_fetch.py --preset fx_ref --from USD --to CNY,EUR,JPY --out "./output/fx_ref.csv"
# 伦敦金现货价
python scripts/live_market_fetch.py --preset gold
# 新浪真实时(USDCNY + 伦敦金)
python scripts/live_market_fetch.py --preset sina --list "USDCNY,hf_XAU"
# 一键聚合全部 5 源
python scripts/live_market_fetch.py --preset all --json
```

> ⚠️ 说明:新浪为非官方接口,需带 Referer 头(脚本已内置)并以 GBK 解码;加密交易所(Binance/OKX/Bybit/CoinGecko 等)在大陆网络被墙、Yahoo/ECB SDW/BIS 旧端点不可达,均已排除,不纳入本脚本。A股/港股实时(东财/腾讯)、需 key 源(Alpha Vantage/Twelve Data/FRED/Tushare)及偏题大模型清单,仅作本地备查,未脚本化。

### 7.7 K 线历史数据(盘面解读的输入)

**本环境实测结论(2026-08/09 中国大陆网络):多数免费 K 线历史源不可用**,故盘面解读的输入遵循"**双路径、取数铁律**":

- **IMA 知识库(个人沉淀,历史行情参考)**:用户腾讯 IMA 知识库中长期积累的**行情复盘笔记 / 历史数据快照 / 方法论**,可作为历史行情与跨市场研判的**补充参考源**(本环境可经 IMA MCP 连接器读取,亦可在写报告时援引)。凡引用 IMA 中的具体数值,须标注 `[源: IMA 知识库 | 截至:YYYY-MM-DD]`,且不作为唯一权威源——关键结论仍以第 1 节所列官方/国际组织一手源交叉验证为准。

- **路径①(零网络依赖,推荐)**:用户从 MT4 导出 CSV 或粘贴 OHLC 文本,由 `scripts/kline_read.py` 本地确定性计算——与手工交易习惯一致、最可靠。
- **路径②(联网权威抓取,需免费 Key)**:当用户**未发送任何 K 线数据**时,用 `kline_read.py --fetch` 经 **Twelve Data** 联网抓取 15min/1H/4H/1D/1W 五周期——**Twelve Data 是中国大陆可直连、免翻墙的权威 OHLC 历史源**(2026-09 实测 HTTP 200,覆盖外汇/黄金/原油)。

> **取数铁律(与技能整体一致,不可逾越)**:任一周期抓取失败(Key 缺失 / 网络受限 / 品种不支持 / 返回空),**仅报告原因并跳过该周期**;五周期全部失败则明确告知"无法从任何权威渠道获取 K 线数据",并引导改用 `--csv`/`--text`,**严禁自行编造、估算或凭记忆生成任何价格**。

| 源 | 状态 | 说明 |
|---|---|---|
| **MT4 导出 CSV** | ✅ **推荐主输入(路径①)** | 文件→另存为,或"数据窗口"右键导出;脚本自动识别 `Date,Time,O,H,L,C,V` 表头与制表符/逗号分隔 |
| 粘贴 OHLC 文本 | ✅ 支持(路径①) | `--text "date,o,h,l,c"` 多行,临时快速解读 |
| **Twelve Data** `api.twelvedata.com` | ✅ **权威网络源(路径②)** | 中国大陆可直连,免费注册 https://twelvedata.com 取 Key;覆盖外汇/黄金/原油与 15min/1h/4h/1day/1week;经 `kline_fetch.py` 抓取,`kline_read.py --fetch` 逐周期分析 |
| **qveris MCP 市场** `mcp.qveris.ai` | ✅ **权威网络源补充(路径②备选)** | 中国大陆可直连,Bearer token 读 `~/.workbuddy/mcp.json`;外汇日线 `alphavantage.fx_daily`(USDJPY/EURUSD/AUDJPY 等,**1 credit/次,无 Twelve Data 429 限频**)、金银现货 `commodity_price_api.rates.live`(**补 XAGUSD 缺口**);`qveris_fetch.py fx --csv` 输出标准 `Date,Open,High,Low,Close` 直接喂 `kline_read.py`;详见第 7.16 节 |
| 新浪旧接口 `CN_FX_Data` / `CN_MarketDataService` | ❌ 失效 | 接口已下线 |
| 东方财富 `push2his` | ❌ 被墙/超时 | 本环境不可达 |
| Yahoo `query1.finance.yahoo.com` | ❌ HTTP 403 | 需 OAuth,已关闭匿名访问 |
| stooq.com | ❌ JS 挑战页 | 非 API,无法解析 |

**MT4 导出步骤**:图表右键 →「数据窗口」→ 右键 →「导出」→ 存为 `.csv`(默认制表符分隔,脚本兼容)。
若只需最近 N 根,用 `--last N` 控制,默认值 120。

**脚本**:`scripts/kline_read.py`(纯标准库,无需 key) + `scripts/kline_fetch.py`(Twelve Data 抓取,需免费 Key)

```bash
# 路径①:CSV 输入 + 输出 JSON/HTML 标注图
python scripts/kline_read.py --csv "./output/EURUSD_H1.csv" \
    --symbol EURUSD --tf H1 --last 120 --json --html --out "./output"
# 路径①:粘贴文本快速解读
python scripts/kline_read.py --text "2026-08-20,1.0850,1.0890,1.0830,1.0880" --symbol EURUSD --tf D1

# 路径②:未发K线时,联网抓取 15min/1H/4H/1D/1W 并逐周期分析(Twelve Data 权威源)
python scripts/kline_read.py --fetch --symbol USDJPY --api-key <TWELVEDATA_KEY>
python scripts/kline_read.py --fetch --symbol XAUUSD --api-key <TWELVEDATA_KEY> --json --out "./output"
# 单源单周期抓取(可输出 CSV)
python scripts/kline_fetch.py --symbol USOIL --interval 1h --api-key <TWELVEDATA_KEY> --out "./output/usoil_1h.csv"
```

> **无 Key 降级提示**:若未配置 Twelve Data Key(环境变量 `TWELVEDATA_API_KEY` 或 `--api-key`),`--fetch` 会明确提示"未配置 Key,无法联网获取 K 线",并给出 --csv / --text 替代方案,**绝不编造价格**。Key 由用户自行在 twelvedata.com 免费注册,**不硬编码进脚本与 zip**。

---

### 7.8 CFTC COT/TFF、WGC/LBMA、OPEC、FedWatch 取数脚本

本组脚本覆盖此前"仅网页/手工"的四类数据,现均提供脚本化入口(可行性分三档,取数铁律一致:**失败即报错/降级,绝不杜撰**):

#### 7.8.1 CFTC COT / TFF 持仓拥挤度（`scripts/cftc_fetch.py`，✅ 免费·无需 key·中国可直连）

- **源**:CFTC 官方年度历史文件——分类持仓 `fut_disagg_txt_YYYY.zip`(商品:黄金/白银/铜/WTI/天然气,投机代理 = **Managed Money**)、金融 TFF `fut_fin_txt_YYYY.zip`(外汇 EUR/USD·JPY·AUD 等/利率/股指,投机代理 = **Leveraged Funds**)。
- **URL 模式**:`https://www.cftc.gov/files/dea/history/{fut_disagg_txt|fut_fin_txt}_YYYY.zip`(2026-09 实测 HTTP 200、中国环境可达;Socrata API 在部分网络被拦截,故用官方静态文件兜底)。
- **输出指标**:投机净头寸 `Net = Long − Short`、净头寸/OI、多空比 L/S、52 周历史分位(→ 拥挤度等级:极度做多≥90% / 偏拥挤做空≤25% / 中性)、周环比 ΔNet / Δ净头寸-OI。
- **品种别名**:`GOLD / XAU / SILVER / COPPER / WTI / CL / NATGAS / PLATINUM / PALLADIUM / EURUSD / JPYUSD / GBPUSD / AUDUSD / CADUSD / CHFUSD / NZDUSD / MXNUSD / US10Y / SP500 / NASDAQ / DJIA` 等(`--list` 列全)。
- **缓存**:`scripts/.cftc_cache`(默认 3 天,自动叠加前一年扩充历史分位);`--from-file` 支持离线解析预下载的 `f_year.txt` / `FinFutYY.txt`。

```bash
python scripts/cftc_fetch.py --symbol GOLD --weeks 52      # 黄金投机净头寸 + 52周拥挤度分位
python scripts/cftc_fetch.py --symbol EURUSD               # 欧元(杠杆基金净头寸)
python scripts/cftc_fetch.py --symbol AUDUSD --json        # 澳元(交易 AUDJPY 联动)
python scripts/cftc_fetch.py --symbol WTI --weeks 26
python scripts/cftc_fetch.py --market-code 067651 --report disagg   # WTI 合约代码直查
python scripts/cftc_fetch.py --from-file f_year.txt --market-code 088691 --report disagg  # 离线
```

> **研判用法**:净头寸/OI 处于 52 周 ≥90% 分位 = 投机极度做多(拥挤,警惕反转/轧空风险);≤10% = 极度做空(警惕空头回补轧空);中性区间跟随趋势。周环比 ΔNet 急剧放大常预示情绪极值点。

#### 7.8.2 WGC / LBMA 黄金取数（`scripts/wgc_lbma_fetch.py`，✅ LBMA 现货代理免费·WGC 供需需手工）

- **LBMA 金价代理(脚本可直连,免费,无需 key)**:`https://api.gold-api.com/price/XAU`(国际现货金,美元/盎司,紧贴 LBMA 定盘;2026-09 实测 HTTP 200)。`--symbol XAU|XAG` 取金/银。
- **WGC 供需 / 央行购金 / LBMA 官方定盘**:gold.org / lbma.org.uk 无免费 JSON API(仅有图表/HTML/xlsx),故 `--manual` 输出标准化 WebFetch 手工取数指引(提取:全球/央行/ETF 季度需求吨数、LBMA Gold Price AM/PM),**绝不杜撰数字**。

```bash
python scripts/wgc_lbma_fetch.py --symbol XAU     # LBMA 金价现货代理(免费)
python scripts/wgc_lbma_fetch.py --manual        # WGC/LBMA 手工取数指引(不联网)
```

#### 7.8.3 OPEC MOMR 原油报告（`scripts/opec_fetch.py`，⚠️ best-effort + 手工指引）

- **可行性**:OPEC 官网(`opec.org`)MOMR 以 HTML/PDF 发布,**无免费 JSON API**;IEA MODS 为付费(€9200+)。本脚本"尽力而为"直连 OPEC 公开页抽取供需关键词,失败(网络/地域封锁,如本开发环境 `opec.org` 返回 403)则输出标准化 WebFetch 手工取数指引。
- **重点提取字段**:全球石油需求增长预测(万桶/日,YoY)、非 OPEC 供应增长、OPEC 原油产量 / 减产履约、OPEC 一揽子油价(ORB)。IEA 免费历史替代:KAPSARC IEA 石油市场数据集(2001–2016)。

```bash
python scripts/opec_fetch.py            # 尝试直连 + 输出指引
python scripts/opec_fetch.py --manual    # 仅打印手工取数指引(不联网)
```

#### 7.8.4 CME FedWatch 降息/加息概率（`scripts/fedwatch_csv.py`，⚠️ 无免费 API·手动导出桥接）

- **可行性**:CME FedWatch Tool **没有免费脚本化 API**(需付费订阅 + OAuth),无法直连抓取。本脚本解析用户从 FedWatch Tool 网页**手动导出**的 CSV,把"会议日期 × 目标利率"概率矩阵转结构化文本/JSON(降息≥25bp / 按兵不动 / 加息≥25bp)。
- **手动导出步骤**:打开 FedWatch Tool → 在概率表点击目标 FOMC 会议 → "Download / Export" 存 CSV → `python scripts/fedwatch_csv.py --csv <文件>`。

```bash
python scripts/fedwatch_csv.py --csv "./output/fedwatch_2026-09-03.csv"
python scripts/fedwatch_csv.py --csv fedwatch.csv --json   # 机器可读
```

> 若持有 CME 付费 DataMine/FedWatch API 订阅,可改用官方接口直连;本脚本仅覆盖"免费手动导出"这一最可达路径。

### 7.9 其他取数方式

- **FRED API**:`fred.stlouisfed.org/docs/api/fred`,免费注册 key;**已脚本化**——用 `scripts/fred_fetch.py` 拉取 `DGS10`/`DFII10`/`T10YIE`/`T10Y2Y` 等宏观利率系列(详见第 7.10 节),key 需自备,可存于 `scripts/.fred_key`。
- **WebFetch**:本环境可直接对官方/聚合页面做结构化抓取(用于无 API 的源,如 WGC、OPEC 报告要点)。
- **用户日报系统**:读取 `./output/financial-dashboard/daily_data.json`,作为滚动相关性分析的本地数据源。
- **Python / Excel**:对取回数据自动更新 20/60 日滚动相关性(见 `scripts/exposure.py` 与 `cross_market.md`)。

### 7.10 FRED API（宏观 / 利率地基,key 需自备）

- **Base**:`https://api.stlouisfed.org/fred`(FRED API v1,公开、需免费 key)。
- **权威价值**:美元/利率方向研判的第一手权威源——10Y 名义利率 `DGS10`、10Y 实际利率(TIPS) `DFII10`(黄金定价第一锚)、10Y 盈亏平衡通胀 `T10YIE`、2s10s 利差 `T10Y2Y`(收益率曲线倒挂/衰退领先信号)、短端 `DGS3MO`/`DGS1`/`DGS2`/`DGS5`、长端 `DGS30`、联邦基金利率 `FEDFUNDS`/`DFF`——直接驱动"宏观利率地基"与外汇/黄金/原油的利率维度。
- **Key 配置**:需自备 key 并写入 `scripts/.fred_key`(本地文件,不进 zip、不进源码);读取优先级 `--api-key` > 环境变量 `FRED_API_KEY` > `scripts/.fred_key`。免费注册 https://fredaccount.stlouisfed.org/apikeys。
- **预设(preset)↔ 系列**:

  | preset | 系列 | 用途 |
  |---|---|---|
  | `nominal_10y` | `DGS10` | 10Y 名义利率 |
  | `real_10y` | `DFII10` | 10Y 实际利率(黄金第一锚) |
  | `breakeven_10y` | `T10YIE` | 10Y 盈亏平衡通胀 |
  | `curve_2s10s` | `T10Y2Y` | 2s10s 利差(倒挂信号) |
  | `short_end` | `DGS3MO`/`DGS1`/`DGS2`/`DGS5` | 短端收益率曲线 |
  | `fed_funds` | `FEDFUNDS`/`DFF` | 政策利率锚 |
  | `all_rates` | 上述全部 | 全曲线 + 实际/通胀/政策(默认推荐) |

- **脚本**:`scripts/fred_fetch.py`(纯标准库);`--preset` 选预设、`--series` 自定义(逗号分隔)、`--last N` 最近 N 个观测、`--start/--end` 区间、`--out` 落盘(`.csv` 宽表 / `.json`);缺失值以 `.` 表示自动跳过;401=Key 无效、400/404=系列不存在、429=限速,均优雅降级。

```bash
# 全曲线 + 实际/通胀/政策利率(最近 30 期)
python scripts/fred_fetch.py --preset all_rates --last 30 --out "./output/fred_rates.csv"
# 黄金定价锚:名义/实际/盈亏平衡通胀(最近 60 期)
python scripts/fred_fetch.py --series DGS10,DFII10,T10YIE --last 60
```

### 7.11 金十数据 Jin10 MCP（实时行情 / 快讯 / 资讯 / 财经日历）

- **定位**:中国大陆可直连的金融实时数据服务,覆盖**实时行情、K线、快讯、深度资讯、财经日历**——事件前中后监控市场反应的极佳源。通过标准 MCP(Mode士 Context Protocol)提供,客户端 `scripts/jin10_mcp.py`(纯标准库)或 WorkBuddy MCP 连接器均可调用。
- **MCP 配置要点**(用户级 `~/.workbuddy/mcp.json`,Bearer Token 访问,**不进 zip**):
  ```json
  {
    "mcpServers": {
      "jin10": {
        "serverUrl": "https://mcp.jin10.com/mcp",
        "headers": { "Content-Type": "application/json", "Authorization": "Bearer <你的Token>" }
      }
    }
  }
  ```
  Token 亦可存于 `scripts/.jin10_key`(脚本用,单行纯文本,不进 zip);读取优先级 `--token` > 环境变量 `JIN10_TOKEN` > `scripts/.jin10_key`。配置后需在连接器面板 **Trust** 该 server 才会加载。
- **标准 MCP 流程**:`initialize` → `notifications/initialized` → `tools/list` / `resources/list` → `tools/call`(推荐协议版本 `2025-11-25`)。结果读取**优先 `result.structuredContent`**;`result.content` 仅作可读文本补充,不作主要机器解析来源。
- **已验证工具**:
  | 工具 | 参数 | 说明 |
  |---|---|---|
  | `get_quote` | `{ code }` | 指定品种实时行情 |
  | `get_kline` | `{ code, time?, count? }` | 指定品种 K 线 |
  | `list_flash` | `{ cursor? }` | 最新快讯列表 |
  | `search_flash` | `{ keyword }` | 按关键词搜索快讯 |
  | `list_news` | `{ cursor? }` | 最新资讯列表 |
  | `search_news` | `{ keyword, cursor? }` | 按关键词搜索资讯 |
  | `get_news` | `{ id }` | 单篇资讯详情 |
  | `list_calendar` | `{}` | 财经日历数据 |
  - **资源**:`quote://codes` —— 支持的报价品种代码列表(调用任何报价前先读它确认 `code`)。
- **数据读取约定**:
  - 报价 `get_quote`:`data.code / name / time / open / close / high / low / volume / ups_price / ups_percent`
  - K线 `get_kline`:`data.code / name / klines[]`(每项 `close/high/low/open/time/volume`)
  - 快讯/资讯列表:`data.items / data.next_cursor / data.has_more`
  - 文章详情 `get_news`:`data.id / title / introduction / time / url / content`
  - 财经日历 `list_calendar`:`data[]`(每项 `pub_time / star / title / previous / consensus / actual / revised / affect_txt`)
- **推荐调用流程**:
  - "某品种报价 / 最近 K线" → 先 `quote://codes` 确认 `code`,再 `get_quote` / `get_kline`
  - "某主题最新快讯" → `search_flash({ keyword })`;顺序浏览最新流 → `list_flash({})` 后按 `next_cursor` 翻页
  - "某主题深度文章" → `search_news({ keyword })` 或 `list_news({})`,拿到 `id` 后 `get_news({ id })`
  - "财经日历 / 本周数据" → 直接 `list_calendar({})`
- **常用品种代码**:`XAUUSD`(现货黄金)、`XAGUSD`(现货白银)、`USOIL`(WTI 原油)、`UKOIL`(布伦特原油)、`COPPER`(现货铜)、`USDJPY`、`EURUSD`、`USDCNH`。
- **关键词示例**:黄金、原油、美联储、日元、通胀、非农、日本央行、欧佩克。
- **分页**:列表统一请求 `cursor`,响应 `data.next_cursor` / `data.has_more`;**不要传 `offset`**(未声明参数)。
- **调用限制**:每个用户每工具每日最多 1500 次(北京时间自然日,次日重置);超额返回「今日该工具调用次数已达上限,请明日再试」。
- **错误处理**:`isError=true` 按业务错误处理;`JSON-RPC error` 按协议错误处理;不传未声明参数。
- **脚本用法**(`scripts/jin10_mcp.py`,实测可用):
  ```bash
  python scripts/jin10_mcp.py quote XAUUSD                # 现货黄金实时报价
  python scripts/jin10_mcp.py kline XAUUSD --count 20     # 黄金K线
  python scripts/jin10_mcp.py flash --all                 # 最新快讯(全量翻页)
  python scripts/jin10_mcp.py flash-search 美联储         # 美联储主题快讯
  python scripts/jin10_mcp.py calendar                    # 财经日历
  python scripts/jin10_mcp.py news-search 原油 --all      # 原油深度资讯
  python scripts/jin10_mcp.py codes                       # 列出可用品种代码(资源 quote://codes)
  ```

### 7.12 iTick API —— ❌ 已移除（v2.4.6 删除脚本；本节保留仅作历史说明）

- **状态**:`scripts/itick_fetch.py` **已于 v2.4.6 删除**(免费 key 过期),仓库内**不存在该脚本**。
  2026-09-28 审计确认:本文档此前仍把 iTick 当作可用源并给出命令,属**指向已删除脚本的失效文档**,现已更正。
- **不要执行以下任何命令**(脚本缺失,必然失败):
  ~~`python scripts/itick_fetch.py quote --asset forex --code XAUUSD`~~
  ~~`python scripts/itick_fetch.py quote --asset future --region US --code GC2506`~~
- **替代方案**:
  - 外汇/贵金属实时报价 → `scripts/live_market_fetch.py`(`--preset sina` 真实时 / `gold` / `fx_ref` / `fx_all`)。
  - 历史 K 线 → `scripts/kline_fetch.py`(Twelve Data,需自备 key)。
  - **期货报价/期现结构**:当前**无免费实时期货源**,请用 `scripts/futures_analysis.py basis --fut <合约:价:到期天数>`
    **手工传入**近月合约价(现货端可取 goldprice.dev / gold-api);跨品种价差用 `spread` 子命令或 `pull --kind oil`。

> ⚠️ 限频说明:免费套餐 **5 次/分钟**;连续抓取会撞 429,脚本会自动提示并建议间隔 ~13s 重试。批量演示请控制频率。

### 7.13 goldprice.dev（现货金价,免费为主）

- **Base**:`https://api.goldprice.dev`,端点 `/v1/prices?symbol=XAU-USD-SPOT`(亦支持 `/v1/spot/XAU-USD-SPOT`)。
- **认证**:免费层**无需 key**;Free key 层用 `x-api-key: <key>`。key 存于 `scripts/.goldprice_key`(不进 zip);读取优先级 `--api-key` > 环境变量 `GOLDPRICE_API_KEY` > `scripts/.goldprice_key`。
- **权威价值**:直接给**国际现货金价 XAU-USD-SPOT**(美元/盎司),作为期现结构分析的"现货锚"(与 LBMA 代理 / qveris 交叉验证)。
- **返回**:`{"XAU-USD-SPOT":{"price":...,"currency":"USD","unit":"troy_ounce",...}}`。
- **脚本**:`scripts/goldprice_fetch.py`(纯标准库;返回现货价,或识别 Cloudflare 拦截返回 `cloudflare_block` 优雅降级)。

```bash
python scripts/goldprice_fetch.py            # 取现货金价(XAU-USD-SPOT)
python scripts/goldprice_fetch.py --api-key $GOLDPRICE_API_KEY
```

> ⚠️ **Cloudflare 限制(仅部分环境)**:`api.goldprice.dev` 启用 Cloudflare "browser signature" 校验,**本构建沙箱出口被 Cloudflare 错误 1010 拦截(仅 TLS 指纹层面,非代码或 key 错误)**;在用户本机(常规浏览器网络)可正常返回。**切勿据此判 key 失效**——脚本识别 1010 后会输出 `cloudflare_block`(exit 0)并附透明说明,绝不杜撰价格。

### 7.14 OilPriceAPI（WTI / Brent 原油 实时与历史,需 Token）

- **Base**:`https://api.oilpriceapi.com`,**实际路径为 `/v1/`(非 `/v3/`)**。
  - 实时(单一/多个):`GET /v1/prices/latest?by_code=WTI_USD`(逗号分隔可同时取多品种)
  - 全部:`GET /v1/prices/all`
  - 历史(近一年日度):`GET /v1/prices/past_year?commodity=WTI_USD&interval=daily&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- **认证**:请求头 `Authorization: Token <key>`(注意是 `Token`,不是 `Bearer`)。key 存于 `scripts/.oilprice_key`(不进 zip);读取优先级 `--api-key` > 环境变量 `OILPRICE_API_KEY` > `scripts/.oilprice_key`。
- **代码 by_code**(snake_case):`WTI_USD` / `BRENT_CRUDE_USD` / `NATURAL_GAS_USD`。
- **权威价值**:WTI / Brent 原油**实时与历史价**——直接服务原油模块(模块四)的 EIA 之外的第二价格源,且**原生给 WTI-Brent 价差**输入,是期货分析(跨品种价差 / 期限结构)的核心原油源。
- **返回**:`{"status":"success","data":{"price":91.97,"currency":"USD","code":"WTI_USD","created_at":"...","unit":"barrel",...}}`(脚本 `_norm_row` 兼容 `price`/`value`)。
- **脚本**:`scripts/oilprice_fetch.py`(纯标准库;`--code` 可多次/逗号分隔、`--history/--start/--end`、`--all`)。

```bash
# WTI 与 Brent 实时价
python scripts/oilprice_fetch.py --code WTI_USD --code BRENT_CRUDE_USD
# 全部品种
python scripts/oilprice_fetch.py --all
# WTI 历史近一年日度
python scripts/oilprice_fetch.py --history --code WTI_USD --start 2026-01-01 --end 2026-09-01
```

> ⚠️ 注意路径与认证:早期文档曾误写 `/v3/` + `byCode`,经官方 Python SDK 源码核实实为 `/v1/` + `by_code` + `Authorization: Token`。脚本已按正路径实现(本环境实测 WTI≈92/Brent≈96 成功返回)。

### 7.15 期货分析（期现结构 / 基差 / 期货价差 / 跨期 / 跨品种 WTI-Brent）

把"期现结构分析"与"期货价差分析"固化成确定性计算,衔接原油模块(四)与黄金专项(三),服务于:Contango/Backwardation 研判、库存与远期曲线信号、WTI-Brent 跨品种价差 z-score(均值回归/裂解价差逻辑)、跨期价差(近月−远月)的展期信号。方法学与公式见 **`references/futures_analysis.md`**;计算由 **`scripts/futures_analysis.py`**(纯标准库)执行。

- **期现结构 / 基差(basis)**:`basis = spot − futures`;基差率 `= basis / spot × 100%`;年化 carry `= (futures − spot)/spot × 365/days × 100%`;多档期货可算**相邻斜率(年化)**与整体 contango/backwardation 判定。
- **期货价差**:
  - 跨期(calendar):`spread = 近月 − 远月`(正值=back/contango 反向结构信号,负值=contango);
  - 跨品种(如 WTI−Brent):可喂入历史序列 CSV 算 **z-score**(偏离均值几个标准差),辅助均值回归研判。
- **一键拉取(pull)**:`pull --kind oil` 自动经 OilPriceAPI 算 WTI−Brent 价差;`pull --kind gold` 取 goldprice.dev / gold-api 现货算期现结构——**期货端已无免费源(iTick 已于 v2.4.6 移除)**,需用 `basis --fut <合约:价:到期天数>` 手工传入近月合约价(任一源缺失时返回 `_error:"partial"` 优雅降级,绝不杜撰)。
- **脚本**:`scripts/futures_analysis.py`(子命令 `basis` / `spread` / `pull`)。

```bash
# 期现结构:现货 2400,两档期货(标签:价格:天数)
python scripts/futures_analysis.py basis --spot 2400 --fut 2405:2410:30 --fut 2408:2425:120
# 期货价差:跨品种 WTI-Brent
python scripts/futures_analysis.py spread --a WTI:91.97 --b BRENT:95.98
# 跨期(近月-远月)
python scripts/futures_analysis.py spread --near 80 --far 85
# 跨品种喂历史序列算 z-score(CSV: label,value)
python scripts/futures_analysis.py spread --a WTI:91.97 --b BRENT:95.98 --series ./output/wti_brent_series.csv
# 一键拉取(自动取数)
python scripts/futures_analysis.py pull --kind oil
python scripts/futures_analysis.py pull --kind gold
```

> ⚠️ 研判纪律:基差/价差仅供**结构信号**,须与库存(EIA)、持仓(CFTC)、利率(实际利率→carry 成本)三维印证;单看曲线结构不构成方向结论。2026-09-28 实测:goldprice.dev / gold-api 在本机均可直连(`pull --kind gold` 的现货锚正常);若某源缺失,脚本返回 partial,请手工传入。

### 7.16 qveris MCP 金融数据市场(金银/外汇/宏观,按调用计费)

- **定位**:qveris 是金融数据**工具市场(MCP 网关)**,本身不是数据源,而是把 Alpha Vantage / EODHD / CommodityPriceAPI / FRED 等第三方权威源聚合成可经 MCP 调用的工具。中国大陆可直连(`https://mcp.qveris.ai/mcp`),Bearer Token 鉴权。
- **价值(对本技能)**:① **填补白银缺口**——Twelve Data 免费层 `XAGUSD=404`,qveris `commodity_price_api.rates.live` 直接给 XAU+XAG 现货价;② **规避限频**——Twelve Data 免费层 ~8 次/分撞 429,qveris 外汇日线 `alphavantage.fx_daily` 单次仅 1 credit、无分钟级限频;③ **多源冗余**——FRED / 央行利率等可作为既有脚本的交叉验证源。
- **计费**:按 `call` 计费,成本随工具而异(2026-09 实测:金银现货 `commodity_price_api.rates.live` ≈ **9.55 credits/次**、外汇日线 `alphavantage.fx_daily` ≈ **1 credit/次**、外汇实时 `eodhd` ≈ 2.81 credits/次)。账户初始额度 **1000 credits**;用尽前用 `qveris_fetch.py credits` 查余量。免费动作:`discover` / `inspect` / `probe` 不计费。
- **MCP 配置**(用户级 `~/.workbuddy/mcp.json`,**不进 zip**):
  ```json
  {
    "mcpServers": {
      "qveris": {
        "type": "http",
        "url": "https://mcp.qveris.ai/mcp",
        "headers": { "Authorization": "Bearer <你的Token>" }
      }
    }
  }
  ```
  Token 亦可存于 `scripts/.qveris_key`(单行纯文本,不进 zip);`qveris_fetch.py` 读取优先级:`--api-key` > 环境变量 `QVERIS_API_KEY` > `scripts/.qveris_key` > `~/.workbuddy/mcp.json`(自动解析 qveris 的 Authorization)。**切勿明文外泄 Token**。
- **调用契约(关键,与 Jin10 不同)**:
  - 标准流程:`initialize` → `notifications/initialized` → **`discover`(自然语言找工具)** → `inspect`(参数/计费) → `probe`(**免費报价**) → **`call`(计费执行)**。
  - `call` 必须带三件套:`tool_id` + `search_id` + `params_to_tool`(真实参数包,路径参数如 `symbol` 放其内)。
  - ⚠️ **`search_id` 在 `discover` 结果的顶层**(非工具层级);`call` 的 `search_id` 必须来自同一次 `discover`。
  - qveris 大结果会被截断:`result.data`(小)或 `result.truncated_content`(JSON 字符串)或 `result.full_content_file_url`(完整文件);`qveris_fetch.py` 已统一处理。
- **已验证工具(tool_id 可能随版本微调,脚本优先 discover 动态获取)**:
  | 用途 | tool_id(2026-09 实测) | 关键参数 | 成本 |
  |---|---|---|---|
  | 金银现货 | `commodity_price_api.rates.live.retrieve.v2.46f86b4e` | `symbol=xau\|xag` | ~9.55 |
  | 外汇日线 | `alphavantage.fx_daily.retrieve.v1.7aca3c4a` | `function=FX_DAILY`,`from_symbol`,`to_symbol`,`outputsize=compact\|full` | ~1 |
  | 外汇实时 | `eodhd.live_data.real_time.retrieve.v1.b60a4285` | `symbol=USDJPY.FOREX` | ~2.81 |
  | FRED 宏观 | `stlouisfed_fred.*`(discover 按系列取) | `series_id` 等 | 视工具 |
- **脚本**:`scripts/qveris_fetch.py`(纯标准库,无需 pip);高层命令 `spot` / `fx` / `fred`,底层 `discover` / `inspect` / `probe` / `call` / `credits` / `tools`。

```bash
# 金银现货(补白银缺口):XAG / XAU
python scripts/qveris_fetch.py spot --symbol XAG
python scripts/qveris_fetch.py spot --symbol XAU
# 外汇日线 -> 直接产 CSV 喂 kline_read.py(AUDJPY/USDJPY/EURUSD)
python scripts/qveris_fetch.py fx --symbol AUDJPY --kind daily --last 120 --csv "./output/AUDJPY_qveris.csv"
python scripts/qveris_fetch.py fx --symbol USDJPY --kind daily --last 20
# 外汇实时报价
python scripts/qveris_fetch.py fx --symbol EURUSD --kind live
# 自然语言找工具 + 查余量
python scripts/qveris_fetch.py discover --query "gold silver spot price XAU XAG"
python scripts/qveris_fetch.py credits
```

> ⚠️ **取数铁律(与本技能一致)**:任一 `call` 失败/超时/返回空,脚本仅报告原因并跳过该品种,**绝不编造、估算或凭记忆生成任何价格**。qveris 按调用计费,批量扫描前先用 `credits` 确认余量;不建议对全部品种无差别高频 `call`(可与免费源 live_market_fetch.py / Twelve Data 分层搭配)。

### 7.17 Frankfurter 免费外汇参考汇率(独立脚本,无需 key)

- **Base**:`https://api.frankfurter.dev/v1`(2026-09-28 更正:旧域 `api.frankfurter.app` **实测 200 且数据一致**,此前"已 301 失效"的说法不成立;本技能为一致性统一使用 `.dev`)。
- **数据源**:由**欧洲央行(ECB)官方每日参考汇率**驱动的开源公共 API——**无认证、无 key、无明确请求上限**(仅基础防滥用)。
- **数据性质**:**ECB 每日参考汇率,仅工作日更新**(非实时 tick);**仅含法币,不含 XAU 黄金 / XAG 白银**(贵金属请用 goldprice.dev / WGC-LBMA / qveris)。
- **与 AllRatesToday 互补**:Frankfurter = **日参考**(权威、工作日、免 key);AllRatesToday(§7.18)= **实时中间价**(约 60 秒刷新、需 key)。二者叠加覆盖"日级研判 + 盘中监控"。
- **端点**:
  - `GET /v1/latest?base=USD&symbols=EUR,GBP,JPY` → 最近一个工作日
  - `GET /v1/2026-01-02?base=USD&symbols=EUR,GBP` → 指定单日(周末/节假日 404)
  - `GET /v1/2025-12-29..2026-01-05?base=USD&symbols=EUR,GBP` → 时间序列区间(`rates` 按日期嵌套)
  - `GET /v1/currencies` → 货币代码→名称(共 30 种)
- **脚本**:`scripts/frankfurter_fetch.py`(纯标准库;`--base/--symbols/--amount`、`--date` 历史单日、`--from/--to` 时间序列、`--currencies` 货币列表、`--out` 落 CSV/JSON、`--json` 原始响应;未指定 `--symbols` 默认 FX 常用 8 币种 EUR,GBP,JPY,AUD,CNY,CHF,CAD,NZD)。

```bash
# 最新 ECB 参考汇率(USD 基准,多目标)
python scripts/frankfurter_fetch.py --base USD --symbols EUR,JPY,AUD,CNY
# 历史单日
python scripts/frankfurter_fetch.py --base USD --symbols EUR --date 2026-01-02
# 时间序列区间(落 CSV)
python scripts/frankfurter_fetch.py --base USD --symbols JPY,AUD --from 2026-08-01 --to 2026-09-01 --out "./output/ecb_series.csv"
# 货币列表
python scripts/frankfurter_fetch.py --currencies
```

### 7.18 AllRatesToday 实时外汇中间价(独立脚本,需 Bearer Token)

- **Base**:`https://allratestoday.com/api`
- **数据源**:AllRatesToday 实时银行间 **mid-market 中间价** API,覆盖 **160+ 法币**,约 **每 60 秒刷新**(非 ECB 官方参考汇率,亦非逐笔 tick);**仅含法币,不含 XAU/XAG**。
- **认证**:`Authorization: Bearer <Token>`(免费档即 160+ 货币)。Token 存于 `scripts/.art_key`(单行纯文本,不进 zip);读取优先级 `--api-key` > 环境变量 `ART_KEY` > `scripts/.art_key`。**切勿明文外泄 Token**,疑泄露即到 allratestoday.com 后台吊销换新。
- **端点**:
  - `GET /api/v1/rates?source=USD&target=EUR` → 最新一对(响应 `[{"rate","source","target","time"}]`)
  - `GET /api/v1/rates?source=USD&target=EUR&time=YYYY-MM-DD` → 历史单日
  - `GET /api/historical-rates?source=USD&target=EUR&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` → 时间序列(响应 `{"source","target","data":[{"date","rate","timestamp"}...]}`)
- **脚本**:`scripts/allratestoday_fetch.py`(纯标准库;`--source/--target`(可逗号多对)/`--time` 历史单日、`--history --start/--end` 时间序列、`--api-key/ART_KEY/.art_key` 取 Token、`--out` 落 CSV/JSON、`--json` 原始响应)。

```bash
# 实时中间价(一次多对)
python scripts/allratestoday_fetch.py --source USD --target JPY,AUD,EUR
# 历史单日
python scripts/allratestoday_fetch.py --source USD --target EUR --time 2026-09-12
# 时间序列(落 CSV)
python scripts/allratestoday_fetch.py --source USD --target JPY --history --start 2026-09-08 --end 2026-09-12 --out "./output/art_series.csv"
```

> ⚠️ 说明:AllRatesToday 为商业实时汇率服务(免费档 160+ 货币),适合事件前后盘中汇率反应监控;其报价为银行间中间价,与 ECB 参考汇率(Frankfurter)、经纪商点差报价存在口径差异,用于方向研判时须标注 `[源: AllRatesToday | 截至:YYYY-MM-DD HH:MM]`。

### 7.19 华尔街见闻 WSCN MCP（全球资讯深度摘要 / 异动归因）

- **定位**:华尔街见闻官方 MCP 服务(服务端 `xgbmcp-market-data`),提供**全球财经资讯的深度摘要与因果归因**,以及 A 股大涨股异动逻辑。
  **与金十(§7.11)的分工**:金十 = 实时快闪/报价/财经日历(高频速报);见闻 = 中低频深度摘要 + 事件因果链 + 异动归因。**见闻作为金十之外的第二资讯源,用于事件结论的交叉验证,不替代金十**。
- **端点**:`https://xgb-mcp-api.xuangubao.cn/mcp`(streamable-http,中国大陆可直连)
- **认证**:`Authorization: Bearer <key>` **且必须同时带请求头 `X-WMCP-Client: wbwscn`** —— 两者缺一即被拒绝。Token 存于 `scripts/.wscn_key`(单行纯文本);读取优先级 `--api-key` > 环境变量 `WSCN_API_KEY` > `scripts/.wscn_key`。**切勿明文外泄 Token**,疑泄露即到华尔街见闻后台吊销换新。
- **三个只读工具**(2026-09-17 实测):
  | 工具 | 用途 | 关键参数 |
  |---|---|---|
  | `get_wscn_global_articles` | 全球资讯列表(**不含正文**,含 title + summary + id) | `date`(YYYY-MM-DD,默认当天) |
  | `get_wscn_global_article_detail` | 单篇正文(HTML) | `date` + `id`(**两者均必填**) |
  | `get_large_stocks` | A 股异动板块 + 个股 + 上涨原因 | `date`(默认当天) |
- **限制**:仅可查询**近两个月**数据;日期为北京时间。
- **脚本**:`scripts/wscn_fetch.py`(纯标准库,无需 pip)。

```bash
# 连通性与工具清单自检
python scripts/wscn_fetch.py probe
# 【推荐】按交易事件相关度排序的资讯(内置央行/汇率/贵金属/原油/通胀/风险 六类关键词打分)
python scripts/wscn_fetch.py relevant --date 2026-09-17 --top 15
# 全量资讯列表(落 JSON)
python scripts/wscn_fetch.py articles --date 2026-09-17 --out "./output/wscn_0917.json"
# 单篇正文(先取列表中的 date + id)
python scripts/wscn_fetch.py detail --date 2026-09-17 3781913
# A 股异动归因
python scripts/wscn_fetch.py stocks --date 2026-09-17
```

- **`relevant` 子命令的排序逻辑**:对本技能交易场景关键的六组关键词打分(央行/货币政策、汇率/美元、贵金属、原油/能源/地缘、通胀/就业/宏观、关税/衰退/避险),命中越多越靠前,同分按 `displayTime` 倒序。输出每条附带 `_score`(命中数)与 `_hits`(命中词列表),便于快速定位事件驱动线索。关键词表在脚本 `KEYWORDS` 常量,可随研究方向增补。
- **用于报告的场景**:
  1. **宏观大事节**——与金十日历交叉验证,补「事件的市场解读与因果链」(见闻擅长,金十偏速报)。
  2. **地缘风险卡**——原油供应冲击、海峡通行风险、制裁类事件的影响传导链。
  3. **跨市场联动**——见闻摘要常直接给出「美联储加息 → 美元拉升 → 黄金跳水 → 美债收益率反弹」的联动表述,可作跨市场结论的外部佐证。
  4. **事件预期差**——同一事件的多家机构解读汇总,识别市场共识与分歧点。
- **溯源格式**:`[源: 华尔街见闻 | 截至:YYYY-MM-DD HH:MM]`;与金十并用时分别标注,出现分歧按 §8 第 4 条记为「预期差」而非取其一。

> ⚠️ **取数铁律(与前文一致)**:任一调用失败/超时/返回空,脚本仅报告原因并跳过该条,**绝不编造、估算或凭记忆生成任何资讯内容**。见闻摘要属**二手加工内容**,用于方向研判时须回到一手源(FRED/官方发布会/统计局)复核关键数字。

### 7.20 Jev 判断/校验工具（Typesafe,API Key 已配置）

- **定位**:`Jev` 是 Typesafe 出品的**判断/校验工具**(非行情源、非信号源)。它的职责是"判断"(judge)——对给定 State 回答你构造的 Questions;**生成归你,判断归 Jev,执行归代码**。本技能把它当作**审计员、门控器、校准器**来用:在已形成交易计划之后,用 Jev 对方向一致性、市场清晰度、安全窗口、品种选择、新闻冲击做独立校验,**不替代你的方向决策**。
- **Key 配置**:Key 已写入 `scripts/.jev_key`(本地文件,**不进 zip**、不进脚本源码);读取优先级 `--api-key` > 环境变量 `JEV_API_KEY`(=`TYPESAFE_API_KEY`) > `scripts/.jev_key`。
- **端点与认证**:`POST https://api.typesafe.ai/v1/systemone`,请求头 `Authorization: Bearer <TYPESAFE_API_KEY>`,`Content-Type: application/json`。请求体 `{"model": "jev-latest", "state": <string>, "questions": { "<id>": { "type": "noul|choice|score", ... } }}`。返回 `{"answers": { "<id>": { "noul"/"choice"/"score"..., "confidence": <0-1> } }}`。
- **三原语**:
  - `noul`(0–1 概率,是/否):用于"是否""有无"类判断(如方向是否一致、窗口是否安全、新闻是否扰动)。
  - `choice`(选项 + 概率 + 置信度):用于"选哪个"(如 best_pair: forex / gold / wti / none)。
  - `score`(有序量表,可小数 + `legend` + 置信度):用于"程度"(如市场清晰度 1–5 档)。
  - 一次请求可混合并行多个原语。
- **100 倍杠杆保守门控阈值(起点参考,实盘前须用本品种历史数据校准)**:

  | 维度 | 原语 | 阈值 | 含义 |
  |---|---|---|---|
  | 方向一致性 `direction_coherent` | noul | ≥0.80 | 未过:计划方向存疑,放弃提交 |
  | 市场清晰度 `market_clarity` | score | ≥2.5 | 未过:放弃或降至 1/3 仓 |
  | 安全窗口 `safe_to_execute` | noul | ≥0.85 | 未过:不执行 |
  | 品种选择 `best_pair` | choice | ≥0.80 | 未过:不交易(选 none) |
  | 新闻冲击 `news_impact` | noul | ≥0.75 | 未过:不纳入决策 |

- **调用纪律(强制)**:
  1. Jev 的判断结果是**信息,不是命令**;永远不要把低置信度输出当作确定事实来行动。在 100 倍杠杆下,一次错误的自信就是一次爆仓。
  2. 低置信度结果(`confidence` 未达阈值)**直接丢弃**,不进入决策。
  3. Jev **不能绕过风控硬边界**(单笔≤净值 1%、当日≤3%、连亏 3 笔熔断 24h、重大数据窗口前 30 分后 15 分禁开仓、隔夜敞口>20 倍须减仓)——门控通过只代表"可进入独立程序化风控复核",不代表放行。
  4. `state` 须为各品种纯净上下文(价/波动区间/数据发布/央行倾向/策略方向及依据),**不混入噪声**;`questions` 一次只问可证伪的明确问题。
  5. 社区回测显示直接把 Jev 当信号源方向命中率约 49.3%(跑输随机),官方标记高风险谨慎——**仅作校验层,绝不作信号层**。
- **State 构造要点**:
  - 外汇:现价 / 近期波动区间 / 待公布数据及时间 / 央行倾向 / 计划方向及依据。
  - 黄金(XAUUSD):现价 / 实际利率(TIPS)方向 / 美元指数 / 地缘事件 / 计划方向。
  - WTI:现价 / EIA 库存变化 / OPEC 表态 / 地缘跳空风险 / 计划方向。
- **客户端用法**:
  ```bash
  # ① 连通性自检(最小请求)
  python scripts/jev_fetch.py probe
  # ② 通用判断(自构 state/questions JSON)
  python scripts/jev_fetch.py evaluate --state-file state.json --questions-file q.json
  # ③ 100 倍杠杆审计门控(内置 4 题,综合决策)
  python scripts/jev_fetch.py audit --state-file state.json
  #   返回 0=审计通过(可进入独立程序化风控复核);2=未通过(放弃)
  ```
- **⚠️ 取数铁律(与本技能一致)**:任一调用失败/超时/返回空,脚本仅报告原因并跳过,绝不杜撰;置信度≠校准胜率,实盘前须用本品种历史数据校准后再用。

## 8. 溯源纪律(强制)

1. 每条宏观结论标注 `[源:xxx | 截至:YYYY-MM-DD]`。
2. 事件交易以官方日历时点为准,不在盘中凭记忆猜"还有几分钟公布"。
3. 社媒/自媒体观点仅作"市场情绪温度计",**不作为方向依据**,不在交易计划中引用其点位。
4. 当权威源之间出现分歧(如 FedWatch 比点阵图更鸽),明确记录为"预期差"机会,而非忽略。
