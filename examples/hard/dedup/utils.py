"""难例：去重且保持顺序，还要能处理不可哈希对象。

第一轮常见的错法是直接用 set()，遇到 dict 就 TypeError。
"""


def deduplicate(items):
    return items
