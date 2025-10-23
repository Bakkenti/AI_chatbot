from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List

from app.db.session import get_db
from app.chat.models import Chat, Message
from pydantic import BaseModel

router = APIRouter(prefix="/api/chats", tags=["Chats"])

active_connections: Dict[int, List[WebSocket]] = {}

class ChatCreate(BaseModel):
    name: str

class MessageCreate(BaseModel):
    content: str


@router.get("/")
async def get_all_chats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chat))
    chats = result.scalars().all()
    return chats

@router.post("/")
async def create_chat(chat: ChatCreate, db: AsyncSession = Depends(get_db)):
    new_chat = Chat(name=chat.name)
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    return new_chat


@router.get("/{chat_id}/messages")
async def get_messages(chat_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return messages

@router.post("/{chat_id}/messages")
async def create_message(chat_id: int, message: MessageCreate, db: AsyncSession = Depends(get_db)):
    new_message = Message(chat_id=chat_id, content=message.content)
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message

