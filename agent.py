"""
设计调整：之前是"本地数据库优先，查不到才联网"，
会导致追踪列表里的5支股票数据永远停留在上次手动跑fetch_data.py那一刻，不会自动更新。

现在反过来："不管问哪支股票，一律先尝试实时联网查询最近90天数据"，
只有联网失败（网络问题、数据源临时不稳定）时，才退回本地数据库里存的旧数据兜底，
并且在返回结果里明确标注这是"备用旧数据"，不会让用户误以为是最新的。
本地数据库从"主要数据源"变成了纯粹的"断网保险丝"。
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd
from anthropic import Anthropic


def _fetch_live(ticker: str):
    """实时联网查询最近90天数据，失败则抛出异常（由调用方决定怎么处理）。"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    if ticker.isdigit() and len(ticker) == 6:
        prefix = "sh" if ticker.startswith("6") else "sz"
        df = ak.stock_zh_a_daily(symbol=f"{prefix}{ticker}", adjust="")
        df = df.reset_index()
        market = "A股"
    else:
        hk_code = ticker.zfill(5)
        df = ak.stock_hk_daily(symbol=hk_code, adjust="")
        market = "港股"

    df["date"] = df["date"].astype(str)
    df = df[(df["date"] >= start_date.strftime("%Y-%m-%d")) & (df["date"] <= end_date.strftime("%Y-%m-%d"))]

    if df.empty:
        raise ValueError(f"没有找到股票代码 {ticker} 最近90天的数据")

    df["daily_return_pct"] = df["close"].pct_change() * 100
    start_price = df["close"].iloc[0]
    end_price = df["close"].iloc[-1]

    return {
        "ticker": ticker,
        "market": market,
        "source": "实时查询（最近90天）",
        "start_price": round(float(start_price), 2),
        "end_price": round(float(end_price), 2),
        "total_return_pct": round(float((end_price - start_price) / start_price * 100), 2),
        "volatility": round(float(df["daily_return_pct"].std()), 2),
    }


def _fetch_from_local_db(ticker: str):
    """从本地数据库查旧数据，查不到返回None（不抛异常，方便调用方判断）。"""
    try:
        conn = sqlite3.connect("finance.db")
        df = pd.read_sql_query("SELECT * FROM stock_prices WHERE ticker = ?", conn, params=(ticker,))
        conn.close()
    except Exception:
        return None

    if df.empty:
        return None

    df = df.sort_values("date")
    df["daily_return_pct"] = df["close"].pct_change() * 100
    start_price = df["close"].iloc[0]
    end_price = df["close"].iloc[-1]

    return {
        "ticker": ticker,
        "name": df["name"].iloc[0],
        "market": df["market"].iloc[0],
        "source": f"⚠️本地缓存旧数据（{df['date'].iloc[0]}至{df['date'].iloc[-1]}，实时查询失败时的备用数据，可能不是最新）",
        "start_price": round(float(start_price), 2),
        "end_price": round(float(end_price), 2),
        "total_return_pct": round(float((end_price - start_price) / start_price * 100), 2),
        "volatility": round(float(df["daily_return_pct"].std()), 2),
    }


def get_stock_summary(ticker: str) -> dict:
    """
    查询任意一支A股或港股的整体表现。
    优先级：先实时联网查询最近90天数据；联网失败才退回本地数据库里的旧数据兜底。
    """
    ticker = ticker.strip()

    try:
        return _fetch_live(ticker)
    except Exception as live_error:
        fallback = _fetch_from_local_db(ticker)
        if fallback is not None:
            return fallback
        return {"error": f"实时查询失败且本地也没有缓存数据：{live_error}（提示：目前只支持A股和港股，不支持美股）"}


def list_watchlist() -> list:
    """列出本地数据库里有缓存的股票（仅供断网时兜底参考，get_stock_summary支持查询任意A股/港股）。"""
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
            "查询任意一支A股或港股最近90天的整体表现（期初价、期末价、总收益率、波动率），"
            "永远优先实时联网查询，只有联网失败时才使用本地缓存的旧数据兜底（结果中会明确标注）。"
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
        "description": "列出本地有缓存数据的股票（仅在实时查询失败时作为兜底参考，不代表能查询的全部范围）。",
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
