from datetime import datetime, timedelta
import re

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from employee_portal import db
from employee_portal.forms import JobFilterForm
from employee_portal.models.job import Job
from employee_portal.services.employer_api_service import fetch_jobs
from employee_portal.utils.helpers import update_job_match_score

job_bp = Blueprint("jobs", __name__)

_LAST_SYNC_AT: datetime | None = None


def _slugify_role(role: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", role.strip().lower())
    return normalized.strip("-") or "other"


def _sync_jobs_if_needed(force: bool = False) -> None:
    global _LAST_SYNC_AT  # noqa: PLW0603

    timeout = current_app.config.get("JOB_CACHE_TIMEOUT", 900)
    should_refresh = force
    if _LAST_SYNC_AT is None:
        should_refresh = True
    elif datetime.utcnow() - _LAST_SYNC_AT > timedelta(seconds=timeout):
        should_refresh = True

    if not should_refresh:
        return

    job_payloads = fetch_jobs()
    seen_external_ids: set[str] = set()

    for payload in job_payloads:
        external_id = str(payload["id"])
        seen_external_ids.add(external_id)
        job = Job.query.filter_by(external_id=external_id).first()
        if job is None:
            job = Job(external_id=external_id)
            db.session.add(job)

        job.title = payload["title"]
        job.role = payload["role"]
        job.company = payload.get("company", "Acme Corp")
        job.location = payload["location"]
        job.description = payload.get("description", "")
        job.required_skills = payload.get("required_skills", [])
        job.required_certifications = payload.get("required_certifications", [])
        posted_at_value = payload.get("posted_at")
        if posted_at_value:
            if isinstance(posted_at_value, str):
                job.posted_at = datetime.fromisoformat(posted_at_value)
            else:
                job.posted_at = posted_at_value

    if seen_external_ids:
        # Don't delete jobs that have applications - preserve application history
        from employee_portal.models.application import Application
        jobs_with_applications = {
            app.job_id for app in Application.query.with_entities(Application.job_id).distinct().all()
        }
        # Only delete jobs that are not in the API response AND don't have applications
        jobs_to_delete = Job.query.filter(
            ~Job.external_id.in_(seen_external_ids)
        ).all()
        for job in jobs_to_delete:
            if job.id not in jobs_with_applications:
                db.session.delete(job)
    db.session.commit()
    _LAST_SYNC_AT = datetime.utcnow()


def _apply_filters(query, form: JobFilterForm):  # noqa: ANN001
    if form.role.data:
        query = query.filter(Job.role.ilike(f"%{form.role.data.strip()}%"))
    if form.location.data:
        query = query.filter(Job.location.ilike(f"%{form.location.data.strip()}%"))
    if form.skill.data:
        query = query.filter(
            Job.required_skills.cast(db.String).ilike(f"%{form.skill.data.strip()}%"),
        )

    sort_field = form.sort_by.data or "match_score"
    if sort_field == "posted_at":
        query = query.order_by(Job.posted_at.desc())
    elif sort_field == "title":
        query = query.order_by(Job.title.asc())
    else:
        query = query.order_by(Job.match_score.desc(), Job.posted_at.desc())

    return query


@job_bp.route("/")
@login_required
def dashboard():
    _sync_jobs_if_needed()
    profile = current_user.profile
    all_jobs = Job.query.all()
    for job in all_jobs:
        update_job_match_score(job, profile)
    db.session.commit()

    placeholder_filter = Job.external_id.notlike("restored_%")
    jobs = (
        Job.query.filter(placeholder_filter)
        .order_by(Job.posted_at.desc())
        .all()
    )

    top_jobs = jobs[:6]

    # Build job categories with normalized role labels
    categories_map: dict[str, dict] = {}
    for job in jobs:
        role_label = (job.role or "Other").strip() or "Other"
        role_key = _slugify_role(role_label)
        category = categories_map.setdefault(
            role_key,
            {
                "role": role_label,
                "count": 0,
                "sample_job_id": job.id,
                "company": job.company,
            },
        )
        category["count"] += 1
        category["slug"] = role_key
    job_categories = sorted(
        categories_map.values(),
        key=lambda item: item["count"],
        reverse=True,
    )

    faqs = [
        {
            "question": "Where can I find a job via the company?",
            "answer": "Browse curated roles across all categories right from your dashboard.",
        },
        {
            "question": "How can I find jobs on the company?",
            "answer": "Use filters for role, skill, and location to narrow down opportunities.",
        },
        {
            "question": "Why should I download the app?",
            "answer": "Get instant alerts, apply faster, and stay connected with your network.",
        },
    ]

    return render_template(
        "dashboard.html",
        jobs=top_jobs,
        profile=profile,
job_categories=job_categories,
        faqs=faqs,
    )


@job_bp.route("/jobs", methods=["GET", "POST"])
@login_required
def job_list():
    _sync_jobs_if_needed()
    profile = current_user.profile
    requested_role = request.args.get("role")
    show_archived = request.args.get("archived") == "true"

    all_jobs = Job.query.all()
    for job in all_jobs:
        update_job_match_score(job, profile)
    db.session.commit()

    form = JobFilterForm()
    if requested_role and not form.is_submitted():
        form.role.data = requested_role

    placeholder_filter = Job.external_id.notlike("restored_%")
    query = Job.query.filter(placeholder_filter)
    if requested_role:
        query = query.filter(func.lower(Job.role) == requested_role.lower())

    # Filter archived jobs (older than 30 days)
    if show_archived:
        archive_threshold = datetime.utcnow() - timedelta(days=30)
        query = query.filter(Job.posted_at < archive_threshold)
        flash("Showing archived jobs (older than 30 days)", "info")
    else:
        # Show active jobs (posted within last 30 days)
        archive_threshold = datetime.utcnow() - timedelta(days=30)
        query = query.filter(Job.posted_at >= archive_threshold)

    if form.validate_on_submit():
        query = _apply_filters(query, form)
    else:
        query = query.order_by(Job.match_score.desc(), Job.posted_at.desc())

    jobs = query.all()

    return render_template(
        "jobs.html",
        jobs=jobs,
        form=form,
        profile=profile,
        active_role=requested_role,
        show_archived=show_archived,
    )


@job_bp.route("/jobs/<int:job_id>")
@login_required
def job_detail(job_id: int):
    _sync_jobs_if_needed()
    job = Job.query.get_or_404(job_id)
    update_job_match_score(job, current_user.profile)
    db.session.commit()
    return render_template("job_detail.html", job=job)


@job_bp.route("/jobs/refresh", methods=["POST"])
@login_required
def refresh_jobs():
    _sync_jobs_if_needed(force=True)
    flash("Job listings refreshed from mock employer API.", "success")
    return redirect(url_for("jobs.job_list"))

