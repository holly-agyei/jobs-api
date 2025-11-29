from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from employee_portal import csrf, db
from employee_portal.forms import ApplicationForm
from employee_portal.models.application import Application
from employee_portal.models.job import Job
from employee_portal.services.cover_letter_service import generate_cover_letter_safe
from employee_portal.services.employer_api_service import post_application

application_bp = Blueprint("applications", __name__, url_prefix="/applications")


@application_bp.route("/")
@login_required
def list_applications():
    # Try to restore missing jobs for orphaned applications
    from employee_portal.routes.job_routes import _sync_jobs_if_needed
    
    # Sync jobs first to get latest from API
    _sync_jobs_if_needed(force=True)
    
    # Find applications with missing jobs and try to restore them
    orphaned_applications = (
        Application.query
        .filter_by(user_id=current_user.id)
        .outerjoin(Job, Application.job_id == Job.id)
        .filter(Job.id.is_(None))
        .all()
    )
    
    # Try to restore jobs by creating placeholder jobs
    if orphaned_applications:
        try:
            from employee_portal.services.employer_api_service import fetch_jobs
            from datetime import datetime
            
            api_jobs = fetch_jobs()
            existing_job_ids = {job.id for job in Job.query.all()}
            
            # Try to match orphaned applications with jobs from API
            for app in orphaned_applications:
                if app.job_id not in existing_job_ids:
                    # Try to find a matching job in API based on skills/certifications
                    matched = False
                    app_skills = set(app.skills) if isinstance(app.skills, list) else set()
                    app_certs = set(app.certifications) if isinstance(app.certifications, list) else set()
                    
                    for api_job in api_jobs:
                        api_skills = set(api_job.get("required_skills", []))
                        api_certs = set(api_job.get("required_certifications", []))
                        
                        # If skills and certs match, this might be the same job
                        if app_skills == api_skills and app_certs == api_certs:
                            # Create the job from API data
                            job = Job(
                                external_id=str(api_job["id"]),
                                title=api_job.get("title", "Unknown Job"),
                                role=api_job.get("role", "Unknown"),
                                company=api_job.get("company", "Unknown Company"),
                                location=api_job.get("location", "Unknown"),
                                description=api_job.get("description", ""),
                                required_skills=api_job.get("required_skills", []),
                                required_certifications=api_job.get("required_certifications", []),
                            )
                            posted_at = api_job.get("posted_at")
                            if posted_at:
                                if isinstance(posted_at, str):
                                    job.posted_at = datetime.fromisoformat(posted_at)
                                else:
                                    job.posted_at = posted_at
                            
                            db.session.add(job)
                            db.session.flush()  # Get the new job ID
                            
                            # Update application to point to the restored job
                            app.job_id = job.id
                            matched = True
                            break
                    
                    # If no match found, create a minimal placeholder
                    if not matched:
                        placeholder_job = Job(
                            external_id=f"restored_{app.id}",
                            title="Job (Details Unavailable)",
                            role="Unknown",
                            company="Unknown Company",
                            location="Unknown",
                            description="This job listing is no longer available. The application was preserved for your records.",
                            required_skills=app.skills if isinstance(app.skills, list) else [],
                            required_certifications=app.certifications if isinstance(app.certifications, list) else [],
                            posted_at=app.submitted_at,  # Use application date as fallback
                        )
                        db.session.add(placeholder_job)
                        db.session.flush()
                        app.job_id = placeholder_job.id
            
            db.session.commit()
        except Exception as e:
            # If restoration fails, just continue - we'll show the error message
            current_app.logger.warning(f"Failed to restore missing jobs: {e}")
            db.session.rollback()
    
    applications = (
        Application.query.options(joinedload(Application.job))
        .filter_by(user_id=current_user.id)
        .order_by(Application.submitted_at.desc())
        .all()
    )
    return render_template("applications.html", applications=applications)


@application_bp.route("/apply/<int:job_id>", methods=["GET", "POST"])
@login_required
def apply(job_id: int):
    job = Job.query.get_or_404(job_id)
    profile = current_user.profile

    if profile is None or not profile.is_complete:
        flash("Please complete your profile before applying to jobs.", "warning")
        return redirect(url_for("profile.manage_profile"))

    existing_application = Application.query.filter_by(
        user_id=current_user.id,
        job_id=job.id,
    ).first()
    if existing_application:
        flash("You have already applied for this job.", "info")
        return redirect(url_for("applications.list_applications"))

    form = ApplicationForm()
    if form.validate_on_submit():
        # Use form resume_link if provided, otherwise use profile resume_link, or empty string
        # Use empty string instead of None to work with existing database NOT NULL constraint
        resume_link = ""
        if form.resume_link.data:
            resume_link = form.resume_link.data.strip()
        elif profile.resume_link:
            resume_link = profile.resume_link.strip()
        
        application = Application(
            user=current_user,
            job=job,
            resume_link=resume_link,
            skills=profile.skills_list,
            certifications=profile.certifications_list,
        )
        db.session.add(application)
        db.session.commit()

        application_payload = {
            "job_id": int(job.external_id),  # Convert to int for API
            "user_id": current_user.id,
            "resume_link": resume_link or "",  # API might need empty string instead of None
            "skills": profile.skills_list,
            "certifications": profile.certifications_list,
            "cover_letter": form.cover_letter.data or "",
        }
        result = post_application(application_payload)

        # Check if application was successfully submitted to API
        if not result.get("success", False):
            error_msg = result.get("error", "Failed to submit application")
            flash(f"Application saved locally but API error: {error_msg}", "warning")
        else:
            flash("Application submitted successfully.", "success")
        return redirect(url_for("applications.list_applications"))

    if request.method == "GET":
        form.resume_link.data = profile.resume_link or ""

    return render_template("apply.html", form=form, job=job, profile=profile)


@application_bp.route("/generate-cover-letter/<int:job_id>", methods=["POST"])
@login_required
@csrf.exempt
def generate_cover_letter_route(job_id: int):
    """Generate a cover letter using AI for the specified job."""
    try:
        job = Job.query.get_or_404(job_id)
        profile = current_user.profile

        current_app.logger.info(f"Cover letter generation request - User: {current_user.id}, Job: {job_id}")

        if profile is None:
            current_app.logger.warning(f"User {current_user.id} has no profile")
            return jsonify({"error": "Please complete your profile first."}), 400

        # Use transcript_summary if available, otherwise use summary
        professional_summary = profile.transcript_summary or profile.summary or ""
        
        current_app.logger.info(f"Profile check - headline: {bool(profile.headline)}, summary: {len(professional_summary)} chars, skills: {len(profile.skills_list) if profile.skills_list else 0}")
        
        # Check for professional summary
        if not professional_summary or not professional_summary.strip():
            current_app.logger.warning(f"User {current_user.id} has no professional summary - transcript_summary: {bool(profile.transcript_summary)}, summary: {bool(profile.summary)}")
            return jsonify({"error": "Please add a professional summary to your profile first. Upload a video or add a summary manually."}), 400

        # Skills are optional but helpful
        skills_list = profile.skills_list or []

        current_app.logger.info(f"Generating cover letter - summary length: {len(professional_summary)}")

        cover_letter = generate_cover_letter_safe(
            professional_summary=professional_summary,
            job_title=job.title,
            company=job.company,
            job_location=job.location,
            job_description=job.description or "No description available",
            candidate_name=current_user.username,
            candidate_email=current_user.email,
            skills=skills_list,
            certifications=profile.certifications_list or [],
        )

        if cover_letter:
            current_app.logger.info(f"Cover letter generated successfully - {len(cover_letter)} chars")
            return jsonify({"cover_letter": cover_letter})
        else:
            current_app.logger.error("Cover letter generation returned None")
            return jsonify({"error": "Failed to generate cover letter. Please check your API key and try again."}), 500
            
    except Exception as e:
        current_app.logger.exception(f"Error generating cover letter: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@application_bp.route("/withdraw/<int:application_id>", methods=["POST"])
@login_required
def withdraw_application(application_id: int):
    application = Application.query.get_or_404(application_id)
    
    # Ensure user can only withdraw their own applications
    if application.user_id != current_user.id:
        flash("You can only withdraw your own applications.", "danger")
        return redirect(url_for("applications.list_applications"))
    
    # Only allow withdrawal if status is still "submitted"
    if application.status not in ["submitted", "pending"]:
        flash(f"Cannot withdraw application with status: {application.status}", "warning")
        return redirect(url_for("applications.list_applications"))
    
    application.status = "withdrawn"
    db.session.commit()
    flash("Application withdrawn successfully.", "success")
    return redirect(url_for("applications.list_applications"))


@application_bp.route("/admin")
@login_required
def admin_dashboard():
    applications = (
        Application.query.options(joinedload(Application.job), joinedload(Application.user))
        .order_by(Application.submitted_at.desc())
        .all()
    )
    return render_template("admin_dashboard.html", applications=applications)

