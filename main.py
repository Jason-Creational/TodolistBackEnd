import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth_router, projects_router, tasks_router, nlp_router, notifications_router
from db import engine, Base
from scheduler import start_scheduler
from dotenv import load_dotenv

load_dotenv()  # load .env if present

app = FastAPI(title="Planner API")

# create DB tables
Base.metadata.create_all(bind=engine)

# Allow multiple origins (comma-separated in FRONTEND_ORIGIN) or "*" for all
raw_origins = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
if raw_origins.strip() == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers under both /api and /apis so frontend requests match
app.include_router(auth_router, prefix="/api/auth")
app.include_router(projects_router, prefix="/api/projects")
app.include_router(tasks_router, prefix="/api/tasks")

# include NLP router for both /api and /apis
app.include_router(nlp_router, prefix="/api/nlp")
app.include_router(nlp_router, prefix="/apis/nlp")

# mount notifications
app.include_router(notifications_router, prefix="/api/notifications")
app.include_router(notifications_router, prefix="/apis/notifications")

app.include_router(auth_router, prefix="/apis/auth")
app.include_router(projects_router, prefix="/apis/projects")
app.include_router(tasks_router, prefix="/apis/tasks")

# Start scheduler to check reminders (prints to console in this scaffold)
start_scheduler()

@app.get("/")
def root():
    return {"status": "ok"}
