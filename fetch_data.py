"""
上一版发现：东方财富数据源不稳定（时好时坏，会偶尔断连接）。
这一版全部改用新浪数据源接口（之前测试里从没失败过），
并且加一个"失败自动重试"的保护机制，这样即使偶尔抽风也能自动恢复，不用你手动重跑。
"""
import time
import sqlite3

import akshare as ak
import pandas as pd

# 关注的股票清单：股票代码 -> (公司名, 市场, 新浪接口需要的symbol格式)
# 新浪的A股接口要求代码前面加交易所前缀：上海用sh，深圳用sz
WATCHLIST = {
    "600519": ("贵州茅台", "A股", "sh600519"),
    "600036": ("招商银行", "A股", "sh600036"),
    "00700": ("腾讯控股", "港股", "00700"),
    "00005": ("汇丰控股", "港股", "00005"),
    "09988": ("阿里巴巴", "港股", "09988"),
}

START_DATE = "2026-06-01"
END_DATE = "2026-08-07"


def fetch_with_retry(fetch_func, max_retries=3, wait_seconds=3):
    """
    通用的"带重试"包装函数：
    - fetch_func 是一个不带参数、调用后返回数据的函数
    - 如果失败，等几秒后重试，最多重试 max_retries 次
    - 全部失败后，抛出最后一次的错误，让外面知道这支股票确实拿不到数据
    这样以后不管是A股还是港股，任何一次网络请求都可以复用这个重试逻辑，不用每处都重复写。
    """
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
        df = df.reset_index().rename(columns={"date": "date", "close": "close"})
        df["date"] = df["date"].astype(str)
    else:
        df = fetch_with_retry(
            lambda: ak.stock_hk_daily(symbol=sina_symbol, adjust="")
        )
        df["date"] = df["date"].astype(str)

    df = df[["date", "close"]]
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]

    df["ticker"] = ticker
    df["name"] = name
    df["market"] = market
    all_rows.append(df)

    print(f"  -> ✅ 抓到 {len(df)} 天的数据")
    time.sleep(1)  # 每支股票之间稍微停一下，减少被限流的概率

combined = pd.concat(all_rows, ignore_index=True)
combined = combined[["ticker", "name", "market", "date", "close"]]

print()
print("=== 合并后的数据预览 ===")
print(combined.head(10))
print(f"总共 {len(combined)} 行")

conn = sqlite3.connect("finance.db")
combined.to_sql("stock_prices", conn, if_exists="replace", index=False)
conn.close()

print()
print("✅ 已存入数据库的 stock_prices 表")
