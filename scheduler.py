from datetime import datetime, timezone
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from db import SessionLocal
from models import Task, Notification

logger = logging.getLogger("scheduler")

def check_reminders():
    """Create notifications for tasks whose remind_at is due and not yet reminded."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        rows = db.query(Task).filter(Task.remind_at != None, Task.reminded == False, Task.remind_at <= now).all()
        if rows:
            logger.info("Found %d reminders to send", len(rows))
        for t in rows:
            msg = f"Reminder: {t.title or 'Task'}"
            notif = Notification(task_id=t.id, user_id=getattr(t, "owner_id", None), message=msg, created_at=now, read=False)
            db.add(notif)
            t.reminded = True
        db.commit()
    except Exception as e:
        logger.exception("Error checking reminders: %s", e)
        db.rollback()
    finally:
        db.close()

_scheduler = None

def start_scheduler():
    """Start background job that checks reminders every minute (idempotent)."""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(check_reminders, "interval", seconds=60, id="check_reminders")
    _scheduler.start()
    logger.info("Scheduler started (check_reminders every 60s)")
