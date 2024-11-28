from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import logging

Base = declarative_base()
logger = logging.getLogger(__name__)


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String(100), nullable=True)
    sessions = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")


class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    content = Column(Text)
    is_user = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    has_errors = Column(Boolean, default=False)
    error_description = Column(Text)
    session = relationship("Session", back_populates="messages")

# Database initialization
engine = create_engine('sqlite:///bot_statistics.db')
Base.metadata.create_all(engine)
Sessionmk = sessionmaker(bind=engine)


def get_db_session():
    return Sessionmk()


def get_session_statistics(user_id: int):
    db_session = Sessionmk()
    try:
        user = db_session.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            return None
        
        sessions = db_session.query(Session).filter(Session.user_id == user.id).all()
        total_messages = 0
        total_errors = 0
        
        for session in sessions:
            messages = session.messages
            total_messages += len(messages)
            total_errors += sum(1 for msg in messages if msg.has_errors)
        
        return {
            'total_sessions': len(sessions),
            'total_messages': total_messages,
            'total_errors': total_errors,
            'error_rate': (total_errors / total_messages * 100) if total_messages > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting session statistics: {str(e)}")
        return None
    finally:
        db_session.close()