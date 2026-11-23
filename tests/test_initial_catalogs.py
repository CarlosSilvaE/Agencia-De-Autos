from pathlib import Path
import sqlite3
import unittest
from unittest.mock import Mock

from models.database import DataAccessError
from models.schema import normalize_years


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
            CREATE TABLE anios (id_anio INTEGER PRIMARY KEY, anio INTEGER UNIQUE, activo INTEGER DEFAULT 1);
            CREATE TABLE estados (id_estado INTEGER PRIMARY KEY, nombre TEXT UNIQUE, activo INTEGER DEFAULT 1);
            CREATE TABLE refacciones (id_refaccion INTEGER PRIMARY KEY, nombre TEXT, sku TEXT UNIQUE, cantidad INTEGER, precio NUMERIC, activo INTEGER DEFAULT 1);
        """)

    def test_seed_loads_only_catalogs_with_correct_relationships(self):
        self.db.executescript(self.seed)
        for table, count in (("marcas", 10), ("modelos", 50), ("anios", 12), ("refacciones", 30), ("estados", 3)):
            with self.subTest(table=table):
                self.assertEqual(self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], count)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.db.execute("SELECT MIN(anio), MAX(anio) FROM anios").fetchone(), (2015, 2026))

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
    def cursor(self, tables, columns):
        cursor = Mock()
        cursor.fetchall.side_effect = [
            [{"TABLE_NAME": table} for table in tables],
            [{"TABLE_NAME": table, "COLUMN_NAME": column} for table, column in columns],
        ]
        return cursor

    def test_legacy_names_are_renamed_without_deleting_records(self):
        for source in ("ano", "anos", "anio", "anios"):
            with self.subTest(source=source):
                cursor = self.cursor([source], [(source, "id_ano"), (source, "ano"), ("vehiculos", "id_ano")])
                normalize_years(cursor)
                statements = [call.args[0] for call in cursor.execute.call_args_list]
                rename_catalog = f"ALTER TABLE `{source}` RENAME COLUMN `id_ano` TO `id_anio`, RENAME COLUMN `ano` TO `anio`"
                if source != "anios":
                    rename_catalog += ", RENAME TO `anios`"
                self.assertEqual(statements[2:], [rename_catalog, "ALTER TABLE vehiculos RENAME COLUMN id_ano TO id_anio"])

    def test_current_schema_requires_no_ddl(self):
        cursor = self.cursor(["anios"], [("anios", "id_anio"), ("anios", "anio"), ("vehiculos", "id_anio")])
        normalize_years(cursor)
        self.assertEqual(cursor.execute.call_count, 2)

    def test_multiple_year_tables_fail_before_ddl(self):
        cursor = self.cursor(["anos", "anio"], [])
        with self.assertRaises(DataAccessError):
            normalize_years(cursor)
        self.assertEqual(cursor.execute.call_count, 1)

    def test_partial_rename_resumes_with_vehicle_column(self):
        cursor = self.cursor(["anios"], [("anios", "id_anio"), ("anios", "anio"), ("vehiculos", "id_ano")])
        normalize_years(cursor)
        self.assertEqual(cursor.execute.call_count, 3)
        cursor.execute.assert_called_with("ALTER TABLE vehiculos RENAME COLUMN id_ano TO id_anio")


if __name__ == "__main__":
    unittest.main()
