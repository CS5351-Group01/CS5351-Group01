"""示例项目：一个有两个 bug 的小模块。

它存在的意义是「有个确定的东西可以拿来跑闭环」——
测试挂了 → 模型生成 → 沙箱验证 → 直到通过。
"""


def add(a: int, b: int) -> int:
    """返回两个数之和。"""
    return a - b  # BUG: 应该是 a + b


def last_item(items: list) -> object:
    """返回最后一个元素。"""
    return items[len(items)]  # BUG: 下标越界，应该是 items[-1]


def average(values: list[float]) -> float:
    """返回平均值，空列表返回 0.0。"""
    if not values:
        return 0.0
    # 故意写成两行：避免和 examples/empty_input 里那一行的字面文本撞车，
    # 否则假模型的全局替换会把这里也顺手改掉，产生一行「无谓改动」。
    total = sum(values)
    return total / len(values)
