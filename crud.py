from sqlalchemy.orm import Session
from models import User, Project, Task
from auth import hash_password, verify_password
from datetime import datetime, timedelta, time
from sqlalchemy import func
import models
from typing import List

# Users
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password: str, name: str = None):
    hashed = hash_password(password)
    user = User(email=email, hashed_password=hashed, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user: return None
    if not verify_password(password, user.hashed_password): return None
    return user

# Projects
def get_projects_for_user(db: Session, user_id: int) -> List[Project]:
    return db.query(Project).filter(Project.owner_id == user_id).all()

def create_project(db: Session, user_id: int, name: str):
    p = Project(name=name, owner_id=user_id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def get_project(db: Session, project_id: int):
    return db.query(Project).filter(Project.id == project_id).first()

# Tasks
def create_task(db: Session, user_id: int, task_in):
    t = Task(
        title=task_in.title,
        description=getattr(task_in, "description", None),
        date=task_in.date,
        remind_before_minutes=getattr(task_in, "remind_before_minutes", None),
        project_id=getattr(task_in, "project_id", None),
        owner_id=user_id
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

def get_task(db, task_id):
    """Return a task or None."""
    from models import Task
    return db.query(Task).filter(Task.id == task_id).first()

def get_tasks_for_user(db, user_id: int, view: str = "inbox"):
    """Return tasks filtered by view (inbox/today/upcoming/completed)."""
    q = db.query(models.Task).filter(models.Task.owner_id == user_id)

    if view == "completed":
        q = q.filter(models.Task.completed == True)
    elif view == "today":
        today = datetime.utcnow().date()
        start = datetime(today.year, today.month, today.day)
        end = start + timedelta(days=1)
        q = q.filter(
            models.Task.date != None,
            models.Task.date >= start,
            models.Task.date < end,
            models.Task.completed == False,
        )
    elif view == "upcoming":
        tomorrow = (datetime.utcnow().date() + timedelta(days=1))
        start = datetime(tomorrow.year, tomorrow.month, tomorrow.day)
        q = q.filter(
            models.Task.date != None,
            models.Task.date >= start,
            models.Task.completed == False,
        )
    else:
        q = q.filter(models.Task.completed == False)

    try:
        q = q.order_by(func.coalesce(models.Task.date, datetime.max), models.Task.created_at.desc())
    except Exception:
        q = q.order_by(models.Task.created_at.desc())

    return q.all()

def update_task(db: Session, task_id: int, patch: dict):
    t = db.query(Task).filter(Task.id == task_id).first()
    if not t: return None
    for k, v in patch.items():
        if hasattr(t, k):
            setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t

def delete_task(db: Session, task_id: int):
    t = db.query(Task).filter(Task.id == task_id).first()
    if not t:
        return False
    db.delete(t)
    db.commit()
    return True

def get_tasks_with_reminder_due(db: Session, now):
    """Return tasks that should be reminded at 'now' (used by scheduler)."""
    tasks = db.query(Task).filter(Task.date != None, Task.remind_before_minutes != None, Task.completed == False).all()
    due = []
    for t in tasks:
        remind_at = t.date - datetime.timedelta(minutes=t.remind_before_minutes)
        if remind_at <= now <= t.date:
            due.append(t)
    return due
