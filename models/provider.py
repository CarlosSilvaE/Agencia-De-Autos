"""Singleton: una instancia de proveedor; conexiones MySQL independientes por operación.

No se comparte una conexión/cursor entre sesiones (evita transacciones cruzadas).
"""
from __future__ import annotations

from threading import Lock
from .database import MySQLDatabase


class DatabaseProvider:
    _instance: DatabaseProvider | None = None
    _lock = Lock()

    def __new__(cls) -> DatabaseProvider:
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._database = MySQLDatabase()
                cls._instance = instance
        return cls._instance

    @property
    def database(self) -> MySQLDatabase:
        """MySQLDatabase crea y cierra cada conexión mediante session()."""
        return self._database
