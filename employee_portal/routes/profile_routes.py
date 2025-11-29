import os
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from employee_portal import db
from employee_portal.forms import ProfileForm
from employee_portal.models.profile import Profile
from employee_portal.services.transcription_service import (
    transcribe_and_extract_profile_safe,
)
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

        # Only set these if video wasn't uploaded (video takes priority)
        # These will be set later if video is uploaded
        if not form.video.data:
            profile.headline = form.headline.data
            profile.skills = parse_comma_separated(form.skills.data)
            profile.certifications = parse_comma_separated(form.certifications.data)
            profile.experience = form.experience.data
        
        # Resume link can always be updated
        profile.resume_link = form.resume_link.data
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

        # Handle optional 30-second video intro - this is the PRIMARY input method
        video_uploaded = False
        if form.video.data:
            video_folder = current_app.config["VIDEO_UPLOAD_FOLDER"]
            os.makedirs(video_folder, exist_ok=True)
            raw_name = secure_filename(form.video.data.filename or "")
            if raw_name:
                v_ext = raw_name.rsplit(".", 1)[-1].lower()
                unique_video = f"{uuid4().hex}.{v_ext}"
                video_path = os.path.join(video_folder, unique_video)
                form.video.data.save(video_path)
                profile.video_filename = unique_video
                video_uploaded = True

                # Transcribe + extract ALL profile data using AI
                transcript, profile_data = transcribe_and_extract_profile_safe(video_path)
                if transcript:
                    profile.video_transcript = transcript
                
                if profile_data:
                    # Auto-populate ALL fields from AI-extracted data
                    if profile_data.get("headline"):
                        profile.headline = profile_data["headline"]
                    if profile_data.get("summary"):
                        profile.summary = profile_data["summary"]
                        profile.transcript_summary = profile_data["summary"]
                    if profile_data.get("skills"):
                        profile.skills = profile_data["skills"]
                    if profile_data.get("certifications"):
                        profile.certifications = profile_data["certifications"]
                    if profile_data.get("experience"):
                        profile.experience = profile_data["experience"]
                    
                    flash("Profile automatically populated from your video introduction!", "success")
                elif transcript:
                    # Fallback: if extraction failed but we have transcript, at least save it
                    flash("Video transcribed. Please complete your profile fields manually.", "info")
                else:
                    flash(
                        "Video uploaded, but automatic transcription failed. "
                        "You can try again later.",
                        "warning",
                    )

        # Only update fields from form if no video was uploaded (video data takes priority)
        if not video_uploaded:
            profile.headline = form.headline.data
            profile.summary = form.summary.data
            profile.skills = parse_comma_separated(form.skills.data)
            profile.certifications = parse_comma_separated(form.certifications.data)
            profile.experience = form.experience.data

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

