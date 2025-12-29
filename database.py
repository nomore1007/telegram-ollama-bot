"""Database models for Telegram Ollama Bot"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()

class User(Base):
    """User model for storing user information and preferences"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    preferred_model = Column(String(50), default='llama2')
    language = Column(String(10), default='en')
    timezone = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    messages = relationship("Message", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

class Conversation(Base):
    """Conversation model for storing chat sessions"""
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(200))
    topic = Column(String(100))
    status = Column(String(20), default='active')  # active, archived, deleted
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")

    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, messages={self.message_count})>"

class Message(Base):
    """Message model for storing individual messages"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    message_type = Column(String(20), default='text')  # text, image, voice, file
    content = Column(Text, nullable=False)
    content_metadata = Column(Text)  # JSON metadata for media files
    role = Column(String(20), default='user')  # user, assistant, system
    tokens_used = Column(Integer)
    processing_time = Column(Float)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, type={self.message_type}, role={self.role})>"

class MediaFile(Base):
    """Media file model for storing uploaded files"""
    __tablename__ = 'media_files'

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('messages.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    checksum = Column(String(128))  # SHA-256 hash
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MediaFile(id={self.id}, filename={self.filename}, size={self.file_size})>"

class AIModel(Base):
    """AI model information and usage statistics"""
    __tablename__ = 'ai_models'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    provider = Column(String(50), default='ollama')  # ollama, openai, gemini, etc.
    model_family = Column(String(50))
    context_length = Column(Integer)
    is_active = Column(Boolean, default=True)
    total_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    average_response_time = Column(Float)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AIModel(name={self.name}, provider={self.provider}, requests={self.total_requests})>"

class UsageStats(Base):
    """Usage statistics for monitoring"""
    __tablename__ = 'usage_stats'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    action = Column(String(100), nullable=False)  # message_sent, video_processed, etc.
    value = Column(Float, default=1.0)  # count, duration, etc.
    metadata = Column(Text)  # JSON additional data
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<UsageStats(user_id={self.user_id}, action={self.action}, value={self.value})>"

class ChannelSettings(Base):
    """Per-channel settings for model, provider, and prompt configuration"""
    __tablename__ = 'channel_settings'

    id = Column(Integer, primary_key=True)
    channel_id = Column(String(50), unique=True, nullable=False, index=True)  # Telegram chat ID
    provider = Column(String(50), default='ollama')  # ollama, openai, groq, etc.
    model = Column(String(100))  # Model name
    host = Column(String(200))  # Custom host for ollama
    prompt = Column(Text)  # Custom system prompt
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ChannelSettings(channel_id={self.channel_id}, provider={self.provider}, model={self.model})>"

# Database connection and session management
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///telegram_bot.db')

engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

if __name__ == "__main__":
    init_db()