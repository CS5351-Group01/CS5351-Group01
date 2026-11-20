"""循环少走一步，最后一个元素被漏掉。"""


def count_positive(numbers):
    count = 0
    for i in range(len(numbers) - 1):
        if numbers[i] > 0:
            count += 1
    return count
