import akshare as ak

print("Testing HK stock data...")
hk_data = ak.stock_hk_hist(symbol="00700", period="daily", start_date="20260601", end_date="20260703", adjust="")
print(hk_data.head())
print("HK test done.")
