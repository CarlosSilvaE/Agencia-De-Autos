import requests
from flask import Blueprint, flash, render_template, request, session, redirect, url_for

from controllers.api_client import api_request

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("auth.login"))
    filter_value = request.args.get("filter", "total")
    selected_date = request.args.get("date") or None
    try:
        data = api_request("GET", "/api/dashboard", params={"filter": filter_value, "date": selected_date})
    except (ValueError, requests.RequestException) as error:
        flash(str(error) or "No se pudo cargar el tablero.", "danger")
        data = []
    return render_template("dashboard.html", data=data, filter_value=filter_value, selected_date=selected_date or "")
