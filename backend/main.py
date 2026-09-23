
from fastapi import FastAPI
from pydantic import BaseModel
from backend.database import get_connection


app = FastAPI()
class Transaction(BaseModel):
    description: str
    category: str
    amount: float
    date: str
    type: str

@app.get("/")
def home():
    return {"message": "MoneyMind API is running"}

@app.get("/transactions")
def get_transactions():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT id, description, category, amount, date, type
    FROM transactions
    ORDER BY id DESC
    """

    cursor.execute(query)

    transactions = cursor.fetchall()

    cursor.close()
    connection.close()

    return transactions

@app.post("/transactions")
def create_transaction(transaction: Transaction):

    connection = get_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO transactions
    (description, category, amount, date, type)
    VALUES (%s, %s, %s, %s, %s)
    """

    data = (
        transaction.description,
        transaction.category,
        transaction.amount,
        transaction.date,
        transaction.type
    )

    cursor.execute(query, data)
    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Transaction added successfully"
    }

@app.get("/balance")
def get_balance():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS total_income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS total_expenses
        FROM transactions
    """)

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    total_income = result[0] or 0
    total_expenses = result[1] or 0
    balance = total_income - total_expenses

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance
    }

@app.get("/categories")
def get_categories():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT category, SUM(amount) AS total
    FROM transactions
    WHERE type = 'expense'
    GROUP BY category
    """

    cursor.execute(query)

    categories = cursor.fetchall()

    cursor.close()
    connection.close()

    return categories



