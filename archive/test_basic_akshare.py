import akshare as ak

print("Testing basic akshare connection...")
data = ak.stock_zh_a_spot_em()
print(data.head())
print("Test done.")
