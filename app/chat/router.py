from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from app.chat.manager import manager



router = APIRouter()

# --- [ 3. 웹소켓 엔드포인트 ] ---
@router.websocket("/ws/{room_id}")
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