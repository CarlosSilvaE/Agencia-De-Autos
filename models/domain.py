"""Objetos de dominio para el comprobante de un servicio."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ReceiptPart:
    # Representa una refacción incluida en el comprobante.
    name: str
    quantity: int
    unit_price: Decimal

    @classmethod
    def from_record(cls, row: dict[str, Any]) -> "ReceiptPart":
        # Convierte un registro SQL en una refacción del comprobante.
        return cls(
            str(row["nombre"]), int(row["cantidad"]),
            Decimal(str(row["precio_unitario"])),
        )

    def describe(self) -> str:
        # Formatea cantidad y precio de una refacción.
        return f"  - {self.name} (x{self.quantity}): ${self.unit_price:,.2f} c/u"


@dataclass(frozen=True)
class ServiceReceipt:
    # Reúne los datos y el texto del comprobante.
    folio: str
    intake_date: str
    owner: str
    owner_phone: str
    vehicle: str
    plates: str
    kind: str
    status: str
    description: str
    cost: Decimal
    deliverer: str
    delivery_phone: str
    relationship: str
    observations: str
    next_date: str
    mileage: str
    parts: tuple[ReceiptPart, ...]
    receiver: str = "No registrado"
    pickup: str = "Propietario"

    @classmethod
    def from_records(
        cls, service: dict[str, Any], parts: list[dict[str, Any]]
    ) -> "ServiceReceipt":
        # Agrupa los datos del servicio y sus refacciones.
        def value(name: str, default: str = "No registrado") -> str:
            # Usa un texto predeterminado cuando falta un dato.
            raw = service.get(name)
            return str(raw) if raw is not None and raw != "" else default

        owner = " ".join(
            str(service.get(part) or "") for part in
            ("nombre", "apellido_paterno", "apellido_materno")
        ).strip()
        return cls(
            folio=value("folio"), intake_date=value("fecha_ingreso"),
            receiver=value("recibido_por"), pickup=value("tercero_recoge", "Propietario"),
            owner=owner, owner_phone=value("telefono"),
            vehicle=" ".join(value(k, "") for k in ("anio", "marca", "modelo")).strip(),
            plates=value("placas"), kind=value("tipo_servicio"),
            status=value("estado"), description=value("descripcion"),
            cost=Decimal(str(service.get("costo") or 0)),
            deliverer=value("nombre_entrega"), delivery_phone=value("telefono_entrega"),
            relationship=value("relacion_propietario"),
            observations=value("observaciones_entrega", "Ninguna"),
            next_date=value("proximo_servicio", "No programado"),
            mileage=value("kilometraje"),
            parts=tuple(ReceiptPart.from_record(row) for row in parts),
        )

    def as_text(self) -> str:
        # Genera el texto listo para visualizar o imprimir.
        lines = [
            "AGENCIA DE AUTOMOVILES - COMPROBANTE DE SERVICIO",
            "=" * 52,
            f"Folio: {self.folio}",
            f"Fecha de ingreso: {self.intake_date}",
            f"Propietario: {self.owner}",
            f"Telefono del propietario: {self.owner_phone}",
            f"Vehiculo: {self.vehicle}",
            f"Placas: {self.plates}",
            f"Servicio: {self.kind} / {self.status}",
            f"Descripcion: {self.description}",
            f"Costo: ${self.cost:,.2f}",
            "Refacciones utilizadas:",
            *([part.describe() for part in self.parts] or ["  - Ninguna"]),
            f"Recibido en la agencia por: {self.receiver}",
            f"Persona autorizada a recoger: {self.pickup}",
            f"Persona que entrego: {self.deliverer}",
            f"Telefono de entrega: {self.delivery_phone}",
            f"Relacion con propietario: {self.relationship}",
            f"Observaciones: {self.observations}",
            f"Proximo servicio: {self.next_date}",
            f"Kilometraje programado: {self.mileage}",
        ]
        return "\n".join(lines)
