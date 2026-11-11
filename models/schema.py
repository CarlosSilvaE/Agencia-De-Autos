"""Migracion de los nombres antiguos de anios sin borrar ni recrear registros."""
from __future__ import annotations

from mysql.connector import MySQLConnection

from .database import DataAccessError


def migrar_esquema_anio(connection: MySQLConnection) -> None:
    """Ejecutar en una conexion sin transaccion de negocio abierta.

    MySQL confirma los ALTER TABLE por separado. Cada paso comprueba el esquema
    existente, por lo que puede retomarse si una ejecucion se interrumpe.
    """
    if connection.in_transaction:
        raise DataAccessError("La migracion de anio debe ejecutarse antes de iniciar una transaccion.")
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ('ano','anos','anios','anio')"
        )
        tables = [row[0] for row in cursor.fetchall()]
        if len(tables) != 1:
            raise DataAccessError(
                "Debe existir una sola tabla de anios (ano, anos, anios o anio). "
                "Inicializa la base o revisa las tablas antes de continuar."
            )
        source = tables[0]
        cursor.execute(
            "SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN (%s,'vehiculos')",
            (source,),
        )
        columns: dict[str, set[str]] = {}
        for table, column in cursor.fetchall():
            columns.setdefault(table, set()).add(column)

        changes = []
        for old, new in (("id_ano", "id_anio"), ("ano", "anio")):
            if len(columns.get(source, set()) & {old, new}) != 1:
                raise DataAccessError(f"Revisa las columnas {old}/{new} de la tabla {source}.")
            if old in columns[source]:
                changes.append(f"RENAME COLUMN `{old}` TO `{new}`")
        vehicle_columns = columns.get("vehiculos", set())
        if vehicle_columns and len(vehicle_columns & {"id_ano", "id_anio"}) != 1:
            raise DataAccessError("Revisa las columnas id_ano/id_anio de vehiculos.")
        if source != "anio":
            changes.append("RENAME TO `anio`")
        if changes:
            cursor.execute(f"ALTER TABLE `{source}` " + ", ".join(changes))
        if "id_ano" in vehicle_columns:
            cursor.execute("ALTER TABLE `vehiculos` RENAME COLUMN `id_ano` TO `id_anio`")
        connection.commit()
    finally:
        cursor.close()
