"""
Week 3 / Day 15-16：第一版 AI Agent（function calling）

三个部分：
1. 真正干活的Python函数（"秘书"）—— 能查数据库，返回真实数字
2. 工具清单（告诉Claude"秘书"能做哪些事，怎么用）
3. 主流程（"老板"和"秘书"之间的一来一回）
"""
import json
import os
import sqlite3

import pandas as pd
from anthropic import Anthropic


# ========== 第一部分：真正干活的函数（"秘书"）==========

def get_stock_summary(ticker: str) -> dict:
    """查询某支股票在追踪期间内的表现：期初价、期末价、总收益率、波动率。
    跟之前 analyze_returns.py 里算汇总的逻辑一样，只是这次包装成一个"可以被调用的函数"。
    """
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


# 一张"名字对照表"：Claude说要调用"get_stock_summary"这个名字时，
# 我们要知道它对应的是上面哪个真正的Python函数
tool_functions = {
    "get_stock_summary": get_stock_summary,
    "list_watchlist": list_watchlist,
}


# ========== 第二部分：工具清单（告诉Claude有什么"秘书技能"可用）==========
# 每个工具要写清楚：叫什么名字、是干什么用的、需要什么参数
# Claude会根据用户的问题和这份清单里的"description"描述，自己判断该不该调用、调用哪个

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


# ========== 第三部分：主流程（老板和秘书的一来一回）==========

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

user_question = "腾讯这段时间表现怎么样？"
print(f"用户提问：{user_question}\n")

messages = [{"role": "user", "content": user_question}]

# 第一次调用：把问题 + 工具清单一起发给Claude
# Claude这时候会自己判断："这个问题需要真实数据，我该调用get_stock_summary这个工具"
response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    messages=messages,
)
messages.append({"role": "assistant", "content": response.content})

if response.stop_reason == "tool_use":
    # Claude决定调用某个工具了——把它想调用什么、传了什么参数取出来
    tool_use_block = next(block for block in response.content if block.type == "tool_use")
    tool_name = tool_use_block.name
    tool_input = tool_use_block.input
    print(f"🔧 Claude决定调用工具：{tool_name}，参数：{tool_input}")

    # 真正执行这个Python函数（"秘书"真的去查数据库了）
    result = tool_functions[tool_name](**tool_input)
    print(f"📊 拿到的真实数据：{result}\n")

    # 把真实数据"递回去"给Claude，让它基于这份真数据组织语言回答，而不是自己编
    messages.append({
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": tool_use_block.id,
            "content": json.dumps(result, ensure_ascii=False),
        }],
    })

    final_response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )
    print("✅ Claude的最终回答：")
    print(final_response.content[0].text)
else:
    # 如果Claude觉得这个问题不需要查数据，会直接回答（这次的问题应该不会走到这里）
    print("Claude没有调用工具，直接回答：")
    print(response.content[0].text)
