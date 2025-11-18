from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_socketio import emit, join_room
from sqlalchemy import and_, or_

from employee_portal import db, socketio
from employee_portal.forms import MessageForm
from employee_portal.models.message import Message
from employee_portal.models.user import User

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def _room_name(user_id_one: int, user_id_two: int) -> str:
    ordered = sorted([user_id_one, user_id_two])
    return f"chat_{ordered[0]}_{ordered[1]}"


@chat_bp.route("/", methods=["GET", "POST"])
@login_required
def chat_home():
    connected_users = current_user.connected_users()
    selected_user_id = request.args.get("user_id", type=int)
    selected_user = None
    if selected_user_id:
        selected_user = next(
            (user for user in connected_users if user.id == selected_user_id),
            None,
        )
        if selected_user is None:
            flash("You must be connected with a user to chat.", "warning")
            return redirect(url_for("chat.chat_home"))
    elif connected_users:
        selected_user = connected_users[0]

    form = MessageForm()
    if form.validate_on_submit() and selected_user:
        if not current_user.is_connected_with(selected_user.id):
            flash("Connection required before sending messages.", "danger")
            return redirect(url_for("chat.chat_home"))

        message = Message(
            sender=current_user,
            receiver=selected_user,
            content=form.content.data,
        )
        db.session.add(message)
        db.session.commit()
        flash("Message sent.", "success")
        return redirect(url_for("chat.chat_home", user_id=selected_user.id))

    messages = []
    room = None
    if selected_user:
        room = _room_name(current_user.id, selected_user.id)
        messages = Message.query.filter(
            or_(
                and_(
                    Message.sender_id == current_user.id,
                    Message.receiver_id == selected_user.id,
                ),
                and_(
                    Message.sender_id == selected_user.id,
                    Message.receiver_id == current_user.id,
                ),
            ),
        ).order_by(Message.created_at.asc()).all()

    return render_template(
        "chat.html",
        users=connected_users,
        selected_user=selected_user,
        messages=messages,
        form=form,
        room=room,
        connection_count=len(connected_users),
    )


@socketio.on("join", namespace="/chat")
def handle_join(data: dict):  # pragma: no cover
    join_room(data["room"])


@socketio.on("send_message", namespace="/chat")
def handle_send_message(data: dict):  # pragma: no cover
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    room = data.get("room")
    content = (data.get("content") or "").strip()

    if not sender_id or not receiver_id or not room or not content:
        return

    sender = User.query.get(sender_id)
    receiver = User.query.get(receiver_id)
    if sender is None or receiver is None:
        return

    if not sender.is_connected_with(receiver.id):
        return

    message = Message(sender=sender, receiver=receiver, content=content)
    db.session.add(message)
    db.session.commit()

    emit(
        "receive_message",
        {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "timestamp": message.created_at.isoformat(),
            "sender_name": sender.username,
        },
        room=room,
    )

