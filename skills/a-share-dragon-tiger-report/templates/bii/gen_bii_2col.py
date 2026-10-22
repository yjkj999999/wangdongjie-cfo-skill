#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BII 双栏范式变体 · A股涨停板龙虎榜深度研判报告（A4 横向）

与 templates/report_template.html（样式 A：MS 色系 + ECharts + A4 纵向）并列的
第二种排版样式（样式 B）：BlackRock 投资研究院（BII）的「左文字栏 + 右图表」双栏范式。

页面单位 = 一页 = runhead + (295px 左文字栏 ‖ 自适应右图表栏) + runfoot
右栏卡片 = 图号 + 结论式标题 + 口径副标题 + 图体 + 黑底「图表结论」条 + 资料来源脚注

用法：
    python3 templates/bii/gen_bii_2col.py --data strategy/sample_data.json --date 2026-09-16 \
        --predict-file strategy/predictions.example.json \
        --out out/dragon-tiger-20260916

产出：<out>/涨停板龙虎榜深度研判报告-BII双栏-YYYYMMDD.html（自包含，Chart.js 已内联）

次日 5 条可证伪预判（第 14 页）由 `--predict-file` / `--predictions` 注入；缺省时自动探测
<data 同级>/predictions.json，再退到 <out>/predictions.json。三者都缺则渲染「示例占位页」
（并明确标注），使模板在无预判数据时仍可独立跑通。

⚠️ 三个防坑工具函数（jsarr / jsdata / svgbox / strip_svg_take）都是有来历的，见 SKILL.md §12.3，
   不要"简化"掉。图型元素数均设了上限（_MAX_*），防止真实候选池变大时把图挤成一团。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from strategy import calibers as C          # noqa: E402
from strategy import formulas as F          # noqa: E402
from strategy import funnel as FN           # noqa: E402
from strategy import pipeline as PL         # noqa: E402

CHART_LIB = (HERE / "chart.umd.js").read_text(encoding="utf-8")   # Chart.js 4.4.1 本地内联
CHART_TPL = (HERE / "chart_js_bii.js").read_text(encoding="utf-8")

TOTAL = 14                      # 封面 + 13 个编号页（含「次日 5 条可证伪预判」页）
CODE = "LHB"                    # 运行时按日期填，形如 LHB0916-2026
SRC_LINE = "腾讯自选股（westock-mcp）· 四层漏斗 L1→L2→L2.5→L3 + 财富密码选股策略"

# 图型元素数上限 —— 真实候选池可达数十只，不设上限会把图挤成一团、也会顶破版心高度
_MAX_RANK = 12      # 图 4 综合分排行
_MAX_FIN = 10       # 图 5 财务对照
_MAX_PB = 10        # 图 6 PB 排序
_MAX_DIM = 8        # 图 7 五维分项
_MAX_BUB = 16       # 图 2 行业气泡


def pb_tradable(c: dict) -> bool:
    """图 6（PB 排序）与其配套论述的准入条件。

    要求 **PB > 0** 且 **未命中 L2.5 名称类剔除**（含「退市」/「ST」/「*ST」）。

    历史缺陷：0917 首版只加了 `float(pb) > 0`，漏掉名称类校验 → 已退市的
    「退市观典」（delisted=True、股价 0.37 元）以 PB 0.23 排到第 2 名，
    并被图结论条归入「低估值区（PB ≤2×）」，与同一份报告第 3 页的
    「L2.5 不可交易清单」直接自相矛盾。
    根因与口径 17 完全一致：**相对估值指标无法识别「公司已经不存在」**，
    必须叠加名称类校验；PB 为负同理（净资产为负 ≠ 特别便宜）。
    """
    v = c.get("pb")
    if v is None:
        return False
    try:
        if not float(v) > 0:
            return False
    except (TypeError, ValueError):
        return False
    if c.get("delisted"):
        return False
    nm = str(c.get("name") or "")
    if c.get("is_st") or "退市" in nm or "ST" in nm.upper():
        return False
    return True


# ══════════════════════════════ 防坑工具函数 ══════════════════════════════
def jsarr(d: Any) -> str:
    """输出 JS 数组字面量。

    ⚠️ 字符串必须加引号：日期/代码这类值若不引号，JS 会把 `2025-09-01` 当成
    **减法算式**算成数字 2015，后续任何 s.slice()/toFixed() 都会抛
    `TypeError: s.slice is not a function`，而**顶层 IIFE 抛错会让同一 <script>
    里后面所有图表一起不执行** —— 症状是"所有 canvas 空白但 window.Chart 正常"。
    """
    out = []
    for v in d:
        if isinstance(v, str):
            out.append("'" + v.replace("\\", "\\\\").replace("'", "\\'") + "'")
        elif v is None:
            out.append("null")
        elif isinstance(v, bool):
            out.append("true" if v else "false")
        else:
            out.append(str(v))
    return "[" + ",".join(out) + "]"


def jsdata(obj: Any) -> str:
    """把嵌套 dict/list 序列化为 JS 字面量（字符串同样必须加引号）。"""
    if isinstance(obj, dict):
        return "{" + ",".join(f"{k}:{jsdata(v)}" for k, v in obj.items()) + "}"
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(jsdata(v) for v in obj) + "]"
    if isinstance(obj, str):
        return "'" + obj.replace("\\", "\\\\").replace("'", "\\'") + "'"
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    return str(obj)


def check_js_syntax(js: str, label: str = "chart_js") -> None:
    """JS 语法自检 —— 占位符检查只能发现"没替换"，发现不了"替换成了非法字面量"。

    ⚠️ 反面教材：模板里写 `var A={__X__}` 而注入端给的是数组字面量 `['a','b']`，
    两者都没报"未替换"，但拼出来是 `{['a','b']}` —— 语法错误，整段脚本不执行，
    8 张图全空白、而 window.Chart 却正常加载，排查起来极费时间。

    这里用 `node --check` 做真正的语法解析；无 node 时退化为括号配对粗检并给出提示。
    """
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(js)
        tmp = fh.name
    try:
        try:
            p = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
            if p.returncode != 0:
                msg = (p.stderr or p.stdout).strip().splitlines()
                detail = " / ".join(msg[:4]) if msg else "unknown"
                raise SystemExit(f"[!] {label} 存在 JS 语法错误：{detail}")
            return
        except FileNotFoundError:
            pass  # 无 node：退化为粗检
        # 粗检：括号/引号配对（能抓住大多数手写失误，但抓不住上面那种语义错）
        pairs = {")": "(", "]": "[", "}": "{"}
        stack: list[str] = []
        quote = None
        esc = False
        for ch in js:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if quote:
                if ch == quote:
                    quote = None
                continue
            if ch in "'\"`":
                quote = ch
                continue
            if ch in "([{":
                stack.append(ch)
            elif ch in ")]}":
                if not stack or stack.pop() != pairs[ch]:
                    raise SystemExit(f"[!] {label} 括号不配对（粗检）")
        if stack or quote:
            raise SystemExit(f"[!] {label} 括号/引号未闭合（粗检）")
        print(f"[i] 未找到 node，{label} 仅做括号粗检")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def svgbox(s: str, h: int | None = None) -> str:
    """内联 SVG：加 display:block 消除行内基线间隙；h=None 时按等比自然高度渲染（最清晰）。"""
    i = s.find(">")
    if i < 0:
        return s
    root = s[:i].replace('width="100%"', 'width="100%" preserveAspectRatio="xMidYMid meet"')
    style = "display:block;width:100%" + (f";height:{h}px" if h else "")
    return root + f' style="{style}"' + s[i:]


def strip_svg_take(s: str) -> str:
    """剔除 SVG 尾部内嵌的「图表结论」黑条（卡片自身已有 fig-take 条），并把 viewBox 收紧到内容下沿。

    复用外部脚本生成的 SVG（桑基图 / 分歧树 / 漏斗示意）时会踩到，
    否则页面上会出现**两条「图表结论」**。
    """
    k = s.rfind("</svg>")
    if k > 0:
        seg = s[:k]
        i = seg.rfind("<rect")
        if i >= 0 and "图表结论" in seg[i:]:
            s = seg[:i] + "</svg>"
    bot = 0.0
    for v in re.findall(r'\by="(-?[\d.]+)"', s):
        bot = max(bot, float(v))
    for m in re.finditer(r"<rect\b[^>]*>", s):
        t = m.group(0)
        y = re.search(r'\by="(-?[\d.]+)"', t)
        h = re.search(r'\bheight="([\d.]+)"', t)
        if y and h:
            bot = max(bot, float(y.group(1)) + float(h.group(1)))
    if bot > 0:
        s = re.sub(r'(viewBox="0 0 \d+ )\d+(")',
                   lambda m: m.group(1) + str(int(bot + 8)) + m.group(2), s, count=1)
    return s


# ══════════════════════════════ CSS ══════════════════════════════
CSS = """
:root{
  --bk:#000000; --by:#FFB500; --by-d:#C98A00; --by-l:#FFF4D6; --by-l2:#FFE9B0;
  --gy:#C9C9C4; --gy2:#9E9E98; --bg:#F7F7F5; --bw:#FFFFFF;
  --bd:#E2E2DD; --bd2:#EFEFEA; --t2:#4A4A4A; --t3:#8C8C8C;
  /* A 股习惯：涨红跌绿 —— 不随机构范式改变 */
  --up:#C1272D; --dn:#1E8449;
}
*{box-sizing:border-box;}
@page{ size: A4 landscape; margin: 0; }
html,body{margin:0;padding:0;background:#EDEDEA;}
body{font-family:"Helvetica Neue",Helvetica,Arial,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  font-size:11.5px;line-height:1.72;-webkit-font-smoothing:antialiased;}
b{font-weight:600;}
.up{color:var(--up);} .dn{color:var(--dn);} .fl{color:var(--t3);}

/* ── 页 ── */
/* 全出血方案：@page margin:0，边距由 .page 自身 padding 提供。
   这样封面才能真的铺满整张纸（负 margin 在打印时会被 page margin 裁掉，做不出出血）。
   版心 = 297−12−12 = 273mm 宽 × 210−11−10 = 189mm 高 ≈ 1032×714 px @96dpi */
.page{width:297mm;min-height:210mm;padding:11mm 12mm 10mm 12mm;
      display:flex;flex-direction:column;
      page-break-after:always;break-after:page;}
.page:last-child{page-break-after:auto;break-after:auto;}
.runhead{display:flex;justify-content:space-between;align-items:baseline;
  font-size:8.5px;color:var(--t3);letter-spacing:.5px;padding-bottom:4px;
  border-bottom:1px solid var(--bd);margin-bottom:10px;text-transform:uppercase;flex:0 0 auto;}
.runfoot{display:flex;justify-content:space-between;font-size:8.5px;color:var(--t3);
  border-top:1px solid var(--bd);padding-top:4px;margin-top:auto;flex:0 0 auto;}
.pbody{flex:1;display:grid;grid-template-columns:295px minmax(0,1fr);gap:22px;align-content:start;}
.pbody.full{grid-template-columns:1fr;}

/* ── 左文字栏 ── */
.colL{font-size:11.5px;line-height:1.78;}
.eyebrow{font-size:9px;font-weight:700;color:var(--by-d);letter-spacing:1.5px;
  display:block;margin-bottom:5px;}
.colL h2{font-size:19px;font-weight:700;line-height:1.26;margin:0 0 10px;letter-spacing:-.4px;}
.colL p{margin:0 0 7px;}
.colL p.lead{font-size:12.5px;color:var(--t2);line-height:1.7;}
.pq{border-left:3px solid var(--by);padding:2px 0 2px 11px;margin:11px 0;
    font-size:13px;line-height:1.5;font-weight:600;color:var(--bk);}
.pq span{display:block;font-size:9px;font-weight:400;color:var(--t3);margin-top:4px;letter-spacing:.4px;}
.impl{background:var(--by-l);padding:9px 13px;margin:11px 0 0;}
.impl .k{font-size:9px;font-weight:700;color:var(--by-d);letter-spacing:1.2px;display:block;margin-bottom:4px;}
.impl ul{margin:0;padding-left:15px;font-size:11px;line-height:1.56;}
.impl li{margin:3px 0;}

/* ── 右图表栏 ── */
.colR{min-width:0;}
.fig{margin:0;}
.fig-h{border-left:4px solid var(--by);padding-left:10px;margin-bottom:8px;}
.fig-h .n{font-size:9px;font-weight:700;color:var(--by-d);letter-spacing:1.4px;display:block;margin-bottom:1px;}
.fig-h h3{font-size:15.5px;font-weight:700;margin:0 0 2px;letter-spacing:-.3px;line-height:1.28;}
.fig-h .sd{font-size:10.5px;color:var(--t3);margin:0;line-height:1.5;}
.fig-b{background:#fff;border:1px solid var(--bd);padding:8px 7px;}
.fig-b.tight{padding:6px 5px;}
.fig-take{background:var(--bk);color:#fff;padding:8px 13px;font-size:11px;line-height:1.54;}
.fig-take .k{font-weight:700;color:var(--by);letter-spacing:.5px;margin-right:7px;}
.fig-take b{color:var(--by);}
.fig-src{font-size:9px;color:var(--t3);line-height:1.58;margin-top:6px;}
.fig-src b{color:var(--t2);font-weight:600;}
canvas{display:block;margin:0 auto;}

/* ── 表格 ── */
table{width:100%;border-collapse:collapse;font-size:11px;table-layout:fixed;}
th{background:var(--bk);color:#fff;font-weight:600;font-size:10px;padding:5.5px 5px;
   text-align:right;white-space:nowrap;letter-spacing:.2px;}
th:first-child,td:first-child{text-align:left;}
td{padding:5px 5px;text-align:right;border-bottom:1px solid var(--bd2);
   white-space:nowrap;font-variant-numeric:tabular-nums;}
tbody tr:last-child td{border-bottom:none;}
tbody tr:nth-child(even){background:#FCFCFA;}
.hi{background:var(--by-l) !important;font-weight:600;}
.tag{display:inline-block;font-size:9px;padding:1px 5px;border-radius:2px;
     background:var(--bk);color:var(--by);font-weight:700;margin-left:4px;vertical-align:1px;}
.tag.g{background:var(--bd);color:var(--t2);}
.tcap{font-size:9px;color:var(--t3);margin-top:5px;line-height:1.55;}

/* ── 封面（全出血：占满整张 A4 横向，无白边） ── */
.cover{background:var(--bk);color:#fff;min-height:210mm;display:flex;flex-direction:column;
       width:297mm;page-break-after:always;break-after:page;
       padding:15mm 18mm 11mm;}
.cover .brand{display:flex;align-items:center;gap:9px;margin-bottom:34px;}
.cover .brand .dot{width:14px;height:14px;background:var(--by);}
.cover .brand .nm{font-size:11px;letter-spacing:2.8px;font-weight:700;color:var(--by);}
.cover .brand .code{margin-left:auto;font-size:9px;color:#7A7A7A;letter-spacing:.6px;}
.cover h1{font-size:38px;font-weight:700;line-height:1.16;margin:0 0 14px;letter-spacing:-1px;max-width:780px;}
.cover h1 em{font-style:normal;color:var(--by);}
.cover .sub{font-size:13.5px;color:#C9C9C9;line-height:1.62;max-width:680px;margin:0 0 28px;}
.cover .rule{height:4px;background:var(--by);width:86px;margin-bottom:22px;}
.cover .meta{font-size:10.5px;color:#8C8C8C;line-height:1.95;margin-top:auto;max-width:930px;}
.cover .meta b{color:#DADADA;font-weight:500;}

/* ── 摘要页 ── */
.verdict{background:var(--bk);color:#fff;padding:15px 19px;font-size:12.5px;line-height:1.78;margin:0 0 16px;}
.verdict .k{display:inline-block;background:var(--by);color:#000;font-size:9.5px;font-weight:700;
            padding:1.5px 8px;letter-spacing:.9px;margin-bottom:7px;}
.verdict b{color:var(--by);font-weight:600;}
.kpis{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:0;
      border-top:1px solid var(--bd);border-left:1px solid var(--bd);margin-bottom:14px;}
.kpi{padding:9px 11px;border-right:1px solid var(--bd);border-bottom:1px solid var(--bd);}
.kpi .l{font-size:9.5px;color:var(--t3);margin:0 0 3px;line-height:1.35;}
.kpi .v{font-size:18px;font-weight:700;letter-spacing:-.5px;margin:0;font-variant-numeric:tabular-nums;line-height:1.2;}
.kpi .s{font-size:9px;color:var(--t3);margin:3px 0 0;font-variant-numeric:tabular-nums;line-height:1.35;}
.kpi.hl{background:var(--by-l);}
.three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:4px;}
.three .impl{margin:0;}

.risk{border:1px solid #E8C4C4;border-left:4px solid var(--up);background:#FDF6F6;
      padding:12px 16px;font-size:11.5px;line-height:1.7;}
.risk ol{margin:0;padding-left:17px;} .risk li{margin:5px 0;}
.disc{background:var(--bg);border-top:3px solid var(--bk);padding:11px 15px;
      font-size:9px;color:var(--t3);line-height:1.8;margin-top:14px;}
.disc b{color:var(--t2);}

@media print{
  html,body{background:#fff !important;}
  *{-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important;}
  .page{min-height:210mm;}
  table{width:100% !important;table-layout:fixed !important;}
  th{position:static !important;}
  thead{display:table-header-group;}
  tr{break-inside:avoid;page-break-inside:avoid;}
  .fig,.impl,.kpis,.three,.risk,.disc{break-inside:avoid;page-break-inside:avoid;}
  .cover{min-height:210mm;}
}
"""


# ══════════════════════════════ 组件 ══════════════════════════════
def page(inner: str, pno: int, sec: str = "", full: bool = False) -> str:
    cls = "pbody full" if full else "pbody"
    return (
        '<section class="page">\n'
        f'<div class="runhead"><span class="sec">{sec}</span>'
        f'<span>{CODE}　·　{pno}/{TOTAL}</span></div>\n'
        f'<div class="{cls}">{inner}</div>\n'
        f'<div class="runfoot"><span>数据来源：{SRC_LINE}</span><span>{pno}</span></div>\n'
        "</section>"
    )


def two(left: str, right: str) -> str:
    return f'<div class="colL">{left}</div><div class="colR">{right}</div>'


def card(n: str, title: str, sub: str, body: str, take: str, src: str) -> str:
    return (
        '<figure class="fig">\n'
        f'<div class="fig-h"><span class="n">图 {n}</span><h3>{title}</h3>'
        f'<p class="sd">{sub}</p></div>\n'
        f'<div class="fig-b">{body}</div>\n'
        f'<div class="fig-take"><span class="k">图表结论</span>{take}</div>\n'
        f'<p class="fig-src">{src}</p>\n'
        "</figure>"
    )


def cv(cid: str, w: int = 678, h: int = 396) -> str:
    return f'<canvas id="{cid}" width="{w}" height="{h}"></canvas>'


def eyebrow(t: str) -> str:
    return f'<span class="eyebrow">{t}</span>'


def pq(text: str, who: str = "") -> str:
    w = f"<span>{who}</span>" if who else ""
    return f'<div class="pq">{text}{w}</div>'


def impl(items: list[str], title: str = "投资启示") -> str:
    li = "".join(f"<li>{x}</li>" for x in items)
    return f'<div class="impl"><span class="k">{title}</span><ul>{li}</ul></div>'


def clamp(items: list, n: int) -> tuple[list, int]:
    """截断到 n 个并返回被截掉的数量（用于在图注里声明「仅显示前 N」）。"""
    if len(items) <= n:
        return list(items), 0
    return list(items[:n]), len(items) - n


# ══════════════════════════ 次日 5 条可证伪预判 ══════════════════════════
def next_trading_day(date_str: str) -> str:
    """下一「交易日」的**近似**值：只跳过周末。

    ⚠️ 法定节假日无法离线判定（需要连接器 trade-calendar）。所以日更时**必须**由
    predictions.json 显式给出 target_date；本函数仅作兜底，命中兜底时页面会标注
    「近似推断」——否则预判会被挂到一个休市日上，次日核验任务直接扑空。
    """
    d = dt.date.fromisoformat(date_str[:10]) + dt.timedelta(days=1)
    while d.weekday() >= 5:           # 5=周六 6=周日
        d += dt.timedelta(days=1)
    return d.isoformat()


PRED_FIELDS = ("claim", "falsify", "source")


def load_predictions(args, data_path: pathlib.Path, out_dir: pathlib.Path) -> dict:
    """读取次日预判：`--predictions`（内联）> `--predict-file` > 自动探测 predictions.json。

    自动探测顺序：<data 同级>/predictions.json → <out 目录>/predictions.json。
    一个都找不到时返回 {} —— 生成端会渲染「示例占位页」，而不是报错，
    这样模板本身在无预判数据时仍可独立跑通（demo / 冒烟）。
    """
    raw: str | None = None
    src: str | None = None
    if args.predictions:
        raw, src = args.predictions, "--predictions（内联）"
    else:
        cands: list[pathlib.Path] = []
        if args.predict_file:
            cands.append(pathlib.Path(args.predict_file).expanduser())
        cands += [data_path.parent / "predictions.json", out_dir / "predictions.json"]
        for p in cands:
            if p.exists():
                raw, src = p.read_text(encoding="utf-8"), str(p)
                break
    if raw is None:
        print("[i] 未找到次日预判（--predict-file / --predictions / predictions.json），"
              "本页将渲染「示例占位」。")
        return {}

    try:
        d = json.loads(raw)
    except Exception as e:                                  # noqa: BLE001
        sys.exit(f"[!] 预判 JSON 解析失败（{src}）：{e}")
    if not isinstance(d, dict):
        sys.exit(f"[!] 预判 JSON 顶层必须是对象（{src}）")
    items = d.get("items") or []
    if len(items) != 5:
        sys.exit(f"[!] 次日预判必须恰好 5 条（可证伪的硬性数量），实际 {len(items)} 条：{src}")
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            sys.exit(f"[!] 第 {i} 条预判不是对象：{src}")
        it.setdefault("n", i)
        if not str(it.get("claim") or "").strip():
            sys.exit(f"[!] 第 {i} 条预判缺 `claim`（预判内容）：{src}")
        if not str(it.get("falsify") or "").strip():
            sys.exit(f"[!] 第 {i} 条预判缺 `falsify`（可证伪判据 / 观测口径）：{src} —— "
                     f"没有判据的预判次日无法核验，等于没写。")
    d.setdefault("target_date", "")
    d["_src"] = src
    return d


def build_pred_page(pred: dict, date: str) -> str:
    """第 14 页 · 次日 5 条可证伪预判（BII 双栏：左文字栏 ‖ 右预判表）。

    ⚠️ 标题必须保留 `9.1 次日（YYYY-MM-DD）5 条可证伪预判` 这一**字面形式**：
    19:15 的核验任务用正则 `2?\\d\\.\\d\\s*次日（<目标日>）\\s*5\\s*条可证伪预判`
    定位本节。改标题 = 核验任务失联（这是踩过的坑，见 SKILL.md §12.4）。
    因此这里刻意用**半角空格**（`\\s` 在各种引擎下都匹配），不要换成全角空格。
    """
    pred = pred or {}
    raw_tgt = str(pred.get("target_date") or "").strip()
    tgt = raw_tgt or next_trading_day(date)
    tgt_src = ("由 predictions.json 显式给出" if raw_tgt
               else "按周末顺延近似推断，节假日以交易日历为准")
    basis = str(pred.get("data_basis_date") or date)
    items = list(pred.get("items") or [])

    if items:
        rows, placeholder = list(items), False      # ⚠️ 这里是 list(items)，不是 []——
    else:                                           #    写成 [] 会让表格渲染成空 tbody，
        placeholder = True                          #    而「有效条数 5/5」照旧正确，很难一眼看出
        rows = [{"n": i, "claim": "（示例占位 —— 日更时由 18:00 任务写入 predictions.json）",
                 "falsify": "—", "source": "—"} for i in range(1, 6)]

    body = "".join(
        f"<tr><td><span class='tag'>{it.get('n', i + 1)}</span></td>"
        f"<td style=\"text-align:left;white-space:normal\">{it.get('claim', '—')}</td>"
        f"<td style=\"text-align:left;white-space:normal\">{it.get('falsify') or '—'}</td>"
        f"<td style=\"text-align:left;white-space:normal\">{it.get('source') or '—'}</td></tr>"
        for i, it in enumerate(rows))

    warn = ""
    if placeholder:
        warn = "　<b>⚠ 本页为示例占位：未提供 predictions.json，5 条预判为空。</b>"
    elif pred.get("demo"):
        warn = "　<b>⚠ 本页预判为示例内容（随演示数据一同生成），非真实盘后预判。</b>"

    n_real = 5 if items else 0
    L = f'''{eyebrow("09　次日预判 · FALSIFIABLE CALLS")}
<h2>9.1 次日（{tgt}）5 条可证伪预判</h2>
<p class="lead">本页写出次日（{tgt}）5 条可证伪预判。预判不是观点，是<b>待检验的命题</b> ——
5 条一律写成「能被次日数据推翻」的形式，指明标的、口径、方向与阈值；任一要素缺失，
盘后就无法判定命中与否，预判也就失去了复盘价值。</p>
{pq("不可证伪的判断，等于没有判断。", "本页的写作纪律")}
<p><b>5 条的最低覆盖要求</b>　① 过会标的的量价确认；② L2.5 可交易性（防退市 / ST / PB&lt;0）；
③ 行业或方向层的分位与额比；④ 资金面（主力净额 / 龙虎榜净买卖）；⑤ 本期结论本身（过会数或名单变化）。</p>
{impl(["<b>判定三态</b>：命中 / 部分命中 / 未命中；含子条件者必须分腿判定（腿 A / 腿 B）。",
       "<b>三层命中率</b>：完全命中率、含部分命中口径、加权命中率（命中 1.0 · 部分 0.5 · 未命中 0）。",
       "<b>阈值校准</b>：每条须标注阈值「过严 / 合适 / 过松」，并给出下一期建议阈值。"],
      "核验规则（次日 19:15 自动执行）")}'''

    R = f'''<table>
<colgroup><col style="width:6%"><col style="width:39%"><col style="width:35%"><col style="width:20%"></colgroup>
<thead><tr><th>#</th><th>预判（可证伪陈述）</th><th>判据阈值（观测口径）</th><th>取数来源</th></tr></thead>
<tbody>{body}</tbody></table>
<p class="tcap"><b>读法</b>　「判据阈值」栏写死了「命中 / 未命中」的分界线，是这 5 条可核验的关键；
该栏若为「—」，则该条<b>不可核验</b>，须在次日盘中补齐后才算成立。预判目标日为
<b>{tgt}</b> —— {tgt_src}；数据基准日 <b>{basis}</b>。<br>
<b>有效条数</b>　{n_real}/5。</p>'''

    # 说明条通栏（grid-column:1/-1）—— 与第 11 / 13 页的 .disc 用法保持一致，同时把版心底部填满
    D = f'''<div class="disc" style="grid-column:1 / -1">
<b>核验链路</b>　次日 19:15 的「预判核验」任务读本页 5 条，逐条给出「当日实际值（含前值对比）→
判定 → 偏差归因（① 资金未延续 / ② 指数板块拖累 / ③ 观测锚点层级错误 / ④ 阈值未触发或设定过严）」，
并汇总三层命中率与阈值校准建议；核验结论回写为下一期的置信度调整依据。<br>
<b>与正文的关系</b>　第 13 页给出「下一交易日盯住什么位」，本页给出「下一交易日哪些命题必须成立」——
前者是观察位，后者是可验证命题，两者缺一不可。<br>
<b>口径与免责</b>　所有阈值基于 {date} 盘后快照测算；本页为技术测算参考，<b>不构成任何投资建议</b>。{warn}
</div>'''
    return page(two(L, R) + D, TOTAL, "09　次日预判")


# ══════════════════════════════ 数据装配 ══════════════════════════════
def build_inputs(data: dict) -> tuple[list, list]:
    # dispersion / note 允许为 None（取数缺口），一律降级为 0.0 / ""；
    # rank / vr 是入池判定的必需字段，缺失即数据错误，直接抛错而不是静默降级。
    for i in data.get("industries", []):
        if i.get("rank") is None or i.get("vr") is None:
            raise SystemExit(f"[!] industries 条目缺 rank/vr（必需字段）：{i.get('name') or i.get('code')}")
    inds = [FN.Industry(i["code"], i["name"], float(i["rank"]), float(i["vr"]),
                        float(i.get("dispersion") or 0.0), i.get("note") or "")
            for i in data.get("industries", [])]
    stocks = []
    for c in data.get("candidates", []):
        raw = {k: v for k, v in c.items()
               if k not in ("code", "name", "sector", "rank", "vr")}
        stocks.append(FN.Stock(c["code"], c["name"], c.get("sector", ""),
                               float(c["rank"]) if c.get("rank") is not None else None,
                               float(c["vr"]) if c.get("vr") is not None else None,
                               raw))
    return inds, stocks


def compute_model(data: dict) -> dict:
    inds, stocks = build_inputs(data)
    fr = FN.run_funnel(inds, stocks)
    ctx = data.get("context", {}) or {}
    equity = float(ctx.get("equity", 1_000_000))
    stage = str(ctx.get("stage", "II")).upper()
    ice = F.is_ice_point(int(ctx.get("limit_up_count", 60)),
                         float(ctx.get("broken_rate", 0.2)),
                         float(ctx.get("index_pct", 0))) if ctx else False
    basis = [s.merged for s in fr.l3_pass] or data.get("candidates", [])
    result = PL.run_pipeline(basis, equity=equity, stage=stage, ice_point=ice)
    # L1 只判「位置」：3 年分位 ≤ 25%。额比 ≥1.0× 归 L2 个股层（口径分工见 funnel.run_funnel）。
    l1_pass = [i for i in inds if i.rank <= C.RANK_LOW_THRESHOLD]
    l1_vr_ok = [i for i in l1_pass if i.vr >= C.VR_THRESHOLD]
    return {"inds": inds, "fr": fr, "ctx": ctx, "equity": equity, "stage": stage,
            "ice": ice, "res": result, "l1_pass": l1_pass, "l1_vr_ok": l1_vr_ok}


# ══════════════════════════════ 图表数据注入 ══════════════════════════════
def inject_charts(m: dict, by_code: dict, by_name: dict) -> str:
    res, fr, inds = m["res"], m["fr"], m["inds"]

    # 图1 个股维度漏斗（保持单调递减；L1 为行业粒度，单独在正文说明）
    stage_l = ["候选池 L0", "L2 技术面入池", "L2.5 可交易", "L3 基本面通过"]
    stage_v = [len(by_code), len(fr.l2_pass),
               len(fr.l2_pass) - len(fr.l2_5_removed), len(fr.l3_pass)]

    # 图2 行业气泡（按分位升序取前 N，截断时在图注声明）
    ind_sorted = sorted(inds, key=lambda i: i.rank)
    ind_show, ind_cut = clamp(ind_sorted, _MAX_BUB)
    ind_n = [i.name for i in ind_show]
    ind_rank = [round(i.rank, 1) for i in ind_show]
    ind_vr = [round(i.vr, 2) for i in ind_show]
    ind_disp = [round(i.dispersion, 1) for i in ind_show]

    # 图3 雷达：综合分前 3
    rows_desc = sorted(res["rows"], key=lambda r: -r.score)
    radar_rows = rows_desc[:3]
    radar_labels = ["技术面", "资金面", "基本面", "周期位置", "斐波那契"]
    radar_sets = []
    for r in radar_rows:
        c = by_code.get(r.code) or by_name.get(r.name) or {}
        radar_sets.append({"label": r.name, "data": [
            float(c.get("tech", 0) or 0), float(c.get("flow", 0) or 0),
            float(c.get("fund", 0) or 0), float(c.get("cycle", 0) or 0),
            float(c.get("fib", 0) or 0)]})

    # 图4 综合分排行（降序，前 N）
    rank_show, rank_cut = clamp(rows_desc, _MAX_RANK)
    score_n = [r.name for r in rank_show]
    score_v = [round(r.score, 1) for r in rank_show]
    score_act = [r.action for r in rank_show]

    # 图5 财务：中报同比 vs 上年度增速（按综合分顺序，取前 N 个有数据的）
    fin_pool = []
    for r in rows_desc:
        c = by_code.get(r.code) or {}
        if c.get("interim_yoy") is None or c.get("prior_fy_yoy") is None:
            continue
        fin_pool.append((r.name, round(float(c["interim_yoy"]), 4),
                         round(float(c["prior_fy_yoy"]), 4)))
    fin_show, fin_cut = clamp(fin_pool, _MAX_FIN)
    fin_n = [x[0] for x in fin_show]
    fin_i = [x[1] for x in fin_show]
    fin_p = [x[2] for x in fin_show]

    # 图6 PB 排序（升序，前 N）—— 只排「可交易且 PB 为正」的标的。
    # 历史缺陷一：不过滤负 PB 时，升序前 10 名会被「净资产为负」的标的全部占满
    # （0917 实测 11 只负 PB 把榜单从头占到位），图里只剩负值柱，
    # 与左栏「估值最低三只」和「PB 为负不属低估值」的论述直接矛盾（0917 修正）。
    # 历史缺陷二：只过滤负 PB 仍不够 —— 已退市的「退市观典」(PB 0.23) 会排到第 2 名，
    # 与同报告 L2.5 不可交易清单自相矛盾。故统一走 pb_tradable()（0917 二次修正）。
    pbs = sorted([(c["name"], float(c["pb"])) for c in by_code.values()
                  if pb_tradable(c)], key=lambda x: x[1])
    pb_show, pb_cut = clamp(pbs, _MAX_PB)
    pb_n = [x[0] for x in pb_show]
    pb_v = [round(x[1], 2) for x in pb_show]

    # 图7 五维分项（按综合分顺序，前 N）
    dim_show, dim_cut = clamp(rows_desc, _MAX_DIM)
    dim_labels = [r.name for r in dim_show]
    dim_keys = [("tech", "技术面"), ("flow", "资金面"), ("fund", "基本面"),
                ("cycle", "周期位置"), ("fib", "斐波那契")]
    dim_sets = [{"label": lab, "data": [
        float((by_code.get(r.code) or {}).get(k, 0) or 0) for r in dim_show]}
        for k, lab in dim_keys]

    # 图8 α 账本（万元）
    led = res["ledger"]
    alpha_max = led["equity"] * led["alpha_budget"] / 10000.0
    alpha_used = float(led.get("open_notional", 0)) / 10000.0
    alpha_remain = max(0.0, alpha_max - alpha_used)

    # 截断声明（写进图注，避免读者误以为看的是全量）
    notes = {
        "bub_cut": ind_cut, "rank_cut": rank_cut, "fin_cut": fin_cut,
        "pb_cut": pb_cut, "dim_cut": dim_cut,
    }

    js = CHART_TPL
    repl = {
        "__STAGE_L__": jsarr(stage_l),
        "__STAGE_V__": jsarr(stage_v),
        "__IND_N__": jsarr(ind_n),
        "__IND_RANK__": jsarr(ind_rank),
        "__IND_VR__": jsarr(ind_vr),
        "__IND_DISP__": jsarr(ind_disp),
        "__RADAR_LABELS__": jsarr(radar_labels),
        "__RADAR_SETS__": jsdata(radar_sets),
        "__SCORE_N__": jsarr(score_n),
        "__SCORE_V__": jsarr(score_v),
        "__SCORE_ACT__": jsarr(score_act),
        "__FIN_N__": jsarr(fin_n),
        "__FIN_INTERIM__": jsarr(fin_i),
        "__FIN_PRIOR__": jsarr(fin_p),
        "__PB_N__": jsarr(pb_n),
        "__PB_V__": jsarr(pb_v),
        "__DIM_LABELS__": jsarr(dim_labels),
        "__DIM_SETS__": jsdata(dim_sets),
        "__ALPHA_USED__": f"{alpha_used:.4f}",
        "__ALPHA_REMAIN__": f"{alpha_remain:.4f}",
        "__ALPHA_MAX__": f"{max(alpha_max, 1.0):.4f}",
    }
    for k, v in repl.items():
        js = js.replace(k, v)
    # 占位符残留检查：先剥掉 // 行注释，否则注释里举例写的占位符会被误判
    code_only = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.splitlines())
    left = re.findall(r"__[A-Z0-9_]+__", code_only)
    if left:
        raise SystemExit(f"[!] 图表配置仍有未替换占位符：{sorted(set(left))}")
    check_js_syntax(js, "chart_js_bii")     # 语法自检 —— 拼出非法字面量时当场拦下
    m["_notes"] = notes
    m["_radar_n"] = len(radar_rows)
    return js


# ══════════════════════════════ 页面构建 ══════════════════════════════
def build_pages(m: dict, data: dict, date: str, by_code: dict, by_name: dict,
                pred: dict | None = None) -> list[str]:
    res, fr, inds = m["res"], m["fr"], m["inds"]
    notes = m.get("_notes", {})
    P: list[str] = []

    n_cand = len(by_code)
    n_l1 = len(m["l1_pass"])
    n_l1v = len(m.get("l1_vr_ok") or [])
    n_l2 = len(fr.l2_pass)
    n_25 = len(fr.l2_5_removed)
    n_l3v = len(fr.l3_vetoed)
    n_pass = len(fr.l3_pass)
    sens = fr.sensitivity
    led = res["ledger"]
    srows = sorted(res["rows"], key=lambda r: -r.score)

    cutoff = f"；仅显示分位最低的 {_MAX_BUB} 个" if notes.get("bub_cut") else ""
    def tail(n_cut: int, n_show: int) -> str:
        """图注截断声明：必须打印【实际展示数】，不是被截掉的数量。
        历史缺陷：曾把 cut 数量当展示数传入 → PB 图注写出「仅显示前 499 个」，
        而实际只画了 _MAX_PB=10 根柱，属误导性图注（0917 修正）。"""
        return f"；仅显示前 {n_show} 个" if n_cut else ""

    # ── 1. 封面 ──
    demo_flag = ('<span style="color:#FFB500">　⚠ 当前为演示数据 · 非当日行情</span>'
                 if data.get("_note") else "")
    P.append(f'''<section class="cover">
  <div class="brand"><span class="dot"></span><span class="nm">A-SHARE DRAGON-TIGER REVIEW</span>
    <span class="code">{CODE}　1/{TOTAL}</span></div>
  <h1>涨停板龙虎榜<br><em>深度研判报告</em></h1>
  <p class="sub">四层漏斗 L1→L2→L2.5→L3 全链路核验 · 财富密码选股策略融合层 ——
     图表版式参照 BlackRock 投资研究院（BII）「左文字栏 + 右图表」双栏范式重构</p>
  <div class="rule"></div>
  <div class="meta">
    <b>报告日期</b>　{date}（交易日）　
    <b>口径版本</b>　{C.CALIBER_VERSION}（永久生效）　
    <b>数据来源</b>　腾讯自选股（westock-mcp）{demo_flag}<br>
    <b>分析框架</b>　四层漏斗（L1 行业 → L2 个股 → L2.5 可交易 → L3 基本面）+ 评分管道
    （技术 / 资金 / 基本面 / 周期 / 位置五维）+ α 预算风控<br>
    <b>图表规范</b>　黑 + 品牌黄（#FFB500）+ 白配色；每图含图号、口径副标题、「图表结论」条与资料来源脚注；
    涨跌类指标保留 A 股「红涨绿跌」惯例；A4 横向双栏<br>
    <b>免责声明</b>　本报告为基于公开数据的技术与基本面分析，<b>不构成任何投资建议</b>
  </div>
</section>''')

    # ── 2. 摘要 ──
    top = srows[0] if srows else None
    all_watch = bool(srows) and all(r.action == "WATCH" for r in srows)
    n_buy = sum(1 for r in srows if r.action == "BUY")
    # 结语必须由 action 分布决定：曾硬编码「有候选、无买点」，
    # 在出现 BUY 的日子里会与第 12 页「本期触发 BUY 的标的数」直接打架。
    # v2.3 升级点 4（123 原则）：核心判断 ≤30 字，必须含 1 个关键词 + 1 个关键数。
    # 关键词取当期主线/定性（弱市取情绪阶段，强市取主线名称），关键数取过会数。
    if n_buy:
        verdict_txt = f"情绪见顶：过会 {n_pass} 只、仅 {n_buy} 只可建仓"
    else:
        verdict_txt = f"情绪见顶：过会 {n_pass} 只、暂无买点"
    budget_txt = ("α 预算已用满" if led["remaining"] < 1
                  else f"剩余 {led['remaining']/10000:.0f} 万")
    verdict = f'''<div class="verdict"><span class="k">核心判断</span>
今日候选池 <b>{n_cand}</b> 只，经四层漏斗后仅 <b>{n_pass}</b> 只过会；
L1 行业层 {len(inds)} 个板块中 <b>{n_l1}</b> 个达门槛；L2.5 剔除 <b>{n_25}</b> 只不可交易标的，
L3 基本面否决 <b>{n_l3v}</b> 只。{'全部过会标的均为 <b>WATCH</b> 观察信号，' if all_watch else ''}
α 预算阶段 <b>{led['stage']}</b> 下已用 <b>{led['used_pct']:.1%}</b>、{budget_txt} ——
结论是「<b>{verdict_txt}</b>」。</div>'''
    kpis = [
        ("候选标的（L0）", str(n_cand), "进入闸门的全部个股", ""),
        ("L1 行业达门槛", f"{n_l1}/{len(inds)}", f"3 年分位 ≤{C.RANK_LOW_THRESHOLD:.0f}%（额比归 L2）", ""),
        ("L2 技术面入池", str(n_l2), "分位与额比双达标", ""),
        ("L3 最终过会", str(n_pass), f"L2.5 剔 {n_25} · L3 否 {n_l3v}", "hl"),
        ("α 预算剩余", f"{led['remaining']/10000:.0f} 万", f"阶段 {led['stage']} 预算 {led['alpha_budget']:.0%}", ""),
        ("敏感度 ±N", f"±{abs(sens['rule_50pct_relative'] - sens['rule_any_deceleration'])} 只",
         "口径③收紧的过会数变化", "hl"),
    ]
    kpi_html = "".join(
        f'<div class="kpi {c}"><p class="l">{k}</p><p class="v">{v}</p><p class="s">{s}</p></div>'
        for k, v, s, c in kpis)
    # ── v2.3 市场情绪仪表盘（缺项自动降级） ──
    import sys as _sys, pathlib as _pl
    _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2]))
    from strategy import knowledge as KN
    ctx = data.get("context", {}) or {}
    _lu = int(ctx.get("limit_up_count", 60)) if ctx else None
    _br = float(ctx.get("broken_rate", 0.2)) if ctx else None
    sent = KN.sentiment_cycle(
        _lu, _br,
        lianban_height=ctx.get("lianban_height"),
        lianban_rate=ctx.get("lianban_rate"),
        prev_premium=ctx.get("prev_premium"),
        prev_stage=ctx.get("prev_sentiment_stage"),
    )
    refl = KN.reflexivity(
        ladder_height_today=ctx.get("lianban_height"),
        ladder_height_prev=ctx.get("lianban_height_prev"),
        vr_slope_up=ctx.get("vr_slope_up"),
        margin_net3d=ctx.get("margin_net3d"),
        prev_premium=ctx.get("prev_premium"),
    )
    _ban = "允许打板" if sent.allow_da_ban else "禁止打板（低吸/半路为主）"
    _sent_cls = "ok" if sent.stage in ("启动", "发酵", "高潮") else "no"
    _refl_cls = "ok" if refl.stage == "强化" else ("no" if refl.stage == "毁灭" else "")
    _sent_reasons = "；".join(sent.reasons) if sent.reasons else "—"
    _refl_reasons = "；".join(refl.reasons) if refl.reasons else "—"
    # 版式护栏（0928）：实测「依据」列若承载 3 段以上长文案（本期为
    # 「涨停 35 家 / 炸板率 18% / 连板率 20%；涨停 35 < 峰值参考 90 的 50%；
    # 昨日涨停溢价 +0.1%」，约 60 字）会撑破 36% 列宽并与「操作指令」列叠印，
    # 而页高/溢出/墨量三重几何判据对此完全无感。此处按字符数硬截断到 ~38 字，
    # 保证固定列宽下必定单行可容；被截信息在左栏「数据与口径说明」中另行完整披露。
    def _clip(s: str, n: int = 38) -> str:
        s = (s or "").strip()
        return s if len(s) <= n else s[: n - 1] + "…"
    _sent_reasons = _clip(_sent_reasons)
    _refl_reasons = _clip(_refl_reasons)
    _sent_note = ("　" + sent.note) if sent.note else ""
    # 版式修正（0928）：原用百分比列宽 + 无 table-layout 约束，当「判定」列文案较长
    # （如「见顶 · 减少操作、不追高，可低吸偏离主线的低位股 · 仓位上限 20%」）时会把
    # 「依据」列挤到文字重叠。改为 table-layout:fixed + 固定列宽 + word-break，
    # 并把「判定」列拆成「阶段 · 仓位上限」短标签，模式文案移到「操作指令」列。
    sentiment_html = (
        '<div class="sentiment-dash" style="margin:10px 0 14px;">'
        '<h3 style="font-size:13px;color:#0A3D6E;margin:0 0 4px;">市场情绪仪表盘（v2.3 知识蒸馏）</h3>'
        '<table style="font-size:11.5px;table-layout:fixed;width:100%;">'
        '<tr><th style="width:15%">维度</th><th style="width:17%">判定</th>'
        '<th style="width:34%">依据</th><th style="width:34%">操作指令</th></tr>'
        f'<tr><td>情绪周期（5 阶段）</td>'
        f'<td class="{_sent_cls}" style="word-break:break-word;">{sent.stage} · 仓位上限 {sent.pos_cap:.0%}</td>'
        f'<td style="word-break:break-word;">{_sent_reasons}</td>'
        f'<td style="word-break:break-word;">{_ban}（{_clip(sent.mode, 10)}）</td></tr>'
        f'<tr><td>反身性（索罗斯）</td>'
        f'<td class="{_refl_cls}">{refl.stage}</td>'
        f'<td style="word-break:break-word;">{_refl_reasons}</td>'
        '<td style="word-break:break-word;">强化期持有待涨，毁灭期逢高兑现、只做首板</td></tr>'
        '</table></div>'
    )
    # 情形二的「当前状态」必须由 action 分布与 α 账本决定：
    # 曾硬编码「不主动建仓」，在出现 BUY 且预算用满的日子会与同一页的
    # 「有买点（N 只触发建仓阈值）」和 KPI「α 预算已用满」当场打架（0917 修正）。
    if n_buy:
        _scen2 = (f"按综合分排序跟踪；本期已触发 <b>{n_buy} 只 BUY</b>"
                f"（α 预算使用率 {led['used_pct']:.1%}），新增建仓须先释放既有额度。")
    else:
        _scen2 = "维持 WATCH 观察，按综合分排序跟踪，不主动建仓；α 预算保持空置。"
    three = "".join([
        impl(["<b>升级条件</b>：过会标的出现放量突破 + 额比回到 1.2× 以上，且行业层维持低位。"], "情形一 · 升级信号"),
        impl([f"<b>当前状态</b>：{_scen2}"], "情形二 · 基准情形"),
        impl(["<b>失效条件</b>：过会标的跌破止损位，或行业分位抬升至 40% 以上。"], "情形三 · 失效信号"),
    ])
    P.append(page(f'''{eyebrow("00　摘要 · EXECUTIVE SUMMARY")}
<h2>一句话：{verdict_txt}</h2>
{verdict}
<div class="kpis">{kpi_html}</div>
{sentiment_html}
<div class="three">{three}</div>''', 2, "00　摘要", full=True))

    # ── 3. 图1 漏斗 ──
    L = f'''{eyebrow("01　漏斗 · FOUR-LAYER FUNNEL")}
<h2>{n_cand} 只候选，最后只有 {n_pass} 只过会</h2>
<p class="lead">四层漏斗按「行业 → 个股 → 可交易性 → 基本面」顺序逐层收口，每一层都有明确的
数值门槛，不靠主观判断。</p>
<p><b>L1 行业层</b>：{len(inds)} 个板块中 {n_l1} 个满足「3 年分位 ≤ {C.RANK_LOW_THRESHOLD:.0f}%」——
位置不贵，构成<b>超跌池</b>。额比 ≥ {C.VR_THRESHOLD:.1f}×（资金是否真的进来）是 <b>L2 个股层</b>的必要条件，
不在 L1 重复设卡：行业位置低但资金没进，只说明「便宜」，够不上「机会」。</p>
<p><b>L2 个股层</b>：{n_l2} 只通过；<b>L2.5 可交易性</b>独立成层，剔除退市整理、*ST、净资产为负等
{n_25} 只；<b>L3 基本面</b>再否决 {n_l3v} 只。</p>
{pq(f"漏斗的价值不在「选出好票」，而在「把不能买的先剔掉」—— 这次剔掉了 {n_25 + n_l3v} 只。",
    "先做减法，再做加法")}
{impl([f"<b>过会 {n_pass} 只</b>：其中 <b>{n_buy} 只</b>触发建仓阈值、{n_pass - n_buy} 只为观察信号。",
       "<b>被剔标的同样有信息量</b>：其共性短板往往就是当期市场的短板。",
       "<b>下一层验证</b>：过会标的需在次日出现量能确认，否则维持 WATCH。"])}
'''
    pass_names = "、".join(s.name for s in fr.l3_pass) or "无"
    R = card(1, f"四层漏斗：从 {n_cand} 只候选到 {n_pass} 只过会",
             f"个股维度逐层通过数（只）；L1 行业层为 {len(inds)}→{n_l1} 入池，未计入本图",
             cv("c1", 678, 340),
             f"逐层收口后仅 <b>{n_pass} 只</b>过会（{pass_names}）。"
             f"L2.5 剔 {n_25} 只、L3 否 {n_l3v} 只 —— "
             "<b>被剔除的数量比通过的数量更有信息量</b>，它刻画的是当期市场的可交易性约束。",
             "<b>资料来源：</b>腾讯自选股（westock-mcp）· 四层漏斗执行结果"
             f"（口径 {C.CALIBER_VERSION}）。<b>注：</b>L1 为行业粒度（个），与个股粒度不可直接相连，"
             "故单独在左栏正文说明。")
    P.append(page(two(L, R), 3, "01　漏斗"))

    # ── 4. 图2 行业气泡 ──
    in_gate = "、".join(i.name for i in m["l1_pass"]) or "无"
    L = f'''{eyebrow("01　漏斗 · L1 INDUSTRY GATE")}
<h2>行业先筛位置，个股再筛资金</h2>
<p class="lead">L1 是唯一一道「站在行业视角」的闸门，但<b>它只回答一个问题：这个行业贵不贵</b>。
「资金进没进」留给 L2 逐只个股去验 —— 两把尺子分工，不在一层里重复设卡。</p>
<p><b>横轴 = 3 年分位</b>，越靠左代表板块在自身过去三年的位置越低；
<b>纵轴 = 额比</b>，是近期成交额与历史常态的比值，衡量资金是否真的进场。
分位 {C.RANK_LOW_THRESHOLD:.0f}% 左侧为 <b>L1 超跌池</b>；额比 {C.VR_THRESHOLD:.1f}× 线是
<b>L2 个股层</b>的资金确认线，画在同一张图上便于对照。</p>
<p>本期超跌池：<b>{in_gate}</b>；其中额比已达 {C.VR_THRESHOLD:.1f}× 的仅 <b>{n_l1v} 个</b>。
位置低但没有放量，只能算「便宜」，够不上「机会」。</p>
{pq("位置低是必要条件，不是充分条件 —— 便宜可以便宜很久，资金进场才是催化剂。",
    "为什么 L1 只看位置")}
{impl(["<b>不要只看跌幅榜</b>：跌得多不等于机会，要配成交额变化一起看。",
       "<b>气泡大小 = 板块内部离散度</b>：气泡越大说明内部分化越剧烈，个股选择越重要。",
       "<b>门槛是过滤器不是预测器</b>：通过门槛只代表「值得继续看」，不代表会涨。"])}
'''
    R = card(2, "行业 3 年分位 × 成交额比：超跌池与资金确认线",
             f"气泡 = 板块内部离散度（越大越分化；散度为 0 表示本次取数无该行业成份股分位样本，"
             f"非「无分化」）；虚线 = 分位 {C.RANK_LOW_THRESHOLD:.0f}% 超跌线（L1 入池）"
             f"与额比 {C.VR_THRESHOLD:.1f}× 资金确认线（L2 判定）{cutoff}",
             cv("c2", 678, 366),
             f"L1 超跌池 <b>{n_l1} 个板块</b>（{in_gate}），其中额比已达 "
             f"{C.VR_THRESHOLD:.1f}× 者仅 <b>{n_l1v} 个</b> —— "
             "<b>「位置低」与「资金进」是两把独立的尺子</b>：前者在 L1 整池筛，后者在 L2 逐只验，"
             "单看任一项都会误判。",
             "<b>资料来源：</b>腾讯自选股（westock-mcp）· 板块年内分位与成交额比。"
             "<b>注：</b>额比按区间成交额与历史常态比值计算，非简单量比；分位为当月保留口径。")
    P.append(page(two(L, R), 4, "01　漏斗"))

    # ── 5. 图3 雷达 ──
    top_names = "、".join(r.name for r in srows[:3]) or "无"
    L = f'''{eyebrow("02　评分 · FIVE-DIMENSION RADAR")}
<h2>同一批候选，强在不同的地方</h2>
<p class="lead">五维评分把「为什么选它」拆成可比较的五个方向。雷达图的作用不是比大小，
而是看<b>形状</b> —— 形状差异直接指向不同的持有方式。</p>
<p>技术面强、基本面弱的是<b>交易型</b>；基本面强、技术面平的是<b>配置型</b>；
只有形状均衡的才适合作为底仓。本期高分候选为 <b>{top_names}</b>。</p>
{pq("看形状，不看面积 —— 面积大但形状歪的标的，往往对应「赚了指数不赚钱」的体验。",
    "雷达图的正确读法")}
{impl(["<b>先定风格再定标的</b>：形状决定该用交易还是配置的方式持有。",
       "<b>短板即风险</b>：雷达上凹进去的那一维，通常就是回撤时最先出问题的维度。",
       "<b>满分 100 但别追满</b>：五维全高的标的一年也未必出现一次。"])}
'''
    R = card(3, "Top 候选五维评分雷达",
             "技术面 / 资金面 / 基本面 / 周期位置 / 斐波那契位置，满分 100",
             cv("c3", 660, 392),
             f"前三名（{top_names}）形状各异：<b>强项维度不同，意味着持有方式不能照搬</b>。"
             "雷达面积接近的标的，未必可以互相替代。",
             "<b>资料来源：</b>腾讯自选股（westock-mcp）评分体系 + 策略包 `pipeline.score_row` 加权。"
             "<b>注：</b>缺少的维度按「不给分」处理，不做均值替代 —— 均值替代会系统性高估数据缺失标的。")
    P.append(page(two(L, R), 5, "02　评分"))

    # ── 6. 图4 综合分 ──
    if srows:
        s0, sN = srows[0], srows[-1]
        gap_line = f"最高分 <b>{s0.score:.1f}</b>（{s0.name}）与末位相差 <b>{s0.score - sN.score:.1f} 分</b>。"
        head_line = (f"本期最高分 <b>{s0.score:.1f}</b>（{s0.name}），动作为 <b>{s0.action}</b>。"
                     + ("全部候选均为 WATCH —— 分数够看，但未触发建仓阈值。" if all_watch else ""))
    else:
        s0 = None
        gap_line = "本期无候选。"
        head_line = "本期无候选。"
    L = f'''{eyebrow("02　评分 · COMPOSITE RANKING")}
<h2>综合分排序与风控动作</h2>
<p class="lead">综合分 = 五维加权 + 加分项（国资背景、新兴科技）− 减分项（单年亏损、增速失速）。
分数决定排序，但<b>动作由风控规则决定</b>，两者是分开的。</p>
<p>{head_line}</p>
{pq("分数告诉你「看谁」，风控告诉你「能不能买」—— 不要用一个答案回答两个问题。",
    "排序与动作分离")}
{impl(["<b>WATCH 不是观望</b>：它是有明确升级条件的等待。",
       "<b>排序会骗人</b>：分差 1~2 分不构成优劣，分差 10 分以上才有区分度。",
       "<b>动作栏才是可执行信息</b>，分数只是研究顺序。"])}
'''
    R = card(4, "候选综合分排序与风控动作",
             f"综合分 = 五维加权 + 加分项 − 减分项，满分 100；末端标注风控动作"
             f"{tail(notes.get('rank_cut', 0), _MAX_RANK)}",
             cv("c4", 678, 320),
             f"{gap_line}但排序只解决「先看谁」，<b>能不能买由风控动作栏决定</b> —— "
             f"本期触发 BUY 的标的数为 <b>{sum(1 for r in srows if r.action == 'BUY')}</b>。",
             "<b>资料来源：</b>腾讯自选股（westock-mcp）· 评分管道输出。"
             "<b>注：</b>综合分与分项分均来自同一评分体系，样本内可比；跨报告不可直接比较。")
    P.append(page(two(L, R), 6, "02　评分"))

    # ── 7. 图5 财务增速 ──
    # 增速红线只对 **L2 入池标的** 执行（L3 层口径），故名单必须限定在 L2 池内 ——
    # 曾对全候选池（数百只）统计，左栏直接列出上百个名字把版面顶破；
    # 且把「未进入 L2 的标的」也算作「触发硬线」本身就不成立。
    _l2codes = {s.code for s in fr.l2_pass}
    hard = [c["name"] for c in by_code.values()
            if c["code"] in _l2codes
            and c.get("interim_yoy") is not None and float(c["interim_yoy"]) <= 0]
    hard_txt = "、".join(hard[:6]) + (f" 等 {len(hard)} 只" if len(hard) > 6 else "") or "无"
    sens_n = abs(sens["rule_50pct_relative"] - sens["rule_any_deceleration"])
    L = f'''{eyebrow("03　财务 · GROWTH RED LINE")}
<h2>增速红线的三道判读</h2>
<p class="lead">口径③以<b>半年口径</b>（最新中报年内同比）判定成长性。它有三档：
硬线排除、减分线扣分、其余通过。</p>
<p><b>硬线</b>：中报同比 ≤ 0 → 直接排除；
<b>减分线</b>：同比 &gt; 0 但不足上一年度增速的 50% → 重大减分 −15 分。
本期触发硬线（限 L2 入池标的）：<b>{hard_txt}</b>。</p>
<p>50% 这条<b>相对线</b>是框架自定默认值，不是市场共识。把它收紧为「任何减速即排除」，
过会数量会从 <b>{sens['rule_50pct_relative']}</b> 只降到 <b>{sens['rule_any_deceleration']}</b> 只，
差 <b>±{sens_n} 只</b> —— 这个敏感度必须随报告披露。</p>
{pq("增速不是越高越好，而是「别掉档」—— 从高增速掉到低增速，比一直低增速更危险。",
    "为什么用相对线而非绝对线")}
{impl([f"<b>本报告 ±N = {sens_n} 只</b>：口径收紧会改变过会名单，务必知悉。",
       "<b>不要用年度口径替代半年口径</b>：两套口径下整批结论会翻转。",
       "<b>扣非与归母要分开看</b>：归母为正但扣非为负，说明盈利质量存疑。"])}
'''
    R = card(5, "中报同比 vs 上年度增速：增速红线的三道判读",
             f"半年口径归母同比（黄）与上一年度增速（灰）对照；单位 %；顶部虚线为 50% 相对线"
             f"{tail(notes.get('fin_cut', 0), _MAX_FIN)}",
             cv("c5", 678, 330),
             f"硬线（同比 ≤0）在 L2 池内排除 <b>{len(hard)} 只</b>（{hard_txt}）；"
             "减分线针对「增速掉档」的标的扣分而非排除。"
             f"<b>口径 50% 相对线的 ±N 敏感度为 {sens_n} 只</b>，"
             "是本报告最需要读者知悉的不确定性来源。",
             "<b>资料来源：</b>腾讯自选股（westock-mcp）`data_finance`"
             "（归母同比 `NPParentCompanyYOY`）。<b>注：</b>半年口径 = 最新中报年内同比；"
             f"增速红线见 `strategy/calibers.py`（口径 {C.CALIBER_VERSION}）。")
    P.append(page(two(L, R), 7, "03　财务"))

    # ── 8. 图6 PB ──
    neg_pb = [c["name"] for c in by_code.values()
              if c.get("pb") is not None and float(c["pb"]) < 0]
    # 名称类剔除（退市 / ST / *ST）—— 单列，供左栏与图结论条说明「它们为何不在榜上」。
    # 不单列会让读者以为榜单漏了标的，单列才能自证与 L2.5 清单一致（0917 二次修正）。
    name_excl = [c["name"] for c in by_code.values()
                 if c.get("pb") is not None and float(c["pb"]) > 0
                 and not pb_tradable(c)]
    low_pb = sorted([(c["name"], float(c["pb"])) for c in by_code.values()
                     if pb_tradable(c)], key=lambda x: x[1])[:3]
    low_txt = "、".join(f"{n}（{v:.2f}×）" for n, v in low_pb) or "无"
    # 名称类剔除项可达数十只（ST 股 PB 多为正），全量罗约会撑破版心 →
    # 图卡结论条只报数量，左栏最多列 4 只作示例（0917 二次修正）。
    _nx_show = "、".join(name_excl[:4]) + ("等" if len(name_excl) > 4 else "")
    name_excl_txt = _nx_show or "无"
    L = f'''{eyebrow("03　财务 · VALUATION")}
<h2>PB 是安全边际，不是上涨理由</h2>
<p class="lead">对重资产与周期型标的，市净率比市盈率更稳定；对轻资产成长股则参考价值有限。
本图只做排序参考，不构成买卖依据。</p>
<p>估值最低的三只：<b>{low_txt}</b>。</p>
<p><b>PB 为负</b>意味着净资产为负，属于可交易性层面的问题，会在 L2.5 被单独剔除，
而不是作为「估值便宜」处理。本期：<b>{"、".join(neg_pb) or "无"}</b>。</p>
<p>同理，<b>已退市与 ST / *ST 标的也不进本榜</b>—— 它们同样命中 L2.5，相对估值指标
识别不了「公司已不存在或已出问题」。本期因此另有 <b>{len(name_excl)} 只</b>被排除
（{name_excl_txt}）。</p>
{pq("低估值只能解释「跌不动」，不能解释「会涨」—— 上涨需要资金和景气度，估值不提供。",
    "低估值的正确位置")}
{impl(["<b>PB 为负不是「极便宜」</b>：净资产为负的标的优先走可交易性剔除流程。",
       "<b>跨行业不可比</b>：不同行业的 PB 中枢差异极大，只在同行业内比较。",
       "<b>与增长配对使用</b>：低 PB + 正增长才是有效组合。"])}
'''
    R = card(6, "候选市净率（PB）排序：安全边际视角",
             "PB 由低到高排列，仅取 PB > 0 且未命中 L2.5 名称类剔除（退市 / ST / *ST）者"
             "（两类命中项均属可交易性问题，已排除，见图结论条与左栏）；"
             "黄 = PB ≤2×（低估值区），灰 = 其余"
             + tail(notes.get("pb_cut", 0), _MAX_PB),
             cv("c6", 678, 336),
             f"低估值区（PB ≤2×）标的为 "
             f"{'、'.join(n for n, v in low_pb if v <= 2) or '无'}；"
             f"PB 为负 <b>{len(neg_pb)} 只</b>（{'、'.join(neg_pb) or '无'}）—— "
             "后者应走可交易性剔除通道，<b>而非被解读为「特别便宜」</b>；"
             f"另有 <b>{len(name_excl)} 只</b>已退市 / ST 标的同样不进榜，"
             "<b>不并入低估值区</b>。",
             "<b>资料来源：</b>腾讯自选股（westock-mcp）`data_finance` 市净率 + `data_quote` PB / 名称核对。"
             "<b>注：</b>PB 仅作同行业内相对排序参考，不构成估值结论；净资产为负、已退市、ST / *ST "
             "标的均在 L2.5 层单独处理。")
    P.append(page(two(L, R), 8, "03　财务"))

    # ── 9. 图7 五维分项 ──
    L = f'''{eyebrow("04　结构 · SCORE DECOMPOSITION")}
<h2>把综合分拆回五个维度</h2>
<p class="lead">综合分是加权结果，看不出短板在哪。拆回五维之后，每只标的的「问题维度」
会直接暴露出来 —— 这比总分更有决策价值。</p>
<p>读法：<b>看哪根柱子最短</b>。最短的那一维就是该标的在回撤中最先失效的环节，
也是仓位上限的真正约束。</p>
{pq("总分决定排序，短板决定仓位 —— 一个决定先看谁，一个决定敢放多少。",
    "为什么要拆项")}
{impl(["<b>基本面维度最低</b>的标的，不适合作为中期持有。",
       "<b>资金面维度最低</b>的标的，即便技术形态好也只适合短打。",
       "<b>五维均衡</b>比「某一维极高」更难得，也更适合承担主要仓位。"])}
'''
    R = card(7, "五维评分分项拆解",
             "各候选在技术面 / 资金面 / 基本面 / 周期位置 / 斐波那契五个维度的原始得分（满分 100）"
             + tail(notes.get("dim_cut", 0), _MAX_DIM),
             cv("c7", 678, 372),
             "拆项后可以看到：<b>多数候选的短板集中在基本面或资金面</b>，而技术面普遍不低 —— "
             "说明当前的约束不是「形态不好」，<b>而是「基本面或资金面不给力」</b>，"
             "这决定了仓位应该偏保守。",
             "<b>资料来源：</b>腾讯自选股（westock-mcp）评分体系分项。"
             "<b>注：</b>分项为原始得分，未含加分项与减分项；加权后的综合分见图 4。")
    P.append(page(two(L, R), 9, "04　结构"))

    # ── 10. 图8 α 账本 ──
    budget_yuan = led["equity"] * led["alpha_budget"]
    empty_note = "预算完全空置，说明本期没有触发建仓条件。" if led["positions"] == 0 else ""
    L = f'''{eyebrow("05　风控 · α BUDGET LEDGER")}
<h2>α 预算：先定风险的额度，再谈机会</h2>
<p class="lead">α 账本把「能亏多少」前置成预算。阶段 <b>{led['stage']}</b> 对应预算比例
<b>{led['alpha_budget']:.0%}</b>，以权益 <b>{led['equity']/10000:.0f} 万</b> 计，
可用额度 <b>{budget_yuan/10000:.0f} 万</b>。</p>
<p>当前持仓 <b>{led['positions']}</b> 笔、已用 <b>{led['used_pct']:.1%}</b>、
剩余 <b>{led['remaining']/10000:.0f} 万</b>。{empty_note}</p>
{pq("预算没用完不是「浪费」，是「没有符合条件的机会」—— 空仓也是一种仓位。",
    "α 预算的纪律意义")}
{impl(["<b>用不完 ≠ 应该用完</b>：预算是上限，不是目标。",
       "<b>冰点期预算减半</b>：`ICE_POINT_ALPHA_MULTIPLIER` 按 0.5 折减，防止在极端行情里放大风险。",
       "<b>三道限额先于选股</b>：单笔、单票、总仓限额在选股之前就已锁定。"])}
'''
    R = card(8, "α 预算使用情况",
             f"阶段 {led['stage']} 预算 = 权益 × {led['alpha_budget']:.0%}；单位万元",
             cv("c8", 678, 190),
             f"已用 <b>{led['open_notional']/10000:.1f} 万</b>、"
             f"剩余 <b>{led['remaining']/10000:.0f} 万</b>。"
             f"当前持仓 {led['positions']} 笔 —— <b>预算空置是可接受的结果</b>，"
             "它的含义是「本期没有符合风险收益要求的机会」，而不是「应该加快出手」。",
             "<b>资料来源：</b>策略包 `risk.AlphaLedger` 快照。"
             "<b>注：</b>α_max 为阶段预算上限；冰点期按 0.5 折减；金额单位万元。")
    P.append(page(two(L, R), 10, "05　风控"))

    # ── 11. 六条口径（full） ──
    rows_cal = [
        ("① 国企央企背景", "偏好项（+6 分），不是门槛", "soe_background"),
        ("② 产业偏好", "新兴科技成长优先（+8 分）", "emerging_tech"),
        ("③ 净利润增长率", "<b>半年口径</b>（最新中报年内同比）", "interim_yoy"),
        ("④ 单年亏损", "减分项（−10 分）；连续两年年报亏损 = 否决", "annual_loss_years"),
        ("⑤「链」形态主题", "跳过 L1 否决权（行业层仅定性）", "CHAIN_THEMES"),
        ("⑥ 基础可交易性", "<b>L2.5 独立层</b>（位于 L2 与 L3 之间）", "gate_tradability"),
    ]
    cal_html = "".join(
        f"<tr><td>{a}</td>"
        f"<td style=\"text-align:left;white-space:normal\">{b}</td>"
        f"<td style=\"text-align:left\">{c2}</td></tr>" for a, b, c2 in rows_cal)
    demo_disc = ("<b>⚠ 本期为演示数据（`strategy/sample_data.json`），非当日真实行情，"
                 "仅用于跑通流程。</b>" if data.get("_note") else "")
    P.append(page(f'''{eyebrow("06　口径 · CALIBERS (PERMANENT)")}
<h2>六条口径：{C.CALIBER_VERSION}，永久生效</h2>
<p class="lead">口径一旦定稿即永久生效。任何变更都必须<b>全量重算历史结论</b>并披露 ±N 只敏感度 ——
口径漂移会让不同日期的报告失去可比性，这比单次判断错误更危险。</p>
<table>
<colgroup><col style="width:22%"><col style="width:52%"><col style="width:26%"></colgroup>
<thead><tr><th>口径</th><th>v2 取值</th><th>实现模块</th></tr></thead>
<tbody>{cal_html}</tbody></table>
<p class="tcap"><b>增速红线（口径③的量化）</b>　硬线：中报同比 ≤ 0 → 排除；减分线：同比 &gt; 0 但不足上一年度增速
50% → 重大减分 −15 分。<b>50% 相对线为框架自定默认值</b>，收紧为「任何减速即排除」会改变过会数量，
本报告披露的敏感度为 <b>±{sens_n} 只</b>。</p>
<div class="disc">
<b>数据与口径说明</b>　行情、资金流向、评分、分位、额比均来自腾讯自选股（westock-mcp）；
口径版本 <b>{C.CALIBER_VERSION}</b>；策略包 `strategy/` 负责闸门与评分，`pipeline` 负责信号输出。
{demo_disc}<br>
<b>图表规范</b>　本报告版式参照 BlackRock 投资研究院（BII）公开材料重构：A4 横向「左文字栏 + 右图表」双栏；
每图含图号、口径副标题、图体、黑底「图表结论」条与资料来源脚注；配色为黑 + 品牌黄（#FFB500）+ 白；
涨跌类指标保留 A 股「红涨绿跌」惯例。<br>
<b>免责声明</b>　本文档为基于公开数据的技术与基本面分析，<b>不构成任何投资建议</b>。
所有目标位、止损位均为技术测算参考，不代表未来价格走势。市场有风险，投资需谨慎。
</div>''', 11, "06　口径", full=True))

    # ── 12. 风险 + 三情形（full） ──
    P.append(page(f'''{eyebrow("07　风险清单与情形推演")}
<h2>六个风险，按优先级排序</h2>
<div class="risk">
<ol>
<li><b>口径敏感度是本报告最大的不确定性</b>：口径③的 50% 相对线收紧会使过会数量由
{sens['rule_50pct_relative']} 只降至 {sens['rule_any_deceleration']} 只（±{sens_n} 只），
须按最保守口径复核名单。</li>
<li><b>过会 ≠ 可买</b>：本期触发 BUY 的标的数为 <b>{sum(1 for r in srows if r.action == 'BUY')}</b>；
把 WATCH 当 BUY 是本流程最常见的误用。</li>
<li><b>数据时效</b>：{"当前为演示数据，非当日行情，任何结论不可直接用于交易。" if data.get("_note") else "行情与资金数据为收盘后快照，盘中数据会变动。"}</li>
<li><b>L2.5 与 L3 不可混同</b>：「不可交易」与「基本面不通过」是两类问题，
混淆会把可修复的问题误判为标的质量问题。</li>
<li><b>分位与额比的历史依赖</b>：两者都基于历史区间计算，区间选择变化会影响门槛通过情况。</li>
<li><b>样本内可比性</b>：综合分与分项分只在同一评分体系、同一口径版本内可比，跨报告不可直接比较。</li>
</ol>
</div>
<div class="three" style="margin-top:14px;">
{impl(["<b>升级条件</b>：过会标的出现放量突破，额比回到 1.2× 以上，且行业层维持低位。三条同时成立才升级为建仓评估。"], "情形一 · 升级信号")}
{impl([f"<b>基准应对</b>：{_scen2}"], "情形二 · 基准情形")}
{impl(["<b>失效条件</b>：过会标的跌破止损位，或行业分位抬升至 40% 以上，或 L3 基本面出现新的否决项。"], "情形三 · 失效信号")}
</div>''', 12, "07　风险清单", full=True))

    # ── 13. 跟踪清单 + 数据说明（full） ──
    # 过会标的可达数十只；全量入表会把版心顶破（2026-09-16 实测 26 行时页高超阈值 454px）。
    # 按综合分降序只列前 _MAX_WATCH 只，并在表下注明总数与截断规则 —— 不静默截断。
    _MAX_WATCH = 11
    watch_shown = srows[:_MAX_WATCH]
    watch_rows = []
    for r in watch_shown:
        c = by_code.get(r.code) or {}
        price = c.get("price")
        entry = c.get("entry")
        stop = c.get("stop")
        watch_rows.append(
            f"<tr><td>{r.name}<span class='tag g'>{r.code}</span></td>"
            f"<td>{price if price is not None else '—'}</td>"
            f"<td>{entry if entry is not None else '—'}</td>"
            f"<td>{stop if stop is not None else '—'}</td>"
            f"<td>{r.score:.1f}</td><td>{r.action}</td></tr>")
    if not watch_rows:
        watch_rows.append("<tr><td colspan='6'>本期无过会标的</td></tr>")
    watch_note = (f"　本表按综合分降序列出前 <b>{len(watch_shown)} 只</b>；"
                  f"本期过会共 <b>{len(srows)} 只</b>，其余 "
                  f"{len(srows) - len(watch_shown)} 只见当日 <code>data.json</code> 候选池"
                  f"与 <code>framework/</code> 落盘明细。"
                  if len(srows) > _MAX_WATCH else "")
    # v2.3 升级点 4（《故事的力量》123 原则）：第 13 页标题必须用结论式，
    # 即「明日盯住这 N 只：XXX / YYY / ZZZ」，而不是中性的「跟踪清单」。
    _buys = [r for r in srows if (getattr(r, "action", "") or "").upper() == "BUY"] or list(srows)
    _top3 = " / ".join((getattr(r, "name", "") or "").strip() for r in _buys[:3]) or "无过会标的"
    _watch_title = f"明日盯住这 {min(len(_buys), 3)} 只：{_top3}"
    P.append(page(f'''{eyebrow("08　跟踪清单与数据说明")}
<h2>{_watch_title}</h2>
<table>
<colgroup><col style="width:26%"><col style="width:12%"><col style="width:14%"><col style="width:14%"><col style="width:16%"><col style="width:18%"></colgroup>
<thead><tr><th>标的</th><th>最新价</th><th>参考入场</th><th>止损位</th><th>综合分</th><th>风控动作</th></tr></thead>
<tbody>{"".join(watch_rows)}</tbody></table>
<p class="tcap"><b>读法</b>　「参考入场 / 止损位」来自候选数据，为技术测算参考；
「风控动作」由评分管道给出，是唯一的可执行字段。<b>动作栏为 WATCH 时不得建仓</b>，
须等待升级条件成立。标的按综合分降序排列，不代表推荐强度排序。{watch_note}</p>

<div class="disc">
<b>数据与口径说明</b>　{date} 交易日盘后复盘；行情 / 资金流向 / 评分 / 分位 / 额比均来自腾讯自选股（westock-mcp）；
策略口径版本 <b>{C.CALIBER_VERSION}</b>（永久生效）；四层漏斗与评分管道由 `strategy/` 包实现。{demo_disc}<br>
<b>图型说明</b>　共 8 张图：① 漏斗递减条形　② 分位×额比气泡矩阵　③ 五维雷达　④ 综合分排行
　⑤ 中报同比对照柱　⑥ PB 排序　⑦ 五维分项拆解　⑧ α 预算账本；版式参照 BII 双栏范式，A4 横向。<br>
<b>免责声明</b>　本文档基于公开数据的技术与基本面分析，<b>不构成任何投资建议</b>。
市场有风险，投资需谨慎，请根据自身风险承受能力独立决策。
</div>''', 13, "08　跟踪清单", full=True))

    # ── 14. 次日 5 条可证伪预判（双栏） ──
    P.append(build_pred_page(pred or {}, date))

    return P


# ══════════════════════════════ 主流程 ══════════════════════════════
def main() -> int:
    ap = argparse.ArgumentParser(description="BII 双栏范式 · 龙虎榜日更报告（A4 横向）")
    ap.add_argument("--data", default=str(REPO / "strategy" / "sample_data.json"))
    ap.add_argument("--date", default=dt.date.today().strftime("%Y-%m-%d"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--equity", type=float, default=None, help="覆盖权益（元）")
    ap.add_argument("--stage", default=None, help="覆盖阶段（I/II/III）")
    ap.add_argument("--predict-file", default=None,
                    help="次日 5 条可证伪预判 JSON（默认自动探测 <data 同级>/predictions.json）")
    ap.add_argument("--predictions", default=None,
                    help="内联预判 JSON 字符串（优先于 --predict-file）")
    args = ap.parse_args()

    global CODE
    dc = args.date.replace("-", "")
    CODE = f"LHB{dc[4:]}-{dc[:4]}"

    data_path = pathlib.Path(args.data)
    if not data_path.exists():
        sys.exit(f"[!] 数据文件不存在：{data_path}")
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if args.equity is not None:
        data.setdefault("context", {})["equity"] = args.equity
    if args.stage is not None:
        data.setdefault("context", {})["stage"] = args.stage

    out_dir = pathlib.Path(args.out) if args.out else REPO / "out" / f"dragon-tiger-{dc}"
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    m = compute_model(data)
    by_code, by_name = {}, {}
    for c in data.get("candidates", []):
        by_code[c["code"]] = c
        by_name[c["name"]] = c

    pred = load_predictions(args, data_path, out_dir)
    if pred and pred.get("report_date") and str(pred["report_date"])[:10] != str(args.date)[:10]:
        print(f"[!] 预判 report_date={pred['report_date']} 与报告日期 {args.date} 不一致 —— "
              f"预判可能挂错交易日，请核对 predictions.json（已照常渲染）。")
    tgt = (pred or {}).get("target_date") or next_trading_day(args.date)

    chart_js = inject_charts(m, by_code, by_name)
    pages = build_pages(m, data, args.date, by_code, by_name, pred)
    if len(pages) != TOTAL:
        sys.exit(f"[!] 页数不符：TOTAL={TOTAL} 实际={len(pages)}")

    html = (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"UTF-8\">\n"
        f"<title>涨停板龙虎榜深度研判报告（BII 双栏）· {args.date}</title>\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n"
        + "".join(pages) +
        "\n<script>__CHART_LIB__</script>\n"
        f"<script>{chart_js}</script>\n</body>\n</html>"
    )
    html = html.replace("__CHART_LIB__", CHART_LIB)

    out_file = out_dir / f"涨停板龙虎榜深度研判报告-BII双栏-{dc}.html"
    out_file.write_text(html, encoding="utf-8")

    print("=" * 66)
    print(f" BII 双栏范式 · A股涨停板龙虎榜深度研判报告 · {args.date}")
    print("=" * 66)
    print(f" 口径 {C.CALIBER_VERSION} | 候选 {len(by_code)} | L1 达门槛 {len(m['l1_pass'])}/{len(m['inds'])}"
          f" | L2 {len(m['fr'].l2_pass)} | L2.5 剔 {len(m['fr'].l2_5_removed)}"
          f" | L3 否 {len(m['fr'].l3_vetoed)} | 过会 {len(m['fr'].l3_pass)}")
    print(f" 页数 {len(pages)}（封面 + {TOTAL - 1} 编号页）| 图 8 张 | Chart.js 已内联")
    _p = pred or {}
    _n = len(_p.get("items") or [])
    print(f" 次日预判 {_n}/5 条 · 目标日 {tgt}"
          f"{'　（示例占位，未提供 predictions.json）' if not _n else ''}"
          f"{'　来源 ' + str(_p.get('_src')) if _p.get('_src') else ''}")
    print(f" HTML: {out_file}  ({out_file.stat().st_size / 1024:.1f} KB)")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
