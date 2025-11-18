from datetime import datetime

from employee_portal import db


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sender = db.relationship(
        "User",
        back_populates="sent_messages",
        foreign_keys=[sender_id],
    )
    receiver = db.relationship(
        "User",
        back_populates="received_messages",
        foreign_keys=[receiver_id],
    )

    def __repr__(self) -> str:
        return f"<Message {self.id} from={self.sender_id} to={self.receiver_id}>"

