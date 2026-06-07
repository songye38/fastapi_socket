from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.chat.router import router as chat_router
from app.auth.router import router as auth_router

# 1. DB 연결 설정과 Base를 불러옵니다.
from app.db.database import engine, Base

# 2. 모든 모델(테이블)을 미리 가져옵니다. 
# (이걸 안 하면 Base.metadata가 테이블을 인식하지 못합니다.)
from app.chat import models as chat_models
from app.auth import models as auth_models

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
app.include_router(auth_router, prefix="/auth")



# main.py 맨 마지막에 추가
if __name__ == "__main__":
    import uvicorn
    # 8000번 포트는 Railway에서 관례적으로 많이 쓰입니다. 
    # 하지만 Railway가 자동으로 정해주는 포트가 있다면 
    # uvicorn main:app --host 0.0.0.0 --port $PORT 명령어가 이를 대신합니다.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
