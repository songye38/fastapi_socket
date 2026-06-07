# main.py 맨 위 구역
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

# ★ 1. DB 연결선과 설계도를 각각 분리해서 가져옵니다.
from database import engine, SessionLocal
import models  # 테이블 설계도가 담긴 파일 전체를 임포트

app = FastAPI()

# ★ 2. [테이블 생성 로직] 서버가 시작될 때 models 안에 있는 모든 설계도를 읽어 실제 DB에 테이블을 만듭니다.
models.Base.metadata.create_all(bind=engine)

# ★ 3. 기존 소켓 매니저에서는 models.ChatMessageDB 로 클래스를 사용합니다.
class ConnectionManager:
    def __init__(self):
        self.room_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.room_connections:
            self.room_connections[room_id] = []
        self.room_connections[room_id].append(websocket)

        db = SessionLocal()
        try:
            # ★ 여기를 models.ChatMessageDB로 변경!
            past_messages = (
                db.query(models.ChatMessageDB) 
                .filter(models.ChatMessageDB.room_id == room_id)
                .order_by(models.ChatMessageDB.id.asc())
                .all()
            )
            for msg in past_messages:
                await websocket.send_text(f"{msg.sender}: {msg.content}")
        finally:
            db.close()

    async def broadcast_to_room(self, room_id: str, sender: str, content: str, full_message: str):
        db = SessionLocal()
        try:
            # ★ 여기도 models.ChatMessageDB로 변경!
            new_msg = models.ChatMessageDB(room_id=room_id, sender=sender, content=content)
            db.add(new_msg)
            db.commit()
        finally:
            db.close()

        if room_id in self.room_connections:
            for connection in self.room_connections[room_id]:
                await connection.send_text(full_message)

manager = ConnectionManager()

# ... (이하 HTML 및 웹소켓 엔드포인트 로직은 기존과 완전히 동일합니다) ...


# --- [ 3. 프론트엔드 HTML / 4. 웹소켓 엔드포인트는 기존 구조 유지 ] ---
html = """
<!DOCTYPE html>
<html>
    <head><title>FastAPI 서비스형 채팅</title></head>
    <body>
        </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(room_id, websocket)
    try:
        while True:
            raw_data = await websocket.receive_text()
            if "||" in raw_data:
                sender_name, message_content = raw_data.split("||", 1)
                
                if message_content == "ENTER":
                    if room_id in manager.room_connections:
                        for connection in manager.room_connections[room_id]:
                            await connection.send_text(f"📢 [{sender_name}] 님이 입장하셨습니다.")
                else:
                    full_msg = f"{sender_name}: {message_content}"
                    await manager.broadcast_to_room(
                        room_id=room_id, 
                        sender=sender_name, 
                        content=message_content, 
                        full_message=full_msg
                    )
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        if room_id in manager.room_connections:
            for connection in manager.room_connections[room_id]:
                await connection.send_text("👤 한 명의 유저가 퇴장했습니다.")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)