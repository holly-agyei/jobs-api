from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=80)],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")


class ProfileForm(FlaskForm):
    headline = StringField("Headline", validators=[Optional(), Length(max=140)])
    summary = TextAreaField("Professional Summary", validators=[Optional(), Length(max=2000)])
    skills = StringField(
        "Skills (comma separated)",
        validators=[DataRequired(), Length(max=255)],
    )
    certifications = StringField(
        "Certifications (comma separated)",
        validators=[DataRequired(), Length(max=255)],
    )
    resume_link = StringField("Resume Link", validators=[DataRequired(), URL()])
    experience = TextAreaField(
        "Experience",
        validators=[DataRequired(), Length(max=5000)],
    )
    photo = FileField(
        "Profile Photo",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif"], "Images only!")],
    )
    submit = SubmitField("Save Profile")


class ApplicationForm(FlaskForm):
    resume_link = StringField("Resume Link", validators=[DataRequired(), URL()])
    cover_letter = TextAreaField(
        "Cover Letter (optional)",
        validators=[Optional(), Length(max=5000)],
    )
    submit = SubmitField("Submit Application")


class JobFilterForm(FlaskForm):
    role = StringField("Role", validators=[Optional(), Length(max=120)])
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    skill = StringField("Skill", validators=[Optional(), Length(max=120)])
    sort_by = SelectField(
        "Sort By",
        choices=[
            ("match_score", "Best Match"),
            ("posted_at", "Most Recent"),
            ("title", "Title"),
        ],
        default="match_score",
    )
    submit = SubmitField("Filter")


class MessageForm(FlaskForm):
    content = TextAreaField(
        "Message",
        validators=[DataRequired(), Length(min=1, max=2000)],
    )
    submit = SubmitField("Send")


class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")

