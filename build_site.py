#!/usr/bin/env python3
"""Build the FindingGrowthStocks static site from markdown reports."""
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"
SELECT_DIR = ROOT / "select"
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
.nav { margin-bottom: 1.5rem; }
.nav a { font-size: 0.9rem; }
"""

INDEX_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.6; color: #24292f; max-width: 960px; margin: 0 auto; padding: 2rem 1rem; background: #fff; }
h1 { font-size: 1.8rem; border-bottom: 1px solid #d0d7de; padding-bottom: 0.5rem; margin-bottom: 1.5rem; }
h2 { font-size: 1.3rem; margin: 1.5rem 0 0.8rem; color: #1f2328; }
h3 { font-size: 1.05rem; margin: 1rem 0 0.5rem; color: #24292f; }
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }
.report-list { list-style: none; }
.report-list li { padding: 0.5rem 0; border-bottom: 1px solid #d0d7de; }
.report-list li:last-child { border-bottom: none; }
.date { color: #656d76; font-size: 0.9rem; margin-left: 0.5rem; }
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


def render_page(title: str, body_html: str, back_href: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<div class="nav"><a href="{back_href}">&larr; Back to index</a></div>
{body_html}
</body>
</html>
"""


def convert_markdown_file(md: markdown.Markdown, md_file: Path) -> tuple[str, str]:
    text = md_file.read_text(encoding="utf-8")
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    title = re.sub(r"^#+\s*", "", first_line).strip() or md_file.stem
    md.reset()
    return title, md.convert(text)


def main() -> None:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
    SITE_DIR.mkdir(exist_ok=True)

    groups: dict[str, list[tuple[str, str]]] = {}
    for stock_dir in sorted(REPORTS_DIR.iterdir()):
        if not stock_dir.is_dir():
            continue
        stock = stock_dir.name
        entries = []
        for md_file in sorted(stock_dir.glob("*.md")):
            title, body_html = convert_markdown_file(md, md_file)
            out_dir = SITE_DIR / "reports" / stock
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{md_file.stem}.html"
            out_file.write_text(render_page(title, body_html, "../../index.html"), encoding="utf-8")
            entries.append((title, f"reports/{stock}/{md_file.stem}.html"))

        groups[stock] = entries

    select_entries: list[tuple[str, str]] = []
    if SELECT_DIR.is_dir():
        for md_file in sorted(SELECT_DIR.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            first_line = text.strip().splitlines()[0] if text.strip() else ""
            title = re.sub(r"^#+\s*", "", first_line).strip() or md_file.stem
            if "选股结果分类" in title:
                lines = text.splitlines()
                head = "\n".join(lines[:2]) + "\n"
                rest = "\n".join(lines[2:])
                md.reset()
                body_html = md.convert(head) + PIN_NOTE + md.convert(rest)
            else:
                md.reset()
                body_html = md.convert(text)
            out_dir = SITE_DIR / "select"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{md_file.stem}.html"
            out_file.write_text(render_page(title, body_html, "../index.html"), encoding="utf-8")
            select_entries.append((title, f"select/{md_file.stem}.html"))

    sections = []
    if select_entries:
        sections.append("<h2>选股结果</h2>")
        sections.append('<ul class="report-list">')
        for title, href in select_entries:
            sections.append(f'<li><a href="{html.escape(href)}">{html.escape(title)}</a></li>')
        sections.append("</ul>")

    sections.append("<h2>个股分析报告</h2>")
    for stock in sorted(groups):
        sections.append(f"<h3>{html.escape(stock)}</h3>")
        sections.append('<ul class="report-list">')
        for title, href in groups[stock]:
            sections.append(f'<li><a href="{html.escape(href)}">{html.escape(title)}</a></li>')
        sections.append("</ul>")

    index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Finding Growth Stocks</title>
<style>{INDEX_CSS}</style>
</head>
<body>
<h1>Finding Growth Stocks</h1>
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
{chr(10).join(sections)}
<footer>
<p>Generated by TradingAgents framework. For research purposes only, not investment advice.</p>
<p><a href="https://github.com/TauricResearch/TradingAgents">TradingAgents</a> | <a href="https://github.com/panhaoneo/FindingGrowthStocks">GitHub</a></p>
</footer>
</body>
</html>
"""
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print(f"Built {len(groups)} stock groups and {len(select_entries)} select files into {SITE_DIR}")


if __name__ == "__main__":
    main()
