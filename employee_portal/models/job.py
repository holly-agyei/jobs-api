from datetime import datetime

from employee_portal import db


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False, index=True)
    company = db.Column(db.String(120), nullable=False, default="Acme Corp")
    location = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.JSON, default=list, nullable=False)
    required_certifications = db.Column(db.JSON, default=list, nullable=False)
    rating = db.Column(db.Float, default=3.0)  # Company rating (1-5 stars)
    match_score = db.Column(db.Float, default=0.0)  # Profile match score (0-5)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_synced_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    applications = db.relationship(
        "Application",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Job {self.title} ({self.role})>"

