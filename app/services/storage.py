"""上传文件的落盘与路径安全。"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import UploadFile

STORAGE_ROOT = Path("storage")
MAX_BYTES = 1_000_000  # 单文件 1MB 上限

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")


def safe_filename(name: str) -> str:
    """只保留安全字符，防止 ../ 和怪异扩展名。"""
    name = Path(name or "upload.py").name
    cleaned = _SAFE_NAME.sub("_", name)
    return cleaned or "upload.py"


class StorageService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or STORAGE_ROOT)

    def save(self, upload: UploadFile, owner_id: int) -> Path:
        target_dir = (self.root / str(owner_id)).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        data = upload.file.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError(f"文件超过 {MAX_BYTES} 字节上限")

        filename = safe_filename(upload.filename or "upload.py")
        target = target_dir / f"{uuid.uuid4().hex}_{filename}"

        # 再确认一次没有逃出 owner 目录
        if target_dir not in target.resolve().parents:
            raise ValueError("非法路径")

        target.write_bytes(data)
        return target
