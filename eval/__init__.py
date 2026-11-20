"""评估层：数据集、批量实验、指标统计。

故意不在这里 import run_experiments —— 否则 `python -m eval.run_experiments`
会先 import 一次再执行一次，报 RuntimeWarning。
"""
