# FinSight — AI Agent for Financial Data Analysis & Reporting

An end-to-end pipeline that fetches real stock market data (A-shares & Hong Kong stocks), analyzes returns and volatility, auto-generates formatted Excel reports, and lets you query any A-share/HK stock in natural language through an AI agent built with Claude's function calling — available both as a terminal chat and a web app.

## What it does

- **Fetches real historical price data** for a watchlist of A-share and Hong Kong stocks via `akshare`, with automatic retry logic to handle upstream data source instability
- **Analyzes performance** with `pandas` — daily returns, 5-day moving averages, total return, and volatility per stock
- **Auto-generates a formatted Excel report** with conditional formatting (gains in green, losses in red) and price trend charts, using `openpyxl`
- **Answers natural language questions about any A-share or Hong Kong stock** through an AI agent that uses Claude's function calling. For every query, it always tries a live lookup first (so results are current, not a stale snapshot); if the live source fails, it falls back to a locally cached snapshot and clearly labels the result as such
- **Available as a web app** (Streamlit) with a chat interface, in addition to the terminal version

## Why this design

The project started with `yfinance`, which is unreliable from within China. After testing several `akshare` data sources, I found the Eastmoney-backed endpoints intermittently dropped connections, while Sina-backed endpoints were consistently stable — so the pipeline standardizes on Sina sources with a retry wrapper. The project scope is intentionally limited to A-shares and Hong Kong stocks (US data sources proved unreliable), which also aligns with the Hong Kong market focus of the roles I'm targeting.

The agent's `get_stock_summary` tool is live-first with a local-cache fallback: every query attempts a fresh `akshare` lookup over a rolling 90-day window, so results reflect the current date rather than a fixed snapshot from whenever the database was last populated. Only if the live request fails does it fall back to the locally stored watchlist data (`fetch_data.py`), and the response is clearly marked as a cached fallback so the user knows the data may be stale.

## Tech stack

Python · pandas · SQLite · akshare · openpyxl · Claude API (function calling) · Streamlit

## Project structure

```
finsight-ai-agent/
├── fetch_data.py       # Pull real price data into SQLite (finance.db) — used as a fallback cache
├── analyze.py          # Compute returns, volatility, moving averages
├── generate_report.py  # Auto-generate a formatted Excel report
├── agent.py             # Terminal AI agent (Claude function calling)
├── streamlit_app.py     # Web chat interface for the same agent
└── requirements.txt
```

## How to run

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Build the local fallback cache (optional but recommended):
   ```
   python3 fetch_data.py
   ```
3. Run the analysis / Excel report on the cached watchlist:
   ```
   python3 analyze.py
   python3 generate_report.py
   ```
4. Chat with the agent in the terminal:
   ```
   export ANTHROPIC_API_KEY="your-key-here"
   python3 agent.py
   ```
   Or launch the web version:
   ```
   streamlit run streamlit_app.py
   ```
   (set `ANTHROPIC_API_KEY` in `.streamlit/secrets.toml` for the web version)

## Example

```
You: How has Tencent performed recently?
Agent: Tencent Holdings (00700, HK) — live query, last 90 days:
       Start: 452.00 → End: 421.20, total return -6.81%,
       volatility 2.24%...
```

## Future improvements

- Schedule `fetch_data.py` to run automatically (e.g. daily) so the fallback cache doesn't go stale
- Add more tools to the agent (e.g. multi-stock comparison, custom date ranges)
- Add unit tests for the data pipeline and agent tools
