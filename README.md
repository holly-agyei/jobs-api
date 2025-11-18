# Employee Portal (Flask)

Production-ready employee job portal built with Flask, featuring authentication, profile management, job browsing with mocked employer API, application workflow, and an in-app employee chat gated by mutual connections.

## Project Structure

```
employee_portal/
├── app.py
├── config.py
├── forms.py
├── models/
├── routes/
├── services/
├── templates/
├── static/
└── utils/
```

- `models/`: SQLAlchemy models for users, profiles, jobs, applications, chat messages, connection requests, and confirmed connections.
- `routes/`: Blueprinted view modules (`auth`, `profile`, `job`, `application`, `chat`, `connections`).
- `services/`: Mock Employer API shim (`fetch_jobs`, `post_application`) to be swapped once the real API is available.
- `templates/` & `static/`: Bootstrap-based UI, Socket.IO chat client, custom styles.
- `utils/helpers.py`: Skill-matching utilities and scoring logic.

## Requirements

- Python 3.11+
- SQLite (bundled)
- NodeJS **not** required
- See `employee_portal/requirements.txt` for Python packages (Flask, Flask-Login, Flask-SocketIO, SQLAlchemy, etc.)

## Local Setup

```bash
cd "/Users/holy/Documents/projects/employee portal"
python3 -m venv venv
source venv/bin/activate
pip install -r employee_portal/requirements.txt
python -m employee_portal.app --port 5050
```

The app defaults to port `5000`. Use `--port` or set `FLASK_RUN_PORT` to avoid macOS AirPlay conflicts.

### Environment Variables

Values can be stored in `.env` (auto-loaded by `config.py`):

```
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:////Users/holy/Documents/projects/employee portal/employee_portal/employee_portal.db
```

## Core Features

- **Authentication & Profiles**: Register, login, logout, maintain detailed profile with skills, certifications, experience, and resume link.
- **Job Feed**: Pulls mocked job listings (role, skills, certifications, location) via `services/employer_api_service.fetch_jobs`, caches the results, and computes match scores based on profile alignment.
- **Applications**: Validates profile completeness, prevents duplicates, snapshots skills/certifications, and posts payloads to the mock API.
- **Chat**: Real-time messaging using Flask-SocketIO. Messages persist in the database.
- **Connections**: Employees must exchange and accept connection requests before chatting.
- **Admin Dashboard**: High-level view of applications (read-only).

## Connection Workflow

1. **Send Request**  
   Visit `Connections` and click `Connect` next to a colleague. Duplicate or reciprocal pending requests are handled gracefully.

2. **Incoming Requests**  
   The same page lists incoming requests with `Accept` and `Decline`. Accepting creates a mutual `Connection`; declining removes the request.

3. **Chat Access**  
   Only confirmed connections appear in the Chat sidebar. Attempts to message non-connections (HTTP or Socket.IO) are blocked.

4. **Remove**  
   Removing a connection deletes the relationship and any outstanding requests, immediately revoking chat access.

## Mock Employer API

- `fetch_jobs()` returns curated job data (skills, certifications, ISO timestamps).
- `post_application()` logs the submission and returns a mock confirmation payload.
- When the real Employer API is ready, replace the internals with `requests.get/post` while preserving the interface.

## Testing & Development Tips

- Compile-time sanity check: `venv/bin/python -m compileall employee_portal`
- Seed sample users (script snippet used during development):

```python
from employee_portal import create_app, db
from employee_portal.models.user import User

users = [
    {"username": "alex", "email": "alex@example.com", "password": "Password123!"},
    {"username": "brett", "email": "brett@example.com", "password": "Password123!"},
    {"username": "casey", "email": "casey@example.com", "password": "Password123!"},
    {"username": "dana", "email": "dana@example.com", "password": "Password123!"},
    {"username": "ebony", "email": "ebony@example.com", "password": "Password123!"},
]

app = create_app()
with app.app_context():
    for info in users:
        user = User.query.filter_by(email=info["email"]).first()
        if not user:
            user = User(username=info["username"], email=info["email"])
            user.set_password(info["password"])
            db.session.add(user)
    db.session.commit()
```

## Deployment Notes

- Use a production-ready WSGI/ASGI server (e.g., Gunicorn + Eventlet/gevent or Uvicorn with ASGI wrapper) instead of the development server.
- Configure secret keys, database, and message queues (if scaling Socket.IO) via environment variables.
- Enforce HTTPS and secure cookies in production (`SESSION_COOKIE_SECURE`, `REMEMBER_COOKIE_SECURE`).


