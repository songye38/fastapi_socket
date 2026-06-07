from sqlalchemy.orm import Session
from .models import User

def create_user(db: Session, username: str, password_hash: str):
    new_user = User(username=username, password=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()