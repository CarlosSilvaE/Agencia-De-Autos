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
            "user": os.getenv("MYSQL_USER", "agencia"),
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
        cursor = connection.cursor(dictionary=True)
        try:
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
            cursor.close()
            connection.close()

    @staticmethod
    def translate_error(error: MySQLError) -> DataAccessError:
        messages = {
            1062: "El registro ya existe; revisa los valores unicos.",
            1451: "No se puede desactivar o eliminar porque hay registros asociados.",
            1452: "Una referencia seleccionada no existe o no es valida.",
        }
        message = messages.get(error.errno, "Ocurrio un error al acceder a MySQL.")
        return DataAccessError(f"{message} ({error})")

