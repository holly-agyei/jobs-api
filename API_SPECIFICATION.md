# Employer API Specification

This document defines the API contract between the **Employee Portal** and the **Employer Portal API**. The Employee Portal expects these two endpoints to be available.

---

## Base URL

The Employee Portal will be configured to call the Employer API at a configurable base URL (e.g., `https://api.employer-portal.com` or `http://localhost:8000`).

---

## Endpoint 1: GET /jobs

Fetches all available job postings from the Employer Portal.

### Request

- **Method:** `GET`
- **Path:** `/jobs`
- **Headers:**
  - `Content-Type: application/json`
  - (Optional) `Authorization: Bearer <token>` if authentication is required

### Response

- **Status Code:** `200 OK`
- **Content-Type:** `application/json`
- **Body:** Array of job objects

#### Job Object Structure

```json
{
  "id": 1001,
  "title": "Sous Chef",
  "role": "Chef",
  "company": "Culinary Collective",
  "location": "New York, NY",
  "description": "Support lead chef with daily kitchen operations and menu execution.",
  "required_skills": ["Cooking", "Food Safety", "Inventory Management"],
  "required_certifications": ["Food Handler Certification"],
  "posted_at": "2025-11-11T10:30:00"
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer/string | Yes | Unique identifier for the job (used as `external_id` in Employee Portal) |
| `title` | string | Yes | Job title (e.g., "Sous Chef", "Front Desk Cashier") |
| `role` | string | Yes | Job role category (e.g., "Chef", "Cashier", "Driver", "Marketing Specialist", "Food Safety Inspector", "Fire Safety Inspector") |
| `company` | string | No | Company name (defaults to "Acme Corp" if missing) |
| `location` | string | Yes | Job location (e.g., "New York, NY", "Chicago, IL") |
| `description` | string | No | Job description text (can be empty string) |
| `required_skills` | array of strings | No | List of required skills (e.g., `["Cooking", "Food Safety"]`) |
| `required_certifications` | array of strings | No | List of required certifications (e.g., `["Food Handler Certification"]`) |
| `posted_at` | string (ISO 8601) | No | Job posting date/time in ISO format (e.g., `"2025-11-11T10:30:00"`) |

#### Example Response

```json
[
  {
    "id": 1001,
    "title": "Sous Chef",
    "role": "Chef",
    "company": "Culinary Collective",
    "location": "New York, NY",
    "description": "Support lead chef with daily kitchen operations and menu execution.",
    "required_skills": ["Cooking", "Food Safety", "Inventory Management"],
    "required_certifications": ["Food Handler Certification"],
    "posted_at": "2025-11-11T10:30:00"
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
    "posted_at": "2025-11-08T14:20:00"
  }
]
```

#### Notes

- The Employee Portal will cache job listings and refresh them periodically (default: every 15 minutes).
- Jobs that no longer appear in the response will be removed from the Employee Portal's local database.
- The `id` field is used to track jobs across syncs (stored as `external_id` in the Employee Portal).

---

## Endpoint 2: POST /applications

Submits a job application from an employee to the Employer Portal.

### Request

- **Method:** `POST`
- **Path:** `/applications`
- **Headers:**
  - `Content-Type: application/json`
  - (Optional) `Authorization: Bearer <token>` if authentication is required
- **Body:** Application object (JSON)

#### Application Object Structure

```json
{
  "job_id": "1001",
  "user_id": 5,
  "resume_link": "https://example.com/resumes/user5_resume.pdf",
  "skills": ["Cooking", "Food Safety", "Inventory Management"],
  "certifications": ["Food Handler Certification"],
  "cover_letter": "I am very interested in this position..."
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_id` | integer/string | Yes | The external job ID (from the `/jobs` endpoint) |
| `user_id` | integer | Yes | The Employee Portal's internal user ID (for reference) |
| `resume_link` | string | Yes | URL or path to the employee's resume |
| `skills` | array of strings | Yes | List of skills the employee has (from their profile) |
| `certifications` | array of strings | Yes | List of certifications the employee has (from their profile) |
| `cover_letter` | string | No | Optional cover letter text |

### Response

- **Status Code:** `201 Created` (or `200 OK` if preferred)
- **Content-Type:** `application/json`
- **Body:** Success response object

#### Success Response Structure

```json
{
  "success": true,
  "application_id": 12345
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | boolean | Yes | Should be `true` on successful submission |
| `application_id` | integer | Yes | Unique identifier for the submitted application (generated by Employer API) |

#### Example Response

```json
{
  "success": true,
  "application_id": 98765
}
```

#### Error Responses

If the application submission fails, return an appropriate HTTP status code (e.g., `400 Bad Request`, `500 Internal Server Error`) with an error object:

```json
{
  "success": false,
  "error": "Job posting no longer available"
}
```

---

## Integration Notes

### Current Implementation

The Employee Portal currently uses a **mock API service** located at:
- `employee_portal/services/employer_api_service.py`

The mock functions are:
- `fetch_jobs()` - Returns hardcoded job data
- `post_application(application_data)` - Logs and returns a mock success response

### Switching to Real API

When the Employer API is ready, update `employee_portal/services/employer_api_service.py`:

1. Replace `fetch_jobs()` with an HTTP GET request to `/jobs`
2. Replace `post_application()` with an HTTP POST request to `/applications`
3. Add error handling for network failures, timeouts, and invalid responses
4. Add configuration for the API base URL (via environment variable or config file)

### Example Implementation (Future)

```python
import requests
from flask import current_app

EMPLOYER_API_BASE_URL = os.getenv("EMPLOYER_API_BASE_URL", "http://localhost:8000")

def fetch_jobs() -> list[dict]:
    try:
        response = requests.get(f"{EMPLOYER_API_BASE_URL}/jobs", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        current_app.logger.error(f"Failed to fetch jobs: {e}")
        return []  # Return empty list on error

def post_application(application_data: dict) -> dict:
    try:
        response = requests.post(
            f"{EMPLOYER_API_BASE_URL}/applications",
            json=application_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        current_app.logger.error(f"Failed to submit application: {e}")
        return {"success": False, "error": str(e)}
```

---

## Testing

### Test Data

The Employee Portal expects jobs with these role types for proper matching:
- Chef
- Cashier
- Driver
- Marketing Specialist
- Food Safety Inspector
- Fire Safety Inspector

See `employee_portal/utils/helpers.py` for the role-to-requirements mapping used for match scoring.

### Validation

The Employee Portal will:
- Validate that required fields are present in job responses
- Handle missing optional fields gracefully
- Parse ISO 8601 datetime strings for `posted_at`
- Store `id` as string to handle both integer and string IDs

---

## Questions or Changes?

If the API structure needs to change, coordinate with the Employee Portal team to update:
1. `employee_portal/services/employer_api_service.py`
2. `employee_portal/routes/job_routes.py` (job sync logic)
3. `employee_portal/routes/application_routes.py` (application submission)

---

**Last Updated:** November 13, 2025


