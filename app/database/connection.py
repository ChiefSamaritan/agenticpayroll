import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import DATABASE_URL  # Your DB URL

# Load environment variables
load_dotenv()

# ✅ Convert your DATABASE_URL for async
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Async Engine
async_engine = create_async_engine(DATABASE_URL, 
    future=True,    
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # recycle every 30 mins
    echo=True,)

# Async Session Factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Declarative Base
Base = declarative_base()


