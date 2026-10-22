---
name: a-share-dragon-tiger-report
description: |
  生成 A 股「涨停板龙虎榜深度研判报告」v2.1（21 章结构编号 0–21 + 22 条计算口径 + 财富密码融合层），
  按四层漏斗 L1→L2→L2.5→L3 框架（六条已确认口径 v2，含半年口径 + 增速红线），
  输出 HTML / PDF / PPTX；内置「十五五 18 方向跟踪池（102 板块 + 12 SW1 + 70 股）」
  及三层核验生成器（reports/build_15th5_report.py），可离线复现 WorkBuddy 侧完整产出。
  支持两种排版样式：样式 A（classic，MS 色系 + ECharts + A4 纵向、26–38 页 PPTX 版）；
  样式 B（bii，BlackRock 投资研究院「左文字栏 + 右图表」双栏范式，A4 横向 + Chart.js 内联 + CDP 导 PDF）。
  当用户要求生成龙虎榜报告、涨停板深度研判、每日收盘复盘、十五五方向四层核验、
  「双栏 / BlackRock 范式 / 左文字栏右图表」版研报，或把 westock / IMA 盘面写入机构风研报时使用。
  仅交易日生成；非交易日应直接说明休市并结束。
  v1.1（21 章 + §16+，26–38 页 PDF，26 页 PPTX）已被 v2.0 取代；
  v2.0 新增 framework/ 跟踪池数据（102 板块 + 12 SW1 + 70 股 + 口径 v2 结论）与 reports/ 18 方向生成器；
  v2.1 新增样式 B（BII 双栏范式，templates/bii/）与 `--style {classic,bii,both}`，并让 PDF 导出
  在 Playwright 浏览器缺失时自动回退到系统 Chrome + CDP。
homepage: https://github.com/yjkj999999/a-share-dragon-tiger-strategy
metadata:
  openclaw:
    emoji: 📊
    version: "2.1.0"
    requires:
      binaries:
        - python3
        - node
  security:
    credentials_usage: |
      可选：IMA OpenAPI 凭证仅发送至 ima.qq.com；westock MCP 若配置则优先使用。
      未配置时降级为本地 sample_data.json（标注「演示数据 · 非当日行情」），并在报告首页
      显式标注数据口径与延迟。**不构成投资建议**。
    allowed_domains:
      - ima.qq.com
      - '*.myqcloud.com'
---

# A 股龙虎榜深度研判 + 财富密码策略 v2.3

> **口径版本 v2.3（2026-09-25 发布）**——**v2 六条口径不变**，新增**知识蒸馏层**：
> 11 本投资类书籍（同花顺短线实战、短线金手3、邹佩轩穿透三部曲、饶钢财务两册、
> 凌鹏《周期估值与人性》、索罗斯投资哲学、李奇霖宏观手册、AI 通胀与武器、故事的力量）
> 蒸馏出 **219 条可操作规则**，收敛为 `strategy/knowledge.py`（8 个子模块，纯函数无 IO）
> + `strategy/calibers.py` 的 `KNOWLEDGE` 阈值表（30+ 键）。非破坏性升级：
> 新增检查只加分/告警；唯一强否决是「科目接力造假扫描」≥2 条强红旗。
> 详见 **§13**。
>
> **口径版本 v2（2026-09-12 定稿，永久生效）**——口径变更须全量重算历史结论并报告 ±N 只敏感度。
>
> **v2.2（2026-09-16 发布）**：**日更默认改为只出样式 B（BII 双栏）**，并给它补上第 14 页
> 「**次日 5 条可证伪预判**」，使其自足成篇（19:15 的核验任务因此只需读这一份）；
> 预判走 `predictions.json` 契约注入（5 条硬性数量、每条必须有 `claim` + `falsify`，
> 生成端硬校验，缺文件则渲染明确标注的「示例占位页」）。同时补齐两个定时任务的编排。
> 详见 **§12.8 / §12.9**。
>
> **v2.1（2026-09-16 发布）**：新增**样式 B —— BII 双栏范式**（`templates/bii/`，A4 横向
> + BlackRock 投资研究院「左文字栏 + 右图表」双栏骨架 + Chart.js 内联 + CDP 导 PDF），
> 与既有样式 A（MS 色系 A4 纵向）并列；`generate_daily.py` 新增 `--style {classic,bii,both}`。
> 同时把「HTML → PDF」抽成公用能力，Playwright 浏览器缺失时自动回退系统 Chrome + CDP。
> 详见 **§12**。
>
> **v2.0（2026-09-12 发布）**：在 v1.1 四层漏斗 + 财富密码融合层基础上，新增
> `framework/`（十五五 18 方向跟踪池：102 板块 + 12 SW1 + 70 股 + 口径 v2 结论）
> 与 `reports/build_15th5_report.py`（18 方向三层核验生成器，纯 stdlib、可离线运行）。
> 至此本仓库 = WorkBuddy 侧完整产出（21 章结构 + 22 条口径 + 跟踪池 + 六条口径 v2 + 增速红线 + 26–38 页 PDF / 26 页 PPTX）。

## 0. 触发

- 「生成今日龙虎榜 / 涨停板深度研判报告」
- 「出 HTML / PDF / PPTX」
- 「跑四层漏斗核验候选 / L1→L2→L2.5→L3」
- 「融合财富密码选股策略」
- 「做十五五六张网 / 新兴支柱 / 未来产业的方向级核验」
- 「用双栏版式 / BlackRock 范式 / BII 那种左文字栏右图表出报告」→ 走 `--style bii`
- 「两套版式都给我」→ 走 `--style both`

## 1. 双平台安装

| 平台 | 技能目录 |
|---|---|
| OpenClaw（大龙虾） | `~/.openclaw/workspace/skills/a-share-dragon-tiger-report/` |
| QClaw（小龙虾） | `~/.qclaw/skills/a-share-dragon-tiger-report/` |
| MiMo Desktop / MiMoCode | `~/.config/mimocode/skills/a-share-dragon-tiger-report/` |

> 三处安装的 `SKILL.md` 应保持同一 `shasum`；改完任一处请同步其余两处（示例见 §12.7）。

安装命令（CI 或手工均适用）：

```bash
R=/path/to/a-share-dragon-tiger-strategy
mkdir -p ~/.openclaw/workspace/skills/a-share-dragon-tiger-report
mkdir -p ~/.config/mimocode/skills/a-share-dragon-tiger-report
cp $R/skill/SKILL.md $R/skill/README.md $R/skill/skill-card.md ~/.openclaw/workspace/skills/a-share-dragon-tiger-report/
cp $R/skill/SKILL.md $R/skill/README.md $R/skill/skill-card.md ~/.config/mimocode/skills/a-share-dragon-tiger-report/
```

仓库根目录：`<your-org>/a-share-dragon-tiger-strategy`（v1.1 已用真实 org 替换 `your-org` 占位符）。

## 2. 硬性流程

1. **交易日判断**：周一至周五且非 A 股法定节假日；否则回复「今日休市，无需出报告」并 **stop**。
    - **再走「收盘状态」关（2026-09-17 新增，与交易日判断同等硬性）**：交易日成立 **≠** 可以出报告。
      以下两个充分信号任一不满足，即回复「今日尚未收盘，报告顺延至收盘后」并 **stop**：
      ① `westock lhb --date <今日>` 能返回当日龙虎榜（不是「未找到市场数据」）；
      ② `westock minute sh000001` 末行分钟数 ≥ 1500。
      **反面教训（2026-09-17 11:33 提前触发）**：交易日历返回「是交易日」，但当时上证分时最后仅到 **1130**、
      当日龙虎榜**不存在**、半日成交额 12,445 亿（前一交易日全天 18,391 亿）、涨停 34（前一交易日 91）。
      报告名与 §1.1 把龙虎榜列为**强制数据源**，无此项即无法满足输出契约；半日数据出报告既违反
      「不得当作当日数据使用」，又会被收盘后的正式运行按**同名路径**覆盖。**仅靠交易日历不足以决定是否出报告。**
2. **取数优先级**：
   - 第一优先 westock MCP：`data_quote` / `data_kline` / `data_finance` / `data_shareholder` / `data_sector` / `data_changedist` / `data_lhb` / `tool_ranking`
   - 第二降级 IMA 库「A股市场每日盘后复盘」「A股每日涨停板龙虎榜深度研判报告」
   - 第三降级 `strategy/sample_data.json`（演示数据，报告页眉标注）
   - **禁止 WebSearch 作为行情源**
3. **工作目录**：`./dragon-tiger-YYYYMMDD/`，文件前缀 `涨停板龙虎榜深度研判报告-YYYYMMDD`。
4. **四层漏斗**：从候选数据构建 `funnel.Industry` / `funnel.Stock`，调 `funnel.run_funnel` 得 `FunnelResult`（含 L2 入池 / L2.5 剔除 / L3 否决 / 最终通过 + 敏感度）。
5. **评分管道**：把 funnel.l3_pass 喂给 `pipeline.run_pipeline`，得 BUY/WATCH/AVOID 信号表 + α 账本快照。
6. **落盘两份数据 JSON**（样式 B 的输入契约）：
   - `dragon-tiger-YYYYMMDD/data.json` —— schema 见 `strategy/sample_data.json`：
     `candidates[]`（`code/name/sector/rank/vr` + 评分与风控字段 `score/action/entry/stop/...`）、
     `industries[]`（`code/name/rank/vr`）、`context`（`equity/stage/limit_up_count/broken_rate/index_pct`）。
   - `dragon-tiger-YYYYMMDD/predictions.json` —— **次日 5 条可证伪预判**，契约见 §12.9
     （5 条硬性数量；每条必须有 `claim` + `falsify`；**必须显式写 `target_date`**）。
7. **生成报告**：`python3 scripts/generate_daily.py --style bii --data <data.json> --date YYYY-MM-DD --predict-file <predictions.json> --out out/dragon-tiger-YYYYMMDD`
   - `bii` = **样式 B，日更默认**：BII 双栏 HTML/PDF，14 页，自带图表/溢出/页数三重校验
   - `classic` = 样式 A：MS 色系 A4 纵向 21 章，HTML/PDF/PPTX（用户另行要求时才出）
   - `both` = 两套都出
8. **交付**：`present_files` 产物 + 摘要（定性 / 核心数据 / 主线 / 推荐与规避 / 盘前检查与 α 预算 / 次日 5 条预判要点）。

## 3. 报告结构（21 章）

| 章节 | 内容 | 数据源 |
|---|---|---|
| 0 | 报告口径（v2 永久生效）| `calibers.describe()` |
| 1 | 四层漏斗 L1→L2→L2.5→L3 结果表 + 敏感度 | `funnel.run_funnel` |
| 2 | 评分管道 · 风控信号表 | `pipeline.render_signal_table` |
| 3 | α 账本 + 限额检查 | `risk.AlphaLedger.snapshot` |
| 4 | 盘前 6 项检查 | `playbook.PRE_OPEN_CHECKLIST` |
| 5 | 财富密码五层图谱（制度→资金→产业→公司→交易） | `playbook.FIVE_LAYER_MAP` |
| 6 | 行业层（L1）扫描 | `filters.gate_industry` |
| 7 | 个股层（L2）扫描 | `filters.gate_industry`（个股粒度）|
| 8 | 不可交易清单（L2.5）| `filters.gate_tradability` |
| 9 | 财务核验表（L3，含增速红线 + 半年口径）| `filters.gate_fundamental` |
| 10 | 加速剂（熔断阶梯 + 冰点判定）| `formulas.circuit_breaker` + `is_ice_point` |
| 11 | 已确认口径（六条，不得再询问）| `calibers.describe()` |
| 12 | 候选 → 评分 → 风控信号表（管道视角）| `pipeline.run_pipeline` |
| 13 | 凯利建议 + 仓位 N 精算 | `formulas.kelly_fraction` + `position_size` |
| 14 | 五条可证伪预判 | — |
| 15 | 十五五六张网跟踪池（102 板块 + 12 SW1 + 70 股） | westock `data_sector` |
| 16 | 财富密码融合层 §16+ —— 综合分 S、α_max、盘前 6 项、管道信号、账户骨架 | `playbook.playbook()` |
| 17 | 财务核验（半年口径与 ±N 敏感度）| `conclusions_v2.json` |
| 18 | 明日盘前动作清单 | 派生 |
| 19 | 三类风险（系统性 / 主线单点 / 链条分歧） | 派生 |
| 20 | 免责声明 | — |
| 21 | 元数据（数据源 / 时间戳 / 口径版本） | — |

> 上表是**样式 A（classic，21 章）**的结构。**样式 B（bii，日更默认）** 把同样的内容压到
> **14 页**：封面 → 摘要 → 图 1–8（8 页，每页 = 左文字栏 ‖ 右图卡片）→ 口径 → 风险三情形 →
> 跟踪清单 → **次日 5 条可证伪预判**（等价于样式 A 的第 14 章，也是 19:15 核验任务的读取入口）。
> 两套样式共用同一份 `data.json` 与同一套漏斗/管道，**结论必然一致**；样式 B 不产 PPTX。

## 3b. 十五五跟踪池与三层核验生成器（v2.0 新增）

仓库内置两套「数据 + 生成器」，使本技能可离线复现 WorkBuddy 侧完整产出：

| 资产 | 路径 | 内容 |
|---|---|---|
| 跟踪池快照 | `framework/baseline_15th5_20260911.json` | 十五五 18 方向（6 张网 + 6 新兴支柱 + 6 未来产业）：**102 板块**（boards_unique=102）、**12 SW1**（ind_layer=12）、**70 股**（stocks_unique=70）；含三层核验分位 / 额比 / 区间位置 |
| 口径 v2 结论 | `framework/conclusions_v2_20260911.json` | 六条已确认口径 v2 + 增速红线（硬线 / 减分线）+ L2 / L2.5 / L3 结果 + ±N 敏感度 |
| L1 行业表 | `framework/L1_industries_20260911.json` | 31 个 SW1 行业代码→名称映射 |
| 18 方向生成器 | `reports/build_15th5_report.py` | 纯 stdlib，读 `reports/cache/`，产出「十五五六张网与产业方向三层核验报告」HTML（≈133 KB，含 18 方向 × 板块 / 个股三层核验）|

运行三层核验生成器（无需联网，用内置快照）：

```bash
cd reports && python3 build_15th5_report.py
# → 生成 十五五六张网与产业方向三层核验报告-20260911.html
```

跟踪池口径校验（与 `conclusions_v2` 一致）：硬线 中报同比 ≤ 0 排除；减分线 中报同比 > 0 但 < 上一年度增速 50% 时 −15 分。50% 相对线为框架默认值，收紧为「任何减速即排除」会使过会再减 1 只（恒瑞医药），须随报告披露 ±N 敏感度。

## 4. 六条已确认口径（v2 · 不得再向用户询问）

唯一来源：`strategy/calibers.py`。

| # | 口径 | v2 取值 | 实现模块 |
|---|---|---|---|
| ① | 国企央企背景 | **偏好项**（+6 分），不是门槛 | `filters.gate_fundamental` soe_background |
| ② | 产业偏好 | **新兴科技成长优先**（+8 分） | `filters.gate_fundamental` emerging_tech |
| ③ | 净利润增长率 | **半年口径**（最新中报年内同比） | `filters.gate_fundamental` interim_yoy |
| ④ | 单年亏损 | **减分项**（−10 分）；连续两年年报亏损 = 否决 | `filters.gate_fundamental` annual_loss_years |
| ⑤ | 「链」形态主题 | **跳过 L1 否决权**（行业层仅定性） | `calibers.CHAIN_THEMES` + `filters.gate_industry` |
| ⑥ | 基础可交易性 | **L2.5 独立层**（位于 L2 与 L3 之间） | `filters.gate_tradability` |

**增速红线**（口径③的量化）：

- 硬线：中报同比 ≤ 0 → 排除
- 减分项：中报同比 > 0 但 < 上一年度增速的 50% → 重大减分 −15 分

**50% 相对线**是框架自定默认值，非市场共识。收紧为「任何减速即排除」会使过会数量再减 1 只（恒瑞医药示例），**必须随报告首页披露该 ±N 只敏感度**。

## 5. 技术规格

| 项 | 规格 |
|---|---|
| 框架 | L1 → L2 → L2.5 → L3 四层漏斗 + 财富密码融合层 |
| **样式 A**（classic） | MS 色系（#002B5C / #C5A572 / #60A3D9）· **A4 纵向** · 21 章铺排 · 可选 ECharts（`assets/echarts.min.js`）· 涨红跌绿 · `@media print` |
| 样式 A 图 | 6 张（资金流 / 板块热度 / 个股分位 / 估值 / 龙虎榜席位 / 风险矩阵） |
| 样式 A PDF | Playwright `sync_playwright`（浏览器缺失时自动回退系统 Chrome + CDP）· 先 `emulate_media("print")` 再 goto · **26–38 页** |
| **样式 B**（bii） | BlackRock 投资研究院双栏范式 · **A4 横向 297×210mm** · 左文字栏 295px ‖ 右图表栏 · 黑底「图表结论」条 · Chart.js 4.4.1 **本地内联** · **13 页**（封面 + 12 编号页）· 详见 §12 |
| 样式 B 图 | 8 张（漏斗 / 行业气泡矩阵 / 五维雷达 / 综合分排行 / 财务增速对照 / PB 排序 / 五维分项 / α 账本）|
| 样式 B PDF | 系统 Chrome 无头 + CDP `Page.printToPDF`（`preferCSSPageSize` + `transferMode:'ReturnAsStream'`），由 CSS `@page` 决定方向 |
| PPTX | python-pptx，**26 页**，3 个原生图表（PIE + 2 BAR），PingFang SC 注入 a:latin/a:ea/a:cs，BAR 类目倒序；**仅样式 A 产出**（v2.0 已将跟踪池与 18 方向生成器数据驱动化（framework/），PPTX 模板当日数据注入仍待函数式重写；已知限制，不影响 HTML/PDF）|
| 计算口径 | **22 条**（含 L2.5 可交易性 + 增速红线 + 半年口径）|
| 字体 | PingFang SC（中文），Microsoft YaHei（备选）|
| 色板 | 涨红 #C1272D / 跌绿 #1E8449（中国 A 股习惯，**两种样式都不随机构配色改变**）|

## 6. 策略包结构（`strategy/`）

| 模块 | 行数 | 职责 |
|---|---:|---|
| `calibers.py` | 88 | 六条已确认口径（v2 永久生效）+ 增速红线常量 |
| `formulas.py` | 215 | S / α / 仓位 N / 斐波那契 / 凯利 / 熔断 / 冰点 |
| `filters.py` | 180 | 闸门（L1 / L2.5 / L3）+ 批量过闸 |
| `funnel.py` | 175 | 四层漏斗 + 历史分位 / 区间位置 / 额比 |
| `risk.py` | 145 | α 预算账本 + 三道限额 + 熔断检查 |
| `pipeline.py` | 165 | 候选 → 评分 → 风控信号表 |
| `playbook.py` | 130 | 投资理念 / PLAN_TARGET / 盘前 6 项 / 账户骨架 |
| `test_formulas.py` | 240 | **107 条自检断言** |
| `run_demo.py` | 130 | 一键 demo |
| `sample_data.json` | 120 | 演示数据（9 个候选 + 7 个行业）|

**跟踪池与生成器（v2.0 新增）**

| 目录 / 文件 | 职责 |
|---|---|
| `framework/baseline_15th5_20260911.json` | 十五五 18 方向跟踪池（102 板块 + 12 SW1 + 70 股）+ 三层核验快照 |
| `framework/conclusions_v2_20260911.json` | 六条口径 v2 + 增速红线 + L2/L2.5/L3 结论 + 敏感度 |
| `framework/L1_industries_20260911.json` | 31 个 SW1 行业代码→名称 |
| `reports/build_15th5_report.py` | 18 方向三层核验生成器（纯 stdlib） |
| `reports/cache/` | 生成器所需快照（themes_*.json / ind_*.json / reuse_style.html 等） |

总代码量约 **1,700 行**（不含 HTML/PDF/PPTX 模板与跟踪池数据）。

## 7. 策略包工具脚本

```bash
# 公式自检（必跑，0 失败才视为可用）
python3 strategy/test_formulas.py
# → 通过 107 / 失败 0

# 一键 demo（无需联网）
python3 strategy/run_demo.py
# 或指定数据：
python3 strategy/run_demo.py --data strategy/sample_data.json --equity 2000000 --stage II

# 生成一日报告（默认样式 A：HTML + PDF + PPTX）
python3 scripts/generate_daily.py --date 2026-09-16 --out out/dragon-tiger-20260916

# 只要 BII 双栏版式（样式 B：HTML + PDF，自带三重校验）
python3 scripts/generate_daily.py --style bii --date 2026-09-16 --out out/dragon-tiger-20260916

# 两套版式都出（5 个文件）
python3 scripts/generate_daily.py --style both --date 2026-09-16 --out out/dragon-tiger-20260916

# 样式 B 的底层一条龙（生成 HTML → 起 Chrome → 校验 → 导 PDF → 页数核对）
bash templates/bii/render.sh --data strategy/sample_data.json --date 2026-09-16

# 样式 B + 次日 5 条可证伪预判（第 14 页；契约见 §12.9）
bash templates/bii/render.sh --data strategy/sample_data.json --date 2026-09-16 \
     --predict-file strategy/predictions.example.json

# 任意本地 HTML → PDF（样式 A/B 通用；方向由 HTML 的 @page 决定）
bash templates/bii/cdp_render.sh in.html out.pdf 2400 css

# 生成十五五 18 方向三层核验报告（离线，用内置快照）
cd reports && python3 build_15th5_report.py
```

## 8. 常见失败模式与陷阱

| 陷阱 | 症状 | 修法 |
|---|---|---|
| **提前触发（盘未收盘）** | 11:33 跑出报告：龙虎榜章节为空、涨停数严重偏低、成交额只有半天 | 交易日 **≠** 已收盘。见 §2 第 1 条的「收盘状态」关：须查当日 `lhb` 与 `minute` 末根 ≥1500 |
| 月线两套口径混用 | 报告之间分位/额比不可比 | rank/lo/hi **保留**当月；额比 **剔除**当月（`funnel.amount_ratio(amounts[:-1])`）|
| 用 `volume` 算额比 | 忽略价格因素 | 必须用 `amount`（成交额）|
| 字段名错位 | 同比找不到 | `data_finance` 营收同比 = `TORGrowRate`（**非** `OperatingRevenueYOY`）；归母同比 = `NPParentCompanyYOY` |
| 涨跌颜色 | 与海外习惯混淆 | 涨红 #C1272D / 跌绿 #1E8449（中国 A 股，两种样式都一样）|
| 半年 vs 年度 | 整批结论翻转 | 报告首页必须写死「半年口径」，并报告 ±N 只敏感度 |
| L2.5 与 L3 合并 | 把「不可交易」误报为「基本面不通过」 | L2.5 必须在 L3 之前，剔除结果**单独**列入「不可交易清单」|
| PPTX 复用旧数据 | 当日数据 vs 2026-09-11 硬编码混用 | v1.1 限制已知，v2.0 将 make_pptx 改造为函数式 API |
| **图表全空白（样式 B）** | 8 张 canvas 全白，但 `window.Chart` 正常、控制台报 `Unexpected token ','` 或 `s.slice is not a function` | 占位符拼出非法 JS → 整个 `<script>` 不执行。见 §12.3 坑 1 / 坑 2；生成器已内置 `node --check` 自检 |
| **PDF 导出静默无文件（样式 B）** | 脚本 exit 0 但 PDF 没落地、或只有 1 页空白 | 大 PDF 撞 WebSocket 消息上限 / 连到了 `about:blank` 标签。见 §12.3 坑 3 |
| **封面半出血** | 深色封面四周留白边 | `@page` 的 margin 会裁掉元素的负 margin —— 出血必须靠 `@page{margin:0}` + 页面自身 padding。见 §12.3 坑 4 |
| **纸张变 Letter** | PDF 是 612×792 而不是 A4 | 模板缺 `@page{size:A4 ...}`，`preferCSSPageSize` 无处可依，Chrome 按 locale 回退。→ 给样式 A 的数据版 HTML 补 `@page` |
| **表格空 `tbody` 但不报错** | 页数/溢出/墨量全绿，打开 PDF 才发现某张表是空的 | `rows` 被赋成 `[]` 而非 `list(items)`。几何判据对"内容为空"无感 → **改过页面结构必须目视抽查该页**。见 §12.3 坑 5 |
| **`set -e` 下 `[ -n "$X" ] && ARR+=()` 静默退出** | `render.sh` 传可选参数时脚本在生成前就退出、无任何输出 | AND 列表左侧为假导致整个列表返回非零。→ 改写成 `if [ -n "$X" ]; then ...; fi`。见 §12.3 坑 6 |
| **预判页定位失联（样式 B）** | 19:15 核验任务报"找不到预判节" | 第 14 页标题被改（换全角空格、改数字或量词）。→ 标题须字面保留 `9.1 次日（YYYY-MM-DD）5 条可证伪预判`。见 §12.8 |
| **BII 与 classic 结论分叉** | 同一天两份报告的过会数对不上 | L1 池误用了双条件（分位 **且** 额比）。→ L1 只判分位，额比归 L2 个股层。见 §12.10 修正 #1 |
| **表格行数无上限撑破版心** | 第 13 页页高超阈值数百 px | 跟踪清单行数不设上限（26 行）。→ `_MAX_WATCH = 11`（每行 ≈28px，版心最多容 11 行）。见 §12.10 修正 #5 |
| **产业主题股进不了 L2** | 18 个方向里只有 2 个能跳过 L1 | `CHAIN_THEMES` 名单与实际方向命名不匹配。→ 补齐 `六张网` / `新兴产业` / `未来产业` 等前缀词。见 §12.10 修正 #2 |

完整 11 项陷阱见 `docs/wealth-password-strategy.md` §10。

## 9. 推送到 GitHub 与定时任务

```bash
cd a-share-dragon-tiger-strategy
git init
git add .
git commit -m "feat: A-share dragon-tiger v2.2 (daily default -> BII two-column + next-day falsifiable-prediction page)"
git remote add origin git@github.com:yjkj999999/a-share-dragon-tiger-strategy.git
git push -u origin main
```

定时任务：**两条**，均为「周一至周五」触发，非交易日直接结束。

| 时间 | 任务 | 关键动作 |
|---|---|---|
| 18:00 | A股涨停板龙虎榜深度研判报告 | 取数 → 落盘 `data.json` + `predictions.json` → `generate_daily.py --style bii` → `present_files` |
| 19:15 | 涨停板龙虎榜预判核验 | 读**上一交易日**报告第 14 页（正则定位）→ 逐条判定 → 三层命中率 + 阈值校准 |

仓库不内置 cron —— 接入方（WorkBuddy 定时任务 / OpenClaw / MiMoCode 等）按各自调度器配置。
核验任务的正则与链路规则见 §12.8。

## 10. 依赖

- **Python 3.10+**：`python-pptx`、`lxml`、`Pillow`（样式 A 的 PPTX）；`playwright` 可选
- **Node 22+**：样式 B 的图表校验与 PDF 导出（用内置 `WebSocket` + `fetch`，**无需 npm install**）
- **浏览器**（导 PDF 需要其一）：
  - **系统 Chrome / Edge / Chromium** —— `cdp_render.sh` 自动探测 `/Applications/...` 与 `PATH`
  - 或 Playwright 自带 chromium：`pip install playwright && playwright install chromium`
  - 两者都缺时：样式 B 直接失败；样式 A 会先试 Playwright 再回退 CDP，也失败才报错
- **可选**：westock MCP（实时取数）、IMA OpenAPI（T-1 降级）

> 样式 B 不依赖 npm/Playwright：`templates/bii/chart.umd.js`（Chart.js 4.4.1）与
> `cdp_pdf.js` / `verify_print.js` 已随技能打包，离线可用。

## 11. 免责声明

本 Skill 仅供教育与研究。数据可能为 T-1；任何收益数字为情景或历史，**不构成投资建议**。
市场有风险，投资需谨慎。

---

## 12. 样式 B —— BII 双栏范式变体（v2.1 新增）

复刻 BlackRock 投资研究院（BII）公开材料版式的第二种排版样式，与样式 A 并列。
**内容口径完全一致**（同一套 `strategy/` 漏斗与管道、同一份数据 JSON），
差别只在版面与图表实现 —— 因此**不需要维护第二套结论逻辑**。

### 12.1 目录与文件

| 文件 | 职责 |
|---|---|
| `templates/bii/gen_bii_2col.py` | 生成器（约 800 行）：算模型 → 注入图表数据 → 拼 14 页 HTML，自带双重自检 |
| `templates/bii/chart_js_bii.js` | 8 张 Chart.js 图配置模板（占位符注入，禁止写死数据）|
| `templates/bii/chart.umd.js` | Chart.js 4.4.1（205 KB），**本地内联**，离线自包含 |
| `templates/bii/render.sh` | 一条龙：生成 HTML → 起 Chrome → 校验 → 导 PDF → 页数核对 |
| `templates/bii/cdp_render.sh` | 通用「本地 HTML → PDF」（样式 A/B 共用；`CDP_ENDPOINT` 可复用已有 Chrome）|
| `templates/bii/cdp_pdf.js` | CDP `Page.printToPDF` 导出器（`ReturnAsStream` 分块取流）|
| `templates/bii/verify_print.js` | 在打印尺寸下量：canvas 墨量 + 每页高度 + 横向溢出 |
| `strategy/predictions.example.json` | 第 14 页「次日 5 条可证伪预判」的数据契约示例（见 12.9）|

```bash
# 样式 B 一条龙（推荐）
bash templates/bii/render.sh --data strategy/sample_data.json --date 2026-09-16

# 带次日预判（第 14 页）
bash templates/bii/render.sh --data strategy/today.json --date 2026-09-16 \
     --predict-file out/dragon-tiger-20260916/predictions.json

# 或经由统一下载入口
python3 scripts/generate_daily.py --style bii --date 2026-09-16
```

产物：`涨停板龙虎榜深度研判报告-BII双栏-YYYYMMDD.html` / `.pdf`（14 页，A4 横向）。

### 12.2 版式骨架

```
@page { size: A4 landscape; margin: 0 }          ← 全出血：边距交给 .page 的 padding
.page { width:297mm; min-height:210mm; padding:11mm 12mm 10mm 12mm;
        display:flex; flex-direction:column }
  ├─ .runhead   页码/章节走栏（全页宽）
  ├─ .pbody     默认 grid-template-columns: 295px minmax(0,1fr); gap:22px
  │   ├─ .colL  左文字栏（eyebrow / h2 / lead / 引用块 .pq / 黄底「投资启示」.impl）
  │   └─ .colR  右图表栏 → figure.fig
  │        ├─ .fig-h   图号 + 结论式标题 + 口径副标题
  │        ├─ .fig-b   图体（canvas 包在白底带边框的框里）
  │        ├─ .fig-take 黑底「图表结论」条（结论必须写"所以呢"，不是复述数据）
  │        └─ .fig-src  资料来源脚注
  └─ .runfoot   数据来源 + 页码（全页宽）
```

- 版心 = 297−12−12 = **273mm 宽** × 210−11−10 = **189mm 高** ≈ **1032×714 px @96dpi**
- 纸张 = **297×210mm ≈ 1123×794 px** ← **量溢出要用这个**
- 封面 / 摘要 / 口径 / 风险 / 跟踪清单用 `full=True` → `.pbody.full{grid-template-columns:1fr}`
- 需要通栏的块（如第 14 页底部说明条）直接写 `style="grid-column:1 / -1"`
- **14 页固定**（`TOTAL = 14`）：封面 + 摘要 + 图 1–8（8 页）+ 口径 + 风险三情形 + 跟踪清单 + 次日预判
  （编号页 pno 2–14；生成器末尾有 `len(pages) != TOTAL` 的硬断言，加页忘了改 TOTAL 会直接报错）

### 12.3 七个必踩坑（都已内置防御，别"简化"掉）

**坑 1 · 占位符拼出非法 JS → 所有图表一起不绘**
模板写 `var A={__X__}` 而注入端给的是数组字面量 `['a','b']`，拼出 `{['a','b']}`。
两者都**不报"未替换"**，但语法错误让整个 `<script>` 不执行 —— 症状是
「8 张 canvas 全白，`window.Chart` 却正常加载」。
→ 生成器已加 `check_js_syntax()`：拼完 JS 先 `node --check`，无 node 时退化为括号粗检。
→ 占位符残留检查会先剥掉 `//` 注释（否则注释里举例写的占位符会被误判）。

**坑 2 · 字符串没加引号 → 日期被当减法算**
`jsarr()` 若不给字符串加引号，`2025-09-01` 会被 JS 算成数字 2015，
后续任何 `s.slice()` 直接 `TypeError: s.slice is not a function`，同样连累整段脚本。
→ `jsarr` / `jsdata` 对 `str` 一律加单引号并转义。

**坑 3 · PDF 静默失败 / 导到空白页**
- 大 PDF（base64 后 ≳8MB）走默认单条消息会撞 WebSocket 的
  `Max decompressed message size exceeded`：ws 被浏览器关闭，脚本**exit 0 但文件不落地**。
  → 必须用 `transferMode:'ReturnAsStream'` + `IO.read` 分块（256KB/块）。
- 无头 Chrome 常额外开一个 `about:blank` / `chrome://` 标签，可能排在 `/json/list` 的前面或后面。
  → 选 target 时**优先 `file://` 页面**，否则会导出一张只有 1 页的空白 PDF。

**坑 4 · 封面做不出全出血**
`@page` 的 margin 会裁掉元素的负 margin —— `.cover{margin:-11mm -12mm 0}` 在屏幕上像出血，
打印出来四周一圈白边。同理会整体裁切、页数虚增。
→ 改 `@page{margin:0}`，边距一律由 `.page` 自身 `padding` 提供，`.cover` 用 `width:297mm` 自然铺满。
（副作用：量溢出时的阈值要从 714px 改成 794px，见 12.5。）

**坑 5 · 表格渲染成空 `tbody`，而所有"数字"看起来都对**
第 14 页预判表写成了 `if items: rows, placeholder = [], False` —— 本想赋 `list(items)`，
结果赋了空列表：表头、`有效条数 5/5`、底部说明条**全部正确**，只有 5 行预判是空的。
症状极具迷惑性：页数对、无溢出、无报错、正则也命中，只有打开 PDF 才发现表格是空的。
→ 教训：**表格类渲染必须目视抽查一次成品**（`pymupdf` 抽该页为 PNG 看一眼），
不能只依赖"页数/墨量/溢出"这三条几何判据 —— 它们对"内容为空"完全无感。
（本地快速抽查：`pymupdf.open(pdf)[-1].get_pixmap(dpi=110).save(...)`）

**坑 6 · `set -e` 下的 `[ -n "$X" ] && ARR+=(...)` 会静默退出脚本**
`render.sh` 里传可选参数时，若写成 `[ -n "$PRED" ] && GEN_ARGS+=(--predict-file "$PRED")`，
`$PRED` 为空时左侧判定返回 1，整个 AND 列表返回非零，`set -e` 直接让脚本**在生成之前就退出**
（无任何报错输出）。→ 必须写成 `if [ -n "$PRED" ]; then ... fi`。

**坑 7 · 「按数值升序取前 N」的图，榜首会被两类垃圾占满**
凡形如「指标由低到高排列，取前 N 展示」的图（图 6 PB 是最典型的一类），**必须同时问两个问题**：

1. **这个指标可能为负吗？** —— PB / PE / 增速 / 净额都可能。
   0917 实测：11 只净资产为负标的把 PB 升序前 10 名从头占到位，图里只剩 `−30×`~`−1×` 的负值柱，
   与左栏「估值最低三只」和图结论条**当场互相打脸**。
2. **命中 L2.5 的标的会不会混进来？** —— 退市 / ST / *ST / 零成交 / 负 PB 都在 L2.5 被剔除，
   但它们**仍留在 `data.json` 的 `candidates` 里**（这是契约要求，不许手工删行），
   只要相对指标好看就会占据榜首。0917 二次实测：已退市的「退市观典」（`delisted=True`、股价 ¥0.37、PB 0.23）
   排到第 2 名，被左栏与图结论条同时采纳为「低估值区」标的，与同一份报告第 3 页的
   「L2.5 不可交易清单」**自相矛盾** —— 这正是口径 17 说的
   「相对估值指标无法识别公司已经不存在」。

→ 图 6 已抽出模块级准入函数 `pb_tradable(c)`（PB>0 **且** 未命中退市/ST/*ST），
`pbs`（柱）与 `low_pb`（左栏三只 + 结论条）共用，避免两处判定再次漂移。
→ 命中名称类剔除的标的**要计数并说明，不要静默丢弃**，否则读者会以为榜单漏了标的；
但**不要全量罗列**（0917 有 24 只 ST 股 PB 为正，全列会撑破版心）—— 图结论条只报数量，左栏最多列 4 只示例。
→ 通则：**任何「取前 N」的图，都要先证明入榜集合是"可比的同类"**；负值、退市、ST 各自属不同的性质，
不能因为"数值小"就并列在一起。

**加页时的溢出经验值**：第 14 页左栏高度实测约 555px / 版心 714px；
在左栏再加一段两行的正文就会把页高顶到 810px（超 16px）——校验会拦下并**不导 PDF**，
此时不要去调阈值，去删字。加内容后**必跑** `render.sh`，它会替你把住这一关。

### 12.4 Chart.js 本地内联 + 占位符注入

- CDN 会波动，一旦拉不到就全图空白且不报错 → **`chart.umd.js` 随技能打包**，
  生成时用 `__CHART_LIB__` 占位替换进 HTML。产物 ~250 KB，离线可开。
- 图表 JS 抽成独立 `chart_js_bii.js`，数据一律走 `__XXX__` 占位符 + `str.replace()` 注入，
  **不要**用 f-string 拼（`{{}}` 转义地狱）。
- 每个图表一个 IIFE `(function(){ ... })()`，`animation:false`（否则导 PDF 时可能拍到半张图）。
- 图型元素数设上限 `_MAX_RANK/_MAX_FIN/_MAX_PB/_MAX_DIM/_MAX_BUB`：
  真实候选池可达数十只，不截断会把图挤成一团并顶破版心；**截断数写进图注**声明。

### 12.5 验收四判据（前三条缺一不可）

```bash
# 起无头 Chrome（受限环境必须 --no-sandbox --in-process-gpu；每次全新 user-data-dir 防缓存）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage \
  --disable-gpu --in-process-gpu --user-data-dir=$(mktemp -d) \
  --remote-debugging-port=9333 --window-size=1400,1200 "file:///abs/path/report.html" &

# 判据 1+2：8 张图墨量 >300、每页高 ≤794px、无横向溢出
node templates/bii/verify_print.js http://127.0.0.1:9333 1123 794
```

| # | 判据 | 通过标准 | 为什么 |
|---|---|---|---|
| 1 | 图表墨量 | 8/8 `chart=true` 且 `ink>300` | 只查 `canvas` 存在会被"空白画布"骗过 |
| 2 | 零溢出 | 每页高 ≤ **794px**（纸张高 210mm） | 屏幕视口宽 ≠ 打印版心宽，SVG `width:100%` 会随视口缩放，**必须钉住 1123px 再量** |
| 3 | 页数一致 | PDF 页数 == HTML 的 `.page` + `.cover` 数 | 最硬的判据；有元素顶破页高时 PDF 会多出页，比看截图可靠得多 |
| 4 | **内容非空**（人工／脚本抽查）| 新增或改动的页抽成 PNG 看一眼 | 前三条对「<tbody> 为空」完全无感（见 12.3 坑 5），改过页面结构就必须抽查 |

`render.sh` 已把前三条判据串进流程，任一条不过就**不导 PDF**（避免产出坏件）。
第 4 条无法自动化，但成本极低：

```python
import pymupdf
d = pymupdf.open("out/.../涨停板龙虎榜深度研判报告-BII双栏-YYYYMMDD.pdf")
d[-1].get_pixmap(dpi=110).save("/tmp/p_last.png")   # 看一眼最后一页
```

### 12.6 两种样式对照

| 维度 | 样式 A（classic） | 样式 B（bii） |
|---|---|---|
| 版式 | 单栏铺排，21 章 | 左文字栏 295px ‖ 右图表栏 |
| 纸张 | A4 **纵向** | A4 **横向** |
| 配色 | MS 深蓝 #002B5C + 金 #C5A572 | 黑 #000 + 品牌黄 #FFB500 |
| 图表 | ECharts（可选）| Chart.js 4.4.1（内联必带）|
| 图表数 | 6 | 8 |
| PDF 通道 | Playwright（→ CDP 回退）| 系统 Chrome + CDP |
| 篇幅 | 26–38 页 | 14 页 |
| 附加产物 | PPTX（26 页）| 无 |
| 适用 | 完整研报、需要分发 PPTX | 一页一图快读、机构风版式 |
| 涨跌色 | 涨红 #C1272D / 跌绿 #1E8449 | **同左**（不随机构配色改变）|

### 12.8 次日 5 条可证伪预判页（第 14 页 · v2.2 新增）

19:15 的「预判核验」定时任务以**正则**在报告里定位这一节：
`2?\d\.\d\s*次日（<目标日>）\s*5\s*条可证伪预判`。样式 B 的第 14 页必须**字面保留**该标题：

```html
<h2>9.1 次日（2026-09-17）5 条可证伪预判</h2>
```

- **别改成全角空格**（`\s` 在半角/全角下表现不一致），**别改数字与量词**（`5 条` 是硬性数量），
  改标题 = 核验任务失联（这是踩过的坑）。
- 页内同时把「次日（YYYY-MM-DD）5 条可证伪预判」这一串**再出现一次**（在 lead 正文里），
  便于用 `grep -F` 兜底定位。

版面：左文字栏 = eyebrow + 标题 + lead + 引用块「不可证伪的判断，等于没有判断」+
「5 条的最低覆盖要求」+ 黄底「核验规则」；右栏 = 5 行 × 4 列预判表（# / 预判 / 判据阈值 / 取数来源）；
底部 `.disc` 通栏写核验链路 + 与正文关系 + 免责。**本页不出图**，因此「本报告共 8 张图」不变。

### 12.9 预判数据契约（`predictions.json`）

预判内容**逐日撰写**，不存在于代码里。生成器按 `--predict-file` > `--predictions`（内联）>
`<data 同级>/predictions.json` > `<out>/predictions.json` 的顺序取；**都不给则渲染「示例占位页」**
（并明确标注），因此模板在无预判数据时仍能独立跑通（demo / 冒烟）。

```json
{
  "demo": false,
  "report_date": "2026-09-16",
  "data_basis_date": "2026-09-16",
  "target_date": "2026-09-17",
  "items": [
    {"n": 1,
     "claim":   "恒瑞医药（sh600276）次日额比维持 ≥1.2×，且收盘不破 MA20",
     "falsify": "额比 <1.2× 或收盘 <MA20 → 未命中；仅一项不达标 → 部分命中",
     "source":  "data_kline(period=day, 60 根) 复算 MA20；成交额 vs 近 3 个完整月均值"}
  ]
}
```

生成端**硬校验**（任一不过直接 `exit 1`，宁可不出一页也不出坏件）：

| 校验 | 报错 |
|---|---|
| 顶层必须是对象 | `预判 JSON 顶层必须是对象` |
| `items` 恰好 5 条 | `次日预判必须恰好 5 条（可证伪的硬性数量），实际 N 条` |
| 每条有 `claim` | `第 N 条预判缺 claim（预判内容）` |
| 每条有 `falsify` | `第 N 条预判缺 falsify（可证伪判据 / 观测口径）—— 没有判据的预判次日无法核验` |
| `report_date` 与 `--date` 一致 | 只**告警**不报错（预判挂错交易日很难在成品上肉眼发现，故必须提示）|

`target_date` 缺省时用 `next_trading_day()` 兜底（**只跳周末**，法定节假日无法离线判定），
并在页内标注「按周末顺延近似推断」。**日更时务必显式写 `target_date`**，否则预判会被挂到休市日上。

### 12.10 v2.2 首轮实跑修正（2026-09-16，五处，回归后 107 条断言全绿）

首轮用真实数据跑通 BII 日更时暴露的五处缺陷 —— 前三处会让**结论本身出错**，
后两处让**版式校验挡不住**。全部已修，`strategy/test_formulas.py` 仍 107 条全绿。

| # | 位置 | 症状 | 修法 |
|---|---|---|---|
| 1 | `funnel.run_funnel` 的 L1 池 | 曾用 `gate_industry` 的**双条件**（分位 ≤25% **且** 额比 ≥1.0×）建 L1 池，而契约第七章规定 **L1 只判分位、额比归 L2 个股层**。实测 6 个分位 ≤25% 的行业里只有食品饮料额比达标 → L2 池从 59 只塌缩到 21 只，与同日 classic 管线（过会 26 只）分叉，违背本节开头「两套样式结论必然一致」 | L1 池改为 `ind.rank <= RANK_LOW_THRESHOLD` 单条件；`gen_bii_2col.compute_model` 的 `l1_pass` 同步改，并新增 `l1_vr_ok` 供图 2 说明「额比达标者仅 N 个」 |
| 2 | `calibers.CHAIN_THEMES` | 名单按「XX产业链」撰写，与实际在用的方向命名对不上：18 个方向里只有「六张网-3算力网」「六张网-4新一代通信网」2 个能命中，**口径⑤ 在第 3~18 个方向上形同虚设**，产业主题股被行业分位（中位 59%~81%）整片挡在 L2 之外 | 补齐实际前缀词：`六张网` / `新兴产业` / `未来产业` / `光模块` / `PCB` / `算力设备` / `IDC` / `大模型` / `电力/绿电` |
| 3 | `filters.gate_fundamental` | 中报同比缺失时**只告警不否决**，与契约第七章「关键数据缺失无法验证 = 一票否决」、以及本函数自己「不得默认通过」的注释相矛盾。实测 龙源电力 / 浙江新能 / 华电国际 三只因此混进过会名单，把过会数从 26 抬到 29 | 改为 `reject`。修正后过会 **26 只**，与 classic 完全一致 |
| 4 | `gen_bii_2col` 摘要结语 | 「一句话：有候选，无买点」与 verdict 结语是**硬编码**，在出现 BUY 的日子会与第 12 页「本期触发 BUY 的标的数」直接打架 | 结语与 h2 改由 action 分布决定（`n_buy`）；α 预算用满时写「已用满」而不是「剩余 0 万」 |
| 5 | `gen_bii_2col` 三处版面 | ① 第 7 页硬线名单统计**全候选池**（数百只）→ 左栏顶破 29px；② 第 13 页跟踪清单**行数无上限**（26 行）→ 超阈值 454px；③ `build_inputs` 对 `dispersion=None` 直接 `float()` 崩 | ① 硬线名单限定 L2 池 + 前 6 个截断（`hard_txt`），图 5 高度 372→330；② 新增 `_MAX_WATCH = 11` 并在表下注明总数与截断规则；③ 改 `float(x or 0.0)`，并对缺 `rank/vr` 抛明确错误 |

**顺带修正的测试构造缺陷**：`test_formulas.py` 的「连续两年亏损 / 间隔亏损 / 单年亏损」三条用例
原本未给 `interim_yoy`，修正 #3 之后会先撞上「数据缺失 → 一票否决」而测不到想测的分支 —— 已补足该字段。

**经验（下期直接复用）**
- 出报告前先跑一次**漏斗 dry-run**（直接调 `gen_bii_2col.compute_model`）核对 L1/L2/L2.5/L3
  四层计数，再跑 `render.sh`。四层数字与同日 classic 管线应当一致；**不一致就是口径分叉，先查口径再查版式**。
- 第 13 页跟踪清单的页高对行数近似线性（**每行 ≈28px**）：`pbody = 813px @ 18 行`，
  可容上限 `794 − 44(runhead) − 36(runfoot) − 130(disc) = 584px` → **最多 11 行**。超了减行，别调阈值。
- 第 14 页预判表的页高由 `claim / falsify / source` 长度决定：claim ≤60 字、falsify ≤55 字、
  **source ≤32 字**（该列仅 20% 宽）时表格 ≈460px，可稳过阈值。
- 编辑 `gen_bii_2col.py` 后**必须回读命中行确认落盘**（本轮出现过一次 edit 报成功但文件未变）。

### 12.11 v2.2 次轮实跑修正（2026-09-17，三处：两处结论/图表口径 + 一处图注）

| # | 位置 | 症状 | 修法 |
|---|---|---|---|
| 1 | `gen_bii_2col` 图 6（PB 排序） | 升序取前 `_MAX_PB=10` 但**未过滤负 PB**：9-17 有 11 只净资产为负标的，把榜单从头占满，图上只剩一串负值柱（`ST东时 −30×`…），与左栏「估值最低三只：金地集团 0.23×…」和「PB 为负不属低估值」当场矛盾 | `pbs` 增加 `float(pb) > 0` 过滤；右栏口径副标题写明「仅取 PB > 0（净资产为负者属 L2.5 可交易性问题，已排除）」。负 PB 数量仍保留在图结论条文字里 |
| 2 | `gen_bii_2col` 摘要页 / 风险页「情形二 · 基准情形」 | 硬编码「维持观察…**不主动建仓；α 预算保持空置**」——在触发 BUY 且预算用满的日子，与同一页的「有买点（N 只触发建仓阈值）」和 KPI「α 预算剩余 0 万」直接打架（9-17：4 只 BUY、预算用满 30%） | 抽出 `_scen2` 变量，按 `n_buy` 与 `led['used_pct']` 生成；两处（摘要第 2 页、风险第 12 页）共用同一变量，避免再次分叉 |
| 3 | `gen_bii_2col` 图注 `tail()` | `clamp()` 返回的是**被截掉的数量**，而 `tail()` 把它当**展示数**打印 → 图 6 注出「仅显示前 499 个」，实际只画了 10 根柱（9-16 那份是「前 622 个」）。四张图全部错，只有气泡图（直接用 `_MAX_BUB`）是对的 | `tail(n_cut, n_show)` 改为双参，四个调用点分别传入 `_MAX_RANK / _MAX_FIN / _MAX_PB / _MAX_DIM` |

**教训（可复用）**
- **`clamp()` 的两个返回值语义相反**（show / cut），图注取值时必须回看常量，不能凭变量名。
- **凡「按数值升序取前 N」的图，先问一句「这个指标有没有可能为负」**：负值会整片占满榜单头部。同理适用于 PE、增速、净额类排行。
- **同一份文案若在两页出现，就必须抽成变量**：本期「情形二」两处硬编码，改一处漏一处的风险自 9-16 起就存在。
- **目视抽查要挑「有排序截断」的页**：0.0723 墨量的气泡图看起来正常，而 0.16 墨量的 PB 图才是错的那张 —— 几何判据在这类问题上完全失效。

### 12.12 三处安装同步

```bash
SRC=~/.config/mimocode/skills/a-share-dragon-tiger-report
for D in ~/.openclaw/workspace/skills/a-share-dragon-tiger-report \
         ~/.qclaw/skills/a-share-dragon-tiger-report ; do
  mkdir -p "$D"
  rsync -a --delete "$SRC/" "$D/"
done
# 校验三处一致（SKILL.md 应同 shasum）
shasum ~/.config/mimocode/skills/a-share-dragon-tiger-report/SKILL.md \
       ~/.openclaw/workspace/skills/a-share-dragon-tiger-report/SKILL.md \
       ~/.qclaw/skills/a-share-dragon-tiger-report/SKILL.md
```

---

## 13. 知识蒸馏层（v2.3 新增，2026-09-25）

11 本投资类书籍 → 219 条规则 → 8 个子模块。**核心原则：v2 六条口径不变**，
新知识只做三件事——加分、告警、以及唯一强否决（造假科目接力 ≥2 条强红旗）。

### 13.1 模块清单（`strategy/knowledge.py`）

| 子模块 | 函数 | 来源书籍 | 作用 |
|---|---|---|---|
| 情绪周期 | `sentiment_cycle()` | 同花顺短线实战 | 5 阶段状态机（萌芽→发酵→高潮→分歧→退潮），输出仓位上限与打板许可 |
| 反身性 | `reflexivity()` | 索罗斯投资哲学 | 强化/毁灭/中性标签，指挥持有 vs 逢高兑现 |
| 龙虎榜力量比 | `lhb_power()` | 短线金手3 | 买1卖1、买5卖5、机构共识比、买一独大 → 力量档位 |
| 封板质量 | `seal_quality()` | 同花顺 + 短线金手3 | 封成比、首次封板时间、开板次数、撤单率 → 封板分 |
| 利润质量 | `profit_quality()` | 穿透财报 + 简明财务 | 净现比红旗、科目接力造假扫描（强否决）、商誉/存货/应收预警 |
| 估值锚 | `valuation_anchor()` | 穿透估值 + 周期估值与人性 | PB-ROE、周期顶低 PE 陷阱、红利股息率价值线 |
| 宏观定位 | `macro_dashboard()` | 宏观经济手册 + AI 通胀与武器 | 4 轴标签（CPI/实际利率/货币信用/景气）→ 风格指令 |
| 试错仓位/逃顶 | `probe_position()` / `top_exit_signal()` | 索罗斯 + 凌鹏 | 试探仓 25%、验证溢价线 3%、巨阴(≥4.5%)逃顶 |

阈值全部集中在 `strategy/calibers.py` 的 `KNOWLEDGE` 字典（30+ 键），不散落在代码里。

### 13.2 接入点

1. **L3 闸门**（`strategy/filters.py`）：`profit_quality()` 已接入——
   扣非为负罚分照旧；造假红旗 ≥2 → `veto_suggest` 建议拒绝并标注人工复核。
2. **每日报告**（`scripts/generate_daily.py` §1）：从 `data.json` 的
   `context` 读取 `limit_up_count/broken_rate/lianban_height/prev_premium/...`
   （缺项自动降级），渲染「市场情绪仪表盘」（情绪周期 + 反身性两行表）。
3. 其余函数（`lhb_power/seal_quality/valuation_anchor/macro_dashboard/`）在
   数据管线补齐对应字段后逐个接入，接入前不改变任何现有判定。

### 13.3 测试与回归

```bash
cd ~/.config/mimocode/skills/a-share-dragon-tiger-report
python3 strategy/test_knowledge.py    # → knowledge v2.3 自检：44 通过 / 0 失败
python3 strategy/test_formulas.py     # → 通过 107 / 失败 0（口径版本断言已升 v2.3）
# 冒烟：用 20260924 真实数据端到端出 classic 报告，验证情绪仪表盘渲染
```

### 13.4 蒸馏底稿

11 份逐书蒸馏文档（每书含核心思想、量化规则表、前 5 条升级建议）在
`<workspace>/knowledge_distill/distilled/*.md`。

---

**Author**

本 Skill 由 **Wang Dongjie 王东杰** 创作

资深复合型战略财务专家 · 上市公司资本运作操盘手 · 集团化财务管控与风险治理高级工程师

Wdj_@163.com · 13952453499