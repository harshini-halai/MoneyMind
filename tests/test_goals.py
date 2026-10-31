"""Run from the project root:  python -m tests.test_goals"""

from datetime import date

from backend.goals import goal_progress

TODAY = date(2026, 10, 29)


def test_active_goal_needs_monthly_amount():
    goal = goal_progress(1, "Laptop", 60000, 12000, date(2027, 4, 29), TODAY)
    assert goal["status"] == "active"
    assert goal["percent"] == 20.0
    assert goal["remaining"] == 48000.0
    assert goal["days_left"] == 182
    # about 5.98 months left -> roughly 8,000 a month
    assert 7900 <= goal["monthly_needed"] <= 8100


def test_less_than_a_month_left_needs_the_whole_remainder():
    goal = goal_progress(2, "Trip", 10000, 4000, date(2026, 11, 8), TODAY)
    assert goal["status"] == "active" and goal["monthly_needed"] == 6000.0


def test_achieved_goal():
    goal = goal_progress(3, "Phone", 20000, 25000, date(2027, 1, 1), TODAY)
    assert goal["status"] == "achieved"
    assert goal["percent"] == 100.0 and goal["remaining"] == 0.0
    assert goal["monthly_needed"] is None


def test_overdue_goal():
    goal = goal_progress(4, "Bike", 50000, 1000, date(2026, 9, 1), TODAY)
    assert goal["status"] == "overdue" and goal["monthly_needed"] is None


def test_goal_without_deadline():
    goal = goal_progress(5, "Someday", 5000, 0, None, TODAY)
    assert goal["status"] == "no_deadline"
    assert goal["target_date"] is None and goal["days_left"] is None


def test_zero_target_does_not_crash():
    assert goal_progress(6, "Zero", 0, 0, None, TODAY)["percent"] == 0.0


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} goal tests passed")