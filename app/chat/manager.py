# --- [ 1. 웹소켓 연결 관리자 ] ---
from fastapi import WebSocket
from app.chat import models
from app.db.database import SessionLocal


class ConnectionManager:
    def __init__(self):
        self.room_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.room_connections:
            self.room_connections[room_id] = []
        self.room_connections[room_id].append(websocket)

        # 방 입장 시 DB에서 과거 대화 내역 조회 후 전송
        db = SessionLocal()
        try:
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

    def disconnect(self, room_id: str, websocket: WebSocket):
        self.room_connections[room_id].remove(websocket)
        if not self.room_connections[room_id]:
            del self.room_connections[room_id]

    async def broadcast_to_room(self, room_id: str, sender: str, content: str, full_message: str):
        # 메시지 수신 시 DB에 영구 저장
        db = SessionLocal()
        try:
            new_msg = models.ChatMessageDB(room_id=room_id, sender=sender, content=content)
            db.add(new_msg)
            db.commit()
        finally:
            db.close()

        # 실시간 브로드캐스트
        if room_id in self.room_connections:
            for connection in self.room_connections[room_id]:
                await connection.send_text(full_message)

manager = ConnectionManager()