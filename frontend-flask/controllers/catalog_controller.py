import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from controllers.api_client import api_request

catalog_bp = Blueprint("catalogos", __name__)

CATALOGS = {
    "marcas": {"title": "Marcas", "id": "id_marca", "fields": [("nombre", "Nombre", "text")]},
    "modelos": {"title": "Modelos", "id": "id_modelo", "fields": [("id_marca", "Marca", "select"), ("nombre", "Nombre", "text")]},
    "anos": {"title": "Años", "id": "id_ano", "fields": [("ano", "Año", "number")]},
    "refacciones": {"title": "Refacciones", "id": "id_refaccion", "fields": [
        ("nombre", "Nombre", "text"), ("sku", "SKU", "text"),
        ("cantidad", "Existencia", "number"), ("precio", "Precio", "number"),
    ]},
}


def signed_in():
    return bool(session.get("user"))


@catalog_bp.get("/catalogos")
def catalogs():
    if not signed_in():
        return redirect(url_for("auth.login"))
    return render_template("catalogos.html", catalogs=CATALOGS)


@catalog_bp.route("/catalogos/<catalogo>", methods=["GET", "POST"])
def catalog(catalogo):
    if not signed_in():
        return redirect(url_for("auth.login"))
    definition = CATALOGS.get(catalogo)
    if definition is None:
        return redirect(url_for("catalogos.catalogs"))
    api_path = f"/api/catalogos/{catalogo}"
    try:
        if request.method == "POST":
            action = request.form.get("action")
            item_id = request.form.get("id")
            if action == "delete":
                api_request("DELETE", f"{api_path}/{item_id}")
                flash("Registro eliminado.", "success")
            else:
                values = {}
                for field, _, field_type in definition["fields"]:
                    value = request.form.get(field, "").strip()
                    values[field] = int(value) if field_type == "number" and value else (value or None)
                if catalogo == "refacciones":
                    values["precio"] = float(request.form.get("precio") or 0)
                    values["cantidad"] = int(request.form.get("cantidad") or 0)
                if item_id:
                    api_request("PUT", f"{api_path}/{item_id}", json=values)
                    flash("Registro actualizado.", "success")
                else:
                    api_request("POST", api_path, json=values)
                    flash("Registro creado.", "success")
            return redirect(url_for("catalogos.catalog", catalogo=catalogo))

        items = api_request("GET", api_path)
        brands = api_request("GET", "/api/catalogos/marcas") if catalogo == "modelos" else []
        editing_id = request.args.get("editar")
        editing = next((item for item in items if str(item[definition["id"]]) == editing_id), None)
        return render_template(
            "catalogo.html", catalogo=catalogo, definition=definition,
            items=items, brands=brands, editing=editing,
        )
    except (ValueError, requests.RequestException) as error:
        flash(str(error) or "No se pudo completar la operación.", "danger")
        if request.method == "POST":
            return redirect(url_for("dashboard.dashboard"))
        return render_template(
            "catalogo.html", catalogo=catalogo, definition=definition,
            items=[], brands=[], editing=None,
        )
