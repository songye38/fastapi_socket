import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- [1. 웹소켓 연결 관리자 (방 관리 기능 업그레이드!)] ---
class ConnectionManager:
    def __init__(self):
        # { "방이름": [WebSocket, WebSocket, ...] } 형태로 저장합니다.
        self.room_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        # 만약 처음 만들어진 방이라면, 새로운 리스트(바구니)를 생성합니다.
        if room_id not in self.room_connections:
            self.room_connections[room_id] = []
        self.room_connections[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        self.room_connections[room_id].remove(websocket)
        # 방에 아무도 없으면 방 자체를 삭제해서 서버 메모리를 아낍니다.
        if not self.room_connections[room_id]:
            del self.room_connections[room_id]

    async def broadcast_to_room(self, room_id: str, message: str):
        # 특정 방에 있는 사람들에게만 메시지를 뿌립니다.
        if room_id in self.room_connections:
            for connection in self.room_connections[room_id]:
                await connection.send_text(message)

manager = ConnectionManager()


# --- [2. 테스트용 프론트엔드 HTML (방 이름 표시 기능 추가)] ---
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI Chat Test</title>
    </head>
    <body>
        <h1>FastAPI 실시간 채팅방: <span id="room-name" style="color: blue;"></span></h1>
        <ul id='messages'></ul>
        <input type="text" id="messageText" autocomplete="off"/>
        <button onclick="sendMessage()">전송</button>
        
        <script>
            // URL 주소창에서 ?room=방이름 부분을 쏙 빼옵니다. (없으면 기본값 'lobby')
            const urlParams = new URLSearchParams(window.location.search);
            const roomId = urlParams.get('room') || 'lobby';
            document.getElementById('room-name').innerText = roomId;

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            // 서버로 연결할 때 내가 어떤 방에 들어가는지 경로에 담아서 알려줍니다. (/ws/apple 같은 형태)
            const ws = new WebSocket(`${protocol}//${window.location.host}/ws/${roomId}`);

            ws.onmessage = function(event) {
                const messages = document.getElementById('messages');
                const message = document.createElement('li');
                const content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };

            function sendMessage() {
                const input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = '';
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)


# --- [3. 웹소켓 엔드포인트 (경로에 room_id 추가)] ---
# URL 경로 자체에 /ws/{room_id}를 넣어서 방을 구분합니다.
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(room_id, websocket) # 해당 방 바구니에 유저 추가
    try:
        while True:
            data = await websocket.receive_text()
            # 메시지를 보낼 때 어떤 방에 보낼지 알려줍니다.
            await manager.broadcast_to_room(room_id, f"익명 유저: {data}")
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        await manager.broadcast_to_room(room_id, "한 명의 유저가 퇴장했습니다.")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)