import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(ROOT_DIR / 'employee_portal.db').as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False
    SOCKETIO_MESSAGE_QUEUE = os.getenv("SOCKETIO_MESSAGE_QUEUE")
    JOB_CACHE_TIMEOUT = int(os.getenv("JOB_CACHE_TIMEOUT", "900"))
    
    # Employer API Configuration
    # Set EMPLOYER_API_ENABLED=true to use real API instead of mock
    EMPLOYER_API_ENABLED = os.getenv("EMPLOYER_API_ENABLED", "false").lower() == "true"
    EMPLOYER_API_BASE_URL = os.getenv("EMPLOYER_API_BASE_URL", "")
    EMPLOYER_API_KEY = os.getenv("EMPLOYER_API_KEY", "")
    EMPLOYER_API_TIMEOUT = int(os.getenv("EMPLOYER_API_TIMEOUT", "10"))
    PROFILE_UPLOAD_FOLDER = os.getenv(
        "PROFILE_UPLOAD_FOLDER",
        (ROOT_DIR / "employee_portal" / "static" / "uploads").as_posix(),
    )
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

