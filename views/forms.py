from __future__ import annotations

from datetime import date
from typing import Any

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .theme import set_primary_button


def set_combo_id(combo: QComboBox, value: Any) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)


def optional_text(value: str) -> str | None:
    return value.strip() or None


def add_buttons(dialog: QDialog, layout: QVBoxLayout) -> None:
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
    set_primary_button(buttons.button(QDialogButtonBox.StandardButton.Save))
    buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)


class CustomerDialog(QDialog):
    def __init__(self, record: dict[str, Any] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("Editar cliente" if record else "Nuevo cliente")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.fields: dict[str, QLineEdit] = {}
        for key, label in (
            ("nombre", "Nombre"),
            ("apellido_paterno", "Apellido paterno"),
            ("apellido_materno", "Apellido materno"),
            ("telefono", "Teléfono"),
            ("email", "Email"),
        ):
            field = QLineEdit(str((record or {}).get(key) or ""))
            self.fields[key] = field
            form.addRow(label, field)
        layout.addLayout(form)
        add_buttons(self, layout)

    def payload(self) -> dict[str, str | None]:
        return {
            "nombre": self.fields["nombre"].text().strip(),
            "apellidoPaterno": self.fields["apellido_paterno"].text().strip(),
            "apellidoMaterno": optional_text(self.fields["apellido_materno"].text()),
            "telefono": optional_text(self.fields["telefono"].text()),
            "email": optional_text(self.fields["email"].text()),
        }


class VehicleDialog(QDialog):
    def __init__(
        self,
        customers: list[dict[str, Any]],
        catalogs: dict[str, list[dict[str, Any]]],
        record: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Editar vehículo" if record else "Nuevo vehículo")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.customer = QComboBox()
        for item in customers:
            display = " ".join(
                str(item.get(key) or "")
                for key in ("nombre", "apellido_paterno", "apellido_materno")
            ).strip()
            self.customer.addItem(display, item["id_cliente"])
        self.brand = QComboBox()
        for item in catalogs["marcas"]:
            self.brand.addItem(item["nombre"], item["id_marca"])
        self.model = QComboBox()
        self.all_models = catalogs["modelos"]
        self.brand.currentIndexChanged.connect(self.filter_models)
        self.year = QComboBox()
        for item in catalogs["anos"]:
            self.year.addItem(str(item["ano"]), item["id_ano"])
        self.plates = QLineEdit(str((record or {}).get("placas") or ""))
        self.color = QLineEdit(str((record or {}).get("color") or ""))
        self.vin = QLineEdit(str((record or {}).get("vin") or ""))
        form.addRow("Cliente:", self.customer)
        form.addRow("Marca:", self.brand)
        form.addRow("Modelo:", self.model)
        form.addRow("Año:", self.year)
        form.addRow("Placas:", self.plates)
        form.addRow("Color:", self.color)
        self.vin.setPlaceholderText("Vacío: generar automáticamente")
        form.addRow("VIN (opcional):", self.vin)
        layout.addLayout(form)
        add_buttons(self, layout)
        if record:
            set_combo_id(self.customer, record.get("id_cliente"))
            set_combo_id(self.brand, record.get("id_marca"))
            self.filter_models()
            set_combo_id(self.model, record.get("id_modelo"))
            set_combo_id(self.year, record.get("id_ano"))
        else:
            self.filter_models()

    def filter_models(self) -> None:
        brand_id = self.brand.currentData()
        selected = self.model.currentData()
        self.model.clear()
        for model in self.all_models:
            if model.get("id_marca") == brand_id:
                self.model.addItem(model["nombre"], model["id_modelo"])
        set_combo_id(self.model, selected)

    def payload(self) -> dict[str, Any]:
        return {
            "idCliente": self.customer.currentData(),
            "idMarca": self.brand.currentData(),
            "idModelo": self.model.currentData(),
            "idAno": self.year.currentData(),
            "placas": self.plates.text().strip(),
            "color": optional_text(self.color.text()),
            "vin": optional_text(self.vin.text()),
        }


class CatalogItemDialog(QDialog):
    def __init__(
        self,
        catalog: str,
        brands: list[dict[str, Any]],
        record: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.catalog = catalog
        self.setWindowTitle("Editar registro" if record else "Nuevo registro")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.fields: dict[str, Any] = {}
        if catalog == "modelos":
            field = QComboBox()
            for brand in brands:
                field.addItem(brand["nombre"], brand["id_marca"])
            set_combo_id(field, (record or {}).get("id_marca"))
            self.fields["id_marca"] = field
            form.addRow("Marca:", field)
            self._add_text(form, "nombre", "Nombre", record)
        elif catalog == "refacciones":
            self._add_text(form, "nombre", "Nombre", record)
            self._add_text(form, "sku", "SKU", record)
            quantity = QSpinBox()
            quantity.setRange(0, 2_000_000_000)
            quantity.setValue(int((record or {}).get("cantidad") or 0))
            self.fields["cantidad"] = quantity
            form.addRow("Existencia:", quantity)
            price = QDoubleSpinBox()
            price.setRange(0, 99_999_999)
            price.setDecimals(2)
            price.setValue(float((record or {}).get("precio") or 0))
            self.fields["precio"] = price
            form.addRow("Precio:", price)
        elif catalog == "anos":
            year = QSpinBox()
            year.setRange(1886, date.today().year + 5)
            year.setValue(int((record or {}).get("ano") or date.today().year))
            self.fields["ano"] = year
            form.addRow("Año:", year)
        else:
            self._add_text(form, "nombre", "Nombre", record)
        layout.addLayout(form)
        add_buttons(self, layout)

    def _add_text(
        self,
        form: QFormLayout,
        key: str,
        label: str,
        record: dict[str, Any] | None,
    ) -> None:
        field = QLineEdit(str((record or {}).get(key) or ""))
        self.fields[key] = field
        form.addRow(f"{label}:", field)

    def payload(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, field in self.fields.items():
            if isinstance(field, QComboBox):
                result[key] = field.currentData()
            elif isinstance(field, (QSpinBox, QDoubleSpinBox)):
                result[key] = field.value()
            else:
                text = field.text().strip()
                if key == "sku":
                    result[key] = text or None
                elif key == "nombre":
                    result[key] = text
                else:
                    result[key] = text
        return result


class AdminDialog(QDialog):
    def __init__(self, record: dict[str, Any] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("Editar administrador" if record else "Nuevo administrador")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(str((record or {}).get("nombre") or ""))
        self.username = QLineEdit(str((record or {}).get("usuario") or ""))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Dejar vacío para conservar")
        form.addRow("Nombre:", self.name)
        form.addRow("Usuario:", self.username)
        form.addRow("Contraseña:", self.password)
        layout.addLayout(form)
        self.active = QCheckBox("Activo")
        self.active.setChecked(bool((record or {}).get("activo", True)))
        layout.addWidget(self.active)
        add_buttons(self, layout)

    def payload(self) -> dict[str, Any]:
        return {
            "nombre": self.name.text().strip(),
            "usuario": self.username.text().strip(),
            "password": optional_text(self.password.text()),
            "activo": self.active.isChecked(),
        }


class ServiceDialog(QDialog):
    def __init__(
        self,
        vehicles: list[dict[str, Any]],
        parts: list[dict[str, Any]],
        record: dict[str, Any] | None = None,
        existing_parts: list[dict[str, Any]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.record = record
        self.vehicles = vehicles
        self.parts = parts
        self.setWindowTitle("Editar servicio" if record else "Nuevo servicio")
        self.resize(760, 760)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.vehicle = QComboBox()
        for item in self.vehicles:
            owner = " ".join(
                str(item.get(key) or "")
                for key in ("nombre", "apellido_paterno", "apellido_materno")
            ).strip()
            display = f"{item.get('placas', '')} — {item.get('marca', '')} {item.get('modelo', '')} — {owner}"
            self.vehicle.addItem(display, item["id_vehiculo"])
        self.kind = QComboBox()
        self.kind.addItems(["Preventivo", "Correctivo"])
        self.status = QComboBox()
        self.status.addItems(["En espera", "En proceso", "Finalizado"])
        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 99_999_999)
        self.cost.setDecimals(2)
        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        self.folio = QLineEdit(str((record or {}).get("folio") or ""))
        if record:
            self.folio.setReadOnly(True)
        form.addRow("Vehículo:", self.vehicle)
        if not record:
            form.addRow("Folio (opcional):", self.folio)
        form.addRow("Tipo:", self.kind)
        form.addRow("Estado:", self.status)
        form.addRow("Costo:", self.cost)
        form.addRow("Descripción:", self.description)
        layout.addLayout(form)

        delivery = QFormLayout()
        self.deliverer = QLineEdit(str((record or {}).get("nombre_entrega") or ""))
        self.delivery_phone = QLineEdit(str((record or {}).get("telefono_entrega") or ""))
        self.relationship = QLineEdit(str((record or {}).get("relacion_propietario") or ""))
        self.delivery_notes = QTextEdit(str((record or {}).get("observaciones_entrega") or ""))
        self.delivery_notes.setMaximumHeight(55)
        delivery.addRow("Persona que entrega:", self.deliverer)
        delivery.addRow("Teléfono:", self.delivery_phone)
        delivery.addRow("Relación:", self.relationship)
        delivery.addRow("Observaciones:", self.delivery_notes)
        layout.addWidget(QLabel("<b>Recepción</b>"))
        layout.addLayout(delivery)

        layout.addWidget(QLabel("<b>Refacciones</b>"))
        self.parts_table = QTableWidget(len(self.parts), 4)
        self.parts_table.setHorizontalHeaderLabels(["Usar", "Refacción", "Cantidad", "Precio unitario"])
        self.parts_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        part_by_id = {part["id_refaccion"]: part for part in (existing_parts or [])}
        for index, part in enumerate(self.parts):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            selected = part.get("id_refaccion") in part_by_id
            check.setCheckState(Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked)
            self.parts_table.setItem(index, 0, check)
            self.parts_table.setItem(index, 1, QTableWidgetItem(str(part["nombre"])))
            quantity = QSpinBox()
            quantity.setRange(1, 2_000_000_000)
            quantity.setValue(int(part_by_id.get(part["id_refaccion"], {}).get("cantidad", 1)))
            self.parts_table.setCellWidget(index, 2, quantity)
            price = QDoubleSpinBox()
            price.setRange(0, 99_999_999)
            price.setDecimals(2)
            price.setValue(
                float(
                    part_by_id.get(part["id_refaccion"], {}).get(
                        "precio_unitario", part.get("precio") or 0
                    )
                )
            )
            self.parts_table.setCellWidget(index, 3, price)
        self.parts_table.setMaximumHeight(180)
        layout.addWidget(self.parts_table)

        next_service = QFormLayout()
        self.next_enabled = QCheckBox("Programar próximo servicio")
        self.next_date = QDateEdit()
        self.next_date.setCalendarPopup(True)
        self.next_date.setDate(QDate.currentDate())
        self.mileage = QSpinBox()
        self.mileage.setRange(0, 2_000_000_000)
        self.next_notes = QLineEdit()
        next_date_value = str((record or {}).get("proximo_servicio") or "")
        self.next_enabled.setChecked(bool(next_date_value))
        if next_date_value:
            parsed = QDate.fromString(next_date_value[:10], "yyyy-MM-dd")
            if parsed.isValid():
                self.next_date.setDate(parsed)
        self.mileage.setValue(int((record or {}).get("kilometraje") or 0))
        self.next_notes.setText(str((record or {}).get("notas_proximo_servicio") or ""))
        next_service.addRow(self.next_enabled)
        next_service.addRow("Fecha:", self.next_date)
        next_service.addRow("Kilometraje:", self.mileage)
        next_service.addRow("Notas:", self.next_notes)
        layout.addLayout(next_service)
        self.next_enabled.toggled.connect(self.toggle_next_service)
        self.toggle_next_service(self.next_enabled.isChecked())

        if record:
            set_combo_id(self.vehicle, record.get("id_vehiculo"))
            self.kind.setCurrentText(str(record.get("tipo_servicio") or "Correctivo"))
            self.status.setCurrentText(str(record.get("estado") or "En espera"))
            self.cost.setValue(float(record.get("costo") or 0))
            self.description.setPlainText(str(record.get("descripcion") or ""))
        add_buttons(self, layout)

    def toggle_next_service(self, enabled: bool) -> None:
        for widget in (self.next_date, self.mileage, self.next_notes):
            widget.setEnabled(enabled)

    def payload(self) -> dict[str, Any]:
        vehicle_id = self.vehicle.currentData()
        vehicle = next(
            (item for item in self.vehicles if item["id_vehiculo"] == vehicle_id),
            None,
        )
        if vehicle is None:
            raise ValueError("Selecciona un vehículo.")
        parts = []
        for index, part in enumerate(self.parts):
            if self.parts_table.item(index, 0).checkState() == Qt.CheckState.Checked:
                parts.append(
                    {
                        "idRefaccion": part["id_refaccion"],
                        "cantidad": self.parts_table.cellWidget(index, 2).value(),
                        "precioUnitario": self.parts_table.cellWidget(index, 3).value(),
                    }
                )
        next_service = None
        if self.next_enabled.isChecked():
            next_service = {
                "fechaProgramada": self.next_date.date().toString("yyyy-MM-dd"),
                "kilometraje": self.mileage.value() or None,
                "notas": optional_text(self.next_notes.text()),
            }
        return {
            "folio": self.folio.text().strip() or None,
            "tipoServicio": self.kind.currentText(),
            "descripcion": self.description.toPlainText().strip(),
            "estado": self.status.currentText(),
            "costo": self.cost.value(),
            "cliente": {
                "id": vehicle["id_cliente"],
                "nombre": vehicle["nombre"],
                "apellidoPaterno": vehicle["apellido_paterno"],
                "apellidoMaterno": vehicle.get("apellido_materno"),
                "telefono": vehicle.get("telefono"),
                "email": vehicle.get("email"),
            },
            "vehiculo": {
                "id": vehicle["id_vehiculo"],
                "idMarca": vehicle["id_marca"],
                "idModelo": vehicle["id_modelo"],
                "idAno": vehicle["id_ano"],
                "placas": vehicle["placas"],
                "color": vehicle.get("color"),
                "vin": vehicle.get("vin"),
            },
            "entrega": {
                "nombre": self.deliverer.text().strip(),
                "telefono": optional_text(self.delivery_phone.text()),
                "relacionPropietario": optional_text(self.relationship.text()),
                "observaciones": optional_text(self.delivery_notes.toPlainText()),
            },
            "refacciones": parts,
            "proximoServicio": next_service,
        }
