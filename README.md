# FinSight — AI Agent for Financial Data Analysis & Reporting

An end-to-end pipeline that fetches real stock market data (A-shares & Hong Kong stocks), analyzes returns and volatility, auto-generates formatted Excel reports, and lets you query the results in natural language through an AI agent built with Claude's function calling.

## What it does

- **Fetches real historical price data** for a watchlist of A-share and Hong Kong stocks via `akshare`, with automatic retry logic to handle upstream data source instability
- **Analyzes performance** with `pandas` — daily returns, 5-day moving averages, total return, and volatility per stock
- **Auto-generates a formatted Excel report** with conditional formatting (gains in green, losses in red) and price trend charts, using `openpyxl`
- **Answers natural language questions** about the data (e.g. *"How has Tencent performed?"*) through an AI agent that uses Claude's function calling to decide which data to query and grounds its answers in real numbers instead of guessing

## Why this design

The project started with `yfinance`, which is unreliable from within China. After testing several `akshare` data sources, I found the Eastmoney-backed endpoints intermittently dropped connections, while Sina-backed endpoints were consistently stable — so the pipeline standardizes on Sina sources with a retry wrapper. The project scope is intentionally limited to A-shares and Hong Kong stocks (US data sources proved unreliable), which also aligns with the Hong Kong market focus of the roles I'm targeting.

## Tech stack

Python · pandas · SQLite · akshare · openpyxl · Claude API (function calling)

## Project structure

```
finsight-ai-agent/
├── fetch_data.py       # Pull real price data into SQLite (finance.db)
├── analyze.py          # Compute returns, volatility, moving averages
├── generate_report.py  # Auto-generate a formatted Excel report
├── agent.py            # Interactive AI agent (Claude function calling)
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
5. Set your Claude API key and chat with the agent:
   ```
   export ANTHROPIC_API_KEY="your-key-here"
   python3 agent.py
   ```

## Example

```
You: How has Tencent performed?
Agent: Tencent Holdings (00700, HK) delivered a +9.82% return over the
       tracked period, with a relatively moderate volatility of 2.95%...
```

## Future improvements

- Extend the watchlist beyond 5 stocks
- Add more tools to the agent (e.g. multi-stock comparison, custom date ranges)
- Deploy as a web app (Streamlit)
