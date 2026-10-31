"""Run from the project root:  python -m tests.test_khata"""

from datetime import date

from backend.goals import goal_progress
from backend.khata import (
    answer_question,
    build_insights,
    detect_intent,
    inr,
)

TODAY = date(2026, 10, 20)  # 12 days left in October (20th to 31st)


def make_snapshot(**overrides):
    snapshot = {
        "finances": {
            "total_income": 25000.0, "total_expenses": 1120.0,
            "protected_savings": 4500.0, "emergency_fund": 1000.0,
            "upcoming_expenses": 6700.0, "balance": 18380.0, "safe_to_spend": 11680.0,
        },
        "month": {
            "spent": 1120.0, "last_spent": 800.0,
            "categories": [
                {"category": "Travel", "total": 500.0},
                {"category": "Other", "total": 480.0},
                {"category": "Food", "total": 140.0},
            ],
            "biggest": {"description": "Uber", "amount": 500.0, "date": "2026-10-12", "category": "Travel"},
        },
        "budgets": [
            {"category": "Food", "month": date(2026, 10, 1), "budget": 3000.0,
             "spent": 140.0, "remaining": 2860.0, "percent_used": 4.7},
            {"category": "Travel", "month": date(2026, 10, 1), "budget": 550.0,
             "spent": 500.0, "remaining": 50.0, "percent_used": 90.9},
            {"category": "Bills", "month": date(2026, 9, 1), "budget": 100.0,
             "spent": 200.0, "remaining": -100.0, "percent_used": 200.0},
        ],
        "goals": [goal_progress(1, "Laptop", 60000, 12000, date(2027, 4, 29), TODAY)],
        "upcoming": [
            {"description": "Rent", "amount": 6000.0, "due_date": date(2026, 10, 25)},
            {"description": "Netflix", "amount": 700.0, "due_date": date(2026, 11, 15)},
        ],
    }
    snapshot.update(overrides)
    return snapshot


def ask(question, snapshot=None):
    return answer_question(question, snapshot or make_snapshot(), TODAY)


def test_inr_uses_indian_grouping():
    assert inr(18380) == "₹18,380.00"
    assert inr(1234567.5) == "₹12,34,567.50"
    assert inr(0) == "₹0.00"
    assert inr(-500) == "-₹500.00"
    assert inr(999.999) == "₹1,000.00"
    assert inr(None) == "₹0.00"


def test_intents_in_english_and_hinglish():
    cases = {
        "What is my safe to spend?": "safe_to_spend",
        "Where did my money go this month?": "categories",
        "How are my budgets doing?": "budgets",
        "how are my goals going": "goals",
        "any bills coming up?": "upcoming",
        "Any tips to save more?": "tips",
        "what is my balance": "balance",
        "mera balance kitna hai": "balance",
        "is mahine kitna kharch hua": "month_spending",
        "pichle mahine se compare karo": "compare_months",
        "my biggest expense": "biggest_expense",
        "hello": "greeting",
        "help": "help",
        "asdf qwerty": "unknown",
    }
    for question, expected in cases.items():
        assert detect_intent(question) == expected, (question, detect_intent(question))


def test_safe_to_spend_answer_has_per_day_figure():
    answer = ask("safe to spend?")["answer"]
    assert "₹11,680.00" in answer and "a day" in answer


def test_negative_safe_to_spend_warns():
    snapshot = make_snapshot()
    snapshot["finances"] = dict(snapshot["finances"], safe_to_spend=-500.0, balance=6200.0)
    assert "below zero" in ask("safe to spend", snapshot)["answer"]


def test_category_detail():
    result = ask("How much did I spend on food?")
    assert result["intent"] == "category_detail"
    assert "₹140.00" in result["answer"] and "Food" in result["answer"]
    assert "not spent anything on Bills" in ask("kitna kharch bills pe hua")["answer"]


def test_budget_question_about_a_category_still_goes_to_budgets():
    assert ask("what is my food budget")["intent"] == "budgets"


def test_budgets_only_show_this_month_and_flag_limits():
    answer = ask("budgets")["answer"]
    assert "Food" in answer and "Travel" in answer
    assert "close to the limit" in answer
    assert "Bills" not in answer  # September budget


def test_compare_and_biggest():
    assert "more than all of last month" in ask("compare with last month")["answer"]
    assert "Uber" in ask("biggest expense")["answer"]


def test_new_user_gets_friendly_answers_not_errors():
    empty = make_snapshot(
        finances={k: 0.0 for k in make_snapshot()["finances"]},
        month={"spent": 0.0, "last_spent": 0.0, "categories": [], "biggest": None},
        budgets=[], goals=[], upcoming=[],
    )
    for question in ["balance", "categories", "budgets", "goals", "bills due", "tips",
                     "biggest expense", "compare last month", "safe to spend"]:
        answer = ask(question, empty)["answer"]
        assert isinstance(answer, str) and answer
    assert "first income" in build_insights(empty, TODAY)[0]["text"]


def test_unknown_question_lists_what_khata_can_do():
    result = ask("what is the capital of france")
    assert result["intent"] == "unknown" and "Ask me things like" in result["answer"]
    assert len(result["suggestions"]) == 5


def test_insights_warn_first_and_are_limited():
    insights = build_insights(make_snapshot(), TODAY)
    assert 1 <= len(insights) <= 5
    levels = [item["level"] for item in insights]
    assert levels == sorted(levels, key=lambda level: {"warn": 0, "good": 1, "info": 2}[level])
    text = " ".join(item["text"] for item in insights)
    assert "Travel budget is 90.9% used" in text
    assert "due in the next 7 days" in text  # Rent on the 25th


def test_insights_skip_pace_early_in_month():
    early = build_insights(make_snapshot(), date(2026, 10, 3))
    assert not any("At this pace" in item["text"] for item in early)


def test_tip_does_not_suggest_a_budget_that_already_exists():
    answer = ask("any tips")["answer"]  # Travel is 45% and already has a budget
    assert "It already has a budget" in answer
    no_budget = make_snapshot(budgets=[])
    assert "Setting a budget for it" in ask("any tips", no_budget)["answer"]


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} khata tests passed")