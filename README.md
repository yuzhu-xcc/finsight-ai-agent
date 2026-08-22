# FinSight — AI Agent for Financial Data Analysis & Reporting

An end-to-end pipeline that fetches real stock market data (A-shares & Hong Kong stocks), analyzes returns and volatility, auto-generates formatted Excel reports, and lets you query any A-share/HK stock in natural language through an AI agent built with Claude's function calling — available both as a terminal chat and a web app.

## What it does

- **Fetches real historical price data** for a watchlist of A-share and Hong Kong stocks via `akshare`, with automatic retry logic to handle upstream data source instability
- **Analyzes performance** with `pandas` — daily returns, 5-day moving averages, total return, and volatility per stock
- **Auto-generates a formatted Excel report** with conditional formatting (gains in green, losses in red) and price trend charts, using `openpyxl`
- **Answers natural language questions about any A-share or Hong Kong stock** through an AI agent that uses Claude's function calling to decide what to query. It checks the local tracked-stock database first, and falls back to a live query for any other ticker — not limited to a fixed watchlist
- **Available as a web app** (Streamlit) with a chat interface, in addition to the terminal version

## Why this design

The project started with `yfinance`, which is unreliable from within China. After testing several `akshare` data sources, I found the Eastmoney-backed endpoints intermittently dropped connections, while Sina-backed endpoints were consistently stable — so the pipeline standardizes on Sina sources with a retry wrapper. The project scope is intentionally limited to A-shares and Hong Kong stocks (US data sources proved unreliable), which also aligns with the Hong Kong market focus of the roles I'm targeting.

The agent's `get_stock_summary` tool uses a database-first, live-fallback strategy: instant results for the core tracked watchlist, live `akshare` queries for anything else, so the agent isn't limited to a fixed list of stocks.

## Tech stack

Python · pandas · SQLite · akshare · openpyxl · Claude API (function calling) · Streamlit

## Project structure

```
finsight-ai-agent/
├── fetch_data.py       # Pull real price data into SQLite (finance.db)
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
2. Fetch data and build the database:
   ```
   python3 fetch_data.py
   ```
3. Run the analysis:
   ```
   python3 analyze.py
   ```
4. Generate the Excel report:
   ```
   python3 generate_report.py
   ```
5. Chat with the agent in the terminal:
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
You: How has Pop Mart performed recently?
Agent: Pop Mart (09992, HK) — live query, last 90 days:
       Start: 245.60 → End: 268.40, total return +9.28%,
       volatility 3.1%...
```

## Future improvements

- Add more tools to the agent (e.g. multi-stock comparison, custom date ranges)
- Cache live-fetched data so repeated queries don't re-hit the API
- Add unit tests for the data pipeline and agent tools
