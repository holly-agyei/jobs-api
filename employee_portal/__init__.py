from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_wtf import CSRFProtect

from .config import DevelopmentConfig

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(async_mode="threading")
csrf = CSRFProtect()


def create_app(config_object: str | type[object] = DevelopmentConfig) -> Flask:
    app = Flask(__name__)
    if isinstance(config_object, str):
        app.config.from_object(config_object)
    else:
        app.config.from_object(config_object)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from .models.user import User  # noqa: WPS433

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return User.query.get(int(user_id))

    from . import models  # noqa: F401
    from .routes import register_blueprints

    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app

