# FinSight — AI Agent for Financial Data Analysis & Reporting

An AI agent for A-share and Hong Kong stock analysis. It pulls real daily price data, computes returns and volatility with pandas, and exposes those capabilities as tools to Claude through function calling — so you can ask in plain language (e.g. *"How has Tencent performed recently?"* or *"Generate an Excel report for Tencent and Moutai"*) and get answers grounded in numbers computed by code, with the exact date range stated. Available as a terminal chat and as a deployed web app.

## What it does

- **Answers natural-language questions about any A-share or Hong Kong stock.** The agent decides which tool to call; every query tries a live lookup first (rolling last 90 days), and only falls back to a locally cached snapshot if the live source fails — clearly labelled as cached
- **States its data dates.** Every reported price comes with the exact start/end dates of the data behind it (daily closing prices), so users know which trading day a number refers to
- **Generates Excel reports on request.** Ask for a report and the agent builds a formatted workbook (up to 10 stocks): a summary sheet with returns and volatility (gains green, losses red) plus a per-stock sheet with daily closes and a trend chart. A failed ticker doesn't break the whole report — the rest are included and the failures are listed
- **Handles unreliable data feeds.** Automatic retry logic in the batch pipeline, graceful fallback to cached data, and tool errors returned to the model as explanations instead of crashes
- **Offline batch pipeline** for a fixed watchlist: fetch prices into SQLite, analyze with pandas (returns, volatility, 5-day moving average), and generate a weekly Excel report
- **Web app** (Streamlit) with a chat interface and a download button for generated reports

## Why this design

The project started with `yfinance`, which is unreliable from within China. After testing several `akshare` data sources, I found the Eastmoney-backed endpoints intermittently dropped connections, while Sina-backed endpoints were consistently stable — so the pipeline standardizes on Sina sources with a retry wrapper. The scope is intentionally limited to A-shares and Hong Kong stocks (US data sources proved unreliable), which also matches the Hong Kong market focus of the roles I'm targeting.

The agent's price lookup is **live-first with a local-cache fallback**. An earlier version was database-first, which meant the tracked watchlist silently froze at the last manual refresh while other tickers were fetched live — inconsistent freshness for the same question. Flipping the priority makes every ticker current, and turns the database into a safety net that is explicitly labelled when used.

Tools, the system prompt and the agent loop live in one shared module (`finsight_core.py`); the terminal and web interfaces are thin shells around it, so there is a single source of truth for the logic.

## Tech stack

Python · pandas · SQLite · akshare · openpyxl · Claude API (function calling) · Streamlit

## Project structure

```
finsight-ai-agent/
├── finsight_core.py     # Tools, system prompt, agent loop (shared by both interfaces)
├── agent.py             # Terminal chat interface
├── streamlit_app.py     # Web chat interface (with Excel download)
├── fetch_data.py        # Batch: pull a rolling 90-day window into SQLite (finance.db) — the fallback cache
├── analyze.py           # Batch: returns, volatility, moving averages
├── generate_report.py   # Batch: weekly Excel report from the cache
└── requirements.txt
```

## How to run

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. (Optional) Build the local fallback cache and run the batch pipeline:
   ```
   python3 fetch_data.py
   python3 analyze.py
   python3 generate_report.py
   ```
3. Chat with the agent in the terminal:
   ```
   export ANTHROPIC_API_KEY="your-key-here"
   python3 agent.py
   ```
   Generated Excel reports are saved to the `reports/` folder.
4. Or launch the web version (put `ANTHROPIC_API_KEY` in `.streamlit/secrets.toml`):
   ```
   streamlit run streamlit_app.py
   ```

## Example

```
You: Generate an Excel report for Tencent and Moutai
Agent: Done — the report covers Tencent (00700) and Kweichow Moutai (600519),
       using daily closes from 2026-07-07 to 2026-10-02 ...
```

## Known limitations

- Data is daily closing prices from free, scraped sources (`akshare`) — not intraday quotes, and without an uptime guarantee
- The fallback cache is refreshed manually (`fetch_data.py`), not on a schedule
- No automated test suite yet; the public demo runs on my own API credits with no per-user rate limiting

## Future improvements

- Schedule `fetch_data.py` so the fallback cache doesn't go stale
- More tools and metrics (maximum drawdown, Sharpe ratio, multi-stock comparison, custom date ranges)
- Unit tests for the data pipeline and agent tools; usage limits for the public demo
