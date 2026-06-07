# models.py
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
# database.py에서 Base를 가져옵니다.
from database import Base

class ChatMessageDB(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, index=True)      
    sender = Column(String)                   
    content = Column(Text)                    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)