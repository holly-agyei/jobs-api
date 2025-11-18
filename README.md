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

## Instructor Q&A Cheat Sheet

**How often do we hit the Employer API?**  
`fetch_jobs()` runs on dashboard/job list loads when the cache (15 min) has expired or when the user clicks **Refresh Jobs**. `post_application()` fires once per successful submission. Everything else (profiles, chat, connections, withdrawals) happens inside our DB.

**Which UI actions trigger writes or network calls?**

- Dashboard/Jobs load → `fetch_jobs()` (cache-aware) + local match-score recompute.  
- “Refresh Jobs” button → `_sync_jobs_if_needed(force=True)` to pull fresh postings.  
- Apply → Profile validation → `Application` insert → `POST /applications` to the Employer API.  
- Withdraw → Ownership + status checks → set `status='withdrawn'` locally (no remote call).  
- Connection requests / chat send → Inserts into `connection_requests`/`connections`; every Socket.IO emission re-checks `User.is_connected_with`.

**What happens if the Employer API is slow or offline?**  
`fetch_jobs()` catches `requests` errors, logs them, and falls back to the bundled mock dataset so the UI never goes blank. `post_application()` still stores the record and surfaces a “saved locally but API error” toast so you can talk about graceful degradation.

**How are match scores computed?**  
`utils.helpers.update_job_match_score` intersects a profile’s `skills_list`/`certifications_list` with the job’s requirements. Missing skills reduce the percentage; once a profile is complete, those jobs bubble up to the top of the dashboard grid.

**What if the Employer API deletes a job I already applied to?**  
During sync we never delete `Job` rows that have `Application` children. The Manage Applications page also back-fills placeholder descriptions so reviewers always see the historical context even if the upstream job disappeared.

**How does withdrawing work under the hood?**  
`applications.withdraw_application` loads the row, asserts ownership, ensures the status is `submitted`/`pending`, flips it to `withdrawn`, and commits. Because the public API has no delete endpoint we treat our local status as the source of truth for both applicant and admin views.

**Why can’t I chat with everyone?**  
Only mutual `Connection` rows unlock the chat UI. Both the HTTP route and the Socket.IO `send_message` handler call `User.is_connected_with` and bail if the relationship isn’t there, so even crafted requests can’t bypass the “request → accept → chat” flow.

**How are profile photos stored?**  
Uploads land in `employee_portal/static/uploads` with a UUID filename (`secure_filename` + `Path.suffix`). Deleting a profile removes the old file. On Render you can point `PROFILE_UPLOAD_FOLDER` at a mounted disk or S3 bucket for durability.

**How would you scale Socket.IO on Render?**  
Set `SOCKETIO_MESSAGE_QUEUE` to a Redis URL and run multiple eventlet workers. Flask-SocketIO will pub/sub through Redis so rooms and typing indicators stay consistent across dynos.

## Deploying to Render

1. Push this repo to GitHub and create a Render “Web Service”.
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:**  
   `gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:$PORT "employee_portal.app:app"`
4. **Environment variables:** `SECRET_KEY`, `DATABASE_URL`, `EMPLOYER_API_BASE_URL`, `EMPLOYER_API_KEY`, `EMPLOYER_API_ENABLED=true`, `EMPLOYER_API_TIMEOUT=10`, and optionally `SOCKETIO_MESSAGE_QUEUE` if you add Redis for multi-instance websockets.
5. Mount a persistent disk or external object store if you need `static/uploads` to survive deploys.
6. On first boot run a one-off `flask shell` (or add Flask-Migrate) to execute `db.create_all()` against your Render Postgres database.

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


