from __future__ import annotations

import argparse
import os

from employee_portal import create_app, socketio

DEFAULT_PORT = int(os.getenv("FLASK_RUN_PORT", "5000"))

parser = argparse.ArgumentParser(description="Run the Employee Portal Flask app.")
parser.add_argument(
    "--host",
    default=os.getenv("FLASK_RUN_HOST", "0.0.0.0"),
    help="Host interface to bind (default: 0.0.0.0)",
)
parser.add_argument(
    "--port",
    type=int,
    default=DEFAULT_PORT,
    help="Port to serve the application on (default: 5000)",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="Run with Flask debug mode enabled.",
)


def main() -> None:
    args = parser.parse_args()
    app = create_app()
    app.debug = args.debug or app.config.get("DEBUG", False)
    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=app.debug,
        allow_unsafe_werkzeug=True,
    )


if __name__ == "__main__":
    main()

