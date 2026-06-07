from app.db.database import SessionLocal
from app.chat.models import ChatMessageDB

class ChatService:

    @staticmethod
    def get_messages(room_id: str):

        db = SessionLocal()

        try:
            return (
                db.query(ChatMessageDB)
                .filter(ChatMessageDB.room_id == room_id)
                .order_by(ChatMessageDB.id.asc())
                .all()
            )
        finally:
            db.close()

    @staticmethod
    def save_message(
        room_id: str,
        sender: str,
        content: str
    ):

        db = SessionLocal()

        try:
            msg = ChatMessageDB(
                room_id=room_id,
                sender=sender,
                content=content
            )

            db.add(msg)
            db.commit()

        finally:
            db.close()