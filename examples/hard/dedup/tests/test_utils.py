from utils import deduplicate


def test_dedup_int():
    assert deduplicate([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_dedup_unhashable():
    assert deduplicate([{"a": 1}, {"b": 2}, {"a": 1}]) == [{"a": 1}, {"b": 2}]
