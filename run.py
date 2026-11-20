"""本地一体化启动入口。

  python run.py            # 起服务 http://127.0.0.1:8000
  python run.py --reload   # 开发时自动重载

前端在同端口下的 / 路径，直接浏览器打开即可。
"""

from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="启动代码修复代理服务")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    import uvicorn

    # 让 uvicorn 用模块路径导入，--reload 才生效
    os.environ.setdefault("PYTHONPATH", os.getcwd())
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
