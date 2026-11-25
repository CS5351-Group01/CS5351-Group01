from calc import format_age


def test_adult():
    assert format_age("Alice", 25) == "Alice is 25 years old."


def test_baby():
    assert format_age("Bob", 1) == "Bob is 1 year old."
