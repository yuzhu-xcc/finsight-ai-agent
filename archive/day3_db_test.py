import sqlite3

conn = sqlite3.connect("finance.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM stocks")
results = cursor.fetchall()

for row in results:
    print(row)

conn.close()

