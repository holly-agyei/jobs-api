from __future__ import annotations

import requests
from datetime import datetime, timedelta
from random import randint

from flask import current_app

MOCK_JOBS = [
    {
        "id": 1001,
        "title": "Sous Chef",
        "role": "Chef",
        "company": "Culinary Collective",
        "location": "New York, NY",
        "description": "Support lead chef with daily kitchen operations and menu execution.",
        "required_skills": ["Cooking", "Food Safety", "Inventory Management"],
        "required_certifications": ["Food Handler Certification"],
        "posted_at": datetime.utcnow() - timedelta(days=2),
    },
    {
        "id": 1002,
        "title": "Front Desk Cashier",
        "role": "Cashier",
        "company": "Gourmet Market",
        "location": "Chicago, IL",
        "description": "Assist guests with purchases, manage the register, and maintain customer satisfaction.",
        "required_skills": ["Customer Service", "Cash Handling", "Food Safety"],
        "required_certifications": ["Food Handler Certification"],
        "posted_at": datetime.utcnow() - timedelta(days=5),
    },
    {
        "id": 1003,
        "title": "Delivery Driver",
        "role": "Driver",
        "company": "FastBite",
        "location": "Los Angeles, CA",
        "description": "Deliver gourmet meals across the metro area ensuring safety and quality.",
        "required_skills": ["Driving", "Customer Service", "Food Safety"],
        "required_certifications": ["Driver's License"],
        "posted_at": datetime.utcnow() - timedelta(days=1),
    },
    {
        "id": 1004,
        "title": "Regional Marketing Specialist",
        "role": "Marketing Specialist",
        "company": "TasteWave",
        "location": "Austin, TX",
        "description": "Develop campaigns and manage brand engagement initiatives.",
        "required_skills": ["Marketing", "Customer Service", "Food Safety"],
        "required_certifications": ["Marketing Certification"],
        "posted_at": datetime.utcnow() - timedelta(days=3),
    },
    {
        "id": 1005,
        "title": "Food Safety Inspector",
        "role": "Food Safety Inspector",
        "company": "SafeServe Inc.",
        "location": "Seattle, WA",
        "description": "Inspect partner facilities to maintain compliance with safety standards.",
        "required_skills": ["Food Safety", "Inventory Management"],
        "required_certifications": ["Food Safety Certification"],
        "posted_at": datetime.utcnow() - timedelta(days=4),
    },
    {
        "id": 1006,
        "title": "Fire Safety Inspector",
        "role": "Fire Safety Inspector",
        "company": "SecureHeat",
        "location": "Denver, CO",
        "description": "Perform safety inspections and ensure adherence to municipal codes.",
        "required_skills": ["Gas leak tests", "City code adherence"],
        "required_certifications": ["CGLI Inspector"],
        "posted_at": datetime.utcnow() - timedelta(days=6),
    },
]


def _get_api_config() -> dict:
    """Get API configuration from app config"""
    return {
        "base_url": current_app.config.get("EMPLOYER_API_BASE_URL", ""),
        "api_key": current_app.config.get("EMPLOYER_API_KEY", ""),
        "timeout": current_app.config.get("EMPLOYER_API_TIMEOUT", 10),
        "enabled": current_app.config.get("EMPLOYER_API_ENABLED", False),
    }


def _fetch_mock_jobs() -> list[dict]:
    """Fallback: Return mock job data"""
    current_app.logger.debug("Using mock employer API (fallback)")
    jobs = []
    for job in MOCK_JOBS:
        job_copy = job.copy()
        job_copy["posted_at"] = job["posted_at"].isoformat()
        jobs.append(job_copy)
    return jobs


def fetch_jobs() -> list[dict]:
    """
    Fetch jobs from the real Employer API.
    Falls back to mock data if API is disabled or unavailable.
    """
    config = _get_api_config()

    # Debug logging
    current_app.logger.info(
        f"API Config - enabled: {config['enabled']}, base_url: {config['base_url']}"
    )

    # Use mock if API is not enabled
    if not config["enabled"] or not config["base_url"]:
        current_app.logger.warning(
            f"API not enabled or base_url missing. enabled={config['enabled']}, base_url={config['base_url']}"
        )
        return _fetch_mock_jobs()

    try:
        api_url = f"{config['base_url']}/jobs"
        current_app.logger.info(f"Fetching jobs from: {api_url}")

        # GET /jobs doesn't require authentication
        response = requests.get(
            api_url,
            timeout=config["timeout"],
        )
        response.raise_for_status()

        jobs = response.json()
        current_app.logger.info(f"Fetched {len(jobs)} jobs from Employer API")
        
        # Return jobs even if empty - don't fallback to mock when API is enabled
        return jobs

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to fetch jobs from Employer API: {e}")
        current_app.logger.warning("Falling back to mock job data")
        return _fetch_mock_jobs()


def post_application(application_data: dict) -> dict:
    """
    Submit application to the real Employer API.
    Falls back to mock response if API is disabled or unavailable.
    """
    config = _get_api_config()

    # Use mock if API is not enabled
    if not config["enabled"] or not config["base_url"]:
        return _post_mock_application(application_data)

    try:
        # POST /applications doesn't require authentication
        headers = {"Content-Type": "application/json"}

        current_app.logger.info(
            f"Submitting application to {config['base_url']}/applications: {application_data}"
        )

        response = requests.post(
            f"{config['base_url']}/applications",
            json=application_data,
            headers=headers,
            timeout=config["timeout"],
        )

        # Log response details
        current_app.logger.info(
            f"API response status: {response.status_code}, body: {response.text[:200]}"
        )

        # Parse JSON response
        result = response.json()

        # Check if API returned success: false (even with 200 status)
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            current_app.logger.error(f"API returned error: {error_msg}")
            return {"success": False, "error": error_msg}

        # Check HTTP status code
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            # If HTTP error, we already have the JSON response above
            error_msg = result.get("error", f"HTTP {response.status_code}")
            current_app.logger.error(f"HTTP error: {error_msg}")
            return {"success": False, "error": error_msg}

        # Success!
        current_app.logger.info(
            f"Application submitted successfully: {result.get('application_id')}"
        )
        return result

    except requests.exceptions.HTTPError as e:
        error_msg = f"API returned error: {e.response.status_code}"
        try:
            error_data = e.response.json()
            error_msg = error_data.get("error", error_msg)
            current_app.logger.error(
                f"HTTP error submitting application: {error_msg}, status: {e.response.status_code}"
            )
        except:
            current_app.logger.error(
                f"HTTP error submitting application: {e.response.status_code}, body: {e.response.text[:200]}"
            )
        return {"success": False, "error": error_msg}

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Network error submitting application: {e}")
        return {"success": False, "error": "Network error. Please try again later."}


def _post_mock_application(application_data: dict) -> dict:
    """Fallback: Return mock application response"""
    current_app.logger.info(
        "Mock employer API received application for job %s from user %s",
        application_data.get("job_id"),
        application_data.get("user_id"),
    )
    return {"success": True, "application_id": randint(10000, 99999)}

