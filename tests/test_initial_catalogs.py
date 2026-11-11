from pathlib import Path
import sqlite3
import unittest
from unittest.mock import Mock

from models.database import DataAccessError
from models.schema import migrar_esquema_anio


class InitialCatalogTests(unittest.TestCase):
    """Comprueba los INSERT reales en un motor SQL, sin credenciales de desarrollo."""

    def setUp(self):
        sql = (Path(__file__).resolve().parents[1] / "database" / "init.sql").read_text(encoding="utf-8")
        self.seed = "BEGIN;" + sql.split("START TRANSACTION;", 1)[1]
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE marcas (id_marca INTEGER PRIMARY KEY, nombre TEXT UNIQUE, activo INTEGER DEFAULT 1);
            CREATE TABLE modelos (id_modelo INTEGER PRIMARY KEY, id_marca INTEGER REFERENCES marcas(id_marca), nombre TEXT, activo INTEGER DEFAULT 1);
            CREATE TABLE anio (id_anio INTEGER PRIMARY KEY, anio INTEGER UNIQUE, activo INTEGER DEFAULT 1);
            CREATE TABLE estados (id_estado INTEGER PRIMARY KEY, nombre TEXT UNIQUE, activo INTEGER DEFAULT 1);
            CREATE TABLE refacciones (id_refaccion INTEGER PRIMARY KEY, nombre TEXT, sku TEXT UNIQUE, cantidad INTEGER, precio NUMERIC, activo INTEGER DEFAULT 1);
        """)

    def test_seed_loads_only_catalogs_with_correct_relationships(self):
        self.db.executescript(self.seed)
        for table, count in (("marcas", 10), ("modelos", 50), ("anio", 12), ("refacciones", 30), ("estados", 3)):
            with self.subTest(table=table):
                self.assertEqual(self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], count)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.db.execute("SELECT MIN(anio), MAX(anio) FROM anio").fetchone(), (2015, 2026))

    def test_repeating_seed_preserves_edited_price_stock_and_inactive_rows(self):
        self.db.executescript(self.seed)
        self.db.execute("UPDATE refacciones SET precio=321.45, cantidad=7, activo=0 WHERE sku='CAT-BOS-001'")
        self.db.execute("UPDATE marcas SET activo=0 WHERE nombre='Toyota'")
        self.db.commit()
        before = list(self.db.iterdump())
        self.db.executescript(self.seed)
        self.db.executescript(self.seed)
        self.assertEqual(list(self.db.iterdump()), before)

    def test_models_use_existing_brand_identifier(self):
        self.db.executescript("""
            INSERT INTO marcas (id_marca,nombre) VALUES (99,'Nissan');
            INSERT INTO modelos (id_modelo,id_marca,nombre) VALUES (80,99,'Versa');
        """)
        self.db.executescript(self.seed)
        self.assertEqual(self.db.execute("SELECT id_marca FROM marcas WHERE nombre='Nissan'").fetchall(), [(99,)])
        self.assertEqual(self.db.execute("SELECT id_modelo FROM modelos WHERE id_marca=99 AND nombre='Versa'").fetchall(), [(80,)])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM modelos WHERE id_marca=99").fetchone()[0], 5)


class YearSchemaMigrationTests(unittest.TestCase):
    def connection(self, tables, columns):
        connection = Mock(in_transaction=False)
        connection.cursor.return_value.fetchall.side_effect = [tables, columns]
        return connection

    def test_legacy_names_are_renamed_without_deleting_records(self):
        for source in ("ano", "anos", "anios"):
            with self.subTest(source=source):
                connection = self.connection([(source,)], [(source, "id_ano"), (source, "ano"), ("vehiculos", "id_ano")])
                migrar_esquema_anio(connection)
                statements = [call.args[0] for call in connection.cursor.return_value.execute.call_args_list]
                self.assertEqual(statements[-2], f"ALTER TABLE `{source}` RENAME COLUMN `id_ano` TO `id_anio`, RENAME COLUMN `ano` TO `anio`, RENAME TO `anio`")
                self.assertEqual(statements[-1], "ALTER TABLE `vehiculos` RENAME COLUMN `id_ano` TO `id_anio`")
                self.assertFalse(any(sql.startswith(("DELETE", "DROP", "INSERT", "UPDATE")) for sql in statements))

    def test_current_schema_requires_no_ddl(self):
        connection = self.connection([("anio",)], [("anio", "id_anio"), ("anio", "anio"), ("vehiculos", "id_anio")])
        migrar_esquema_anio(connection)
        self.assertEqual(connection.cursor.return_value.execute.call_count, 2)

    def test_multiple_year_tables_fail_before_ddl(self):
        connection = self.connection([("anos",), ("anio",)], [])
        with self.assertRaises(DataAccessError):
            migrar_esquema_anio(connection)
        self.assertEqual(connection.cursor.return_value.execute.call_count, 1)
        connection.commit.assert_not_called()

    def test_active_business_transaction_is_not_committed_by_migration(self):
        connection = Mock(in_transaction=True)
        with self.assertRaises(DataAccessError):
            migrar_esquema_anio(connection)
        connection.cursor.assert_not_called()
        connection.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
