"""Khata: a small assistant that answers questions about the user's own money.

No AI service is called and no data leaves the server. Khata matches keywords
(English and Hinglish) to a topic, then builds the answer from a "snapshot" of
the user's numbers. main.py builds the snapshot from the database.

snapshot = {
    "finances": {total_income, total_expenses, protected_savings, emergency_fund,
                 upcoming_expenses, balance, safe_to_spend},
    "month":    {"spent": float, "last_spent": float,
                 "categories": [{"category", "total"}],   # this month, biggest first
                 "biggest": {"description", "amount", "date", "category"} or None},
    "budgets":  [{"category", "month": date, "budget", "spent", "remaining",
                  "percent_used"}],
    "goals":    [goal_progress(...) dicts],
    "upcoming": [{"description", "amount", "due_date": date}],   # next 30 days
}
"""

import calendar
import re
from datetime import date

SUGGESTED_QUESTIONS = [
    "What is my safe to spend?",
    "Where did my money go this month?",
    "How are my budgets doing?",
    "How are my goals going?",
    "Any tips to save more?",
]

CATEGORY_WORDS = {
    "food": "Food", "khana": "Food", "khane": "Food",
    "travel": "Travel", "shopping": "Shopping",
    "bills": "Bills", "bill": "Bills", "other": "Other",
}
SPEND_WORDS = re.compile(r"spen|kharch|expens|how much|kitna|kitne", re.I)

# Checked in order; the first match wins.
INTENTS = [
    ("safe_to_spend", r"safe.?to.?spend|can i spend|kharch kar (sakta|sakti)|kitna kharch kar"),
    ("compare_months", r"last month|previous month|pichle mahine|pichhle mahine|compare|vs last"),
    ("biggest_expense", r"biggest|largest|highest|sabse (bada|badi)|sabse zyada kharch"),
    ("categories", r"categor|where.*(money|spend|spent|go)|kahan.*(kharch|paisa|paise)|top spend|most spen|sabse (zyada|jyada)"),
    ("month_spending", r"(this month|is mahine|iss mahine|monthly).*(spen|kharch|expens)|(spen|kharch|expens).*(this month|is mahine|iss mahine)|how much.*spen"),
    ("budgets", r"budget"),
    ("goals", r"\bgoals?\b|dream"),
    ("upcoming", r"upcoming|\bdue\b|\bbills?\b|next payment|aane wale|aane wali"),
    ("savings", r"saving|bachat|emergency"),
    ("balance", r"balance|available|how much (money|do i have)|kitna (paisa|paise)|kitne paise|\bbacha\b"),
    ("tips", r"\btips?\b|advice|suggest|save more|improve|kaise (bachau|bachaun|bachat)|help me save"),
    ("greeting", r"^(hi+|hello|hey|namaste|namaskar|hola)\b"),
    ("help", r"\bhelp\b|what can you|kya kar sakte|madad"),
]


# ---------- helpers ----------

def inr(value) -> str:
    """Format as rupees with Indian grouping: 1234567.5 -> ₹12,34,567.50"""
    amount = round(float(value or 0), 2)
    sign = "-" if amount < 0 else ""
    whole, fraction = f"{abs(amount):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{sign}₹{whole}.{fraction}"

def _days(count: int) -> str:
    return f"{count} day" if count == 1 else f"{count} days"

def _days_left_in_month(today: date) -> int:
    return calendar.monthrange(today.year, today.month)[1] - today.day + 1


def _this_month_budgets(snapshot: dict, today: date) -> list:
    return [
        item for item in snapshot.get("budgets", [])
        if item["month"].year == today.year and item["month"].month == today.month
    ]


def _named_category(question: str):
    for word, category in CATEGORY_WORDS.items():
        if re.search(rf"\b{word}\b", question):
            return category
    return None


def _top_category_share(month: dict):
    """(category, total, percent_of_month_spending) or None."""
    categories = month.get("categories") or []
    spent = month.get("spent") or 0
    if not categories or spent <= 0:
        return None
    top = categories[0]
    return top["category"], top["total"], round(top["total"] / spent * 100)


# ---------- answers ----------

def _answer_balance(snapshot, today):
    f = snapshot["finances"]
    return (
        f"Your available balance is {inr(f['balance'])}: income {inr(f['total_income'])} "
        f"minus expenses {inr(f['total_expenses'])}, savings {inr(f['protected_savings'])} "
        f"and emergency fund {inr(f['emergency_fund'])}."
    )


def _answer_safe_to_spend(snapshot, today):
    f = snapshot["finances"]
    safe = f["safe_to_spend"]
    if safe < 0:
        return (
            f"Your Safe to Spend is {inr(safe)}, which is below zero. Bills due in the next "
            f"30 days ({inr(f['upcoming_expenses'])}) are more than your free balance "
            f"({inr(f['balance'])}). It is best to hold off on extra spending."
        )
    days = _days_left_in_month(today)
    text = (
        f"Your Safe to Spend is {inr(safe)}: your balance {inr(f['balance'])} minus "
        f"{inr(f['upcoming_expenses'])} of bills due in the next 30 days."
    )
    if safe > 0:
            text += f" Spread over the {_days(days)} left this month, that is about {inr(safe / days)} a day."
    return text


def _answer_month_spending(snapshot, today):
    month = snapshot["month"]
    if month["spent"] <= 0:
        return "You have not recorded any expenses this month yet."
    text = f"You have spent {inr(month['spent'])} this month so far."
    top = _top_category_share(month)
    if top:
        text += f" Most of it went to {top[0]} ({inr(top[1])}, {top[2]}%)."
    return text


def _answer_categories(snapshot, today):
    month = snapshot["month"]
    categories = month.get("categories") or []
    if not categories or month["spent"] <= 0:
        return "No expenses recorded this month yet, so there is no category breakdown."
    parts = [
        f"{c['category']} {inr(c['total'])} ({round(c['total'] / month['spent'] * 100)}%)"
        for c in categories[:3]
    ]
    return "This month your money went mostly to: " + ", ".join(parts) + "."


def _answer_category_detail(snapshot, today, category):
    month = snapshot["month"]
    total = next(
        (c["total"] for c in month.get("categories", []) if c["category"] == category), 0
    )
    if total <= 0:
        return f"You have not spent anything on {category} this month."
    share = round(total / month["spent"] * 100) if month["spent"] > 0 else 0
    return f"You have spent {inr(total)} on {category} this month, which is {share}% of your spending."


def _answer_compare_months(snapshot, today):
    month = snapshot["month"]
    spent, last = month["spent"], month["last_spent"]
    if last <= 0:
        return (
            f"I have no expenses recorded for last month to compare with. "
            f"This month you have spent {inr(spent)} so far."
        )
    diff = spent - last
    percent = round(abs(diff) / last * 100)
    direction = "more" if diff > 0 else "less"
    return (
        f"Last month you spent {inr(last)}. This month so far you have spent {inr(spent)}, "
        f"which is {inr(abs(diff))} ({percent}%) {direction} than all of last month."
    )


def _answer_biggest(snapshot, today):
    biggest = snapshot["month"].get("biggest")
    if not biggest:
        return "No expenses recorded this month yet."
    return (
        f"Your biggest expense this month is {biggest['description']}: "
        f"{inr(biggest['amount'])} ({biggest['category']}, {biggest['date']})."
    )


def _answer_budgets(snapshot, today):
    budgets = _this_month_budgets(snapshot, today)
    if not budgets:
        return "You have no budgets for this month. Add one from the dashboard to track a category."
    lines = []
    for b in budgets:
        note = ""
        if b["percent_used"] >= 100:
            note = " - over budget!"
        elif b["percent_used"] >= 80:
            note = " - close to the limit"
        lines.append(
            f"{b['category']}: {inr(b['spent'])} of {inr(b['budget'])} ({b['percent_used']}%){note}"
        )
    return "Your budgets this month: " + "; ".join(lines) + "."


def _answer_goals(snapshot, today):
    goals = snapshot.get("goals") or []
    if not goals:
        return "You have no savings goals yet. Create one to start saving towards something."
    lines = []
    for g in goals[:4]:
        line = f"{g['name']}: {inr(g['saved'])} of {inr(g['target_amount'])} ({g['percent']}%)"
        if g["status"] == "achieved":
            line += " - achieved!"
        elif g["status"] == "overdue":
            line += " - the target date has passed"
        elif g["monthly_needed"] is not None:
            line += f" - needs about {inr(g['monthly_needed'])} a month"
        lines.append(line)
    return "Your goals: " + "; ".join(lines) + "."


def _answer_upcoming(snapshot, today):
    upcoming = snapshot.get("upcoming") or []
    if not upcoming:
        return "You have no bills or payments due in the next 30 days."
    total = sum(item["amount"] for item in upcoming)
    items = ", ".join(
        f"{item['description']} {inr(item['amount'])} on {item['due_date'].strftime('%d %b')}"
        for item in upcoming[:5]
    )
    return f"Due in the next 30 days ({inr(total)} in total): {items}."


def _answer_savings(snapshot, today):
    f = snapshot["finances"]
    return (
        f"You have {inr(f['protected_savings'])} in protected savings and "
        f"{inr(f['emergency_fund'])} in your emergency fund."
    )


def _answer_tips(snapshot, today):
    tips = []
    month, f = snapshot["month"], snapshot["finances"]

    top = _top_category_share(month)
    budgets = _this_month_budgets(snapshot, today)
    if top and top[2] >= 40:
        if any(b["category"] == top[0] for b in budgets):
            tips.append(
                f"{top[0]} is {top[2]}% of this month's spending. It already has a budget, "
                f"so look at which purchases pushed it up."
            )
        else:
            tips.append(
                f"{top[0]} is {top[2]}% of this month's spending. Setting a budget for it "
                f"is the quickest way to bring it down."
            )
    if not budgets:
        tips.append("You have no budgets this month. Even one budget for your biggest category helps.")
    if month["last_spent"] > 0 and f["emergency_fund"] < month["last_spent"] * 3:
        tips.append(
            f"A common rule is an emergency fund of about 3 months of spending "
            f"(around {inr(month['last_spent'] * 3)}). You have {inr(f['emergency_fund'])}."
        )
    if not snapshot.get("goals"):
        tips.append("Pick one savings goal. Saving towards something specific is easier to stick to.")
    if not tips:
        tips.append("You are doing well. Keep recording every expense so Khata can spot changes early.")

    return " ".join(f"{i}. {tip}" for i, tip in enumerate(tips[:3], 1)) + (
        " (General tips from your own numbers, not financial advice.)"
    )


def _answer_greeting(snapshot, today):
    return (
        "Hi, I am Khata. I can tell you your balance, what is safe to spend, where your money "
        "went, how your budgets and goals are doing, and give saving tips. What would you like to know?"
    )


def _answer_help(snapshot, today):
    return (
        "Ask me things like: What is my safe to spend? Where did my money go this month? "
        "How much did I spend on Food? How are my budgets and goals doing? Any bills coming up? "
        "Any tips to save more? You can also ask in Hinglish, for example 'is mahine kitna kharch hua'."
    )


ANSWERS = {
    "safe_to_spend": _answer_safe_to_spend,
    "compare_months": _answer_compare_months,
    "biggest_expense": _answer_biggest,
    "categories": _answer_categories,
    "month_spending": _answer_month_spending,
    "budgets": _answer_budgets,
    "goals": _answer_goals,
    "upcoming": _answer_upcoming,
    "savings": _answer_savings,
    "balance": _answer_balance,
    "tips": _answer_tips,
    "greeting": _answer_greeting,
    "help": _answer_help,
}


def detect_intent(question: str) -> str:
    text = re.sub(r"\s+", " ", (question or "").lower()).strip()
    for intent, pattern in INTENTS:
        if re.search(pattern, text):
            return intent
    return "unknown"


def answer_question(question: str, snapshot: dict, today: date) -> dict:
    text = re.sub(r"\s+", " ", (question or "").lower()).strip()[:300]

    # "How much did I spend on food?" -> a category-specific answer
    named = _named_category(text)
    if named and SPEND_WORDS.search(text) and "budget" not in text:
        return {
            "intent": "category_detail",
            "answer": _answer_category_detail(snapshot, today, named),
            "suggestions": SUGGESTED_QUESTIONS,
        }

    intent = detect_intent(text)
    if intent == "unknown":
        return {
            "intent": "unknown",
            "answer": "I am not sure I understood that. " + _answer_help(snapshot, today),
            "suggestions": SUGGESTED_QUESTIONS,
        }

    return {
        "intent": intent,
        "answer": ANSWERS[intent](snapshot, today),
        "suggestions": SUGGESTED_QUESTIONS,
    }


# ---------- dashboard insights ----------

def build_insights(snapshot: dict, today: date) -> list:
    """Short, proactive messages for the dashboard. Warnings come first."""
    f, month = snapshot["finances"], snapshot["month"]
    has_any_data = (
        f["total_income"] > 0 or f["total_expenses"] > 0 or f["protected_savings"] > 0
    )
    if not has_any_data:
        return [{
            "level": "info",
            "text": "Add your first income and expenses and Khata will start giving you insights.",
        }]

    insights = []

    safe = f["safe_to_spend"]
    if safe < 0:
        insights.append({
            "level": "warn",
            "text": f"Your Safe to Spend is {inr(safe)}, about {inr(safe / days)} a day for the {_days(days)} left this month.",
        })
    elif safe > 0:
        days = _days_left_in_month(today)
        insights.append({
            "level": "good",
            "text": f"Your Safe to Spend is {inr(safe)}, about {inr(safe / days)} a day for the {days} days left this month.",
        })

    # Monthly pace vs last month (skipped in the first days of a month: too noisy)
    if today.day >= 5 and month["last_spent"] > 0 and month["spent"] > 0:
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        projected = month["spent"] / today.day * days_in_month
        change = round((projected - month["last_spent"]) / month["last_spent"] * 100)
        if change >= 10:
            insights.append({
                "level": "warn",
                "text": f"At this pace you will spend about {inr(projected)} this month, {change}% more than last month ({inr(month['last_spent'])}).",
            })
        elif change <= -10:
            insights.append({
                "level": "good",
                "text": f"At this pace you will spend about {inr(projected)} this month, {abs(change)}% less than last month.",
            })

    top = _top_category_share(month)
    if top and top[2] >= 35:
        insights.append({
            "level": "info",
            "text": f"{top[0]} is your biggest expense this month: {inr(top[1])} ({top[2]}% of spending).",
        })

    for budget in _this_month_budgets(snapshot, today):
        if budget["percent_used"] >= 100:
            insights.append({
                "level": "warn",
                "text": f"You are over your {budget['category']} budget: {inr(budget['spent'])} of {inr(budget['budget'])}.",
            })
        elif budget["percent_used"] >= 80:
            insights.append({
                "level": "warn",
                "text": f"Your {budget['category']} budget is {budget['percent_used']}% used ({inr(budget['remaining'])} left).",
            })

    active = [g for g in snapshot.get("goals", []) if g["status"] == "active"]
    if active:
        nearest = min(active, key=lambda g: g["days_left"])
        insights.append({
            "level": "info",
            "text": f"To reach '{nearest['name']}' by {nearest['target_date']}, save about {inr(nearest['monthly_needed'])} a month.",
        })

    soon = [
        item for item in snapshot.get("upcoming", [])
        if 0 <= (item["due_date"] - today).days <= 7
    ]
    if soon:
        total = sum(item["amount"] for item in soon)
        insights.append({
            "level": "warn",
            "text": f"{len(soon)} payment(s) worth {inr(total)} are due in the next 7 days.",
        })

    order = {"warn": 0, "good": 1, "info": 2}
    insights.sort(key=lambda item: order[item["level"]])
    return insights[:5]