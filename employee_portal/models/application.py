from datetime import datetime

from sqlalchemy import UniqueConstraint

from employee_portal import db


class Application(db.Model):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_applications_user_job"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_link = db.Column(db.String(255), nullable=True)
    skills = db.Column(db.JSON, nullable=False)
    certifications = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(50), default="submitted", nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="applications")
    job = db.relationship("Job", back_populates="applications")

    def __repr__(self) -> str:
        return f"<Application user={self.user_id} job={self.job_id}>"

