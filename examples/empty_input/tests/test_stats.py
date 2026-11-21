from stats import average


def test_average():
    assert average([2.0, 4.0]) == 3.0


def test_empty_returns_zero():
    assert average([]) == 0.0
