
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from langchain_core.messages import HumanMessage, AIMessage
# from langchain.memory import ConversationBufferMemory # Not available

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Database Setup ---
Base = declarative_base()

class ChatHistory(Base):
    """SQLAlchemy model for storing chat history."""
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True)
    role = Column(String(50), nullable=False)  # 'user' or 'ai'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatHistory(role='{self.role}', timestamp='{self.timestamp}')>"

# Create database engine
# Using a local SQLite file 'memory.db' in the agent directory
DB_PATH = os.path.join(os.path.dirname(__file__), 'memory.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

# Create tables if they don't exist
Base.metadata.create_all(engine)

# Session factory
Session = sessionmaker(bind=engine)


# --- Memory Manager ---

class AgentMemory:
    """
    Manages conversation history using a custom buffer and SQLite persistence.
    """
    def __init__(self, k: int = 5):
        """
        Args:
            k: Number of message pairs to keep in the short-term buffer.
        """
        self.k = k
        # Simple list of messages (HumanMessage, AIMessage)
        self.buffer_messages: List[Any] = [] 
        self._load_from_db_to_buffer()

    def _load_from_db_to_buffer(self):
        """Loads the last k conversation turns from DB into the buffer."""
        session = Session()
        try:
            # Fetch last 2*k messages (user + ai)
            recent_msgs = session.query(ChatHistory).order_by(ChatHistory.timestamp.desc()).limit(self.k * 2).all()
            
            # Re-order to chronological
            recent_msgs.reverse()

            self.buffer_messages = []
            for msg in recent_msgs:
                if msg.role == 'user':
                    self.buffer_messages.append(HumanMessage(content=msg.content))
                elif msg.role == 'ai':
                    self.buffer_messages.append(AIMessage(content=msg.content))
            
            logger.info(f"Loaded {len(recent_msgs)} messages from DB into memory buffer.")
        except Exception as e:
            logger.error(f"Error loading memory from DB: {e}")
        finally:
            session.close()

    def add_to_memory(self, user_msg: str, ai_msg: str):
        """
        Savings the interaction to both SQLite and the active buffer.
        """
        # 1. Add to Buffer
        self.buffer_messages.append(HumanMessage(content=user_msg))
        self.buffer_messages.append(AIMessage(content=ai_msg))
        
        # Trim buffer if needed (keep last 2*k)
        if len(self.buffer_messages) > self.k * 2:
            self.buffer_messages = self.buffer_messages[-(self.k * 2):]

        # 2. Add to SQLite
        session = Session()
        try:
            user_entry = ChatHistory(role='user', content=user_msg)
            ai_entry = ChatHistory(role='ai', content=ai_msg)
            
            session.add(user_entry)
            session.add(ai_entry)
            session.commit()
            logger.info("Saved interaction to persistent memory.")
        except Exception as e:
            logger.error(f"Failed to save to DB: {e}")
            session.rollback()
        finally:
            session.close()

    def get_history(self) -> str:
        """
        Returns the chat history as a formatted string from the buffer.
        """
        history_str = ""
        for msg in self.buffer_messages:
            if isinstance(msg, HumanMessage):
                history_str += f"User: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                history_str += f"AI: {msg.content}\n"
        return history_str

    def clear_memory(self):
        """Clears both local buffer and database storage."""
        # Clear Buffer
        self.buffer_messages = []
        
        # Clear DB
        session = Session()
        try:
            session.query(ChatHistory).delete()
            session.commit()
            logger.info("Memory cleared successfully.")
        except Exception as e:
            logger.error(f"Error clearing memory DB: {e}")
            session.rollback()
        finally:
            session.close()

# Singleton-like usage if needed, or instantiate per session
agent_memory = AgentMemory()
