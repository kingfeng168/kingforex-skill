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
| **FRED**(圣路易斯联储) `fred.stlouisfed.org` | 官方一手 | `DGS10`(10Y 名义利率)、`DFII10`(10Y TIPS 实际利率)、`T10YIE`(10Y 盈亏平衡通胀) | 日频 | 网页 / 公开 API(需免费 key:`fred.stlouisfed.org/docs/api/fred`) |
| **美联储官网** `federalreserve.gov` | 官方一手 | SEP 经济预测摘要(含点阵图 Dot Plot)、FOMC 声明、鲍威尔发布会讲稿 | 每次会议 | 网页(经济预测摘要 / monetary policy) |
| **CME FedWatch** `cmegroup.com`(FedWatch Tool) | 市场隐含 | 联邦基金期货隐含的加息/降息概率路径 | 实时 | 网页工具(利率 → FedWatch) |
| **克利夫兰联储 Inflation Expectations** `clevelandfed.org` | 官方一手 | 未来通胀预期模型 | 日/周 | 网页 |
| **IMF** `imf.org`(SDMX 3.0 API) | 国际组织一手 | IFS 国际金融统计(实际有效汇率 `PRX_REER`、官方储备、货币总量)、WEO 宏观预测 | 月/季 | **脚本** `scripts/imf_fetch.py`(详见第 7 节) |
| **World Bank** `worldbank.org`(Open Data API v2) | 国际组织一手 | 实际利率 `FR.INR.RINR`、CPI 通胀 `FP.CPI.TOTL.ZG`、GDP 增速 `NY.GDP.MKTP.KD.ZG`、官方汇率 `PA.NUS.FCRF`——利率平价(IRP)/套息利差、通胀差、增长 Regime | 年(多数) | **脚本** `scripts/worldbank_fetch.py`(详见第 7 节) |
| **QuantGist** `quantgist.com`(API v1) | 聚合一手 | 经济日历/事件(`actual/forecast/surprise_pct`)、宏数据最近值(CPI/NFP/PCE/FOMC)、新闻雷达(地缘/油价/央行意外)、商品 ETF 快照(GL/USO)、情绪/意外排名 | 实时/日 | **脚本** `scripts/quantgist_fetch.py`(需 X-API-Key,详见第 7 节) |
| **实时行情源(聚合,无需 key)** `Frankfurter/gold-api/US Treasury/exchangerate-api/新浪` | 实时/参考报价 | Frankfurter(ECB 官方日参考汇率)、gold-api.com(伦敦金 XAU 现货价,秒级)、US Treasury Fiscal Data(美债收益率/汇率)、exchangerate-api(150+ 货币)、新浪(USDCNY 即期 + 伦敦金 hf_XAU **真实时**)——盘中实时报价、事件前后价格反应监控 | 实时/日 | **脚本** `scripts/live_market_fetch.py`(详见第 7 节,均无需 key) |

---

## 2. 外汇(对应 `fx.md`)

| 数据源 | 权威性 | 关键内容 | 更新频率 | 获取方式 |
|--------|--------|----------|----------|----------|
| **CFTC COT / TFF** `cftc.gov`(或 `cot.futures.io`) | 官方一手 | 持仓拥挤度;TFF(Traders in Financial Futures)报告覆盖欧元、日元、英镑、澳元等金融期货投机净头寸 | 每周五发布(截至周二) | 网页 / 下载 CSV |
| **BIS** `bis.org`(SDMX v2 API) | 国际组织一手 | 各国央行政策利率(`WS_CBPOL`)、美元汇率(`WS_XRU`)、有效汇率(`WS_EER`)、全球流动性(`WS_GLI`) | 月/季 | **脚本** `scripts/bis_fetch.py`(无需 key);详见第 7 节 |
| **IMF COFER** `imf.org`(SDMX 3.0 API) | 国际组织一手 | 官方外汇储备币种构成——**美元储备份额**(全球去美元化 / 美元信用结构性核心指标)、各币种配置 | 季(年度详细) | **脚本** `scripts/imf_fetch.py`;详见第 7 节 |
| **World Bank** `worldbank.org`(Open Data API v2) | 国际组织一手 | 经常账户占 GDP(`BN.CAB.XOKA.GD.ZS`——中期汇率方向)、实际利率(`FR.INR.RINR`——套息/IRP)、外储(`FI.RES.TOTL.CD`——EM 脆弱性/干预能力)、政府债务(`GC.DOD.TOTL.GD.ZS`) | 年 | **脚本** `scripts/worldbank_fetch.py`;详见第 7 节 |
| **QuantGist** `quantgist.com`(API v1) | 聚合一手 | 经济事件 `affected_symbols` 含 EURUSD/USDJPY/GBPUSD 等、新闻雷达地缘主题(iran-war/oil-supply/middle-east-risk)、情绪/意外排名 | 实时 | **脚本** `scripts/quantgist_fetch.py`(需 X-API-Key,详见第 7 节) |
| **实时行情源(聚合,无需 key)** | 实时/参考报价 | Frankfurter(ECB 日参考汇率)、exchangerate-api(150+ 货币)、新浪(USDCNY **真实时** 即期)——盘中即期报价直达、事件前后汇率反应 | 实时/日 | **脚本** `scripts/live_market_fetch.py`(详见第 7 节,无需 key) |
| **ECB 官网** `ecb.europa.eu` | 官方一手 | 货币政策声明、利率决议、前瞻指引 | 每次会议 | 网页 |
| **BoJ 官网** `boj.or.jp` | 官方一手 | 政策利率、YCC/正常化进程、日元展望 | 每次会议 | 网页 |
| **BoE 官网** `bankofengland.co.uk` | 官方一手 | 利率决议、通胀报告、前瞻指引 | 每次会议 | 网页 |
| **PBOC / 外管局** `pbc.gov.cn` `safe.gov.cn` | 官方一手 | 人民币中间价、跨境资本流动 | 日频 | 网页 |
| **美元指数 DXY** | 市场基准 | ICE 美元指数(一篮子 6 货币) | 实时 | TradingView / Yahoo / 经纪商终端 |

---

## 3. 黄金(对应 `gold.md`)

| 数据源 | 权威性 | 关键内容 | 更新频率 | 获取方式 |
|--------|--------|----------|----------|----------|
| **World Gold Council** `gold.org` | 行业权威一手 | 《Gold Demand Trends》季度报告、央行购金(官方部门统计)、ETF 流量、供需平衡 | 季度 / 月 | 网页 / 研究报告下载 |
| **LBMA** `lbma.org.uk` | 行业基准 | 伦敦金银定盘价、贵金属清算数据 | 日频 | 网页 |
| **CFTC COT**(见第 2 节) | 官方一手 | 黄金投机净头寸(拥挤度) | 周 | 同第 2 节 |
| **10Y TIPS**(FRED `DFII10`) | 官方一手 | 黄金定价第一锚(实际利率) | 日频 | 见第 1 节 |
| **gold-api.com / 新浪**(实时行情源) | 聚合参考 | 伦敦金 XAU 现货价(gold-api 秒级)、新浪 hf_XAU **真实时**(含黄金 T+D gds_AUTD)——盘中金价与事件前后反应 | 实时 | **脚本** `scripts/live_market_fetch.py`(`gold` / `sina` 预设,无需 key) |

---

## 4. 原油(对应 `oil.md`)

| 数据源 | 权威性 | 关键内容 | 更新频率 | 获取方式 |
|--------|--------|----------|----------|----------|
| **EIA** `eia.gov`(v2 API) | 官方一手 | 周度库存(原油 `WCRSTUS1` / 汽油总 `WGTSTUS1` / 馏分油 `WDISTUS1`,千桶)、WTI `RWTC`/Brent `RBRTE` 现货价(美元/桶) | 周三(库存) | **脚本** `scripts/eia_fetch.py`(key 已配置于 `scripts/.eia_key`);详见第 7.2 节 |
| **IEA** `iea.org` | 国际组织一手 | 月度石油市场报告(MOMR 同类)、全球需求预测、库存 | 月 | 网页 / 报告 |
| **OPEC** `opec.org` | 官方一手 | 月度石油市场报告、产量配额、执行率、闲置产能 | 月 | 网页 / 报告 |
| **API**(美国石油协会) | 行业一手 | 周度库存补充(公布早于 EIA) | 周二 | 网页 |
| **期货期限结构**(CME NYMEX / ICE) | 市场基准 | WTI-Brent 价差、Contango/Backwardation | 实时 | 经纪商 / TradingView |

---

## 5. 跨市场联动(对应 `cross_market.md`)

| 数据源 | 权威性 | 关键内容 | 获取方式 |
|--------|--------|----------|----------|
| **TradingView** `tradingview.com` | 市场基准 | 跨市场图表模板、VIX、信用利差(ICE/BofA)、AUD/JPY、USD/CAD、USD/CNH | 网页 / 模板 |
| **本地宏观日报系统(可选)** | 自用 | 已覆盖 40 品种的 JSON/HTML(`daily_data.json`),可直接作为本技能宏观研判输入源,**避免重复采集** | 读取 `./daily_data.json` |
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

本技能在 `scripts/` 随包提供六个**标准库实现、无需 pip 安装**的取数脚本,直接拉取权威源、输出 CSV,供研判与交易计划复用:

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

### 7.2 EIA v2 API（原油模块,已配置 key）

- **Base**:`https://api.eia.gov/v2`,免费 key 注册 https://www.eia.gov/opendata/。
- **Key 已配置**:key 已写入 `scripts/.eia_key`(本地文件,**不进 zip**、不进脚本源码);读取优先级 `--api-key` > 环境变量 `EIA_API_KEY` > `scripts/.eia_key`。用户重装 skill 后需重设(见 SKILL.md 末尾"密钥安全")。
- **权威价值**:周度原油/汽油/馏分油库存、WTI/Brent 现货价——原油模块(模块四)的核心一手源,直接驱动 EIA 周三库存事件交易研判。
- **常用路由/系列(2026-08 实测校准)**:
  - `petroleum/sum/sndw`(周度供需,**强制需要 `frequency=weekly`**):原油库存 `WCRSTUS1`、汽油总库存 `WGTSTUS1`、馏分油库存 `WDISTUS1`(单位均为千桶)。
  - `petroleum/pri/spt/data`(现货价,日度 `frequency=daily`):WTI 库欣 `RWTC`、Brent `RBRTE`(美元/桶)。
  - ⚠️ 系列过滤必须用 `facets[series][]=XXX`(脚本已内置),直接用 `series=` 参数会返回 HTTP 400;`crude_prod`(周度产量)在该路由下无对应 ID,已从预设移除。
- **脚本**:`scripts/eia_fetch.py`(标准库;预设 `crude_stocks/gas_stocks/dist_stocks/wti/brent`;`--last N` 自动按 period 倒序取最近 N 期,规避 EIA 5000 行分页截断)。

```bash
# 美国商业原油库存最近 12 周(无需再传 key,自动读 .eia_key)
python scripts/eia_fetch.py --preset crude_stocks --last 12 --out "./output/eia_crude_stocks.csv"
# 汽油总库存 / 馏分油库存 / WTI / Brent
python scripts/eia_fetch.py --preset gas_stocks --last 12
python scripts/eia_fetch.py --preset dist_stocks --last 12
python scripts/eia_fetch.py --preset wti --last 30
python scripts/eia_fetch.py --preset brent --last 30
# 直接指定路由+系列(sndw 必须带 --freq weekly)
python scripts/eia_fetch.py --route petroleum/sum/sndw --series WCRSTUS1 --freq weekly --last 24 --out "./output/eia_crude.csv"
```

### 7.3 IMF SDMX 3.0 API（宏观 / 外汇,需联网验证）

- **Base**:`https://api.imf.org/external/sdmx/3.0`(用户提供的 IMF SDMX 3.0 API),可用 `--base` 切换备用节点(如 `https://sdmxcentral.imf.org/sdmx/v3`)。
- **权威价值**:**COFER 美元储备份额**(全球官方外汇储备中美元占比,美元信用与去美元化的结构性核心指标)、IFS 实际/名义有效汇率、官方储备、WEO 宏观预测、BOP 国际收支、DOT 贸易方向——宏观与外汇研判的一手国际源。
- **常用 dataflow**:`COFER`(储备币种构成)、`IFS`(国际金融统计)、`BOP`(国际收支)、`DOT`(贸易方向)。
- **脚本**:`scripts/imf_fetch.py`(标准库,`--list` 列 dataflow、`--structure` 查维度、`--flow/--key` 取数、预设 `cofer/ifs/bop/dot`)。

```bash
# 先确认连通性与 dataflow 列表(本环境构建时 IMF 端点 502/404,需本地验证)
python scripts/imf_fetch.py --list
# 查 COFER 维度顺序,再写 key
python scripts/imf_fetch.py --structure COFER
# 拉全球美元储备份额相关序列(示例 key,以 --structure 为准)
python scripts/imf_fetch.py --preset cofer --format csv --out "./output/imf_cofer.csv"
```

> ⚠️ 透明说明:脚本编写时,构建环境对 `api.imf.org` 的 SDMX 3.0 端点返回 502/404(同一环境对 BIS 端点返回 200,判定为 IMF 服务端临时不可达或路径调整)。脚本严格按 SDMX 3.0 标准与用户基址编写;请本地用 `--list` 确认可达后再正式取数,路径变更时用 `--base` 指向可用节点。

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
  - **Frankfurter** `api.frankfurter.app`(ECB 官方参考汇率,日更,无 key / 限流宽松)——预设 `fx_ref`。
  - **gold-api.com** `api.gold-api.com`(伦敦金 XAU 现货价,秒级更新,无 key)——预设 `gold`。
  - **US Treasury Fiscal Data** `api.fiscaldata.treasury.gov`(美债收益率/汇率,v1 路由,无 key)——预设 `ust_yield`。
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

> ⚠️ 说明:新浪为非官方接口,需带 Referer 头(脚本已内置)并以 GBK 解码;加密交易所(Binance/OKX/Bybit/CoinGecko 等)在大陆网络被墙、Yahoo/ECB SDW/BIS 旧端点不可达,均已排除,不纳入本脚本。A股/港股实时(东财/腾讯)、需 key 源(Alpha Vantage/Twelve Data/FRED/Tushare)及偏题大模型清单,仅记录于用户桌面档案,未脚本化。

### 7.7 K 线历史数据(盘面解读的输入)

**本环境实测结论(2026-08/09 中国大陆网络):多数免费 K 线历史源不可用**,故盘面解读的输入遵循"**双路径、取数铁律**":

- **路径①(零网络依赖,推荐)**:用户从 MT4 导出 CSV 或粘贴 OHLC 文本,由 `scripts/kline_read.py` 本地确定性计算——与手工交易习惯一致、最可靠。
- **路径②(联网权威抓取,需免费 Key)**:当用户**未发送任何 K 线数据**时,用 `kline_read.py --fetch` 经 **Twelve Data** 联网抓取 15min/1H/4H/1D/1W 五周期——**Twelve Data 是中国大陆可直连、免翻墙的权威 OHLC 历史源**(2026-09 实测 HTTP 200,覆盖外汇/黄金/原油)。

> **取数铁律(与技能整体一致,不可逾越)**:任一周期抓取失败(Key 缺失 / 网络受限 / 品种不支持 / 返回空),**仅报告原因并跳过该周期**;五周期全部失败则明确告知"无法从任何权威渠道获取 K 线数据",并引导改用 `--csv`/`--text`,**严禁自行编造、估算或凭记忆生成任何价格**。

| 源 | 状态 | 说明 |
|---|---|---|
| **MT4 导出 CSV** | ✅ **推荐主输入(路径①)** | 文件→另存为,或"数据窗口"右键导出;脚本自动识别 `Date,Time,O,H,L,C,V` 表头与制表符/逗号分隔 |
| 粘贴 OHLC 文本 | ✅ 支持(路径①) | `--text "date,o,h,l,c"` 多行,临时快速解读 |
| **Twelve Data** `api.twelvedata.com` | ✅ **权威网络源(路径②)** | 中国大陆可直连,免费注册 https://twelvedata.com 取 Key;覆盖外汇/黄金/原油与 15min/1h/4h/1day/1week;经 `kline_fetch.py` 抓取,`kline_read.py --fetch` 逐周期分析 |
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

### 7.8 其他取数方式

- **FRED API**:`fred.stlouisfed.org/docs/api/fred`,免费注册 key,支持序列历史拉取(可用 `curl` 或 Python `requests`)。
- **WebFetch**:本环境可直接对官方/聚合页面做结构化抓取(用于无 API 的源,如 WGC、OPEC 报告要点)。
- **本地日报系统(可选)**:读取 `./daily_data.json`,作为滚动相关性分析的本地数据源。
- **Python / Excel**:对取回数据自动更新 20/60 日滚动相关性(见 `scripts/exposure.py` 与 `cross_market.md`)。

---

## 8. 溯源纪律(强制)

1. 每条宏观结论标注 `[源:xxx | 截至:YYYY-MM-DD]`。
2. 事件交易以官方日历时点为准,不在盘中凭记忆猜"还有几分钟公布"。
3. 社媒/自媒体观点仅作"市场情绪温度计",**不作为方向依据**,不在交易计划中引用其点位。
4. 当权威源之间出现分歧(如 FedWatch 比点阵图更鸽),明确记录为"预期差"机会,而非忽略。
