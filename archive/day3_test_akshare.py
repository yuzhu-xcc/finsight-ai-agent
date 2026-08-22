import akshare as ak

# Test Hong Kong stock data
print("--- HK stock test ---")
hk_data = ak.stock_hk_hist(symbol="00700", period="daily", start_date="20260601", end_date="20260703", adjust="")
print(hk_data.head())

# Test US stock data
print("--- US stock test ---")
us_data = ak.stock_us_hist(symbol="AAPL", period="daily", start_date="20260601", end_date="20260703", adjust="")
print(us_data.head())
