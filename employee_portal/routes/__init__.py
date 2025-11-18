from flask import Flask

from .application_routes import application_bp
from .auth_routes import auth_bp
from .chat_routes import chat_bp
from .connection_routes import connections_bp
from .job_routes import job_bp
from .profile_routes import profile_bp
from .general_routes import general_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(application_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(general_bp)
    app.register_blueprint(connections_bp)

