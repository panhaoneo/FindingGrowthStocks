# Finding Growth Stocks

AI-assisted multi-agent trading analysis reports, generated using the [TradingAgents](https://github.com/TauricResearch/TradingAgents) framework.

## Reports

Reports are organized by stock ticker and date under `reports/`:

```
reports/
  601869_长飞光纤/
    2026-08-26.md
  600105_永鼎股份/
    2026-08-26.md
```

Each report contains five modules:

1. **基本面分析** — Company profile, financials (income statement, balance sheet, cash flow), valuation
2. **技术分析** — Price trends, moving averages, technical indicators, capital flow
3. **多空辩论** — Bull vs bear debate with research manager synthesis
4. **风险评估** — Aggressive / conservative / neutral risk analyst debate
5. **策略参考** — Final rating, entry/exit prices, position sizing, key indicators to track

## Major Restructuring Watch

Event-driven reports on major asset restructurings are organized under `restructuring/`, one markdown file per stock (e.g. `002155_湖南黄金.md`). The watch list page is generated under `select/` (e.g. `restructuring_watch_2026-09-10.md`) and links to each report.

## View Online

Reports are automatically deployed to GitHub Pages on push to `main`.

## Disclaimer

All reports are for research purposes only and do not constitute investment advice.
