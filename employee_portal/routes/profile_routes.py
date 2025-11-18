import os
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from employee_portal import db
from employee_portal.forms import ProfileForm
from employee_portal.models.profile import Profile
from employee_portal.utils.helpers import ensure_profile_lists, parse_comma_separated

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/", methods=["GET", "POST"])
@login_required
def manage_profile():
    profile = current_user.profile
    form = ProfileForm()

    if form.validate_on_submit():
        if profile is None:
            profile = Profile(user=current_user)
            db.session.add(profile)

        profile.headline = form.headline.data
        profile.summary = form.summary.data
        profile.skills = parse_comma_separated(form.skills.data)
        profile.certifications = parse_comma_separated(form.certifications.data)
        profile.resume_link = form.resume_link.data
        profile.experience = form.experience.data
        ensure_profile_lists(profile)

        if form.photo.data:
            upload_folder = current_app.config["PROFILE_UPLOAD_FOLDER"]
            os.makedirs(upload_folder, exist_ok=True)
            filename = secure_filename(form.photo.data.filename or "")
            if filename:
                ext = filename.rsplit(".", 1)[-1].lower()
                unique_name = f"{uuid4().hex}.{ext}"
                form.photo.data.save(os.path.join(upload_folder, unique_name))
                profile.photo_filename = unique_name

        db.session.commit()
        flash("Profile saved successfully.", "success")
        return redirect(url_for("profile.manage_profile"))

    if not form.is_submitted() and profile:
        form.headline.data = profile.headline
        form.summary.data = profile.summary
        form.skills.data = ", ".join(profile.skills_list)
        form.certifications.data = ", ".join(profile.certifications_list)
        form.resume_link.data = profile.resume_link
        form.experience.data = profile.experience

    return render_template("profile.html", form=form, profile=profile)


@profile_bp.route("/delete", methods=["POST"])
@login_required
def delete_profile():
    profile = current_user.profile
    if profile:
        db.session.delete(profile)
        db.session.commit()
        flash("Profile deleted.", "info")
    else:
        flash("No profile to delete.", "warning")
    return redirect(url_for("profile.manage_profile"))

