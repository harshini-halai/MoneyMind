"""Dream Goals: progress maths for a savings goal.

Pure functions only (no database), so they are easy to test.
Money put towards a goal is saved in the `savings` table with a goal_id, so the
dashboard balance logic does not change.
"""

from datetime import date

DAYS_PER_MONTH = 30.44


def goal_progress(
    goal_id: int,
    name: str,
    target_amount,
    saved,
    target_date,
    today: date,
) -> dict:
    target = float(target_amount or 0)
    saved = float(saved or 0)

    percent = round(min(saved / target * 100, 100.0), 1) if target > 0 else 0.0
    remaining = round(max(target - saved, 0.0), 2)
    achieved = target > 0 and saved >= target

    days_left = (target_date - today).days if target_date else None
    monthly_needed = None

    if achieved:
        status = "achieved"
    elif target_date is None:
        status = "no_deadline"
    elif days_left < 0:
        status = "overdue"
    else:
        status = "active"
        # If less than a month is left, the whole remainder is needed this month.
        months_left = max(days_left / DAYS_PER_MONTH, 1.0)
        monthly_needed = round(remaining / months_left, 2)

    return {
        "id": goal_id,
        "name": name,
        "target_amount": round(target, 2),
        "saved": round(saved, 2),
        "percent": percent,
        "remaining": remaining,
        "target_date": target_date.isoformat() if target_date else None,
        "days_left": days_left,
        "monthly_needed": monthly_needed,
        "status": status,
    }