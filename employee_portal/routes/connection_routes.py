from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from employee_portal import db
from employee_portal.forms import EmptyForm
from employee_portal.models.connection import Connection
from employee_portal.models.connection_request import ConnectionRequest
from employee_portal.models.user import User

connections_bp = Blueprint("connections", __name__, url_prefix="/connections")


def _ordered_pair(user_id_one: int, user_id_two: int) -> tuple[int, int]:
    return tuple(sorted((user_id_one, user_id_two)))


def _create_connection(sender_id: int, receiver_id: int) -> None:
    user_one_id, user_two_id = _ordered_pair(sender_id, receiver_id)
    existing = Connection.query.filter_by(
        user_one_id=user_one_id,
        user_two_id=user_two_id,
    ).first()
    if existing:
        return
    connection = Connection(
        user_one_id=user_one_id,
        user_two_id=user_two_id,
    )
    db.session.add(connection)


@connections_bp.route("/", methods=["GET"])
@login_required
def manage_connections():
    incoming_requests = (
        ConnectionRequest.query.filter_by(
            receiver_id=current_user.id,
            status="pending",
        )
        .order_by(ConnectionRequest.created_at.desc())
        .all()
    )
    outgoing_requests = (
        ConnectionRequest.query.filter_by(
            sender_id=current_user.id,
            status="pending",
        )
        .order_by(ConnectionRequest.created_at.desc())
        .all()
    )

    connected_users = sorted(
        current_user.connected_users(),
        key=lambda user: user.username.lower(),
    )
    connected_ids = {user.id for user in connected_users}
    pending_ids = {
        request.sender_id for request in incoming_requests
    } | {request.receiver_id for request in outgoing_requests}
    excluded_ids = connected_ids | pending_ids | {current_user.id}
    if excluded_ids:
        available_query = User.query.filter(~User.id.in_(excluded_ids))
    else:
        available_query = User.query
    available_users = available_query.order_by(User.username.asc()).all()

    form = EmptyForm()
    return render_template(
        "connections.html",
        incoming_requests=incoming_requests,
        outgoing_requests=outgoing_requests,
        connected_users=connected_users,
        available_users=available_users,
        form=form,
    )


@connections_bp.route("/request/<int:user_id>", methods=["POST"])
@login_required
def send_request(user_id: int):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash("Invalid submission.", "danger")
        return redirect(url_for("connections.manage_connections"))

    if user_id == current_user.id:
        flash("You cannot connect with yourself.", "warning")
        return redirect(url_for("connections.manage_connections"))

    target_user = User.query.get_or_404(user_id)
    if current_user.is_connected_with(target_user.id):
        flash("You are already connected.", "info")
        return redirect(url_for("connections.manage_connections"))

    existing_request = current_user.connection_request_with(target_user.id)
    if existing_request:
        if existing_request.receiver_id == current_user.id:
            # Auto-accept reciprocal pending request.
            existing_request.mark_accepted()
            _create_connection(existing_request.sender_id, existing_request.receiver_id)
            db.session.delete(existing_request)
            db.session.commit()
            flash(f"You are now connected with {target_user.username}.", "success")
        else:
            flash("Connection request already pending.", "info")
        return redirect(url_for("connections.manage_connections"))

    request_from_target = ConnectionRequest.query.filter_by(
        sender_id=target_user.id,
        receiver_id=current_user.id,
        status="pending",
    ).first()
    if request_from_target:
        request_from_target.mark_accepted()
        _create_connection(request_from_target.sender_id, request_from_target.receiver_id)
        db.session.delete(request_from_target)
        db.session.commit()
        flash(f"You are now connected with {target_user.username}.", "success")
        return redirect(url_for("connections.manage_connections"))

    connection_request = ConnectionRequest(
        sender=current_user,
        receiver=target_user,
    )
    db.session.add(connection_request)
    db.session.commit()
    flash("Connection request sent.", "success")
    return redirect(url_for("connections.manage_connections"))


@connections_bp.route("/requests/<int:request_id>/accept", methods=["POST"])
@login_required
def accept_request(request_id: int):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash("Invalid submission.", "danger")
        return redirect(url_for("connections.manage_connections"))

    connection_request = ConnectionRequest.query.get_or_404(request_id)
    if connection_request.receiver_id != current_user.id:
        flash("You are not authorized to accept this request.", "danger")
        return redirect(url_for("connections.manage_connections"))

    connection_request.mark_accepted()
    _create_connection(connection_request.sender_id, connection_request.receiver_id)
    db.session.delete(connection_request)
    db.session.commit()
    flash("Connection request accepted.", "success")
    return redirect(url_for("connections.manage_connections"))


@connections_bp.route("/requests/<int:request_id>/decline", methods=["POST"])
@login_required
def decline_request(request_id: int):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash("Invalid submission.", "danger")
        return redirect(url_for("connections.manage_connections"))

    connection_request = ConnectionRequest.query.get_or_404(request_id)
    if connection_request.receiver_id != current_user.id:
        flash("You are not authorized to decline this request.", "danger")
        return redirect(url_for("connections.manage_connections"))

    connection_request.mark_declined()
    db.session.delete(connection_request)
    db.session.commit()
    flash("Connection request declined.", "info")
    return redirect(url_for("connections.manage_connections"))


@connections_bp.route("/remove/<int:user_id>", methods=["POST"])
@login_required
def remove_connection(user_id: int):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash("Invalid submission.", "danger")
        return redirect(url_for("connections.manage_connections"))

    if user_id == current_user.id:
        flash("Invalid connection selection.", "danger")
        return redirect(url_for("connections.manage_connections"))

    target_user = User.query.get_or_404(user_id)
    connection = current_user.active_connection_record(target_user.id)
    if connection is None:
        flash("No active connection found.", "warning")
        return redirect(url_for("connections.manage_connections"))

    db.session.delete(connection)
    # Remove any lingering requests between the pair.
    ConnectionRequest.query.filter(
        ConnectionRequest.sender_id.in_([current_user.id, target_user.id]),
        ConnectionRequest.receiver_id.in_([current_user.id, target_user.id]),
    ).delete(synchronize_session="fetch")
    db.session.commit()

    flash("Connection removed.", "info")
    return redirect(url_for("connections.manage_connections"))

