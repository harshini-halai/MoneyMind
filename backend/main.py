
from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel

from backend.expense import (
    add_expense,
    view_expenses,
    view_expenses_by_category,
    view_expenses_by_date,
    delete_transaction,
    update_transaction
)

from backend.analysis import (
    view_balance,
    category_totals,
    category_percentages
)

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

def add_income():

    # Income validation
    while True:

        try:
            amount = int(input("Enter income: "))

            if amount > 0:
                break
            else:
                print("Income should be positive")

        except ValueError:
            print("Please enter a valid number")

    transaction_date = datetime.now().strftime("%Y-%m-%d")

    # Save income to MySQL
    connection = get_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO transactions
    (description, category, amount, date, type)
    VALUES (%s, %s, %s, %s, %s)
    """

    data = (
        "Income",
        "Income",
        amount,
        transaction_date,
        "income"
    )

    cursor.execute(query, data)

    connection.commit()

    cursor.close()
    connection.close()

    print("Income added successfully")


def run_cli():

    while True:

        print("\n===== MoneyMind =====")
        print("1. Add Income")
        print("2. Add Expense")
        print("3. View Expenses")
        print("4. View Balance")
        print("5. Category Totals")
        print("6. View Expenses by Category")
        print("7. Category Spending Percentage")
        print("8. View Expenses by Date")
        print("9. Update Transaction")
        print("10. Delete Transaction")
        print("11. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_income()

        elif choice == "2":
            add_expense()

        elif choice == "3":
            view_expenses()

        elif choice == "4":
            view_balance()

        elif choice == "5":
            category_totals()

        elif choice == "6":
            view_expenses_by_category()

        elif choice == "7":
            category_percentages()

        elif choice == "8":
            view_expenses_by_date()

        elif choice == "9":
            update_transaction()

        elif choice == "10":
            delete_transaction()

        elif choice == "11":
            print("Thank you for using MoneyMind!")
            break

        else:
            print("Enter a valid choice")


if __name__ == "__main__":
    run_cli()

