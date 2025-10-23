from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.db.session import Base, async_engine
from app.chat.routes import router as chat_router
from app.chat.websocket import router as chat_ws_router
from app.files.routes import router as files_router
from app.storage import minio_client as storage 

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()


app = FastAPI(title="WebSocket AI Chat Bot")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await init_db()


app.include_router(chat_router, tags=["Chats"])
app.include_router(chat_ws_router, tags=["Chat WebSocket"])
app.include_router(files_router, tags=["Files"])


app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def get_index():
    path = os.path.join("app", "templates", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/files", tags=["Files"])
async def list_files():
    try:
        objects = storage.client.list_objects(storage.BUCKET_NAME, recursive=True)
        return [obj.object_name for obj in objects if hasattr(obj, "object_name")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
