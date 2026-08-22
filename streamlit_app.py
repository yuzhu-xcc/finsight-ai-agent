"""
FinSight 网页版 Agent（修复版）
修复：本地数据库查询之前没有错误处理，部署到没有finance.db的服务器上会直接崩溃。
现在改成：本地查询失败（数据库不存在/表不存在）就当作"本地没有"，
自动往下走实时联网查询这条路，不会导致整个功能瘫痪。
"""
import json
import sqlite3
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd
import streamlit as st
from anthropic import Anthropic


def get_stock_summary(ticker: str) -> dict:
    ticker = ticker.strip()

    # ---- 第一步：先查本地数据库，但这次给它加上保护 ----
    df = pd.DataFrame()
    try:
        conn = sqlite3.connect("finance.db")
        df = pd.read_sql_query("SELECT * FROM stock_prices WHERE ticker = ?", conn, params=(ticker,))
        conn.close()
    except Exception:
        # 数据库文件不存在，或者表不存在，都会走到这里——
        # 不让程序崩溃，而是当作"本地没有这支股票的数据"，继续往下走实时查询
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

    # ---- 第二步：本地没有，实时联网查询最近90天 ----
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
        return []  # 本地数据库不存在时返回空列表，而不是崩溃


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
            result = tool_functions[block.name](**block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        messages.append({"role": "user", "content": tool_results})


# ========== 网页界面 ==========

st.set_page_config(page_title="FinSight Agent", page_icon="📈")
st.title("📈 FinSight — AI 金融数据分析 Agent")
st.caption("任意A股/港股 · pandas 分析 · 基于 Claude function calling")

client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

if "api_messages" not in st.session_state:
    st.session_state.api_messages = []
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []

for role, text in st.session_state.display_messages:
    with st.chat_message(role):
        st.markdown(text)

user_input = st.chat_input("问问关于A股/港股的问题，比如“泡泡玛特这段时间表现怎么样”")

if user_input:
    st.session_state.display_messages.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.api_messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("正在查询数据..."):
            answer = ask_agent(client, st.session_state.api_messages)
        st.markdown(answer)

    st.session_state.display_messages.append(("assistant", answer))
