from __future__ import annotations
import unittest
from unittest.mock import Mock
from controllers import AgencyControllers
from models import AgencyModel, DataAccessError
from models.dashboard_strategy import DailyDashboardStrategy, TotalDashboardStrategy
from models.provider import DatabaseProvider


class DesignPatternTests(unittest.TestCase):
    def test_singleton_uses_same_provider_and_database(self):
        first, second = DatabaseProvider(), DatabaseProvider()
        self.assertIs(first, second)
        self.assertIs(first.database, second.database)

    def test_strategy_daily_filters_date_without_sql_interpolation(self):
        sql, params = DailyDashboardStrategy().build('2026-11-10')
        self.assertIn('DATE(s.fecha_ingreso)=%s', sql)
        self.assertEqual(params, ('2026-11-10',))
        with self.assertRaises(ValueError):
            DailyDashboardStrategy().build('2026-99-99')
        with self.assertRaises(ValueError):
            DailyDashboardStrategy().build(None)

    def test_strategy_total_uses_no_parameters(self):
        sql, params = TotalDashboardStrategy().build()
        self.assertIn('LEFT JOIN servicios', sql)
        self.assertEqual(params, ())
        self.assertNotIn('DATE(s.fecha_ingreso)', sql)

    def test_model_selects_strategy_and_rejects_unknown_mode(self):
        db = Mock()
        cursor = Mock()
        cursor.fetchall.return_value = [{'estado': 'En espera', 'cantidad': 4}]
        db.session.return_value.__enter__ = Mock(return_value=(None, cursor))
        db.session.return_value.__exit__ = Mock(return_value=False)
        model = AgencyModel(db)
        result = model.dashboard('daily', '2026-11-10')
        self.assertEqual(result[0]['cantidad'], 4)
        self.assertEqual(cursor.execute.call_args.args[1], ('2026-11-10',))
        with self.assertRaises(ValueError):
            model.dashboard('invalido')

    def test_noop_update_is_not_missing_record(self):
        cursor = Mock()
        cursor.fetchone.return_value = {'1': 1}
        AgencyModel._require_existing_update(
            cursor, 0, 'clientes', 'id_cliente', 42, 'No se encontró.'
        )
        cursor.execute.assert_called_once()

    def test_missing_record_still_fails(self):
        cursor = Mock()
        cursor.fetchone.return_value = None
        with self.assertRaises(DataAccessError):
            AgencyModel._require_existing_update(
                cursor, 0, 'clientes', 'id_cliente', 42, 'No se encontró.'
            )

    def test_logout_forgets_current_admin(self):
        model = Mock(spec=AgencyModel)
        model.authenticate.return_value = 'admin'
        auth = AgencyControllers.from_model(model).auth
        self.assertEqual(auth.login('admin', 'clave'), 'admin')
        self.assertEqual(auth.current_user, 'admin')
        auth.logout()
        self.assertIsNone(auth.current_user)


if __name__ == '__main__':
    unittest.main()


class ReceiptDomainTests(unittest.TestCase):
    def test_receipt_includes_service_parts_owner_deliverer_and_next_date(self):
        from models.domain import ServiceReceipt
        receipt = ServiceReceipt.from_records(
            {"folio": "S-1", "nombre": "Ana", "apellido_paterno": "López",
             "nombre_entrega": "Carlos", "proximo_servicio": "2026-12-05",
             "costo": "150.50", "placas": "ABC-123"},
            [{"nombre": "Filtro", "cantidad": 2, "precio_unitario": "25.00"}],
        )
        result = receipt.as_text()
        for value in ('S-1', 'Ana López', 'Carlos', '2026-12-05', 'Filtro (x2)', '$150.50'):
            self.assertIn(value, result)
