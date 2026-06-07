from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from . import schemas, service

router = APIRouter()

@router.post("/signup", response_model=schemas.UserResponse)
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # 이미 존재하는지 확인 로직 추가 가능
    return service.register_user(db, user_data)