from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import struct
import uuid
from datetime import date, datetime
from typing import Any

from .database import DataAccessError, MySQLDatabase
from .dashboard_strategy import DailyDashboardStrategy, TotalDashboardStrategy
from .domain import ServiceReceipt
from .schema import migrar_esquema_anio


class AgencyModel:
    """Domain data model backed directly by the Docker-hosted MySQL database."""

    STATES = ("En espera", "En proceso", "Finalizado")
    DASHBOARD_STRATEGIES = {
        "total": TotalDashboardStrategy(),
        "daily": DailyDashboardStrategy(),
    }
    CATALOGS = {
        "marcas": ("marcas", "id_marca", ("nombre",)),
        "modelos": ("modelos", "id_modelo", ("id_marca", "nombre")),
        "anio": ("anio", "id_anio", ("anio",)),
        "refacciones": (
            "refacciones",
            "id_refaccion",
            ("nombre", "sku", "cantidad", "precio"),
        ),
    }

    def __init__(self, database: MySQLDatabase) -> None:
        self.database = database

    def initialize(self, admin_username: str, admin_password: str) -> None:
        with self.database.session() as (connection, _):
            migrar_esquema_anio(connection)
        with self.database.session(transaction=True) as (_, cursor):
            cursor.execute(
                "INSERT IGNORE INTO estados (nombre) VALUES (%s), (%s), (%s)",
                self.STATES,
            )
            for year in range(1980, date.today().year + 3):
                cursor.execute("INSERT IGNORE INTO anio (anio) VALUES (%s)", (year,))
            cursor.execute("SELECT COUNT(*) AS total FROM administradores")
            if cursor.fetchone()["total"] == 0:
                if not admin_username.strip() or len(admin_password) < 8:
                    raise DataAccessError(
                        "Configura ADMIN_INITIAL_USERNAME y ADMIN_INITIAL_PASSWORD "
                        "(minimo 8 caracteres) en .env para el primer inicio."
                    )
                cursor.execute(
                    """
                    INSERT INTO administradores (nombre, usuario, password_hash)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        "Administrador principal",
                        admin_username,
                        self.hash_password(admin_password),
                    ),
                )

    def authenticate(self, username: str, password: str) -> str:
        with self.database.session() as (_, cursor):
            cursor.execute(
                """
                SELECT password_hash FROM administradores
                WHERE usuario=%s AND activo=1 LIMIT 1
                """,
                (username,),
            )
            row = cursor.fetchone()
        if row is None or not self.verify_password(password, row["password_hash"]):
            raise ValueError("Usuario o contrasena incorrectos.")
        return username

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        iterations = 100_000
        subkey = hashlib.pbkdf2_hmac(
            "sha512", password.encode("utf-8"), salt, iterations, dklen=32
        )
        payload = struct.pack(">BIII", 1, 2, iterations, len(salt)) + salt + subkey
        return base64.b64encode(payload).decode("ascii")

    @staticmethod
    def verify_password(password: str, encoded_hash: str) -> bool:
        try:
            payload = base64.b64decode(encoded_hash, validate=True)
            if not payload:
                return False
            if payload[0] == 0:
                if len(payload) != 49:
                    return False
                salt, expected = payload[1:17], payload[17:]
                actual = hashlib.pbkdf2_hmac(
                    "sha1", password.encode("utf-8"), salt, 1_000, dklen=32
                )
                return hmac.compare_digest(actual, expected)
            if payload[0] != 1 or len(payload) < 14:
                return False
            prf, iterations, salt_length = struct.unpack(">III", payload[1:13])
            if iterations <= 0 or salt_length <= 0 or 13 + salt_length >= len(payload):
                return False
            hash_name = {0: "sha1", 1: "sha256", 2: "sha512"}.get(prf)
            if hash_name is None:
                return False
            salt = payload[13 : 13 + salt_length]
            expected = payload[13 + salt_length :]
            actual = hashlib.pbkdf2_hmac(
                hash_name,
                password.encode("utf-8"),
                salt,
                iterations,
                dklen=len(expected),
            )
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError, struct.error):
            return False

    def dashboard(
        self, filter_name: str, day: str | None = None
    ) -> list[dict[str, Any]]:
        # Strategy: las variantes encapsulan sus propias condiciones y parametros SQL.
        strategy = self.DASHBOARD_STRATEGIES.get(str(filter_name).casefold())
        if strategy is None:
            raise ValueError("Filtro de dashboard desconocido.")
        query, parameters = strategy.build(day)
        with self.database.session() as (_, cursor):
            cursor.execute(query, parameters)
            return cursor.fetchall()

    def list_services(self, folio: str = "", owner: str = "") -> list[dict[str, Any]]:
        with self.database.session() as (_, cursor):
            cursor.execute(
                """
                SELECT s.id_servicio, s.folio, s.tipo_servicio, s.descripcion,
                       s.fecha_ingreso, s.fecha_programada, s.estado, s.costo,
                       v.id_vehiculo, v.placas, v.color, v.vin, v.id_marca,
                       v.id_modelo, v.id_anio, m.nombre AS marca,
                       mo.nombre AS modelo, a.anio, c.id_cliente, c.nombre,
                       c.apellido_paterno, c.apellido_materno, c.telefono, c.email,
                       e.nombre_entrega, e.telefono AS telefono_entrega,
                       e.relacion_propietario, e.observaciones AS observaciones_entrega,
                       p.fecha_programada AS proximo_servicio, p.kilometraje,
                       p.notas AS notas_proximo_servicio
                FROM servicios s
                JOIN vehiculos v ON v.id_vehiculo=s.id_vehiculo
                JOIN marcas m ON m.id_marca=v.id_marca
                JOIN modelos mo ON mo.id_modelo=v.id_modelo
                JOIN anio a ON a.id_anio=v.id_anio
                JOIN clientes c ON c.id_cliente=v.id_cliente
                LEFT JOIN entregas e ON e.id_entrega=(
                    SELECT MAX(e2.id_entrega) FROM entregas e2
                    WHERE e2.id_servicio=s.id_servicio
                )
                LEFT JOIN proximos_servicios p ON p.id_proximo_servicio=(
                    SELECT MAX(p2.id_proximo_servicio) FROM proximos_servicios p2
                    WHERE p2.id_servicio=s.id_servicio
                )
                WHERE (%s='' OR s.folio=%s)
                  AND (%s='' OR CONCAT_WS(' ', c.nombre, c.apellido_paterno,
                       c.apellido_materno) LIKE CONCAT('%%', %s, '%%'))
                ORDER BY s.fecha_ingreso DESC
                """,
                (folio, folio, owner, owner),
            )
            return cursor.fetchall()

    def service_options(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        return self.list_vehicles(), self.list_catalog("refacciones")

    def service_receipt(self, folio: str) -> ServiceReceipt:
        rows = self.list_services(folio=folio)
        if not rows:
            raise DataAccessError("No se encontro el servicio solicitado.")
        return ServiceReceipt.from_records(rows[0], self.service_parts(folio))

    def delivery_history(self, folio: str) -> list[dict[str, Any]]:
        with self.database.session() as (_, cursor):
            cursor.execute(
                """SELECT e.fecha, e.nombre_entrega, e.telefono,
                          e.relacion_propietario, e.observaciones
                   FROM entregas e JOIN servicios s ON s.id_servicio=e.id_servicio
                   WHERE s.folio=%s ORDER BY e.id_entrega DESC""",
                (folio,),
            )
            return cursor.fetchall()

    def service_parts(self, folio: str) -> list[dict[str, Any]]:
        with self.database.session() as (_, cursor):
            cursor.execute(
                """
                SELECT sr.id_refaccion, sr.cantidad, sr.precio_unitario,
                       r.nombre, r.sku
                FROM servicio_refaccion sr
                JOIN refacciones r ON r.id_refaccion=sr.id_refaccion
                JOIN servicios s ON s.id_servicio=sr.id_servicio
                WHERE s.folio=%s
                """,
                (folio,),
            )
            return cursor.fetchall()

    def create_service(self, payload: dict[str, Any]) -> dict[str, str]:
        self._validate_service(payload)
        folio = payload.get("folio") or (
            f"SRV-{datetime.utcnow():%Y%m%d%H%M%S%f}-{uuid.uuid4().hex[:6]}"
        )
        with self.database.session(transaction=True) as (connection, cursor):
            client_id = self._save_client(cursor, payload["cliente"])
            vehicle_id = self._save_vehicle(cursor, payload["vehiculo"], client_id)
            cursor.execute(
                """
                INSERT INTO servicios
                    (folio,id_vehiculo,tipo_servicio,descripcion,estado,costo)
                VALUES (%s,%s,%s,%s,%s,%s)
                """,
                (
                    folio,
                    vehicle_id,
                    payload["tipoServicio"],
                    payload["descripcion"].strip(),
                    payload["estado"],
                    payload["costo"],
                ),
            )
            self._save_service_relations(
                cursor, int(cursor.lastrowid), payload
            )
        return {"folio": folio}

    def update_service(self, folio: str, payload: dict[str, Any]) -> None:
        self._validate_service(payload)
        with self.database.session(transaction=True) as (_, cursor):
            cursor.execute(
                "SELECT id_servicio FROM servicios WHERE folio=%s",
                (folio,),
            )
            service = cursor.fetchone()
            if service is None:
                raise DataAccessError("No se encontro el servicio solicitado.")
            service_id = int(service["id_servicio"])
            client_id = self._save_client(cursor, payload["cliente"])
            vehicle_id = self._save_vehicle(cursor, payload["vehiculo"], client_id)
            cursor.execute(
                """
                UPDATE servicios
                SET id_vehiculo=%s, tipo_servicio=%s, descripcion=%s,
                    estado=%s, costo=%s
                WHERE id_servicio=%s
                """,
                (
                    vehicle_id,
                    payload["tipoServicio"],
                    payload["descripcion"].strip(),
                    payload["estado"],
                    payload["costo"],
                    service_id,
                ),
            )
            self._save_service_relations(cursor, service_id, payload)

    def update_service_status(self, folio: str, status: str) -> None:
        if status not in self.STATES:
            raise ValueError("Estado invalido.")
        with self.database.session() as (connection, cursor):
            cursor.execute(
                "UPDATE servicios SET estado=%s WHERE folio=%s",
                (status, folio),
            )
            if cursor.rowcount == 0:
                cursor.execute("SELECT 1 FROM servicios WHERE folio=%s", (folio,))
                if cursor.fetchone() is None:
                    raise DataAccessError("No se encontro el servicio solicitado.")
            connection.commit()

    def delete_service(self, folio: str) -> None:
        with self.database.session(transaction=True) as (_, cursor):
            cursor.execute(
                "SELECT id_servicio FROM servicios WHERE folio=%s",
                (folio,),
            )
            service = cursor.fetchone()
            if service is None:
                raise DataAccessError("No se encontro el servicio solicitado.")
            service_id = int(service["id_servicio"])
            cursor.execute(
                """
                SELECT id_refaccion, cantidad FROM servicio_refaccion
                WHERE id_servicio=%s
                """,
                (service_id,),
            )
            for part in cursor.fetchall():
                cursor.execute(
                    "UPDATE refacciones SET cantidad=cantidad+%s WHERE id_refaccion=%s",
                    (part["cantidad"], part["id_refaccion"]),
                )
            for table in ("servicio_refaccion", "entregas", "proximos_servicios"):
                cursor.execute(f"DELETE FROM {table} WHERE id_servicio=%s", (service_id,))
            cursor.execute("DELETE FROM servicios WHERE id_servicio=%s", (service_id,))

    def list_upcoming(self, folio: str = "", owner: str = "") -> list[dict[str, Any]]:
        with self.database.session() as (_, cursor):
            cursor.execute(
                """
                SELECT p.*, s.folio, v.placas, c.nombre,
                       c.apellido_paterno, c.apellido_materno
                FROM proximos_servicios p
                JOIN servicios s ON s.id_servicio=p.id_servicio
                JOIN vehiculos v ON v.id_vehiculo=s.id_vehiculo
                JOIN clientes c ON c.id_cliente=v.id_cliente
                WHERE (%s='' OR s.folio=%s)
                  AND (%s='' OR CONCAT_WS(' ', c.nombre, c.apellido_paterno,
                       c.apellido_materno) LIKE CONCAT('%%', %s, '%%'))
                ORDER BY p.fecha_programada
                """,
                (folio, folio, owner, owner),
            )
            return cursor.fetchall()

    def customer_vehicle_data(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
        customers = self.list_customers()
        vehicles = self.list_vehicles()
        catalogs = {
            name: self.list_catalog(name)
            for name in ("marcas", "modelos", "anio")
        }
        return customers, vehicles, catalogs

    def list_customers(self) -> list[dict[str, Any]]:
        with self.database.session() as (_, cursor):
            cursor.execute(
                """
                SELECT * FROM clientes WHERE activo=1
                ORDER BY nombre, apellido_paterno
                """
            )
            return cursor.fetchall()

    def save_customer(
        self, payload: dict[str, Any], customer_id: int | None = None
    ) -> None:
        if not payload.get("nombre", "").strip() or not payload.get(
            "apellidoPaterno", ""
        ).strip():
            raise ValueError("Nombre y apellido paterno son obligatorios.")
        values = (
            payload["nombre"].strip(),
            payload["apellidoPaterno"].strip(),
            payload.get("apellidoMaterno"),
            payload.get("telefono"),
            payload.get("email"),
        )
        with self.database.session() as (connection, cursor):
            if customer_id is None:
                cursor.execute(
                    """
                    INSERT INTO clientes
                        (nombre,apellido_paterno,apellido_materno,telefono,email)
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    values,
                )
            else:
                cursor.execute(
                    """
                    UPDATE clientes SET nombre=%s, apellido_paterno=%s,
                        apellido_materno=%s, telefono=%s, email=%s
                    WHERE id_cliente=%s AND activo=1
                    """,
                    (*values, customer_id),
                )
                self._require_existing_update(
                    cursor, cursor.rowcount, "clientes", "id_cliente", customer_id,
                    "No se encontro el cliente."
                )
            connection.commit()

    def delete_customer(self, customer_id: int) -> None:
        with self.database.session() as (connection, cursor):
            cursor.execute(
                "UPDATE clientes SET activo=0 WHERE id_cliente=%s AND activo=1",
                (customer_id,),
            )
            self._require_existing(cursor, cursor.rowcount, "No se encontro el cliente.")
            connection.commit()

    def list_vehicles(self) -> list[dict[str, Any]]:
        with self.database.session() as (_, cursor):
            cursor.execute(
                """
                SELECT v.*, c.nombre, c.apellido_paterno, c.apellido_materno,
                       c.telefono, c.email, m.nombre AS marca, mo.nombre AS modelo,
                       a.anio
                FROM vehiculos v
                JOIN clientes c ON c.id_cliente=v.id_cliente
                JOIN marcas m ON m.id_marca=v.id_marca
                JOIN modelos mo ON mo.id_modelo=v.id_modelo
                JOIN anio a ON a.id_anio=v.id_anio
                WHERE v.activo=1 AND c.activo=1
                ORDER BY v.placas
                """
            )
            return cursor.fetchall()

    def save_vehicle(
        self, payload: dict[str, Any], vehicle_id: int | None = None
    ) -> None:
        if not payload.get("placas", "").strip():
            raise ValueError("Las placas son obligatorias.")
        with self.database.session() as (connection, cursor):
            cursor.execute(
                """
                SELECT COUNT(*) AS total FROM modelos
                WHERE id_modelo=%s AND id_marca=%s AND activo=1
                """,
                (payload["idModelo"], payload["idMarca"]),
            )
            if cursor.fetchone()["total"] == 0:
                raise ValueError("El modelo seleccionado no pertenece a la marca.")
            values = (
                payload["idCliente"],
                payload["idMarca"],
                payload["idModelo"],
                payload["idAnio"],
                payload["placas"].strip(),
                payload.get("color"),
                payload.get("vin"),
            )
            if vehicle_id is None:
                cursor.execute(
                    """
                    INSERT INTO vehiculos
                        (id_cliente,id_marca,id_modelo,id_anio,placas,color,vin)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    values,
                )
            else:
                cursor.execute(
                    """
                    UPDATE vehiculos SET id_cliente=%s, id_marca=%s,
                        id_modelo=%s, id_anio=%s, placas=%s, color=%s, vin=%s
                    WHERE id_vehiculo=%s AND activo=1
                    """,
                    (*values, vehicle_id),
                )
                self._require_existing_update(
                    cursor, cursor.rowcount, "vehiculos", "id_vehiculo", vehicle_id,
                    "No se encontro el vehiculo."
                )
            connection.commit()

    def delete_vehicle(self, vehicle_id: int) -> None:
        with self.database.session() as (connection, cursor):
            cursor.execute(
                "UPDATE vehiculos SET activo=0 WHERE id_vehiculo=%s AND activo=1",
                (vehicle_id,),
            )
            self._require_existing(cursor, cursor.rowcount, "No se encontro el vehiculo.")
            connection.commit()

    def list_catalog(self, catalog: str) -> list[dict[str, Any]]:
        table, identifier, _ = self._catalog_definition(catalog)
        with self.database.session() as (_, cursor):
            cursor.execute(
                f"SELECT * FROM `{table}` WHERE activo=1 ORDER BY `{identifier}` DESC"
            )
            return cursor.fetchall()

    def save_catalog_item(
        self,
        catalog: str,
        payload: dict[str, Any],
        item_id: int | None = None,
    ) -> None:
        table, identifier, fields = self._catalog_definition(catalog)
        for field in fields:
            value = payload.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                if catalog == "refacciones" and field == "sku":
                    continue
                raise ValueError(f"El campo {field} es obligatorio.")
        with self.database.session() as (connection, cursor):
            if item_id is None:
                names = ", ".join(f"`{field}`" for field in fields)
                placeholders = ", ".join(["%s"] * len(fields))
                cursor.execute(
                    f"INSERT INTO `{table}` ({names}) VALUES ({placeholders})",
                    tuple(payload.get(field) for field in fields),
                )
            else:
                assignments = ", ".join(f"`{field}`=%s" for field in fields)
                cursor.execute(
                    f"UPDATE `{table}` SET {assignments} "
                    f"WHERE `{identifier}`=%s AND activo=1",
                    (*[payload.get(field) for field in fields], item_id),
                )
                self._require_existing_update(
                    cursor, cursor.rowcount, table, identifier, item_id,
                    "No se encontro el registro."
                )
            connection.commit()

    def delete_catalog_item(self, catalog: str, item_id: int) -> None:
        table, identifier, _ = self._catalog_definition(catalog)
        with self.database.session() as (connection, cursor):
            cursor.execute(
                f"UPDATE `{table}` SET activo=0 WHERE `{identifier}`=%s AND activo=1",
                (item_id,),
            )
            self._require_existing(cursor, cursor.rowcount, "No se encontro el registro.")
            connection.commit()

    def list_admins(self) -> list[dict[str, Any]]:
        with self.database.session() as (_, cursor):
            cursor.execute(
                """
                SELECT id_administrador, nombre, usuario, activo
                FROM administradores ORDER BY nombre
                """
            )
            return cursor.fetchall()

    def save_admin(
        self, payload: dict[str, Any], admin_id: int | None = None
    ) -> None:
        name = str(payload.get("nombre") or "").strip()
        username = str(payload.get("usuario") or "").strip()
        password = payload.get("password")
        active = bool(payload.get("activo", True))
        if not name or not username:
            raise ValueError("Nombre y usuario son obligatorios.")
        if admin_id is None and (not password or len(password) < 8):
            raise ValueError("La contrasena debe tener al menos 8 caracteres.")
        if password and len(password) < 8:
            raise ValueError("La contrasena debe tener al menos 8 caracteres.")
        with self.database.session(transaction=True) as (_, cursor):
            if admin_id is not None and not active:
                self._ensure_another_active_admin(cursor, admin_id)
            if admin_id is None:
                cursor.execute(
                    """
                    INSERT INTO administradores (nombre,usuario,password_hash,activo)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (name, username, self.hash_password(password), active),
                )
            else:
                if password:
                    cursor.execute(
                        """
                        UPDATE administradores
                        SET nombre=%s, usuario=%s, password_hash=%s, activo=%s
                        WHERE id_administrador=%s
                        """,
                        (name, username, self.hash_password(password), active, admin_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE administradores
                        SET nombre=%s, usuario=%s, activo=%s
                        WHERE id_administrador=%s
                        """,
                        (name, username, active, admin_id),
                    )
                self._require_existing_update(
                    cursor, cursor.rowcount, "administradores", "id_administrador",
                    admin_id, "No se encontro el administrador.", active_only=False,
                )

    def delete_admin(self, admin_id: int) -> None:
        with self.database.session(transaction=True) as (_, cursor):
            self._ensure_another_active_admin(cursor, admin_id)
            cursor.execute(
                """
                UPDATE administradores SET activo=0
                WHERE id_administrador=%s AND activo=1
                """,
                (admin_id,),
            )
            self._require_existing(cursor, cursor.rowcount, "No se encontro el administrador.")

    def _save_client(self, cursor: Any, payload: dict[str, Any]) -> int:
        name = str(payload.get("nombre") or "").strip()
        surname = str(payload.get("apellidoPaterno") or "").strip()
        if not name or not surname:
            raise ValueError("Se requiere el nombre y apellido del propietario.")
        values = (
            name,
            surname,
            payload.get("apellidoMaterno"),
            payload.get("telefono"),
            payload.get("email"),
        )
        client_id = payload.get("id")
        if client_id is None:
            cursor.execute(
                """
                INSERT INTO clientes
                    (nombre,apellido_paterno,apellido_materno,telefono,email)
                VALUES (%s,%s,%s,%s,%s)
                """,
                values,
            )
            return int(cursor.lastrowid)
        cursor.execute(
            """
            UPDATE clientes SET nombre=%s, apellido_paterno=%s,
                apellido_materno=%s, telefono=%s, email=%s
            WHERE id_cliente=%s AND activo=1
            """,
            (*values, client_id),
        )
        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT 1 FROM clientes WHERE id_cliente=%s AND activo=1",
                (client_id,),
            )
            if cursor.fetchone() is None:
                raise ValueError("El propietario seleccionado ya no existe.")
        return int(client_id)

    def _save_vehicle(
        self, cursor: Any, payload: dict[str, Any], client_id: int
    ) -> int:
        if not str(payload.get("placas") or "").strip():
            raise ValueError("Se requieren las placas del vehiculo.")
        cursor.execute(
            """
            SELECT COUNT(*) AS total FROM modelos
            WHERE id_modelo=%s AND id_marca=%s AND activo=1
            """,
            (payload["idModelo"], payload["idMarca"]),
        )
        if cursor.fetchone()["total"] == 0:
            raise ValueError("El modelo seleccionado no pertenece a la marca.")
        values = (
            client_id,
            payload["idMarca"],
            payload["idModelo"],
            payload["idAnio"],
            payload["placas"].strip(),
            payload.get("color"),
            payload.get("vin"),
        )
        vehicle_id = payload.get("id")
        if vehicle_id is None:
            cursor.execute(
                """
                INSERT INTO vehiculos
                    (id_cliente,id_marca,id_modelo,id_anio,placas,color,vin)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                values,
            )
            return int(cursor.lastrowid)
        cursor.execute(
            """
            UPDATE vehiculos SET id_cliente=%s, id_marca=%s, id_modelo=%s,
                id_anio=%s, placas=%s, color=%s, vin=%s
            WHERE id_vehiculo=%s AND activo=1
            """,
            (*values, vehicle_id),
        )
        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT 1 FROM vehiculos WHERE id_vehiculo=%s AND activo=1",
                (vehicle_id,),
            )
            if cursor.fetchone() is None:
                raise ValueError("El vehiculo seleccionado ya no existe.")
        return int(vehicle_id)

    def _save_service_relations(
        self, cursor: Any, service_id: int, payload: dict[str, Any]
    ) -> None:
        cursor.execute(
            "SELECT id_refaccion, cantidad FROM servicio_refaccion WHERE id_servicio=%s",
            (service_id,),
        )
        for part in cursor.fetchall():
            cursor.execute(
                "UPDATE refacciones SET cantidad=cantidad+%s WHERE id_refaccion=%s",
                (part["cantidad"], part["id_refaccion"]),
            )
        cursor.execute(
            "DELETE FROM servicio_refaccion WHERE id_servicio=%s", (service_id,)
        )
        for part in payload.get("refacciones") or []:
            quantity = int(part["cantidad"])
            if quantity <= 0 or float(part["precioUnitario"]) < 0:
                raise ValueError("Las cantidades deben ser positivas y los precios no negativos.")
            cursor.execute(
                """
                UPDATE refacciones SET cantidad=cantidad-%s
                WHERE id_refaccion=%s AND activo=1 AND cantidad >= %s
                """,
                (quantity, part["idRefaccion"], quantity),
            )
            if cursor.rowcount == 0:
                raise ValueError(
                    "No hay inventario suficiente para una refaccion seleccionada."
                )
            cursor.execute(
                """
                INSERT INTO servicio_refaccion
                    (id_servicio,id_refaccion,cantidad,precio_unitario)
                VALUES (%s,%s,%s,%s)
                """,
                (
                    service_id,
                    part["idRefaccion"],
                    quantity,
                    part["precioUnitario"],
                ),
            )
        delivery = payload["entrega"]
        deliverer = str(delivery.get("nombre") or "").strip()
        if not deliverer:
            raise ValueError("Se requiere identificar a la persona que entrega el vehiculo.")
        cursor.execute(
            """SELECT nombre_entrega, telefono, relacion_propietario, observaciones
               FROM entregas WHERE id_servicio=%s
               ORDER BY id_entrega DESC LIMIT 1""",
            (service_id,),
        )
        last_delivery = cursor.fetchone()
        delivery_values = (
            deliverer, delivery.get("telefono"), delivery.get("relacionPropietario"),
            delivery.get("observaciones"),
        )
        if last_delivery is None or delivery_values != tuple(
            last_delivery.get(key) for key in
            ("nombre_entrega", "telefono", "relacion_propietario", "observaciones")
        ):
            cursor.execute(
                """INSERT INTO entregas
                   (id_servicio,nombre_entrega,telefono,relacion_propietario,observaciones)
                   VALUES (%s,%s,%s,%s,%s)""",
                (service_id, *delivery_values),
            )
        cursor.execute(
            "DELETE FROM proximos_servicios WHERE id_servicio=%s", (service_id,)
        )
        next_service = payload.get("proximoServicio")
        if next_service:
            cursor.execute(
                """
                INSERT INTO proximos_servicios
                    (id_servicio,fecha_programada,kilometraje,notas)
                VALUES (%s,%s,%s,%s)
                """,
                (
                    service_id,
                    next_service["fechaProgramada"],
                    next_service.get("kilometraje"),
                    next_service.get("notas"),
                ),
            )

    def _ensure_another_active_admin(self, cursor: Any, admin_id: int) -> None:
        cursor.execute(
            "SELECT id_administrador FROM administradores WHERE activo=1 FOR UPDATE"
        )
        active_ids = [row["id_administrador"] for row in cursor.fetchall()]
        if admin_id in active_ids and len(active_ids) <= 1:
            raise DataAccessError("Debe permanecer al menos un administrador activo.")

    @staticmethod
    def _require_existing_update(
        cursor: Any, affected: int, table: str, identifier: str, item_id: int,
        message: str, active_only: bool = True,
    ) -> None:
        if affected:
            return
        # Los nombres provienen exclusivamente de las constantes internas (allowlist).
        allowed = {
            ("clientes", "id_cliente"),
            ("vehiculos", "id_vehiculo"),
            ("administradores", "id_administrador"),
            ("marcas", "id_marca"),
            ("modelos", "id_modelo"),
            ("anio", "id_anio"),
            ("refacciones", "id_refaccion"),
        }
        if (table, identifier) not in allowed:
            raise ValueError("Tabla o identificador no permitidos.")
        active_clause = " AND activo=1" if active_only else ""
        cursor.execute(
            f"SELECT 1 FROM `{table}` WHERE `{identifier}`=%s{active_clause}",
            (item_id,),
        )
        if cursor.fetchone() is None:
            raise DataAccessError(message)

    @staticmethod
    def _require_existing(cursor: Any, affected: int, message: str) -> None:
        if affected == 0:
            raise DataAccessError(message)

    @classmethod
    def _catalog_definition(cls, catalog: str) -> tuple[str, str, tuple[str, ...]]:
        try:
            return cls.CATALOGS[catalog]
        except KeyError as error:
            raise ValueError("Catalogo desconocido.") from error

    @classmethod
    def _validate_service(cls, payload: dict[str, Any]) -> None:
        if not str(payload.get("descripcion") or "").strip():
            raise ValueError("La descripcion es obligatoria.")
        if payload.get("tipoServicio") not in ("Preventivo", "Correctivo"):
            raise ValueError("El tipo de servicio debe ser Preventivo o Correctivo.")
        if payload.get("estado") not in cls.STATES:
            raise ValueError("El estado debe ser En espera, En proceso o Finalizado.")
        if float(payload.get("costo") or 0) < 0:
            raise ValueError("El costo no puede ser negativo.")
        if not isinstance(payload.get("cliente"), dict):
            raise ValueError("Se requiere el propietario.")
        if not isinstance(payload.get("vehiculo"), dict):
            raise ValueError("Se requiere el vehiculo.")
        if not isinstance(payload.get("entrega"), dict):
            raise ValueError("Se requiere identificar a la persona que entrega el vehiculo.")

