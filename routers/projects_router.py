from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from db import get_db
import crud
from schemas import ProjectCreate
from auth import decode_token

projects_router = APIRouter()

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

@projects_router.get("/")
def list_projects(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.get_projects_for_user(db, user_id)

@projects_router.post("/")
def create_project(payload: ProjectCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.create_project(db, user_id, payload.name)

@projects_router.get("/{project_id}")
def get_project(project_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    p = crud.get_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    if p.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return p
