FastAPI backend for Todoist-like planner with NLP date parsing.

1. python -m venv .venv
2. source .venv/bin/activate   # or .venv\\Scripts\\activate on Windows
3. pip install -r requirements.txt
4. copy .env.example -> .env and update SECRET_KEY
5. uvicorn main:app --reload

APIs:
- POST /api/auth/signup
- POST /api/auth/login
- GET/POST /api/projects
- GET/POST/PATCH/DELETE /api/tasks
- POST /api/nlp
