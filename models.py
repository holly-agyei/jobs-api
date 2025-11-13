"""Database models for the Employer API."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON

db = SQLAlchemy()


class Job(db.Model):
    """Job posting model."""
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(JSON, nullable=False, default=list)
    required_certifications = db.Column(JSON, nullable=False, default=list)
    posted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship to applications
    applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert job model to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'role': self.role,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'required_skills': self.required_skills or [],
            'required_certifications': self.required_certifications or [],
            'posted_at': self.posted_at.isoformat() if self.posted_at else None
        }
    
    def __repr__(self):
        return f'<Job {self.id}: {self.title} at {self.company}>'


class Application(db.Model):
    """Job application model."""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    resume_link = db.Column(db.String(500), nullable=False)
    skills = db.Column(JSON, nullable=False, default=list)
    certifications = db.Column(JSON, nullable=False, default=list)
    cover_letter = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert application model to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'user_id': self.user_id,
            'resume_link': self.resume_link,
            'skills': self.skills or [],
            'certifications': self.certifications or [],
            'cover_letter': self.cover_letter,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Application {self.id}: User {self.user_id} for Job {self.job_id}>'

