"""
上一步已经确认：网络、akshare库都没问题，只是 stock_hk_hist（东方财富接口）
这一个特定接口不稳定。这次换一个走新浪数据源的港股接口试试，同时测一下美股。
"""
import time

import akshare as ak

print("=== 测试1：港股备用接口 stock_hk_daily（新浪数据源，跟之前失败的是不同接口）===")
try:
    hk_data = ak.stock_hk_daily(symbol="00700", adjust="")
    print("✅ 成功！最近5行：")
    print(hk_data.tail())
except Exception as e:
    print("❌ 还是失败，报错信息：")
    print(repr(e))

print()
print("=== 测试2：美股接口 stock_us_hist ===")
try:
    us_data = ak.stock_us_hist(
        symbol="105.AAPL", period="daily",
        start_date="20260601", end_date="20260703", adjust=""
    )
    print("✅ 成功！前5行：")
    print(us_data.head())
except Exception as e:
    print("❌ 失败，报错信息：")
    print(repr(e))

print()
print("=== 测试3：把之前失败的 stock_hk_hist 再重试3次（判断是不是偶尔抽风，不是完全打不通）===")
for i in range(1, 4):
    try:
        hk_data2 = ak.stock_hk_hist(
            symbol="00700", period="daily",
            start_date="20260601", end_date="20260703", adjust=""
        )
        print(f"✅ 第{i}次重试成功！")
        print(hk_data2.head())
        break
    except Exception as e:
        print(f"❌ 第{i}次重试失败：{repr(e)}")
        time.sleep(3)

print()
print("=== 全部测试完成，把上面结果复制粘贴发给我 ===")
