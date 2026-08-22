name = "Ivy"
year = 2026
print("my name is " + name + ", this year is " + str(year) + " year")
stocks = ["AAPL", "0700.HK", "TSLA", "0005.HK", "NVDA"]

for stock in stocks:
    print(stock)
    tencent = {"name": "Tecent", "price": 380, "currency": "HKD"}

print(tencent["name"] + " current stock value is " + str(tencent["price"]) + " " + tencent["currency"])
buy_price = 100
sell_price = 120

if sell_price > buy_price:
    print("Profit")
else:
    print("Loss")
def calculate_return(buy_price, sell_price):
    profit_rate = (sell_price - buy_price) / buy_price * 100
    return profit_rate

result = calculate_return(100, 120)
print("The return rate is " + str(result) + "%")
e 

a