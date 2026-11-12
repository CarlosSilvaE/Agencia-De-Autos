from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector.errors import Error as MySQLError


class DataAccessError(RuntimeError):
    """A database connection or operation failed."""


class MySQLDatabase:
    def __init__(self) -> None:
        self.settings = {
            "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "port": int(os.getenv("MYSQL_PORT", "3307")),
            "database": os.getenv("MYSQL_DATABASE", "agencia_autos"),
            "user": os.getenv("MYSQL_USER", "admin"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "connection_timeout": 10,
        }

    def connect(self) -> MySQLConnection:
        try:
            return mysql.connector.connect(**self.settings)
        except MySQLError as error:
            raise self.translate_error(error) from error

    @contextmanager
    def session(
        self, transaction: bool = False
    ) -> Iterator[tuple[MySQLConnection, Any]]:
        connection = self.connect()
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            if transaction:
                connection.start_transaction()
            yield connection, cursor
            if transaction:
                connection.commit()
        except MySQLError as error:
            if transaction:
                connection.rollback()
            raise self.translate_error(error) from error
        except Exception:
            if transaction:
                connection.rollback()
            raise
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            finally:
                connection.close()

    @staticmethod
    def translate_error(error: MySQLError) -> DataAccessError:
        messages = {
            1045: "MySQL rechazo la cuenta configurada. Revisa .env y ejecuta scripts/preparar_entorno.py.",
            1049: "La base configurada no existe. Ejecuta scripts/preparar_entorno.py.",
            1054: "El esquema esta desactualizado. Ejecuta scripts/preparar_entorno.py para aplicar las migraciones.",
            1146: "Faltan tablas o sus nombres no coinciden. Ejecuta scripts/preparar_entorno.py.",
            2003: "No se pudo conectar a MySQL. Revisa Docker, MYSQL_HOST y MYSQL_PORT.",
            1062: "El registro ya existe; revisa los valores unicos.",
            1451: "No se puede desactivar o eliminar porque hay registros asociados.",
            1452: "Una referencia seleccionada no existe o no es valida.",
        }
        message = messages.get(error.errno, "Ocurrio un error al acceder a MySQL.")
        return DataAccessError(f"{message} ({error})")

