"""示例项目的验收测试：三个函数，前两个是红的。"""

from calc import add, average, last_item


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_last_item():
    assert last_item([1, 2, 3]) == 3
    assert last_item(["a"]) == "a"


def test_average():
    assert average([2.0, 4.0]) == 3.0
    assert average([]) == 0.0
