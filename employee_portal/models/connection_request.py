from __future__ import annotations

from datetime import datetime

from employee_portal import db


class ConnectionRequest(db.Model):
    __tablename__ = "connection_requests"
    __table_args__ = (
        db.UniqueConstraint(
            "sender_id",
            "receiver_id",
            name="uq_connection_request_sender_receiver",
        ),
    )

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
    status = db.Column(db.String(20), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    responded_at = db.Column(db.DateTime)

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_connection_requests",
    )
    receiver = db.relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_connection_requests",
    )

    def mark_accepted(self):
        self.status = "accepted"
        self.responded_at = datetime.utcnow()

    def mark_declined(self):
        self.status = "declined"
        self.responded_at = datetime.utcnow()


