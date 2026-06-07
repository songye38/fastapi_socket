from passlib.context import CryptContext
from . import repository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def register_user(db, user_data):
    # 비밀번호 길이 제한 처리 (72바이트 초과 시 자르기)
    password_to_hash = user_data.password
    if len(password_to_hash) > 72:
        password_to_hash = password_to_hash[:72]
        
    hashed_password = pwd_context.hash(password_to_hash)
    return repository.create_user(db, user_data.username, hashed_password)