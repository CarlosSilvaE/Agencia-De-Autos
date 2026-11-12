from contextlib import contextmanager
import unittest
from unittest.mock import Mock, patch

from mysql.connector.errors import Error as MySQLError

from models import AgencyModel, DataAccessError
from models.database import MySQLDatabase


class RequestedFixTests(unittest.TestCase):
    def setUp(self):
        self.cursor = Mock()
        self.cursor.rowcount = 1
        self.connection = Mock()
        self.database = Mock()

        @contextmanager
        def session(**kwargs):
            yield self.connection, self.cursor

        self.database.session.side_effect = session
        self.model = AgencyModel(self.database)
        self.payload = {
            "descripcion": "Cambio de aceite", "tipoServicio": "Preventivo",
            "estado": "En espera", "costo": 100, "cliente": {},
            "vehiculo": {}, "entrega": {},
        }

    def test_generated_folio_fits_schema_and_is_unique(self):
        with patch.object(self.model, "_save_client"), patch.object(
            self.model, "_save_vehicle"
        ), patch.object(self.model, "_save_service_relations"):
            self.cursor.lastrowid = 1
            folios = [self.model.create_service(self.payload)["folio"] for _ in range(20)]
        self.assertEqual(len(set(folios)), 20)
        self.assertTrue(all(len(folio) <= 30 for folio in folios))

    def test_long_custom_folio_fails_before_database_access(self):
        with self.assertRaisesRegex(ValueError, "folio"):
            self.model.create_service({**self.payload, "folio": "X" * 31})
        self.database.session.assert_not_called()

    def test_empty_vin_generates_valid_values(self):
        values = [AgencyModel._validate_vin(value) for value in (None, "", "  ")]
        self.assertEqual(len(set(values)), 3)
        for vin in values:
            self.assertRegex(vin, r"^[A-HJ-MO-PR-Z0-9]{17}$")

    def test_vin_normalizes_lowercase(self):
        self.assertEqual(AgencyModel._validate_vin(" abcdefghj23456789 "), "ABCDEFGHJ23456789")

    def test_generated_vin_is_sent_to_vehicle_insert(self):
        self.cursor.fetchone.return_value = {"total": 1}
        self.model.save_vehicle({
            "idCliente": 1, "idMarca": 1, "idModelo": 1, "idAno": 1,
            "placas": "ABC-123", "vin": "",
        })
        sql, values = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO vehiculos", sql)
        self.assertRegex(values[-1], r"^[A-HJ-MO-PR-Z0-9]{17}$")

    def test_manual_vin_is_preserved_when_saving(self):
        self.cursor.fetchone.return_value = {"total": 1}
        self.model.save_vehicle({
            "idCliente": 1, "idMarca": 1, "idModelo": 1, "idAno": 1,
            "placas": "ABC-123", "vin": "abcdefghj23456789",
        }, vehicle_id=3)
        self.assertEqual(self.cursor.execute.call_args.args[1][-2], "ABCDEFGHJ23456789")

    def test_vin_rejects_missing_length_symbols_and_forbidden_letters(self):
        for vin in ("A" * 16, "A" * 18, "A" * 16 + "-",
                    "A" * 16 + "I", "A" * 16 + "N", "A" * 16 + "Q",
                    "A" * 16 + "\u00f1", "A" * 16 + " "):
            with self.subTest(vin=vin), self.assertRaises(ValueError):
                AgencyModel._validate_vin(vin)

    def test_vehicle_save_rejects_invalid_vin_before_sql(self):
        with self.assertRaisesRegex(ValueError, "VIN"):
            self.model.save_vehicle({"placas": "ABC", "vin": "INVALIDO"})
        self.database.session.assert_not_called()

    def test_service_vehicle_path_rejects_invalid_vin(self):
        with self.assertRaisesRegex(ValueError, "VIN"):
            self.model._save_vehicle(self.cursor, {"placas": "ABC", "vin": "INVALIDO"}, 1)
        self.cursor.execute.assert_not_called()

    def test_admin_is_deleted_including_inactive_accounts(self):
        self.cursor.fetchall.return_value = [{"id_administrador": 1}]
        self.model.delete_admin(2)
        self.cursor.execute.assert_any_call(
            "DELETE FROM administradores WHERE id_administrador=%s", (2,)
        )
        self.database.session.assert_called_once_with(transaction=True)

    def test_last_active_admin_is_protected(self):
        self.cursor.fetchall.return_value = [{"id_administrador": 1}]
        with self.assertRaises(DataAccessError):
            self.model.delete_admin(1)
        self.assertEqual(self.cursor.execute.call_count, 1)

    def test_missing_admin_is_reported(self):
        self.cursor.fetchall.return_value = [{"id_administrador": 1}]
        self.cursor.rowcount = 0
        with self.assertRaises(DataAccessError):
            self.model.delete_admin(2)


class DatabaseSessionTests(unittest.TestCase):
    def test_cursor_creation_failure_closes_connection(self):
        database = MySQLDatabase()
        connection = Mock()
        connection.cursor.side_effect = MySQLError("cursor failure")
        with patch.object(database, "connect", return_value=connection):
            with self.assertRaises(DataAccessError):
                with database.session():
                    self.fail("No debe abrir la sesion")
        connection.close.assert_called_once()

    def test_cursor_close_failure_still_closes_connection(self):
        database = MySQLDatabase()
        connection = Mock()
        connection.cursor.return_value.close.side_effect = RuntimeError("close failure")
        with patch.object(database, "connect", return_value=connection):
            with self.assertRaises(RuntimeError):
                with database.session():
                    pass
        connection.close.assert_called_once()

    def test_transaction_rolls_back_on_business_error(self):
        database = MySQLDatabase()
        connection = Mock()
        with patch.object(database, "connect", return_value=connection):
            with self.assertRaises(ValueError):
                with database.session(transaction=True):
                    raise ValueError("Inventario insuficiente")
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()
        connection.close.assert_called_once()
