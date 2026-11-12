from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models import AgencyModel


class AuthController:
    # Gestiona el inicio y cierre de sesión del administrador.
    def __init__(self, model: AgencyModel) -> None:
        self.model = model
        self.current_user: str | None = None

    def login(self, username: str, password: str) -> str:
        # Valida las credenciales y guarda el usuario de la sesión.
        self.current_user = self.model.authenticate(username, password)
        return self.current_user

    def logout(self) -> None:
        """Descarta la identidad autenticada al salir de la aplicacion."""
        # Limpia la identidad del administrador que cerró sesión.
        self.current_user = None


class DashboardController:
    # Comunica el dashboard con las consultas del modelo.
    def __init__(self, model: AgencyModel) -> None:
        self.model = model

    def summary(self, filter_name: str, day: str | None = None) -> list[dict[str, Any]]:
        # Solicita al modelo el resumen filtrado de servicios.
        return self.model.dashboard(filter_name, day)


class ServiceController:
    # Coordina consultas y operaciones de servicios.
    def __init__(self, model: AgencyModel) -> None:
        self.model = model

    def list(self, folio: str = "", owner: str = "") -> list[dict[str, Any]]:
        # Consulta servicios por folio o propietario.
        return self.model.list_services(folio, owner)

    def options(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        # Obtiene vehículos y refacciones disponibles para el formulario.
        return self.model.service_options()

    def receipt(self, folio: str) -> str:
        # Solicita el comprobante y lo convierte a texto.
        return self.model.service_receipt(folio).as_text()

    def delivery_history(self, folio: str) -> list[dict[str, Any]]:
        # Consulta quién entregó el vehículo en cada registro.
        return self.model.delivery_history(folio)

    def parts(self, folio: str) -> list[dict[str, Any]]:
        # Consulta las refacciones usadas en un servicio.
        return self.model.service_parts(folio)

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Envía los datos al modelo para registrar el servicio.
        return self.model.create_service(payload)

    def update(self, folio: str, payload: dict[str, Any]) -> None:
        # Envía los cambios de un servicio existente.
        self.model.update_service(folio, payload)

    def change_status(self, folio: str, status: str) -> None:
        # Actualiza el estado del servicio indicado.
        self.model.update_service_status(folio, status)

    def delete(self, folio: str) -> None:
        # Solicita eliminar el servicio y sus relaciones.
        self.model.delete_service(folio)


class UpcomingController:
    # Permite consultar próximos mantenimientos.
    def __init__(self, model: AgencyModel) -> None:
        self.model = model

    def list(self, folio: str = "", owner: str = "") -> list[dict[str, Any]]:
        # Filtra próximos servicios por folio o propietario.
        return self.model.list_upcoming(folio, owner)


class CustomerVehicleController:
    # Coordina el CRUD de clientes y vehículos.
    def __init__(self, model: AgencyModel) -> None:
        self.model = model

    def data(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
        # Obtiene clientes, vehículos y catálogos relacionados.
        return self.model.customer_vehicle_data()

    def save_customer(
        self, payload: dict[str, Any], customer_id: int | None = None
    ) -> None:
        # Crea o actualiza un cliente.
        self.model.save_customer(payload, customer_id)

    def delete_customer(self, customer_id: int) -> None:
        # Solicita desactivar un cliente.
        self.model.delete_customer(customer_id)

    def save_vehicle(self, payload: dict[str, Any], vehicle_id: int | None = None) -> None:
        # Crea o actualiza un vehículo.
        self.model.save_vehicle(payload, vehicle_id)

    def delete_vehicle(self, vehicle_id: int) -> None:
        # Solicita desactivar un vehículo.
        self.model.delete_vehicle(vehicle_id)


class CatalogController:
    # Controla los catálogos de marcas, modelos, años y refacciones.
    def __init__(self, model: AgencyModel) -> None:
        self.model = model

    def list(self, catalog: str) -> list[dict[str, Any]]:
        # Consulta los registros activos de un catálogo.
        return self.model.list_catalog(catalog)

    def brands(self) -> list[dict[str, Any]]:
        # Obtiene las marcas disponibles.
        return self.model.list_catalog("marcas")

    def save(
        self,
        catalog: str,
        payload: dict[str, Any],
        item_id: int | None = None,
    ) -> None:
        # Registra o modifica un elemento de catálogo.
        self.model.save_catalog_item(catalog, payload, item_id)

    def delete(self, catalog: str, item_id: int) -> None:
        # Solicita desactivar un elemento de catálogo.
        self.model.delete_catalog_item(catalog, item_id)


class AdminController:
    # Gestiona las cuentas de administradores.
    def __init__(self, model: AgencyModel) -> None:
        self.model = model

    def list(self) -> list[dict[str, Any]]:
        # Consulta los administradores registrados.
        return self.model.list_admins()

    def save(self, payload: dict[str, Any], admin_id: int | None = None) -> None:
        # Registra o modifica un administrador.
        self.model.save_admin(payload, admin_id)

    def delete(self, admin_id: int) -> None:
        # Solicita desactivar un administrador.
        self.model.delete_admin(admin_id)


@dataclass(frozen=True)
class AgencyControllers:
    # Agrupa los controladores que comparten el mismo modelo.
    auth: AuthController
    dashboard: DashboardController
    services: ServiceController
    upcoming: UpcomingController
    customers_vehicles: CustomerVehicleController
    catalogs: CatalogController
    admins: AdminController

    @classmethod
    def from_model(cls, model: AgencyModel) -> AgencyControllers:
        # Crea todos los controladores a partir del mismo modelo.
        return cls(
            auth=AuthController(model),
            dashboard=DashboardController(model),
            services=ServiceController(model),
            upcoming=UpcomingController(model),
            customers_vehicles=CustomerVehicleController(model),
            catalogs=CatalogController(model),
            admins=AdminController(model),
        )
