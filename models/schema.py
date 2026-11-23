"""Preparacion repetible del esquema sin recrear el volumen ni borrar registros."""
from pathlib import Path

from .database import DataAccessError, MySQLDatabase

ROOT = Path(__file__).resolve().parents[1]


def execute_script(cursor, source: str) -> None:
    cursor.execute(source)
    while True:
        if cursor.with_rows:
            cursor.fetchall()
        if not cursor.nextset():
            break


def normalize_years(cursor) -> None:
    cursor.execute("""
        SELECT TABLE_NAME FROM information_schema.TABLES
        WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ('ano','anos','anio','anios')
    """)
    tables = [row["TABLE_NAME"] for row in cursor.fetchall()]
    if len(tables) > 1:
        raise DataAccessError("Hay varios catalogos de anios. Revisa sus nombres antes de preparar la base.")
    if not tables:
        return
    source = tables[0]
    cursor.execute("""
        SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN (%s,'vehiculos')
    """, (source,))
    columns = {}
    for row in cursor.fetchall():
        columns.setdefault(row["TABLE_NAME"], set()).add(row["COLUMN_NAME"])
    changes = []
    for old, new in (("id_ano", "id_anio"), ("ano", "anio")):
        if len(columns[source] & {old, new}) != 1:
            raise DataAccessError(f"Revisa las columnas {old}/{new} del catalogo de anios.")
        if old in columns[source]:
            changes.append(f"RENAME COLUMN `{old}` TO `{new}`")
    vehicle_columns = columns.get("vehiculos", set())
    if vehicle_columns and len(vehicle_columns & {"id_ano", "id_anio"}) != 1:
        raise DataAccessError("Revisa las columnas id_ano/id_anio de vehiculos.")
    if source != "anios":
        changes.append("RENAME TO `anios`")
    if changes:
        cursor.execute(f"ALTER TABLE `{source}` " + ", ".join(changes))
    if "id_ano" in vehicle_columns:
        cursor.execute("ALTER TABLE vehiculos RENAME COLUMN id_ano TO id_anio")


def prepare_schema(database: MySQLDatabase) -> None:
    with database.session() as (connection, cursor):
        cursor.execute("SELECT GET_LOCK('agencia_schema_v1',30) AS adquirido")
        if cursor.fetchone()["adquirido"] != 1:
            raise DataAccessError("Otra preparacion esta en ejecucion. Espera a que termine.")
        try:
            normalize_years(cursor)
            execute_script(cursor, (ROOT / "database" / "init.sql").read_text(encoding="utf-8"))
            cursor.execute("""
                SELECT IS_NULLABLE FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='servicios' AND COLUMN_NAME='mano_obra'
            """)
            labor = cursor.fetchone()
            if labor is None:
                execute_script(cursor, (ROOT / "database" / "migrations" / "002_mano_obra.sql").read_text(encoding="utf-8"))
            elif labor["IS_NULLABLE"] == "YES":
                cursor.execute("""
                    UPDATE servicios s LEFT JOIN (
                        SELECT id_servicio,SUM(cantidad*precio_unitario) AS subtotal
                        FROM servicio_refaccion GROUP BY id_servicio
                    ) piezas ON piezas.id_servicio=s.id_servicio
                    SET s.mano_obra=GREATEST(0,s.costo-COALESCE(piezas.subtotal,0))
                    WHERE s.mano_obra IS NULL
                """)
                cursor.execute("ALTER TABLE servicios MODIFY COLUMN mano_obra DECIMAL(12,2) NOT NULL DEFAULT 1500.00")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
