from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"echo": data})
    except WebSocketDisconnect:
        pass

@app.websocket("/ws/notifications/{user_id}")
async def notification_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        await websocket.send_text(f"Notification for {user_id}: {message}")
