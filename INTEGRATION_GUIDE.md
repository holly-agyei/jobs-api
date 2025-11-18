# Employer API Integration Guide

This guide explains how to connect the Employee Portal to the real Employer API when it's ready.

---

## Overview

The Employer API will be **hosted online** (e.g., on a cloud server, AWS, Heroku, etc.) and the Employee Portal will make HTTP requests to it. You'll need to configure:

1. **API Base URL** - Where the API is hosted
2. **Authentication** - How to authenticate requests (API key, token, etc.)
3. **Network Security** - HTTPS, firewall rules, etc.

---

## Hosting Options

The Employer API can be hosted on:

- **Cloud Platforms:** AWS, Google Cloud, Azure, Heroku, DigitalOcean
- **Dedicated Server:** VPS, dedicated hosting
- **Container Services:** Docker on Kubernetes, Docker Swarm
- **Serverless:** AWS Lambda, Google Cloud Functions (if appropriate)

**The Employee Portal doesn't care where it's hosted** - it just needs a public URL (or internal network URL if both apps are on the same network).

---

## Authentication Strategies

Here are common authentication methods you can use:

### Option 1: API Key (Simplest)

The Employer API provides a secret API key that the Employee Portal includes in requests.

**How it works:**
- Employer team generates an API key (e.g., `sk_live_abc123xyz789`)
- Employee Portal stores it in environment variable
- Employee Portal sends it in `Authorization` header or as a query parameter

**Pros:** Simple, easy to implement
**Cons:** Less secure if key is leaked, harder to revoke per-request

### Option 2: Bearer Token (Recommended)

Similar to API key but uses OAuth2-style bearer tokens.

**How it works:**
- Employee Portal authenticates once and gets a token
- Token is included in `Authorization: Bearer <token>` header
- Tokens can expire and be refreshed

**Pros:** More secure, can expire, industry standard
**Cons:** Requires token management logic

### Option 3: Basic Authentication

Username/password or service account credentials.

**How it works:**
- Employee Portal has a service account username/password
- Credentials sent in `Authorization: Basic <base64>` header

**Pros:** Simple, widely supported
**Cons:** Less secure, credentials must be stored

### Option 4: Mutual TLS (mTLS) - Most Secure

Both sides use SSL certificates to authenticate each other.

**How it works:**
- Employee Portal has a client certificate
- Employer API validates the certificate
- No keys/tokens needed in requests

**Pros:** Very secure, no secrets in requests
**Cons:** Complex setup, certificate management

---

## Recommended Setup: API Key with HTTPS

For most use cases, we recommend **API Key authentication over HTTPS**:

1. **Employer API hosts on HTTPS** (e.g., `https://api.employer-portal.com`)
2. **Employer team provides an API key** (e.g., `emp_portal_key_abc123`)
3. **Employee Portal stores key securely** in environment variable
4. **All requests use HTTPS** to encrypt data in transit

---

## Configuration

### Step 1: Update `.env` File

Add these environment variables to your `.env` file:

```bash
# Employer API Configuration
EMPLOYER_API_BASE_URL=https://api.employer-portal.com
EMPLOYER_API_KEY=your_secret_api_key_here

# Optional: Timeout settings
EMPLOYER_API_TIMEOUT=10
```

### Step 2: Update `config.py`

Add configuration options:

```python
class Config:
    # ... existing config ...
    
    # Employer API settings
    EMPLOYER_API_BASE_URL = os.getenv("EMPLOYER_API_BASE_URL", "")
    EMPLOYER_API_KEY = os.getenv("EMPLOYER_API_KEY", "")
    EMPLOYER_API_TIMEOUT = int(os.getenv("EMPLOYER_API_TIMEOUT", "10"))
    EMPLOYER_API_ENABLED = os.getenv("EMPLOYER_API_ENABLED", "false").lower() == "true"
```

### Step 3: Update `requirements.txt`

Add the `requests` library if not already present:

```txt
requests>=2.31.0
```

### Step 4: Update `employer_api_service.py`

Replace the mock functions with real HTTP calls:

```python
import os
import requests
from flask import current_app

def fetch_jobs() -> list[dict]:
    """
    Fetch jobs from the real Employer API.
    Falls back to mock data if API is disabled or unavailable.
    """
    base_url = current_app.config.get("EMPLOYER_API_BASE_URL")
    api_key = current_app.config.get("EMPLOYER_API_KEY")
    timeout = current_app.config.get("EMPLOYER_API_TIMEOUT", 10)
    enabled = current_app.config.get("EMPLOYER_API_ENABLED", False)
    
    # Use mock if API is not enabled
    if not enabled or not base_url:
        current_app.logger.debug("Using mock employer API (API not enabled)")
        return _fetch_mock_jobs()
    
    try:
        headers = {}
        if api_key:
            # Option 1: API Key in header
            headers["Authorization"] = f"Bearer {api_key}"
            # OR Option 2: Custom header
            # headers["X-API-Key"] = api_key
        
        response = requests.get(
            f"{base_url}/jobs",
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        
        jobs = response.json()
        current_app.logger.info(f"Fetched {len(jobs)} jobs from Employer API")
        return jobs
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to fetch jobs from Employer API: {e}")
        # Fallback to mock data on error
        current_app.logger.warning("Falling back to mock job data")
        return _fetch_mock_jobs()


def post_application(application_data: dict) -> dict:
    """
    Submit application to the real Employer API.
    Falls back to mock response if API is disabled or unavailable.
    """
    base_url = current_app.config.get("EMPLOYER_API_BASE_URL")
    api_key = current_app.config.get("EMPLOYER_API_KEY")
    timeout = current_app.config.get("EMPLOYER_API_TIMEOUT", 10)
    enabled = current_app.config.get("EMPLOYER_API_ENABLED", False)
    
    # Use mock if API is not enabled
    if not enabled or not base_url:
        current_app.logger.debug("Using mock employer API (API not enabled)")
        return _post_mock_application(application_data)
    
    try:
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            # OR: headers["X-API-Key"] = api_key
        
        response = requests.post(
            f"{base_url}/applications",
            json=application_data,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        
        result = response.json()
        current_app.logger.info(
            f"Application submitted successfully: {result.get('application_id')}"
        )
        return result
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"API returned error: {e.response.status_code}"
        try:
            error_data = e.response.json()
            error_msg = error_data.get("error", error_msg)
        except:
            pass
        current_app.logger.error(f"Failed to submit application: {error_msg}")
        return {"success": False, "error": error_msg}
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Network error submitting application: {e}")
        return {"success": False, "error": "Network error. Please try again later."}


# Keep mock functions for fallback
def _fetch_mock_jobs() -> list[dict]:
    """Fallback mock job data"""
    # ... existing MOCK_JOBS code ...


def _post_mock_application(application_data: dict) -> dict:
    """Fallback mock application response"""
    # ... existing mock post_application code ...
```

---

## Security Best Practices

### 1. **Never Commit Secrets to Git**

- Add `.env` to `.gitignore`
- Use environment variables or secret management services
- Never hardcode API keys in source code

### 2. **Use HTTPS Only**

- Always use `https://` URLs in production
- Never send API keys over HTTP
- Validate SSL certificates (requests does this by default)

### 3. **Rotate API Keys Regularly**

- Change API keys periodically
- Have a process to revoke compromised keys
- Use different keys for development/staging/production

### 4. **Rate Limiting**

- The Employer API should implement rate limiting
- Employee Portal should handle rate limit errors gracefully
- Consider implementing retry logic with exponential backoff

### 5. **Error Handling**

- Log errors but don't expose sensitive details to users
- Have fallback behavior (mock data) for development
- Monitor API health and alert on failures

---

## Testing the Integration

### Development Mode (Mock API)

```bash
# .env
EMPLOYER_API_ENABLED=false
```

The app will use mock data.

### Staging Mode (Real API)

```bash
# .env
EMPLOYER_API_ENABLED=true
EMPLOYER_API_BASE_URL=https://staging-api.employer-portal.com
EMPLOYER_API_KEY=staging_key_abc123
```

### Production Mode

```bash
# .env (on production server)
EMPLOYER_API_ENABLED=true
EMPLOYER_API_BASE_URL=https://api.employer-portal.com
EMPLOYER_API_KEY=prod_key_xyz789
```

---

## Deployment Checklist

When deploying to production:

- [ ] API keys stored in secure environment variables (not in code)
- [ ] HTTPS enabled for all API communication
- [ ] Error logging configured to monitor API failures
- [ ] Fallback behavior tested (what happens if API is down?)
- [ ] Rate limiting understood and handled
- [ ] API endpoint URLs verified (staging vs production)
- [ ] Network firewall rules allow outbound HTTPS requests
- [ ] SSL certificate validation enabled (default in requests)

---

## Troubleshooting

### "Connection refused" or "Could not resolve host"

- Check `EMPLOYER_API_BASE_URL` is correct
- Verify network connectivity
- Check firewall rules

### "401 Unauthorized" or "403 Forbidden"

- Verify `EMPLOYER_API_KEY` is correct
- Check API key hasn't expired
- Confirm authentication method matches (Bearer vs X-API-Key)

### "Timeout" errors

- Increase `EMPLOYER_API_TIMEOUT` value
- Check API server performance
- Verify network latency

### API returns unexpected format

- Check API response matches specification in `API_SPECIFICATION.md`
- Verify Content-Type headers
- Review API logs on Employer side

---

## Example: Complete Integration

Here's what the final `employer_api_service.py` might look like:

```python
import os
import requests
from flask import current_app
from typing import Optional

def _get_api_config():
    """Get API configuration from app config"""
    return {
        "base_url": current_app.config.get("EMPLOYER_API_BASE_URL", ""),
        "api_key": current_app.config.get("EMPLOYER_API_KEY", ""),
        "timeout": current_app.config.get("EMPLOYER_API_TIMEOUT", 10),
        "enabled": current_app.config.get("EMPLOYER_API_ENABLED", False),
    }

def _get_headers(api_key: Optional[str] = None) -> dict:
    """Build request headers with authentication"""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers

def fetch_jobs() -> list[dict]:
    config = _get_api_config()
    
    if not config["enabled"] or not config["base_url"]:
        return _fetch_mock_jobs()
    
    try:
        response = requests.get(
            f"{config['base_url']}/jobs",
            headers=_get_headers(config["api_key"]),
            timeout=config["timeout"]
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        current_app.logger.error(f"API error: {e}")
        return _fetch_mock_jobs()

def post_application(application_data: dict) -> dict:
    config = _get_api_config()
    
    if not config["enabled"] or not config["base_url"]:
        return _post_mock_application(application_data)
    
    try:
        response = requests.post(
            f"{config['base_url']}/applications",
            json=application_data,
            headers=_get_headers(config["api_key"]),
            timeout=config["timeout"]
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"API HTTP error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        current_app.logger.error(f"API error: {e}")
        return {"success": False, "error": "Service unavailable"}
```

---

## Next Steps

1. **Coordinate with Employer API team:**
   - Share `API_SPECIFICATION.md` with them
   - Agree on authentication method (API key recommended)
   - Get the API base URL and test credentials

2. **Update Employee Portal:**
   - Add `requests` to `requirements.txt` if needed
   - Update `config.py` with API settings
   - Update `employer_api_service.py` with real HTTP calls
   - Test in staging environment first

3. **Deploy:**
   - Set environment variables on production server
   - Monitor logs for API errors
   - Have fallback plan if API is unavailable

---

**Questions?** Coordinate with the Employer API team to ensure both sides are aligned on authentication, endpoints, and error handling.


