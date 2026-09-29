# kingforex-skill 更新日志

## v2.9.0 — 一致性修复版(数值口径 / 崩溃 / 数据源 / 量化 / 开仓闸门) · 2026-09-28

**⚠️ 本次为纯缺陷修复，不改报告格式**——冻结模板、23 节结构、15 图与 CSS 全部未动。
修复动因:第三方只读审计(实跑 60+ 次脚本、39 个端点实测、供应链哈希交叉验证)发现
文档与代码分裂成两套事实来源、约 1/3 "权威数据源"不可用或路径臆造、旗舰入口在中文
Windows 上必然崩溃、量化"第四维"因估计量偏误恒为通过、组合层缺开仓前闸门。

### 修复

1. **单笔风险统一到 1%(框架铁律 `calc_engine.RISK_HARD_CAP`)**
   - `scripts/position_report.py`: `--risk-pct` 默认值 `2.0` → `1.0`,报告纪律文案与文档示例同步。
   - `scripts/sl_tp_evaluate.py`: OVER_RISK 判定阈值 `>2%` → `>硬上限`,并新增 `>0.5%` warn 档。
   - `scripts/decision_enhanced_report_v25.py`: 判定 4 的 severe 阈值 `>2.0` → `>硬上限`(取引擎常量,不再写死)。
   - 文档同步:`SKILL.md`、`references/position_report.md`、`assets/position_report_template.html`。
2. **黄金/白银 pip 口径统一到 `calc_engine.CONTRACTS`(唯一事实来源)**
   - 修复前:黄金 0.01 手 / 止损 $50 被报「单笔美元风险 $50,000 = 账户 5,000%」(真实 $50 = 5%),放大 **1000 倍**。
   - `scripts/sl_tp_evaluate.py`、`scripts/decision_enhanced_report_v25.py` 的 `pip_scale()` 与
     `pip_value_account_per_stdlot()` 改为委托 `calc_engine`(支持 XAU/XAG/WTI 等别名);
     删除 v25 中 `100.0 * 0.1 * 10.0` 的硬凑常数。
   - 口径现为:黄金 pip=1.0($100/手)、白银 pip=0.01($50/手)、JPY 对 0.01、其余 0.0001。
3. **`scripts/exposure.py` 名义本金改为价格驱动(删除硬编码)**
   - 修复前硬编码 XAU=200000 / XAG=140000 / WTI=75000(隐含金价 $2000),黄金风险金额低估约 2.1 倍。
   - 现为 `名义本金 = 实时价 × 每标准手合约单位`;价格取 `--price SYM=VAL` >
     免费源自动取数(gold-api 金/银、Frankfurter 外汇) > **报错**(遵守「绝不杜撰价格」铁律,不用内置假价顶替)。
   - 新增 `--price` / `--no-fetch`;补齐此前缺失的 `audjpy`/`nzdjpy`(原对主力品种直接 `ValueError` 抛栈)。
4. **中文 Windows(cp936)编码崩溃修复**
   - 三类脚本在 cp936 控制台下因输出 `⚠ / ✗ / ⑪` 等字符抛 `UnicodeEncodeError` 并中断:
     `sl_tp_evaluate.py`(原 exit=1)、`gen_decision_enhanced_v256.py`(旗舰入口,原崩在装配完成前)。
   - 统一加 stdout/stderr `errors="replace"` 护栏(不改变控制台原生编码)。
   - `sl_tp_evaluate.py` 的 `subprocess.run(..., text=True)` 补 `encoding="utf-8"`:
     修复前自动取价静默失败 → `剩余 R:R` 恒为 `None`。

### 第二批(同日):数据源真实性 + 隐私披露

5. **IMF 源按实测重写(`scripts/imf_fetch.py`)**
   - 端点校正为 IMF 官方路径:结构 `GET /structure/dataflow/all/*/+`(实测 200,222 个 dataflow)、
     数据 `GET /data/dataflow/{agency}/{flow}/{version}/{key}`;旧路径 `/dataflow/IMF`、
     `/datastructure/IMF/{flow}`、`/Data/{flow}/{key}` 实测**全部 404**,已废弃。
   - agency/version 改为从结构清单**实时解析**(IMF 升版无需改码)。
   - **移除不存在的预设 `IFS` / `DOT`**(实测在 222 个 dataflow 中查无此 id);现存 `cofer/bop/cpi/irfcl/weo`。
   - **新增 0 观测检测**:实测 IMF 数据端点对所有键写法 / `AllDimensions` / SDMX-JSON Accept / 期间参数
     一律返回「结构信封 + 0 观测」,即**当前不可供数**。脚本检测到即 **exit 3** 并给出替代源
     (worldbank_fetch / bis_fetch / fred_fetch),`--allow-empty` 仅供排查,绝不把空信封当数据落盘。
6. **QuantGist 加服务可用性预检(`scripts/quantgist_fetch.py`)**
   - 实测 `api.quantgist.com` 的 `/`、`/docs`、`/v1/health`、`/v1/calendar`、`/v1/usage` **全部 502**
     (官网 200 → API 子域后端故障),13 个预设 100% 不可用。
   - 新增 `preflight()`:4xx 视为服务在线(交给 `fetch()` 报鉴权/套餐错),5xx/超时即提前 **exit 3**
     并说明原因与替代源(jin10_mcp / wscn_fetch);`--force` 可跳过预检。
7. **财政部预设口径更正(`scripts/live_market_fetch.py`)**
   - `ust_yield` 原实现调 `v1/accounting/od/rates_of_exchange`(外币折算**记账汇率**,完全不含收益率),
     属误标;现改用 `v2/accounting/od/avg_interest_rates`(**存量国债平均利率,月度**),
     并在字段注明"非市场收益率,市场收益率见 fred_fetch.py DGS10"。
   - 记账汇率另立新预设 `ust_fx`(原行为原样保留);`--preset all` 同步聚合两者。
8. **Frankfurter 域名统一与说明更正**
   - `live_market_fetch.py` 的 `fx_ref` 由 `api.frankfurter.app` 统一为 `api.frankfurter.dev`,
     与 `frankfurter_fetch.py` / `data_sources.md` 一致。
   - 更正 `frankfurter_fetch.py` 与两处文档中"旧 `.app` 域已 301 失效"的错误说法:
     2026-09-28 实测 `.app` 与 `.dev` **均返回 200 且数据一致**。
9. **LBMA / WGC 链接与定性更正(`scripts/wgc_lbma_fetch.py`)**
   - LBMA 手工取数链接 `/market-data/statistics`(实测 404)→ `/prices-and-data/precious-metal-prices`(200)。
   - WGC 子页 `/goldhub/data/gold-demand-trends`(404)改为 `/goldhub/data/gold-demand-by-country`(200)并注明。
   - 定性更正:gold-api.com 是**第三方连续现货报价**,与 LBMA 10:30/15:00 **拍卖定盘**机制不同,
     正文不再称"紧贴 LBMA 定盘"/"定盘代理"。
10. **幽灵脚本引用清理(文档)**
    - `references/data_sources.md` §7.12「iTick API」整节改写为「已移除(v2.4.6)」:
      原文档给出 `itick_fetch.py quote/kline` 命令、`scripts/.itick_key` 等,**而该脚本早已删除**;
      现标注失效命令并给出替代(live_market_fetch / kline_fetch / `futures_analysis.py basis --fut` 手工传价)。
    - 同步 `references/futures_analysis.md`(数据源表 / 降级说明)、`references/position_report.md`(第 3.1 节
      必备数据源:实时报价改注 AllRatesToday)、`references/quant_finance.md`(value 因子:IMF REER 标注暂不可用)。
    - `data_sources.md` §7.17 与 §7.11 更正 frankfurter 域名与 goldprice.dev "被 Cloudflare 拦截"的过时说明
      (实测本机可直连)。

### 隐私与卫生(第二批)

11. **`.gitignore` 补个人财务数据规则**:新增 `scripts/daily_data_*.json`、`daily_data_*.json`、
    `*_sample.html`、`KingForex数据/` —— 此前 `daily_data_*.json` 与 `*_sample.html` 会把**真实账户权益与持仓**
    一起提交(内容不含密钥,但属个人财务数据)。
12. **从发布副本移除 `scripts/daily_data_20260914.json`**(28KB,含 equity 636.59 / deposit 522.0 /
    AUDJPY SELL 0.02 持仓快照;本地安装副本保留)。⚠️ **仍需你在 GitHub 侧执行**:
    ① `git rm --cached` 后提交,② 如需彻底清除历史可用 `git filter-repo`/BFG(历史提交中该文件仍可被检出)。
13. **README 密钥表补披露**:新增 WSCN / QuantGist / qveris 三行,并明确写出
    `qveris_fetch.py` 会回退读取用户级 `~/.workbuddy/mcp.json` 的 `mcpServers.qveris.headers.Authorization`
    (仅限该条目、仅用于 qveris 请求、不外传),消除"未披露的越界读取"。
14. **ECharts CDN 回退版本统一到 5.5.1**:`position_report.py` / `gen_decision_enhanced_v256.py` /
    `decision_enhanced_report.py` / `gen_report_param.py`(原钉 `5.4.3`)、`kline_read.py` /
    `mtf_confluence.py`(原为未钉版本的 `@5`)与 `assets/position_report_template.html` 全部对齐
    本地资产版本 5.5.1(本地内嵌优先策略不变,产出 HTML 的 CDN 引用仍须为 0)。

### 第三批(同日):数据新鲜度门禁 / Hurst 定稿 / 开仓前闸门 / JSON 输出

15. **旗舰生成器:`gen_decision_enhanced_v256.py` 数据新鲜度门禁(消除"页头今天、正文旧日期")**
    - **删除机器私有兜底路径**:原输出目录解析的第 3 级兜底是 `r"D:/R12/美日输出/FOREX"`(作者本机目录),
      会在任意用户机器上"技能外静默写盘";现改为 `KINGFOREX_DATA`(须存在) > `<包根>/KingForex数据/output/<最新日期>`
      > **报错退出**,不再回退任何技能目录之外的绝对路径;末级写死的 `2026-09-18` 日期目录一并删除。
    - **缺 `scripts/.td_key` 时拒绝回退硬编码旧价**:原实现取价失败会静默使用 `USDJPY=157.11787`、
      `POS_CUR=111.97327`,产出混杂报告;现直接报错退出并给出补救方式(写 key / 设 `TWELVEDATA_API_KEY` /
      显式 `KINGFOREX_ALLOW_STALE=1` 确认离线出图)。同时新增 `TWELVEDATA_API_KEY` 环境变量支持。
    - **数据基准日取自数据本身**:`DATA_AS_OF` = 各标的日K末根的最大日期;滞后超过
      `KINGFOREX_MAX_LAG_DAYS`(默认 3)天即拒绝出报告。
    - **溯源行日期改写 + 收尾门禁**:「数据截至/取数/末根」类文字统一改用 `DATA_AS_OF`,
      并在写盘前扫描这些行 —— 只要残留与基准日不符的日期字面量(如数据层未更新时的
      `FRED 利率观测 09-18/17`)即**拒绝写出**并逐条列出,`--allow-stale` 可显式放行。
    - 顺带删除重复的 `_html_subs` / `_md_subs` 同步块(等价冗余)。
    - 实测:场景 1(数据层仍旧)exit 1 并列出 15 处不符;场景 2(`ALLOW_STALE=1`)exit 0 且溯源行显示
      真实基准日 `2026-09-28`;场景 3(缺 key)exit 1;场景 4(无输出目录)exit 1 且不再写 `D:/R12`。
16. **Hurst 定稿:`quant_metrics.py` 改用 DFA-1 + 自助法随机游走带**
    - 实测对照(n=200, 60 次随机游走, 理论 H=0.500):原 R/S 实现均值 **0.984**、
      加 Anis-Lloyd 修正后仍 **0.840**、**DFA-1(smin=8, smax=n/4)均值 0.505**。
      对真实持续性序列(AR(1) φ=0.3)DFA-1 给 0.667(正确>0.5)、R/S 给 0.836(被偏误污染)。
      → **主估计量改为 `hurst_dfa()`**;`hurst_rs()` 保留但标注"已知偏高,仅对照"。
    - **判定改用自助法随机游走带(5%/95%)**:`Hurst_判定` ∈ {趋势显著 / 均值回归显著 / 与随机游走不可区分},
      不再使用固定 0.45/0.55 阈值。真实 7 标的实测:6/7 落在带内(即**不再假报趋势**),AUDJPY 显著(H=0.688, 带[0.389,0.651])。
    - `--json` 增出 `Hurst_DFA` / `Hurst_RS_有偏` / `Hurst_随机游走带` / `Hurst_判定`;新增 `--boot N`(默认 100, 0=跳过)。
    - **去重**:`decision_enhanced_report_v25.py` 与 `gen_decision_enhanced_v256.py` 里各自的本地 R/S 实现
      改为委托 `quant_metrics.hurst_dfa`(单一事实来源),模块不可用时返回 0.5(不判趋势)。
17. **`quant_metrics.py --json` 输出修复**
    - 原实现 `out[k] = v if v is None or (isinstance(v, float) and math.isfinite(v)) else None` 会把
      **list / str / int / bool 全部吞成 null**(导致新增的带与判定字段在 JSON 里恒为 null);
      改为递归清洗(仅非有限 float 置 None)。
    - JSON 改为**纯 ASCII 转义**输出,cp936 管道/GBK 控制台下的下游解析不再乱码。
18. **`exposure.py` 新增开仓前组合闸门 `--check-new`(纪律从"写在文档"变为"可执行")**
    - 原技能只有事后净方向计算,纪律里写着"禁止多金+多澳+多油(单一美元空头)"却**无任何开仓前拦截**。
    - 现把待开仓与现有持仓合并后逐条判定:①单笔风险 ≤ `calc_engine.RISK_HARD_CAP` ②组合总风险 ≤ `PORTFOLIO_CAP`
      ③净美元 β 集中度(提示 2.0 / 否决 3.0)④同向暴露笔数(提示 3 / 否决 4)⑤按上限反推的最大手数。
      **通过 exit 0 / 否决 exit 3**,可直接作为 agent 的下单前闸门。
    - 实测:黄金 0.01 手 / 止损 1.5% / 权益 574 → 单笔 10.83%、组合 17.82% → **exit 3 否决**;
      GBPUSD 0.05 手 / 止损 0.5% / 权益 10000 → 单笔 0.33%、组合 0.90% → **exit 0 通过**。
19. **版本治理**:SKILL.md frontmatter 增 `version: 2.9.0`(并移除非标准字段 `agent_created`)、
    **description 由 1977 字符(4171 字节)精简为 293 字符**,原全量触发词迁至
    `references/trigger_guide.md`;README 版本号、脚本/参考/资产计数(48 / 19 / 11)与快速开始同步;
    生成器与报告产物的版本串统一为 `v2.9.0`。

### 第四批(同日):脚本清理(仍在 v2.9.0,未改版本号)

20. **处理 6 个"克隆后必然报 `FileNotFoundError`"的历史/开发脚本**(依赖已删除的
    `gen_report_20260914.py`、从未随仓库分发的 `_paramtest/` 比对样本、或写死的日期目录):
    - **修复**:`scripts/parity_check.py` 改为命令行传参(`--orig/--param`,或 `--dir` 自动取最新
      两份 `今日行情分析*.html`),并新增「数值字面量缺失统计」;实测比对 v2.8.1 与 v2.9.0 两份真实报告,
      输出 23 节 / 10 评分卡 / 15 个 `echarts.init` / CDN 0 —— **确认报告格式零漂移**。
    - **归档**:`transform_to_param.py`、`build_daily_json.py`、`build_gen_daily.py`、
      `decision_enhanced_report.py`(v2.3)、`gen_report_param.py`(v2.4)移至
      `scripts/_archive/legacy_dev_tools/`,**不再随安装包分发**(与仓库既有的 `_archive/` 约定一致)。
    - 文档同步:`SKILL.md` 标注归档并在每日更新流程中改为「直接改生成器数据层」;
      `README.md` 脚本计数 48 → **36 个活跃脚本**;`references/daily_data_contract.md` 标注为 legacy;
      `INSTALL.md` 第九节列出处理明细(包内不再有不可运行脚本)。
    - 影响面:活跃 `scripts/` 由 40 → **36** 个,全部 `py_compile` 通过,日常流程不依赖任何归档件。

### 已知遗留(未在本次范围内)

- 报告**正文数据层**仍为快照式硬编码(如事件日历 09-18 条目、宏观事项文本):鲜度门禁会因此拦下未更新
  数据层的运行——这是**有意设计**(阻止"页头今天、正文旧日期"),日常需配合 `build_gen_daily.py` 更新数据层。
- `references/quant_finance.md` 的其余量化事实错误(小时年化系数 2190、小时 EWMA λ=0.97、IC 语义、
  EG 协整临界值、roll yield 公式)与若干方向性事实错误(利差与 CIP/UIP 表述、铜金比命名、EIA 冬令时时点、
  仓位公式漏合约乘数)仍待逐条更正(清单见评估说明附录 D)。
- `assets/decision_enhanced_sample.html`(1.15MB)仍含真实账户痕迹(已加 .gitignore,但历史提交仍可检出),
  如需彻底清除须 `git filter-repo`/BFG。

## v2.8.1 — 新增 Jev 判断/校验工具(Typesafe,API Key 已配置) · 2026-09-21

触发场景:用户指令「请在技能中加入Jev:apikey_...」(提供 Jev(Typesafe 判断工具)API Key,并补充完整规格)。

**⚠️ 本次为纯数据源能力扩展,不涉及任何报告格式变更**——v2.8.0 冻结模板与产出结构完全不变。

### ① 新增判断/校验工具:Jev(Typesafe,API Key 已配置)

- **定位已确认**:`Jev` 为 Typesafe 出品的**判断/校验工具**(非行情源、非信号源),端点 `https://api.typesafe.ai/v1/systemone`,`Authorization: Bearer <TYPESAFE_API_KEY>`。本技能将其定位为**审计员/门控器/校准器**——只做"判断/校验",不替代方向决策,低置信度结果直接丢弃。
- **Key 已配置**:写入 `scripts/.jev_key`(本地文件,不进 zip、不进源码);读取优先级 `--api-key` > 环境变量 `JEV_API_KEY`(=`TYPESAFE_API_KEY`) > `scripts/.jev_key`。
- **客户端:由探针升级为完整 Typesafe Jev 客户端**:`scripts/jev_fetch.py` 现提供 `probe`(连通性自检)/ `evaluate`(通用判断,自构 `--state-file`+`--questions-file`)/ `audit`(内置 4 题 100 倍杠杆审计门控,返回 0=通过、2=放弃)三个子命令;三原语 `noul/choice/score` 并行支持,保守阈值 direction_coherent(noul)≥0.80 / market_clarity(score)≥2.5 / safe_to_execute(noul)≥0.85 / best_pair(choice)≥0.80 / news_impact(noul)≥0.75。
- **文档同步**:`README.md` 密钥表改为「Typesafe 判断工具 / api.typesafe.ai」;`SKILL.md` 正文第 0 阶列表与 references 表把 Jev 改为「判断/校验工具」,「密钥安全」bullet 重写为 Typesafe 定位与 100 倍杠杆阈值;`references/data_sources.md` §7.20 整段重写为 Typesafe 接入说明(端点/认证/三原语/阈值表/调用纪律/State 构造/示例)。

### ② 安全说明

- 真实 Key 不落盘于可分发产物;如怀疑泄露,立即到 Jev 平台吊销并换新 key。

## v2.8.0 — 移除事件静默纪律(一票否决) · 2026-09-21

触发场景：用户指令「更新技能 去除 事件静默纪律」(附图指向「事件静默纪律(一票否决)」)。

**本次为策略规则移除，整体框架/版式骨架不动**；产出结构由 24 节变为 **23 节**(六·补事件静默节整节下线)。冻结模板 `assets/decision_enhanced_template_v256.html` 文件本身不改动，仅作 CSS 骨架。报告生成器版本号 v2.7.0 → **v2.8.0**。

### 移除清单(事件静默纪律整族)

- **引擎** `scripts/decision_enhanced_report_v25.py`：`evaluate_position()` 删除角度⑥事件静默与一票否决分支 → **五角度收敛**(凯利半仓/1%硬上限/0.5%保守/组合约束/ATR 匹配)；`event_silent`/`event_name` 参数仅向后兼容保留、不再生效；渲染层删除角度⑥行，收敛规则与「六角度」措辞同步改为「五角度」。
- **补节** `scripts/extra_sections_20260916.py`：`sec06b()`(六·补 事件静默自动计算)与 EVENTS 表整节移除；一致性校验 CHECKS 删除「事件静默规则一致」项。
- **生成器** `scripts/gen_decision_enhanced_v256.py`：移除 `_SEC06B` 注入与 `event_silent=True` 传参；第六节「⚠ 事件纪律」横幅(HTML)与 MD 事件纪律行删除；交易纪律卡移除「事件前 4h 不开新仓」「议息前 24h 清仓或最小仓」两条。
- **文档** `SKILL.md` / `README.md` / `references/position_report.md`：规则表删除「事件静默」「议息清仓」两行，24 节顺序改 23 节，收敛规则同步修订。
- **保留**：`scripts/calc_engine.py` 的 `event_silence()` 降级为纯时间窗计算工具(兼容 `gen_report_param.py` 等旧脚本，不强制任何约束)；`_archive/` 与历史 CHANGELOG 条目不动。

### 实盘影响

- 事件窗口(如央行周)内**允许开新仓**——仓位仅受凯利/1%硬上限/0.5%保守/组合 5%/ATR 五角度最小值约束。
- 风险提示：该规则原为超级央行周强制降杠杆保护，移除后事件窗口的波动风险由交易者自行评估。

## v2.6.0 — 新增华尔街见闻 WSCN MCP 数据源(第二资讯源) · 2026-09-17

触发场景：用户指令「把华尔街见闻 MCP 加入到 kingforex-skill 的数据源」。

**⚠️ 本次不涉及任何报告格式变更**——v2.5.6 冻结模板与产出结构完全不变(24 节 / 15 ECharts / 10 评分卡 / 0 CDN 基线照旧)。本版本为**纯数据源能力扩展**。

### ① 新增数据源:华尔街见闻 WSCN MCP

- **端点**：`https://xgb-mcp-api.xuangubao.cn/mcp`（streamable-http，中国大陆可直连）
- **服务端**：`xgbmcp-market-data v0.1.0`
- **认证**：`Authorization: Bearer <key>` **且必须同时带 `X-WMCP-Client: wbwscn`**（缺一即被网关拒绝——该头是本源的接入契约关键）
- **费用**：免费（2026-09-17 实测连通并取回真实数据）
- **限制**：仅可查询**近两个月**数据，日期为北京时间
- **三个只读工具**：
  | 工具 | 用途 | 关键参数 |
  |---|---|---|
  | `get_wscn_global_articles` | 全球资讯列表(title+summary+id,**不含正文**) | `date`(默认当天) |
  | `get_wscn_global_article_detail` | 单篇正文(HTML) | `date` + `id`(均必填) |
  | `get_large_stocks` | A股异动板块+个股+上涨原因 | `date`(默认当天) |

### ② 新增脚本 `scripts/wscn_fetch.py`（纯标准库，无需 pip）

标准 MCP streamable-HTTP 流程（`initialize` → `notifications/initialized` → `tools/list` → `tools/call`，协议 2024-11-05）。子命令：

| 子命令 | 作用 |
|---|---|
| `probe` | 连通性 + 工具清单自检 |
| **`relevant`** | **【推荐】按交易事件相关度排序的资讯**——内置六类关键词打分 |
| `articles` | 全球资讯列表(可落 JSON) |
| `detail` | 单篇正文 |
| `stocks` | A股大涨股异动 |

- **`relevant` 排序逻辑**：对六组交易关键关键词(央行/货币政策、汇率/美元、贵金属、原油/能源/地缘、通胀/就业/宏观、关税/衰退/避险)统计命中数，命中越多越靠前，同分按 `displayTime` 倒序；输出每条附 `_score`(命中数)与 `_hits`(命中词列表)。关键词表在脚本 `KEYWORDS` 常量，可随研究方向增补。
- **实测样本(2026-09-17)**：全量 45 条资讯中命中交易事件 12 条，排序首位命中 8 词——「美联储全票通过三年来首次加息，点阵图料年内还将加一次」，与当日宏观主线完全吻合。

### ③ 定位:金十之外的第二资讯源

| 源 | 定位 | 内容特征 |
|---|---|---|
| 金十 Jin10(§7.11) | 第一源 | 实时快闪 / 报价 / 财经日历 —— **高频速报** |
| 华尔街见闻 WSCN(§7.19) | **第二源** | 全球资讯深度摘要 + 事件因果归因 + 异动逻辑 —— **中低频解读** |

**见闻用于事件结论的交叉验证，不替代金十**。用于报告的四个场景：①宏观大事节(补事件的市场解读与因果链) ②地缘风险卡(原油供应冲击/海峡通行/制裁传导链) ③跨市场联动(见闻摘要常直接给出「美联储加息→美元拉升→黄金跳水→美债收益率反弹」的联动表述) ④事件预期差(多家机构解读汇总，识别共识与分歧)。

### ④ 凭据与溯源

- Token 存于 `scripts/.wscn_key`(单行纯文本，**不进 zip**)；读取优先级：`--api-key` > 环境变量 `WSCN_API_KEY` > `scripts/.wscn_key`。
- 溯源格式：`[源: 华尔街见闻 | 截至:YYYY-MM-DD HH:MM]`；与金十并用时分别标注，出现分歧按 `references/data_sources.md` §8 第 4 条记为「预期差」而非取其一。
- **见闻摘要属二手加工内容**，用于方向研判时须回到一手源(FRED/官方发布会/统计局)复核关键数字；任一调用失败仅报告原因并跳过，**绝不编造资讯内容**。

### ⑤ 文档同步

- `references/data_sources.md`：新增 **§7.19 华尔街见闻 WSCN MCP**；§1 速查表(宏观与利率)新增一行条目；§0/§8 溯源纪律沿用。
- `SKILL.md`：frontmatter description 新增「华尔街见闻 WSCN/见闻全球资讯」触发词与数据源列举；脚本清单新增 `scripts/wscn_fetch.py` 条目；「密钥与环境变量」节新增 WSCN MCP token 条目(含 `X-WMCP-Client` 头提醒)；加密文件清单补入 `.wscn_key`。
- 版本线：**v2.6.0 当前**（数据源扩展版），v2.5.6 仍为**报告格式冻结基线**（两者不冲突：v2.6.0 未改格式）。

## v2.5.6 (热修②) — scorechart 柱内标签改「居中横排」+ 柱体加宽(修复数字重叠/溢出) · 2026-09-16

触发场景：用户第四次「调准格式」指令（同日）：v2.5.6 首发版 scorechart 柱内数值标签（insideTop + rotate 90 竖排）**数字重叠**，要求「柱形图中的数字放到柱子中间、横着显示，注意数字大小不要超出柱子外」。

- **柱内数值标签**：`position: insideTop + rotate:90 + fontSize 9` → **`position: inside + rotate:0 + fontSize 8 + fontWeight 600`**（柱内正中、横向显示）。
- **柱体加宽**：四维柱 series 统一追加 `barCategoryGap: "8%"` / `barGap: "5%"`（每柱 ≈27px，容纳 5 字符 2 位小数标注，不溢出柱宽、不与相邻柱标签重叠）。
- 数值/位数**零改动**：柱内四维与折线总分仍全部 2 位小数，与四·补明细同源（AUDJPY 65.30 / USDKRW 59.90）。
- 无头截图核验（评分节独立页 + 分组放大）：XAUUSD/XAGUSD/AUDJPY/USDKRW 各组柱内数字居中横排、无重叠、无溢出。
- 资产同步：冻结模板 `assets/decision_enhanced_template_v256.html` 更新（新 SHA256 前缀 `0f1d7176`，1,243,090 B）；生成器 `scripts/gen_decision_enhanced_v256.py` 同步；实战样本重新产出（24 节 24/24、echarts init 15/15、CDN 0、三引擎 patch 全 OK）。**版本号保持 v2.5.6**（同一授权框架内的渲染缺陷修复，非新格式版本）。

## v2.5.6 — 「调准格式」第三次授权: 撤回 v2.5.5 分项说明表 + scorechart 数值标注(2位小数, 与四·补明细一致) · 2026-09-16

本轮同步技能（开源副本 + 已安装副本），**不动 EXE**。
触发场景：用户 2026-09-16 第三次「调准格式」指令：**去除 v2.5.5 版本、回归 v2.5.4 框架**；scorechart 微调——柱状图内显示数值、折线数值与「四·补 评分模型子项明细」**数值一致、位数一致**（2 位小数），更新版本 V2.5.6。

### ① 撤回 v2.5.5
- 移除第四节「4.1 评分分项说明一览表」，评分卡回归 v2.5.4 框架（score-card 卡片 + scorechart 图表）。
- v2.5.5 模板/生成器资产（`decision_enhanced_template_v255.html` / `gen_decision_enhanced_v255.py`）已从技能与交付目录删除；下方 v2.5.5 条目保留作历史记录（标记已撤回）。

### ② scorechart 数值标注（本次核心）
- **四维柱**：柱内竖排（rotate 90, insideTop）标注数值，**2 位小数**（如 68.00），位数与四·补「维内均值」列一致。（⚠️ 该竖排方式后被同日热修②改为居中横排，见上方条目）
- **综合总分折线**：由整数改为**精确加权值 2 位小数**（AUDJPY 65.30 / USDKRW 59.90 等），与四·补「总分」行完全一致；图下注释同步为 65.30。
- 数据源：与四·补明细同源（SCORES 四维加权；AUDJPY 66/68/64/62、USDKRW 58/70/56/52 与明细维内均值逐一相符），无独立数据块。
- 图表标题注明「数值均为2位小数与四·补子项明细一致」。

### ③ 版本与资产
- 冻结模板 `assets/decision_enhanced_template_v256.html`（SHA256 前缀 `f918f78a`，1,215,549 B）；生成器 `scripts/gen_decision_enhanced_v256.py`（= v2.5.4 框架 + ②）。
- 实战样本 `今日行情分析_决策增强版_v2.5.6_2026-09-16.html`：24 节 24/24、echarts init 15/15、CDN 0、三引擎 patch 全 OK、无头截图核验柱内数值/折线 2 位小数标注渲染正常。
- SKILL.md 输出规范首条升级 v2.5.6 口径（评分卡双格式 + 数值位数铁律 + 校验清单 8 项）；版本线：**v2.5.6 当前基线**，v2.5.5 已撤回删除，v2.5.4/v2.5.3/v2.5.2 历史保留。


## v2.5.5 — 【已撤回 · 2026-09-16】「调准格式」第二次授权: 评分卡新增 4.1 分项说明一览表

> ⚠️ **本版本已按用户指令于同日撤回**（第三次调准指令：去除 v2.5.5、回归 2.5.4），相关资产已删除，仅留此记录。其「分项说明一览表」内容如需恢复由 v2.5.6+ 按新指令重新实现。


## v2.5.4 — 「调准格式」授权调准: 评分卡加评分图表 + 各节数据截至行 + 校验/纪律序号调换 · 2026-09-16

本轮同步技能（开源副本 + 已安装副本），**不动 EXE**。
触发场景：用户 2026-09-16 发出「调准格式」指令（格式变更唯一授权词），要求：①标的评分卡按模板逻辑与评分标准不变、格式调准增加图表；②数据和信息部分显示获取截止时间；③截图标注末节序号「二十/十九」需调换。

### ① 评分卡新增 ECharts 评分图表（第四节）
- score-card 卡片网格（4×3，格式与逻辑不变）之后新增 `id="scorechart"` 评分图表：**四维分组柱**（宏观25% #4a7fff / 技术30% #2ecc71 / 量化25% #f1c40f / 情绪20% #e67e22）+ **综合总分折线**（#ff5c7a，含数据标签）+ **75 分建仓绿色虚线 markLine**；数据与卡片同源（SCORES 四维加权），图下注明「与第二节不建仓判定一致」。
- ECharts 实例 14 → **15**；评分逻辑与评分标准（四维加权、≥75 可建仓）零改动。

### ② 数据/信息节新增「⏱ 数据截至」说明行
- 页头 meta 新增全局数据截至行（行情/K线/FRED/日历/COT 五源汇总）；三快照、四评分、五宏观、六日历、七跨市场、八K线、九量化、十七回测共 8 节首行各加分项截至说明（源 + 末根/观测日 + 取数时点 15:45 GMT+8）。
- 十八节「引用与依据」数据|源|截至表沿用不变（此前已含截至列）。

### ③ 章节序号调换（纪律仍置末）
- **数据一致性校验报告：二十 → 十九；交易纪律：十九 → 二十**；装配顺序不变（校验报告仍先于纪律），`extra_sections` 的 sec20() 标题同步改。
- 页脚交叉引用「数据溯源见⑯」勘误为「见⑱」（引用与依据节）。

### ④ 版本与资产
- 冻结模板 `assets/decision_enhanced_template_v254.html`（SHA256 前缀 `98c47592`，1,214,824 B）；生成器 `scripts/gen_decision_enhanced_v254.py`（数据层/渲染层分离继承 v2.5.2）；`scripts/extra_sections_20260916.py` 同步更新。
- 实战样本 `今日行情分析_决策增强版_v2.5.4_2026-09-16.html`：24 节标题 24/24、score-card 10/10、echarts init 15/15、CDN 0、数据截至行 9 处、三引擎 patch 全 OK；无头截图核验评分图表与末节编号渲染正常。
- 版本号说明：v2.5.3 已由「报告生成器参数化 + goldprice.dev 历史接口」占用，故本次格式调准使用 v2.5.4。
- SKILL.md 输出规范首条/模板条目/生成器条目/调用示例同步升级为 v2.5.4 口径；v2.5.2 及更早版本标记历史保留。


## v2.5.3 — 报告生成器参数化(gen_report_param.py) + goldprice.dev 历史 K 线接口 · 2026-09-16

本轮同步技能（开源副本 + 已安装副本），**不动 EXE**。
触发场景：用户确认 gen_report_20260914.py 为 09-14 静态快照（报价/事件硬编码），要求重构为参数化版本并纳入技能；同时新增 goldprice.dev 历史 K 线取数接口。

### ① 报告生成器参数化（核心）
- 新增 `scripts/gen_report_param.py`：完全由 `daily_data.json` 驱动，不再硬编码任何每日市场数据（报价/利率/评分/账户/事件/持仓/相关性/止损/K线/徽章/版本号）。原 1562 行 HTML/MD/XLSX 装配逻辑零改写，仅把顶部硬编码常量抽成数据契约，运行时由桥(json.load)重新绑定同名全局变量。
- 配套 `scripts/daily_data_20260914.json`：09-14 全量数据契约样例（37 个顶层 key），可作 schema 参考，亦可复现 09-14 报告。
- 数据契约文档：`references/daily_data_contract.md`（逐字段说明 + 每日填写铁律）。
- 迁移/校验工具：`scripts/build_daily_json.py`（快照模块 → daily_data.json，零转录误差）、`scripts/transform_to_param.py`（快照 → 参数化版的转换器）、`scripts/parity_check.py`（与原报告逐项 parity 校验）。
- **parity 校验全绿**：HTML 字节差异仅 +93（INST 配置紧凑 JSON 注入 vs 原 JS 对象字面量，渲染等价）、MD 字节完全一致、节数 22=22、外链 6=6、jsdelivr CDN 0=0（离线内嵌）、MD 二级标题 22=22、15 项关键数值双方均在。
- 账户状态关键数值（$636.59/$522/浮动 $0/累计 21.94%）改为由 `account` 字段渲染，杜绝卡片硬编码。
- echarts 加载路径改为脚本相对（`<skill>/assets/echarts.min.js`），提升跨机可移植性。

### ② goldprice.dev 历史 K 线接口
- `scripts/goldprice_fetch.py` 新增 `--history` 模式：优先走官方 `/v1/bars`（取代已弃用 `/v1/prices/history`），支持游标分页、自动按 `bar_start` 升序、剔除 `is_closed=false` 的正在形成棒（`--keep-forming` 可保留），输出 `kline_<SYM>_1d.csv` 直喂报告 KD 字典。
- 免费层限制：仅最近 30 天日线 XAU/USD；更久历史需 Pro。脚本对 Cloudflare(1010) 拦截做友好降级。

### ③ 使用方式
- 参数化报告：`python scripts/gen_report_param.py --date 2026-09-16 --data daily_data_20260916.json --kline-dir <csv目录> --out <输出目录>`
- 刷新黄金 K 线：`python scripts/goldprice_fetch.py --history --symbol XAU-USD-SPOT --from 2026-09-16 --to 2026-10-16 --out-dir <csv目录>`


## v2.5.2 — §九 量化验证改为「分标的独立雷达」(不叠加) · 2026-09-15

本轮同步技能（开源副本 + 已安装副本），**不动 EXE**。
触发场景：用户对 §九 量化验证节提出格式要求 ——「每个分析的标的单独一个图，不要叠加在一起」。

### ① §九 量化验证节：从「单图/叠加」改为「分标的独立雷达」
- **旧版问题**：v2.4.x 将 AUDJPY + XAUUSD 双多边形叠加在同一张雷达（直方图同理叠加）；v2.5.0/2.5.1 退化为仅 AUDJPY 单图，**韩元(USDKRW) 专项无独立图**。
- **v2.5.2 规范**：§九 按标的内部分段（9.1 / 9.2 / …），**每个标的独占一张雷达图**（各自 `id="radar_<sym>"`、各自独立 `echarts.init`），**严禁多标的一张图叠加**。
- **实现**：`quant_block(sym, klines)` 计算单标的六维画像（|Hurst| / |Z| / |Sharpe| / |Sortino| / |偏度| / 日VaR95%）；`radar_option(name, vals, color, area)` 工厂按统一 6 轴（max 1/3/3/4/2/3）生成独立坐标系。
- **本次实战样本**：AUDJPY（Hurst 0.96 / Z −1.54 / Sharpe 0.07 / Sortino 0.07 / 偏度 0.39 / VaR95 0.8%）+ 韩元 USDKRW（Hurst 0.96 / Z −0.97 / Sharpe 0.64 / Sortino 0.66 / 偏度 0.03 / VaR95 1.1%），各自独立雷达，数值与 §七跨市场/4H 技术面读数自洽。
- 报告文件名、标题、页脚、MD、XLSX 版本号统一由 v2.5.1 → v2.5.2。

### ② 引擎新增可复用量化工具（供后续报告直接 import）
- `scripts/decision_enhanced_report_v25.py` 新增 `quant_block(sym, klines)` 与 `radar_option(name, vals, color, area)`。
- 口径与实战报告一致（Hurst 作用于 log 价格序列、Z 为 60 日收盘价窗口、返回绝对值供雷达归一化）。

## v2.5.1 — 引擎级修复（角度 4 真正实现 · 参数口径注释 · 渲染修正）· 2026-09-15

本轮仅更新技能（开源副本 + 已安装副本），**不动 EXE**。
触发场景：AUDJPY 部分平仓（110.20 平 0.01 手，剩余 0.01 手）+ 临时新增韩元（USDKRW）专项分析的实战产出复核。

### ① 角度 4「ATR 波动匹配」此前为空实现 —— 本次真正补全

`evaluate_position()` 的六角度中，角度 4 旧代码恒返回 `None`：

```python
atr_sl_pips = atr_sl_units / pip_scale_guess(sl_pips) if False else None   # 死代码
lots_atr = None
```

即六角度实际只有 **5 个**在参与收敛，但报告文案仍宣称「六角度评估」。本次补全：

- `atr_sl_pips = (atr_mult × atr) ÷ pip`（`pip` 缺省时按 `pip_scale_guess(sl_pips)` 推断）；
- 有效止损距离取 **`max(结构止损, 1.5×ATR)`** —— 波动放大时 1.5×ATR 往往宽于结构止损，此时应**缩减**仓位；
- 按 **1% 风险预算**反推手数，并正式加入收敛候选列表；
- 新增输出字段 `atr` / `atr_sl_pips` / `atr_mult`。

### ② `evaluate_position()` 新增 `pip` 参数 + 参数口径文档

函数 docstring 新增「⚠️ 参数口径（易错点）」段，明确三件事：

| 参数 | 口径 | 典型值 |
|------|------|--------|
| `pip_value_per_std` | **每 0.01 手**每 pip 的账户币价值（函数内 ×100 转标准手） | AUDJPY @USDJPY 154.93 ≈ **0.0645** |
| `sl_pips` | **止损距离（pips）**，不是价格差 | 89 |
| `pip` | 该品种 pip 最小变动单位 | JPY 对 0.01 / XAU·XAG 0.1 / 其余 0.0001 |

重点防范经典误用：**误传每标准手口径的 6.45**（而非 0.0645）→ 手数被缩小 100 倍。

### ③ 渲染修正（⑪·补 六角度表）

- ⑤ ATR 行改为显示**真实手数 / 美元 / 占净值**（旧版为占位 `—`），并在 ATR 成为约束时高亮 `yellow`；
- ④ 组合总额风险行「已占用」改为 `5.00% − 余量` 的**正确值**（旧版硬编码 `0.00%`）。

### ④ 质量口径备忘 —— `quant_block()` 已废弃，勿再复用

实战复核中暴露：**内联 `quant_block()`**（存在于 `decision_enhanced_report.py` / `_20260912.py` / `_v24.py`）有两处口径缺陷：

1. Hurst 算在**收益率**序列上（`h = hurst(rs)`）→ 应算在**价格 / 对数价格**序列上（趋势持续性口径）；且用的是单滞后 `log(R/S)/log(m)` 而非 R/S 回归；
2. Z 用 `(last − mean) / (sd / √n)` 的 **t 统计量**口径 → 会产生 `|Z| ≈ 350950` 之类的荒谬值，应为**滚动窗口 Z-score**。

**处置**：该函数自 **v2.4.1** 起已被 `quant_metrics.py` 取代（`hurst_rs(价格序列)` + 63d 滚动 Z-score），上述内联版本仅存于**归档生成器**，不再复用。新生成器请统一调用 `scripts/quant_metrics.py`。

### ⑤ 本轮实测（AUDJPY 部分平仓 + 韩元专项）

- **止损止盈**：判定 `REASONABLE`；`initRR 3.72` / `restRR 0.22`（原 SL 113.284 口径）；按建议 SL 111.30 口径 `restRR 0.71`、剩余风险 `$5.74 = 0.95%`（≤1% ✓）；浮盈 `+416.2 pip = $26.86`。
- **六角度**：`{kelly 0.0105, cap1pct 0.0105, small05 0.0052, atr 0.0072, portfolio 0.0105, event 0.0}` → 最终 **0.000 手**（约束＝事件静默纪律·一票否决，超级央行周 Fed+BoE+BoJ）。
- **结构校验**：24 节完整（含 四·补 / 六·补 / 十一·补 / 十四·补 / 二十）· `CDN refs: 0` · 14 项数据一致性校验全 PASS。

## v2.5.0 — 决策增强版模板强制规范（冻结模板 + 锚点 patch · 止损止盈评估 · 仓位多角度评估）· 2026-09-14

**对应需求（用户原话）**：「1：技能需要注意，严格按照此模板进行输出，严禁随意调准格式。@"D:/R12/美日输出/FOREX/今日行情分析_决策增强版_2026-09-14.html" 2：止损止盈需要加入合理性评估。3：把使用注意事项放到红色框处。4：仓位评估方面，请从不同角度进行评估，然后输出最终的仓位选择，参照格式图2。5：其他方面按照 kingforex skill 要求进行。」

本轮仅更新技能（开源副本 + 已安装副本），**不动 EXE**。

### ① 模板固化（对应需求 1）—— 「严禁随意调整格式」铁律

- 用户 2026-09-14 交付版 `今日行情分析_决策增强版_2026-09-14.html` **原样冻结**为技能资产 `assets/decision_enhanced_template.html`。
  - 1,203,066 B / 1,182,010 字符，SHA256 前缀 `0431e48d`。
  - 含 20 节结构 + 内嵌 ECharts + 12 个图表容器（`cross` / `chart_XAUUSD` / `chart_EURUSD` / `chart_GBPUSD` / `chart_USDJPY` / `chart_AUDUSD` / `chart_AUDJPY` / `radar` / `hist` / `k_pipinfo` / `corr` / `equity` / `stopcmp` / `rcurve`）。
- **架构转向「冻结模板 + 锚点 patch」（patch-not-rewrite）**：新增 `scripts/decision_enhanced_report_v25.py`，流程为
  `Read 模板 → 字符串锚点定位 → str.replace() 注入/迁移片段 → 输出`，**模板文件零改写，格式零漂移**。
- `SKILL.md` 输出规范新增**首条【最高优先级】强制条款**：禁止改动 CSS 类名 / section 顺序与编号 / 卡片结构 / 配色字体 / 图表容器 id；禁止 rewrite，只能插在既有 section 之间（编号用「X·补」）。
- 原 `assets/decision_enhanced_sample.html` 保留作**内容填充参考**，不再作为格式基准。

三处锚点：

| 变更 | 锚点 |
|------|------|
| ⑪·补 仓位多角度评估 | `<div class="section"><div class="section-title">🔗 十二、收益相关性热力图` |
| ⑭·补 止损止盈合理性评估 | `<div class="section"><div class="section-title">💡 十五、综合判定与操作建议</div>` |
| 凯利注意事项迁移 | 含「三分之一凯利 (保守)」行的 `</table></div>` |

### ② 止损止盈合理性评估（对应需求 2）—— 新增第 ⑭·补 节

- 引擎 `evaluate_sl_tp()`（`scripts/sl_tp_evaluate.py` 同口径）：pip 距离 → **初始 R:R vs 剩余 R:R** → 浮盈（pips/USD/权益占比）→ 单笔美元风险 → SL 方向校验 → ATR 宽度 sanity（1.0×~3.0×）。
- **三级判定** `REASONABLE / CAUTION / UNREASONABLE` + 逐条理由。
- **八类缺陷代码分级**：`SL_REVERSED`(severe，需 `cur_to_sl > 3×cur_to_tp` 确认) / `TRAIL_SUGGEST`(warn) / `REST_RR_BROKEN`(<0.5 severe) / `REST_RR_LOW`(<1.5 warn) / `BAD_INIT_RR` / `OVER_RISK` / `OVER_1PCT` / `SL_TOO_TIGHT` / `SL_TOO_WIDE`。
- **SL 已触发锁利降级逻辑**：`sl_triggered and sl_triggered_pips > 0` → 强制判 `REASONABLE`，并把 `OVER_RISK` / `OVER_1PCT` / `BAD_INIT_RR` 由 severe 降为 warn。
- 重点防范：① 反向移动止损（盈利单把 SL 移回亏损侧，回吐浮盈）；② 剩余 R:R 崩塌（用极大风险博极小剩余空间）。

### ③ 凯利使用注意事项迁移（对应需求 3）—— 从节末移入左卡红框区

- `patch_kelly_notes()` 两步操作：
  1. 定位节底原 `verdict-warn` 块（`凯利公式使用注意` → `rfind('<div class="verdict-warn"')` 至 `再点「重新计算」。</div>`）并整段删除；
  2. 注入第⑪节左侧「凯利公式原理」卡片内红框区 —— 锚点为含「三分之一凯利 (保守)」行的 `</table></div>`，改为 `</table>\n<notes>\n</div>`，即**回测表格正下方**。

### ④ 仓位多角度评估与最终仓位选择（对应需求 4）—— 新增第 ⑪·补 节

- 引擎 `evaluate_position()`，**六角度分别评估**：

  | # | 角度 | 口径 |
  |---|------|------|
  | ① | 凯利理论 | 半凯利，含 1% 硬上限约束 |
  | ② | 1% 单笔风险硬上限 | 纪律红线 |
  | ③ | 0.5% 小账户保守口径 | 净值 < $1000 适用 |
  | ④ | 组合总额风险约束 | ≤ 5%，扣减已占用风险 |
  | ⑤ | ATR 波动匹配 | 波动 regime 适配 |
  | ⑥ | 事件静默纪律 | **一票否决** |

- **收敛规则**：取六角度**最小值**；事件静默**一票否决**；凯利负期望**直接否决**；落地按最小手 0.01 手**向下取整**（**绝不向上取整**）。
- **`below_min_lot` 语义**：理论手数 < 最小手 → 判「不可交易」，并给出最小手对应风险占比解释。输出字段 `pre_floor_lots` / `below_min_lot` / `min_lot` / `min_lot_risk_usd` / `min_lot_risk_pct`。
- **输出格式**：横向六角度评估表 + **唯一绿色高亮推荐表**（`🎯 最终仓位选择: X.XXX 手` + 「项目 \| 具体操作」）。

### ⑤ 实测结论

- **SL/TP**：`REASONABLE`｜`initRR=3.72 restRR=0.17`｜浮盈 `+429.5 pip = $55.46`。
- **仓位六角度**：`{kelly: 0.0118, cap1pct: 0.0118, small05: 0.0059, portfolio: 0.0118, event: 0.0}` → **最终 0.000 手（事件静默一票否决）**。
- 输出 `今日行情分析_决策增强版_2026-09-15.html`（1,182.1 KB，三处 patch 全部 OK，`cdn.jsdelivr.net` 零残留）。

### ⑥ 文档同步

- `SKILL.md`：输出规范新增首条强制条款 + 模板清单重排（`decision_enhanced_template.html` 提为冻结骨架）+ 脚本表新增 v2.5.0 生成器 + 调用示例。
- `references/position_report.md`：新增**第 5.5 节「决策增强版模板强制规范」**（适用范围 / 唯一骨架与 SHA256 / patch 装配三锚点 / 20 节固定顺序 / 凯利注意事项固定位置 / 两个强制模块 / 强制核对清单 / pip 口径统一）+ 演进记录新增 v2.5.0 行。
- 同步至开源副本（`<输出文件>/开源技能/kingforex-skill/`）。
- **脚本计数**：净脚本数 **35 → 36**。

### ⑦ 踩坑记录

- **`%`-格式化陷阱**：`render_sl_tp_section()` 内 `"... 1% 硬上限（%s）"` 触发 `ValueError: unsupported format character '?' (0x786c) at index 13` —— 字面量 `1%` 未转义，`% 硬` 被解析为格式化符。修复：改写为 `1%%`。同一文件中 `总风险上限 5.00%` 等处已预先写成 `%%`，属同类预防。
- **无头截图定位中后部 section**：iframe + `f.onload` 内 `W.scrollTo()` 时序不可靠（截图仍为页首）。改用 `_verify_v25b.py` —— 用 `<div>` 平衡算法把目标 section 整段提取为独立 HTML 页面（带原 `<style>`），再分别截图，三张全部成功。

## v2.4.7 — 新增止损/止盈合理性评估脚本（sl_tp_evaluate.py）· 2026-09-14

**对应需求：用户要求技能增加"止损止盈合理性评估"能力。触发场景为实盘 AUDJPY 空单把 SL 从盈利区(113.284)上移到入场上方(114.90)的离场纪律诊断。**

- **新增 `scripts/sl_tp_evaluate.py`（纯标准库,可选实时价）**：
  - 输入 `--direction BUY/SELL --entry --sl --tp`,可选 `--current`(或 `--symbol` 自动经 AllRatesToday 取实时价)、`--equity --lot --atr --account-currency`。
  - 输出：pip 距离(入场→SL / 入场→TP / 当前→SL / 当前→TP)、初始 R:R、剩余 R:R(持仓已盈利时真正要盯的 R:R)、浮盈(pips + 账户币 + 权益占比)、单笔美元风险(对比 2% 铁律)、SL 方向校验、ATR 宽度 sanity(可选)。
  - **三级判定 REASONABLE / CAUTION / UNREASONABLE** + 逐条理由,重点防范两类典型错误:① 反向移动止损(盈利单把 SL 从盈利侧移回亏损侧,回吐全部浮盈);② 剩余 R:R 崩塌(用极大风险博极小剩余空间)。
  - 自动识别"SL 已触发"(价格已越过 SL → 持仓已平仓锁定利润),此时跳过剩余 R:R 误判,直接判 REASONABLE 并提示离场纪律成立。
  - 美元风险换算:账户=USD 且品种为 JPY/XAU 等时经 AllRatesToday 取 USDJPY 折算;非 USD 账户且报价币≠账户币时降级跳过 $ 指标并提示。
  - 支持 `--json` / `--out`(`.txt`/`.json`)。`py_compile` 通过;四维用例验证(CASE A 反向移动→UNREASONABLE / CASE B 已锁利→REASONABLE / CASE C 正常防护止损→CAUTION / CASE D 自动取价→CAUTION)结论均符合预期。
- **文档同步**：SKILL.md 脚本表新增 `sl_tp_evaluate.py` 条目 + 调用示例;README 脚本目录注释 `34 → 35`;版本号 `v2.4.6 → v2.4.7`。本轮仅更新技能(开源副本 + 已安装副本),不动 EXE。
- **计数变更**：净脚本数 **34 → 35**。

## v2.4.6 — 数据源增删（移除 iTick · 新增 Frankfurter + AllRatesToday · IMA 知识库标注）· 2026-09-14

**对应需求：iTick key 过期需删除；新增 AllRatesToday 实时中间价与 Frankfurter ECB 日参考汇率双源；历史行情复盘可参考用户 IMA 知识库；整理数据源清单。本轮仅更新技能（开源副本 + 已安装副本），不重建 EXE。**

- **删除 iTick 数据源（key 过期）**：
  - 删除 `scripts/itick_fetch.py`（两副本：开源 + 已安装 `~/.workbuddy/skills/kingforex-skill/`）。
  - 同步清理所有文档对 iTick 的引用：SKILL.md（description / 脚本表 / 示例 / 期货分析数据源 / 密钥管理段 / 原则清单 / position_report 调用链）、README.md（数据源列表 / 密钥表 / 脚本计数）、data_sources.md（§7.12 整节改为「已移除」+ 替代源清单；§7.13/§7.15 去 iTick；§7.6 域名 `api.frankfurter.app` → `api.frankfurter.dev`）。
  - **修复脚本硬依赖**（否则删文件后直接崩溃）：`position_report.py` 的 `fetch_quote` 由 iTick 改为 **AllRatesToday 实时中间价**（`--source <base> --target <quote> --json`，以实时 mid 为 price、上一交易日 mid 推算 change/chg_pct，open/high/low 以 price 兜底）；`futures_analysis.py` 的 `_pull_gold` 去掉 `import itick_fetch`，现货端走 goldprice.dev（可选 qveris 现货交叉验证），GC 期货端因无免费源改为 `basis --fut` 手动传入并明确提示。两脚本 `py_compile` 通过、无残留 `import itick_fetch`。
- **新增 Frankfurter（`scripts/frankfurter_fetch.py`，免 key）**：ECB 官方每日参考汇率，`https://api.frankfurter.dev/v1`（旧 `.app` 已 301 失效），30 主权法币、仅工作日、无 XAU；子命令 `latest`/`date`/`timeseries`/`currencies`。服务**日级外汇研判**，与 AllRatesToday 实时中间价互补。data_sources.md 新增 §7.17。
- **新增 AllRatesToday（`scripts/allratestoday_fetch.py`，Bearer Token）**：实时银行间中间价（约 60 秒刷新、160+ 法币、无 XAU），`https://allratestoday.com/api`；子命令 `latest`/`history`/`series`；key 优先级 `--api-key` > `ART_KEY` > `scripts/.art_key`（已落盘 `.art_key` 两副本，不进 zip）。服务**盘中实时监控**，与 Frankfurter 互补。data_sources.md 新增 §7.18。
- **IMA 知识库标注**：历史行情/复盘可参考用户腾讯 IMA 知识库，引用须标注 `[源: IMA 知识库 | 截至: YYYY-MM-DD]`，不作唯一权威源（以实时 API 为准）；写入 data_sources.md §7.7 与 SKILL.md「K 线历史」节。
- **计数变更**：净脚本数 **33 → 34**（−iTick +Frankfurter +AllRatesToday）。README 脚本目录注释、SKILL.md 脚本表、data_sources.md 脚本清单同步。
- **验证**：frankfurter_fetch / allratestoday_fetch 实跑三模式通过（AllRatesToday `AUD->JPY 110.104` 实时）；position_report / futures_analysis 编译通过；全目录 grep 确认无残留 `import itick_fetch`。

## v2.4.5 — ECharts 离线内嵌根治（图表空白 / CDN 外链不可达）· 2026-09-14

**对应需求：09-14 决策增强版报告在大陆网络 / 预览沙箱下 13 张 ECharts 图表全部空白。根因：HTML 头部引用 cdn.jsdelivr.net 外链，该域名在大陆网络与 WorkBuddy 预览环境下不可达。单文件修复验证后，将同一方案根治到技能全部图表链路。**

- **修复范围（7 个脚本 + 2 个资产）**：
  - **类一 · loader 模式（4 个决策增强版生成器）**：`decision_enhanced_report.py` / `decision_enhanced_report_20260912.py` / `decision_enhanced_report_v24.py` / `decision_enhanced_report_v241.py` —— 与 v2.4.2 同款「本地内嵌优先、CDN 回退」加载块（候选路径：输出目录 → `assets/echarts.min.js`），HTML 头部 CDN 行改为 `""" + _ECHARTS_TAG + """` 拼接。
  - **类二 · 后置替换（2 个工具脚本）**：`kline_read.py` / `mtf_confluence.py` 的 HTML 为 %-格式化模板，ECharts 源码含 `%` 不能直接拼入模板串 → 新增模块级 `_inline_echarts(html)` helper，在 `return html` 前把 CDN 标签替换为内嵌块。kline_read 的 `to_html` 与 mtf 的 `to_html_mtf` 主输出均已套用（mtf 另两处 `return html` 为表格片段，不含 CDN，无需处理）。
  - **类三 · 模板链路**：`position_report.py` 在 `fill_template` 之后调用 `_inline_echarts()`（模板 `position_report_template.html` 的 CDN 行保留为回退标记，避免 `__KEY__` 占位替换与 1MB 库源码碰撞）；静态样例 `assets/decision_enhanced_sample.html` 直接内嵌完整库（91KB → 1.12MB，自包含可离线查看；它同时是各生成器的 CSS 来源，`<style>` 切片提取不受影响，已回归验证）。
  - **资产**：`assets/echarts.min.js`（v5.6.0，1,030,185 字符，已验证不含 `</script>`）为全技能唯一图表库来源。
- **验证**：7 个改动 py 全部 `py_compile` 通过；v241 loader 段沙箱执行确认内嵌生效；`kline_read.analyze → to_html` 合成数据端到端跑通（输出 1.04MB 自包含 HTML，`cdn.jsdelivr.net` 零残留）；CRLF/LF 行尾风格逐文件保持。
- **踩坑记录**：kline_read 补丁首版先插 helper 再计数 `    return html`，helper 内 `return html_text` 含该子串导致计数 4≠1 断言中断（save 未执行、文件无损坏）→ 改为**先替换 return 再插 helper**；mtf / position_report 同理按上下文锚点先替换后插入。
- **终态 CDN 分布**：各 py 保留 1 处 CDN 字符串作为回退常量（kline_read / mtf 为 2 处：模板行 + helper 常量，运行时均被内嵌替换），`decision_enhanced_sample.html` 为 0。新生成 HTML 的合格标准：`cdn.jsdelivr.net` 出现 0 次。

## v2.4.4 — 跨机迁移加固（exposure CLI 崩溃 / openpyxl 硬依赖 / 打包配套）· 2026-09-13

**对应需求：把本技能完整迁移到另一台电脑上直接可用。为此对全量脚本做换机可移植性改造，并在新机自检中抓到 2 个新缺陷。**

- **① `exposure.py --help` 崩溃**（与 v2.4.3 修的同类缺陷，上次扫描遗漏）：
  - **现象**：`python exposure.py --help` → `ValueError: unsupported format character ')' (0x29) at index 17`。根因是 `--max-risk` 的 help 写成 `"总风险暴露上限 %% (基于止损%), 默认 5"` —— 开头的 `%%` 是对的，但 `(基于止损%)` 里的 `%` 紧跟 `)`，argparse 做 `help % params` 格式化时炸掉，**整条命令行不可用**。
  - **修复**：`(基于止损%)` → `(基于止损%%)`。
  - **新增全量静态扫描**（AST 提取所有 `help=` / `description=` / `epilog=` 字符串并试运行 `s % {...}`）：本目录 33 个脚本现命中 0 处，根治此类问题。
- **② openpyxl 由硬依赖改为优雅降级**（5 个决策增强报告生成器）：
  - **现象**：`from openpyxl import Workbook` 在文件末尾无条件 import，新机未装 openpyxl 时**在 HTML/MD 都已写完之后**抛 `ModuleNotFoundError`，用户误以为整份报告失败。
  - **修复**：改为 `try / except ImportError`，缺库时打印「XLSX skipped: 未安装 openpyxl …HTML/MD 已正常产出，功能不受影响」并 `raise SystemExit(0)` 干净退出。
- **③ 跨机可移植性改造**（换机直接跑的关键）：
  - 脚本内绝对路径全部改为动态解析：`sys.executable`（Python 解释器）、`os.path.dirname(os.path.abspath(__file__))`（技能目录/资源/输出）、`os.environ.get("TEMP")`（临时目录）。**目标机用户名不同也无需改任何代码**。
  - 报告生成器读取的日线 CSV 归位到 `output/行情分析_YYYYMMDD/`，随包分发。
- **④ 迁移配套交付物**：`请先读我.md`（安装/验证/FAQ/密钥安全须知）、`安装.bat`（GBK+CRLF：一键探测 Python → 复制含隐藏文件 → 装依赖 → 自检）、`自检.py`（8 组 54 项）、`requirements.txt`、`离线依赖/`（openpyxl + et-xmlfile wheel，免联网）、`assets/vendor/echarts.min.js`（离线出图备用）。
- **安装器实测教训**：**不要用 `errorlevel` 判断解释器可用性** —— cmd 的 errorlevel 是有符号数，`py` 启动器失败返回 `0xA0000006`（`%errorlevel%` 显示 2684354566 / 有符号 −1610612730），`if not errorlevel 1` 会判真并**选中坏解释器**。改为**正向输出探测**：候选解释器执行 `sys.version_info>=(3,10) and print(sys.executable)`，只有版本达标才打印路径，再用 `for /f` 捕获，最后校验路径真实存在。

## v2.4.3 — 发布级缺陷修复（CLI 崩溃 / 过期自检 / 数据缺失硬崩）· 2026-09-13

**对应需求:将 v2.4.x 全部更新发布到 GitHub。发布前逐脚本实跑验证时暴露 3 类真实缺陷,一并修复。**

- **① argparse help 中的裸 `%` 导致 `--help` 直接崩溃**(影响 `position_report.py` / `risk_unit.py`):
  - **现象**:执行 `python position_report.py --help` → `ValueError: incomplete format`,argparse 在 `_expand_help()` 里对 help 文本做 `% params` 格式化,裸 `%` 不是合法转换说明符即抛错 → **整条命令行不可用**(不只是帮助信息)。
  - **修复**:`help="单笔风险%"` → `help="单笔风险占净值百分比,输入 2.0 表示 2%%"`;`--dd`、`--risk` 同类问题一并转义为 `%%`。修复后 `--help` 与参数校验报错均正常输出。
- **② `calc_engine.py` 自检残留过期汇率与陈旧口径**(文档与实跑结果自相矛盾):
  - **现象**:`--help`/自检输出仍写「每 pip 价值 = $0.1809(v2.3 误写 0.864,修正后≈0.0905×2=0.181)」——该值基于 `USDJPY=110.54`(2022 年水平),与 v2.4 起采用的实时口径 **$0.1303 @ USDJPY 153.478** 冲突;自检止损距离仍用 116 pip(v2.4.2 已修正为 32.7 pip)。
  - **修复**:自检块示例汇率更新为 `USDJPY = 153.478` 并显式标注"示例值,实盘请传当日结算汇率";现价 110.54 → 110.121、止损 116 → 32.7;输出文案改为「(实时计算 | lot_unit × pip / USDJPY)」;一致性校验演示的"已修正"用例 `score_total` 由 80 改为 79.75(与 25/30/25/20 加权和一致),使该用例真正返回空 issue 列表。
  - **修复后自检实测**:`每pip价值 = $0.1303` / `浮盈(114.573→110.121) = $58.01` / `1%风险·止损32.7pip 手数 = 0.0270 手` / `凯利 全42.23%·半21.11%·三14.08%,最终 0.02 手(用户上限)` / `评分 68.00 判定观望` / `故意矛盾 → 2 项 issue,已修正 → []`。全部与 v2.4.2 报告一致。
- **③ 5 个决策增强报告生成器在缺 K 线时 `IndexError` 硬崩**(影响 `decision_enhanced_report.py` / `_20260912` / `_v24` / `_v241` / `_v242`):
  - **现象**:脚本从 `OUT` 目录读取 6 个品种日线 CSV(`KD` 字典),文件缺失时 `klines[sym]` 为空列表 → `IndexError: list index out of range`(`ENG["now_px"] = round(klines["AUDJPY"][-1][4], 3)`),报错信息完全无法指向真实原因。
  - **修复**:在 `klines` 载入后插入数据存在性守卫,缺失时 `SystemExit` 输出**缺失品种清单 + 预期目录 + 预期文件名 + `kline_fetch.py` 获取命令**,不再裸崩。
- **④ 开源发布配套**:`scripts/` 33 个脚本、`references/` 18 份方法论、`assets/` 6 份模板全量脱敏(个人绝对路径 → 相对路径 / `sys.executable` / `os.path.dirname(__file__)` 动态解析),密钥本地便利文件与缓存目录强制排除;新增仓库级 `README.md` / `LICENSE` / `.gitignore`;`README` 计数与模块清单同步至 v2.4.3。

## v2.4.2 — 章节序号互换 + 凯利注意事项归位 + 凯利计算器 Bug 修复 · 2026-09-13

**对应需求:①「数据一致性校验报告」与「交易纪律」两个模块序号互换; ②「凯利公式使用注意」提示框移至第⑪节左面板底部; ③凯利计算器改 4 项参数后点「重新计算」下方无反应 —— 排查并修复。**

- **① 序号互换**:第十九节 = 数据一致性校验报告、第二十节 = 交易纪律(永远置末)。修正了 v2.4 引入的「十八 → 二十 → 十九」序号错乱,现视觉与编号一致(十八引用 → 十九校验 → 二十纪律置末),HTML/MD 同步。
- **② 注意事项归位**:「💡 凯利公式使用注意」由第⑪节底部(横跨整节)移入**左面板「凯利公式原理」卡片底部**(三分之一凯利行下方),与右侧「本账户仓位测算」并列,版面更紧凑、不必跨列阅读。
- **③ 凯利计算器 Bug(确认存在,已修复)**:
  - **根因 1（无反应的直接原因）**:`o_cur`(超配%)与 `o_act`(建议操作)在 JS 中对 AUDJPY 分支**硬编码**为「超配 150%」「减至 0.01 手(接近半凯利)」→ 无论净值/胜率/盈亏比/风险偏好怎么改,这两行**永不更新**。
  - **根因 2（看起来没生效）**:`fcap=0.01` 把凯利档位**静默压回** 1% 硬上限且界面不作说明 → 用户选「全凯利/三分之一凯利」时"最优仓位比例"恒显示 1.0%,误判为无反应。
  - **修复**:重写 `calcKelly()` — ①持仓对比**动态计算** 超配/低配 = (当前手数/推荐手数−1)×100%;②明确标注"凯利档 X% · 约束:1% 硬上限/凯利档位";③新增**负期望否决**提示(0 手 + 平仓观望);④新增**小账户 0.5% 口径**对照行;⑤`INST.AUDJPY.sl` 116 → 32.7(与报告 SL 114.90 口径一致)。
  - **修复后实测**(node mock 浏览器点击):净值 10000 / 胜率 70% / 盈亏比 100 / 三分之一凯利 / 止损 55 → 最优仓位 1.00%(凯利档 23.21% · 约束 1% 硬上限)、最大可亏 $100.00、推荐 **0.279 手**、当前 0.02 手 → **合规 ✓(上限 0.279 手)**、建议"维持当前手数(≤0.5% 口径 0.139 手)";负期望场景正确输出"0.000 手(负期望 · 否决) + 平仓观望"。
- 输出 `今日行情分析_决策增强版_v2.4.2_2026-09-13.html`(23 节 / 13 图 / 一致性校验 10 项全 PASS)+ MD + XLSX,已复制`./output/`。

## v2.4.1 — 雷达图口径修正 + 量化验证按模板重构 · 2026-09-13

**对应需求:用户反馈三处问题 —— ①建仓判定需逐项起行; ②量化雷达图异常; ③量化验证按参考模板（双标的雷达 + 收益分布 + 6.1/6.2/6.3 指标表 + 结论）重做。**

- **修复雷达图异常（根因:指标口径错误 + 量程失配）**:
  - 旧 `quant_block()` 把 Hurst 算在**收益率序列**上（应算在价格序列），且 Z 用 `(last-mean)/(sd/√n)` 的 **t 统计量**口径（应为 63 日滚动 Z-score）→ 6 轴中只有 2 轴有值、其余接近 0，雷达多边形被拉成**细长条**（视觉异常）。
  - 现改用 `quant_metrics.py` 引擎真实计算：`hurst_rs(price)`、`rolling_zscore(price,63)`、`annualized_metrics`、`max_drawdown`、`distribution_stats`、`var_cvar`、`ewma_variance`、`realized_vol`。
  - 雷达改为 **AUDJPY vs XAUUSD 双多边形 + 6 轴 0-100 归一化**（年化波动÷30% / 最大回撤÷40% / 下行偏差÷25% / |偏度|÷1.5 / |Z63|÷3 / 日VaR95÷5%），形状恢复为正常多边形。
  - 实测值：AUDJPY [23.5, 10.4, 20.9, 26.7, 67.0, 16.4]；XAUUSD [74.4, 63.5, 67.8, 12.3, 8.8, 54.8]。Hurst 0.920（真实）、Z63 **-2.01**（原误报 -1.81）、VaR95 0.819%。
- **第⑨节按参考模板重构**:新增 `📊 日对数收益分布（直方图）`（±5% / 20 bins，双标的并排）+ **6.1 AUDJPY 200 根**（收益风险/回撤/分布/尾部/波动/时序 7 行）+ **6.2 XAUUSD 200 根 + CFTC 拥挤度**（7 行）+ **6.3 量化结论**（4 维度 + 框架引用）。版面仍复用 `.grid grid-3` / `.journal-table` / `.chart-box`，无新增 CSS。
- **接入 CFTC 真实数据**（`cftc_fetch.py --symbol GOLD`）：报告日 2026-09-01，投机多 149,721 / 空 12,950 → 净多 **136,771 手**（净多/总持仓 32.94%），52 周分位 **89.22%**（偏拥挤·做多），周环比 **ΔNet -7,976 手**。
- **新增风险量化**:单日 95% 分位风险 —— AUDJPY 0.02 手 ≈ **$11.75**（占账户 2.05%）；XAUUSD 0.01 手（1 盎司）≈ **$118.80**（占账户 **20.69%**，远超 1% 上限）→ 结论：当前账户规模不可参与黄金。
- **建仓判定改逐项起行**:① 宏观 / ② 评分 / ③ 凯利 / ④ 事件 各占一行（HTML + MD 双同步）。
- **一致性校验**:仍为 10 项全 PASS、0 issue；输出 `今日行情分析_决策增强版_v2.4.1_2026-09-13.html`（23 节 / **13 图**）+ MD（311 行）+ XLSX，已复制`./output/`。

## v2.4 — v2.3 版面冻结 + 统一计算引擎注入（微调版） · 2026-09-13

**对应需求:在 v2.3 基础上适当微调（禁止大幅改动、版面须与 v2.3 一致），但必须落实 统一计算引擎与一致性校验要求。**

- **版面条线**:19 节 DOM/CSS/JS/图表/配色/交互零改动;仅新增 3 个「补充节」插在原有节之间,全部复用既有 `section`/`journal-table`/`card` 类:
  - 四·补 AUDJPY 评分模型子项明细(维度/子项/标准化分/维内均值/加权分)
  - 六·补 事件静默自动计算(事件/时间/星级/**距基准小时数**/新开仓/24h清仓窗口)
  - 二十、数据一致性校验报告(10 项 PASS/FAIL 表)
- **新增 `scripts/decision_enhanced_report_v24.py`**:由 v2.3 生成器复制,顶部接入 `calc_engine.py`(单一事实来源),所有关键数字由统一函数产出:
  - `pip_value_per_pip` → AUDJPY 0.02 手 $0.1303/pip、0.01 手 $0.0652/pip(禁写死)
  - `pnl` → 浮盈 $58.01(445.2 pips × $0.1303 × 0.02 手)
  - `compute_lots` → 1% 风险上限 0.027 手、0.5% 小账户 0.0135 手
  - `kelly_recommended_lots` → 全凯利 42.23% / 半凯利 21.11%(对应 0.5691 手,**禁止实盘**) / 最终 = min(凯利档, 1%风险, 用户上限);**已删除「最优仓位 20%」误导表述**
  - `corr_matrix` → 相关性文字由 60 日 Pearson 矩阵实时生成(修复 v2.3「文字 -0.78 vs 矩阵 0.44」矛盾)
  - `score_4d` → 子项明细可复盘,维内均值→加权求和→总分 66.90,**总分 = Σ维分×权重** 可校验
  - `event_silence` → 距 FOMC 96.92h / BoJ 129.92h 自动判定,24h 清仓窗口触发点 09-16 02:00 / 09-17 11:00(北京)
  - `backtest` → 样本 12 笔 <100,**年化预测已封禁**(删除 v2.3 的「年化 +27%~+41%」)
  - `consistency_check` → 10 项校验**全部 PASS、0 issue**
- **单一事实来源**:AUDJPY 现价统一为日线最后收盘 **110.121**(快照 = 图表最后收盘 = 计算器价),消除 v2.3 的 110.46967/110.54/110.47 三处不一致。
- **风控结论**:原 SL 113.284 在盈利区(非保护)且风险 2.93% 超上限 → 强制修正 SL 至 **114.90**;修正后 0.02 手风险 $4.26(0.74%)、0.01 手 $2.13(0.37%) 均 ≤1%。
- **输出**:`./output/行情分析_20260912/今日行情分析_决策增强版_v2.4_2026-09-13.html`(23 节/12 图,node --check 通过)+ MD(274 行)+ 复盘 XLSX;已交付到本地产出目录。

## v2.3 模板回滚重出 — 2026-09-12(决策增强版 v2.3 · 2026-09-12 期)

**对应需求:用户裁定 v3.0 违反「界面冻结」(自建 8 节版面替代了已冻结的 v2.3 19 节模板),要求立即回到 v2.3 模板严格输出并重新优化。**

- **新增 `scripts/decision_enhanced_report_20260912.py`**:完整复制 v2.3 生成器(19 节 DOM+样式逐字节保留),仅更新数据块与叙述至 2026-09-12 / 下周(09-14~09-20)真实数据:FOMC 09-16(料 −25bp)+BoJ 09-17~18(料 +25bp 至 1.25%)双议息周、USDJPY 153.478、AUDJPY 现价 110.04(K线 200 根最新 110.123)、浮盈 +453pips/+$59.03(+10.29%)、单笔风险 2.93%(0.02手×128.9pip×$0.1303/pip)。
- **风险修正全报告贯穿**:原 SL 113.284 位于入场 114.573 下方=盈利区(非保护性止损)→ 推荐新 SL 114.90(入场上方 33pips);09-15 前平 50% 锁 +$29.5 → 剩余风险 $2.13(0.37%)达标 ≤1%。凯利 pip 价值按 0.01 手口径 $0.0652 修正。
- **输出**:`./output/行情分析_20260912/` 下 HTML(19 节/12 ECharts,node --check 通过)+ MD(235 行)+ 复盘 XLSX;同步复制至 `./output/`。
- **模板纪律**:v2.3 的 19 节版面为冻结模板;后续任何版本(v3.x)只允许注入数据,不得重排版面。v3.0 流水线(report_agent_v3.py)已归档至 `_archive/v3_obsolete/`,渲染层须回落 v2.3 DOM。

> ⚠️ **v3.0 已归档**：`scripts/report_agent_v3.py` 与 `references/v3_spec.md` 已移至 `_archive/v3_obsolete/`，本技能当前版本线为 **v2.7.0**，不再保留 v3.0 全自动 Agent 功能。以下章节仅作历史记录保留。

> ⚠️ **v3.0 已归档**：`scripts/report_agent_v3.py` 与 `references/v3_spec.md` 已移至 `_archive/v3_obsolete/`，本技能当前版本线为 **v2.7.0**，不再保留 v3.0 全自动 Agent 功能。以下章节仅作历史记录保留。

## v3.0 — 全自动模板填充 Agent + 统一计算引擎(修复 v2.3 全部计算矛盾) · 2026-09-12

**对应需求:用户提供 v3.0 完整 Agent 规范(角色/原则/数据层/计算引擎/八步流水线/一致性校验/交付物),要求对技能再次优化并输出分析文档。**

- **新增 `scripts/calc_engine.py` 统一计算引擎(单一事实来源)**:合约规格表(pip 价值实时计算,禁写死)、`pip_value_per_pip`、`pnl`、`compute_lots`(风险预算反推+1%硬上限压回)、`kelly`(f*=(p×b−q)/b+负期望否决)、`kelly_recommended_lots`(最终=min(凯利档,1%风险,用户上限),禁理论全凯利当实盘/禁「最优仓位20%」误导)、`corr_matrix`(60日Pearson,文字由矩阵实时生成)、`score_4d`(四维25/30/25/20+可量化子项明细,修复黑箱)、`event_silence`(4h/24h静默)、`backtest`(样本<100禁年化预测)、`consistency_check`(第八章校验清单)。
- **修复 v2.3 模板矛盾(经引擎自检验证)**:① pip 价值 $0.864/0.01手 → 实测 $0.1809/0.02手(AUDJPY,差数量级已纠);② AUDJPY 现价三处不一致(110.46967/110.54/110.47)→ 一致性校验自动标红;③ 凯利「20%」误导 → 改为 min 约束手数;④ 相关性文字 -0.78 vs 矩阵 0.44 → 文字由矩阵生成;⑤ 回测 12 笔给 +27%~+41% 年化 → 样本<100 禁止预测;⑥ 评分黑箱 → 四维子项明细。
- **新增 `scripts/report_agent_v3.py` 八步编排器**:①采集(MCP/API 降级)②校验③指标④评分⑤决策(任一不满足→不建议)⑥持仓管理⑦一致性校验⑧渲染。**界面冻结**:复用 v2.3 模板 `<style>`+19 节 DOM 骨架,仅注入标准 JSON,不改动界面代码。输出 HTML+标准JSON+执行清单+一致性校验报告+数据源状态报告。
- **实测暴露真实风险**:当前 AUDJPY 0.02 手、止损 128.9 pip → 单笔风险 **4.06%**,违反 1% 硬上限;v3.0 一致性校验已自动标红(v2.3 模板把该风险埋没)。
- **新增 `references/v3_spec.md`**:完整存档 v3.0 规范(角色/核心原则/数据层/计算引擎/流水线/一致性校验清单/异常处理/禁止事项/交付物/合规声明)。
- 技能文档同步:SKILL.md(计算脚本清单加 calc_engine+report_agent_v3、模板段落加 v3.0 Agent 说明)、references/position_report.md 演进记录加 v3.0 行。

## v3.0.1 — 数据采集管道修复(真实数据贯通) · 2026-09-12

**对应需求:用户要求「按照3.0版本要求输出」下周分析报告;实测发现 report_agent_v3.py 多数数据源解析失败,真实数据无法注入,USDJPY 静默回落 stale 110.54 导致风险误报 4.06%。**

- **修复 `collect_quotes`**:live_market_fetch 输出为 CSV(非 JSON),原 `json.loads` 永远失败 → 改为解析 CSV 取 `USD+币种`,并用 jin10 实时兜底 `USDJPY`/`XAUUSD`。现 USDJPY 取真实 **153.478**(致金JPY 实际 pip 价值 $0.1303/0.02手,单笔风险修正为 **2.93%**)。
- **修复 `collect_rates`**:fred_fetch 输出为文本(行如 `DGS10: 4.95`),原 JSON 解析失败 → 正则提取 `系列:数值`,现 FRED 8 字段生效(DGS10 4.95 / DFII10 2.55 / T10YIE 2.36 …)。
- **修复 `collect_central_banks`**:bis_fetch 输出为 CSV,原 JSON 解析失败 → 按 `REF_AREA→OBS_VALUE` 解析,现 BIS 4 央行生效(Fed 3.625 / BoE 3.75 / BoJ 1.0 / RBA 4.35)。
- **修复 `collect_calendar`**:jin10 返回 `{"data":[...]}` 字典,原取列表失败 → 改取 `j.get("data")`,现 231 事件生效(含五星事件触发 24h 静默)。
- **修复 `collect_klines`**:kline_fetch 无 `--count` 参数且非 `--json` 时输出人类可读文本 → 改用 `--json` 取收盘序列;并将 `insts` 从 166 个 USD 交叉(不含 AUDJPY)改为固定真实标的列表(含持仓 AUDJPY)。
- **新增 AUDJPY 三角套利兜底**:`AUDJPY = AUDUSD × USDJPY`,当直接报价/K线缺失或 Twelve Data 免费配额耗尽时仍能算持仓浮盈/风险。
- **效果**:v3.0 流水线现贯通真实数据;一致性校验正确标红 `单笔风险超 1%: 2.93%`;持仓浮盈 +$59.03;verdict=不建议建仓(评分<75)。输出 `今日行情分析_v3.0_2026-09-12.html` + `v3_data_*.json` + `v3_consistency_*.txt`。

## v2.3 — 八项模板升级 + 凯利公式融入仓位控制 · 2026-09-11

**对应需求:用户提供 8 张参考图提出 8 项模板改动(评分卡 4×2/宏观列表化/凯利多标的下拉/引用位置/综合判定模板/快照扩列/宏观内容扩充/版本升级),并追加要求把凯利公式逻辑融合进 position_size.py 的仓位控制计算。**

- **①8标的综合评分卡改 4×2 排列**:`grid grid-4` 两行八列,替代旧三列布局,标题标注「· 4×2排列」。
- **②宏观大事综合改为列表/表格形式**:每标的 2 条事件,格式 `【标的】事件 → 明确影响陈述`(加粗结论句),替代原卡片叙述。
- **③凯利仓位计算器新增投资标的下拉框**:`<select id="k_inst">` 覆盖全部 7 个可交易标的(AUDJPY/USDJPY/EURUSD/GBPUSD/XAUUSD/XAGUSD/USOIL);JS `INST` 配置对象按标的维护 pip 值/止损距离/现价,`onInst()` 切换时联动更新输入框、pip 说明行并重算 `calcKelly()`;AUDJPY 显示「超配150%」持仓警示行,其余标的显示「未持仓·新开仓评估」。
- **④引用与依据移至倒数第二**:节序调整为 十六交易决策日志 → 十七信号历史回测 → **十八引用与依据** → 十九交易纪律,纪律永远置末。
- **⑤综合判定与操作建议按参考图5模板重构**:15.1 持仓诊断 4 迷你卡(浮盈状态/至TP·至原SL距离/三周期方向/事件风险)、15.2 三种情景卡(A激进否决/B稳健推荐/C硬扛不接受)+最终推荐表(7 行项目/具体操作)、15.3 其余 7 标的判定 + 今日总判定绿框。
- **⑥分析标的快照扩列**:7 列(标的/现价/日内%/日内区间/趋势结构/MTF方向/计划判定)+ 日内主轴横幅;现价/日内%/区间由 Twelve Data 真实 K 线末两根日线计算(非 K 线标的用参考值)。
- **⑦宏观金融面解读扩充**:新增 5.1 央行政策对比表(Fed/ECB/BoJ/BoE/RBA × 政策利率/最近动作/周期定位/对市场)、5.3 利差结构加「趋势」列与套息结论横幅、5.4 地缘风险 4 卡(中东红海/通胀回潮/日本变量/风险偏好);当日数据节新增 6.1 今日已公布(7 行)、6.2 今日待公布(8 行含星级)、6.3 议息提醒(3 央行)三表 + 事件纪律横幅。
- **⑧position_size.py 融合凯利公式**:新增 `--winrate/--payoff/--kelly-mode{full,half,third}` 参数;核心逻辑 f* = (p×b−q)/b,输出 full/half/third 三档凯利百分比;**三重约束取最小** `有效风险% = min(纪律风险%, 凯利档位%, 1%硬上限)` 并标注约束来源;**负期望否决**——f*≤0 时直接输出 0 手不开仓;保留传统(非凯利)模式回归兼容。实测:p=62.5%/b=1.85 → f*=42.23%/半凯利 21.11%/有效风险 1.000%(1% 纪律约束生效);p=40%/b=1.0 → 否决 0 手。
- **生成器更新**:`scripts/decision_enhanced_report.py` 升级为 v2.3(1172 行);产物 `今日行情分析_决策增强版_v2.3_2026-09-11.html(153KB)/md` + `交易复盘模板_v2.3.xlsx`,node --check 通过,19 节顺序、12 图表容器/初始化、6 个凯利下拉标记全部校验通过。

## v2.2 — 模块顺序按分析/交易逻辑重排 + 新增今日交易计划/综合判定/交易纪律 · 2026-09-11

**对应需求:用户提供 3 张参考图,要求模块保持不变但重排顺序——决策总览第一、建仓/持仓计划第二(不适宜建仓须明确声明)、其余按分析→交易逻辑调序、综合判定须有指定模块、日志与回测放最后、交易纪律按图执行并置报告末尾。**

- **报告结构重排为 19 节固定顺序**:一、今日决策总览 → 二、今日交易计划(建仓/持仓判定) → 三、分析标的快照 → 四、8标的综合评分卡 → 五、宏观金融面解读 → 六、当日重要数据+议息 → 七、跨市场验证 → 八、多周期共振(K线+关键位) → 九、量化验证 → 十、概率情景预案 → 十一、凯利仓位计算器 → 十二、相关性热力图 → 十三、账户风险仪表盘 → 十四、动态止损方案对比 → 十五、综合判定与操作建议 → 十六、引用与依据 → 十七、交易决策日志 → 十八、信号历史回测 → 十九、交易纪律(永远置末)。
- **新增第二节「今日交易计划（建仓/持仓判定）」**:先给建仓判定框——不适宜建仓时明确「不建仓」并给四维否决理由(宏观/评分/凯利/拥挤度);再给持仓计划表(参考图1版式: 交易标的/方向手数/入场价时间/止损止盈/入场核心理由3条/信心指数/情绪状态/最大当前浮盈/当前状态/离场计划/可能出错的地方)。
- **新增第十五节「综合判定与操作建议」(参考图2)**:最终推荐(情景B·进取派, 5 条编号操作)+「其余 7 标的判定」表(标的/判定/理由, 不建议建仓红/观望黄)+「今日总判定」绿框(空仓即结论, 错过即纪律)。
- **交易纪律改为参考图3版式并置末**:顶部「最核心铁律: 风控第一, 盈利第二; 纪律第一, 机会第二」横幅 + 当日纪律提示, 下接 6 类 × 4 条纪律卡——仓位纪律(单笔≤1%/组合≤5%/凯利半仓/不加仓逆势)、入场纪律(评分≥75/止损前置1.5×ATR/RR≥1.5/事件前4h不开新仓)、持仓纪律(浮盈≥2R平50%/移动SL只向盈利/议息前24h清仓/绝不摊平)、离场纪律(2R平50%→3R再平30%→跟踪/SL触发不犹豫/事件后15分钟不决策/结构破位全平)、复盘纪律(每笔写日志/每周更新凯利/每月回顾系统/连亏3次停24h)、心理纪律(不贪最后一段/不报复市场/只应对不预测/错过即纪律)。
- **日志与回测移至末段**:交易决策日志(十七)、信号历史回测(十八)紧随综合判定与引用之后, 纪律(十九)置报告最末。
- **生成器更新**:`scripts/decision_enhanced_report.py` 升级为 v2.2(各节构建为独立变量后按序拼装, 便于后续调整节序); 产物 `今日行情分析_决策增强版_v2.2_2026-09-11.html/md` + `交易复盘模板_v2.2.xlsx`, node --check 通过, 19 节顺序与 12 图表容器/初始化校验通过。

## v2.1 — 决策增强 9 模块参考模板重排 + 独立 Excel 复盘模板 · 2026-09-11

**对应需求:用户提供 8 张参考图,要求将决策增强 9 模块逐一按目标版式重排,并新增独立 Excel 复盘模板,重新优化升级技能。**

- **①今日决策总览 → 4 卡片横排**:账户状态(净值+浮盈+持仓风险进度条/上限5%)、今日信号质量(B+评级+可交易/观望标的计数)、凯利最优仓位(推荐手数+f*+当前超配%+减仓建议)、今日最大风险(CPI 五星+预期波动±50-80pips+减仓纪律)。
- **②概率加权情景预案 → 表格化**:三情景(基准/反弹/尾部)由色块卡片改为 5 列表格(情景/概率/触发路径/操作/预期结果),路径与操作分栏更清晰。
- **③凯利仓位计算器 → 左公式右交互双面板**:左侧凯利公式原理(f*=(p×b−q)/b + 半凯利建议 + AUDJPY 60日线回测参数 p/b/f*/半凯利/三分之一凯利),右侧本账户仓位测算(账户净值/胜率/盈亏比/止损距离/风险偏好下拉 交互输入 + 重新计算按钮 + 最优仓位/最大可亏/推荐手数/超配警示/建议操作),底部「凯利使用注意」三条。
- **④收益相关性热力图 → 增加 3 列解读面板**:高度正相关(风险集中,XAU↔XAG 0.92/EUR↔GBP 0.85/AUDJPY↔USDJPY -0.78)、低相关(分散风险,USOIL↔AUDJPY 0.12/XAU↔EUR 0.35/DXY↔XAU -0.68)、今日组合诊断(当前持仓/相关性集中度/隐含暴露/风险提示/建议)。
- **⑤账户风险仪表盘 → 4 指标卡 + 权益曲线 + 风险预警框**:账户净值(入金+浮盈+累计收益)、单笔风险(剩余仓位@SL+占比进度条)、组合风险(相关性调整后+总风险进度条)、最大回撤(阈值黄/红灯+安全区),下接账户权益曲线(模拟,含入金虚线)+「⚠风险预警(共N项)」黄色警示框(单笔风险超标等)。
- **⑥动态止损方案对比 → 柱状图 + 对比表 + 推荐绿框**:三方案分组柱状图(风险$/被扫概率%/保住利润分),对比表(止损位/止损距离/单笔风险/被扫概率/保住利润/适用场景,推荐列绿色高亮),底部「最终推荐」绿色 verdict 框(移动止损+分批止盈分步操作+核心逻辑)。
- **⑦交易决策日志 → 表格化**:当前持仓日志表(交易标的/方向手数/入场价时间/止损止盈/入场核心理由3条/信心指数/情绪状态/最大当前浮盈/当前状态/离场计划/可能出错的地方)。
- **⑧信号历史回测 → 整体面板 + R曲线 + 明细表 + 结论4列**:策略整体表现面板(总次数/胜负/胜率/盈亏比/期望/连胜连败/回撤/利润因子),R乘数资金曲线图,近期信号明细表(#/时间/标的/方向/入场价/出场价/盈亏/R倍数/结果),回测结论与优化方向 4 列卡(策略有效/需要警惕/优化方向/长期预测)。
- **⑨新增独立 Excel 复盘模板**:4 工作表(交易复盘记录 18列+示例行+20空行模板 / R乘数统计(策略统计+信号明细) / 复盘问题清单(每笔10问) / 每周复盘汇总),openpyxl 生成,表头蓝底白字+边框+冻结首行。
- **生成器沉淀**:新增 `scripts/decision_enhanced_report.py`(v2.1 决策增强报告一键生成器,922 行,HTML+MD+XLSX 三件套输出,全部 ECharts option 用 json.dumps 注入,`node --check` 通过,12 个图表容器与初始化一一对应校验通过)。实战产物: `今日行情分析_决策增强版_v2.1_2026-09-11.html/md` + `交易复盘模板_v2.1.xlsx`。

## v2.0 — 决策增强版（融合博士 v2.0 + v1.4.3 框架）· 2026-09-11

**对应需求:用户将博士修改的「决策增强版 v2.0」与 v1.4.3 框架融合,产出 skill 最新版本。**

- **决策增强 9 模块(v2.0 核心,置于九大节骨架之上)**:①今日决策总览(账户状态/信号质量/凯利仓位/最大风险 + 一句话结论) ②8 标的综合评分卡(宏观25%+技术30%+量化25%+情绪20% 四维加权,≥75 可建仓 / 60-74 观望 / <60 回避) ③概率加权情景预案(三情景 + 概率,只准备不预测) ④凯利仓位计算器(公式 f*=(p·b−q)/b + 回测参数 + 交互式输入) ⑤品种相关性矩阵(60 日收益率热力图 + 组合诊断) ⑥账户风险仪表盘(权益曲线模拟 + 单笔/组合/回撤风险条) ⑦动态止损方案对比(ATR/结构/移动 三方案 + 图表) ⑧交易决策日志(当前持仓明细 + 复盘模板) ⑨信号历史回测(策略表现 + R 乘数资金曲线 + 信号明细表)。
- **融合 v1.4.3 修复并完整保留**:雷达图 radius 55%/center 54% 防边界溢出(§六 量化验证);关键位统一表格(品种/关键位/类型/作用,§五 5.2,不再用 V2.0 残留的小方块);最终推荐强制附「抉择依据」(§七),说明为何选该情景而非其他。
- **模板与样本**:`assets/position_report_template.html` 升级为 v2.0(九大节 + 9 决策增强模块);新增 `assets/decision_enhanced_sample.html`(2026-09-11 八标的 + AUDJPY 持仓实战样本,含全部交互 JS,`node --check` 通过);`scripts/position_report.py` 生成器同步输出决策增强摘要(决策总览卡 + 单标的评分卡 + 凯利 + 风险仪表盘 + 动态止损对比 + 交易日志)。

## v1.4.3 — 雷达图/关键位表格/方案抉择依据优化 · 2026-09-11

**对应需求:用户对 2026-09-11 今日行情分析报告的版面提出 3 处微调,优化可视化边界、提升方案透明度、统一关键位呈现形式。**

- **雷达图防边界溢出(v1.4.3 新增)**:`assets/position_report_template.html` 中 radar 的 `radius` 从 `68%` 收紧至 `55%`,`center` 从 `['50%','56%']` 调整为 `['50%','54%]`;同时 `.chart-small` 高度从 320px 提升至 360px,确保 tooltip 与图例不超出容器边界。
- **最终推荐加「抉择依据」(v1.4.3 新增)**:第⑦节「最终推荐」标题下方必须追加抉择依据段落,用 A/B/C 三情景对比句式明确说明为何选 B(进取派)不选 A(稳健派)或 C(激进派),禁止只给结论不给理由;同步修改 `scripts/position_report.py` 填充 `__RECOMMENDATION_RATIONALE__` 占位符。
- **关键位改为表格(v1.4.3 修正 v1.4.2 规范落地不一致)**:`assets/position_report_template.html` 第⑤节 5.2 的 `key-levels` 小方块卡片改为 `<table>`(品种/关键位/类型/作用),与 `references/position_report.md` §3.5 规范一致;`scripts/position_report.py` 同步输出 `<tr>` 格式。
- **影响**:本次重出的「今日行情分析_2026-09-11」按 v1.4.3 模板生成,作为新模板实战样本;一键生成器 `position_report.py` 已同步适配表格关键位与抉择依据。

## v1.4.2 — 默认标的/利差/关键位/宏观大事/交易计划判定细化 · 2026-09-10

**对应需求:用户基于 4 张截图对报告模板提出 5 条细化规则,将多品种交易计划标准化为 8 标的一锅端输出,并强化「可交易才给计划,不可交易直接不建议建仓」的纪律。**

- **默认投资标的(v1.4.2 新增)**:用户未指定时,多品种交易计划默认覆盖 8 个标的——金(XAUUSD)、银(XAGUSD)、美元(DXY)、欧元(EURUSD)、英镑(GBPUSD)、日元(USDJPY)、WTI 原油(USOIL) + 当日「利差最大的货币对」(动态,常见 AUDJPY/USDJPY,与已有标的不重复);用户指定标的时按指定覆盖,第 8 位仍优先用利差最大货币对补足。
- **利差结构表(v1.4.2 新增)**:第②节 2.2 固定 3 行——US 2s10s + 两个利差最大的货币对利差(如 US 10Y−JP 10Y、AU−JP 利差),明确套息/反套息对日元交叉盘与商品货币的影响。
- **关键位表格化(v1.4.2 新增)**:第⑤节 5.2 每个标的只列 1 个最关键位,用统一表格区分品种,类型仅「支撑/阻力/中枢」三选一,并注明触发条件。
- **宏观大事综合(v1.4.2 新增)**:第②节 2.4 每个标的必须列出 2 条影响最大的宏观事项,格式为 `【XAUUSD】① ... ② ...`,事项具体且给出差异化影响路径。
- **交易计划判定规则(v1.4.2 重大调整)**:第⑦节不再默认给交易计划,改为按可交易性二选一:
  - **可交易**:三维共振 + 结构触发 + 风险可控 → 输出完整交易计划表,并**强制包含明确平仓计划**(何时平 50%、移动止损、何时全平、计划失效条件);
  - **不建议建仓**:三维未共振/信号冲突/事件窗口流动性差/ATR 过大/无合格 RR → 直接输出「不建议建仓」并给出 2-3 条具体理由。
- **更新 SKILL.md 输出规范**:把上述 5 条规则写入「输出规范(强制)」,并同步更新 `references/position_report.md` 模板说明与演进记录。
- **后续影响**:本次重出的「八品种交易计划(2026-09-10)」将按 v1.4.2 规则生成,作为新模板实战样本。

## v1.4.1 — 分析报告模板强制化(覆盖所有报告) · 2026-09-10

**对应需求:用户再次明确「后续强制按照此模板输出每次的分析报告」,将 v1.4.0 的持仓报告模板升级为本技能唯一批准的分析报告骨架,适用范围从"持仓诊断"扩展到全部分析报告。**

- **SKILL.md「输出规范(强制)」新增最高优先级铁律**:
  - 任何"分析报告"类输出(持仓深度诊断 / 多品种·单品种交易计划 / 专项行情分析)一律以 `assets/position_report_template.html` 九大节骨架为唯一输出骨架,**不得另起炉灶、不得用纯文字或自由表格替代**;
  - 九大节固定顺序:① 快照 ② 宏观金融面 ③ 当日数据+议息 ④ 跨市场 ⑤ 多周期共振(K线+四线)⑥ 量化 ⑦ 操作建议 ⑧ 引用 ⑨ 纪律(永置末);
  - 持仓类走 `scripts/position_report.py` 一键生成;**非持仓类**第一章"持仓快照"改为"分析标的快照"(列每品种实时价/ATR/趋势/计划方向,不写浮盈与持仓健康度),其余八节不变;
  - **HTML + MD 双版本必须格式一致**;数值 2 位小数;结论禁用模糊词;
  - 触发报告生成前先 `Read` 模板套骨架再填数。
- **`references/position_report.md` 升级为「分析报告统一模板」**:
  - 标题与适用范围改为覆盖三类报告;新增 **第 0 节 适用范围与第①节适配规则**(持仓类 vs 交易计划 vs 专项分析的章节差异表);
  - 第①节结构表改为"快照(持仓/分析标的)"双模式。
- **SKILL.md 模板章节**标明该模板为"本技能唯一批准的分析报告模板(强制套用)"。
- **影响**:此前自由结构的多品种计划(如 2026-09-10 美元/黄金/白银…八品种计划)此后一律改为九大节模板输出,确保视觉与章节与用户确认的 AUDJPY 报告完全一致。

## v1.4.0 — 持仓分析报告模板 + 一键生成器 · 2026-09-10

**对应需求:用户要求「后续按此模板输出每次的分析报告」,将 v1.3+ 实战沉淀的 AUDJPY 持仓分析报告标准化为可复用模板 + 一键生成器。**

- **新增 `assets/position_report_template.html`(持仓分析报告 HTML 模板,47 KB)**:
  - 九大节固定结构(纪律永远在最后):① 持仓快照 ② 宏观金融面解读(央行政策路径/利差结构/地缘+风险偏好/综合)③ 当日重要数据+本月议息会议提醒(已公布/待公布/月度议息)④ 跨市场验证(含三角一致性公式)⑤ 多周期共振(真实 K 线图+入场/SL/TP/当前 四线 markLine+方向矩阵+关键位)⑥ 量化验证(雷达图+收益分布+日线/1H 双表)⑦ 综合判定与操作建议(健康度评分+三种情景+最终推荐)⑧ 引用与依据 ⑨ 交易纪律(6 大铁律卡);
  - 占位符 `__SYMBOL__` / `__CURRENT__` / `__ENTRY__` 等,`scripts/position_report.py` 自动填充;
  - 配色:深空蓝背景 + 红绿涨跌(国际惯例)+ 紫央行 + 4 种语义色,霓虹暗色版面;
  - 内嵌 ECharts 5.4.3(candlestick/柱图/雷达/折线) + dataZoom 缩放。

- **新增 `scripts/position_report.py`(持仓分析报告一键生成器,~30 KB)**:
  - 输入:`--symbol --direction --lots --entry --sl --tp --account --risk-pct --out-dir`;
  - 6 步自动流水线:
    1. iTick 拉取 4 个实时报价(限频 5 次/分钟,智能 sleep);
    2. Twelve Data 抓取日线 200 + 1H 200 根 OHLC;
    3. quant_metrics.py 计算 Sharpe/Sortino/Hurst/Z-score/MDD/VaR 等 6 类指标;
    4. BIS 拉取 AU/JP 政策利率,FRED 拉取 DGS10/T10Y2Y;
    5. jin10 MCP 拉取 200+ 条经济日历事件;
    6. 三角验证(USDJPY × AUDUSD vs AUDJPY)+ 数据汇总 + 模板填充;
  - PnL 公式修正:JPY 报价对 = pips × lots × 1000 / USDJPY_rate(USDJPY 实时拉取,失败 fallback 153.0);
  - 输出:`<SYMBOL>持仓分析.html`(47 KB 含真实 K 线)+ `持仓分析报告_<SYMBOL>_<YYYY-MM-DD>.md`(精简版,2-3 KB)。

- **新增 `references/position_report.md`(持仓分析报告方法论,6 节)**:
  1. 九大节结构 + 必填数据 + 数据源映射表;
  2. 视觉规范(配色 / 图表类型 / 数据精度);
  3. 数据获取流程(7 个数据源调用顺序);
  4. 操作建议输出标准(持仓健康度评分 5 维度满分 100);
  5. 一键生成命令(可直接复制粘贴);
  6. 模板演进记录。

- **SKILL.md 同步更新**:
  - description 触发词补齐(持仓分析报告/position report/一键生成/报告模板);
  - 「模板(直接套用输出)」章节新增 `assets/position_report_template.html` 与 `references/position_report.md` 条目;
  - 脚本表新增 `position_report.py`(完整调用链说明);
  - 调用示例新增一行:`python scripts/position_report.py --symbol AUDJPY --direction SELL ...`。

- **实战验证**:
  - AUDJPY 持仓分析从手动 ~40 步工具调用 → 1 行命令 6 步自动完成;
  - 数据一致性:脚本输出 +$48.9 vs 手动计算 +$48.6(误差 < 1%,来自 USDJPY 汇率四舍五入);
  - 模板结构稳定性:HTML 47 KB,MD 2 KB,首尾一致;

## v1.3.1 — 最优 f + 信息比率 + 多重分形补强 · 2026-09-10

**对应需求:接 IMA 知识库交叉验证后,按权威源补强金融工程/量化维度(用户选"增量升级")。**

- **新增 `scripts/optimal_f.py`(最优 f 仓位计算,Ralph Vince 方法 + 蒙特卡洛,纯标准库)**:
  - 网格搜索最大化几何增长率 `G(f)=[∏(1+f·P_i/W)]^(1/N)` 求最优 f;
  - 输出最优 f、1/2 f、1/4 f(分数 f)、期末财富倍数 TWR;
  - 蒙特卡洛重采样逐笔盈亏,估计**最大回撤分布**(平均/中位/P95/P99/最坏)与**破产概率**(腰斩概率);
  - 实测:全 f 破产概率 > 99%(必爆),1/4 f 常 < 5%(可承受)——印证 Vince 原书结论;
  - `--csv`/`--text` 输入,`--json` 结构化输出,`--mc` 控制模拟次数。
- **`references/quant_finance.md` 六项补强(均标注 IMA 权威源)**:
  1. §2.4 GARCH(1,1) 实装示例(`arch` 库调用 + `α+β` 波动持久度 + long-run vol 用法,Cuthbertson);
  2. §3.4 收益回撤比正式命名 + ≥1 门槛(Carver);
  3. §5.5 最优 f(Vince:全 f 必爆、分数 f 才可执行、与凯利区别);
  4. §5.6 区间市顺向减仓/单边市顺向加仓(魏强斌《外汇交易进阶》);
  5. §8.4 多重分形(Mandelbrot:单一 H 是均值,应分时窗重估);
  6. §12 信息比率 IR = IC × √BR + 主动管理基本定律(Grinold & Kahn);
  7. §13 新增 **IMA 知识库引用清单**(8 本权威源 → 章节映射表)。
- **SKILL.md 同步**:脚本表新增 `optimal_f.py`;description 触发词补齐(最优 f/分数 f/信息比率/IR/主动管理基本定律/多重分形/收益回撤比/破产概率/蒙特卡洛回撤/几何增长率)。

## v1.3.0 — 金融工程与量化分析维度 · 2026-09-10

**对应需求:参考知识库关于金融工程和量化分析等的知识,对技能再做优化升级。**

- **新增 `scripts/quant_metrics.py`(量化指标计算引擎,纯标准库)**:
  - 输入:CSV(--csv)/ 粘贴文本(--text)/ 联网抓取(--fetch)价格序列,可选第二品种(--csv-b)做相关性;
  - 输出六大类指标:
    1. **收益与风险调整**:总对数收益、年化收益、年化波动率、Sharpe、Sortino;
    2. **回撤分析**:最大回撤、回撤期(峰→谷→恢复)、当前回撤;
    3. **分布形态**:偏度、峰度、Jarque-Bera 正态性检验;
    4. **尾部风险**:95%/99% 历史 VaR 与 CVaR(Expected Shortfall)、参数 VaR(正态假设,作对比);
    5. **波动率建模**:EWMA(λ=0.94, RiskMetrics 标准)、已实现波动率(21d 滚动);
    6. **时间序列诊断**:自相关 lag(1)、均值回归半衰期(AR(1))、**Hurst 指数**(R/S 法,判定趋势 vs 均值回归)、63 日 Z-score;
  - 支持 `--json` 结构化输出与 `--corr-b` 双序列皮尔逊相关;
  - 自适应窗口:Z-score 在样本不足 63 时自动回退到 n/2,小样本也能用;
  - 数值统一保留 4 位有效位,百分比 2 位小数。
- **新增 `references/quant_finance.md`(金融工程/量化方法论,11 节)**:
  1. 收益与风险度量(对数收益、Sharpe/Sortino/Calmar);
  2. 波动率建模(EWMA/已实现 vol/GARCH 参考/regime 切换);
  3. 回撤与资金曲线(MDD、回撤期、CAGR/MaxDD、阶梯降仓表);
  4. VaR 与尾部风险(历史 vs 参数、CVaR、厚尾/偏度口诀);
  5. 仓位管理量化(凯利/分数凯利、风险预算、波动率目标、R 倍数期望值);
  6. 因子模型(FX 三因子 carry/momentum/value、商品期限结构、Z 标准化加权);
  7. 协整与配对交易(Engle-Granger 简化法、Z-score 阈值、半衰期);
  8. Hurst 指数与均值回归(H<0.45 反转、H>0.55 趋势、Z-score 综合用法);
  9. 相关性与组合分散(滚动相关、风险平价、最大分散);
  10. 实战纪律(过拟合、前视偏差、生存偏差、交易成本、心理与执行清单);
  11. 与本技能其他模块的衔接表(每节对应脚本/参考文件)。
- **分析框架升级 — 第四维「量化验证」**:在原有"宏观 + 跨市场 + 盘面"三维印证基础上,新增量化验证层——当三维共振 + 量化指标健康(Sharpe > 0.5、CAGR/MaxDD > 1、Hurst 与策略类型匹配、跨品种相关不集中)时,信号可信度最高;反之三维共振但量化指标退化(如厚尾 + 负偏度)时仓位自动折扣。
- **SKILL.md 同步更新**:文件表新增 `quant_finance.md`、脚本表新增 `quant_metrics.py`;核心原则新增"先量化验证再下注";description 触发词补齐量化关键词(对数收益/Sharpe/Sortino/Calmar/最大回撤/凯利公式/半衰期/Hurst/协整/配对/波动率/波动率目标/风险预算/尾部风险/Expected Shortfall/CVaR/分位/Z-score/Jarque-Bera/因子模型/期限结构/资金曲线/过拟合/前视偏差/walk-forward 等)。

## v1.2.2 — 时间核对与数据鲜度铁律 · 2026-09-06

**对应需求:使用技能时自动核对当下具体时间,宏观/经济/行情数据须截止到"最新"时间维度分析。**

- **新增「前置铁律:时间核对与数据鲜度」**(SKILL.md,置于核心原则之前,每次调用第一动作):
  - 启动分析/取数前,必须首先确认"此刻"的**具体时间(日期+时分+时区)**,以该时间为分析基准;严禁用会话历史旧时间戳、缓存文件旧日期或假设日期代替"当下";对外口径统一北京时区(GMT+8)。
  - 宏观/经济/行情数据一律建立在**截至该当下时间的最新可用数据**之上:实时数据取"现在"最新值;日/周级序列取到最近已发布窗口,不得用更早缓存假装最新;取不到最新时**显式标注"数据截至 XXX(非最新)"**并说明原因,禁止静默以旧充新。
  - 输出每条数值/结论的 `[源 | 截至]` 必须填入**已核对的当下具体时间**(`YYYY-MM-DD HH:MM TZ`);计划/报告文件名或正文须携带该基准时间。
- **步骤 0.0 强化**:权威实证取数第一动作改为先执行时间核对铁律,再拉取当日数据;所有取数须为最新可用值。
- **输出规范新增鲜度条款**:明确时间戳格式与"非最新"显式标注要求,严禁静默以旧充新。

## v1.2.1 — 指标体系精简 + 宏观深度 + 周期角色澄清 · 2026-09-05

**对应需求:5 项优化指令(点位降噪 / 指标精简 / 宏观深化 / 客观理性+周期角色 / 周期差异优化)**

- **指令1 关键位融合降噪**:旧版把每周期数十个原始阻力/支撑/整数位全列出,无参考意义。改为只保留**强/中**级别的跨周期聚类共振区,按强度排序、剔除孤立弱位与过远噪音,上限 8 条;⑤ 章节说明同步更新(旧版数十个→现仅高信号共振位)。
- **指令2 指标体系精简为 EMA5/10/60 + 趋势线 + 成交密集区 + ATR**:
  - `kline_read.analyze()` 趋势排列由 EMA20/50 改为 **EMA5/EMA10/EMA60**(多头排列=价>EMA5>EMA10>EMA60 等);报告字典移除 `ema20/ema50`,新增 `ema5/ema10/ema60`。
  - `_tf_panel` 单周期面板重排为:趋势背景 / 市场结构 / 收·EMA5·EMA10·EMA60 / EMA排列(5/10/60) / ATR(14) / 趋势线(角度·状态·当前值) / 成交密集区(POC·HVN) / ATR 止损参考(1.0×与 1.5×) / 仓位参考(账户$·单笔风险%·止损距·建议手数) / 关键阻力(前2) / 关键支撑(前2) / 仅留量价背离与跳空提示。
  - **彻底移除 MACD/RSI/布林/随机** 等冗余指标展示(共识矩阵、④-B 表、面板均不再出现 EMA20/50 与 MACD)。
  - K 线图图例与标线同步改为 EMA5(紫)/EMA10(青)/EMA60(黄宽)/趋势线(灰虚)+ POC 成交密集区。
- **指令3 宏观经济面深度分析**:③ 章节由简略 checklist 扩展为结构化深度分析(约 2600+ 字)——3.1 美元与利率地基(实际利率框架:US10Y/DGS10、10Y TIPS/DFII10、盈亏平衡/T10YIE) 3.2 四大央行周期与利差表 3.3 收益率曲线状态(2s10s 陡峭/平坦/倒挂) 3.4 宏观 Regime 与 risk-on/off 表 3.5 跨市场验证(≥2 相关市场确认,背离即警告) 3.6 宏观方向指引结论。
- **指令4 客观理性 + 周期角色声明**:③ 章节置顶"周期角色声明"——宏观/跨市场只用于 W/D 大方向指引,不给出具体入场/止损/目标;1H 小时级交易以盘面为绝对主导;与 W/D 冲突自动降级为"不交易"。交易计划标题改为「⑦ 交易计划(1H 盘面触发,宏观仅过滤)」,风险铁律新增周期角色与"仓位按 ATR 计算"两条。
- **指令5 周期差异优化(看大做小)**:新增 **④-B 周期差异与"看大做小"逻辑** 表,逐维度对比 W/D/H1 的趋势背景/市场结构/EMA排列/最新收盘/ATR/趋势线/关键阻力/关键支撑/最强形态,并单列"交易含义"列 + 看大做小纪律(大周期定方向、小周期定时机;逆大周期不做)。
- **Bug 修复**:修复 `to_html_mtf` 因模板中裸 `2%`(欧央行通胀目标)触发 `%`-format "not enough arguments" 导致 HTML 生成失败的问题(`2%`→`2%%` 转义)。
- **回归测试**:AUDJPY 演示三周期重生成通过,HTML/JSON 正常,EMA20/50/MACD/RSI/布林/随机 残留次数均为 0,⑤ 关键位融合 6 行,③ 宏观章节 2600+ 字,④-B 表头含"交易含义"列。

## v1.2.0 — 多周期共振(三维印证)引擎 · 2026-09-04

**核心优化(对应需求:三维共振分析 + 增强数据分析 + 图表 + 明确结论)**

- **新增 `scripts/mtf_confluence.py`(多周期共振引擎)**
  - 输入周线(W)+日线(D)+1小时(H1)三周期 K 线(本地 CSV / 粘贴文本 / `--fetch` 联网),直接复用 `kline_read.analyze()` 做单周期客观解读,不重写指标计算。
  - **方向共识矩阵**:每周期由趋势背景(ATR 归一化摆动斜率)+ EMA20/50 排列 + 摆动结构三方投票,定偏多/偏空/中性及强度;W+D 收敛为大周期背景方向(评分 ≥±1.5)。
  - **关键位融合(confluence zone)**:三周期阻力/支撑/整数位邻近(±0.3% 价或 ±0.4×日线 ATR)聚类,按跨周期数/测试次数定强/中/弱,标记支撑区/阻力区/中枢区。
  - **ATR 跨周期差异量化**:日线 ATR ÷ 1H ATR、周线 ATR ÷ 日线 ATR、1H/日线波动占现价 %,用于止损距离与仓位尺度、波动 regime 判定。
  - **明确结论(不含糊)**:仅当 W+D 背景同向且 1H 顺向(或回调至支撑区待转多)时给"做多/做空"(入场锚共振区、止损=结构外 1.5×ATR_1H、目标=最近共振区、附 R 倍数);任一反向给"不交易"并指明冲突周期。**结论文本禁用"可能/或许"等模糊词,全部基于客观数值**。
  - 输出 `--json`(结构化结论,供程序消费)与 `--html`(**9 段深度分析报告**,霓虹暗色版面 + 粘性目录导航 + 卡片化布局):① 执行摘要(大周期背景评分条 + 周/日/1H 方向迷你卡) ② 三维共振总览(共识矩阵) ③ 宏观/跨市场衔接(checklist) ④ 各周期深度盘面(W/D/1H 各含 K 线图 + EMA20/50 + 共振区/枢轴/通道标线 + 指标面板 + Morris 量化形态表) ⑤ 关键位融合(强度分级 + 强度条) ⑥ ATR 跨周期波动结构(柱状图) ⑦ 交易计划(入场/止损/目标/R + 触发/失效/持有逻辑) ⑧ 风险与纪律铁律 ⑨ 数据溯源与方法学(IMA 引用)。多方面逐项展开,满足 10+ 页深度输出与版面优化要求。
- **新增 `references/mtf_confluence.md`(方法论)**:周线/日线定方向背景、1H 定进场时机的层级原则;方向共识矩阵、关键位融合、ATR 跨周期差异、结论分支;IMA 知识库(金融 id `7490653902604963`)权威背书——魏强斌《外汇交易进阶》第十八阶"多重时间框架"、《ATR止损法深度研究与实践指南》;数值规则衔接本地 `ta_reading.md` / `indicators.md` / `channels.md`。
- **SKILL.md 整合**:description 增加多周期共振/看大做小/共振区/明确结论触发词;分析主线第二阶补充「多周期共振」调用说明;文件表与脚本表新增条目;新增 `mtf_confluence.py` 用法示例。
- **回归测试**:三分支(共振做多 / 共振做空 / 周线日线冲突不交易)全部给出确定性结论,JSON/HTML 输出正常。

## v1.1.0 — GitHub 发布与 `kline_read` 盘面解读引擎 · 2026-09-03

- 新增 `scripts/kline_read.py`(K 线盘面解读引擎:趋势背景、市场结构、EMA 排列、ATR、Morris 量化形态评级与确认、MACD/RSI/布林/随机、回归通道、经典形态;支持 `--csv`/`--text`/`--fetch` 与 `--json`/`--html`)。
- 新增 `scripts/kline_fetch.py`(Twelve Data 权威 K 线抓取,中国大陆可直连,覆盖 15min/1H/4H/1D/1W)。
- 发布至 GitHub `kingfeng168/kingforex-skill`(增量更新,脱敏、提交邮箱 noreply、Git Data API 绕过 10054 重置)。
- 配套数据源与盘面分析参考文档(`data_sources.md`、`ta_reading.md` 等)持续完善。

## v1.0.0 — 体系奠基

- 九大模块交易体系:宏观利率地基、外汇/黄金/原油专项、跨市场联动、微观结构、风险与心理、盘前计划→策略落地模板、权威数据源速查、纪律与资金管控。
- 三维印证(宏观定方向 / 跨市场验方向 / 盘面定时机)分析哲学确立。
