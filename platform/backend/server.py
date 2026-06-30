import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from api.auth import bp as auth_bp
from api.markers import bp as markers_bp
from api.run import bp as run_bp
from api.logs import bp as logs_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-prod")
    CORS(app, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(markers_bp)
    app.register_blueprint(run_bp)
    app.register_blueprint(logs_bp)

    @app.route("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        dist_dir = Path(__file__).resolve().parent / "static" / "dist"
        if path and (dist_dir / path).exists():
            return send_from_directory(str(dist_dir), path)
        return send_from_directory(str(dist_dir), "index.html")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PLATFORM_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"[Platform] Backend starting on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
