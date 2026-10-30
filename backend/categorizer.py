"""Smart categorization that learns from the user's own choices.

How it works
------------
* Every time you save or correct an EXPENSE, we remember the merchant words
  from the description and the category you chose ("swiggy" -> Food).
* The most recent choice wins, so one correction is enough to change what is
  suggested next time.
* To suggest a category we look for learned words first, then fall back to the
  built-in keyword rules, then to "Other".

This module has no database code, so it is easy to test. main.py does the
reading and writing of the `category_memory` table.
"""

import re

from backend.transaction_parser import guess_category

MAX_TOKENS = 4
MIN_TOKEN_LENGTH = 3

# Words that say nothing about WHAT was bought.
STOPWORDS = {
    "paid", "pay", "payment", "payments", "upi", "the", "and", "for", "via",
    "ref", "txn", "transaction", "bank", "account", "debited", "credited",
    "sent", "received", "imported", "order", "purchase", "pvt", "ltd",
    "limited", "india", "online", "from", "with", "bill",
}

RULE_CONFIDENCE = 0.6


def merchant_keys(description: str) -> list:
    """Return the memory keys for a description, most specific first.

    "Swiggy order #1234 lunch"  -> ["swiggy lunch", "swiggy", "lunch"]
    "Ramesh tiffin centre"      -> ["ramesh tiffin centre", "ramesh tiffin",
                                    "ramesh", "tiffin", "centre"]

    Keys with a space are "phrase" keys; keys without are single words.
    """
    words = re.findall(r"[a-z]+", (description or "").lower())
    tokens = [
        word for word in words
        if len(word) >= MIN_TOKEN_LENGTH and word not in STOPWORDS
    ][:MAX_TOKENS]

    if not tokens:
        return []

    keys = []
    for size in (3, 2):
        phrase = " ".join(tokens[:size])
        if " " in phrase and phrase not in keys:
            keys.append(phrase)
    for token in tokens:
        if token not in keys:
            keys.append(token)
    return [key[:100] for key in keys]


def _full_confidence(times: int) -> float:
    return min(0.5 + 0.1 * times, 0.95)


def _token_confidence(times: int) -> float:
    return min(0.4 + 0.1 * times, 0.85)


def suggest(description: str, memory: dict) -> dict:
    """Suggest a category.

    `memory` maps key -> (category, times_confirmed) for this user.
    Returns {"category", "confidence", "source"} where source is
    "learned", "rule" or "default".
    """
    learned = None
    keys = merchant_keys(description)

    # 1) the most specific phrase you have used before
    for key in keys:
        if " " in key and key in memory:
            category, times = memory[key]
            learned = {
                "category": category,
                "confidence": _full_confidence(times),
                "source": "learned",
            }
            break

    # 2) otherwise the strongest single word (e.g. just "swiggy")
    if learned is None:
        for key in keys:
            if " " not in key and key in memory:
                category, times = memory[key]
                confidence = _token_confidence(times)
                if learned is None or confidence > learned["confidence"]:
                    learned = {
                        "category": category,
                        "confidence": confidence,
                        "source": "learned",
                    }

    rule_category = guess_category(description or "", "expense")
    rule = None
    if rule_category != "Other":
        rule = {
            "category": rule_category,
            "confidence": RULE_CONFIDENCE,
            "source": "rule",
        }

    if learned and (rule is None or learned["confidence"] >= rule["confidence"]):
        return learned
    if rule:
        return rule
    return {"category": "Other", "confidence": 0.2, "source": "default"}