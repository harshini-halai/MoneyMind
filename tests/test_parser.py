"""Run from the project root:  python -m tests.test_parser"""

from datetime import date

from backend.transaction_parser import parse_transactions

TODAY = date(2026, 10, 29)

# Real text read by Tesseract from a Paytm for Business screenshot.
PAYTM_TEXT = """10:31 etl 4G
Account Deactivated fi
%23,230 from 82 Payments, Today
at 10:28 PM RITIKM 2485
Bank Account
fi 10:23 PM SANDEEP K 7885
Bank Account
A 10:18 PM DEVASHISH S 230
Bank Account
A 10:17 PM DEEPU S %30
Bank Account
fi 10:14 PM VIVAAN S 220
Bank Account
Paytm
Home Insurance Soundbox Loans Support"""


def test_paytm_list():
    rows = parse_transactions(PAYTM_TEXT, "income", TODAY)
    assert [r["description"] for r in rows] == [
        "RITIKM", "SANDEEP K", "DEVASHISH S", "DEEPU S", "VIVAAN S",
    ]
    assert [r["amount"] for r in rows] == [2485.0, 7885.0, 230.0, 30.0, 220.0]
    # the one-click correction for a rupee sign misread as a digit
    assert [r["alt_amount"] for r in rows] == [485.0, 885.0, 30.0, None, 20.0]
    assert all(r["type"] == "income" for r in rows)
    assert all(r["date"] == "2026-10-29" and not r["date_guessed"] for r in rows)


def test_summary_and_status_lines_are_skipped():
    text = "10:31 etl 4G\n%23,230 from 82 Payments, Today\nBalance ₹10,000"
    assert parse_transactions(text, "expense", TODAY) == []


def test_csv_style_rows():
    text = "Date, Description, Amount\n2026-10-01, Swiggy, 350\n2026-10-02, Uber ,180"
    rows = parse_transactions(text, "expense", TODAY)
    assert [(r["description"], r["amount"], r["date"], r["category"]) for r in rows] == [
        ("Swiggy", 350.0, "2026-10-01", "Food"),
        ("Uber", 180.0, "2026-10-02", "Travel"),
    ]


def test_app_and_sms_styles():
    text = (
        "12 Oct 2026\n"
        "Paid to Swiggy ₹350\n"
        "Received from Rahul ₹1,200.50\n"
        "Oct 9, 2026 Salary credited ₹45,000"
    )
    rows = parse_transactions(text, "expense", TODAY)
    assert [(r["description"], r["amount"], r["type"], r["date"]) for r in rows] == [
        ("Swiggy", 350.0, "expense", "2026-10-12"),
        ("Rahul", 1200.5, "income", "2026-10-12"),
        ("Salary credited", 45000.0, "income", "2026-10-09"),
    ]


def test_lines_without_money_clues_are_ignored():
    assert parse_transactions("UPI Ref 123456789012\nOrder 3", "expense", TODAY) == []


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} parser tests passed")