"""Run from the project root:  python -m tests.test_categorizer"""

from backend.categorizer import merchant_keys, suggest


def test_merchant_keys():
    assert merchant_keys("Swiggy order #1234 lunch") == ["swiggy lunch", "swiggy", "lunch"]
    assert merchant_keys("Ramesh tiffin centre") == [
        "ramesh tiffin centre", "ramesh tiffin", "ramesh", "tiffin", "centre",
    ]
    assert merchant_keys("Uber") == ["uber"]
    assert merchant_keys("Paid to UPI 12345") == []
    assert merchant_keys("") == []
    assert merchant_keys(None) == []


def test_rule_used_when_nothing_learned():
    result = suggest("Swiggy dinner", {})
    assert (result["category"], result["source"]) == ("Food", "rule")


def test_default_when_nothing_known():
    assert suggest("random shop", {}) == {
        "category": "Other", "confidence": 0.2, "source": "default",
    }


def test_learned_phrase_beats_rule():
    result = suggest("Swiggy dinner", {"swiggy dinner": ("Bills", 1)})
    assert (result["category"], result["source"]) == ("Bills", "learned")


def test_one_weak_word_does_not_override_a_good_rule():
    result = suggest("Amazon shoes", {"amazon": ("Bills", 1)})
    assert (result["category"], result["source"]) == ("Shopping", "rule")


def test_habit_wins_after_two_confirmations():
    result = suggest("Amazon shoes", {"amazon": ("Bills", 2)})
    assert (result["category"], result["source"]) == ("Bills", "learned")


def test_extra_words_still_match_a_learned_phrase():
    memory = {"ramesh tiffin": ("Food", 3)}
    result = suggest("Ramesh tiffin centre", memory)
    assert result["category"] == "Food" and result["confidence"] > 0.7


def test_confidence_is_capped():
    assert suggest("abc tiffin", {"abc tiffin": ("Food", 99)})["confidence"] == 0.95


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} categorizer tests passed")