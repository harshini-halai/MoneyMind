from typing import Literal
from datetime import date

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.database import get_connection
from backend.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


# -------------------- DATABASE HELPERS --------------------

def fetch_all(query, params=()):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def fetch_one(query, params=()):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def execute_write(query, params=()):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        return cursor.rowcount, cursor.lastrowid
    except Exception:
        if connection and connection.is_connected():
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# -------------------- MODELS --------------------

class Transaction(BaseModel):
    description: str
    category: Literal["Food", "Travel", "Shopping", "Bills", "Other"]
    amount: float = Field(gt=0)
    date: date
    type: Literal["income", "expense"]


class Saving(BaseModel):
    amount: float = Field(gt=0)
    description: str
    date: date


class EmergencyFund(BaseModel):
    amount: float = Field(gt=0)
    description: str
    date: date


class UpcomingExpense(BaseModel):
    amount: float = Field(gt=0)
    description: str
    due_date: date


class Budget(BaseModel):
    category: str
    amount: float = Field(gt=0)
    month: date


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


# -------------------- FRONTEND PAGES --------------------

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


# -------------------- TRANSACTIONS --------------------

@app.post("/transactions")
def create_transaction(
    transaction: Transaction,
    user_id: int = Depends(get_current_user),
):
    try:
        execute_write(
            """
            INSERT INTO transactions
            (description, category, amount, date, type, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                transaction.description,
                transaction.category,
                transaction.amount,
                transaction.date,
                transaction.type,
                user_id,
            ),
        )
        return {"message": "Transaction added successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to add transaction")


@app.get("/transactions")
def get_transactions(user_id: int = Depends(get_current_user)):
    try:
        return fetch_all(
            """
            SELECT id, description, category, amount, date, type
            FROM transactions
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (user_id,),
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch transactions")


@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction: Transaction,
    user_id: int = Depends(get_current_user),
):
    try:
        rowcount, _ = execute_write(
            """
            UPDATE transactions
            SET description = %s, category = %s, amount = %s,
                date = %s, type = %s
            WHERE id = %s AND user_id = %s
            """,
            (
                transaction.description,
                transaction.category,
                transaction.amount,
                transaction.date,
                transaction.type,
                transaction_id,
                user_id,
            ),
        )

        if rowcount == 0:
            exists = fetch_one(
                "SELECT id FROM transactions WHERE id = %s AND user_id = %s",
                (transaction_id, user_id),
            )
            if not exists:
                raise HTTPException(status_code=404, detail="Transaction not found")

        return {"message": "Transaction updated successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to update transaction")


@app.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user),
):
    try:
        rowcount, _ = execute_write(
            "DELETE FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id),
        )
        if rowcount == 0:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {"message": "Transaction deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to delete transaction")


# -------------------- PROTECTED SAVINGS --------------------

@app.post("/savings")
def create_saving(
    saving: Saving,
    user_id: int = Depends(get_current_user),
):
    try:
        execute_write(
            """
            INSERT INTO savings (amount, description, date, user_id)
            VALUES (%s, %s, %s, %s)
            """,
            (saving.amount, saving.description, saving.date, user_id),
        )
        return {"message": "Saving added successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to add saving")


@app.get("/savings")
def get_savings(user_id: int = Depends(get_current_user)):
    try:
        return fetch_all(
            """
            SELECT id, amount, description, date
            FROM savings
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (user_id,),
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch savings")


# -------------------- EMERGENCY FUND --------------------

@app.post("/emergency-fund")
def create_emergency_fund(
    fund: EmergencyFund,
    user_id: int = Depends(get_current_user),
):
    try:
        execute_write(
            """
            INSERT INTO emergency_fund (amount, description, date, user_id)
            VALUES (%s, %s, %s, %s)
            """,
            (fund.amount, fund.description, fund.date, user_id),
        )
        return {"message": "Emergency fund added successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to add emergency fund")


@app.get("/emergency-fund")
def get_emergency_fund(user_id: int = Depends(get_current_user)):
    try:
        return fetch_all(
            """
            SELECT id, amount, description, date
            FROM emergency_fund
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (user_id,),
        )
    except Exception:
        raise HTTPException(
            status_code=500, detail="Unable to fetch emergency fund"
        )


# -------------------- UPCOMING EXPENSES --------------------

@app.post("/upcoming-expenses")
def create_upcoming_expense(
    expense: UpcomingExpense,
    user_id: int = Depends(get_current_user),
):
    try:
        execute_write(
            """
            INSERT INTO upcoming_expenses
            (amount, description, due_date, user_id)
            VALUES (%s, %s, %s, %s)
            """,
            (expense.amount, expense.description, expense.due_date, user_id),
        )
        return {"message": "Upcoming expense added successfully"}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Unable to add upcoming expense"
        )


@app.get("/upcoming-expenses")
def get_upcoming_expenses(user_id: int = Depends(get_current_user)):
    try:
        return fetch_all(
            """
            SELECT id, amount, description, due_date
            FROM upcoming_expenses
            WHERE user_id = %s
            ORDER BY due_date ASC
            """,
            (user_id,),
        )
    except Exception:
        raise HTTPException(
            status_code=500, detail="Unable to fetch upcoming expenses"
        )


@app.get("/upcoming-expenses/total")
def get_total_upcoming_expenses(user_id: int = Depends(get_current_user)):
    try:
        result = fetch_one(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM upcoming_expenses
            WHERE user_id = %s
            """,
            (user_id,),
        )
        return {"upcoming_expenses": result["total"]}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Unable to fetch total upcoming expenses"
        )


# -------------------- BALANCE & SAFE TO SPEND --------------------

def calculate_finances(user_id: int):
    transactions = fetch_one(
        """
        SELECT
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0)
                AS total_income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0)
                AS total_expenses
        FROM transactions
        WHERE user_id = %s
        """,
        (user_id,),
    )

    savings = fetch_one(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM savings WHERE user_id = %s",
        (user_id,),
    )

    emergency = fetch_one(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM emergency_fund WHERE user_id = %s
        """,
        (user_id,),
    )

    upcoming = fetch_one(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM upcoming_expenses
        WHERE user_id = %s
          AND due_date BETWEEN CURRENT_DATE
          AND DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY)
        """,
        (user_id,),
    )

    income = float(transactions["total_income"])
    expenses = float(transactions["total_expenses"])
    protected_savings = float(savings["total"])
    emergency_fund = float(emergency["total"])
    upcoming_expenses = float(upcoming["total"])

    balance = income - expenses - protected_savings - emergency_fund

    return {
        "total_income": income,
        "total_expenses": expenses,
        "protected_savings": protected_savings,
        "emergency_fund": emergency_fund,
        "upcoming_expenses": upcoming_expenses,
        "balance": balance,
        "safe_to_spend": balance - upcoming_expenses,
    }


@app.get("/balance")
def get_balance(user_id: int = Depends(get_current_user)):
    try:
        result = calculate_finances(user_id)
        return {
            "total_income": result["total_income"],
            "total_expenses": result["total_expenses"],
            "protected_savings": result["protected_savings"],
            "emergency_fund": result["emergency_fund"],
            "balance": result["balance"],
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch balance")


@app.get("/safe-to-spend")
def get_safe_to_spend(user_id: int = Depends(get_current_user)):
    try:
        result = calculate_finances(user_id)
        return {
            "available_balance": result["balance"],
            "upcoming_expenses": result["upcoming_expenses"],
            "safe_to_spend": result["safe_to_spend"],
        }
    except Exception:
        raise HTTPException(
            status_code=500, detail="Unable to calculate safe-to-spend"
        )


# -------------------- BUDGETS --------------------

@app.post("/budgets")
def create_budget(
    budget: Budget,
    user_id: int = Depends(get_current_user),
):
    try:
        execute_write(
            """
            INSERT INTO budgets (category, amount, month, user_id)
            VALUES (%s, %s, %s, %s)
            """,
            (budget.category, budget.amount, budget.month, user_id),
        )
        return {"message": "Budget added successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to add budget")


@app.get("/budgets")
def get_budgets(user_id: int = Depends(get_current_user)):
    try:
        return fetch_all(
            """
            SELECT id, category, amount, month
            FROM budgets
            WHERE user_id = %s
            ORDER BY month DESC
            """,
            (user_id,),
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch budgets")


@app.get("/budgets/analysis")
def get_budget_analysis(user_id: int = Depends(get_current_user)):
    try:
        budgets = fetch_all(
            """
            SELECT
                b.category,
                b.amount AS budget,
                COALESCE(SUM(t.amount), 0) AS spent
            FROM budgets b
            LEFT JOIN transactions t
                ON b.category = t.category
                AND t.type = 'expense'
                AND t.user_id = b.user_id
                AND YEAR(t.date) = YEAR(b.month)
                AND MONTH(t.date) = MONTH(b.month)
            WHERE b.user_id = %s
            GROUP BY b.id, b.category, b.amount
            ORDER BY b.category
            """,
            (user_id,),
        )

        for budget in budgets:
            budget["budget"] = float(budget["budget"])
            budget["spent"] = float(budget["spent"])
            budget["remaining"] = budget["budget"] - budget["spent"]

        return budgets
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to analyze budgets")


# -------------------- CATEGORIES --------------------

@app.get("/categories")
def get_categories(user_id: int = Depends(get_current_user)):
    try:
        categories = fetch_all(
            """
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE type = 'expense' AND user_id = %s
            GROUP BY category
            """,
            (user_id,),
        )
        for category in categories:
            category["total"] = float(category["total"])
        return categories
    except Exception:
        raise HTTPException(
            status_code=500, detail="Unable to fetch category totals"
        )


# -------------------- KHATA SUMMARY --------------------

@app.get("/khata/summary")
def khata_summary(user_id: int = Depends(get_current_user)):
    try:
        result = calculate_finances(user_id)

        category_spending = fetch_all(
            """
            SELECT category, COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE type = 'expense' AND user_id = %s
            GROUP BY category
            ORDER BY total DESC
            """,
            (user_id,),
        )

        for category in category_spending:
            category["total"] = float(category["total"])

        return {
            "balance": result["balance"],
            "income": result["total_income"],
            "expenses": result["total_expenses"],
            "protected_savings": result["protected_savings"],
            "emergency_fund": result["emergency_fund"],
            "safe_to_spend": result["safe_to_spend"],
            "upcoming_expenses": result["upcoming_expenses"],
            "category_spending": category_spending,
        }
    except Exception:
        raise HTTPException(
            status_code=500, detail="Unable to fetch Khata summary"
        )


# -------------------- AUTHENTICATION --------------------

@app.post("/register")
def register_user(user: UserCreate):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        hashed_password = hash_password(user.password)

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (user.name, user.email, hashed_password),
        )
        connection.commit()
        return {"message": "User registered successfully"}

    except Exception:
        if connection and connection.is_connected():
            connection.rollback()
        raise HTTPException(
            status_code=400, detail="Unable to register user; check the email"
        )

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.post("/login")
def login_user(user: UserLogin):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, password_hash FROM users WHERE email = %s",
            (user.email,),
        )
        db_user = cursor.fetchone()

        if not db_user or not verify_password(
            user.password, db_user["password_hash"]
        ):
            raise HTTPException(
                status_code=401, detail="Invalid email or password"
            )

        token = create_access_token(db_user["id"])
        return {"access_token": token, "token_type": "bearer"}

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()