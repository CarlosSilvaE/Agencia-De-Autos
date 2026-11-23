"""Pruebas optativas con bases y cuentas temporales propias en MySQL Docker."""
import os
from pathlib import Path
import re
import secrets
import unittest
from uuid import uuid4

from configuration import ROOT, load_project_env
from models import AgencyModel, DataAccessError
from models.database import MySQLDatabase
from models.schema import prepare_schema
from scripts.preparar_entorno import bootstrap_sql, run_compose


@unittest.skipUnless(os.getenv("AGENCIA_MYSQL_INTEGRATION") == "1", "Activar AGENCIA_MYSQL_INTEGRATION=1 para probar MySQL Docker.")
class MySQLDeploymentIntegrationTests(unittest.TestCase):
    def root_sql(self, sql):
        return run_compose([
            "exec", "-T", "-e", "MYSQL_PWD", "database", "mysql", "--user=root",
            "--batch", "--silent", "--skip-column-names", "--default-character-set=utf8mb4",
        ], self.values, ROOT / ".env", sql=sql)

    def setUp(self):
        self.values = load_project_env(deployment=True)
        token = uuid4().hex[:12]
        self.name = "agencia_verificacion_" + token
        self.user = "verificacion_" + token
        self.password = secrets.token_urlsafe(18) + "'\\$"
        # Comprobar que estos nombres no pertenecen a un recurso anterior.
        existing = self.root_sql(
            f"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{self.name}';"
            f"SELECT User FROM mysql.user WHERE User='{self.user}';"
        ).stdout.strip()
        if existing:
            self.fail("El nombre temporal ya existe; no se modifico ese recurso.")
        self.addCleanup(self.cleanup_resources)
        temporary_values = {**self.values, "MYSQL_DATABASE": self.name, "MYSQL_USER": self.user, "MYSQL_PASSWORD": self.password}
        self.root_sql(bootstrap_sql(temporary_values))
        self.database = MySQLDatabase()
        self.database.settings.update(database=self.name, user=self.user, password=self.password)

    def cleanup_resources(self):
        if not re.fullmatch(r"agencia_verificacion_[a-f0-9]{12}", self.name):
            raise AssertionError("La limpieza no puede salir de la base temporal.")
        if not re.fullmatch(r"verificacion_[a-f0-9]{12}", self.user):
            raise AssertionError("La limpieza no puede salir de la cuenta temporal.")
        self.root_sql(f"DROP DATABASE IF EXISTS `{self.name}`; DROP USER IF EXISTS '{self.user}'@'%';")

    def snapshot(self):
        with self.database.session() as (_, cursor):
            cursor.execute("SHOW TABLES")
            tables = [next(iter(row.values())) for row in cursor.fetchall()]
            result = {}
            for table in tables:
                cursor.execute(f"SELECT * FROM `{table}` ORDER BY 1,2")
                result[table] = cursor.fetchall()
            return result

    def create_sample_service(self):
        model = AgencyModel(self.database)
        payload = {
            "folio": "VERIFICACION-001", "descripcion": "Prueba de despliegue",
            "tipoServicio": "Preventivo", "estado": "En espera", "manoObra": "1500",
            "cliente": {"nombre": "Prueba", "apellidoPaterno": "Despliegue"},
        }
        with self.database.session() as (_, cursor):
            cursor.execute("SELECT id_modelo,id_marca FROM modelos ORDER BY id_modelo LIMIT 1")
            selected = cursor.fetchone()
            cursor.execute("SELECT id_anio FROM anios ORDER BY id_anio LIMIT 1")
            year = cursor.fetchone()["id_anio"]
            cursor.execute("SELECT id_refaccion,precio FROM refacciones WHERE sku='CAT-BOS-001'")
            part = cursor.fetchone()
        payload["vehiculo"] = {"idModelo": selected["id_modelo"], "idMarca": selected["id_marca"], "idAno": year, "placas": "VERIFICACION"}
        payload["refacciones"] = [{"idRefaccion": part["id_refaccion"], "cantidad": 2, "precioUnitario": part["precio"]}]
        model.create_service(payload)
        return model

    def test_fresh_database_and_repeated_preparation_preserve_records(self):
        prepare_schema(self.database)
        model = self.create_sample_service()
        model.initialize("desarrollo", "prueba-despliegue-123")
        self.assertEqual(model.authenticate("desarrollo", "prueba-despliegue-123"), "desarrollo")
        self.assertEqual(len(model.list_catalog("marcas")), 10)
        self.assertEqual(len(model.list_catalog("modelos")), 50)
        before = self.snapshot()
        prepare_schema(self.database)
        model.initialize("desarrollo", "otro-valor-no-restablece")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(model.authenticate("desarrollo", "prueba-despliegue-123"), "desarrollo")

    def test_old_names_and_missing_or_partial_labor_migrate_without_data_loss(self):
        prepare_schema(self.database)
        model = self.create_sample_service()
        before = self.snapshot()
        with self.database.session() as (_, cursor):
            cursor.execute("ALTER TABLE anios RENAME COLUMN id_anio TO id_ano, RENAME COLUMN anio TO ano, RENAME TO anos")
            cursor.execute("ALTER TABLE vehiculos RENAME COLUMN id_anio TO id_ano")
            cursor.execute("ALTER TABLE servicios DROP COLUMN mano_obra")
        prepare_schema(self.database)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(model.list_services()[0]["mano_obra"], 1500)
        with self.database.session(transaction=True) as (_, cursor):
            cursor.execute("ALTER TABLE servicios MODIFY COLUMN mano_obra DECIMAL(12,2) NULL DEFAULT NULL")
            cursor.execute("UPDATE servicios SET mano_obra=NULL")
        prepare_schema(self.database)
        self.assertEqual(self.snapshot(), before)

    def test_env_password_synchronizes_existing_account_with_special_characters(self):
        with self.database.session() as (_, cursor):
            cursor.execute("SELECT 1 AS conectado")
            self.assertEqual(cursor.fetchone()["conectado"], 1)
        new_password = secrets.token_urlsafe(18) + "'\\${literal}"
        values = {**self.values, "MYSQL_DATABASE": self.name, "MYSQL_USER": self.user, "MYSQL_PASSWORD": new_password}
        self.root_sql(bootstrap_sql(values))
        with self.assertRaises(DataAccessError):
            self.database.connect()
        self.database.settings["password"] = new_password
        with self.database.session() as (_, cursor):
            cursor.execute("SELECT 1 AS conectado")
            self.assertEqual(cursor.fetchone()["conectado"], 1)


if __name__ == "__main__":
    unittest.main()
