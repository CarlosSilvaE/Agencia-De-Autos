import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from controllers.api_client import api_request

service_bp = Blueprint("servicios", __name__)
STATES = ["En espera", "En proceso", "Finalizado"]


def signed_in():
    return bool(session.get("user"))


def service_options():
    return {
        "brands": api_request("GET", "/api/catalogos/marcas"),
        "models": api_request("GET", "/api/catalogos/modelos"),
        "years": api_request("GET", "/api/catalogos/anos"),
        "parts": api_request("GET", "/api/catalogos/refacciones"),
        "vehicles": api_request("GET", "/api/vehiculos"),
    }


def save_service(folio=None):
    existing = None
    try:
        options = service_options()
        if folio:
            results = api_request("GET", "/api/servicios", params={"folio": folio})
            existing = results[0] if results else None
            if existing is None:
                flash("No se encontró el servicio solicitado.", "danger")
                return redirect(url_for("servicios.services"))
            existing["refacciones"] = api_request("GET", f"/api/servicios/{folio}/refacciones")
        if request.method == "POST":
            form = request.form
            parts = [
                {"idRefaccion": int(part_id),
                 "cantidad": int(form.get(f"cantidad_{part_id}", "1")),
                 "precioUnitario": float(form.get(f"precio_{part_id}", "0"))}
                for part_id in form.getlist("refacciones")
            ]
            next_date = form.get("fecha_proximo")
            payload = {
                "folio": form.get("folio") or None,
                "tipoServicio": form.get("tipo_servicio"),
                "descripcion": form.get("descripcion", "").strip(),
                "estado": form.get("estado"),
                "costo": float(form.get("costo") or 0),
                "cliente": {
                    "id": int(form["id_cliente"]) if form.get("id_cliente") else None,
                    "nombre": form.get("nombre", "").strip(),
                    "apellidoPaterno": form.get("apellido_paterno", "").strip(),
                    "apellidoMaterno": form.get("apellido_materno") or None,
                    "telefono": form.get("telefono") or None,
                    "email": form.get("email") or None,
                },
                "vehiculo": {
                    "id": int(form["id_vehiculo"]) if form.get("id_vehiculo") else None,
                    "idMarca": int(form.get("id_marca") or 0),
                    "idModelo": int(form.get("id_modelo") or 0),
                    "idAno": int(form.get("id_ano") or 0),
                    "placas": form.get("placas", "").strip(),
                    "color": form.get("color") or None,
                    "vin": form.get("vin") or None,
                },
                "entrega": {
                    "nombre": form.get("nombre_entrega", "").strip(),
                    "telefono": form.get("telefono_entrega") or None,
                    "relacionPropietario": form.get("relacion") or None,
                    "observaciones": form.get("observaciones_entrega") or None,
                },
                "refacciones": parts,
                "proximoServicio": {
                    "fechaProgramada": next_date,
                    "kilometraje": int(form["kilometraje"]) if form.get("kilometraje") else None,
                    "notas": form.get("notas_proximo") or None,
                } if next_date else None,
            }
            if folio:
                api_request("PUT", f"/api/servicios/{folio}", json=payload)
                flash("Servicio actualizado.", "success")
            else:
                result = api_request("POST", "/api/servicios", json=payload)
                flash(f"Servicio creado con folio {result['folio']}.", "success")
            return redirect(url_for("servicios.services"))
        if existing:
            for key in ("fecha_ingreso", "proximo_servicio"):
                if existing.get(key):
                    existing[key] = str(existing[key])[:10]
        return render_template("servicio_form.html", options=options, states=STATES, service=existing)
    except (ValueError, KeyError, requests.RequestException) as error:
        flash(str(error) or "No se pudo completar la operación.", "danger")
        return redirect(url_for("servicios.services"))


@service_bp.get("/servicios")
def services():
    if not signed_in():
        return redirect(url_for("auth.login"))
    try:
        services_list = api_request(
            "GET", "/api/servicios",
            params={"folio": request.args.get("folio", ""), "propietario": request.args.get("propietario", "")},
        )
        return render_template("servicios.html", services=services_list)
    except (ValueError, requests.RequestException) as error:
        flash(str(error) or "No se pudieron consultar los servicios.", "danger")
        return render_template("servicios.html", services=[])


@service_bp.route("/servicios/nuevo", methods=["GET", "POST"])
def create():
    if not signed_in():
        return redirect(url_for("auth.login"))
    return save_service()


@service_bp.route("/servicios/<folio>/editar", methods=["GET", "POST"])
def edit(folio):
    if not signed_in():
        return redirect(url_for("auth.login"))
    return save_service(folio)


@service_bp.post("/servicios/<folio>/estado")
def update_status(folio):
    if not signed_in():
        return redirect(url_for("auth.login"))
    try:
        api_request("PATCH", f"/api/servicios/{folio}/estado", json={"estado": request.form.get("estado")})
        flash("Estado actualizado.", "success")
    except (ValueError, requests.RequestException) as error:
        flash(str(error) or "No se pudo actualizar el estado.", "danger")
    return redirect(url_for("servicios.services"))


@service_bp.post("/servicios/<folio>/eliminar")
def delete(folio):
    if not signed_in():
        return redirect(url_for("auth.login"))
    try:
        api_request("DELETE", f"/api/servicios/{folio}")
        flash("Servicio eliminado.", "success")
    except (ValueError, requests.RequestException) as error:
        flash(str(error) or "No se pudo eliminar el servicio.", "danger")
    return redirect(url_for("servicios.services"))


@service_bp.get("/proximos-servicios")
def upcoming():
    if not signed_in():
        return redirect(url_for("auth.login"))
    try:
        upcoming_list = api_request(
            "GET", "/api/servicios/proximos",
            params={"folio": request.args.get("folio", ""), "propietario": request.args.get("propietario", "")},
        )
        return render_template("proximos.html", upcoming=upcoming_list)
    except (ValueError, requests.RequestException) as error:
        flash(str(error) or "No se pudieron consultar los próximos servicios.", "danger")
        return render_template("proximos.html", upcoming=[])


@service_bp.get("/comprobante/<folio>")
def receipt(folio):
    if not signed_in():
        return redirect(url_for("auth.login"))
    try:
        services_list = api_request("GET", "/api/servicios", params={"folio": folio})
        return render_template("comprobante.html", service=services_list[0] if services_list else None)
    except (ValueError, requests.RequestException) as error:
        flash(str(error) or "No se pudo obtener el comprobante.", "danger")
        return redirect(url_for("servicios.services"))
