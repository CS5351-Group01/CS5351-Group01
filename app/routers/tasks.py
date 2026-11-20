"""修复任务：上传代码 → 建任务 → 后台跑 → 查结果。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routers.auth import get_current_user
from app.services.storage import StorageService
from app.services.task_runner import run_repair_task

router = APIRouter()


@router.post("/tasks", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    background: BackgroundTasks,
    file: Annotated[UploadFile, File(...)],
    current: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        stored = StorageService().save(file, owner_id=current.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    task = models.Task(
        owner_id=current.id,
        filename=file.filename or stored.name,
        stored_path=str(stored),
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    background.add_task(run_repair_task, task.id)
    return task


@router.get("/tasks", response_model=list[schemas.TaskResponse])
def list_tasks(
    current: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return (
        db.query(models.Task)
        .filter(models.Task.owner_id == current.id)
        .order_by(models.Task.id.desc())
        .all()
    )


@router.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_task(
    task_id: int,
    current: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    task = db.get(models.Task, task_id)
    if task is None or task.owner_id != current.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task
