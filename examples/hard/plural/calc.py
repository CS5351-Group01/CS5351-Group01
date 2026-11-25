"""难例：单复数边界。

初始代码只返回 'Alice is 25'，测试要求成年人加 'years old'、
一岁婴儿用单数 'year old'。模型第一轮通常只处理常规情况。
"""


def format_age(name, age):
    return f'{name} is {age}'
