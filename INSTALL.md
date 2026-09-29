# kingforex-skill v2.9.0 安装与使用（INSTALL）

> 面向**手工**外汇/贵金属/大宗商品交易者的宏观交易体系与纪律框架技能。
> 纯决策支持：**不下单、不发单、不外传数据**。不构成投资建议。

## 一、安装（WorkBuddy）

```bash
# 方式一：直接拷贝目录
#   Windows:  %USERPROFILE%\.workbuddy\skills\kingforex-skill
#   macOS/Linux:  ~/.workbuddy/skills/kingforex-skill
# 把本包内的全部内容放到上述目录（保持 SKILL.md 在根目录）

# 方式二：解压 zip
unzip kingforex-skill-v2.9.0.zip -d ~/.workbuddy/skills/
# 解压后目录名需为 kingforex-skill（若为 kingforex-skill-v2.9.0 请改名）
```

安装后刷新/重启 Agent，用 `@skill:kingforex-skill` 或在对话中描述
「制定下一交易日交易计划 / 分析美日汇率 / 多周期共振研判黄金 / 已有持仓做深度诊断 / 评估这笔单的止损止盈」触发。

## 二、其他 Agent 形态

| 目标 | 放置位置 | 备注 |
| --- | --- | --- |
| WorkBuddy | `~/.workbuddy/skills/kingforex-skill/` | 本包默认目标 |
| Claude / 通用 Agent Skills | 任意 skills 目录，保持 `SKILL.md` + `references/` + `scripts/` 结构 | frontmatter 已含 `name` / `description`(293 字符) / `version` / `license` |
| 仅要方法论 | 只取 `SKILL.md` + `references/` | 脚本为纯标准库 Python，可选 |

## 三、依赖

- **Python 3.8+**，全部脚本只用标准库（`urllib` / `json` / `csv` / `math`），无需 pip 安装。
- 可选：`openpyxl`（仅在生成 Excel 复盘模板时需要，缺失会自动跳过并提示）。
- **图表离线可用**：`assets/echarts.min.js`（5.5.1，与官方字节级一致）由生成器内嵌，
  产出 HTML 无任何 CDN 外链。

## 四、API Key（全部可选，按需配置）

不配任何 key 也能用：`calc_engine`、`kline_read`、`mtf_confluence`、`quant_metrics`、
`sl_tp_evaluate`、`exposure`、`position_size`、`risk_unit`、`optimal_f`、`futures_analysis`
（本地/手工输入模式）、World Bank、BIS、CFTC、Frankfurter、gold-api、goldprice.dev、美财政部。

需 key 的源（`--api-key` > 环境变量 > `scripts/.<name>_key` 单行文本）：

| 源 | 环境变量 | 本地文件 |
| --- | --- | --- |
| FRED（利率/曲线） | `FRED_API_KEY` | `scripts/.fred_key` |
| Twelve Data（K 线/实时价） | `TWELVEDATA_API_KEY` | `scripts/.td_key` |
| EIA（原油库存） | `EIA_API_KEY` | `scripts/.eia_key` |
| 金十 Jin10（快讯/日历/报价） | `JIN10_TOKEN` | `scripts/.jin10_key` |
| 华尔街见闻 WSCN | `WSCN_API_KEY` | `scripts/.wscn_key` |
| AllRatesToday（实时中间价） | `ART_KEY` | `scripts/.art_key` |
| goldprice.dev / OilPriceAPI / Jev | `GOLDPRICE_API_KEY` / `OILPRICEAPI_KEY` / `JEV_API_KEY` | 同名 `scripts/.<x>_key` |

> 本包**不包含任何密钥文件**，请自行创建。
> ⚠️ 当前**不可用**的源（已在脚本与文档中标明）：**IMF**（端点返回 0 观测，脚本 exit 3 并给替代源）、
> **QuantGist**（API 后端 502，预检 exit 3）、OPEC/CME FedWatch（被拦，走手工取数）。

## 五、安装后自检（3 条命令，均无需 key）

```bash
python scripts/calc_engine.py                # 计算引擎自检（pip 口径/手数/凯利/评分）
python scripts/quant_metrics.py --csv <价格CSV> --date-col datetime --price-col close --json
python scripts/kline_read.py --csv <K线CSV> --symbol EURUSD --tf D1 --last 200
```

**下单前必过闸门**（新增，通过 exit 0 / 否决 exit 3）：

```bash
python scripts/exposure.py --equity 574 \
  --positions "AUDJPY:short:0.02:2.85" \
  --check-new "XAUUSD:long:0.01:1.5"
```

## 六、v2.9.0 关键行为（务必了解）

1. **单笔风险硬上限 1%**（`calc_engine.RISK_HARD_CAP`），文档与代码同源。
2. **黄金/白银 pip 与每 pip 美元价值**统一由 `calc_engine.CONTRACTS` 提供
   （黄金 pip=1.0 → $100/标准手；白银 pip=0.01 → $50/标准手）。
3. **`exposure.py` 名义本金 = 实时价 × 合约单位**；取不到价会**报错退出**（不杜撰价格），
   可用 `--price SYM=VAL` 手工传入或 `--no-fetch` 禁用联网。
4. **旗舰报告生成器**（`gen_decision_enhanced_v256.py`）：
   - 需要 `KINGFOREX_DATA` 指向已存在目录，且其 `kline/` 下有 7 个日线 CSV；
   - **数据鲜度门禁**：数据基准日取自日K末根；滞后超 3 天、或溯源行日期与基准日不符时**拒绝写出**；
   - 缺 `scripts/.td_key` 时**拒绝回退硬编码旧价**；
   - 仅当显式 `KINGFOREX_ALLOW_STALE=1`（或 `--allow-stale`）才允许离线出快照图。
5. **Hurst 用 DFA-1 + 自助法随机游走带**判定，不再使用 0.45/0.55 固定阈值；
   `Hurst_判定 = 与随机游走不可区分` 时**不得据此判趋势**。
6. 报告格式冻结基线 = **v2.5.6**（23 节 / 15 图 / 0 CDN）；本版**未改格式**。

## 七、目录结构

```
kingforex-skill/
├── SKILL.md              # 技能主文档（含 frontmatter: name/version/description）
├── README.md             # 面向人的说明与快速开始
├── CHANGELOG.md          # 变更日志（v2.9.0 为一致性修复版）
├── INSTALL.md            # 本文件
├── LICENSE               # MIT
├── references/           # 19 份方法论参考（含 trigger_guide.md 触发词总表）
├── scripts/              # 36 个活跃脚本（计算引擎 / 量化 / 盘面 / 共振 / 取数 / 风控 / 报告）
└── assets/               # 报告模板 + echarts.min.js（离线内嵌用）
```

## 九、历史 / 开发脚本的处理（v2.9.0）

原先有 6 个脚本依赖本机开发环境的中间产物（已删除的 `gen_report_20260914.py`、从未随仓库分发的
`_paramtest/` 比对样本、写死的日期目录），克隆后直接运行必然报 `FileNotFoundError`。现已处理：

| 脚本 | 处理 | 说明 |
| --- | --- | --- |
| `scripts/parity_check.py` | **修复并保留** | 改为命令行传参（`--orig/--param`，或 `--dir` 自动取最新两份报告），实测可正常比对 |
| `scripts/transform_to_param.py` | 归档 | 依赖已删除的 `gen_report_20260914.py` → `scripts/_archive/legacy_dev_tools/` |
| `scripts/build_daily_json.py` | 归档 | 同上 |
| `scripts/build_gen_daily.py` | 归档 | 一次性数据层替换脚本（写死某日数据），已被"生成器数据层直改"流程取代 |
| `scripts/decision_enhanced_report.py` | 归档 | v2.3 历史生成器 |
| `scripts/gen_report_param.py` | 归档 | v2.4 历史生成器 |

> 归档件**不随本安装包分发**；如需查阅历史实现，可从源码仓库的 `scripts/_archive/` 获取。
> 日常流程不依赖任何归档件：分析走 `kline_read` / `mtf_confluence` / `position_report` /
> `quant_metrics` / `exposure` / `sl_tp_evaluate`，报告走 `gen_decision_enhanced_v256.py`。

## 八、免责声明

本技能仅用于教育与研究。所有信号、计划与结论基于公开数据与客观数值，
**不构成投资建议**。外汇/贵金属/大宗商品杠杆高、风险大，请独立判断、自担风险。
