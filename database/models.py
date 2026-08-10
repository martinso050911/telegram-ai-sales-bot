from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)  # "admin" or "user"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String(50), default="new", nullable=False)  # "new", "contacted", "closed"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)  # telegram user_id or web session UUID
    source = Column(String(50), nullable=False)                    # "telegram" or "web"
    sender = Column(String(50), nullable=False)                    # "user" or "ai"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class SystemPromptConfig(Base):
    __tablename__ = "system_prompt_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, default="sales_consultant", nullable=False)
    prompt_text = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
