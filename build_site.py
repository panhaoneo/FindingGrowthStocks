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
            title, body_html = convert_markdown_file(md, md_file)
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
