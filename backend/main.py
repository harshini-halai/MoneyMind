import datetime as dt
import logging
import os
import re
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Annotated, Literal

import mysql.connector
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints, field_validator

from backend.database import get_connection
from backend.security import (
    create_access_token,
    fake_verify_password,
    get_current_user,
    hash_password,
    verify_password,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("moneymind")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

app = FastAPI(title="MoneyMind")

# The frontend is served by this same app, so CORS is not needed by default.
# Set ALLOWED_ORIGINS="https://example.com,https://app.example.com" only if
# you host the frontend somewhere else.
_allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
if _allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


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


def server_error(message: str) -> HTTPException:
    """Log the real exception (call inside `except`) and return a safe 500."""
    logger.exception(message)
    return HTTPException(status_code=500, detail=message)


# -------------------- MODELS --------------------

Category = Literal["Food", "Travel", "Shopping", "Bills", "Other"]
Money = Annotated[float, Field(gt=0, lt=10_000_000_000)]
Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Transaction(BaseModel):
    description: Text
    category: Category
    amount: Money
    date: dt.date
    type: Literal["income", "expense"]


class Saving(BaseModel):
    amount: Money
    description: Text
    date: dt.date


class EmergencyFund(BaseModel):
    amount: Money
    description: Text
    date: dt.date


class UpcomingExpense(BaseModel):
    amount: Money
    description: Text
    due_date: dt.date


class Budget(BaseModel):
    category: Category
    amount: Money
    month: dt.date


class UserCreate(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    email: Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
    password: Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Enter a valid email address")
        return value


class UserLogin(BaseModel):
    email: Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
    password: Annotated[str, Field(min_length=1, max_length=128)]


# -------------------- LOGIN RATE LIMIT (in-memory, single process) --------------------

MAX_LOGIN_FAILURES = 5
LOGIN_WINDOW_SECONDS = 15 * 60
_login_failures: dict[str, deque] = defaultdict(deque)


def _login_key(request: Request, email: str) -> str:
    client = request.client.host if request.client else "unknown"
    return f"{client}|{email}"


def _check_login_limit(key: str) -> None:
    now = time.time()
    attempts = _login_failures.get(key)
    if not attempts:
        return
    while attempts and now - attempts[0] > LOGIN_WINDOW_SECONDS:
        attempts.popleft()
    if not attempts:
        _login_failures.pop(key, None)
        return
    if len(attempts) >= MAX_LOGIN_FAILURES:
        raise HTTPException(
            status_code=429,
            detail="Too many failed attempts. Please try again in a few minutes.",
        )


def _record_login_failure(key: str) -> None:
    _login_failures[key].append(time.time())


# -------------------- FRONTEND PAGES --------------------

def page(name: str) -> FileResponse:
    return FileResponse(TEMPLATES_DIR / name)


@app.get("/")
def home():
    return page("index.html")


@app.get("/login")
def login_page():
    return page("login.html")


@app.get("/register")
def register_page():
    return page("register.html")


@app.get("/add-income")
def add_income_page():
    return page("add-income.html")


@app.get("/add-expense")
def add_expense_page():
    return page("add-expense.html")


@app.get("/transactions-page")
def transactions_page():
    return page("transactions.html")


@app.get("/add-savings")
def add_savings_page():
    return page("add-savings.html")


@app.get("/add-emergency-fund")
def add_emergency_fund_page():
    return page("add-emergency-fund.html")


@app.get("/add-budget")
def add_budget_page():
    return page("add-budget.html")


@app.get("/add-upcoming-expense")
def add_upcoming_expense_page():
    return page("add-upcoming-expense.html")


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
                round(transaction.amount, 2),
                transaction.date,
                transaction.type,
                user_id,
            ),
        )
        return {"message": "Transaction added successfully"}
    except Exception:
        raise server_error("Unable to add transaction")


@app.get("/transactions")
def get_transactions(user_id: int = Depends(get_current_user)):
    try:
        return fetch_all(
            """
            SELECT id, description, category, amount, date, type
            FROM transactions
            WHERE user_id = %s
            ORDER BY date DESC, id DESC
            """,
            (user_id,),
        )
    except Exception:
        raise server_error("Unable to fetch transactions")


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
                round(transaction.amount, 2),
                transaction.date,
                transaction.type,
                transaction_id,
                user_id,
            ),
        )

        # MySQL reports 0 changed rows when nothing actually changed, so
        # check that the row exists before calling it a 404.
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
        raise server_error("Unable to update transaction")


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
        raise server_error("Unable to delete transaction")


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
            (round(saving.amount, 2), saving.description, saving.date, user_id),
        )
        return {"message": "Saving added successfully"}
    except Exception:
        raise server_error("Unable to add saving")


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
        raise server_error("Unable to fetch savings")


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
            (round(fund.amount, 2), fund.description, fund.date, user_id),
        )
        return {"message": "Emergency fund added successfully"}
    except Exception:
        raise server_error("Unable to add emergency fund")


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
        raise server_error("Unable to fetch emergency fund")


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
            (round(expense.amount, 2), expense.description, expense.due_date, user_id),
        )
        return {"message": "Upcoming expense added successfully"}
    except Exception:
        raise server_error("Unable to add upcoming expense")


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
        raise server_error("Unable to fetch upcoming expenses")


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
        return {"upcoming_expenses": float(result["total"])}
    except Exception:
        raise server_error("Unable to fetch total upcoming expenses")


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

    # Only upcoming expenses due in the next 30 days reduce safe-to-spend.
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
        "total_income": round(income, 2),
        "total_expenses": round(expenses, 2),
        "protected_savings": round(protected_savings, 2),
        "emergency_fund": round(emergency_fund, 2),
        "upcoming_expenses": round(upcoming_expenses, 2),
        "balance": round(balance, 2),
        "safe_to_spend": round(balance - upcoming_expenses, 2),
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
        raise server_error("Unable to fetch balance")


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
        raise server_error("Unable to calculate safe-to-spend")


# -------------------- BUDGETS --------------------

@app.post("/budgets")
def create_budget(
    budget: Budget,
    user_id: int = Depends(get_current_user),
):
    try:
        month_start = budget.month.replace(day=1)

        existing = fetch_one(
            """
            SELECT id FROM budgets
            WHERE user_id = %s AND category = %s
              AND YEAR(month) = %s AND MONTH(month) = %s
            """,
            (user_id, budget.category, month_start.year, month_start.month),
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="A budget for this category and month already exists",
            )

        execute_write(
            """
            INSERT INTO budgets (category, amount, month, user_id)
            VALUES (%s, %s, %s, %s)
            """,
            (budget.category, round(budget.amount, 2), month_start, user_id),
        )
        return {"message": "Budget added successfully"}
    except HTTPException:
        raise
    except Exception:
        raise server_error("Unable to add budget")


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
        raise server_error("Unable to fetch budgets")


@app.get("/budgets/analysis")
def get_budget_analysis(user_id: int = Depends(get_current_user)):
    try:
        budgets = fetch_all(
            """
            SELECT
                b.id,
                b.category,
                b.month,
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
            GROUP BY b.id, b.category, b.month, b.amount
            ORDER BY b.month DESC, b.category
            """,
            (user_id,),
        )

        for item in budgets:
            item["budget"] = float(item["budget"])
            item["spent"] = float(item["spent"])
            item["remaining"] = round(item["budget"] - item["spent"], 2)
            item["percent_used"] = (
                round(item["spent"] / item["budget"] * 100, 1)
                if item["budget"] > 0
                else 0
            )

        return budgets
    except Exception:
        raise server_error("Unable to analyze budgets")


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
        raise server_error("Unable to fetch category totals")


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
        raise server_error("Unable to fetch Khata summary")


# -------------------- AUTHENTICATION --------------------

@app.post("/register")
def register_user(user: UserCreate):
    try:
        hashed_password = hash_password(user.password)
        execute_write(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (user.name, user.email, hashed_password),
        )
        return {"message": "User registered successfully"}
    except mysql.connector.IntegrityError:
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        )
    except Exception:
        raise server_error("Unable to register user")


@app.post("/login")
def login_user(user: UserLogin, request: Request):
    email = user.email.lower()
    key = _login_key(request, email)
    _check_login_limit(key)

    try:
        db_user = fetch_one(
            "SELECT id, password_hash FROM users WHERE email = %s",
            (email,),
        )
    except Exception:
        raise server_error("Unable to log in")

    if db_user:
        valid = verify_password(user.password, db_user["password_hash"])
    else:
        fake_verify_password(user.password)  # keep timing similar
        valid = False

    if not valid:
        _record_login_failure(key)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    _login_failures.pop(key, None)
    token = create_access_token(db_user["id"])
    return {"access_token": token, "token_type": "bearer"}