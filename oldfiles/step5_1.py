import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- [1. 웹소켓 연결 관리자 (대화 기록 기능 추가!)] ---
class ConnectionManager:
    def __init__(self):
        self.room_connections: dict[str, list[WebSocket]] = {}
        # ★ [추가] 각 방의 대화 내역을 임시로 저장할 바구니입니다.
        # { "방이름": ["메시지1", "메시지2", ...] }
        self.room_history: dict[str, list[str]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.room_connections:
            self.room_connections[room_id] = []
            self.room_history[room_id] = [] # 방이 처음 생길 때 대화 기록장도 개설
        self.room_connections[room_id].append(websocket)

        # ★ [핵심] 방에 입장하자마자 이 방의 과거 대화 기록을 새로 들어온 유저에게만 싹 보내줍니다.
        for past_message in self.room_history[room_id]:
            await websocket.send_text(past_message)

    def disconnect(self, room_id: str, websocket: WebSocket):
        self.room_connections[room_id].remove(websocket)
        if not self.room_connections[room_id]:
            del self.room_connections[room_id]
            # 주의: 지금은 메모리 저장이라 방이 폭파되면 기록도 지워집니다. (나중에 진짜 DB로 해결할 부분!)

    async def broadcast_to_room(self, room_id: str, message: str):
        # ★ [추가] 새로운 메시지가 발생하면 먼저 기록장에 적어둡니다.
        if room_id in self.room_history:
            self.room_history[room_id].append(message)
            
        # 그 후 방에 있는 사람들에게 실시간 전송
        if room_id in self.room_connections:
            for connection in self.room_connections[room_id]:
                await connection.send_text(message)

manager = ConnectionManager()

# --- [2. 프론트엔드 HTML / 3. 엔드포인트는 기존과 완전히 동일] ---
# (아래 코드는 기존과 같으므로 생략해도 되지만 덮어쓰기 편하게 전체 유지합니다)
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI 서비스형 채팅</title>
        <style>
            body { font-family: sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }
            .hidden { display: none; }
            #lobby, #chat-room { border: 1px solid #ccc; padding: 20px; border-radius: 8px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
            input { padding: 8px; font-size: 14px; margin-right: 5px; }
            button { padding: 8px 15px; font-size: 14px; cursor: pointer; }
            #messages { list-style: none; padding: 0; max-height: 300px; overflow-y: auto; border: 1px solid #eee; padding: 10px; }
            #messages li { margin-bottom: 8px; padding: 5px; border-bottom: 1px solid #f9f9f9; }
        </style>
    </head>
    <body>
        <div id="lobby">
            <h2>💬 실시간 대기실</h2>
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
            let ws = null; let nickname = ""; let roomId = "";
            function joinRoom() {
                const nickInput = document.getElementById("input-nickname");
                const roomInput = document.getElementById("input-room");
                if (!nickInput.value.trim() || !roomInput.value.trim()) { alert("닉네임과 방 이름을 모두 입력해주세요!"); return; }
                nickname = nickInput.value.trim(); roomId = roomInput.value.trim();
                document.getElementById("lobby").style.display = "none";
                document.getElementById("chat-room").classList.remove("hidden");
                document.getElementById("room-title").innerText = roomId;
                document.getElementById("user-display").innerText = nickname;

                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${protocol}//${window.location.host}/ws/${roomId}`);
                ws.onopen = function() { ws.send(`${nickname}||ENTER`); };
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
async def get(): return HTMLResponse(html)

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(room_id, websocket)
    try:
        while True:
            raw_data = await websocket.receive_text()
            if "||" in raw_data:
                sender_name, message_content = raw_data.split("||", 1)
                if message_content == "ENTER":
                    await manager.broadcast_to_room(room_id, f"📢 [{sender_name}] 님이 입장하셨습니다.")
                else:
                    await manager.broadcast_to_room(room_id, f"{sender_name}: {message_content}")
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        await manager.broadcast_to_room(room_id, "👤 한 명의 유저가 퇴장했습니다.")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)