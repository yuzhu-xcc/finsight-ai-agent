import sqlite3

conn = sqlite3.connect("finance.db")
cursor = conn.cursor()

cursor.execute("SELECT ticker, name, price FROM stocks")
results = cursor.fetchall()

print("Stock Return Analysis")
print("-------------------")

for row in results:
    ticker = row[0]
    name = row[1]
    current_price = row[2]
    buy_price = current_price * 0.9

    return_rate = (current_price - buy_price) / buy_price * 100

    print(name + " (" + ticker + "): return rate = " + str(round(return_rate, 2)) + "%")

conn.close()

