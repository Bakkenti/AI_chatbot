from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from app.bot.manager import dispatch
from app.db.session import AsyncSessionLocal
from app.chat.models import Message
from app.bot.commands.pdf import handle_pdf

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()

last_ai_messages: dict[int, str] = {}

async def save_message(chat_id: int, sender: str, content: str):
    async with AsyncSessionLocal() as session:
        msg = Message(chat_id=chat_id, sender=sender, content=content)
        session.add(msg)
        await session.commit()
        
@router.websocket("/api/chats/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int):
    await manager.connect(websocket)
    await manager.send_json(websocket, {"sender": "system", "content": f"Connected to chat {chat_id}"})

    try:
        while True:
            raw_data = await websocket.receive_text()
            
            try:
                import json
                parsed = json.loads(raw_data)
            except:
                parsed = {"content": raw_data}

            if parsed.get("filetype") == "pdf" and "filename" in parsed and "content" in parsed:
                file_content_base64 = parsed["content"]
                import base64
                file_bytes = base64.b64decode(file_content_base64)
                filename = parsed["filename"]
                try:
                    text = handle_pdf(file_bytes)
                    await save_message(chat_id, "user", f"[PDF] {filename} uploaded")
                    await save_message(chat_id, "ai", text)
                    last_ai_messages[chat_id] = text
                    await manager.send_json(websocket, {"sender": "ai", "content": text})
                except Exception as e:
                    await manager.send_json(websocket, {"sender": "ai", "content": f"❌ PDF Error: {e}"})
                continue

            user_message = parsed.get("content", raw_data)
            await save_message(chat_id, "user", user_message)
            
            response = await dispatch(user_message, chat_id=chat_id)
            await save_message(chat_id, "ai", response)
            last_ai_messages[chat_id] = response
            await manager.send_json(websocket, {"sender": "ai", "content": response})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
