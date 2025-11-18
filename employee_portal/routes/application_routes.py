from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from employee_portal import db
from employee_portal.forms import ApplicationForm
from employee_portal.models.application import Application
from employee_portal.models.job import Job
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
        application = Application(
            user=current_user,
            job=job,
            resume_link=form.resume_link.data,
            skills=profile.skills_list,
            certifications=profile.certifications_list,
        )
        db.session.add(application)
        db.session.commit()

        application_payload = {
            "job_id": int(job.external_id),  # Convert to int for API
            "user_id": current_user.id,
            "resume_link": form.resume_link.data,
            "skills": profile.skills_list,
            "certifications": profile.certifications_list,
            "cover_letter": form.cover_letter.data,
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
        form.resume_link.data = profile.resume_link

    return render_template("apply.html", form=form, job=job, profile=profile)


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

