from fastapi import APIRouter, Depends, Body, Query, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime
from db import get_db
import crud
from models import Notification
from schemas import TaskCreate, TaskOut
from auth import decode_token

tasks_router = APIRouter()

def get_current_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth header")
    payload = decode_token(parts[1])
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(payload.get("sub"))

@tasks_router.get("/")
def list_tasks(category: str = Query("inbox", alias="category"), user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.get_tasks_for_user(db, user_id, category)

def _parse_iso_to_dt(val):
    """Convert ISO string (accepts trailing 'Z') or datetime -> datetime or None."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if not isinstance(val, str):
        return None
    try:
        s = val.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        try:
            return datetime.fromisoformat(val)
        except Exception:
            return None

@tasks_router.post("/", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # create via crud (crud.create_task likely sets basic fields)
    t = crud.create_task(db, user_id, payload)

    # convert and persist parsed/ISO fields safely
    if getattr(payload, "parsedDate", None):
        dt = _parse_iso_to_dt(payload.parsedDate)
        if dt:
            t.parsed_date = dt
    if getattr(payload, "date", None):
        dt = _parse_iso_to_dt(payload.date)
        if dt:
            t.date = dt
    if getattr(payload, "location", None):
        t.location = payload.location
    if getattr(payload, "remindAt", None):
        dt = _parse_iso_to_dt(payload.remindAt)
        if dt:
            t.remind_at = dt
            t.reminded = False
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@tasks_router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # optional: enforce user ownership here if needed
    return task

@tasks_router.patch("/{task_id}")
def patch_task(
    task_id: int,
    patch: dict = Body(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # convert date/remindAt string inputs to datetime objects before update
    if "date" in patch:
        dt = _parse_iso_to_dt(patch.get("date"))
        patch["date"] = dt
    if "remindAt" in patch:
        dt = _parse_iso_to_dt(patch.get("remindAt"))
        patch["remindAt"] = dt

    updated = crud.update_task(db, task_id, patch)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")

    # create notification when marking completed
    try:
        if "completed" in patch and bool(patch["completed"]) is True:
            msg = f"Task completed: {getattr(updated, 'title', 'Task')}"
            notif = Notification(
                task_id=updated.id,
                user_id=user_id,
                message=msg,
                created_at=datetime.utcnow(),
                read=False,
            )
            db.add(notif)
            db.commit()
    except Exception:
        db.rollback()

    return updated

@tasks_router.delete("/{task_id}")
def delete_task(task_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    ok = crud.delete_task(db, task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}
