import os
from pathlib import Path
from llm.iterative_fix import repair_project
from llm.client import default_client

HARD_CASES_DIR = Path(__file__).parent / "tmp_hard_cases"

def setup_case1():
    """难题1：单复数边界陷阱。"""
    case_dir = HARD_CASES_DIR / "case1_plural"
    if not case_dir.exists():
        case_dir.mkdir(parents=True)
    
    (case_dir / "calc.py").write_text(
        "def format_age(name, age):\n    return f'{name} is {age}'\n", 
        encoding="utf-8"
    )
    (case_dir / "test_calc.py").write_text(
        "from calc import format_age\n\ndef test_adult():\n    assert format_age('Alice', 25) == 'Alice is 25 years old.'\n\ndef test_baby():\n    assert format_age('Bob', 1) == 'Bob is 1 year old.'\n",
        encoding="utf-8"
    )
    return case_dir, "calc.py"

def setup_case2():
    """难题2：去重不可哈希对象陷阱。模型第一轮大概率用 set() 导致 TypeError。"""
    case_dir = HARD_CASES_DIR / "case2_dedup"
    if not case_dir.exists():
        case_dir.mkdir(parents=True)
        
    (case_dir / "utils.py").write_text(
        "def deduplicate(items):\n    return items\n",
        encoding="utf-8"
    )
    # 故意塞入 dict，set() 无法处理
    (case_dir / "test_utils.py").write_text(
        "from utils import deduplicate\n\ndef test_dedup_int():\n    assert deduplicate([3, 1, 3, 2, 1]) == [3, 1, 2]\n\ndef test_dedup_unhashable():\n    assert deduplicate([{'a': 1}, {'b': 2}, {'a': 1}]) == [{'a': 1}, {'b': 2}]\n",
        encoding="utf-8"
    )
    return case_dir, "utils.py"

def run_cases():
    if not os.environ.get("LLM_API_KEY"):
        print("❌ 请先配置 LLM_API_KEY 环境变量！")
        return

    client = default_client() 
    print(f"当前客户端: {client.__class__.__name__}\n")

    print("="*50)
    print("开始跑难题 1：单复数边界陷阱")
    print("="*50)
    dir1, target1 = setup_case1()
    outcome1 = repair_project(dir1, target1, max_iters=3, client=client)
    
    print(f"最终结果: {'PASS' if outcome1.success else 'FAIL'}, 总共轮数: {outcome1.iterations}")
    for h in outcome1.history:
        print(f"  > {h}")
        
    print("\n" + "="*50)
    print("开始跑难题 2：去重不可哈希对象陷阱")
    print("="*50)
    dir2, target2 = setup_case2()
    outcome2 = repair_project(dir2, target2, max_iters=3, client=client)
    
    print(f"最终结果: {'PASS' if outcome2.success else 'FAIL'}, 总共轮数: {outcome2.iterations}")
    for h in outcome2.history:
        print(f"  > {h}")

if __name__ == "__main__":
    run_cases()