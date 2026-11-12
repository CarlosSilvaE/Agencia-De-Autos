"""Strategy: consultas intercambiables para total de servicios y por fecha."""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date


class DashboardQueryStrategy(ABC):
    @abstractmethod
    # Strategy: establece cómo construir una consulta del dashboard.
    def build(self, day: str | None = None) -> tuple[str, tuple]:
        """Devuelve SQL parametrizado y sus parametros."""
        # Define el contrato para devolver SQL y parámetros.


class TotalDashboardStrategy(DashboardQueryStrategy):
    # Genera el resumen general sin filtrar por fecha.
    def build(self, day: str | None = None) -> tuple[str, tuple]:
        # Cuenta los servicios de cada estado sin filtro diario.
        return ("""
            SELECT e.nombre AS estado, COUNT(s.id_servicio) AS cantidad
            FROM estados e
            LEFT JOIN servicios s ON s.estado=e.nombre
            WHERE e.activo=1
            GROUP BY e.nombre ORDER BY e.id_estado
        """, ())


class DailyDashboardStrategy(DashboardQueryStrategy):
    # Genera el resumen de servicios para una fecha concreta.
    def build(self, day: str | None = None) -> tuple[str, tuple]:
        # Valida la fecha y filtra servicios mediante un parámetro SQL.
        if not day:
            raise ValueError("Selecciona una fecha para consultar servicios por dia.")
        try:
            # Valida el formato de la fecha antes de construir la consulta.
            date.fromisoformat(day)
        except ValueError as error:
            raise ValueError("La fecha debe tener el formato AAAA-MM-DD.") from error
        return ("""
            SELECT e.nombre AS estado, COUNT(s.id_servicio) AS cantidad
            FROM estados e
            LEFT JOIN servicios s
              ON s.estado=e.nombre AND DATE(s.fecha_ingreso)=%s
            WHERE e.activo=1
            GROUP BY e.nombre ORDER BY e.id_estado
        """, (day,))
