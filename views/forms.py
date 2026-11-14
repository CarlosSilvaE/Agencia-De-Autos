from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
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
    QListView,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .theme import set_primary_button

PREVENTIVE_TEMPLATES = (
    ("Revision general", "Mantenimiento preventivo: revision general del vehiculo, niveles de fluidos, filtros, frenos y puntos de seguridad."),
    ("Aceite y filtro", "Mantenimiento preventivo: cambio de aceite y filtro de aceite, revision de niveles y verificacion de fugas."),
    ("Frenos", "Mantenimiento preventivo: revision de pastillas, discos, liquido de frenos y funcionamiento del sistema de frenado."),
    ("Por kilometraje", "Mantenimiento preventivo por kilometraje: revision de filtros, fluidos, bandas y puntos de mantenimiento indicados para el vehiculo."),
    ("Enfriamiento", "Mantenimiento preventivo: revision de refrigerante, mangueras, radiador y posibles fugas del sistema de enfriamiento."),
)


def set_combo_id(combo: QComboBox, value: Any) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)


def optional_text(value: str) -> str | None:
    return value.strip() or None


def add_buttons(
    dialog: QDialog, layout: QVBoxLayout, on_save: Callable[[], None] | None = None,
) -> None:
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
    set_primary_button(buttons.button(QDialogButtonBox.StandardButton.Save))
    buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
    buttons.accepted.connect(on_save if on_save is not None else dialog.accept)
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
            ("telefono", "Telefono"),
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
        self.setWindowTitle("Editar vehiculo" if record else "Nuevo vehiculo")
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
        for item in catalogs["anios"]:
            self.year.addItem(str(item["anio"]), item["id_anio"])
        self.plates = QLineEdit(str((record or {}).get("placas") or ""))
        self.color = QLineEdit(str((record or {}).get("color") or ""))
        self.vin = QLineEdit(str((record or {}).get("vin") or ""))
        form.addRow("Cliente:", self.customer)
        form.addRow("Marca:", self.brand)
        form.addRow("Modelo:", self.model)
        form.addRow("Anio:", self.year)
        form.addRow("Placas:", self.plates)
        form.addRow("Color:", self.color)
        self.vin.setPlaceholderText("Vacio: generar automaticamente")
        form.addRow("VIN (opcional):", self.vin)
        layout.addLayout(form)
        add_buttons(self, layout)
        if record:
            set_combo_id(self.customer, record.get("id_cliente"))
            set_combo_id(self.brand, record.get("id_marca"))
            self.filter_models()
            set_combo_id(self.model, record.get("id_modelo"))
            set_combo_id(self.year, record.get("id_anio"))
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
        elif catalog == "anios":
            year = QSpinBox()
            year.setRange(1886, date.today().year + 5)
            year.setValue(int((record or {}).get("anio") or date.today().year))
            self.fields["anio"] = year
            form.addRow("Anio:", year)
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
    def __init__(
        self, record: dict[str, Any] | None = None, parent: QWidget | None = None,
        *, on_save: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("Editar administrador" if record else "Nuevo administrador")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(str((record or {}).get("nombre") or ""))
        self.username = QLineEdit(str((record or {}).get("usuario") or ""))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText(
            "Dejar vacio para conservar" if record else "Minimo 8 caracteres"
        )
        form.addRow("Nombre:", self.name)
        form.addRow("Usuario:", self.username)
        form.addRow("Contrasena:", self.password)
        layout.addLayout(form)
        self.active = QCheckBox("Activo")
        self.active.setChecked(bool((record or {}).get("activo", True)))
        layout.addWidget(self.active)
        add_buttons(self, layout, on_save)

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
        *, on_save: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.record = record
        self.vehicles = vehicles
        self.parts = parts
        self.setWindowTitle("Editar servicio" if record else "Nuevo servicio")
        self.resize(960, 700)
        self.setMinimumSize(760, 560)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        service_page = QWidget()
        service_layout = QVBoxLayout(service_page)
        service_scroll = QScrollArea()
        service_scroll.setWidgetResizable(True)
        service_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        service_scroll.setWidget(service_page)
        parts_page = QWidget()
        parts_layout = QVBoxLayout(parts_page)
        delivery_page = QWidget()
        delivery_layout = QVBoxLayout(delivery_page)
        self.tabs.addTab(service_scroll, "Servicio")
        self.tabs.addTab(parts_page, "Refacciones")
        self.tabs.addTab(delivery_page, "Recepcion (opcional)")
        form = QFormLayout()
        self.vehicle = QComboBox()
        self.vehicle.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.vehicle.setMaxVisibleItems(12)
        vehicle_list = QListView(self.vehicle)
        self.vehicle.setView(vehicle_list)
        vehicle_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        vehicle_list.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
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
        self.labor = QDoubleSpinBox()
        self.labor.setRange(0, 9_999_999_999.99)
        self.labor.setDecimals(2)
        self.labor.setPrefix("$ ")
        if record and record.get("mano_obra") is not None:
            labor = Decimal(str(record["mano_obra"]))
        elif record:
            subtotal = sum(
                (Decimal(str(part["precio_unitario"])) * int(part["cantidad"])
                 for part in (existing_parts or [])), Decimal("0"),
            )
            labor = max(Decimal("0"), Decimal(str(record.get("costo") or 0)) - subtotal)
        else:
            labor = Decimal("1500.00")
        self.labor.setValue(float(labor))
        self.parts_subtotal = QLabel("$ 0.00")
        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 9_999_999_999.99)
        self.cost.setDecimals(2)
        self.cost.setPrefix("$ ")
        self.cost.setReadOnly(True)
        self.cost.setToolTip("Total automatico: mano de obra mas las refacciones seleccionadas.")
        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        self.preventive_label = QLabel("Mensaje preventivo:")
        self.preventive_message = QComboBox()
        self.preventive_message.addItem("Descripcion personalizada", None)
        for title, message in PREVENTIVE_TEMPLATES:
            self.preventive_message.addItem(title, message)
        self.folio = QLineEdit(str((record or {}).get("folio") or ""))
        if record:
            self.folio.setReadOnly(True)
        form.addRow("Vehiculo:", self.vehicle)
        if not record:
            form.addRow("Folio (opcional):", self.folio)
        form.addRow("Tipo:", self.kind)
        form.addRow("Estado:", self.status)
        form.addRow("Mano de obra:", self.labor)
        form.addRow("Subtotal refacciones:", self.parts_subtotal)
        form.addRow("Total del servicio:", self.cost)
        form.addRow(self.preventive_label, self.preventive_message)
        form.addRow("Descripcion:", self.description)
        service_layout.addLayout(form)

        delivery = QFormLayout()
        self.deliverer = QLineEdit(str((record or {}).get("nombre_entrega") or ""))
        self.deliverer.setPlaceholderText("Nombre de quien trae el vehiculo a la agencia")
        self.delivery_phone = QLineEdit(str((record or {}).get("telefono_entrega") or ""))
        self.relationship = QLineEdit(str((record or {}).get("relacion_propietario") or ""))
        self.relationship.setPlaceholderText("Propietario, familiar, empleado...")
        self.delivery_notes = QTextEdit(str((record or {}).get("observaciones_entrega") or ""))
        self.delivery_notes.setMaximumHeight(110)
        delivery.addRow("Persona que entrega el vehiculo:", self.deliverer)
        delivery.addRow("Telefono:", self.delivery_phone)
        delivery.addRow("Relacion:", self.relationship)
        delivery.addRow("Observaciones:", self.delivery_notes)
        delivery_help = QLabel(
            "Si lo deseas, registra a la persona que trae y entrega el vehiculo en la agencia. "
            "Puede ser el propietario o un tercero. Todos estos datos son opcionales."
        )
        delivery_help.setWordWrap(True)
        delivery_layout.addWidget(delivery_help)
        delivery_layout.addLayout(delivery)
        delivery_layout.addStretch()

        parts_help = QLabel("Marca Usar en las refacciones necesarias y ajusta la cantidad y el precio unitario.")
        parts_help.setWordWrap(True)
        parts_layout.addWidget(parts_help)
        self.parts_table = QTableWidget(len(self.parts), 4)
        self.parts_table.setHorizontalHeaderLabels(["Usar", "Refaccion", "Cantidad", "Precio unitario"])
        header = self.parts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.parts_table.setColumnWidth(0, 65)
        self.parts_table.setColumnWidth(2, 120)
        self.parts_table.setColumnWidth(3, 165)
        self.parts_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.parts_table.setAlternatingRowColors(True)
        self.parts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.parts_table.setWordWrap(False)
        self.parts_table.verticalHeader().setVisible(False)
        part_by_id = {part["id_refaccion"]: part for part in (existing_parts or [])}
        for index, part in enumerate(self.parts):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            selected = part.get("id_refaccion") in part_by_id
            check.setCheckState(Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked)
            self.parts_table.setItem(index, 0, check)
            name = QTableWidgetItem(str(part["nombre"]))
            name.setToolTip(str(part["nombre"]))
            self.parts_table.setItem(index, 1, name)
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
            quantity.valueChanged.connect(self.update_total)
            price.valueChanged.connect(self.update_total)
        row_height = 42
        if self.parts:
            row_height = max(row_height, self.parts_table.cellWidget(0, 2).sizeHint().height() + 6)
        self.parts_table.verticalHeader().setDefaultSectionSize(row_height)
        parts_layout.addWidget(self.parts_table, 1)
        self.parts_table.itemChanged.connect(self.update_total)
        self.labor.valueChanged.connect(self.update_total)

        next_service = QFormLayout()
        self.next_enabled = QCheckBox("Programar proximo servicio")
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
        service_layout.addWidget(QLabel("<b>Proximo servicio</b>"))
        service_layout.addLayout(next_service)
        service_layout.addStretch()
        self.next_enabled.toggled.connect(self.toggle_next_service)
        self.toggle_next_service(self.next_enabled.isChecked())

        if record:
            set_combo_id(self.vehicle, record.get("id_vehiculo"))
            self.kind.setCurrentText(str(record.get("tipo_servicio") or "Correctivo"))
            self.status.setCurrentText(str(record.get("estado") or "En espera"))
            self.description.setPlainText(str(record.get("descripcion") or ""))
        else:
            self.description.setPlainText(PREVENTIVE_TEMPLATES[0][1])
        self._description_kind = self.kind.currentText()
        self._description_drafts = {
            "Preventivo": PREVENTIVE_TEMPLATES[0][1], "Correctivo": "",
        }
        self._description_drafts[self._description_kind] = self.description.toPlainText()
        self.kind.currentTextChanged.connect(self.change_service_kind)
        self.preventive_message.currentIndexChanged.connect(self.apply_preventive_message)
        self.description.textChanged.connect(self.update_preventive_controls)
        self.update_preventive_controls()
        self.update_total()
        add_buttons(self, layout, on_save)

    def update_preventive_controls(self) -> None:
        preventive = self.kind.currentText() == "Preventivo"
        self.preventive_label.setVisible(preventive)
        self.preventive_message.setVisible(preventive)
        self.description.setPlaceholderText(
            "Selecciona un mensaje o escribe la descripcion del servicio."
            if preventive else "Describe manualmente la falla y el trabajo correctivo."
        )
        index = self.preventive_message.findData(self.description.toPlainText())
        self.preventive_message.blockSignals(True)
        self.preventive_message.setCurrentIndex(max(0, index))
        self.preventive_message.blockSignals(False)

    def change_service_kind(self, kind: str) -> None:
        self._description_drafts[self._description_kind] = self.description.toPlainText()
        self._description_kind = kind
        self.description.setPlainText(self._description_drafts[kind])
        self.update_preventive_controls()

    def apply_preventive_message(self) -> None:
        message = self.preventive_message.currentData()
        if self.kind.currentText() == "Preventivo" and message is not None:
            self.description.setPlainText(message)

    def update_total(self) -> None:
        subtotal = Decimal("0")
        for index in range(self.parts_table.rowCount()):
            if self.parts_table.item(index, 0).checkState() == Qt.CheckState.Checked:
                quantity = self.parts_table.cellWidget(index, 2).value()
                price = Decimal(str(self.parts_table.cellWidget(index, 3).value()))
                subtotal += quantity * price
        self.parts_subtotal.setText(f"$ {subtotal:,.2f}")
        self.cost.setValue(float(Decimal(str(self.labor.value())) + subtotal))

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
            raise ValueError("Selecciona un vehiculo.")
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
            "manoObra": self.labor.value(),
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
                "idAno": vehicle["id_anio"],
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
