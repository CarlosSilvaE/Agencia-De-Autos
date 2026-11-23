import os
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from configuration import CONFIG_KEYS, ConfigurationError, load_project_env
from models import DataAccessError
from models.schema import normalize_years
from scripts.preparar_entorno import RootAccessError, bootstrap_sql, preparar, run_compose


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.env = Path(self.directory.name) / ".env"
        self.values = {
            "MYSQL_ROOT_PASSWORD": "root-demo-123", "MYSQL_DATABASE": "agencia_demo",
            "MYSQL_USER": "demo", "MYSQL_PASSWORD": "demo-123456",
            "MYSQL_HOST": "127.0.0.1", "MYSQL_PORT": "3307",
            "ADMIN_INITIAL_USERNAME": "developer", "ADMIN_INITIAL_PASSWORD": "developer",
        }
        self.environment = patch.dict(os.environ)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        for key in CONFIG_KEYS:
            os.environ.pop(key, None)

    def write_env(self):
        self.env.write_text("\n".join(f"{key}={value}" for key, value in self.values.items()), encoding="utf-8")

    def test_file_has_priority_over_old_terminal_variables(self):
        self.write_env()
        os.environ.update(MYSQL_USER="antiguo", MYSQL_PORT="1234", COMPOSE_PROJECT_NAME="otro")
        values = load_project_env(self.env, deployment=True)
        self.assertEqual(values["MYSQL_USER"], "demo")
        self.assertEqual(os.environ["MYSQL_PORT"], "3307")
        self.assertEqual(values["COMPOSE_PROJECT_NAME"], "agencia-automoviles")

    def test_missing_file_value_does_not_silently_use_terminal_password(self):
        del self.values["MYSQL_PASSWORD"]
        self.write_env()
        os.environ["MYSQL_PASSWORD"] = "valor-antiguo"
        with self.assertRaisesRegex(ConfigurationError, "MYSQL_PASSWORD"):
            load_project_env(self.env)

    def test_literal_password_is_not_interpolated_from_terminal(self):
        self.values["MYSQL_PASSWORD"] = "abc${NO_EXISTE}123"
        self.write_env()
        os.environ["NO_EXISTE"] = "diferente"
        self.assertEqual(load_project_env(self.env)["MYSQL_PASSWORD"], "abc${NO_EXISTE}123")

    def test_invalid_ports_and_placeholder_values_fail_early(self):
        for value in ("0", "65536", "abc"):
            self.values["MYSQL_PORT"] = value
            self.write_env()
            with self.subTest(value=value), self.assertRaises(ConfigurationError):
                load_project_env(self.env, deployment=True)
        self.values["MYSQL_PORT"] = "3307"
        self.values["MYSQL_PASSWORD"] = "CAMBIA_SQL_POR_UNA_CLAVE_UNICA"
        self.write_env()
        with self.assertRaisesRegex(ConfigurationError, "CAMBIA"):
            load_project_env(self.env, deployment=True)

    def test_bootstrap_quotes_password_with_literal_backslash_and_apostrophe(self):
        self.values["MYSQL_PASSWORD"] = "ab'cd\\ef$gh"
        sql = bootstrap_sql(self.values)
        self.assertIn("sql_mode='NO_BACKSLASH_ESCAPES'", sql)
        self.assertIn("IDENTIFIED BY 'ab''cd\\ef$gh'", sql)
        self.assertIn("ON `agencia_demo`.* TO 'demo'@'%'", sql)
        self.assertNotIn("DROP ", sql)

    def test_passwords_travel_in_input_and_environment_not_command_arguments(self):
        self.write_env()
        values = load_project_env(self.env, deployment=True)
        result = subprocess.CompletedProcess([], 0, "", "")
        with patch("scripts.preparar_entorno.subprocess.run", return_value=result) as run:
            run_compose(["exec", "-T", "-e", "MYSQL_PWD", "database", "mysql"], values, self.env, sql=bootstrap_sql(values))
        args, kwargs = run.call_args
        for key in ("MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD"):
            self.assertNotIn(values[key], " ".join(args[0]))
        self.assertEqual(kwargs["env"]["MYSQL_PWD"], values["MYSQL_ROOT_PASSWORD"])
        self.assertIn("CREATE USER", kwargs["input"])

    def test_failed_sql_does_not_include_password_in_error(self):
        self.write_env()
        values = load_project_env(self.env, deployment=True)
        result = subprocess.CompletedProcess([], 1, "", "ERROR 1045 " + values["MYSQL_PASSWORD"])
        with patch("scripts.preparar_entorno.subprocess.run", return_value=result):
            with self.assertRaises(ConfigurationError) as error:
                run_compose([], values, self.env, sql=bootstrap_sql(values))
        self.assertIn("1045", str(error.exception))
        self.assertNotIn(values["MYSQL_PASSWORD"], str(error.exception))

    def test_ambiguous_old_catalogs_abort_before_ddl(self):
        cursor = Mock()
        cursor.fetchall.return_value = [{"TABLE_NAME": "anos"}, {"TABLE_NAME": "anios"}]
        with self.assertRaises(DataAccessError):
            normalize_years(cursor)
        self.assertEqual(cursor.execute.call_count, 1)

    def test_valid_application_account_can_continue_when_root_password_differs(self):
        self.write_env()
        database = MagicMock()
        database.session.return_value.__enter__.return_value = (Mock(), Mock())
        with patch("scripts.preparar_entorno.run_compose", side_effect=[None, RootAccessError("root anterior")]), patch(
            "scripts.preparar_entorno.MySQLDatabase", return_value=database
        ), patch("scripts.preparar_entorno.prepare_schema") as schema, patch(
            "scripts.preparar_entorno.AgencyModel"
        ), redirect_stdout(StringIO()):
            preparar(self.env)
        schema.assert_called_once_with(database)
        database.session.assert_called_once()

    def test_legacy_catalog_renames_columns_and_keeps_relationship(self):
        cursor = Mock()
        cursor.fetchall.side_effect = [
            [{"TABLE_NAME": "anos"}],
            [{"TABLE_NAME": "anos", "COLUMN_NAME": "id_ano"},
             {"TABLE_NAME": "anos", "COLUMN_NAME": "ano"},
             {"TABLE_NAME": "vehiculos", "COLUMN_NAME": "id_ano"}],
        ]
        normalize_years(cursor)
        statements = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertIn("RENAME TO `anios`", statements[-2])
        self.assertIn("RENAME COLUMN id_ano TO id_anio", statements[-1])


if __name__ == "__main__":
    unittest.main()
