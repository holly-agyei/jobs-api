from __future__ import annotations

from collections.abc import Iterable

from flask import current_app




def parse_comma_separated(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [segment.strip() for segment in raw.split(",") if segment.strip()]




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

