import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

project_root = os.path.join(os.path.dirname(__file__), "..", "..")
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL") 

async_engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def async_session():
    async with AsyncSessionLocal() as session:
        yield session
        
async def get_db():
    async with AsyncSessionLocal() as session:
        print("AsyncSession created")
        yield session
