import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- [1. 웹소켓 연결 관리자] ---
# 접속한 유저들의 소켓 연결을 보관하고, 메시지를 브로드캐스트하는 역할을 합니다.
class ConnectionManager:
    def __init__(self):
        # 접속한 모든 클라이언트 소켓을 리스트로 보관
        self.active_connections: list[WebSocket] = []
        print("ConnectionManager가 생성되었습니다. 이제 웹소켓 연결을 관리할 준비가 되었습니다.",self.active_connections)


    async def connect(self, websocket: WebSocket):
        await websocket.accept() # Handshake 승인! 이제 선이 연결됩니다.
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # 연결된 모든 사람의 선을 타고 메시지를 동시에 뿌립니다.
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


# --- [2. 테스트용 프론트엔드 HTML] ---
# 브라우저로 접속했을 때 웹소켓을 직접 테스트할 수 있는 초간단 화면입니다.
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI Chat Test</title>
    </head>
    <body>
        <h1>FastAPI 실시간 채팅방</h1>
        <ul id='messages'></ul>
        <input type="text" id="messageText" autocomplete="off"/>
        <button onclick="sendMessage()">전송</button>
        
        <script>
            // 현재 접속 주소에 맞춰 ws:// 또는 wss:// 주소를 자동으로 맞춥니다. (로컬/배포 공용)
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

            // 서버로부터 메시지가 왔을 때 화면에 리스트로 추가하는 함수
            ws.onmessage = function(event) {
                const messages = document.getElementById('messages');
                const message = document.createElement('li');
                const content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };

            // 전송 버튼을 누르면 인풋 창의 텍스트를 서버로 쏘는 함수
            function sendMessage() {
                const input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = '';
            }
        </script>
    </body>
</html>
"""

# 일반적인 REST API 방식처럼, 처음 접속했을 때 위의 HTML 화면을 그려주는 엔드포인트입니다.
# 웹 클라이언트 화면 그리는 코드
@app.get("/")
async def get():
    return HTMLResponse(html)


# --- [3. 웹소켓 엔드포인트] ---
# 클라이언트가 실시간 연결을 맺는 통로입니다.
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket) # 유저가 오면 연결을 맺고 리스트에 보관
    try:
        while True:
            # 클라이언트가 메시지를 보낼 때까지 일꾼이 여기서 딱 대기(Await)합니다.
            data = await websocket.receive_text()
            # 메시지가 들어오면 관리자에게 넘겨서 모든 접속자에게 뿌립니다.
            await manager.broadcast(f"익명 유저: {data}")
    except WebSocketDisconnect:
        # 유저가 브라우저 창을 닫거나 나가면 실행됩니다.
        manager.disconnect(websocket)
        await manager.broadcast("한 명의 유저가 퇴장했습니다.")


# --- [4. 서버 실행 설정 (Railway 배포 대응)] ---
if __name__ == "__main__":
    import uvicorn
    # Railway가 환경변수로 던져주는 PORT가 있으면 그걸 쓰고, 없으면 로컬 환경용 8000번을 씁니다.
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)