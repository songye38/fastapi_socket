from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from app.db.database import get_db
from . import schemas, service

router = APIRouter()

@router.post("/signup", response_model=schemas.UserResponse)
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # 이미 존재하는지 확인 로직 추가 가능
    user = service.register_user(db, user_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 아이디입니다."
        )
    return user


# @router.post("/login")
# def login(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
#     user = service.authenticate_user(db, user_data.username, user_data.password)
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="아이디나 비밀번호가 틀렸습니다."
#         )
    
#     return {"message": "로그인 성공!", "user_id": user.id}


@router.post("/login")
def login(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="아이디나 비밀번호가 틀렸습니다.")
    
    token = service.create_access_token({"sub": user.username})
    
    # 이렇게 정보를 합쳐서 보내세요!
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }