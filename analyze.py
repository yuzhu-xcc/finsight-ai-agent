"""
Week 2 / Day 8-9：pandas数据分析
目标：把 stock_prices 表里"每天的价格"，变成有意义的分析指标——
每日涨跌了多少、整体涨跌了多少、波动大不大。
"""
import sqlite3

import pandas as pd

conn = sqlite3.connect("finance.db")
df = pd.read_sql_query("SELECT * FROM stock_prices", conn)
conn.close()

# 把date列从文字转成pandas认识的"日期"类型，之后排序、计算才不会出错
df["date"] = pd.to_datetime(df["date"])

# 按股票代码、再按日期从早到晚排序——计算"涨跌"必须保证顺序是对的
df = df.sort_values(["ticker", "date"])

# --- 计算每日收益率 ---
# groupby("ticker") 的意思是："把数据按ticker分成5组（5支股票各一组），
#                              下面的计算在每一组内部分别进行，不会把不同股票的数据混在一起算"
# pct_change() 是pandas自带的函数，算的是"这一行比上一行变化了百分之多少"
#              第一天因为没有"前一天"可比，会是空值(NaN)，这是正常的
df["daily_return_pct"] = df.groupby("ticker")["close"].pct_change() * 100

# --- 计算5日移动平均线 ---
# rolling(window=5) 的意思是："看最近5天的一个滑动窗口"
# .mean() 对这个窗口取平均值
# 移动平均线的作用：股价每天上下跳动，直接看很难看出趋势，
#                   取几天的平均能把这种"噪音"抹平，更容易看出是涨是跌
df["ma5"] = df.groupby("ticker")["close"].transform(
    lambda x: x.rolling(window=5).mean()
)

print("=== 明细数据预览（含每日收益率、5日均线）===")
print(df.head(10))

# --- 按股票汇总：整个区间表现如何 ---
# agg() 的意思是"对每一组，同时做好几种统计"
# first/last 拿到区间的第一天、最后一天价格；std 是标准差，用来衡量波动率
summary = df.groupby(["ticker", "name", "market"]).agg(
    start_price=("close", "first"),
    end_price=("close", "last"),
    volatility=("daily_return_pct", "std"),
).reset_index()

# 整体收益率 = (期末价格 - 期初价格) / 期初价格 * 100
summary["total_return_pct"] = (
    (summary["end_price"] - summary["start_price"]) / summary["start_price"] * 100
)

print()
print("=== 股票汇总分析（这段时间整体涨跌了多少、波动率多大）===")
print(summary[["ticker", "name", "market", "start_price", "end_price",
                "total_return_pct", "volatility"]].to_string(index=False))
