from __future__ import annotations

import logging
import os

from flask import current_app

try:  # pragma: no cover - optional dependency at runtime
    import google.generativeai as genai
    from google.api_core import exceptions as google_exceptions
except Exception:  # pragma: no cover
    genai = None  # type: ignore[assignment]
    google_exceptions = Exception  # type: ignore[assignment, misc]


def _get_gemini_client():
    """
    Configure and return Gemini client.
    Raises RuntimeError if library is missing or API key is not set.
    """
    if genai is None:
        raise RuntimeError(
            "google-generativeai package is not installed. Make sure requirements are up to date.",
        )
    
    # Get API key from Flask config or environment
    try:
        api_key = current_app.config.get("GEMINI_API_KEY", "")
    except RuntimeError:
        # Outside Flask context, use os.getenv directly
        api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured. Check your .env file or environment variables.")
    
    genai.configure(api_key=api_key)
    return genai


def generate_cover_letter(
    professional_summary: str,
    job_title: str,
    company: str,
    job_location: str,
    job_description: str,
    candidate_name: str,
    candidate_email: str,
    skills: list[str] | None = None,
    certifications: list[str] | None = None,
) -> str:
    """
    Generate a personalized cover letter using Gemini AI based on:
    - User's professional summary
    - Job title and company
    - Job description
    - User's skills and certifications
    
    Returns the generated cover letter text.
    """
    logger = getattr(current_app, "logger", logging.getLogger(__name__))
    _get_gemini_client()  # Configure API key
    
    logger.info("Generating cover letter for %s at %s", job_title, company)
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    skills_text = ", ".join(skills) if skills else "Not specified"
    certs_text = ", ".join(certifications) if certifications else "None"
    
    # Get current date in proper format
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")
    
    prompt = (
        "Write a complete, professional cover letter for a job application. "
        "The cover letter MUST include:\n"
        "1. A proper header with the candidate's name, email, and today's date\n"
        "2. The company name and location (if provided) in the recipient address\n"
        "3. A professional salutation (e.g., 'Dear Hiring Team' or 'Dear Hiring Manager')\n"
        "4. A personalized body (3-4 paragraphs, approximately 300-400 words) that:\n"
        "   - Shows genuine interest in the specific role and company\n"
        "   - Highlights relevant experience from the professional summary\n"
        "   - Connects the candidate's skills to the job requirements\n"
        "   - Uses professional, confident, and enthusiastic tone\n"
        "5. A closing with the candidate's name\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "- Use the ACTUAL candidate name provided below (do NOT use placeholders like [Your Name])\n"
        "- Use the ACTUAL candidate email provided below\n"
        f"- Use today's date: {current_date} (format as: Month Day, Year)\n"
        "- Use the ACTUAL company name and location provided\n"
        "- Do NOT leave any placeholders or brackets like [Your Name], [Date], [Company Address], [Your Email]\n"
        "- Write a complete, ready-to-use cover letter with all information filled in\n"
        "- Format the cover letter properly with header (name, email, date), recipient address, salutation, body, and signature\n"
        "- Only use information provided below. Do NOT invent details.\n\n"
        f"**Today's Date:** {current_date}\n"
        f"**Candidate Name:** {candidate_name}\n"
        f"**Candidate Email:** {candidate_email}\n"
        f"**Job Title:** {job_title}\n"
        f"**Company:** {company}\n"
        f"**Company Location:** {job_location}\n"
        f"**Job Description:**\n{job_description}\n\n"
        f"**Candidate's Professional Summary:**\n{professional_summary}\n\n"
        f"**Candidate's Skills:** {skills_text}\n"
        f"**Candidate's Certifications:** {certs_text}\n\n"
        "Write the complete cover letter now with all information filled in (no placeholders):"
    )
    
    try:
        response = model.generate_content(prompt)
        cover_letter = response.text.strip()
        
        logger.info("Cover letter generated (%d chars)", len(cover_letter))
        return cover_letter
        
    except Exception as e:
        logger.exception("Failed to generate cover letter: %s", e)
        raise


def generate_cover_letter_safe(
    professional_summary: str,
    job_title: str,
    company: str,
    job_location: str,
    job_description: str,
    candidate_name: str,
    candidate_email: str,
    skills: list[str] | None = None,
    certifications: list[str] | None = None,
) -> str | None:
    """
    Wrapper that never raises in production routes.
    Logs any error and returns None on failure.
    """
    logger = getattr(current_app, "logger", logging.getLogger(__name__))
    try:
        return generate_cover_letter(
            professional_summary=professional_summary,
            job_title=job_title,
            company=company,
            job_location=job_location,
            job_description=job_description,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            skills=skills,
            certifications=certifications,
        )
    except RuntimeError as exc:
        error_msg = str(exc)
        if "GEMINI_API_KEY" in error_msg:
            logger.error("Gemini API key not configured: %s", exc)
        else:
            logger.error("Runtime error during cover letter generation: %s", exc)
        return None
    except google_exceptions.GoogleAPIError as exc:
        logger.error("Google Gemini API error: %s", exc)
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to generate cover letter: %s", exc)
        return None

