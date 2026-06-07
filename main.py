import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

# ★ CORS 처리를 위한 미들웨어 임포트
from fastapi.middleware.cors import CORSMiddleware

# database, models 파일에서 필요한 부품들 수입
from database import engine, SessionLocal
import models

app = FastAPI()


# ★ [추가] CORS 설정 구역
# 여기에 허용할 프론트엔드 주소들을 적어줍니다.
origins = [
    "http://localhost:5173",    # 로컬 React 개발 서버 주소
    "https://my-chat-seven-mu.vercel.app/" # ★ 방금 배포 성공한 Vercel 주소 입력!
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # 허용할 고향(Origin) 주소들
    allow_credentials=True,
    allow_methods=["*"],            # GET, POST, PUT, DELETE 등 모든 메서드 허용
    allow_headers=["*"],            # 모든 헤더 허용
)

# [테이블 생성] 서버 시작 시 데이터베이스에 테이블 자동 생성
models.Base.metadata.create_all(bind=engine)


# --- [ 1. 웹소켓 연결 관리자 ] ---
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


# --- [ 2. 프론트엔드 HTML (생략 없는 전체 코드) ] ---
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI 서비스형 채팅</title>
        <style>
            body { font-family: sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }
            .hidden { display: none !important; }
            #lobby, #chat-room { border: 1px solid #ccc; padding: 20px; border-radius: 8px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
            input { padding: 8px; font-size: 14px; margin-right: 5px; }
            button { padding: 8px 15px; font-size: 14px; cursor: pointer; }
            #messages { list-style: none; padding: 0; max-height: 300px; overflow-y: auto; border: 1px solid #eee; padding: 10px; }
            #messages li { margin-bottom: 8px; padding: 5px; border-bottom: 1px solid #f9f9f9; }
        </style>
    </head>
    <body>

        <div id="lobby">
            <h2>💬 실시간 대기실 (PostgreSQL 영구저장)</h2>
            <p>닉네임과 입장할 방 이름을 입력해 주세요.</p>
            <div style="margin-bottom: 10px;">
                <label>내 닉네임: </label>
                <input type="text" id="input-nickname" placeholder="예: 송이" autocomplete="off"/>
            </div>
            <div style="margin-bottom: 15px;">
                <label>방 이름 입력: </label>
                <input type="text" id="input-room" placeholder="예: apple 또는 개발방" autocomplete="off"/>
            </div>
            <button onclick="joinRoom()">채팅방 입장하기</button>
        </div>

        <div id="chat-room" class="hidden">
            <h2>방 이름: <span id="room-title" style="color: blue;"></span></h2>
            <h4>접속자: <span id="user-display" style="color: green;"></span></h4>
            
            <ul id='messages'></ul>
            
            <div style="display: flex;">
                <input type="text" id="messageText" style="flex-grow: 1;" autocomplete="off" onkeyup="if(window.event.keyCode==13){sendMessage()}"/>
                <button onclick="sendMessage()">전송</button>
            </div>
        </div>
        
        <script>
            let ws = null;
            let nickname = "";
            let roomId = "";

            function joinRoom() {
                const nickInput = document.getElementById("input-nickname");
                const roomInput = document.getElementById("input-room");

                if (!nickInput.value.trim() || !roomInput.value.trim()) {
                    alert("닉네임과 방 이름을 모두 입력해주세요!");
                    return;
                }

                nickname = nickInput.value.trim();
                roomId = roomInput.value.trim();

                document.getElementById("lobby").style.display = "none";
                document.getElementById("chat-room").classList.remove("hidden");
                
                document.getElementById("room-title").innerText = roomId;
                document.getElementById("user-display").innerText = nickname;

                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${protocol}//${window.location.host}/ws/${roomId}`);

                ws.onopen = function() {
                    ws.send(`${nickname}||ENTER`);
                };

                ws.onmessage = function(event) {
                    const messages = document.getElementById('messages');
                    const message = document.createElement('li');
                    message.appendChild(document.createTextNode(event.data));
                    messages.appendChild(message);
                    messages.scrollTop = messages.scrollHeight;
                };
            }

            function sendMessage() {
                const input = document.getElementById("messageText");
                if (input.value.trim() === "" || !ws) return;
                
                ws.send(`${nickname}||${input.value}`);
                input.value = '';
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)


# --- [ 3. 웹소켓 엔드포인트 ] ---
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