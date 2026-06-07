import bcrypt
from . import repository
import jwt
import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # 이거 꼭 해줘야 함

SECRET_KEY = os.getenv("SECRET_KEY")  # 실제로는 환경변수로 숨겨야 합니다!
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def register_user(db, user_data):
    # 1. 비밀번호 길이 제한 (72자)
    password = user_data.password[:72]
    
    # 2. 비밀번호를 바이트로 변환 후 솔트(salt)와 함께 해싱
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    
    # 3. 데이터베이스에 저장할 때는 문자열로 변환하여 저장
    # return repository.create_user(db, user_data.username, hashed_password.decode('utf-8'))
    user = repository.create_user(db, user_data.username, hashed_password.decode('utf-8'))
    if not user:
        return None # 중복 처리 이미 있는 아이디라면 none을 반환한다. 
    return user

def verify_password(plain_password, hashed_password):
    # 나중에 로그인 로직에서 사용할 검증 함수
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def authenticate_user(db, username, password):
    # 1. 유저 조회
    user = repository.get_user_by_username(db, username)
    if not user:
        return None
    
    # 2. 비밀번호 검증 (DB에 저장된 해시값과 비교)
    if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return user
    return None