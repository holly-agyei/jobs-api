# Employer API - Job Posting Guide

This guide explains how to post jobs to the Employer API that will be displayed in the Employee Portal.

---

## Overview

The Employer API should expose a `GET /jobs` endpoint that returns a list of job postings. This document provides example jobs and explains the required format.

---

## Job Object Format

Each job object must follow this structure:

```json
{
  "id": 1001,
  "title": "Sous Chef",
  "role": "Chef",
  "company": "Culinary Collective",
  "location": "New York, NY",
  "description": "Job description text...",
  "required_skills": ["Cooking", "Food Safety", "Inventory Management"],
  "required_certifications": ["Food Handler Certification"],
  "posted_at": "2025-11-11T10:30:00"
}
```

### Field Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer/string | **Yes** | Unique identifier for the job (used to track jobs across syncs) |
| `title` | string | **Yes** | Job title (e.g., "Sous Chef", "Front Desk Cashier") |
| `role` | string | **Yes** | Job role category (see Role Types below) |
| `company` | string | No | Company name (defaults to "Acme Corp" if missing) |
| `location` | string | **Yes** | Job location (e.g., "New York, NY", "Chicago, IL") |
| `description` | string | No | Job description text (can be empty string) |
| `required_skills` | array of strings | No | List of required skills (e.g., `["Cooking", "Food Safety"]`) |
| `required_certifications` | array of strings | No | List of required certifications (e.g., `["Food Handler Certification"]`) |
| `posted_at` | string (ISO 8601) | No | Job posting date/time in ISO format (e.g., `"2025-11-11T10:30:00"`) |

---

## Supported Role Types

The Employee Portal has built-in matching logic for these role types. Use these exact role names for optimal matching:

1. **Chef** - Kitchen positions (Sous Chef, Line Cook, Kitchen Manager)
2. **Cashier** - Front desk and checkout positions
3. **Driver** - Delivery and transportation positions
4. **Marketing Specialist** - Marketing and promotion positions
5. **Food Safety Inspector** - Food safety and compliance positions
6. **Fire Safety Inspector** - Fire safety and code compliance positions

### Role-Specific Requirements

Each role has expected skills and certifications for matching:

#### Chef
- **Skills:** Cooking, Food Safety, Inventory Management
- **Certifications:** Food Handler Certification

#### Cashier
- **Skills:** Customer Service, Cash Handling, Food Safety
- **Certifications:** Food Handler Certification

#### Driver
- **Skills:** Driving, Customer Service, Food Safety
- **Certifications:** Driver's License

#### Marketing Specialist
- **Skills:** Marketing, Customer Service, Food Safety
- **Certifications:** Marketing Certification

#### Food Safety Inspector
- **Skills:** Food Safety, Inventory Management
- **Certifications:** Food Safety Certification

#### Fire Safety Inspector
- **Skills:** Gas leak tests, City code adherence
- **Certifications:** CGLI Inspector

---

## Example Jobs

See `EXAMPLE_JOBS.json` for 15 complete example job postings that you can use as templates.

### Quick Examples

#### Example 1: Chef Position

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

#### Example 2: Cashier Position

```json
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
```

#### Example 3: Driver Position

```json
{
  "id": 1003,
  "title": "Delivery Driver",
  "role": "Driver",
  "company": "FastBite",
  "location": "Los Angeles, CA",
  "description": "Deliver gourmet meals across the metro area ensuring safety and quality.",
  "required_skills": ["Driving", "Customer Service", "Food Safety"],
  "required_certifications": ["Driver's License"],
  "posted_at": "2025-11-12T08:15:00"
}
```

---

## API Endpoint Implementation

### GET /jobs

**Request:**
```
GET /jobs
Headers:
  Authorization: Bearer <api_key>
```

**Response:**
```json
[
  {
    "id": 1001,
    "title": "Sous Chef",
    "role": "Chef",
    "company": "Culinary Collective",
    "location": "New York, NY",
    "description": "...",
    "required_skills": ["Cooking", "Food Safety", "Inventory Management"],
    "required_certifications": ["Food Handler Certification"],
    "posted_at": "2025-11-11T10:30:00"
  },
  {
    "id": 1002,
    ...
  }
]
```

### Important Notes

1. **ID Uniqueness:** Job IDs must be unique and stable. The Employee Portal uses the `id` field to track jobs across syncs. If a job with the same ID appears in subsequent requests, it will be updated. If it doesn't appear, it will be removed from the Employee Portal.

2. **Date Format:** Use ISO 8601 format for `posted_at` (e.g., `"2025-11-11T10:30:00"`). The Employee Portal will parse this automatically.

3. **Skills & Certifications:** These are case-insensitive for matching purposes. The Employee Portal normalizes them to lowercase for comparison. However, store them in a readable format (e.g., "Food Safety" not "food safety").

4. **Empty Arrays:** If a job has no required skills or certifications, use empty arrays `[]` rather than omitting the fields.

5. **Company Field:** If omitted, defaults to "Acme Corp" in the Employee Portal. Always include a company name for better job listings.

---

## Job Matching in Employee Portal

The Employee Portal calculates a **match score** for each job based on:

1. **Skills Match:** How many required skills the employee has
2. **Certifications Match:** How many required certifications the employee has
3. **Role Match:** How well the employee's profile matches the role requirements

Jobs are sorted by match score (highest first), so employees see the most relevant jobs first.

---

## Best Practices

### 1. **Clear Job Titles**
Use descriptive, specific job titles:
- ✅ "Sous Chef"
- ✅ "Front Desk Cashier"
- ❌ "Worker"
- ❌ "Help Wanted"

### 2. **Detailed Descriptions**
Include enough detail for employees to understand the role:
- Responsibilities
- Work environment
- Schedule information
- Benefits (if applicable)

### 3. **Accurate Skills & Certifications**
List only skills and certifications that are actually required:
- ✅ ["Cooking", "Food Safety", "Inventory Management"]
- ❌ ["Everything", "All Skills"]

### 4. **Consistent Location Format**
Use a consistent location format:
- ✅ "New York, NY"
- ✅ "Chicago, IL"
- ❌ "NYC"
- ❌ "Windy City"

### 5. **Recent Post Dates**
Use recent `posted_at` dates for active positions. The Employee Portal shows newer jobs first when match scores are equal.

### 6. **Unique IDs**
Ensure job IDs are unique and don't change. If you need to update a job, use the same ID with updated fields.

---

## Testing

### Test with Employee Portal

1. Start the Employer API with example jobs
2. Configure Employee Portal to connect to your API
3. Verify jobs appear in the Employee Portal
4. Test job matching with employee profiles
5. Verify applications are received correctly

### Sample Test Data

Use the jobs in `EXAMPLE_JOBS.json` to test:
- Different role types
- Various locations
- Different skill requirements
- Multiple companies

---

## FAQ

### Q: Can I add new role types?
A: Yes, but they won't have built-in matching logic. The Employee Portal will still match based on skills and certifications.

### Q: What if a job has no required skills?
A: Use an empty array `[]`. The match score will be based on certifications only.

### Q: Can I update a job after posting?
A: Yes, use the same `id` with updated fields. The Employee Portal will sync and update the job.

### Q: How often should I update the jobs list?
A: The Employee Portal syncs jobs every 15 minutes (configurable). Post updates as needed.

### Q: What happens if I delete a job?
A: Remove it from the `/jobs` response. The Employee Portal will remove it on the next sync.

---

## Complete Example Response

Here's what a complete `/jobs` response might look like:

```json
[
  {
    "id": 1001,
    "title": "Sous Chef",
    "role": "Chef",
    "company": "Culinary Collective",
    "location": "New York, NY",
    "description": "Support lead chef with daily kitchen operations and menu execution. Responsible for food preparation, maintaining kitchen standards, and coordinating with kitchen staff.",
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
    "description": "Assist guests with purchases, manage the register, and maintain customer satisfaction. Handle cash transactions, process payments, and provide excellent customer service.",
    "required_skills": ["Customer Service", "Cash Handling", "Food Safety"],
    "required_certifications": ["Food Handler Certification"],
    "posted_at": "2025-11-08T14:20:00"
  },
  {
    "id": 1003,
    "title": "Delivery Driver",
    "role": "Driver",
    "company": "FastBite",
    "location": "Los Angeles, CA",
    "description": "Deliver gourmet meals across the metro area ensuring safety and quality. Maintain delivery vehicle, follow traffic regulations, and provide friendly customer interactions.",
    "required_skills": ["Driving", "Customer Service", "Food Safety"],
    "required_certifications": ["Driver's License"],
    "posted_at": "2025-11-12T08:15:00"
  }
]
```

---

## Next Steps

1. **Review Example Jobs:** Check `EXAMPLE_JOBS.json` for 15 complete examples
2. **Implement GET /jobs:** Create the endpoint that returns jobs in this format
3. **Test Integration:** Connect Employee Portal to your API and verify jobs appear
4. **Monitor Syncs:** Check that jobs are syncing correctly every 15 minutes
5. **Handle Applications:** Implement `POST /applications` to receive job applications

---

**Need Help?** Refer to `API_SPECIFICATION.md` for the complete API contract between Employee Portal and Employer API.


