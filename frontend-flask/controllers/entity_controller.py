import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from controllers.api_client import api_request

entity_bp = Blueprint("entidades", __name__)


@entity_bp.route("/clientes-vehiculos", methods=["GET", "POST"])
def manage():
    if not session.get("user"):
        return redirect(url_for("auth.login"))
    try:
        if request.method == "POST":
            action = request.form.get("action")
            item_id = request.form.get("id")
            if action in ("delete_cliente", "delete_vehiculo"):
                kind = action.removeprefix("delete_")
                api_request("DELETE", f"/api/{'clientes' if kind == 'cliente' else 'vehiculos'}/{item_id}")
                flash(f"{kind.capitalize()} desactivado.", "success")
            elif action in ("cliente", "vehiculo"):
                if action == "cliente":
                    payload = {
                        "nombre": request.form.get("nombre", "").strip(),
                        "apellidoPaterno": request.form.get("apellido_paterno", "").strip(),
                        "apellidoMaterno": request.form.get("apellido_materno") or None,
                        "telefono": request.form.get("telefono") or None,
                        "email": request.form.get("email") or None,
                    }
                    path = "/api/clientes"
                else:
                    payload = {
                        "idCliente": int(request.form["id_cliente"]),
                        "idMarca": int(request.form["id_marca"]),
                        "idModelo": int(request.form["id_modelo"]),
                        "idAno": int(request.form["id_ano"]),
                        "placas": request.form.get("placas", "").strip(),
                        "color": request.form.get("color") or None,
                        "vin": request.form.get("vin") or None,
                    }
                    path = "/api/vehiculos"
                if item_id:
                    api_request("PUT", f"{path}/{item_id}", json=payload)
                else:
                    api_request("POST", path, json=payload)
                flash("Registro guardado.", "success")
            return redirect(url_for("entidades.manage"))

        customers = api_request("GET", "/api/clientes")
        vehicles = api_request("GET", "/api/vehiculos")
        brands = api_request("GET", "/api/catalogos/marcas")
        models = api_request("GET", "/api/catalogos/modelos")
        years = api_request("GET", "/api/catalogos/anos")
        customer_id = request.args.get("editar_cliente")
        vehicle_id = request.args.get("editar_vehiculo")
        customer = next((item for item in customers if str(item["id_cliente"]) == customer_id), None)
        vehicle = next((item for item in vehicles if str(item["id_vehiculo"]) == vehicle_id), None)
        return render_template(
            "clientes_vehiculos.html", customers=customers, vehicles=vehicles,
            brands=brands, models=models, years=years,
            customer=customer, vehicle=vehicle,
        )
    except (ValueError, KeyError, requests.RequestException) as error:
        flash(str(error) or "No se pudo completar la operación.", "danger")
        if request.method == "POST":
            return redirect(url_for("dashboard.dashboard"))
        return render_template(
            "clientes_vehiculos.html", customers=[], vehicles=[],
            brands=[], models=[], years=[], customer=None, vehicle=None,
        )
