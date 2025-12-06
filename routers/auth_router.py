from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
import crud
from schemas import UserCreate, TokenOut
from auth import create_access_token

auth_router = APIRouter()

@auth_router.post("/signup", response_model=TokenOut)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, payload.email, payload.password, payload.name)
    token = create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer"}

@auth_router.post("/login", response_model=TokenOut)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer"}
