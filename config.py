"""Configuration settings for the Employer API."""
import os
from dotenv import load_dotenv

load_dotenv()


def get_database_url():
    """
    Get and normalize the database URL from environment variables.
    Handles Render's postgres:// URLs by converting them to postgresql://
    which is required by SQLAlchemy 2.0+.
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        return 'sqlite:///employer.db'
    
    # Convert postgres:// to postgresql:// for SQLAlchemy compatibility
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return database_url


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EMPLOYER_API_KEY = os.environ.get('EMPLOYER_API_KEY') or 'myemployerkey123'
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Flask settings
    JSON_SORT_KEYS = False  # Preserve JSON key order


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_employer.db'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

