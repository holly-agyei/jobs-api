from __future__ import annotations

from datetime import datetime

from employee_portal import db


class Connection(db.Model):
    __tablename__ = "connections"
    __table_args__ = (
        db.UniqueConstraint(
            "user_one_id",
            "user_two_id",
            name="uq_connections_user_pair",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_one_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_two_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_one = db.relationship(
        "User",
        foreign_keys=[user_one_id],
        back_populates="connections_one",
    )
    user_two = db.relationship(
        "User",
        foreign_keys=[user_two_id],
        back_populates="connections_two",
    )

    def counterpart_for(self, user_id: int):
        if self.user_one_id == user_id:
            return self.user_two
        if self.user_two_id == user_id:
            return self.user_one
        return None


