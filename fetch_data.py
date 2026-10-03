"""
修复版：之前START_DATE/END_DATE是写死的固定日期（2026-06-01到2026-08-07），
不管哪天跑脚本，抓到的都是同一段历史数据，不会跟着"今天"变化。

这一版改成：每次运行，自动抓"从今天往前推90天"的数据——
跟Agent里"实时查询"那部分用的是同一套逻辑（datetime.now() + timedelta），
这样长期追踪的股票和临时查询的股票，用的是统一的、动态的时间窗口。
"""
import time
import sqlite3
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd

WATCHLIST = {
    "600519": ("贵州茅台", "A股", "sh600519"),
    "600036": ("招商银行", "A股", "sh600036"),
    "00700": ("腾讯控股", "港股", "00700"),
    "00005": ("汇丰控股", "港股", "00005"),
    "09988": ("阿里巴巴", "港股", "09988"),
}

# 之前这里是两个写死的字符串，现在改成跟"今天"绑定，每次跑都会自动更新
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=90)


def fetch_with_retry(fetch_func, max_retries=3, wait_seconds=3):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return fetch_func()
        except Exception as e:
            last_error = e
            print(f"  第{attempt}次尝试失败：{e}，{wait_seconds}秒后重试...")
            time.sleep(wait_seconds)
    raise last_error


all_rows = []

for ticker, (name, market, sina_symbol) in WATCHLIST.items():
    print(f"正在抓取 {name}（{ticker}，{market}）...")

    if market == "A股":
        df = fetch_with_retry(
            lambda: ak.stock_zh_a_daily(symbol=sina_symbol, adjust="")
        )
        df = df.reset_index()
        df["date"] = df["date"].astype(str)
    else:
        df = fetch_with_retry(
            lambda: ak.stock_hk_daily(symbol=sina_symbol, adjust="")
        )
        df["date"] = df["date"].astype(str)

    df = df[["date", "close"]]
    df = df[(df["date"] >= START_DATE.strftime("%Y-%m-%d")) & (df["date"] <= END_DATE.strftime("%Y-%m-%d"))]

    df["ticker"] = ticker
    df["name"] = name
    df["market"] = market
    all_rows.append(df)

    print(f"  -> ✅ 抓到 {len(df)} 天的数据")
    time.sleep(1)

combined = pd.concat(all_rows, ignore_index=True)
combined = combined[["ticker", "name", "market", "date", "close"]]

print()
print(f"=== 数据时间窗口：{START_DATE.strftime('%Y-%m-%d')} 到 {END_DATE.strftime('%Y-%m-%d')}（滚动最近90天）===")
print(combined.head(10))
print(f"总共 {len(combined)} 行")

conn = sqlite3.connect("finance.db")
combined.to_sql("stock_prices", conn, if_exists="replace", index=False)
conn.close()

print()
print("✅ 已存入数据库的 stock_prices 表")
