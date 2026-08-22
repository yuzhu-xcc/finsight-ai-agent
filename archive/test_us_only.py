import akshare as ak

print("Testing US stock data...")
us_data = ak.stock_us_hist(symbol="AAPL", period="daily", start_date="20260601", end_date="20260703", adjust="")
print(us_data.head())
print("US test done.")
t.penup