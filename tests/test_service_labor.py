from decimal import Decimal
import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from models import AgencyModel
from models.domain import ServiceReceipt
from views.forms import ServiceDialog


VEHICLE = {
    "id_vehiculo": 1, "id_cliente": 2, "id_marca": 3, "id_modelo": 4,
    "id_anio": 5, "nombre": "Ana", "apellido_paterno": "Lopez",
    "placas": "PRUEBA", "marca": "Nissan", "modelo": "Versa",
}
PART = {"id_refaccion": 6, "nombre": "Filtro", "precio": 180}


class ServiceLaborTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def dialog(self, record=None, existing_parts=None):
        dialog = ServiceDialog([VEHICLE], [PART], record, existing_parts)
        self.addCleanup(dialog.close)
        return dialog

    def test_new_service_defaults_to_1500_and_accepts_empty_reception(self):
        dialog = self.dialog()
        dialog.description.setPlainText("Revision general")
        self.assertEqual(dialog.labor.value(), 1500)
        self.assertEqual(dialog.cost.value(), 1500)
        self.assertTrue(dialog.cost.isReadOnly())
        self.assertEqual(AgencyModel._validate_service(dialog.payload()), (Decimal("1500.00"), Decimal("1500.00")))

    def test_total_reacts_to_selection_quantity_price_and_labor(self):
        dialog = self.dialog()
        dialog.parts_table.item(0, 0).setCheckState(Qt.CheckState.Checked)
        self.assertEqual(dialog.cost.value(), 1680)
        dialog.parts_table.cellWidget(0, 2).setValue(2)
        self.assertEqual(dialog.cost.value(), 1860)
        dialog.parts_table.cellWidget(0, 3).setValue(125.50)
        dialog.labor.setValue(1600.25)
        self.assertEqual(dialog.cost.value(), 1851.25)
        dialog.parts_table.item(0, 0).setCheckState(Qt.CheckState.Unchecked)
        self.assertEqual(dialog.cost.value(), 1600.25)

    def test_edit_keeps_saved_zero_labor(self):
        dialog = self.dialog(
            {**VEHICLE, "mano_obra": 0, "costo": 360},
            [{**PART, "cantidad": 2, "precio_unitario": 180}],
        )
        self.assertEqual(dialog.labor.value(), 0)
        self.assertEqual(dialog.cost.value(), 360)

    def test_model_calculates_total_without_trusting_payload_cost(self):
        payload = {"manoObra": "1600.25", "costo": "1", "refacciones": [
            {"cantidad": 2, "precioUnitario": "125.50"},
        ]}
        self.assertEqual(AgencyModel._service_amounts(payload), (Decimal("1600.25"), Decimal("1851.25")))
        self.assertEqual(AgencyModel._service_amounts({}), (Decimal("1500.00"), Decimal("1500.00")))

    def test_model_rejects_invalid_money_and_quantities(self):
        for amount in ("-1", "NaN", "Infinity", "incorrecto", "10000000000"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                AgencyModel._service_amounts({"manoObra": amount})
        for quantity in (0, -1, 1.5, "NaN", 2000000001):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                AgencyModel._service_amounts({"refacciones": [{"cantidad": quantity, "precioUnitario": 5}]})

    def test_empty_reception_does_not_create_empty_history_and_still_saves_next_service(self):
        cursor = Mock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = None
        AgencyModel(Mock())._save_service_relations(cursor, 1, {
            "entrega": {}, "proximoServicio": {"fechaProgramada": "2027-01-10"},
        })
        statements = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertFalse(any("INSERT INTO entregas" in sql for sql in statements))
        self.assertTrue(any("INSERT INTO proximos_servicios" in sql for sql in statements))

    def test_clearing_reception_appends_history_instead_of_deleting_previous_entries(self):
        cursor = Mock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = {
            "nombre_entrega": "Ana", "telefono": None,
            "relacion_propietario": None, "observaciones": None,
        }
        AgencyModel(Mock())._save_service_relations(cursor, 1, {"entrega": {}})
        statements = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertFalse(any("DELETE FROM entregas" in sql for sql in statements))
        delivery_calls = [call for call in cursor.execute.call_args_list if "INSERT INTO entregas" in call.args[0]]
        self.assertEqual(delivery_calls[0].args[1], (1, "", None, None, None))

    def test_omitted_reception_preserves_existing_history(self):
        cursor = Mock()
        cursor.fetchall.return_value = []
        AgencyModel(Mock())._save_service_relations(cursor, 1, {})
        self.assertFalse(any("entregas" in call.args[0] for call in cursor.execute.call_args_list))

    def test_receipt_shows_labor_parts_total_and_unregistered_reception(self):
        receipt = ServiceReceipt.from_records(
            {"folio": "PRUEBA", "mano_obra": "1500", "costo": "1860"},
            [{"nombre": "Filtro", "cantidad": 2, "precio_unitario": "180"}],
        ).as_text()
        for text in ("Mano de obra: $1,500.00", "Subtotal refacciones: $360.00", "Total del servicio: $1,860.00", "Persona que entrego: No registrado"):
            self.assertIn(text, receipt)


if __name__ == "__main__":
    unittest.main()
