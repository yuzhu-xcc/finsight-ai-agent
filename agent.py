"""
Week 3 修复版：本地数据库查询加上错误处理，数据库不存在/表不存在时
优雅降级到实时联网查询，而不是让整个功能崩溃。
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd
from anthropic import Anthropic


def get_stock_summary(ticker: str) -> dict:
    ticker = ticker.strip()

    df = pd.DataFrame()
    try:
        conn = sqlite3.connect("finance.db")
        df = pd.read_sql_query("SELECT * FROM stock_prices WHERE ticker = ?", conn, params=(ticker,))
        conn.close()
    except Exception:
        df = pd.DataFrame()

    if not df.empty:
        df = df.sort_values("date")
        df["daily_return_pct"] = df["close"].pct_change() * 100
        start_price = df["close"].iloc[0]
        end_price = df["close"].iloc[-1]
        return {
            "ticker": ticker,
            "name": df["name"].iloc[0],
            "market": df["market"].iloc[0],
            "source": "本地追踪数据库",
            "start_price": round(float(start_price), 2),
            "end_price": round(float(end_price), 2),
            "total_return_pct": round(float((end_price - start_price) / start_price * 100), 2),
            "volatility": round(float(df["daily_return_pct"].std()), 2),
        }

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        if ticker.isdigit() and len(ticker) == 6:
            prefix = "sh" if ticker.startswith("6") else "sz"
            live_df = ak.stock_zh_a_daily(symbol=f"{prefix}{ticker}", adjust="")
            market = "A股"
        else:
            hk_code = ticker.zfill(5)
            live_df = ak.stock_hk_daily(symbol=hk_code, adjust="")
            market = "港股"

        live_df["date"] = live_df["date"].astype(str)
        live_df = live_df[
            (live_df["date"] >= start_date.strftime("%Y-%m-%d"))
            & (live_df["date"] <= end_date.strftime("%Y-%m-%d"))
        ]

        if live_df.empty:
            return {"error": f"没有找到股票代码 {ticker} 最近的数据，请确认代码是否正确"}

        live_df["daily_return_pct"] = live_df["close"].pct_change() * 100
        start_price = live_df["close"].iloc[0]
        end_price = live_df["close"].iloc[-1]

        return {
            "ticker": ticker,
            "market": market,
            "source": "实时查询（最近90天）",
            "start_price": round(float(start_price), 2),
            "end_price": round(float(end_price), 2),
            "total_return_pct": round(float((end_price - start_price) / start_price * 100), 2),
            "volatility": round(float(live_df["daily_return_pct"].std()), 2),
        }
    except Exception as e:
        return {"error": f"查询股票代码 {ticker} 时出错：{e}（提示：目前只支持A股和港股，不支持美股）"}


def list_watchlist() -> list:
    try:
        conn = sqlite3.connect("finance.db")
        df = pd.read_sql_query("SELECT DISTINCT ticker, name, market FROM stock_prices", conn)
        conn.close()
        return df.to_dict(orient="records")
    except Exception:
        return []


tool_functions = {
    "get_stock_summary": get_stock_summary,
    "list_watchlist": list_watchlist,
}

tools = [
    {
        "name": "get_stock_summary",
        "description": (
            "查询任意一支A股或港股的整体表现（期初价、期末价、总收益率、波动率）。"
            "支持系统长期追踪的股票，也支持其他任意A股/港股代码（会自动实时联网查询最近90天数据）。"
            "不支持美股。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "股票代码，A股6位数字（如600519），港股4-5位数字（如00700或700）"},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "list_watchlist",
        "description": "列出系统长期追踪的核心股票清单（代码、名称、市场）。注意：这不代表能查询的全部范围，get_stock_summary可以查询任意A股/港股。",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def extract_text(content_blocks) -> str:
    for block in content_blocks:
        if block.type == "text":
            return block.text
    return ""


def ask_agent(client, messages):
    while True:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return extract_text(response.content)

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  🔧 调用工具：{block.name}，参数：{block.input}")
            result = tool_functions[block.name](**block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        messages.append({"role": "user", "content": tool_results})


client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
messages = []

print("FinSight Agent 已启动，输入你的问题（输入 exit 退出）\n")

while True:
    user_input = input("你：")
    if user_input.strip().lower() in ("exit", "quit", "退出"):
        print("再见！")
        break

    messages.append({"role": "user", "content": user_input})
    answer = ask_agent(client, messages)
    print(f"\nAgent：{answer}\n")
