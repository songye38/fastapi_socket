# app/auth/models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users" # 데이터베이스에 저장될 테이블 이름

    id = Column(Integer, primary_key=True, index=True) # 고유 번호
    username = Column(String, unique=True, index=True, nullable=False) # 아이디 (중복 불가)
    password = Column(String, nullable=False) # 암호화된 비밀번호
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # 가입 일시

    def __repr__(self):
        return f"<User {self.username}>"