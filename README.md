# Backend README (FastAPI + NLP + SQLAlchemy)

## 🚀 Introduction

This backend provides APIs for a Vietnamese natural-language-powered
task manager.\
It includes authentication, projects, tasks, NLP extraction, and
reminder scheduling.

## 📦 Installation

``` bash
git clone <repo-backend-url>
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Create `.env`:

    SECRET_KEY=your-secret-key

## ▶️ Run server

``` bash
uvicorn main:app --reload
```

## 🔥 Main APIs

### Auth

-   POST `/api/auth/signup`
-   POST `/api/auth/login`

### Projects

-   GET `/api/projects`
-   POST `/api/projects`
-   GET `/api/projects/{id}`

### Tasks

-   GET `/api/tasks?category=...`
-   POST `/api/tasks`
-   PATCH `/api/tasks/{id}`
-   DELETE `/api/tasks/{id}`

### NLP

-   POST `/api/nlp`

## 📂 Structure

    backend/
     ├── routers/
     ├── models/
     ├── schemas/
     ├── services/
     ├── utils/
     └── main.py
