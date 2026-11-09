import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from controllers.auth_controller import auth_bp
from controllers.catalog_controller import catalog_bp
from controllers.service_controller import service_bp
from controllers.dashboard_controller import dashboard_bp
from controllers.admin_controller import admin_bp
from controllers.entity_controller import entity_bp

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "clave-local-de-desarrollo")
app.config["BACKEND_URL"] = os.getenv("BACKEND_URL", "http://localhost:8081")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "false").lower() == "true",
)
CSRFProtect(app)

app.register_blueprint(auth_bp)
app.register_blueprint(catalog_bp)
app.register_blueprint(service_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(entity_bp)


@app.get("/")
def index():
    from flask import redirect, session, url_for
    return redirect(url_for("dashboard.dashboard") if session.get("user") else url_for("auth.login"))


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "frontend-flask"}
