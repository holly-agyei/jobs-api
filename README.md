# Employer API

A production-ready Flask REST API that serves as the backend for the Employee Portal. This API handles job postings and job applications.

## Features

- ✅ RESTful API endpoints for jobs and applications
- ✅ PostgreSQL and SQLite database support
- ✅ API key authentication for protected routes
- ✅ CORS enabled for cross-origin requests
- ✅ Database migrations with Flask-Migrate
- ✅ Production-ready with Gunicorn
- ✅ Environment-based configuration

## API Endpoints

### Public Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/jobs` | Fetch all available job postings |
| POST | `/applications` | Submit a new job application |
| GET | `/health` | Health check endpoint |

### Protected Endpoints (Require API Key)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/jobs` | Create a new job posting |
| GET | `/applications` | View all job applications |

**Authentication:** Include `x-api-key` header with your API key for protected endpoints.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and update with your values:

```bash
cp .env.example .env
```

Edit `.env` and set:
- `SECRET_KEY`: A secret key for Flask sessions
- `DATABASE_URL`: Database connection string
- `EMPLOYER_API_KEY`: API key for protected endpoints

### 3. Initialize Database

```bash
# Create database tables
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Seed sample data
python seed_data.py
```

### 4. Run the Application

**Development:**
```bash
python app.py
```

**Production (with Gunicorn):**
```bash
gunicorn app:app
```

The API will be available at `http://localhost:8000`

## API Usage Examples

### Get All Jobs

```bash
curl http://localhost:8000/jobs
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
    "description": "Support lead chef with daily kitchen operations...",
    "required_skills": ["Cooking", "Food Safety", "Inventory Management"],
    "required_certifications": ["Food Handler Certification"],
    "posted_at": "2025-11-11T10:30:00"
  }
]
```

### Submit an Application

```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1001,
    "user_id": 5,
    "resume_link": "https://example.com/resumes/user5_resume.pdf",
    "skills": ["Cooking", "Food Safety"],
    "certifications": ["Food Handler Certification"],
    "cover_letter": "I am very interested in this position..."
  }'
```

**Response:**
```json
{
  "success": true,
  "application_id": 98765
}
```

### Create a Job (Protected)

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -H "x-api-key: myemployerkey123" \
  -d '{
    "title": "Software Engineer",
    "role": "Engineering",
    "company": "Tech Corp",
    "location": "Remote",
    "description": "Build amazing software...",
    "required_skills": ["Python", "Flask"],
    "required_certifications": []
  }'
```

### Get All Applications (Protected)

```bash
curl http://localhost:8000/applications \
  -H "x-api-key: myemployerkey123"
```

## Project Structure

```
employer_api/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models
├── seed_data.py           # Database seeding script
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration
├── .env.example          # Environment variables template
├── routes/
│   ├── __init__.py
│   ├── job_routes.py     # Job-related endpoints
│   └── application_routes.py  # Application endpoints
└── utils/
    ├── __init__.py
    └── auth.py           # API key authentication
```

## Database Models

### Job
- `id` (Primary Key)
- `title`, `role`, `company`, `location`
- `description`
- `required_skills` (JSON array)
- `required_certifications` (JSON array)
- `posted_at` (DateTime)

### Application
- `id` (Primary Key)
- `job_id` (Foreign Key to Job)
- `user_id`
- `resume_link`
- `skills` (JSON array)
- `certifications` (JSON array)
- `cover_letter`
- `created_at` (DateTime)

## Deployment

### Render.com

1. Connect your GitHub repository to Render
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn app:app`
4. Add environment variables in Render dashboard:
   - `FLASK_ENV=production`
   - `SECRET_KEY=<your-secret-key>`
   - `DATABASE_URL=<your-postgres-url>`
   - `EMPLOYER_API_KEY=<your-api-key>`
   - `CORS_ORIGINS=<your-frontend-url>`

### Heroku

1. Install Heroku CLI and login
2. Create app: `heroku create employer-api`
3. Add PostgreSQL: `heroku addons:create heroku-postgresql:hobby-dev`
4. Set environment variables: `heroku config:set SECRET_KEY=...`
5. Deploy: `git push heroku main`
6. Run migrations: `heroku run flask db upgrade`
7. Seed data: `heroku run python seed_data.py`

## Development

### Running Migrations

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Testing

Test the API endpoints using curl, Postman, or your preferred HTTP client.

## Security Notes

- Never commit `.env` file to version control
- Use strong `SECRET_KEY` in production
- Rotate `EMPLOYER_API_KEY` regularly
- Configure `CORS_ORIGINS` to specific domains in production
- Use HTTPS in production
- Keep dependencies updated

## License

MIT

