from pathlib import Path
import sqlite3
import unittest


class CatalogSeedTests(unittest.TestCase):
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

    def test_seed_inserts_only_catalogs_with_valid_relations(self):
        self.db.executescript(self.seed)
        for table, expected in (("marcas", 10), ("modelos", 50), ("anios", 12), ("refacciones", 30), ("estados", 3)):
            with self.subTest(table=table):
                self.assertEqual(self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], expected)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_repeated_seed_preserves_edits_and_inactive_records(self):
        self.db.executescript(self.seed)
        self.db.execute("UPDATE refacciones SET precio=321.45, cantidad=7, activo=0 WHERE sku='CAT-BOS-001'")
        self.db.execute("UPDATE marcas SET activo=0 WHERE nombre='Toyota'")
        self.db.commit()
        before = list(self.db.iterdump())
        self.db.executescript(self.seed)
        self.db.executescript(self.seed)
        self.assertEqual(list(self.db.iterdump()), before)

    def test_existing_brand_and_model_ids_are_reused(self):
        self.db.executescript("""
            INSERT INTO marcas (id_marca,nombre) VALUES (99,'Nissan');
            INSERT INTO modelos (id_modelo,id_marca,nombre) VALUES (80,99,'Versa');
        """)
        self.db.executescript(self.seed)
        self.assertEqual(self.db.execute("SELECT id_marca FROM marcas WHERE nombre='Nissan'").fetchall(), [(99,)])
        self.assertEqual(self.db.execute("SELECT id_modelo FROM modelos WHERE id_marca=99 AND nombre='Versa'").fetchall(), [(80,)])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM modelos WHERE id_marca=99").fetchone()[0], 5)


if __name__ == "__main__":
    unittest.main()
