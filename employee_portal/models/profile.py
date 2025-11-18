from datetime import datetime

from sqlalchemy import event

from employee_portal import db


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    headline = db.Column(db.String(140))
    summary = db.Column(db.Text)
    skills = db.Column(db.JSON, default=list, nullable=False)
    certifications = db.Column(db.JSON, default=list, nullable=False)
    resume_link = db.Column(db.String(255))
    experience = db.Column(db.Text)
    photo_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<Profile user_id={self.user_id}>"

    @property
    def skills_list(self) -> list[str]:
        return list(self.skills or [])

    @property
    def certifications_list(self) -> list[str]:
        return list(self.certifications or [])

    @property
    def is_complete(self) -> bool:
        return bool(
            self.resume_link
            and self.experience
            and self.skills_list
            and self.certifications_list
        )

    def photo_path(self) -> str | None:
        if self.photo_filename:
            return f"uploads/{self.photo_filename}"
        return None


@event.listens_for(Profile.skills, "set", retval=True)
def _normalize_skills(target, value, oldvalue, initiator):  # noqa: ANN001
    if value is None:
        return []
    if isinstance(value, list):
        return sorted({skill.strip() for skill in value if skill.strip()})
    if isinstance(value, str):
        return sorted(
            {segment.strip() for segment in value.split(",") if segment.strip()},
        )
    return value


@event.listens_for(Profile.certifications, "set", retval=True)
def _normalize_certs(target, value, oldvalue, initiator):  # noqa: ANN001
    if value is None:
        return []
    if isinstance(value, list):
        return sorted({cert.strip() for cert in value if cert.strip()})
    if isinstance(value, str):
        return sorted(
            {segment.strip() for segment in value.split(",") if segment.strip()},
        )
    return value

