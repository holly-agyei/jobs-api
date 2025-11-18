from datetime import datetime

from flask_login import UserMixin

from employee_portal import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profile = db.relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    applications = db.relationship(
        "Application",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    connections_one = db.relationship(
        "Connection",
        foreign_keys="Connection.user_one_id",
        back_populates="user_one",
        cascade="all, delete-orphan",
    )
    connections_two = db.relationship(
        "Connection",
        foreign_keys="Connection.user_two_id",
        back_populates="user_two",
        cascade="all, delete-orphan",
    )
    sent_connection_requests = db.relationship(
        "ConnectionRequest",
        foreign_keys="ConnectionRequest.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan",
    )
    received_connection_requests = db.relationship(
        "ConnectionRequest",
        foreign_keys="ConnectionRequest.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan",
    )
    sent_messages = db.relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.sender_id",
        cascade="all, delete-orphan",
    )
    received_messages = db.relationship(
        "Message",
        back_populates="receiver",
        foreign_keys="Message.receiver_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def set_password(self, password: str) -> None:
        from werkzeug.security import generate_password_hash  # noqa: WPS433

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        from werkzeug.security import check_password_hash  # noqa: WPS433

        return check_password_hash(self.password_hash, password)

    @property
    def connections(self):
        return list(self.connections_one + self.connections_two)

    def connected_users(self):
        partners = []
        for connection in self.connections_one:
            partners.append(connection.user_two)
        for connection in self.connections_two:
            partners.append(connection.user_one)
        return partners

    def is_connected_with(self, user_id: int) -> bool:
        return any(
            connection.user_two_id == user_id for connection in self.connections_one
        ) or any(connection.user_one_id == user_id for connection in self.connections_two)

    def connection_request_with(self, user_id: int):
        for request in self.sent_connection_requests:
            if request.receiver_id == user_id and request.status == "pending":
                return request
        for request in self.received_connection_requests:
            if request.sender_id == user_id and request.status == "pending":
                return request
        return None

    def active_connection_record(self, user_id: int):
        for connection in self.connections_one:
            if connection.user_two_id == user_id:
                return connection
        for connection in self.connections_two:
            if connection.user_one_id == user_id:
                return connection
        return None

