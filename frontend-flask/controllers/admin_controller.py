import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from controllers.api_client import api_request

admin_bp = Blueprint("administradores", __name__)


@admin_bp.route("/administradores", methods=["GET", "POST"])
def admins():
    if not session.get("user"):
        return redirect(url_for("auth.login"))
    try:
        if request.method == "POST":
            action = request.form.get("action")
            admin_id = request.form.get("id")
            if action == "delete":
                api_request("DELETE", f"/api/administradores/{admin_id}")
                flash("Administrador desactivado.", "success")
            else:
                payload = {
                    "nombre": request.form.get("nombre", "").strip(),
                    "usuario": request.form.get("usuario", "").strip(),
                    "password": request.form.get("password") or None,
                    "activo": request.form.get("activo") == "1",
                }
                if admin_id:
                    api_request("PUT", f"/api/administradores/{admin_id}", json=payload)
                else:
                    api_request("POST", "/api/administradores", json=payload)
                flash("Administrador guardado.", "success")
            return redirect(url_for("administradores.admins"))
        administrators = api_request("GET", "/api/administradores")
        edit_id = request.args.get("editar")
        editing = next((item for item in administrators if str(item["id_administrador"]) == edit_id), None)
        return render_template("administradores.html", administrators=administrators, editing=editing)
    except (ValueError, requests.RequestException) as error:
        flash(str(error) or "No se pudo completar la operación.", "danger")
        if request.method == "POST":
            return redirect(url_for("dashboard.dashboard"))
        return render_template("administradores.html", administrators=[], editing=None)
