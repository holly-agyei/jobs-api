"""
Company Rating Service
Fetches company ratings from Yelp API and web scraping.
"""
import logging
import re
from typing import Any

import nltk
import requests
from bs4 import BeautifulSoup
from flask import current_app
from googlesearch import search
from textblob import TextBlob

# Download NLTK data if needed
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

logger = logging.getLogger(__name__)

# Yelp API Key - should be in environment variables
YELP_API_KEY = "Ikthrb2yLGz0G4SYqB6lGjpNdoCb94XVRRBrUwfDDc6zX6cUwjoUYUw8gn1W3-DDO0IDn2drx4gmI8O-BLMYJbrLyEsZZkCpkqMbjlkJtr25K2MRbBehD_9CoCIcaXYx"

REVIEW_KEYWORDS = [
    "review",
    "reviews",
    "customer",
    "client",
    "feedback",
    "testimonial",
    "rating",
    "experience",
    "service",
]


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def yelp_search(company: str, location: str = "United States") -> dict[str, Any] | None:
    """Search for company on Yelp."""
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": company, "location": location}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            logger.warning(f"Yelp API returned status {r.status_code} for {company}")
            return None

        data = r.json()
        if not data.get("businesses"):
            return None

        # Strict matching
        company_clean = company.lower().replace("inc", "").replace("llc", "").strip()

        for business in data["businesses"]:
            name_clean = business["name"].lower()
            if company_clean in name_clean or name_clean in company_clean:
                return business

        return None
    except Exception as e:
        logger.exception(f"Error searching Yelp for {company}: {e}")
        return None


def yelp_reviews(business_id: str) -> list[dict[str, Any]]:
    """Get reviews from Yelp for a business."""
    url = f"https://api.yelp.com/v3/businesses/{business_id}/reviews"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return []

        data = r.json()
        reviews = data.get("reviews", [])
        if not reviews:
            return []

        return [
            {"review": rev["text"], "rating": rev["rating"]}
            for rev in reviews[:3]
        ]
    except Exception as e:
        logger.exception(f"Error fetching Yelp reviews for {business_id}: {e}")
        return []


def scrape_reviews_from_web(company: str) -> list[str] | None:
    """Scrape reviews from web search results."""
    query = f"{company} customer reviews testimonials feedback"

    try:
        links = list(search(query, num_results=8))
    except Exception as e:
        logger.warning(f"Error searching web for {company}: {e}")
        return None

    extracted_sentences = []

    for url in links[:5]:
        try:
            response = requests.get(
                url,
                timeout=7,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )

            soup = BeautifulSoup(response.text, "lxml")

            # Collect review-like elements
            candidates = []

            # 1. Paragraphs
            candidates += soup.find_all("p")

            # 2. Elements with review-related classes
            classes_to_check = ["review", "testimonial", "comment", "feedback"]
            for cls in classes_to_check:
                candidates += soup.find_all(class_=re.compile(cls, re.I))

            # Extract text and clean it
            for candidate in candidates:
                text = clean_text(candidate.get_text())
                if any(keyword in text.lower() for keyword in REVIEW_KEYWORDS):
                    if 30 < len(text) < 350:
                        extracted_sentences.append(text)

        except Exception as e:
            logger.debug(f"Error scraping {url}: {e}")
            continue

    # Return the top 3 unique review-like sentences
    unique_reviews = list(dict.fromkeys(extracted_sentences))
    return unique_reviews[:3] if unique_reviews else None


def generate_rating(text_list: list[str]) -> float:
    """Generate rating (1-5) from text using sentiment analysis."""
    if not text_list:
        return 3.0  # Neutral default

    blob = TextBlob(" ".join(text_list))
    polarity = blob.sentiment.polarity  # -1 to +1

    rating = round(((polarity + 1) / 2) * 4 + 1, 1)
    return max(1.0, min(rating, 5.0))


def get_company_rating(company: str) -> dict[str, Any]:
    """
    Get company rating from Yelp, web scraping, or AI fallback.
    Returns dict with rating, source, and reviews.
    """
    logger.info(f"Getting rating for company: {company}")

    # Try Yelp first
    business = yelp_search(company)

    if business:
        logger.info(f"Yelp match found for {company}")

        yelp_rating = business.get("rating", None)
        reviews = yelp_reviews(business["id"])

        # Yelp match + reviews available
        if reviews and len(reviews) > 0:
            avg_rating = round(sum(r["rating"] for r in reviews) / len(reviews), 1)
            return {
                "company": company,
                "source": "yelp",
                "rating": avg_rating,
                "reviews": reviews,
            }

        # Yelp match but NO REVIEWS - scrape web
        logger.info(f"Yelp has business but no reviews. Scraping web for {company}...")
        scraped = scrape_reviews_from_web(company)

        if scraped:
            return {
                "company": company,
                "source": "yelp + web_scrape",
                "rating": yelp_rating or generate_rating(scraped),
                "reviews": [{"review": s, "rating": None} for s in scraped],
            }

        # Fallback text
        fallback_txt = [
            f"{company} is listed on Yelp but no reviews were found. "
            "Public sentiment is mixed based on available info."
        ]
        generated_rating = generate_rating(fallback_txt)

        return {
            "company": company,
            "source": "yelp + ai_fallback",
            "rating": yelp_rating or generated_rating,
            "reviews": [{"review": fallback_txt[0], "rating": None}],
        }

    # No Yelp match - scrape web
    logger.info(f"No Yelp match for {company}. Scraping web...")
    scraped = scrape_reviews_from_web(company)

    if scraped:
        rating = generate_rating(scraped)
        return {
            "company": company,
            "source": "web_scrape",
            "rating": rating,
            "reviews": [{"review": s, "rating": None} for s in scraped],
        }

    # Final fallback - AI sentiment
    logger.info(f"No web data for {company}. Using AI fallback.")
    fallback_text = [
        f"Public information on {company} is extremely limited. "
        "Online sentiment appears neutral based on scarce available mentions."
    ]
    rating = generate_rating(fallback_text)

    return {
        "company": company,
        "source": "ai_fallback",
        "rating": rating,
        "reviews": [{"review": fallback_text[0], "rating": rating}],
    }


def update_job_ratings() -> None:
    """Update ratings for all unique companies in the database."""
    from employee_portal import db
    from employee_portal.models.job import Job

    if not current_app:
        return

    # Get all unique companies
    companies = db.session.query(Job.company).distinct().all()
    company_names = [c[0] for c in companies]

    logger.info(f"Updating ratings for {len(company_names)} companies")

    # Cache ratings by company name
    ratings_cache: dict[str, float] = {}

    for company in company_names:
        if company in ratings_cache:
            rating = ratings_cache[company]
        else:
            try:
                result = get_company_rating(company)
                rating = result["rating"]
                ratings_cache[company] = rating
                logger.info(f"Company {company}: {rating} stars ({result['source']})")
            except Exception as e:
                logger.exception(f"Error getting rating for {company}: {e}")
                rating = 3.0  # Default neutral rating

        # Update all jobs for this company
        Job.query.filter_by(company=company).update({"rating": rating})

    db.session.commit()
    logger.info("Job ratings updated successfully")

