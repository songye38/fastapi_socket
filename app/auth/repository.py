from sqlalchemy.orm import Session
from .models import User

def create_user(db: Session, username: str, password_hash: str):
    # 이미 존재하는지 확인
    existing_user = get_user_by_username(db, username)
    if existing_user:
        return None # 중복이면 None 반환
    
    new_user = User(username=username, password=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()
