import sqlite3

connection = sqlite3.connect('pos_system.db')

cursor = connection.execute("SELECT name from garments")

for row in cursor:
    print(row)