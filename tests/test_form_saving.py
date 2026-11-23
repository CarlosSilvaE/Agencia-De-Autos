from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox

from controllers import AdminController, ServiceController
from models import AgencyModel, DataAccessError
from views.forms import AdminDialog, ServiceDialog
from views.main_window import AdminsPage, ServicesPage


VEHICLE = {
    "id_vehiculo": 1, "id_cliente": 2, "id_marca": 3, "id_modelo": 4,
    "id_anio": 5, "nombre": "Ana", "apellido_paterno": "Lopez",
    "placas": "PRUEBA", "marca": "Nissan", "modelo": "Versa",
}
PART = {"id_refaccion": 6, "nombre": "Filtro de aceite", "precio": 180.00}


class FormSavingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def exercise(self, dialog_type, operation, action):
        def run(dialog):
            dialog.show()
            self.app.processEvents()
            try:
                action(dialog, errors)
                return dialog.result()
            finally:
                dialog.hide()

        with patch.object(dialog_type, "exec", new=run), patch(
            "views.main_window.show_error"
        ) as errors, patch("views.main_window.QMessageBox.information"):
            operation()

    def click(self, dialog, button=QDialogButtonBox.StandardButton.Save):
        dialog.findChild(QDialogButtonBox).button(button).click()

    def admin_page(self):
        database = MagicMock()
        cursor = Mock(rowcount=1)
        database.session.return_value.__enter__.return_value = (None, cursor)
        controller = Mock(spec=AdminController)
        controller.list.return_value = []
        controller.save.side_effect = AgencyModel(database).save_admin
        page = AdminsPage(controller)
        self.addCleanup(page.close)
        return page, database, cursor

    def service_page(self):
        controller = Mock(spec=ServiceController)
        controller.list.return_value = []
        controller.options.return_value = ([VEHICLE], [PART])
        page = ServicesPage(controller)
        self.addCleanup(page.close)
        return page, controller

    def test_admin_retries_blank_and_short_password_without_losing_data(self):
        page, database, _ = self.admin_page()

        def action(dialog, errors):
            dialog.name.setText("Ana Lopez")
            dialog.username.setText("ana")
            for password in ("", "   ", *("a" * length for length in range(1, 8))):
                with self.subTest(password=password):
                    dialog.password.setText(password)
                    self.click(dialog)
                    self.assertTrue(dialog.isVisible())
                    self.assertEqual(dialog.name.text(), "Ana Lopez")
                    self.assertEqual(dialog.username.text(), "ana")
                    self.assertEqual(dialog.password.text(), password)
                    self.assertIs(errors.call_args.args[0], dialog)
                    self.assertIn("8 caracteres", str(errors.call_args.args[1]))
                    database.session.assert_not_called()
            dialog.password.setText("abcdefgh")
            self.click(dialog)
            self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
            self.assertFalse(dialog.isVisible())
            database.session.assert_called_once_with(transaction=True)

        self.exercise(AdminDialog, page.save_admin, action)
        self.assertEqual(page.controller.list.call_count, 2)

    def test_edit_admin_allows_blank_password_to_keep_existing_hash(self):
        page, database, cursor = self.admin_page()
        record = {"id_administrador": 9, "nombre": "Ana", "usuario": "ana", "activo": True}

        def action(dialog, errors):
            self.assertEqual(dialog.password.placeholderText(), "Dejar vacio para conservar")
            dialog.password.setText("corta")
            self.click(dialog)
            self.assertTrue(dialog.isVisible())
            database.session.assert_not_called()
            dialog.password.clear()
            self.click(dialog)
            self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
            self.assertNotIn("password_hash", cursor.execute.call_args.args[0])
            errors.assert_called_once()

        self.exercise(AdminDialog, lambda: page.save_admin(record), action)

    def test_admin_database_error_keeps_form_open_and_cancel_does_not_refresh(self):
        page, _, _ = self.admin_page()
        page.controller.save.side_effect = DataAccessError("Usuario duplicado.")

        def action(dialog, errors):
            dialog.name.setText("Ana")
            dialog.username.setText("ana")
            dialog.password.setText("abcdefgh")
            self.click(dialog)
            self.assertTrue(dialog.isVisible())
            errors.assert_called_once()
            self.click(dialog, QDialogButtonBox.StandardButton.Cancel)
            self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)

        self.exercise(AdminDialog, page.save_admin, action)
        page.controller.list.assert_called_once()

    def test_create_service_keeps_selected_parts_after_validation_error(self):
        page, controller = self.service_page()
        controller.create.side_effect = [ValueError("Se requiere la persona que entrega."), {"folio": "SRV-1"}]

        def action(dialog, errors):
            dialog.description.setPlainText("Cambio de aceite")
            dialog.tabs.setCurrentIndex(1)
            dialog.parts_table.item(0, 0).setCheckState(Qt.CheckState.Checked)
            dialog.parts_table.cellWidget(0, 2).setValue(2)
            self.click(dialog)
            self.assertTrue(dialog.isVisible())
            self.assertEqual(dialog.description.toPlainText(), "Cambio de aceite")
            self.assertEqual(dialog.payload()["refacciones"][0]["cantidad"], 2)
            errors.assert_called_once()
            self.assertEqual(controller.list.call_count, 1)
            dialog.tabs.setCurrentIndex(2)
            dialog.deliverer.setText("Luis Lopez")
            self.click(dialog)
            self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
            self.assertFalse(dialog.isVisible())
            self.assertEqual(controller.create.call_args.args[0]["entrega"]["nombre"], "Luis Lopez")

        self.exercise(ServiceDialog, page.create_service, action)
        self.assertEqual(controller.list.call_count, 2)

    def test_edit_service_preserves_form_after_save_error(self):
        page, controller = self.service_page()
        record = {
            **VEHICLE, "folio": "SRV-1", "tipo_servicio": "Preventivo",
            "estado": "En espera", "descripcion": "Cambio de aceite",
            "nombre_entrega": "Ana Lopez", "costo": 500,
            "proximo_servicio": "2027-01-10", "kilometraje": 30000,
            "notas_proximo_servicio": "Revision de frenos",
        }
        controller.list.return_value = [record]
        controller.parts.return_value = [{**PART, "cantidad": 2, "precio_unitario": 180.00}]
        controller.update.side_effect = [DataAccessError("Error al guardar."), None]
        page.refresh()
        page.table.selectRow(0)

        def action(dialog, errors):
            self.assertEqual(dialog.payload()["refacciones"][0]["cantidad"], 2)
            self.assertEqual(dialog.payload()["proximoServicio"]["fechaProgramada"], "2027-01-10")
            dialog.description.setPlainText("Cambio de aceite y revision")
            self.click(dialog)
            self.assertTrue(dialog.isVisible())
            self.assertEqual(dialog.description.toPlainText(), "Cambio de aceite y revision")
            errors.assert_called_once()
            self.click(dialog)
            self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)

        self.exercise(ServiceDialog, page.edit_service, action)
        self.assertEqual(controller.update.call_count, 2)
        self.assertEqual(controller.update.call_args.args[0], "SRV-1")


if __name__ == "__main__":
    unittest.main()
