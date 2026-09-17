#!/usr/bin/env python3
"""Build the FindingGrowthStocks static site from markdown reports.

Site hierarchy:
  index.html            — hub linking to the three second-level sections
  reports/index.html    — all stock analysis reports, grouped by stock
  restructuring/index.html — restructuring watch lists + per-stock info reports
  select/index.html     — stock screen results
"""
import html
import json
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"
SELECT_DIR = ROOT / "select"
RESTRUCTURING_DIR = ROOT / "restructuring"
SITE_DIR = ROOT / "_site"

PAGE_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.6; color: #24292f; max-width: 960px; margin: 0 auto; padding: 2rem 1rem; background: #fff; }
h1 { font-size: 1.6rem; border-bottom: 1px solid #d0d7de; padding-bottom: 0.5rem; margin: 1.5rem 0 1rem; }
h2 { font-size: 1.3rem; margin: 1.5rem 0 0.8rem; padding-bottom: 0.3rem; border-bottom: 1px solid #d0d7de; }
h3 { font-size: 1.1rem; margin: 1.2rem 0 0.6rem; }
p { margin: 0.6rem 0; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; display: block; overflow-x: auto; }
th, td { border: 1px solid #d0d7de; padding: 0.5rem 0.75rem; text-align: left; white-space: nowrap; }
th { background: #f6f8fa; font-weight: 600; }
tr:nth-child(even) { background: #f6f8fa; }
blockquote { border-left: 3px solid #d0d7de; padding-left: 1rem; color: #656d76; margin: 1rem 0; }
code { background: #f6f8fa; padding: 0.15rem 0.3rem; border-radius: 3px; font-size: 0.9em; }
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 1.5rem 0; }
em { color: #656d76; }
ul, ol { padding-left: 1.5rem; margin: 0.6rem 0; }
li { margin: 0.25rem 0; }
.nav { margin-bottom: 1.5rem; font-size: 0.9rem; color: #656d76; }
.nav a { font-size: 0.9rem; }
.chart-box { position: relative; height: 340px; margin: 1.25rem 0; }
"""

INDEX_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.6; color: #24292f; max-width: 960px; margin: 0 auto; padding: 2rem 1rem; background: #fff; }
h1 { font-size: 1.8rem; border-bottom: 1px solid #d0d7de; padding-bottom: 0.5rem; margin-bottom: 1rem; }
h2 { font-size: 1.3rem; margin: 1.5rem 0 0.8rem; color: #1f2328; border-bottom: 1px solid #d0d7de; padding-bottom: 0.3rem; }
h3 { font-size: 1.05rem; margin: 1rem 0 0.5rem; color: #24292f; }
p { margin: 0.6rem 0; }
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }
ul, ol { padding-left: 1.5rem; }
.report-list { list-style: none; padding-left: 0; }
.report-list li { padding: 0.5rem 0; border-bottom: 1px solid #d0d7de; }
.report-list li:last-child { border-bottom: none; }
.date { color: #656d76; font-size: 0.9rem; margin-left: 0.5rem; }
.nav { margin: 0.5rem 0 1rem; font-size: 0.9rem; color: #656d76; }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #d0d7de; color: #656d76; font-size: 0.85rem; }
.methodology { border: 1px solid #d0d7de; border-left: 4px solid #0969da; background: #f6f8fa; border-radius: 6px; padding: 1rem 1.25rem; margin: 1.5rem 0; }
.methodology p { margin: 0 0 0.5rem; }
.methodology ol { margin: 0; padding-left: 1.4rem; }
.methodology li { margin: 0.35rem 0; }
.methodology .attr { margin: 0.6rem 0 0; color: #656d76; font-size: 0.9rem; text-align: right; }
.pin-note { border: 1px solid #d4a72c; border-left: 4px solid #b8860b; background: #fffdf3; border-radius: 6px; padding: 1rem 1.25rem; margin: 1.5rem 0; }
.pin-note p { margin: 0.4rem 0; }
.pin-note .pin-title { font-weight: 600; color: #7a5c00; margin-top: 0; }
.pin-note .pin-attr { margin: 0.6rem 0 0; color: #8a6d1a; font-size: 0.9rem; text-align: right; }
.sections { display: grid; gap: 0.9rem; margin: 1.5rem 0; }
.section-card { border: 1px solid #d0d7de; border-radius: 8px; padding: 1rem 1.25rem; }
.section-card:hover { border-color: #0969da; }
.section-card h2 { margin: 0 0 0.3rem; padding: 0; border: none; font-size: 1.25rem; }
.section-card p.desc { margin: 0.2rem 0 0.5rem; color: #57606a; font-size: 0.95rem; }
.section-card p.count { margin: 0; color: #656d76; font-size: 0.85rem; }
.rating { font-size: 0.78rem; padding: 0.08rem 0.45rem; border-radius: 10px; margin-left: 0.4rem; white-space: nowrap; }
.r-buy { background: #1a7f37; color: #fff; }
.r-overweight { background: #dafbe1; color: #1a7f37; }
.r-hold { background: #f6f8fa; color: #57606a; border: 1px solid #d0d7de; }
.r-underweight { background: #ffebe9; color: #cf222e; }
.r-sell { background: #cf222e; color: #fff; }
"""

PIN_NOTE = """
<div class="pin-note">
<p class="pin-title">◆ 中报读后：三大方向，翻倍以上空间</p>
<p>中报预告读至今日，现在看有三个方向是可以看到翻倍以上的空间的：</p>
<p><strong>1、AI 泛科技</strong>：本轮 AI 泛科技伴随指数开展中期调整后，产业链中依然存在供需矛盾，严重供不应求，持续涨价放量的可持续性标的（AI 大基建中依然卡脖子环节和产业链新秀）。</p>
<p><strong>2、创新药、CXO，以及部分已经走出医保政策影响，开始新品放量上市、价格持续恢复、出口持续旺盛的医疗器械、医药行业</strong>。</p>
<p><strong>3、大消费、新消费行业中的业绩开始拐头向上，具有带领性、带动效应的行业 α</strong>。</p>
<p>这三个行业是非常明确的：AI 在高位，但基本面景气不变（筹码博弈波动变大），依然会出现新的产业链机会；创新药和大消费逐渐走出下行周期，部分 α 一定会在未来 2-5 年走出 10 倍效应，拭目以待。</p>
</div>
"""

RATING_LABELS = {
    "Buy": "买入",
    "Overweight": "增持",
    "Hold": "持有",
    "Underweight": "减持",
    "Sell": "卖出",
}
_RATING_RE = re.compile(r"最终评级[：:]\s*(Buy|Overweight|Hold|Underweight|Sell)")

FOOTER = """
<footer>
<p>Generated by TradingAgents framework. For research purposes only, not investment advice.</p>
<p><a href="https://github.com/TauricResearch/TradingAgents">TradingAgents</a> | <a href="https://github.com/panhaoneo/FindingGrowthStocks">GitHub</a></p>
</footer>
"""


def render_page(title: str, body_html: str, nav_html: str, has_charts: bool = False) -> str:
    chart_head = f'\n<script src="{CHART_JS_CDN}"></script>' if has_charts else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>{PAGE_CSS}</style>{chart_head}
</head>
<body>
<div class="nav">{nav_html}</div>
{body_html}
</body>
</html>
"""


def render_index_page(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>{INDEX_CSS}</style>
</head>
<body>
{body_html}
{FOOTER}
</body>
</html>
"""


_MD_LINK = re.compile(r'href="(?!https?://|mailto:|#)([^"]+)\.md"')


def rewrite_md_links(body_html: str) -> str:
    """Point relative .md links at their built .html counterparts."""
    return _MD_LINK.sub(r'href="\1.html"', body_html)


CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"

_CHART_BLOCK_RE = re.compile(r"```chart[ \t]*\n(.*?)```", re.DOTALL)


def _chart_style(name: str) -> tuple[str, bool]:
    if "乐观" in name:
        return "#1a7f37", True
    if "悲观" in name:
        return "#cf222e", True
    if "中性" in name:
        return "#9a6700", True
    if "历史" in name or "实际" in name:
        return "#0969da", False
    return "#8250df", False


def parse_chart_spec(spec: str) -> dict | None:
    """Parse a ```chart block: `title:` line, `x:` labels, then `系列名: v1, v2` lines ("-" = no data)."""
    title = ""
    labels: list[str] = []
    series: list[tuple[str, list[float | None]]] = []
    for raw in spec.strip().splitlines():
        line = raw.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key == "title":
            title = value
        elif key == "x":
            labels = [v.strip() for v in value.split(",")]
        elif value:
            points: list[float | None] = []
            for v in value.split(","):
                v = v.strip()
                points.append(None if v in ("", "-", "null", "None") else float(v))
            series.append((key, points))
    if not labels or not series:
        return None
    return {"title": title, "labels": labels, "series": series}


def render_chart(chart: dict, index: int) -> str:
    datasets = []
    for name, points in chart["series"]:
        color, dashed = _chart_style(name)
        datasets.append(
            {
                "label": name,
                "data": points,
                "borderColor": color,
                "backgroundColor": color,
                "tension": 0.25,
                "spanGaps": True,
                "pointRadius": 3,
                "borderWidth": 2.2,
                "borderDash": [6, 3] if dashed else [],
            }
        )
    config = {
        "type": "line",
        "data": {"labels": chart["labels"], "datasets": datasets},
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"position": "bottom"},
                "title": {"display": bool(chart["title"]), "text": chart["title"]},
            },
        },
    }
    return (
        f'<div class="chart-box"><canvas id="chart-{index}"></canvas></div>\n'
        f'<script>new Chart(document.getElementById("chart-{index}"), '
        f"{json.dumps(config, ensure_ascii=False)});</script>"
    )


def extract_charts(text: str) -> tuple[str, list[dict]]:
    """Replace ```chart blocks with placeholders; unparsable blocks stay as code blocks."""
    charts: list[dict] = []

    def repl(match: re.Match) -> str:
        chart = parse_chart_spec(match.group(1))
        if chart is None:
            return match.group(0)
        charts.append(chart)
        return f'<div data-chart-block="{len(charts) - 1}"></div>'

    return _CHART_BLOCK_RE.sub(repl, text), charts


def convert_markdown_file(md: markdown.Markdown, md_file: Path) -> tuple[str, str, bool]:
    text = md_file.read_text(encoding="utf-8")
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    title = re.sub(r"^#+\s*", "", first_line).strip() or md_file.stem
    text, charts = extract_charts(text)
    md.reset()
    body_html = md.convert(text)
    for i, chart in enumerate(charts):
        body_html = body_html.replace(f'<div data-chart-block="{i}"></div>', render_chart(chart, i))
    return title, rewrite_md_links(body_html), bool(charts)


def extract_rating(md_file: Path) -> str | None:
    match = _RATING_RE.search(md_file.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def rating_badge(rating: str | None) -> str:
    if not rating:
        return ""
    return f'<span class="rating r-{rating.lower()}">{RATING_LABELS[rating]}</span>'


def build_report_pages(md: markdown.Markdown) -> list[tuple[str, list[tuple[str, str, str | None]]]]:
    """Render reports/<stock>/<file>.html; return [(stock, [(title, href, rating)])]."""
    groups: list[tuple[str, list[tuple[str, str, str | None]]]] = []
    for stock_dir in sorted(REPORTS_DIR.iterdir()):
        if not stock_dir.is_dir():
            continue
        stock = stock_dir.name
        entries = []
        for md_file in sorted(stock_dir.glob("*.md")):
            title, body_html, has_charts = convert_markdown_file(md, md_file)
            out_dir = SITE_DIR / "reports" / stock
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{md_file.stem}.html").write_text(
                render_page(
                    title,
                    body_html,
                    '<a href="../index.html">&larr; 个股分析报告</a> &nbsp;·&nbsp; <a href="../../index.html">首页</a>',
                    has_charts,
                ),
                encoding="utf-8",
            )
            entries.append((title, f"{stock}/{md_file.stem}.html", extract_rating(md_file)))
        groups.append((stock, entries))
    return groups


def build_select_pages(md: markdown.Markdown) -> list[tuple[str, str]]:
    """Render select/<file>.html; return [(title, href)]."""
    entries: list[tuple[str, str]] = []
    if not SELECT_DIR.is_dir():
        return entries
    for md_file in sorted(SELECT_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        first_line = text.strip().splitlines()[0] if text.strip() else ""
        title = re.sub(r"^#+\s*", "", first_line).strip() or md_file.stem
        text, charts = extract_charts(text)
        if "选股结果分类" in title:
            lines = text.splitlines()
            head_end = 1
            while head_end < len(lines) and lines[head_end].strip() == "":
                head_end += 1
            head_end = min(head_end + 1, len(lines))
            head = "\n".join(lines[:head_end]) + "\n"
            rest = "\n".join(lines[head_end:])
            md.reset()
            body_html = md.convert(head) + PIN_NOTE + md.convert(rest)
        else:
            md.reset()
            body_html = md.convert(text)
        for i, chart in enumerate(charts):
            body_html = body_html.replace(f'<div data-chart-block="{i}"></div>', render_chart(chart, i))
        body_html = rewrite_md_links(body_html)
        out_dir = SITE_DIR / "select"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{md_file.stem}.html"
        out_file.write_text(
            render_page(
                title,
                body_html,
                '<a href="index.html">&larr; 选股结果</a> &nbsp;·&nbsp; <a href="../index.html">首页</a>',
                bool(charts),
            ),
            encoding="utf-8",
        )
        entries.append((title, f"{md_file.stem}.html"))
    return entries


def build_restructuring_pages(md: markdown.Markdown) -> list[tuple[str, str]]:
    """Render restructuring/<file>.html; return [(title, href)]."""
    entries: list[tuple[str, str]] = []
    if not RESTRUCTURING_DIR.is_dir():
        return entries
    for md_file in sorted(RESTRUCTURING_DIR.glob("*.md")):
        title, body_html, has_charts = convert_markdown_file(md, md_file)
        out_dir = SITE_DIR / "restructuring"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{md_file.stem}.html").write_text(
            render_page(
                title,
                body_html,
                '<a href="index.html">&larr; 重大资产重组观察组</a> &nbsp;·&nbsp; <a href="../index.html">首页</a>',
                has_charts,
            ),
            encoding="utf-8",
        )
        entries.append((title, f"{md_file.stem}.html"))
    return entries


def build_section_pages(
    groups: list[tuple[str, list[tuple[str, str, str | None]]]],
    select_entries: list[tuple[str, str]],
    restructuring_entries: list[tuple[str, str]],
) -> None:
    # 个股分析报告
    sections = ['<p class="nav"><a href="../index.html">&larr; 首页</a></p>', "<h1>个股分析报告</h1>"]
    total = sum(len(entries) for _, entries in groups)
    sections.append(f"<p>共 {len(groups)} 只标的 · {total} 篇报告，按代码排序。每篇包含五个模块：基本面 / 技术分析 / 多空辩论（含七项 α 标准评分）/ 风险评估 / 策略参考。</p>")
    for stock, entries in groups:
        sections.append(f"<h3>{html.escape(stock)}</h3>")
        sections.append('<ul class="report-list">')
        for title, href, rating in entries:
            sections.append(f'<li><a href="{html.escape(href)}">{html.escape(title)}</a>{rating_badge(rating)}</li>')
        sections.append("</ul>")
    reports_dir = SITE_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "index.html").write_text(render_index_page("个股分析报告", "\n".join(sections)), encoding="utf-8")

    # 重大资产重组观察组
    sections = ['<p class="nav"><a href="../index.html">&larr; 首页</a></p>', "<h1>重大资产重组观察组</h1>"]
    sections.append("<p>CANSLIM <strong>N</strong>（New）：重大资产重组可能带来新业务 / 新管理层 / 基本面转折。本组为事件观察名单，不参与评分与买卖纪律。信息报告为 AI 整理的公开资料：事件背景与时间线 / 交易核心方案 / 并购前后业务与治理变化 / 交易要点拆解 / 跟踪指标清单。</p>")
    watch_entries = [(t, h) for t, h in select_entries if "重大资产重组" in t]
    if watch_entries:
        sections.append("<h2>观察名单</h2>")
        sections.append('<ul class="report-list">')
        for title, href in watch_entries:
            sections.append(f'<li><a href="../select/{html.escape(href)}">{html.escape(title)}</a></li>')
        sections.append("</ul>")
    sections.append(f"<h2>个股信息报告（{len(restructuring_entries)} 篇）</h2>")
    sections.append('<ul class="report-list">')
    for title, href in restructuring_entries:
        short = re.sub(r"重大资产重组信息报告$", "", title).strip()
        sections.append(f'<li><a href="{html.escape(href)}">{html.escape(short or title)}</a></li>')
    sections.append("</ul>")
    restructuring_dir = SITE_DIR / "restructuring"
    restructuring_dir.mkdir(parents=True, exist_ok=True)
    (restructuring_dir / "index.html").write_text(render_index_page("重大资产重组观察组", "\n".join(sections)), encoding="utf-8")

    # 选股结果
    sections = ['<p class="nav"><a href="../index.html">&larr; 首页</a></p>', "<h1>选股结果</h1>"]
    sections.append(f"<p>共 {len(select_entries)} 份筛选文件：业绩筛选、分类选股、七项 α 标准复核、重大资产重组观察等。</p>")
    sections.append('<ul class="report-list">')
    for title, href in select_entries:
        sections.append(f'<li><a href="{html.escape(href)}">{html.escape(title)}</a></li>')
    sections.append("</ul>")
    select_dir = SITE_DIR / "select"
    select_dir.mkdir(parents=True, exist_ok=True)
    (select_dir / "index.html").write_text(render_index_page("选股结果", "\n".join(sections)), encoding="utf-8")


def build_home_page(
    groups: list[tuple[str, list[tuple[str, str, str | None]]]],
    select_entries: list[tuple[str, str]],
    restructuring_entries: list[tuple[str, str]],
) -> None:
    total_reports = sum(len(entries) for _, entries in groups)
    cards = [
        (
            "reports/index.html",
            "个股分析报告",
            "TradingAgents 五模块深度报告：基本面 / 技术分析 / 多空辩论（含七项 α 标准评分）/ 风险评估 / 策略参考。",
            f"{len(groups)} 只标的 · {total_reports} 篇报告",
        ),
        (
            "restructuring/index.html",
            "重大资产重组观察组",
            "CANSLIM N 属性事件观察：近 90 天公告的资产重组名单 + 逐标的公开信息研究报告。",
            f"{len(restructuring_entries)} 篇信息报告",
        ),
        (
            "select/index.html",
            "选股结果",
            "定期筛选：中报业绩高增速、分类选股、七项 α 标准复核等。",
            f"{len(select_entries)} 份筛选文件",
        ),
    ]
    card_html = "\n".join(
        f"""<div class="section-card">
<h2><a href="{href}">{title}</a></h2>
<p class="desc">{desc}</p>
<p class="count">{count}</p>
</div>"""
        for href, title, desc, count in cards
    )
    body = f"""<h1>Finding Growth Stocks</h1>
<p>AI-assisted multi-agent trading analysis reports.</p>
<div class="methodology">
<p><strong>最强成长价投法（静水2008）</strong></p>
<ol>
<li>读财报，并找以下关键词。</li>
<li>选择财报中带有：<strong>供不应求、行业高景气、供需偏紧、产品涨价、出货量超预期、下游加价意愿强</strong>等字样。</li>
<li>看核心指标：<strong>营收与利润增速＞40%</strong>。</li>
<li>增加胜率：具有<strong>行业趋势和板块效应</strong>。</li>
<li>同时满足条件 2、3、4 的，大概率就是这一财报期的良好基本面成长股，你在其中选择自己能力圈范围内的。</li>
<li>分批分仓介入，介入后，<strong>对了拿住，错了砍掉</strong>。</li>
<li>周而复始，财富自由，这就成长股投资法。就是这么朴实无华，重剑无锋，大巧不工。</li>
</ol>
<p class="attr">— 静水2008，成长股投资法</p>
</div>
<div class="sections">
{card_html}
</div>"""
    (SITE_DIR / "index.html").write_text(render_index_page("Finding Growth Stocks", body), encoding="utf-8")


def main() -> None:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
    SITE_DIR.mkdir(exist_ok=True)

    groups = build_report_pages(md)
    select_entries = build_select_pages(md)
    restructuring_entries = build_restructuring_pages(md)
    build_section_pages(groups, select_entries, restructuring_entries)
    build_home_page(groups, select_entries, restructuring_entries)

    total_reports = sum(len(entries) for _, entries in groups)
    print(
        f"Built {len(groups)} stock groups ({total_reports} reports), "
        f"{len(select_entries)} select files, {len(restructuring_entries)} restructuring reports, "
        f"4 index pages into {SITE_DIR}"
    )


if __name__ == "__main__":
    main()
