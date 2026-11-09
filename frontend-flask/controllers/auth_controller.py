import requests
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from controllers.api_client import api_request

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            data = api_request(
                "POST",
                "/api/auth/login",
                json={"username": request.form.get("usuario"), "password": request.form.get("password")},
            )
            if data.get("authenticated"):
                session.clear()
                session["user"] = data["user"]
                return redirect(url_for("dashboard.dashboard"))
        except ValueError:
            flash("Usuario o contraseña incorrectos.", "danger")
        except requests.RequestException:
            flash("No se pudo conectar con el servicio de autenticación.", "danger")
    return render_template("login.html")


@auth_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
