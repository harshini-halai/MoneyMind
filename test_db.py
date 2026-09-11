from database import get_connection


connection = get_connection()
cursor = connection.cursor()

query = """
INSERT INTO transactions
(description, category, amount, date, type)
VALUES (%s, %s, %s, %s, %s)
"""

data = ("Pizza", "Food", 250, "2026-09-10", "expense")

cursor.execute(query, data)

connection.commit()

print("Transaction added successfully")

cursor.close()
connection.close()