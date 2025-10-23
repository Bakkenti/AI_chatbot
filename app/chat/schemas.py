from pydantic import BaseModel
from typing import List
from datetime import datetime

class MessageSchema(BaseModel):
    id: int
    sender: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True  

class ChatSchema(BaseModel):
    id: int
    name: str
    created_at: datetime
    messages: List[MessageSchema] = []

    class Config:
        from_attributes = True
