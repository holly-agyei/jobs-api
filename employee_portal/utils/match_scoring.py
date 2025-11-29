"""
Advanced match scoring algorithm (0-5 scale).
Compares user profile with job requirements.
"""
import re
from collections.abc import Iterable

from employee_portal.models.job import Job
from employee_portal.models.profile import Profile


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    return text.lower().strip()


def _normalize_list(items: Iterable[str] | None) -> set[str]:
    """Normalize a list of strings to a set of lowercase strings."""
    if not items:
        return set()
    return {_normalize_text(item) for item in items if isinstance(item, str) and item.strip()}


def _fuzzy_match(text1: str, text2: str) -> float:
    """
    Calculate fuzzy match score between two texts (0.0 to 1.0).
    Returns 1.0 for exact match, 0.5-0.9 for partial matches, 0.0 for no match.
    """
    text1 = _normalize_text(text1)
    text2 = _normalize_text(text2)
    
    # Exact match
    if text1 == text2:
        return 1.0
    
    # One contains the other
    if text1 in text2 or text2 in text1:
        return 0.8
    
    # Word-level matching
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate word overlap
    common_words = words1 & words2
    total_unique_words = len(words1 | words2)
    
    if total_unique_words == 0:
        return 0.0
    
    overlap_ratio = len(common_words) / total_unique_words
    
    # If significant overlap, return partial score
    if overlap_ratio >= 0.5:
        return 0.6 + (overlap_ratio - 0.5) * 0.8  # Scale 0.5-1.0 overlap to 0.6-1.0 score
    
    return 0.0


def _extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text."""
    if not text:
        return set()
    
    # Stop words to ignore
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "should", "could", "may", "might", "must", "can", "this",
        "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
        "what", "which", "who", "when", "where", "why", "how", "all", "each",
        "every", "both", "few", "more", "most", "other", "some", "such",
        "only", "own", "same", "than", "too", "very", "just", "about", "into",
        "through", "during", "including", "against", "among", "throughout",
    }
    
    # Extract words
    words = re.findall(r'\b[a-z]+\b', text.lower())
    
    # Filter stop words and short words
    keywords = {word for word in words if word not in stop_words and len(word) >= 3}
    
    return keywords


def calculate_match_score(profile: Profile | None, job: Job) -> float:
    """
    Calculate match score between profile and job (0-5 scale).
    
    Scoring breakdown:
    - Skills matching: 3.0 points (60%) - Most important
    - Description/experience keyword matching: 1.5 points (30%)
    - Certifications matching: 0.3 points (6%)
    - Role/title alignment: 0.2 points (4%)
    
    Returns a score from 0.0 to 5.0.
    """
    if profile is None:
        return 0.0
    
    total_score = 0.0
    max_possible = 0.0
    
    # 1. Skills Matching (up to 3.0 points) - Most important factor
    profile_skills = _normalize_list(profile.skills_list)
    job_skills = _normalize_list(job.required_skills)
    
    if job_skills:
        max_possible += 3.0
        exact_matches = len(job_skills & profile_skills)
        fuzzy_score = 0.0
        
        # Check fuzzy matches for unmatched job skills
        unmatched_job_skills = job_skills - profile_skills
        for job_skill in unmatched_job_skills:
            best_match = 0.0
            for profile_skill in profile_skills:
                match_score = _fuzzy_match(profile_skill, job_skill)
                best_match = max(best_match, match_score)
            fuzzy_score += best_match * 0.7  # 70% credit for fuzzy matches
        
        # Calculate: exact matches get full points, fuzzy matches get 70% credit
        skill_score = (exact_matches + fuzzy_score) / len(job_skills)
        total_score += skill_score * 3.0
    else:
        # No skills required = give partial credit (0.5 points) since it's easier
        max_possible += 3.0
        total_score += 0.5
    
    # 2. Description/Experience Keyword Matching (up to 1.5 points)
    profile_text = ""
    if profile.summary:
        profile_text += profile.summary + " "
    if profile.transcript_summary:
        profile_text += profile.transcript_summary + " "
    if profile.experience:
        profile_text += profile.experience + " "
    
    if profile_text and job.description:
        max_possible += 1.5
        job_keywords = _extract_keywords(job.description)
        profile_keywords = _extract_keywords(profile_text)
        
        if job_keywords:
            matching_keywords = len(job_keywords & profile_keywords)
            keyword_score = matching_keywords / len(job_keywords)
            total_score += keyword_score * 1.5
        else:
            # No keywords extracted = small credit
            total_score += 0.2
    else:
        # No profile text or job description = no credit
        max_possible += 1.5
    
    # 3. Certifications Matching (up to 0.3 points) - Small weight
    profile_certs = _normalize_list(profile.certifications_list)
    job_certs = _normalize_list(job.required_certifications)
    
    if job_certs:
        max_possible += 0.3
        exact_cert_matches = len(job_certs & profile_certs)
        if exact_cert_matches > 0:
            cert_score = exact_cert_matches / len(job_certs)
            total_score += cert_score * 0.3
    else:
        # No certs required = small credit
        max_possible += 0.3
        total_score += 0.1
    
    # 4. Role/Title Alignment (up to 0.2 points) - Small weight
    max_possible += 0.2
    if job.role and profile.headline:
        job_role = _normalize_text(job.role)
        headline = _normalize_text(profile.headline)
        
        # Check if role appears in headline
        if job_role in headline:
            total_score += 0.2
        else:
            # Check word overlap
            job_words = set(job_role.split())
            headline_words = set(headline.split())
            if job_words and headline_words:
                overlap = len(job_words & headline_words)
                if overlap > 0:
                    overlap_ratio = overlap / max(len(job_words), 1)
                    total_score += overlap_ratio * 0.15
    
    # Normalize to 0-5 scale based on what's actually possible
    # This ensures scores vary based on job requirements
    if max_possible > 0:
        normalized_score = (total_score / max_possible) * 5.0
    else:
        normalized_score = 0.0
    
    # Round to 1 decimal place
    return round(min(max(normalized_score, 0.0), 5.0), 1)


def update_job_match_score(job: Job, profile: Profile | None) -> None:
    """Update the match score for a job based on the profile."""
    job.match_score = calculate_match_score(profile, job)

