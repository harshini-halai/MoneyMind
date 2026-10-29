"""Turn OCR text from a payment-app screenshot into draft transactions.

Nothing here talks to the database or the OCR engine, so it is easy to test.
The results are only DRAFTS: the user reviews and edits them before saving.
"""

import re
from datetime import date, timedelta

MAX_CANDIDATES = 100
MAX_AMOUNT = 10_000_000

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH_NAMES = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"

# ---------- patterns ----------

TIME_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AaPp]\.?[Mm]\.?)?(?!\d)")

ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
NUMERIC_DATE_RE = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4}|\d{2})\b")
DAY_MONTH_RE = re.compile(
    rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_NAMES})[a-z]*\.?,?(?:\s+(\d{{4}}))?\b",
    re.I,
)
MONTH_DAY_RE = re.compile(
    rf"\b({_MONTH_NAMES})[a-z]*\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?\b",
    re.I,
)
RELATIVE_DATE_RE = re.compile(r"\b(today|yesterday)\b", re.I)

_AMOUNT = r"(\d{1,3}(?:,\d{2,3})+|\d+)(\.\d{1,2})?"
# An amount written with a real currency marker, anywhere in the line.
CURRENCY_AMOUNT_RE = re.compile(r"(?<![\w.])(?<!\d,)(₹|Rs\.?|INR)\s*" + _AMOUNT, re.I)
# An amount at the end of the line. The optional prefix also accepts one stray
# symbol, because OCR often reads the rupee sign as %, =, £ and similar.
END_AMOUNT_RE = re.compile(
    r"(?<![\w.])(?<!\d,)(₹|Rs\.?|INR|[^\w\s.,:/\-+()]{1})?\s*"
    + _AMOUNT
    + r"\s*(?:/-|CR|DR)?\s*$",
    re.I,
)

# Lines that are never a transaction row.
SUMMARY_RE = re.compile(
    r"\b\d+\s+payments?\b|\b(total|balance|available|limit|statement|summary)\b",
    re.I,
)
STATUS_BAR_RE = re.compile(r"\b[2-5]G\b|\bLTE\b|\bwi-?fi\b|\bbattery\b", re.I)

STRONG_EXPENSE_RE = re.compile(
    r"\b(paid|sent|debited|debit|purchase|spent|withdraw\w*|payment to|transfer to)\b",
    re.I,
)
STRONG_INCOME_RE = re.compile(
    r"\b(received|credited|credit|refund\w*|cashback|salary|deposit\w*|"
    r"payment from|transfer from)\b",
    re.I,
)
WEAK_EXPENSE_RE = re.compile(r"\bto\b", re.I)
WEAK_INCOME_RE = re.compile(r"\bfrom\b", re.I)

LEADING_WORDS_RE = re.compile(
    r"^(?:paid to|paid|sent to|sent|received from|received|payment from|"
    r"payment to|credited to|credited by|credited|debited from|debited for|"
    r"debited|transfer to|transfer from)\s+",
    re.I,
)
NOISE_WORDS_RE = re.compile(r"\b(successful|completed|success|upi)\b", re.I)

CATEGORY_KEYWORDS = {
    "Food": [
        "swiggy", "zomato", "restaurant", "cafe", "food", "pizza", "dominos",
        "kfc", "mcdonald", "burger", "bakery", "chai", "tea", "biryani", "dhaba",
    ],
    "Travel": [
        "uber", "ola", "rapido", "irctc", "railway", "redbus", "metro", "petrol",
        "fuel", "diesel", "bus", "cab", "taxi", "flight", "indigo", "fastag",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "meesho", "ajio", "store", "mart",
        "mall", "supermarket", "bigbasket", "blinkit", "zepto",
    ],
    "Bills": [
        "electricity", "recharge", "jio", "airtel", "vodafone", "bill", "broadband",
        "insurance", "rent", "dth", "gas", "water", "postpaid", "emi", "loan",
    ],
}


# ---------- helpers ----------

def _safe_date(year: int, month: int, day: int):
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _with_year(month: int, day: int, year, today: date):
    """Build a date when the screenshot omits the year."""
    if year:
        return _safe_date(int(year), month, day)
    result = _safe_date(today.year, month, day)
    if result and result > today + timedelta(days=2):
        result = _safe_date(today.year - 1, month, day)
    return result


def extract_date(line: str, today: date):
    """Return (date or None, line with the date text removed)."""
    match = ISO_DATE_RE.search(line)
    if match:
        found = _safe_date(*(int(g) for g in match.groups()))
        if found:
            return found, line[: match.start()] + " " + line[match.end():]

    match = NUMERIC_DATE_RE.search(line)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), match.group(3)
        if month > 12 >= day:  # looks like mm/dd, swap
            day, month = month, day
        full_year = int(year) + 2000 if len(year) == 2 else int(year)
        found = _safe_date(full_year, month, day)
        if found:
            return found, line[: match.start()] + " " + line[match.end():]

    match = DAY_MONTH_RE.search(line)
    if match:
        found = _with_year(MONTHS[match.group(2).lower()[:3]], int(match.group(1)),
                           match.group(3), today)
        if found:
            return found, line[: match.start()] + " " + line[match.end():]

    match = MONTH_DAY_RE.search(line)
    if match:
        found = _with_year(MONTHS[match.group(1).lower()[:3]], int(match.group(2)),
                           match.group(3), today)
        if found:
            return found, line[: match.start()] + " " + line[match.end():]

    match = RELATIVE_DATE_RE.search(line)
    if match:
        found = today if match.group(1).lower() == "today" else today - timedelta(days=1)
        return found, line[: match.start()] + " " + line[match.end():]

    return None, line


def guess_type(text: str, default_type: str, sign: str = "") -> str:
    if sign == "-":
        return "expense"
    if sign == "+":
        return "income"

    strong_expense = bool(STRONG_EXPENSE_RE.search(text))
    strong_income = bool(STRONG_INCOME_RE.search(text))
    if strong_expense and not strong_income:
        return "expense"
    if strong_income and not strong_expense:
        return "income"
    if strong_expense and strong_income:
        return default_type

    weak_expense = bool(WEAK_EXPENSE_RE.search(text))
    weak_income = bool(WEAK_INCOME_RE.search(text))
    if weak_expense and not weak_income:
        return "expense"
    if weak_income and not weak_expense:
        return "income"
    return default_type


def guess_category(description: str, tx_type: str) -> str:
    if tx_type == "income":
        return "Other"
    lowered = description.lower()
    for category, words in CATEGORY_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(word)}", lowered) for word in words):
            return category
    return "Other"


def _find_amount(text: str):
    """Return (amount, symbol_seen, sign, text_without_amount) or None."""
    match = CURRENCY_AMOUNT_RE.search(text)
    symbol_seen = True
    if not match:
        match = END_AMOUNT_RE.search(text)
        if not match:
            return None
        symbol_seen = bool(match.group(1))

    whole, decimals = match.group(2), match.group(3) or ""
    amount = float(whole.replace(",", "") + decimals)
    if amount <= 0 or amount >= MAX_AMOUNT:
        return None

    before = text[: match.start()].rstrip()
    sign = before[-1] if before[-1:] in ("-", "+") else ""
    remaining = (before + " " + text[match.end():]).strip()
    return amount, symbol_seen, sign, remaining, whole, decimals


def _alternative_amount(whole: str, decimals: str, symbol_seen: bool):
    """Amount with the first digit removed.

    OCR often reads the rupee sign as a digit (rupee 485 comes out as 2485).
    When no currency symbol was seen we offer this as a one-click correction.
    """
    digits = whole.replace(",", "")
    if symbol_seen or len(digits) < 2:
        return None
    alt = float(digits[1:] + decimals)
    return alt if alt > 0 else None


def _clean_description(text: str) -> str:
    text = LEADING_WORDS_RE.sub("", text.strip())
    text = NOISE_WORDS_RE.sub(" ", text)
    text = re.sub(r"^[^\w]+|[^\w)]+$", "", text)  # stray punctuation at the ends
    text = re.sub(r"\s+", " ", text).strip()
    return text[:255] if text else "Imported transaction"


# ---------- public API ----------

def parse_transactions(text: str, default_type: str = "expense", today: date = None):
    """Return a list of draft transactions found in `text`."""
    today = today or date.today()
    current_date = None
    candidates = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        found_date, without_date = extract_date(line, today)
        if found_date:
            current_date = found_date  # a header like "Today" or "12 Oct 2026"

        if SUMMARY_RE.search(line) or STATUS_BAR_RE.search(line):
            continue

        time_match = TIME_RE.search(without_date)
        has_time = bool(time_match)
        working = without_date
        if time_match:
            before_time = working[: time_match.start()].strip()
            if len(before_time) <= 3:  # icon noise such as "at" or "fi"
                before_time = ""
            working = before_time + " " + working[time_match.end():]

        found = _find_amount(working.strip())
        if not found:
            continue
        amount, symbol_seen, sign, remaining, whole, decimals = found

        has_type_word = bool(STRONG_EXPENSE_RE.search(line) or STRONG_INCOME_RE.search(line))
        if not (has_time or found_date or symbol_seen or has_type_word or sign):
            continue  # a bare number with nothing money-like around it

        tx_type = guess_type(line, default_type, sign)
        description = _clean_description(remaining)

        candidates.append({
            "description": description,
            "amount": amount,
            "alt_amount": _alternative_amount(whole, decimals, symbol_seen),
            "date": (found_date or current_date or today).isoformat(),
            "date_guessed": not (found_date or current_date),
            "type": tx_type,
            "category": guess_category(description, tx_type),
            "symbol_seen": symbol_seen,
            "source_line": line[:200],
        })

        if len(candidates) >= MAX_CANDIDATES:
            break

    return candidates
