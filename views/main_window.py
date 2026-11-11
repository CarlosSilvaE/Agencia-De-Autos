from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtPrintSupport import QPrintDialog, QPrinter

from controllers import (
    AdminController,
    AgencyControllers,
    AuthController,
    CatalogController,
    CustomerVehicleController,
    DashboardController,
    ServiceController,
    UpcomingController,
)
from models.database import DataAccessError
from .theme import set_primary_button
from .status_chart import StatusBarChart
from .forms import (
    AdminDialog,
    CatalogItemDialog,
    CustomerDialog,
    ServiceDialog,
    VehicleDialog,
)


def table_for(parent: QWidget, headers: list[str]) -> QTableWidget:
    table = QTableWidget(parent)
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.verticalHeader().setVisible(False)
    return table


def fill_table(table: QTableWidget, rows: list[dict[str, Any]], columns: list[str]) -> None:
    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        for column_index, key in enumerate(columns):
            value = row.get(key)
            if isinstance(value, bool):
                text = "Si" if value else "No"
            else:
                text = "" if value is None else str(value)
            item = QTableWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, row)
            table.setItem(row_index, column_index, item)


def selected_record(table: QTableWidget) -> dict[str, Any] | None:
    row = table.currentRow()
    if row < 0 or table.item(row, 0) is None:
        return None
    return table.item(row, 0).data(Qt.ItemDataRole.UserRole)


def show_error(parent: QWidget, error: Exception) -> None:
    QMessageBox.critical(parent, "Error", str(error))


def ask_delete(parent: QWidget, description: str) -> bool:
    return (
        QMessageBox.question(
            parent,
            "Confirmar",
            f"¿Deseas desactivar o eliminar {description}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        == QMessageBox.StandardButton.Yes
    )


class LoginDialog(QDialog):
    def __init__(self, controller: AuthController) -> None:
        super().__init__()
        self.controller = controller
        self.username = ""
        self.setWindowTitle("Iniciar sesion")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        title = QLabel("Agencia de Automoviles")
        title.setObjectName("loginTitle")
        layout.addWidget(title)
        form = QFormLayout()
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Usuario")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Contrasena")
        form.addRow("Usuario:", self.user_input)
        form.addRow("Contrasena:", self.password_input)
        layout.addLayout(form)
        self.message = QLabel()
        self.message.setStyleSheet("color: #b42318")
        layout.addWidget(self.message)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Entrar")
        set_primary_button(buttons.button(QDialogButtonBox.StandardButton.Ok))
        buttons.accepted.connect(self.login)
        layout.addWidget(buttons)
        self.password_input.returnPressed.connect(self.login)

    def login(self) -> None:
        username = self.user_input.text().strip()
        try:
            self.username = self.controller.login(username, self.password_input.text())
        except (DataAccessError, ValueError) as error:
            self.message.setText(str(error))
            return
        self.password_input.clear()
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, controllers: AgencyControllers, username: str) -> None:
        super().__init__()
        self.setWindowTitle("Agencia de Automoviles")
        self.resize(1280, 780)
        self._auth = controllers.auth
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(22, 18, 22, 20)
        layout.setSpacing(16)
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        header = QHBoxLayout(top_bar)
        header.setContentsMargins(18, 13, 18, 13)
        title = QLabel("Agencia de Automoviles")
        title.setObjectName("headerTitle")
        header.addWidget(title)
        header.addStretch()
        session = QLabel(f"Sesion: {username}")
        session.setObjectName("headerSession")
        self._session_label = session
        header.addWidget(session)
        logout = QPushButton("Cerrar sesion")
        logout.setObjectName("headerButton")
        logout.clicked.connect(self.logout)
        header.addWidget(logout)
        layout.addWidget(top_bar)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(DashboardPage(controllers.dashboard), "Resumen")
        tabs.addTab(ServicesPage(controllers.services), "Servicios")
        tabs.addTab(UpcomingPage(controllers.upcoming), "Proximos servicios")
        tabs.addTab(
            CustomersVehiclesPage(controllers.customers_vehicles),
            "Clientes y vehiculos",
        )
        tabs.addTab(CatalogsPage(controllers.catalogs), "Catalogos")
        tabs.addTab(AdminsPage(controllers.admins), "Administradores")
        tabs.currentChanged.connect(lambda index: self._refresh_tab(tabs, index))
        layout.addWidget(tabs, 1)
        self.setCentralWidget(central)

    @staticmethod
    def _refresh_tab(tabs: QTabWidget, index: int) -> None:
        page = tabs.widget(index)
        if page is not None and hasattr(page, "refresh"):
            page.refresh()

    def logout(self) -> None:
        self._auth.logout()
        self._session_label.clear()
        self.close()

    def closeEvent(self, event) -> None:
        self._auth.logout()
        self._session_label.clear()
        super().closeEvent(event)


class DashboardPage(QWidget):
    def __init__(self, controller: DashboardController) -> None:
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.filter = QComboBox()
        self.filter.addItem("Total", "total")
        self.filter.addItem("Por fecha", "daily")
        self.day = QDateEdit()
        self.day.setCalendarPopup(True)
        self.day.setDate(QDate.currentDate())
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        controls.addWidget(QLabel("Consulta:"))
        controls.addWidget(self.filter)
        controls.addWidget(self.day)
        controls.addWidget(refresh)
        controls.addStretch()
        layout.addLayout(controls)
        self.summary = QGridLayout()
        self.summary.setHorizontalSpacing(14)
        self.summary.setVerticalSpacing(12)
        self.total_services = QLabel("0")
        self.waiting = QLabel("0")
        self.in_progress = QLabel("0")
        self.finished = QLabel("0")
        for column, (title, label) in enumerate(
            [
                ("Servicios", self.total_services),
                ("En espera", self.waiting),
                ("En proceso", self.in_progress),
                ("Finalizados", self.finished),
            ]
        ):
            card = QWidget()
            card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 13, 16, 13)
            card_title = QLabel(title)
            card_title.setObjectName("metricTitle")
            label.setObjectName("metricValue")
            card_layout.addWidget(card_title)
            card_layout.addWidget(label)
            self.summary.addWidget(card, 0, column)
        layout.addLayout(self.summary)
        self.chart = StatusBarChart(self)
        layout.addWidget(self.chart, 1)
        self.table = table_for(self, ["Estado", "Cantidad"])
        self.table.setMaximumHeight(160)
        layout.addWidget(self.table)
        self.filter.currentIndexChanged.connect(self.refresh)
        self.day.dateChanged.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        try:
            day = None
            if self.filter.currentData() == "daily":
                day = self.day.date().toString("yyyy-MM-dd")
                self.day.setEnabled(True)
            else:
                self.day.setEnabled(False)
            rows = self.controller.summary(self.filter.currentData(), day)
            fill_table(self.table, rows, ["estado", "cantidad"])
            counts = {row["estado"]: int(row["cantidad"]) for row in rows}
            self.waiting.setText(str(counts.get("En espera", 0)))
            self.in_progress.setText(str(counts.get("En proceso", 0)))
            self.finished.setText(str(counts.get("Finalizado", 0)))
            self.total_services.setText(str(sum(counts.values())))
            self.chart.set_counts(counts)
        except (DataAccessError, KeyError, TypeError, ValueError) as error:
            show_error(self, error)


class ServicesPage(QWidget):
    def __init__(self, controller: ServiceController) -> None:
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        filters = QHBoxLayout()
        self.folio_filter = QLineEdit()
        self.folio_filter.setPlaceholderText("Folio")
        self.owner_filter = QLineEdit()
        self.owner_filter.setPlaceholderText("Propietario")
        search = QPushButton("Buscar")
        set_primary_button(search)
        search.clicked.connect(self.refresh)
        filters.addWidget(self.folio_filter)
        filters.addWidget(self.owner_filter)
        filters.addWidget(search)
        layout.addLayout(filters)
        actions = QHBoxLayout()
        for text, callback in (
            ("Nuevo", self.create_service),
            ("Editar", self.edit_service),
            ("Cambiar estado", self.change_status),
            ("Comprobante", self.receipt),
            ("Historial recepcion", self.show_delivery_history),
            ("Eliminar", self.delete_service),
            ("Actualizar", self.refresh),
        ):
            button = QPushButton(text)
            if text == "Nuevo":
                set_primary_button(button)
            button.clicked.connect(callback)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.table = table_for(
            self,
            ["Folio", "Ingreso", "Tipo", "Estado", "Costo", "Propietario", "Vehiculo"],
        )
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        try:
            self.rows = self.controller.list(
                self.folio_filter.text().strip(),
                self.owner_filter.text().strip(),
            )
            display = []
            for row in self.rows:
                display.append(
                    {
                        **row,
                        "_owner": " ".join(
                            str(row.get(key) or "")
                            for key in ("nombre", "apellido_paterno", "apellido_materno")
                        ).strip(),
                        "_vehicle": " ".join(
                            str(row.get(key) or "")
                            for key in ("anio", "marca", "modelo", "placas")
                        ).strip(),
                    }
                )
            fill_table(
                self.table,
                display,
                ["folio", "fecha_ingreso", "tipo_servicio", "estado", "costo", "_owner", "_vehicle"],
            )
        except (DataAccessError, ValueError) as error:
            show_error(self, error)

    def current(self) -> dict[str, Any] | None:
        record = selected_record(self.table)
        if record is None:
            QMessageBox.information(self, "Servicios", "Selecciona un servicio.")
        return record

    def create_service(self) -> None:
        def save() -> None:
            try:
                result = self.controller.create(dialog.payload())
            except (DataAccessError, KeyError, ValueError) as error:
                show_error(dialog, error)
                return
            QMessageBox.information(dialog, "Servicio creado", f"Folio: {result['folio']}")
            dialog.accept()

        try:
            vehicles, parts = self.controller.options()
            dialog = ServiceDialog(vehicles, parts, parent=self, on_save=save)
        except (DataAccessError, ValueError) as error:
            show_error(self, error)
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def edit_service(self) -> None:
        record = self.current()
        if record is None:
            return

        def save() -> None:
            try:
                self.controller.update(record["folio"], dialog.payload())
            except (DataAccessError, KeyError, ValueError) as error:
                show_error(dialog, error)
                return
            dialog.accept()

        try:
            vehicles, catalog_parts = self.controller.options()
            parts = self.controller.parts(record["folio"])
            dialog = ServiceDialog(vehicles, catalog_parts, record, parts, self, on_save=save)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh()
        except (DataAccessError, KeyError, ValueError) as error:
            show_error(self, error)

    def change_status(self) -> None:
        record = self.current()
        if record is None:
            return
        state, accepted = QInputDialogCompat.get_item(
            self, "Cambiar estado", "Estado:", ["En espera", "En proceso", "Finalizado"],
            str(record["estado"]),
        )
        if not accepted:
            return
        try:
            self.controller.change_status(record["folio"], state)
            self.refresh()
        except (DataAccessError, ValueError) as error:
            show_error(self, error)

    def receipt(self) -> None:
        record = self.current()
        if record is None:
            return
        try:
            ReceiptDialog(self.controller.receipt(record["folio"]), self).exec()
        except (DataAccessError, ValueError, KeyError, TypeError) as error:
            show_error(self, error)

    def show_delivery_history(self) -> None:
        record = self.current()
        if record is None:
            return
        try:
            entries = self.controller.delivery_history(record["folio"])
            text = [f"Historial de recepcion del servicio {record['folio']}", "=" * 48]
            for idx, row in enumerate(entries, start=1):
                text.extend([
                    f"Registro {idx} — {row['fecha']}",
                    f"Nombre: {row['nombre_entrega']}",
                    f"Telefono: {row.get('telefono') or 'Sin telefono'}",
                    f"Relacion: {row.get('relacion_propietario') or 'Sin especificar'}",
                    f"Observaciones: {row.get('observaciones') or 'Ninguna'}", "",
                ])
            ReceiptDialog("\n".join(text), self).exec()
        except (DataAccessError, KeyError) as error:
            show_error(self, error)

    def delete_service(self) -> None:
        record = self.current()
        if record is None or not ask_delete(self, f"el servicio {record['folio']}"):
            return
        try:
            self.controller.delete(record["folio"])
            self.refresh()
        except (DataAccessError, ValueError) as error:
            show_error(self, error)


class ReceiptDialog(QDialog):
    def __init__(self, content: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Comprobante de servicio")
        self.resize(620, 560)
        layout = QVBoxLayout(self)
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        self.content.setPlainText(content)
        layout.addWidget(self.content)
        actions = QHBoxLayout()
        print_button = QPushButton("Imprimir")
        print_button.clicked.connect(self.print_receipt)
        pdf_button = QPushButton("Guardar PDF")
        pdf_button.clicked.connect(self.save_pdf)
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        actions.addWidget(print_button)
        actions.addWidget(pdf_button)
        actions.addStretch()
        actions.addWidget(close_button)
        layout.addLayout(actions)

    def print_receipt(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.content.print_(printer)

    def save_pdf(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar comprobante", "comprobante.pdf", "PDF (*.pdf)"
        )
        if not filename:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filename)
        self.content.print_(printer)


class QInputDialogCompat:
    @staticmethod
    def get_item(
        parent: QWidget, title: str, label: str, items: list[str], current: str
    ) -> tuple[str, bool]:
        from PySide6.QtWidgets import QInputDialog

        return QInputDialog.getItem(parent, title, label, items, items.index(current), False)


class UpcomingPage(QWidget):
    def __init__(self, controller: UpcomingController) -> None:
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        filters = QHBoxLayout()
        self.folio = QLineEdit()
        self.folio.setPlaceholderText("Folio")
        self.owner = QLineEdit()
        self.owner.setPlaceholderText("Propietario")
        refresh = QPushButton("Buscar")
        set_primary_button(refresh)
        refresh.clicked.connect(self.refresh)
        filters.addWidget(self.folio)
        filters.addWidget(self.owner)
        filters.addWidget(refresh)
        layout.addLayout(filters)
        self.table = table_for(
            self,
            ["Fecha", "Folio", "Placas", "Propietario", "Kilometraje", "Notas"],
        )
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        try:
            rows = self.controller.list(
                self.folio.text().strip(),
                self.owner.text().strip(),
            )
            display = [
                {
                    **row,
                    "_owner": " ".join(
                        str(row.get(key) or "")
                        for key in ("nombre", "apellido_paterno", "apellido_materno")
                    ).strip(),
                }
                for row in rows
            ]
            fill_table(
                self.table,
                display,
                ["fecha_programada", "folio", "placas", "_owner", "kilometraje", "notas"],
            )
        except (DataAccessError, ValueError) as error:
            show_error(self, error)


class CustomersVehiclesPage(QWidget):
    def __init__(self, controller: CustomerVehicleController) -> None:
        super().__init__()
        self.controller = controller
        self.customer_rows: list[dict[str, Any]] = []
        self.vehicle_rows: list[dict[str, Any]] = []
        self.catalogs: dict[str, list[dict[str, Any]]] = {
            "marcas": [],
            "modelos": [],
            "anio": [],
        }
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h3>Clientes</h3>"))
        customer_actions = QHBoxLayout()
        for title, callback in (
            ("Nuevo cliente", self.create_customer),
            ("Editar cliente", self.edit_customer),
            ("Desactivar cliente", self.delete_customer),
        ):
            button = QPushButton(title)
            if title.startswith("Nuevo"):
                set_primary_button(button)
            button.clicked.connect(callback)
            customer_actions.addWidget(button)
        customer_actions.addStretch()
        layout.addLayout(customer_actions)
        self.customers = table_for(
            self, ["ID", "Nombre", "Apellido paterno", "Apellido materno", "Telefono", "Email"]
        )
        layout.addWidget(self.customers, 1)
        layout.addWidget(QLabel("<h3>Vehiculos</h3>"))
        vehicle_actions = QHBoxLayout()
        for title, callback in (
            ("Nuevo vehiculo", self.create_vehicle),
            ("Editar vehiculo", self.edit_vehicle),
            ("Desactivar vehiculo", self.delete_vehicle),
        ):
            button = QPushButton(title)
            button.clicked.connect(callback)
            vehicle_actions.addWidget(button)
        vehicle_actions.addStretch()
        layout.addLayout(vehicle_actions)
        self.vehicles = table_for(
            self, ["ID", "Placas", "Propietario", "Marca", "Modelo", "Anio", "Color", "VIN"]
        )
        layout.addWidget(self.vehicles, 2)
        self.refresh()

    def refresh(self) -> None:
        try:
            self.customer_rows, self.vehicle_rows, self.catalogs = self.controller.data()
            fill_table(
                self.customers,
                self.customer_rows,
                ["id_cliente", "nombre", "apellido_paterno", "apellido_materno", "telefono", "email"],
            )
            display = [
                {
                    **row,
                    "_owner": " ".join(
                        str(row.get(key) or "")
                        for key in ("nombre", "apellido_paterno", "apellido_materno")
                    ).strip(),
                }
                for row in self.vehicle_rows
            ]
            fill_table(
                self.vehicles,
                display,
                ["id_vehiculo", "placas", "_owner", "marca", "modelo", "anio", "color", "vin"],
            )
        except (DataAccessError, ValueError) as error:
            show_error(self, error)

    def create_customer(self) -> None:
        self.save_customer()

    def edit_customer(self) -> None:
        row = selected_record(self.customers)
        if row:
            self.save_customer(row)

    def save_customer(self, row: dict[str, Any] | None = None) -> None:
        dialog = CustomerDialog(row, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            payload = dialog.payload()
            self.controller.save_customer(payload, row["id_cliente"] if row else None)
            self.refresh()
        except (DataAccessError, ValueError) as error:
            show_error(self, error)

    def delete_customer(self) -> None:
        row = selected_record(self.customers)
        if row and ask_delete(self, f"el cliente {row['nombre']}"):
            self.run_delete("cliente", row["id_cliente"])

    def create_vehicle(self) -> None:
        self.save_vehicle()

    def edit_vehicle(self) -> None:
        row = selected_record(self.vehicles)
        if row:
            self.save_vehicle(row)

    def save_vehicle(self, row: dict[str, Any] | None = None) -> None:
        dialog = VehicleDialog(self.customer_rows, self.catalogs, row, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            payload = dialog.payload()
            self.controller.save_vehicle(payload, row["id_vehiculo"] if row else None)
            self.refresh()
        except (DataAccessError, ValueError) as error:
            show_error(self, error)

    def delete_vehicle(self) -> None:
        row = selected_record(self.vehicles)
        if row and ask_delete(self, f"el vehiculo {row['placas']}"):
            self.run_delete("vehiculo", row["id_vehiculo"])

    def run_delete(self, entity: str, entity_id: int) -> None:
        try:
            if entity == "cliente":
                self.controller.delete_customer(entity_id)
            else:
                self.controller.delete_vehicle(entity_id)
            self.refresh()
        except (DataAccessError, ValueError) as error:
            show_error(self, error)


class CatalogsPage(QWidget):
    CATALOGS = {
        "marcas": ("Marcas", "id_marca", ["nombre"]),
        "modelos": ("Modelos", "id_modelo", ["id_marca", "nombre"]),
        "anio": ("Anios", "id_anio", ["anio"]),
        "refacciones": ("Refacciones", "id_refaccion", ["nombre", "sku", "cantidad", "precio"]),
    }

    def __init__(self, controller: CatalogController) -> None:
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.catalog = QComboBox()
        for key, (title, _, _) in self.CATALOGS.items():
            self.catalog.addItem(title, key)
        controls.addWidget(self.catalog)
        for title, callback in (
            ("Nuevo", self.create_item),
            ("Editar", self.edit_item),
            ("Desactivar", self.delete_item),
            ("Actualizar", self.refresh),
        ):
            button = QPushButton(title)
            if title == "Nuevo":
                set_primary_button(button)
            button.clicked.connect(callback)
            controls.addWidget(button)
        controls.addStretch()
        layout.addLayout(controls)
        self.table = table_for(self, [""])
        layout.addWidget(self.table)
        self.catalog.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        key = self.catalog.currentData()
        if not key:
            return
        try:
            self.rows = self.controller.list(key)
            keys = self.CATALOGS[key][2]
            self.table.setColumnCount(len(keys) + 1)
            self.table.setHorizontalHeaderLabels(["ID", *keys])
            fill_table(self.table, self.rows, [self.CATALOGS[key][1], *keys])
        except (DataAccessError, ValueError) as error:
            show_error(self, error)

    def create_item(self) -> None:
        self.save_item()

    def edit_item(self) -> None:
        row = selected_record(self.table)
        if row:
            self.save_item(row)

    def save_item(self, row: dict[str, Any] | None = None) -> None:
        key = self.catalog.currentData()
        try:
            brands = self.controller.brands() if key == "modelos" else []
            dialog = CatalogItemDialog(key, brands, row, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            values = dialog.payload()
            item_id = row[self.CATALOGS[key][1]] if row else None
            self.controller.save(key, values, item_id)
            self.refresh()
        except (DataAccessError, ValueError) as error:
            show_error(self, error)

    def delete_item(self) -> None:
        row = selected_record(self.table)
        key = self.catalog.currentData()
        if row and ask_delete(self, "el registro seleccionado"):
            try:
                self.controller.delete(key, row[self.CATALOGS[key][1]])
                self.refresh()
            except (DataAccessError, ValueError) as error:
                show_error(self, error)


class AdminsPage(QWidget):
    def __init__(self, controller: AdminController) -> None:
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        actions = QHBoxLayout()
        for title, callback in (
            ("Nuevo administrador", self.create_admin),
            ("Editar", self.edit_admin),
            ("Desactivar", self.delete_admin),
            ("Actualizar", self.refresh),
        ):
            button = QPushButton(title)
            if title == "Nuevo administrador":
                set_primary_button(button)
            button.clicked.connect(callback)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.table = table_for(self, ["ID", "Nombre", "Usuario", "Activo"])
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        try:
            self.rows = self.controller.list()
            fill_table(
                self.table,
                self.rows,
                ["id_administrador", "nombre", "usuario", "activo"],
            )
        except (DataAccessError, ValueError) as error:
            show_error(self, error)

    def create_admin(self) -> None:
        self.save_admin()

    def edit_admin(self) -> None:
        row = selected_record(self.table)
        if row:
            self.save_admin(row)

    def save_admin(self, row: dict[str, Any] | None = None) -> None:
        def save() -> None:
            try:
                self.controller.save(
                    dialog.payload(),
                    row["id_administrador"] if row else None,
                )
            except (DataAccessError, ValueError) as error:
                show_error(dialog, error)
                return
            dialog.accept()

        dialog = AdminDialog(row, self, on_save=save)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def delete_admin(self) -> None:
        row = selected_record(self.table)
        if row and ask_delete(self, f"el administrador {row['usuario']}"):
            try:
                self.controller.delete(row["id_administrador"])
                self.refresh()
            except (DataAccessError, ValueError) as error:
                show_error(self, error)
