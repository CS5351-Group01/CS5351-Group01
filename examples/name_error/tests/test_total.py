from total import item_count


def test_item_count():
    assert item_count([1, 2, 3]) == 3


def test_empty():
    assert item_count([]) == 0
