from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.chat.router import router as chat_router

# 1. DB 연결 설정과 Base를 불러옵니다.
from app.db.database import engine, Base

# 2. 모든 모델(테이블)을 미리 가져옵니다. 
# (이걸 안 하면 Base.metadata가 테이블을 인식하지 못합니다.)
from app.chat import models as chat_models
# 나중에 auth 모델 만들면 여기서도 임포트해야 합니다.
# from app.auth import models as auth_models

# 3. 앱 시작 시 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://my-chat-seven-mu.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)



