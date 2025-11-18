from __future__ import annotations

from collections.abc import Iterable

from flask import current_app

from employee_portal.models.job import Job
from employee_portal.models.profile import Profile

JOB_ROLE_REQUIREMENTS = {
    "Chef": {
        "skills": {"cooking", "food safety", "inventory management"},
        "certifications": {"food handler certification"},
    },
    "Cashier": {
        "skills": {"customer service", "cash handling", "food safety"},
        "certifications": {"food handler certification"},
    },
    "Driver": {
        "skills": {"driving", "customer service", "food safety"},
        "certifications": {"driver's license"},
    },
    "Marketing Specialist": {
        "skills": {"marketing", "customer service", "food safety"},
        "certifications": {"marketing certification"},
    },
    "Food Safety Inspector": {
        "skills": {"food safety", "inventory management"},
        "certifications": {"food safety certification"},
    },
    "Fire Safety Inspector": {
        "skills": {"gas leak tests", "city code adherence"},
        "certifications": {"cgli inspector"},
    },
}


def _normalize_iterable(items: Iterable[str] | None) -> set[str]:
    if not items:
        return set()
    return {
        item.strip().lower()
        for item in items
        if isinstance(item, str) and item.strip()
    }


def parse_comma_separated(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [segment.strip() for segment in raw.split(",") if segment.strip()]


def calculate_match_score(
    profile: Profile | None,
    job: Job,
) -> float:
    if profile is None:
        return 0.0

    profile_skills = _normalize_iterable(profile.skills_list)
    profile_certs = _normalize_iterable(profile.certifications_list)
    job_skills = _normalize_iterable(job.required_skills)
    job_certs = _normalize_iterable(job.required_certifications)

    if not job_skills and not job_certs:
        return 0.0

    skill_match = len(job_skills & profile_skills)
    cert_match = len(job_certs & profile_certs)
    total_requirements = max(len(job_skills) + len(job_certs), 1)
    base_score = (skill_match + cert_match) / total_requirements

    role_requirements = JOB_ROLE_REQUIREMENTS.get(job.role)
    if role_requirements:
        role_skills = role_requirements["skills"]
        role_certs = role_requirements["certifications"]
        role_skill_match = len(role_skills & profile_skills)
        role_cert_match = len(role_certs & profile_certs)
        role_total = max(len(role_skills) + len(role_certs), 1)
        role_score = (role_skill_match + role_cert_match) / role_total
        base_score = (base_score * 0.6) + (role_score * 0.4)

    return round(min(base_score, 1.0), 2)


def update_job_match_score(job: Job, profile: Profile | None) -> None:
    job.match_score = calculate_match_score(profile, job)


def ensure_profile_lists(profile: Profile) -> None:
    profile.skills = profile.skills_list
    profile.certifications = profile.certifications_list


def profile_snapshot(profile: Profile) -> dict[str, list[str]]:
    return {
        "skills": profile.skills_list,
        "certifications": profile.certifications_list,
    }


def log_info(message: str) -> None:
    current_app.logger.info(message)

