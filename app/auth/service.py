from passlib.context import CryptContext
from . import repository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def register_user(db, user_data):
    # 비밀번호 암호화
    hashed_password = pwd_context.hash(user_data.password)
    return repository.create_user(db, user_data.username, hashed_password)