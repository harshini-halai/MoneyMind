from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from backend.database import get_connection
from datetime import date


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


class Transaction(BaseModel):
    description: str
    category: Literal["Food", "Travel", "Shopping", "Bills", "Other"]
    amount: float = Field(gt=0)
    date: date
    type: Literal["income", "expense"]


@app.get("/")
def home():
    return FileResponse("frontend/templates/index.html")


@app.get("/add-income")
def add_income_page():
    return FileResponse("frontend/templates/add-income.html")


@app.get("/add-expense")
def add_expense_page():
    return FileResponse("frontend/templates/add-expense.html")

@app.get("/transactions-page")
def transactions_page():
    return FileResponse("frontend/templates/transactions.html")

@app.get("/add-savings")
def add_savings_page():
    return FileResponse("frontend/templates/add-savings.html")

@app.get("/add-emergency-fund")
def add_emergency_fund_page():
    return FileResponse("frontend/templates/add-emergency-fund.html")

@app.get("/add-budget")
def add_budget_page():
    return FileResponse("frontend/templates/add-budget.html")

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

class Saving(BaseModel):
    amount: float = Field(gt=0)
    description: str
    date: date

@app.post("/savings")
def create_saving(saving: Saving):
    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO savings (amount, description, date)
        VALUES (%s, %s, %s)
        """

        data = (
            saving.amount,
            saving.description,
            saving.date
        )

        cursor.execute(query, data)
        connection.commit()

        cursor.close()
        connection.close()

        return {"message": "Saving added successfully"}

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to add saving"
        )
class EmergencyFund(BaseModel):
    amount: float = Field(gt=0)
    description: str
    date: date

@app.post("/emergency-fund")
def create_emergency_fund(fund: EmergencyFund):
    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO emergency_fund (amount, description, date)
        VALUES (%s, %s, %s)
        """

        data = (
            fund.amount,
            fund.description,
            fund.date
        )

        cursor.execute(query, data)
        connection.commit()

        cursor.close()
        connection.close()

        return {"message": "Emergency fund added successfully"}

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to add emergency fund"
        )

@app.get("/savings")
def get_savings():
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id, amount, description, date
        FROM savings
        ORDER BY id DESC
        """

        cursor.execute(query)
        savings = cursor.fetchall()

        cursor.close()
        connection.close()

        return savings

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch savings"
        )
@app.get("/emergency-fund")
def get_emergency_fund():
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id, amount, description, date
        FROM emergency_fund
        ORDER BY id DESC
        """

        cursor.execute(query)
        funds = cursor.fetchall()

        cursor.close()
        connection.close()

        return funds

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch emergency fund"
        )

@app.get("/savings/total")
def get_total_savings():
    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        SELECT SUM(amount)
        FROM savings
        """

        cursor.execute(query)
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        total_savings = result[0] or 0

        return {
            "protected_savings": total_savings
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch total savings"
        )
    
@app.get("/emergency-fund/total")
def get_total_emergency_fund():
    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        SELECT SUM(amount)
        FROM emergency_fund
        """

        cursor.execute(query)
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        total_fund = result[0] or 0

        return {
            "emergency_fund": total_fund
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch total emergency fund"
        )

class UpcomingExpense(BaseModel):
    amount: float = Field(gt=0)
    description: str
    due_date: date   

@app.post("/upcoming-expenses")
def create_upcoming_expense(expense: UpcomingExpense):

    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO upcoming_expenses (amount, description, due_date)
        VALUES (%s, %s, %s)
        """

        data = (
            expense.amount,
            expense.description,
            expense.due_date
        )

        cursor.execute(query, data)
        connection.commit()

        cursor.close()
        connection.close()

        return {"message": "Upcoming expense added successfully"}

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to add upcoming expense"
        )

@app.get("/upcoming-expenses")
def get_upcoming_expenses():

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id, amount, description, due_date
        FROM upcoming_expenses
        ORDER BY due_date ASC
        """

        cursor.execute(query)

        expenses = cursor.fetchall()

        cursor.close()
        connection.close()

        return expenses

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch upcoming expenses"
        )  

@app.get("/upcoming-expenses/total")
def get_total_upcoming_expenses():

    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        SELECT SUM(amount)
        FROM upcoming_expenses
        """

        cursor.execute(query)

        result = cursor.fetchone()

        cursor.close()
        connection.close()

        total_upcoming_expenses = result[0] or 0

        return {
            "upcoming_expenses": total_upcoming_expenses
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch total upcoming expenses"
        )

@app.get("/safe-to-spend")
def get_safe_to_spend():

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END),
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END)
            FROM transactions
        """)

        transaction_result = cursor.fetchone()

        total_income = transaction_result[0] or 0
        total_expenses = transaction_result[1] or 0

        cursor.execute("""
            SELECT SUM(amount)
            FROM savings
        """)

        savings_result = cursor.fetchone()
        protected_savings = savings_result[0] or 0

        cursor.execute("""
            SELECT SUM(amount)
            FROM emergency_fund
        """)

        emergency_result = cursor.fetchone()
        emergency_fund = emergency_result[0] or 0

        cursor.execute("""
            SELECT SUM(amount)
            FROM upcoming_expenses
        """)

        upcoming_result = cursor.fetchone()
        upcoming_expenses = upcoming_result[0] or 0

        cursor.close()
        connection.close()

        available_balance = (
            total_income
            - total_expenses
            - protected_savings
            - emergency_fund
        )

        safe_to_spend = (
            available_balance
            - upcoming_expenses
        )

        return {
            "available_balance": available_balance,
            "upcoming_expenses": upcoming_expenses,
            "safe_to_spend": safe_to_spend
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to calculate safe-to-spend"
        )

class Budget(BaseModel):
    category: str
    amount: float = Field(gt=0)
    month: date

@app.post("/budgets")
def create_budget(budget: Budget):

    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO budgets (category, amount, month)
        VALUES (%s, %s, %s)
        """

        data = (
            budget.category,
            budget.amount,
            budget.month
        )

        cursor.execute(query, data)
        connection.commit()

        cursor.close()
        connection.close()

        return {"message": "Budget added successfully"}

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to add budget"
        )
@app.get("/budgets")
def get_budgets():

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id, category, amount, month
        FROM budgets
        ORDER BY month DESC
        """

        cursor.execute(query)

        budgets = cursor.fetchall()

        cursor.close()
        connection.close()

        return budgets

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch budgets"
        ) 

@app.get("/budgets/analysis")
def get_budget_analysis():

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            b.category,
            b.amount AS budget,
            COALESCE(SUM(t.amount), 0) AS spent
        FROM budgets b
        LEFT JOIN transactions t
            ON b.category = t.category
            AND t.type = 'expense'
            AND YEAR(t.date) = YEAR(b.month)
            AND MONTH(t.date) = MONTH(b.month)
        GROUP BY b.id, b.category, b.amount
        ORDER BY b.category
        """

        cursor.execute(query)

        budgets = cursor.fetchall()

        cursor.close()
        connection.close()

        for budget in budgets:
            budget["remaining"] = (
                float(budget["budget"])
                - float(budget["spent"])
            )

        return budgets

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to analyze budgets"
        )

@app.put("/transactions/{transaction_id}")
def update_transaction(transaction_id: int, transaction: Transaction):

    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        UPDATE transactions
        SET description = %s,
            category = %s,
            amount = %s,
            date = %s,
            type = %s
        WHERE id = %s
        """

        data = (
            transaction.description,
            transaction.category,
            transaction.amount,
            transaction.date,
            transaction.type,
            transaction_id
        )

        cursor.execute(query, data)
        connection.commit()

        if cursor.rowcount == 0:
            cursor.close()
            connection.close()
            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )

        cursor.close()
        connection.close()

        return {
            "message": "Transaction updated successfully"
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to update transaction"
        )


@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int):

    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        DELETE FROM transactions
        WHERE id = %s
        """

        cursor.execute(query, (transaction_id,))
        connection.commit()

        if cursor.rowcount == 0:
            cursor.close()
            connection.close()
            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )

        cursor.close()
        connection.close()

        return {
            "message": "Transaction deleted successfully"
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to delete transaction"
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

        total_income = result[0] or 0
        total_expenses = result[1] or 0

        cursor.execute("""
            SELECT SUM(amount)
            FROM savings
        """)

        savings_result = cursor.fetchone()
        protected_savings = savings_result[0] or 0

        cursor.execute("""
            SELECT SUM(amount)
            FROM emergency_fund
        """)

        emergency_result = cursor.fetchone()
        emergency_fund = emergency_result[0] or 0

        cursor.close()
        connection.close()

        balance = (
            total_income
            - total_expenses
            - protected_savings
            - emergency_fund
        )

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "protected_savings": protected_savings,
            "emergency_fund": emergency_fund,
            "balance": balance
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