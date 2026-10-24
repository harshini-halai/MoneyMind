import os
from io import BytesIO
from typing import Literal, List, Optional
from datetime import date

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image

from backend.database import get_connection
from backend.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from backend.transaction_ocr import extract_transactions_from_image


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
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        if connection and connection.is_connected():
            connection.close()


def fetch_one(query, params=()):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        if connection and connection.is_connected():
            connection.close()


def execute_write(query, params=()):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id
    finally:
        if connection and connection.is_connected():
            connection.close()


# -------------------- PYDANTIC MODELS --------------------

class User(BaseModel):
    name: Optional[str] = "User"
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

    def get_identifier(self) -> str:
        ident = self.email or self.username or ""
        if not ident:
            raise ValueError("email or username is required")
        if "@" not in ident:
            return f"{ident}@moneymind.local"
        return ident


class Transaction(BaseModel):
    description: str
    category: Literal["Food", "Travel", "Shopping", "Bills", "Other"]
    amount: float = Field(gt=0)
    date: date
    type: Literal["expense", "income"]


class SavingsGoal(BaseModel):
    goal_name: str
    target_amount: float = Field(gt=0)
    saved_amount: float = Field(ge=0)


class EmergencyFund(BaseModel):
    target_months: int = Field(gt=0)
    monthly_expense: float = Field(gt=0)
    current_amount: float = Field(ge=0)


class UpcomingExpense(BaseModel):
    title: str
    amount: float = Field(gt=0)
    due_date: date


class Budget(BaseModel):
    category: Literal["Food", "Travel", "Shopping", "Bills", "Other"]
    monthly_limit: float = Field(gt=0)


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


# -------------------- AUTHENTICATION --------------------

@app.post("/register")
def register(user: User):
    try:
        user_email = user.get_identifier()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    existing_user = fetch_one(
        "SELECT id FROM users WHERE email = %s",
        (user_email,),
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = hash_password(user.password)
    user_name = user.name if user.name != "User" else (user.username or user_email.split("@")[0])
    execute_write(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        (user_name, user_email, hashed_pw),
    )
    return {"message": "User registered successfully"}


@app.post("/login")
def login(user: User):
    try:
        user_email = user.get_identifier()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db_user = fetch_one(
        "SELECT id, password_hash FROM users WHERE email = %s",
        (user_email,),
    )
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": str(db_user["id"])})
    return {"access_token": token, "token_type": "bearer"}


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
                str(transaction.date),
                transaction.type,
                user_id,
            ),
        )
        return {"message": "Transaction added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transactions")
def get_transactions(user_id: int = Depends(get_current_user)):
    try:
        return fetch_all(
            "SELECT * FROM transactions WHERE user_id = %s ORDER BY date DESC",
            (user_id,),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction: Transaction,
    user_id: int = Depends(get_current_user),
):
    try:
        existing = fetch_one(
            "SELECT id FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id),
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Transaction not found")

        execute_write(
            """
            UPDATE transactions
            SET description = %s, category = %s, amount = %s, date = %s, type = %s
            WHERE id = %s AND user_id = %s
            """,
            (
                transaction.description,
                transaction.category,
                transaction.amount,
                str(transaction.date),
                transaction.type,
                transaction_id,
                user_id,
            ),
        )
        return {"message": "Transaction updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user),
):
    try:
        existing = fetch_one(
            "SELECT id FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id),
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Transaction not found")

        execute_write(
            "DELETE FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id),
        )
        return {"message": "Transaction deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- SCREENSHOT IMPORT --------------------

@app.post("/transactions/import-screenshot")
async def import_screenshot_preview(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="uploaded file is not an image")

    contents = await file.read()
    try:
        img = Image.open(BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid image format")

    extracted_items = extract_transactions_from_image(img)
    return {"transactions": extracted_items}


@app.post("/transactions/confirm-import")
def confirm_imported_transactions(
    items: List[Transaction],
    user_id: int = Depends(get_current_user),
):
    saved_count = 0
    for item in items:
        execute_write(
            """
            INSERT INTO transactions
            (description, category, amount, date, type, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                item.description,
                item.category,
                item.amount,
                str(item.date),
                item.type,
                user_id,
            ),
        )
        saved_count += 1

    return {"message": "transactions imported successfully", "count": saved_count}


# -------------------- SAVINGS --------------------

@app.post("/savings")
def create_savings_goal(
    goal: SavingsGoal,
    user_id: int = Depends(get_current_user),
):
    try:
        execute_write(
            """
            INSERT INTO savings_goals
            (goal_name, target_amount, saved_amount, user_id)
            VALUES (%s, %s, %s, %s)
            """,
            (goal.goal_name, goal.target_amount, goal.saved_amount, user_id),
        )
        return {"message": "Savings goal added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/savings")
def get_savings_goals(user_id: int = Depends(get_current_user)):
    try:
        return fetch_all(
            "SELECT * FROM savings_goals WHERE user_id = %s",
            (user_id,),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/savings/total")
def get_total_savings(user_id: int = Depends(get_current_user)):
    try:
        row = fetch_one(
            "SELECT COALESCE(SUM(saved_amount), 0) as total FROM savings_goals WHERE user_id = %s",
            (user_id,),
        )
        return {"total_savings": float(row["total"]) if row else 0.0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- EMERGENCY FUND --------------------

@app.post("/emergency-fund")
def set_emergency_fund(
    fund: EmergencyFund,
    user_id: int = Depends(get_current_user),
):
    try:
        execute_write(
            """
            INSERT INTO emergency_funds
            (target_months, monthly_expense, current_amount, user_id)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            target_months = VALUES(target_months),
            monthly_expense = VALUES(monthly_expense),
            current_amount = VALUES(current_amount)
            """,
            (fund.target_months, fund.monthly_expense, fund.current_amount, user_id),
        )
        return {"message": "Emergency fund updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/emergency-fund")
def get_emergency_fund(user_id: int = Depends(get_current_user)):
    try:
        fund = fetch_one(
            "SELECT * FROM emergency_funds WHERE user_id = %s",
            (user_id,),
        )
        return fund or {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/emergency-fund/total")
def get_total_emergency_fund(user_id: int = Depends(get_current_user)):
    try:
        row = fetch_one(
            "SELECT COALESCE(current_amount, 0) as total FROM emergency_funds WHERE user_id = %s",
            (user_id,),
        )
        return {"total_emergency_fund": float(row["total"]) if row else 0.0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- UPCOMING EXPENSES --------------------

@app.post("/upcoming-expenses")
def create_upcoming_expense(
    expense_item: UpcomingExpense,
    user_id: int = Depends(get_current_user),
):
    try:
        execute_write(
            """
            INSERT INTO upcoming_expenses
            (title, amount, due_date, user_id)
            VALUES (%s, %s, %s, %s)
            """,
            (expense_item.title, expense_item.amount, str(expense_item.due_date), user_id),
        )
        return {"message": "Upcoming expense added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/upcoming-expenses")
def get_upcoming_expenses(user_id: int = Depends(get_current_user)):
    try:
        return fetch_all(
            "SELECT * FROM upcoming_expenses WHERE user_id = %s ORDER BY due_date ASC",
            (user_id,),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/upcoming-expenses/total")
def get_total_upcoming_expenses(user_id: int = Depends(get_current_user)):
    try:
        row = fetch_one(
            "SELECT COALESCE(SUM(amount), 0) as total FROM upcoming_expenses WHERE user_id = %s",
            (user_id,),
        )
        return {"total_upcoming_expenses": float(row["total"]) if row else 0.0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- BALANCE & SAFE TO SPEND --------------------

@app.get("/balance")
def get_balance(user_id: int = Depends(get_current_user)):
    try:
        income_row = fetch_one(
            "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = %s AND type = 'income'",
            (user_id,),
        )
        expense_row = fetch_one(
            "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = %s AND type = 'expense'",
            (user_id,),
        )
        income = float(income_row["total"])
        expense_amt = float(expense_row["total"])
        return {
            "total_income": income,
            "total_expense": expense_amt,
            "balance": income - expense_amt,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/safe-to-spend")
def get_safe_to_spend(user_id: int = Depends(get_current_user)):
    try:
        balance_data = get_balance(user_id=user_id)
        current_balance = balance_data["balance"]

        upcoming_row = fetch_one(
            "SELECT COALESCE(SUM(amount), 0) as total FROM upcoming_expenses WHERE user_id = %s",
            (user_id,),
        )
        upcoming_total = float(upcoming_row["total"]) if upcoming_row else 0.0

        safe_amount = max(0.0, current_balance - upcoming_total)
        return {
            "current_balance": current_balance,
            "upcoming_commitments": upcoming_total,
            "safe_to_spend": safe_amount,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- BUDGETS --------------------

@app.post("/budgets")
def set_budget(
    budget: Budget,
    user_id: int = Depends(get_current_user),
):
    try:
        execute_write(
            """
            INSERT INTO budgets (category, monthly_limit, user_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE monthly_limit = VALUES(monthly_limit)
            """,
            (budget.category, budget.monthly_limit, user_id),
        )
        return {"message": "Budget set successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/budgets")
def get_budgets(user_id: int = Depends(get_current_user)):
    try:
        return fetch_all(
            "SELECT * FROM budgets WHERE user_id = %s",
            (user_id,),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/budgets/analysis")
def get_budget_analysis(user_id: int = Depends(get_current_user)):
    try:
        budgets = fetch_all(
            "SELECT * FROM budgets WHERE user_id = %s",
            (user_id,),
        )
        analysis_data = []
        for b in budgets:
            cat = b["category"]
            limit_val = float(b["monthly_limit"])
            spent_row = fetch_one(
                """
                SELECT COALESCE(SUM(amount), 0) as spent
                FROM transactions
                WHERE user_id = %s AND category = %s AND type = 'expense'
                """,
                (user_id, cat),
            )
            spent_val = float(spent_row["spent"])
            analysis_data.append({
                "category": cat,
                "monthly_limit": limit_val,
                "spent": spent_val,
                "remaining": limit_val - spent_val,
                "over_budget": spent_val > limit_val,
            })
        return analysis_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- CATEGORIES & KHATA SUMMARY --------------------

@app.get("/categories")
def get_categories():
    return {"categories": ["Food", "Travel", "Shopping", "Bills", "Other"]}


@app.get("/khata/summary")
def get_khata_summary(user_id: int = Depends(get_current_user)):
    try:
        balance_info = get_balance(user_id=user_id)
        budget_info = get_budget_analysis(user_id=user_id)
        return {
            "balance": balance_info,
            "budgets": budget_info,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))