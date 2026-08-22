import akshare as ak

print("=== 测试：美股新浪数据源接口 stock_us_daily ===")
try:
    us_data = ak.stock_us_daily(symbol="aapl", adjust="")
    print("✅ 成功！最近5行：")
    print(us_data.tail())
except Exception as e:
    print("❌ 失败，报错信息：")
    print(repr(e))
