from flask import Blueprint, render_template

from employee_portal import db
from employee_portal.models.connection import Connection
from employee_portal.models.job import Job
from employee_portal.models.user import User

general_bp = Blueprint("general", __name__)


def _format_stat_value(count: int) -> str:
    """Format large numbers with k notation (e.g., 1200 -> 1.2k, 50000 -> 50k)"""
    if count >= 1000:
        k_value = count / 1000
        if k_value >= 10:
            return f"{int(k_value)}k"
        return f"{k_value:.1f}k"
    return str(count)


@general_bp.route("/about")
def about():
    # Calculate real-time statistics from database
    active_members_count = User.query.count()
    open_roles_count = Job.query.count()
    connections_made_count = Connection.query.count()

    features = [
        {
            "title": "Discover Roles Faster",
            "description": "Browse curated categories, filter by skills, and see match scores tailored to your profile.",
        },
        {
            "title": "Showcase Your Profile",
            "description": "Build rich profiles with skills, certifications, and resumes that employers can trust.",
        },
        {
            "title": "Apply in One Click",
            "description": "Submit polished applications directly from your dashboard—complete with snapshots for every job.",
        },
        {
            "title": "Grow Your Network",
            "description": "Connect with peers, send messages, and collaborate through the built-in chat experience.",
        },
    ]
    stats = [
        {"label": "Active Members", "value": _format_stat_value(active_members_count)},
        {"label": "Open Roles", "value": _format_stat_value(open_roles_count)},
        {"label": "Connections Made", "value": _format_stat_value(connections_made_count)},
    ]
    return render_template("about.html", features=features, stats=stats)

