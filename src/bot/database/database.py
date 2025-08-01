import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger
from sqlalchemy.sql import func
from loguru import logger

from ..config import settings

Base = declarative_base()

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Dialog(Base):
    """Модель диалога/сообщения"""
    __tablename__ = "dialogs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True, index=True)  # Сделаем nullable
    telegram_id = Column(BigInteger, nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=True)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Глобальные переменные для подключения к БД
engine = None
async_session = None

async def init_database():
    """Инициализация базы данных"""
    global engine, async_session
    
    try:
        # Создаем асинхронный движок
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        # Создаем фабрику сессий
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Создаем таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def get_session():
    """Получить асинхронную сессию базы данных"""
    if async_session is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

async def close_database():
    """Закрытие подключения к базе данных"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")