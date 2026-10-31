import datetime as dt
import io
import logging
import os
import re
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Annotated, Literal

import mysql.connector
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints, field_validator

from backend.categorizer import merchant_keys
from backend.categorizer import suggest as suggest_category
from backend.database import get_connection
from backend.goals import goal_progress
from backend.khata import SUGGESTED_QUESTIONS, answer_question, build_insights
from backend.transaction_parser import parse_transactions
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


def execute_many(query, rows):
    """Run one INSERT for many rows inside a single transaction."""
    connection = None
    cursor = None
    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor()
        cursor.executemany(query, rows)
        connection.commit()
        return cursor.rowcount
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


# -------------------- CATEGORY LEARNING --------------------

LEARN_SQL = """
    INSERT INTO category_memory (user_id, merchant_key, category, times_confirmed)
    VALUES (%s, %s, %s, 1)
    ON DUPLICATE KEY UPDATE
        times_confirmed = IF(category = VALUES(category), times_confirmed + 1, 1),
        category = VALUES(category)
"""


def load_memory(user_id: int, keys=None) -> dict:
    """What this user has taught us: {merchant_key: (category, times_confirmed)}.

    Pass `keys` to load only those keys, or leave it out to load everything.
    """
    if keys is not None:
        if not keys:
            return {}
        placeholders = ", ".join(["%s"] * len(keys))
        rows = fetch_all(
            "SELECT merchant_key, category, times_confirmed FROM category_memory "
            f"WHERE user_id = %s AND merchant_key IN ({placeholders})",
            (user_id, *keys),
        )
    else:
        rows = fetch_all(
            "SELECT merchant_key, category, times_confirmed FROM category_memory "
            "WHERE user_id = %s",
            (user_id,),
        )
    return {
        row["merchant_key"]: (row["category"], row["times_confirmed"])
        for row in rows
    }


def learn_category(user_id: int, description: str, category: str) -> None:
    """Remember that this user files this kind of expense under `category`.

    Best effort: a problem here must never stop the transaction from saving.
    """
    try:
        for key in merchant_keys(description):
            execute_write(LEARN_SQL, (user_id, key, category))
    except Exception:
        logger.exception("Could not save category learning; continuing")


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


class BulkTransactions(BaseModel):
    transactions: list[Transaction] = Field(min_length=1, max_length=100)


class Saving(BaseModel):
    amount: Money
    description: Text
    date: dt.date
    goal_id: int | None = None  # put this saving towards a goal


class Goal(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    target_amount: Money
    target_date: dt.date | None = None


class KhataQuestion(BaseModel):
    question: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)
    ]


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

# To add a page: create the HTML file in frontend/templates and add one line here.
PAGES = {
    "/": "index.html",
    "/login": "login.html",
    "/register": "register.html",
    "/add-income": "add-income.html",
    "/add-expense": "add-expense.html",
    "/transactions-page": "transactions.html",
    "/add-savings": "add-savings.html",
    "/add-emergency-fund": "add-emergency-fund.html",
    "/add-budget": "add-budget.html",
    "/add-upcoming-expense": "add-upcoming-expense.html",
    "/import-screenshot": "import-screenshot.html",
    "/goals-page": "goals.html",
    "/add-goal": "add-goal.html",
    "/khata": "khata.html",
}


def _register_page(path: str, filename: str) -> None:
    def serve():
        file_path = TEMPLATES_DIR / filename
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="Page not found")
        return FileResponse(file_path)

    app.add_api_route(path, serve, methods=["GET"], include_in_schema=False)


for _path, _filename in PAGES.items():
    _register_page(_path, _filename)


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
        if transaction.type == "expense":
            learn_category(user_id, transaction.description, transaction.category)
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

        if transaction.type == "expense":
            learn_category(user_id, transaction.description, transaction.category)
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


# -------------------- SCREENSHOT IMPORT --------------------

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


@app.post("/import/screenshot")
def import_screenshot(
    file: UploadFile = File(...),
    default_type: Literal["income", "expense"] = Form("expense"),
    user_id: int = Depends(get_current_user),
):
    """Read a payment-app screenshot and return DRAFT transactions.

    Nothing is saved here and the image is never written to disk: the user
    reviews the drafts and saves them with POST /transactions/bulk.
    """
    try:
        import pytesseract
        from PIL import Image

        from backend.transaction_ocr import extract_text_from_image
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Screenshot import is not set up on the server "
            "(install pytesseract and Pillow).",
        )

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Upload a PNG, JPG or WEBP image")

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large (max 5 MB)")

    try:
        image = Image.open(io.BytesIO(data))
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise HTTPException(status_code=413, detail="Image dimensions are too large")
        image.load()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="That file is not a valid image")

    try:
        text = extract_text_from_image(image)
    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Tesseract OCR is not installed, or TESSERACT_CMD in .env is wrong.",
        )
    except RuntimeError:  # pytesseract raises this when OCR times out
        raise HTTPException(
            status_code=504,
            detail="Reading the image took too long. Try a smaller or cropped screenshot.",
        )
    except Exception:
        raise server_error("Unable to read the screenshot")

    candidates = parse_transactions(text, default_type)

    # Prefer categories this user has chosen before over the built-in guesses.
    for candidate in candidates:
        candidate["category_source"] = "default"
    try:
        memory = load_memory(user_id)
        for candidate in candidates:
            if candidate["type"] == "expense":
                suggestion = suggest_category(candidate["description"], memory)
                candidate["category"] = suggestion["category"]
                candidate["category_source"] = suggestion["source"]
    except Exception:
        logger.exception("Category suggestions failed; using built-in guesses")

    # Flag rows that look like transactions you already saved.
    for candidate in candidates:
        candidate["possible_duplicate"] = False
    if candidates:
        try:
            dates = [candidate["date"] for candidate in candidates]
            existing = fetch_all(
                """
                SELECT date, amount, type FROM transactions
                WHERE user_id = %s AND date BETWEEN %s AND %s
                """,
                (user_id, min(dates), max(dates)),
            )
            seen = {
                (row["date"].isoformat(), round(float(row["amount"]), 2), row["type"])
                for row in existing
            }
            for candidate in candidates:
                key = (candidate["date"], round(candidate["amount"], 2), candidate["type"])
                candidate["possible_duplicate"] = key in seen
        except Exception:
            logger.exception("Duplicate check failed; continuing without it")

    return {"text": text, "transactions": candidates}


@app.post("/transactions/bulk")
def create_transactions_bulk(
    payload: BulkTransactions,
    user_id: int = Depends(get_current_user),
):
    try:
        rows = [
            (
                item.description,
                item.category,
                round(item.amount, 2),
                item.date,
                item.type,
                user_id,
            )
            for item in payload.transactions
        ]
        execute_many(
            """
            INSERT INTO transactions
            (description, category, amount, date, type, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            rows,
        )
        for item in payload.transactions:
            if item.type == "expense":
                learn_category(user_id, item.description, item.category)
        return {"message": f"{len(rows)} transactions added", "count": len(rows)}
    except Exception:
        raise server_error("Unable to add transactions")


# -------------------- PROTECTED SAVINGS --------------------

@app.post("/savings")
def create_saving(
    saving: Saving,
    user_id: int = Depends(get_current_user),
):
    try:
        if saving.goal_id is not None:
            goal = fetch_one(
                "SELECT id FROM goals WHERE id = %s AND user_id = %s",
                (saving.goal_id, user_id),
            )
            if not goal:
                raise HTTPException(status_code=404, detail="Goal not found")
            execute_write(
                """
                INSERT INTO savings (amount, description, date, user_id, goal_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    round(saving.amount, 2),
                    saving.description,
                    saving.date,
                    user_id,
                    saving.goal_id,
                ),
            )
        else:
            execute_write(
                """
                INSERT INTO savings (amount, description, date, user_id)
                VALUES (%s, %s, %s, %s)
                """,
                (round(saving.amount, 2), saving.description, saving.date, user_id),
            )
        return {"message": "Saving added successfully"}
    except HTTPException:
        raise
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


# -------------------- DREAM GOALS --------------------

def load_goals(user_id: int, today: dt.date) -> list:
    rows = fetch_all(
        """
        SELECT g.id, g.name, g.target_amount, g.target_date,
               COALESCE(SUM(s.amount), 0) AS saved
        FROM goals g
        LEFT JOIN savings s ON s.goal_id = g.id AND s.user_id = g.user_id
        WHERE g.user_id = %s
        GROUP BY g.id, g.name, g.target_amount, g.target_date
        ORDER BY g.id DESC
        """,
        (user_id,),
    )
    return [
        goal_progress(
            row["id"],
            row["name"],
            row["target_amount"],
            row["saved"],
            row["target_date"],
            today,
        )
        for row in rows
    ]


@app.post("/goals")
def create_goal(
    goal: Goal,
    user_id: int = Depends(get_current_user),
):
    try:
        if goal.target_date and goal.target_date < dt.date.today():
            raise HTTPException(
                status_code=400, detail="Target date must be today or later"
            )
        execute_write(
            """
            INSERT INTO goals (name, target_amount, target_date, user_id)
            VALUES (%s, %s, %s, %s)
            """,
            (goal.name, round(goal.target_amount, 2), goal.target_date, user_id),
        )
        return {"message": "Goal added successfully"}
    except HTTPException:
        raise
    except Exception:
        raise server_error("Unable to add goal")


@app.get("/goals")
def get_goals(user_id: int = Depends(get_current_user)):
    try:
        return load_goals(user_id, dt.date.today())
    except Exception:
        raise server_error("Unable to fetch goals")


@app.delete("/goals/{goal_id}")
def delete_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user),
):
    """Delete a goal. Money already saved towards it stays in your savings."""
    try:
        rowcount, _ = execute_write(
            "DELETE FROM goals WHERE id = %s AND user_id = %s",
            (goal_id, user_id),
        )
        if rowcount == 0:
            raise HTTPException(status_code=404, detail="Goal not found")
        return {"message": "Goal deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        raise server_error("Unable to delete goal")


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


def budget_analysis(user_id: int) -> list:
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


@app.get("/budgets/analysis")
def get_budget_analysis(user_id: int = Depends(get_current_user)):
    try:
        return budget_analysis(user_id)
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


@app.get("/categories/suggest")
def suggest_expense_category(
    description: str = Query(..., min_length=1, max_length=255),
    user_id: int = Depends(get_current_user),
):
    """Suggest a category for an expense description, using what you taught us."""
    try:
        memory = load_memory(user_id, merchant_keys(description))
        return suggest_category(description, memory)
    except Exception:
        raise server_error("Unable to suggest a category")


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


# -------------------- KHATA ASSISTANT --------------------

def build_snapshot(user_id: int, today: dt.date) -> dict:
    """Collect the numbers Khata answers questions from (see backend/khata.py)."""
    finances = calculate_finances(user_id)

    month_start = today.replace(day=1)
    next_month_start = (month_start + dt.timedelta(days=32)).replace(day=1)
    last_month_start = (month_start - dt.timedelta(days=1)).replace(day=1)

    def expenses_between(start, end) -> float:
        row = fetch_one(
            """
            SELECT COALESCE(SUM(amount), 0) AS total FROM transactions
            WHERE user_id = %s AND type = 'expense' AND date >= %s AND date < %s
            """,
            (user_id, start, end),
        )
        return float(row["total"])

    categories = fetch_all(
        """
        SELECT category, SUM(amount) AS total FROM transactions
        WHERE user_id = %s AND type = 'expense' AND date >= %s AND date < %s
        GROUP BY category ORDER BY total DESC
        """,
        (user_id, month_start, next_month_start),
    )
    for category in categories:
        category["total"] = float(category["total"])

    biggest = fetch_one(
        """
        SELECT description, amount, date, category FROM transactions
        WHERE user_id = %s AND type = 'expense' AND date >= %s AND date < %s
        ORDER BY amount DESC, id DESC LIMIT 1
        """,
        (user_id, month_start, next_month_start),
    )
    if biggest:
        biggest["amount"] = float(biggest["amount"])

    upcoming = fetch_all(
        """
        SELECT description, amount, due_date FROM upcoming_expenses
        WHERE user_id = %s AND due_date BETWEEN %s AND %s
        ORDER BY due_date ASC LIMIT 10
        """,
        (user_id, today, today + dt.timedelta(days=30)),
    )
    for item in upcoming:
        item["amount"] = float(item["amount"])

    # Goals need the goals table; Khata should still work if it is missing.
    try:
        goals = load_goals(user_id, today)
    except Exception:
        logger.exception("Could not load goals for Khata; continuing without them")
        goals = []

    return {
        "finances": finances,
        "month": {
            "spent": expenses_between(month_start, next_month_start),
            "last_spent": expenses_between(last_month_start, month_start),
            "categories": categories,
            "biggest": biggest,
        },
        "budgets": budget_analysis(user_id),
        "goals": goals,
        "upcoming": upcoming,
    }


@app.get("/khata/insights")
def khata_insights(user_id: int = Depends(get_current_user)):
    try:
        today = dt.date.today()
        snapshot = build_snapshot(user_id, today)
        return {
            "insights": build_insights(snapshot, today),
            "suggested_questions": SUGGESTED_QUESTIONS,
        }
    except Exception:
        raise server_error("Unable to load Khata insights")


@app.post("/khata/ask")
def khata_ask(
    payload: KhataQuestion,
    user_id: int = Depends(get_current_user),
):
    try:
        today = dt.date.today()
        snapshot = build_snapshot(user_id, today)
        return answer_question(payload.question, snapshot, today)
    except Exception:
        raise server_error("Unable to answer that right now")


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