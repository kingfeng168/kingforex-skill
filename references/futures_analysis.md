# 期货分析:期现结构(基差)与期货价差

> 配套脚本:`scripts/futures_analysis.py`(纯标准库)。本文件讲**方法学与公式**,脚本负责**确定性计算**。
> 数据源:iTick(期货报价/K线)、goldprice.dev(现货金)、OilPriceAPI(WTI/Brent 原油)。

---

## 0. 为什么做期货分析

EIA/OPEC 只给库存与供需平衡,缺"期现关系 + 期限结构"这一关键维度。期限结构(Curve)与基差(Basis)直接反映**市场预期、持有成本、便利收益与逼仓/短缺信号**,是原油(模块四)与黄金(模块三)研判的硬指标:

- **Contango(升水/远期溢价)**:远月 > 近月 > 现货。常态,反映持有成本(仓储+融资+保险);深度 contango 常意味供给宽松、库存高。
- **Backwardation(贴水/近月溢价)**:近月 > 远月 > 现货。反映现货短缺、便利收益高(持有实物更值钱);常出现在供给冲击、逼仓、低库存时。
- **基差 Basis = 现货 − 期货**:正值=该合约处于 back;负值=处于 contango。

---

## 1. 期现结构分析(spot-futures structure / basis)

### 输入
- 现货价 `spot`
- N 个期货合约:每合约 `(标签, 期货价, 到期天数 days)`(或 `YYYY-MM-DD`,脚本自动算天数)

### 公式(脚本逐合约输出)
| 指标 | 公式 | 含义 |
|---|---|---|
| 基差 `basis` | `spot − futures` | >0 该合约 back;<0 contango |
| 基差率 | `basis / spot × 100%` | 相对现货的偏离幅度 |
| 年化 carry | `(futures − spot)/spot × 365/days × 100%` | >0 贴水市场/持有成本(contango 常态为正);<0 升水/便利收益(back 常态为负) |
| 相邻斜率(年化) | `(F_{i+1} − F_i)/F_i × 365/(days_{i+1}−days_i) × 100%` | 段内曲线陡峭度;>0 段 contango,<0 段 back |
| 整体形态 | 首末合约年化斜率 | contango(升水)/backwardation(贴水)/flat |

### 交易含义
- **Contango 市场**:滚动收益为负("展期亏损")——持多期货每换月被动亏;适合"卖近买远"或做空较远合约的结构性头寸;现货紧缺信号弱。
- **Backwardation 市场**:滚动收益为正——持多期货每换月被动赚;反映现货溢价/短缺,常配合做多近月。
- **曲线陡峭化/平坦化**:陡峭化=远端预期更宽松或持有成本上升;平坦化/倒挂加深=近端紧张加剧。

### 脚本
```bash
# 现货金 2400,GC 2405=2410(30天) GC 2408=2425(120天)
python scripts/futures_analysis.py basis --spot 2400 --fut 2405:2410:30 --fut 2408:2425:120
# 直连实时:现货(goldprice.dev)+ GC 期货(iTick)
python scripts/futures_analysis.py pull --kind gold
```

---

## 2. 期货价差分析(futures spread)

### 2.1 跨期价差(calendar spread)
- 定义:`spread = 近月 − 远月`(可按品种约定符号)。
- `>0` = 该段 back(近月溢价);`<0` = contango(远月溢价)。
- 交易:contango 段可考虑"空近月/多远月";back 段相反。需结合持仓成本与展期方向。

### 2.2 跨品种价差(inter-commodity)
- 典型:**WTI − Brent**(美元/桶)。
  - 常态为负(WTI 相对 Brent 贴水),反映美国增产、库欣累库、物流瓶颈。
  - 极端负值(深度 WTI 贴水)= 美国供给过剩/管道受限信号;极端正值=美国供给收紧/出口强劲。
- 判定偏离:配合历史序列算 **z-score**(`--series` 传入历史价差 CSV/文本,每行一个值):
  - `z > 1.5` → 价差偏高,考虑空 near/多 far(或做空跨品种价差);
  - `z < −1.5` → 价差偏低,考虑多 near/空 far;
  - `|z| ≤ 1.5` → 中性区间,不追。

### 脚本
```bash
# 跨品种 WTI vs Brent
python scripts/futures_analysis.py spread --a WTI:91.97 --b BRENT:95.98
# 跨期(近月 2410 / 远月 2425)
python scripts/futures_analysis.py spread --near M1:2410 --far M2:2425
# 算 z-score(历史价差文件)
python scripts/futures_analysis.py spread --a WTI:91.97 --b BRENT:95.98 --series "D:/workbuddy/输出文件/wti_brent_spread_hist.csv"
# 直连实时:OilPriceAPI 取 WTI/Brent 算跨品种价差
python scripts/futures_analysis.py pull --kind oil
```

---

## 3. 数据获取(喂给分析的数据源)

| 用途 | 数据源 | 脚本 | 说明 |
|---|---|---|---|
| 期货报价(黄金 GC / 原油 CL / 股指) | iTick | `itick_fetch.py quote --asset future --region US --code GC` | 免费层 `api-free.itick.org`,限频 5 次/分钟 |
| 期货/现货 K 线 | iTick | `itick_fetch.py kline --asset future ...` | kType: 1m/5m/15m/30m/1h/2h/4h/1d/1w/1mo |
| 现货金基准 | goldprice.dev | `goldprice_fetch.py` | `XAU-USD-SPOT`;本构建环境被 Cloudflare 拦截,**本机正常** |
| WTI / Brent 实时 + 历史 | OilPriceAPI | `oilprice_fetch.py` | `by_code=WTI_USD`/`BRENT_CRUDE_USD`;`Authorization: Token` |

> 完整端点、认证头、限流与降级说明见 `data_sources.md` 第 7.12–7.14 节。

---

## 4. 研判纪律(与技能整体一致)

- **公式确定、不编造**:所有基差/斜率/z-score 由脚本确定性计算,绝不手估或记忆填数。
- **降级优先**:数据源不可达(goldprice.dev Cloudflare、iTick 限频、key 缺失)时,脚本给出明确提示并建议使用 `basis`/`spread` 子命令手动传入数值,**不臆造价格**。
- **三维印证**:期货结构/价差只是"跨市场验证"维度之一,需与宏观(利率/库存)、盘面(K线/关键位)共振才作为交易依据;单独信号不硬开仓。
- **[源 | 截至]**:所有引用的现货/期货/价差数值标注来源与数据时间。
