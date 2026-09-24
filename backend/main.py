from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from backend.database import get_connection
from datetime import date

app = FastAPI()

class Transaction(BaseModel):
    description: str
    category: Literal["Food", "Travel", "Shopping", "Bills", "Other"]
    amount: float = Field(gt=0)
    date: date
    type: Literal["income", "expense"]

@app.get("/")
def home():
    return {"message": "MoneyMind API is running"}

@app.get("/transactions")
def get_transactions():

    try:
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

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch transactions"
        )

@app.post("/transactions")
def create_transaction(transaction: Transaction):

    try:
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

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to add transaction"
        )

@app.get("/balance")
def get_balance():

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END),
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END)
            FROM transactions
        """)

        result = cursor.fetchone()

        cursor.close()
        connection.close()

        total_income = result[0] or 0
        total_expenses = result[1] or 0

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": total_income - total_expenses
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch balance"
        )
    
@app.get("/categories")
def get_categories():

    try:
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

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch category totals"
        )



