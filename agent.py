"""
Week 3 / Day 16-17：第二版 AI Agent —— 支持持续对话
跟v1的区别：v1只能回答一个写死的问题，跑一次就结束；
这一版能在终端里一直问下去，而且Claude会记得之前聊过什么。
"""
import json
import os
import sqlite3

import pandas as pd
from anthropic import Anthropic


# ========== 工具函数（跟v1一样，没有变化）==========

def get_stock_summary(ticker: str) -> dict:
    """查询某支股票在追踪期间内的表现：期初价、期末价、总收益率、波动率。"""
    conn = sqlite3.connect("finance.db")
    df = pd.read_sql_query("SELECT * FROM stock_prices WHERE ticker = ?", conn, params=(ticker,))
    conn.close()

    if df.empty:
        return {"error": f"没有找到股票代码 {ticker} 的数据"}

    df = df.sort_values("date")
    df["daily_return_pct"] = df["close"].pct_change() * 100
    start_price = df["close"].iloc[0]
    end_price = df["close"].iloc[-1]

    return {
        "ticker": ticker,
        "name": df["name"].iloc[0],
        "market": df["market"].iloc[0],
        "start_price": round(float(start_price), 2),
        "end_price": round(float(end_price), 2),
        "total_return_pct": round(float((end_price - start_price) / start_price * 100), 2),
        "volatility": round(float(df["daily_return_pct"].std()), 2),
    }


def list_watchlist() -> list:
    """列出目前追踪的所有股票代码、名称、市场。"""
    conn = sqlite3.connect("finance.db")
    df = pd.read_sql_query("SELECT DISTINCT ticker, name, market FROM stock_prices", conn)
    conn.close()
    return df.to_dict(orient="records")


tool_functions = {
    "get_stock_summary": get_stock_summary,
    "list_watchlist": list_watchlist,
}

tools = [
    {
        "name": "get_stock_summary",
        "description": "查询某一支股票在追踪期间内的整体表现，包括期初价、期末价、总收益率和波动率。",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "股票代码，例如 00700（腾讯）或 600519（贵州茅台）"},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "list_watchlist",
        "description": "列出目前系统追踪的所有股票，包含代码、名称、所属市场。",
        "input_schema": {"type": "object", "properties": {}},
    },
]


# ========== 把"问一次、答一次"包装成一个函数 ==========
# 这样不管用户问多少次，都调用同一段逻辑，不用重复写代码

def ask_agent(client, messages):
    """
    把当前的对话历史(messages)发给Claude，如果它要调用工具就执行工具、
    再把结果发回去，直到Claude给出最终的文字回答为止。
    用while循环是因为：有的问题可能需要连续调用好几次工具才能回答完整
    （比如"帮我对比腾讯和茅台"，可能需要连续调用两次get_stock_summary）。
    """
    while True:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Claude不再需要调用工具了，说明它已经准备好最终答案
            return response.content[0].text

        # 还需要调用工具——可能一次返回好几个工具调用请求，全部处理掉
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
        # 回到while循环开头，把工具结果发给Claude，看它这次是直接回答还是还要再查


# ========== 主流程：终端里持续对话 ==========

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
messages = []  # 保存整个对话历史，这样Claude能"记得"之前聊过什么

print("FinSight Agent 已启动，输入你的问题（输入 exit 退出）\n")

while True:
    user_input = input("你：")
    if user_input.strip().lower() in ("exit", "quit", "退出"):
        print("再见！")
        break

    messages.append({"role": "user", "content": user_input})
    answer = ask_agent(client, messages)
    print(f"\nAgent：{answer}\n")
