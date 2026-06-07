import bcrypt
from . import repository

def register_user(db, user_data):
    # 1. 비밀번호 길이 제한 (72자)
    password = user_data.password[:72]
    
    # 2. 비밀번호를 바이트로 변환 후 솔트(salt)와 함께 해싱
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    
    # 3. 데이터베이스에 저장할 때는 문자열로 변환하여 저장
    return repository.create_user(db, user_data.username, hashed_password.decode('utf-8'))

def verify_password(plain_password, hashed_password):
    # 나중에 로그인 로직에서 사용할 검증 함수
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))