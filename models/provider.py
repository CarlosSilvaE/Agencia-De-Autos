"""Singleton: una instancia de proveedor; conexiones MySQL independientes por operacion.

No se comparte una conexion/cursor entre sesiones (evita transacciones cruzadas).
"""
from __future__ import annotations

from threading import Lock
from .database import MySQLDatabase


class DatabaseProvider:
    # Singleton: reutiliza una sola instancia del proveedor de MySQL.
    _instance: DatabaseProvider | None = None
    _lock = Lock()

    def __new__(cls) -> DatabaseProvider:
        # Crea el proveedor una sola vez y reutiliza la misma instancia.
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._database = MySQLDatabase()
                cls._instance = instance
        return cls._instance

    @property
    def database(self) -> MySQLDatabase:
        """MySQLDatabase crea y cierra cada conexion mediante session()."""
        # Entrega el gestor compartido de conexiones MySQL.
        return self._database
