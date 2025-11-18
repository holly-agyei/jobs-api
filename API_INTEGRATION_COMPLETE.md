# Employer API Integration - Complete ✅

The Employee Portal is now fully integrated with the real Employer API.

---

## Configuration

The Employee Portal is configured to connect to:

**API Base URL:** `https://jobs-api-s4o6.onrender.com`  
**API Key:** `myemployerkey123` (stored in `.env`)

### Environment Variables (`.env`)

```bash
EMPLOYER_API_ENABLED=true
EMPLOYER_API_BASE_URL=https://jobs-api-s4o6.onrender.com
EMPLOYER_API_KEY=myemployerkey123
EMPLOYER_API_TIMEOUT=10
```

---

## What Was Updated

### 1. **`employer_api_service.py`**
   - ✅ Added `requests` library import
   - ✅ Replaced mock `fetch_jobs()` with real HTTP GET request to `/jobs`
   - ✅ Replaced mock `post_application()` with real HTTP POST request to `/applications`
   - ✅ Added error handling with fallback to mock data on failures
   - ✅ Added proper logging for API calls

### 2. **`application_routes.py`**
   - ✅ Updated to convert `job.external_id` to integer for API
   - ✅ Added error handling for API submission failures
   - ✅ Shows user-friendly error messages if API submission fails

### 3. **`.env` file**
   - ✅ Added Employer API configuration
   - ✅ Enabled API integration

---

## How It Works

### Fetching Jobs (`GET /jobs`)

1. When users visit the dashboard or jobs page, the app calls `fetch_jobs()`
2. The service makes a GET request to `https://jobs-api-s4o6.onrender.com/jobs`
3. Jobs are returned and cached locally in SQLite
4. Jobs are synced every 15 minutes (configurable)
5. If the API is unavailable, it falls back to mock data

**Note:** `GET /jobs` doesn't require authentication according to the API docs.

### Submitting Applications (`POST /applications`)

1. When an employee applies for a job, the application is:
   - Saved locally in SQLite database
   - Sent to the Employer API via `POST /applications`

2. The application payload includes:
   ```json
   {
     "job_id": 1001,  // Integer from Employer API
     "user_id": 5,    // Employee Portal user ID
     "resume_link": "...",
     "skills": ["Cooking", "Food Safety"],
     "certifications": ["Food Handler Certification"],
     "cover_letter": "..."
   }
   ```

3. If the API submission succeeds:
   - User sees "Application submitted successfully"
   - Application is saved in both local DB and Employer API

4. If the API submission fails:
   - Application is still saved locally
   - User sees a warning message about API error
   - Logs are written for debugging

**Note:** `POST /applications` doesn't require authentication according to the API docs.

---

## Fallback Behavior

The Employee Portal includes intelligent fallback:

- **If API is disabled** (`EMPLOYER_API_ENABLED=false`): Uses mock data
- **If API is unavailable** (network error, timeout): Falls back to mock data and logs error
- **If API returns error** (4xx, 5xx): Logs error and falls back to mock data

This ensures the app continues working even if the Employer API is temporarily down.

---

## Testing the Integration

### 1. Test Job Fetching

1. Restart the Flask app to load new configuration
2. Visit the dashboard or jobs page
3. Check server logs - you should see: `"Fetched X jobs from Employer API"`
4. Jobs from the Employer API should appear in the UI

### 2. Test Application Submission

1. Log in as a user
2. Complete your profile
3. Apply for a job
4. Check server logs - you should see: `"Application submitted successfully: <application_id>"`
5. Check the Employer API - the application should appear in `/applications` endpoint

### 3. Verify API Health

```bash
curl https://jobs-api-s4o6.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "Employer API"
}
```

---

## Monitoring

### Check Logs

The app logs all API interactions:

- **Success:** `"Fetched X jobs from Employer API"`
- **Success:** `"Application submitted successfully: <application_id>"`
- **Error:** `"Failed to fetch jobs from Employer API: <error>"`
- **Error:** `"Failed to submit application: <error>"`

### Common Issues

1. **"Falling back to mock job data"**
   - API might be down or unreachable
   - Check network connectivity
   - Verify API base URL is correct

2. **"Application saved locally but API error: ..."**
   - Application is saved in local DB
   - Check API logs for details
   - Verify job_id exists in Employer API

3. **Timeout errors**
   - Increase `EMPLOYER_API_TIMEOUT` in `.env`
   - Check API server performance

---

## Switching Back to Mock Data

If you need to disable the real API and use mock data:

```bash
# In .env
EMPLOYER_API_ENABLED=false
```

Then restart the Flask app.

---

## Next Steps

1. **Monitor API Usage:** Check Employer API logs to verify requests are being received
2. **Test Edge Cases:** Test with API downtime, invalid job IDs, etc.
3. **Review Application Data:** Verify applications are being stored correctly in Employer API
4. **Performance:** Monitor sync times and optimize if needed

---

## API Endpoints Used

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/jobs` | GET | No | Fetch all job postings |
| `/applications` | POST | No | Submit job application |
| `/health` | GET | No | Health check (optional) |

**Note:** According to the API docs, `/jobs` and `/applications` don't require the `x-api-key` header. The API key is stored in config but not currently used for these endpoints. If the API requires it later, update `employer_api_service.py` to include it in headers.

---

**Integration Status:** ✅ **COMPLETE**  
**Last Updated:** November 13, 2025


