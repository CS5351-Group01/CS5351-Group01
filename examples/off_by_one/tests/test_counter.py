from counter import count_positive


def test_counts_last_element():
    assert count_positive([1, 2, 3]) == 3


def test_all_negative():
    assert count_positive([-1, -2]) == 0
