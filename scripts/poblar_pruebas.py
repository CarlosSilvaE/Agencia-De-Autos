"""Genera servicios y datos ficticios para probar la aplicacion sin reiniciar la base."""
from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models import AgencyModel, DataAccessError
from models.database import MySQLDatabase
from configuration import ConfigurationError, load_project_env


FOLIO_PREFIX = "PRB-SRV-"
PLATE_PREFIX = "PRB-"
SKU_PREFIX = "PRB-REF-"
EMAIL_PREFIX = "prb.cliente."
NAMES = ("Ana", "Luis", "Maria", "Carlos", "Sofia", "Jorge", "Elena", "Pedro", "Lucia", "Hector")
SURNAMES = ("Lopez", "Garcia", "Martinez", "Ramirez", "Gonzalez", "Torres", "Hernandez", "Flores")
COLORS = ("Blanco", "Negro", "Gris", "Azul", "Rojo", "Plata")
JOBS = (
    "Cambio de aceite y filtro", "Revision general y niveles",
    "Revision de frenos", "Revision de suspension",
    "Diagnostico electrico", "Mantenimiento por kilometraje",
    "Revision de encendido", "Revision de enfriamiento y fugas",
)
TABLES = (
    "clientes", "vehiculos", "refacciones", "servicios", "entregas",
    "servicio_refaccion", "proximos_servicios",
)


def plan_servicio(index: int, today: date, parts: list[dict[str, Any]]) -> dict[str, Any]:
    """Datos repetibles: el folio depende del indice, no de la fecha de ejecucion."""
    if index < 1 or len(parts) < 3:
        raise ValueError("Se requiere un indice positivo y al menos tres refacciones.")
    intake_day = today if index <= 12 else today - timedelta(days=1 + (index * 7) % 120)
    intake = datetime.combine(intake_day, time(hour=8 + index % 10, minute=index % 60))
    selected = []
    if index % 10:
        for offset in range(1 + index % 3):
            part = parts[(index * 7 + offset) % len(parts)]
            selected.append({
                "idRefaccion": part["id_refaccion"],
                "cantidad": 1 + (index + offset) % 3,
                "precioUnitario": part["precio"],
            })
    next_service = None
    if index % 2 == 0:
        days = (-15, 0, 15, 30, 60, 90)[(index // 2 - 1) % 6]
        next_service = {
            "fechaProgramada": today + timedelta(days=days),
            "kilometraje": 20000 + index * 250,
            "notas": "[PRUEBA] Revision programada del servicio " + str(index),
        }
    parts_cost = sum(
        (Decimal(str(part["precioUnitario"])) * part["cantidad"] for part in selected),
        Decimal("0"),
    )
    return {
        "folio": f"{FOLIO_PREFIX}{index:04d}",
        "fecha_ingreso": intake,
        "tipoServicio": "Preventivo" if index % 2 else "Correctivo",
        "estado": AgencyModel.STATES[(index - 1) % 3],
        "descripcion": f"[PRUEBA] {JOBS[(index - 1) % len(JOBS)]}. Caso {index:04d}.",
        "manoObra": Decimal("1500.00"),
        "costo": Decimal("1500.00") + parts_cost,
        "refacciones": selected,
        "proximoServicio": next_service,
    }


def cargar_datos_prueba(
    database: MySQLDatabase, cantidad: int = 100, today: date | None = None,
) -> dict[str, int]:
    if not 1 <= cantidad <= 1000:
        raise ValueError("La cantidad debe estar entre 1 y 1000 servicios.")
    today = today or date.today()
    counts = dict.fromkeys(TABLES, 0)
    model = AgencyModel(database)
    with database.session(transaction=True) as (_, cursor):
        # La conexion libera el bloqueo despues de confirmar o revertir la carga.
        cursor.execute("SELECT GET_LOCK('agencia_pruebas_v1', 10) AS adquirido")
        if cursor.fetchone()["adquirido"] != 1:
            raise ValueError("Otro poblado esta en ejecucion. Intenta nuevamente al terminar.")

        cursor.execute("""
            SELECT mo.id_modelo, mo.id_marca
            FROM modelos mo JOIN marcas ma ON ma.id_marca=mo.id_marca
            WHERE mo.activo=1 AND ma.activo=1 ORDER BY mo.id_modelo
        """)
        models = cursor.fetchall()
        cursor.execute("SELECT id_anio FROM anios WHERE activo=1 AND anio BETWEEN 2020 AND 2026 ORDER BY anio")
        years = cursor.fetchall()
        cursor.execute("""
            SELECT nombre, precio FROM refacciones
            WHERE activo=1 AND sku LIKE 'CAT-%' ORDER BY sku LIMIT 15
        """)
        source_parts = cursor.fetchall()
        if not models or not years or len(source_parts) < 3:
            raise ValueError("Carga primero los catalogos de database/init.sql.")

        def ensure_row(table, identifier, values, keys):
            # Tablas y columnas son constantes internas; todos los valores se parametrizan.
            where = " AND ".join(f"`{key}`=%s" for key in keys)
            cursor.execute(
                f"SELECT * FROM `{table}` WHERE {where} ORDER BY `{identifier}` LIMIT 1",
                tuple(values[key] for key in keys),
            )
            existing = cursor.fetchone()
            if existing is not None:
                return existing
            columns = ", ".join(f"`{key}`" for key in values)
            placeholders = ", ".join(["%s"] * len(values))
            cursor.execute(
                f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})",
                tuple(values.values()),
            )
            counts[table] += 1
            return {**values, identifier: int(cursor.lastrowid)}

        customers = []
        for index in range(1, min(25, cantidad) + 1):
            customers.append(ensure_row("clientes", "id_cliente", {
                "nombre": NAMES[(index - 1) % len(NAMES)],
                "apellido_paterno": SURNAMES[index * 3 % len(SURNAMES)],
                "apellido_materno": SURNAMES[(index * 5 + 1) % len(SURNAMES)],
                "telefono": None,
                "email": f"{EMAIL_PREFIX}{index:03d}@example.invalid",
            }, ("email",)))

        vehicles = []
        for index in range(1, min(30, cantidad) + 1):
            customer = customers[(index - 1) % len(customers)]
            selected_model = models[(index - 1) % len(models)]
            vehicles.append(ensure_row("vehiculos", "id_vehiculo", {
                "id_cliente": customer["id_cliente"],
                "id_marca": selected_model["id_marca"],
                "id_modelo": selected_model["id_modelo"],
                "id_anio": years[(index - 1) % len(years)]["id_anio"],
                "placas": f"{PLATE_PREFIX}{index:04d}",
                "color": COLORS[(index - 1) % len(COLORS)],
                "vin": model._validate_vin(f"PRBCARABC{index:08d}"),
            }, ("placas",)))

        parts = []
        for index, source in enumerate(source_parts, 1):
            part = ensure_row("refacciones", "id_refaccion", {
                "nombre": "[PRUEBA] " + source["nombre"],
                "sku": f"{SKU_PREFIX}{index:03d}",
                "cantidad": 300,
                "precio": source["precio"],
            }, ("sku",))
            if part.get("activo", True):
                parts.append(part)
        for suffix, name, stock in (("CERO", "Pieza sin existencia", 0), ("UNO", "Pieza con ultima unidad", 1)):
            ensure_row("refacciones", "id_refaccion", {
                "nombre": "[PRUEBA] " + name, "sku": SKU_PREFIX + suffix,
                "cantidad": stock, "precio": Decimal("100.00"),
            }, ("sku",))
        if len(parts) < 3:
            raise ValueError("Se requieren al menos tres refacciones de prueba activas.")

        for index in range(1, cantidad + 1):
            folio = f"{FOLIO_PREFIX}{index:04d}"
            cursor.execute("SELECT id_servicio FROM servicios WHERE folio=%s", (folio,))
            if cursor.fetchone() is not None:
                continue
            vehicle = vehicles[(index - 1) % len(vehicles)]
            cursor.execute("SELECT * FROM clientes WHERE id_cliente=%s", (vehicle["id_cliente"],))
            customer = cursor.fetchone()
            if customer is None:
                raise ValueError("No se encontro el propietario de un vehiculo de prueba.")
            if not vehicle.get("activo", True) or not customer.get("activo", True):
                raise ValueError(
                    "Un cliente o vehiculo de prueba esta desactivado. "
                    "Reactivalo antes de generar nuevos servicios relacionados."
                )
            plan = plan_servicio(index, today, parts)
            third_party = index % 4 == 0 or index % 10 == 0
            owner = " ".join(str(customer.get(key) or "") for key in ("nombre", "apellido_paterno", "apellido_materno")).strip()
            delivery = {
                "nombre": f"Familiar de prueba {index:03d}" if third_party else owner,
                "telefono": None,
                "relacionPropietario": "Familiar" if third_party else "Propietario",
                "observaciones": f"[PRUEBA] Recepcion del servicio {index:04d}.",
            }
            cursor.execute("""
                INSERT INTO servicios
                    (folio,id_vehiculo,tipo_servicio,descripcion,fecha_ingreso,estado,costo,mano_obra)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (folio, vehicle["id_vehiculo"], plan["tipoServicio"], plan["descripcion"],
                  plan["fecha_ingreso"], plan["estado"], plan["costo"], plan["manoObra"]))
            service_id = int(cursor.lastrowid)
            counts["servicios"] += 1
            if index % 10 == 0:
                cursor.execute("""
                    INSERT INTO entregas (id_servicio,nombre_entrega,relacion_propietario,fecha,observaciones)
                    VALUES (%s,%s,%s,%s,%s)
                """, (service_id, owner, "Propietario", plan["fecha_ingreso"], "[PRUEBA] Recepcion inicial."))
                counts["entregas"] += 1
            model._save_service_relations(cursor, service_id, {**plan, "entrega": delivery})
            cursor.execute("""
                UPDATE entregas SET fecha=%s
                WHERE id_servicio=%s AND observaciones=%s
            """, (plan["fecha_ingreso"] + timedelta(minutes=15), service_id, delivery["observaciones"]))
            counts["entregas"] += 1
            counts["servicio_refaccion"] += len(plan["refacciones"])
            counts["proximos_servicios"] += int(plan["proximoServicio"] is not None)
    return counts


def resumen(database: MySQLDatabase) -> dict[str, Any]:
    with database.session() as (_, cursor):
        cursor.execute("SELECT estado, COUNT(*) AS total FROM servicios WHERE folio LIKE %s GROUP BY estado", (FOLIO_PREFIX + "%",))
        states = {row["estado"]: row["total"] for row in cursor.fetchall()}
        cursor.execute("SELECT COUNT(*) AS total FROM clientes WHERE email LIKE %s", (EMAIL_PREFIX + "%@example.invalid",))
        customers = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM vehiculos WHERE placas LIKE %s", (PLATE_PREFIX + "%",))
        vehicles = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM refacciones WHERE sku LIKE %s", (SKU_PREFIX + "%",))
        parts = cursor.fetchone()["total"]
        cursor.execute("""
            SELECT COUNT(*) AS total FROM proximos_servicios p
            JOIN servicios s ON s.id_servicio=p.id_servicio WHERE s.folio LIKE %s
        """, (FOLIO_PREFIX + "%",))
        upcoming = cursor.fetchone()["total"]
    return {"servicios": sum(states.values()), "estados": states, "clientes": customers,
            "vehiculos": vehicles, "refacciones": parts, "proximos_servicios": upcoming}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cantidad", type=int, default=100, help="Servicios a generar, de 1 a 1000 (por defecto: 100).")
    parser.add_argument("--fecha", type=date.fromisoformat, help="Fecha base AAAA-MM-DD; por defecto, hoy.")
    parser.add_argument("--resumen", action="store_true", help="Consultar los datos de prueba sin modificarlos.")
    args = parser.parse_args()
    try:
        load_project_env()
        database = MySQLDatabase()
        if not args.resumen:
            counts = cargar_datos_prueba(database, args.cantidad, args.fecha)
            print("Carga completada. Registros nuevos:")
            for table, count in counts.items():
                print(f"  {table}: {count}")
        print("Resumen de los datos de prueba:")
        for key, value in resumen(database).items():
            print(f"  {key}: {value}")
    except (DataAccessError, ConfigurationError, ValueError) as error:
        print(f"No se pudo completar la operacion: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
