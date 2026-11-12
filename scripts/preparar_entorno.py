"""Prepara MySQL con Docker y el .env del proyecto en Windows, Linux o macOS."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configuration import ConfigurationError, load_project_env
from models import AgencyModel, DataAccessError
from models.database import MySQLDatabase
from models.schema import prepare_schema


class RootAccessError(ConfigurationError):
    pass


def bootstrap_sql(values: dict[str, str]) -> str:
    def literal(value):
        return "'" + value.replace("'", "''") + "'"

    account = literal(values["MYSQL_USER"]) + "@'%'"
    password = literal(values["MYSQL_PASSWORD"])
    database = "`" + values["MYSQL_DATABASE"] + "`"
    return (
        "SET SESSION sql_mode='NO_BACKSLASH_ESCAPES';\n"
        f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4;\n"
        f"CREATE USER IF NOT EXISTS {account} IDENTIFIED BY {password};\n"
        f"ALTER USER {account} IDENTIFIED BY {password};\n"
        f"GRANT ALL PRIVILEGES ON {database}.* TO {account};\n"
    )


def run_compose(args, values, env_file: Path, *, sql: str | None = None):
    environment = os.environ.copy()
    environment.update(values)
    environment.pop("COMPOSE_FILE", None)
    environment.pop("COMPOSE_PROFILES", None)
    if sql is not None:
        environment["MYSQL_PWD"] = values["MYSQL_ROOT_PASSWORD"]
    command = [
        "docker", "compose", "--project-directory", str(ROOT),
        "--env-file", str(env_file), "--file", str(ROOT / "docker-compose.yml"),
        "--project-name", values["COMPOSE_PROJECT_NAME"], *args,
    ]
    try:
        result = subprocess.run(
            command, input=sql, text=True, encoding="utf-8", errors="replace",
            capture_output=True, env=environment, cwd=ROOT, timeout=240,
        )
    except FileNotFoundError as error:
        raise ConfigurationError("Instala Docker Desktop o Docker Engine con Docker Compose.") from error
    except subprocess.TimeoutExpired as error:
        raise ConfigurationError("Docker no termino a tiempo. Revisa que el motor este iniciado.") from error
    if result.returncode:
        if sql is not None:
            code = re.search(r"ERROR\s+(\d+)", result.stderr)
            suffix = f" (MySQL {code.group(1)})" if code else ""
            if code and code.group(1) == "1045":
                raise RootAccessError(
                    "No se pudo sincronizar la cuenta MySQL" + suffix + ". "
                    "MYSQL_ROOT_PASSWORD debe coincidir con la clave root del volumen existente. "
                    "Recrear el contenedor no cambia esa clave."
                )
            raise ConfigurationError(
                "No se pudo sincronizar la cuenta MySQL" + suffix + ". "
                "Comprueba que el contenedor este iniciado, los valores de .env y los permisos de root."
            )
        details = result.stderr or result.stdout
        for key, value in values.items():
            if "PASSWORD" in key and value:
                details = details.replace(value, "[oculto]")
        raise ConfigurationError("Docker no pudo iniciar MySQL: " + details.strip())
    return result


def preparar(env_file: Path | str = ROOT / ".env") -> None:
    env_file = Path(env_file).resolve()
    values = load_project_env(env_file, deployment=True)
    print("1/4 Iniciando MySQL y esperando disponibilidad...", flush=True)
    run_compose(["up", "-d", "--wait", "--wait-timeout", "120", "database"], values, env_file)
    print("2/4 Sincronizando la cuenta de conexion con .env...", flush=True)
    database = MySQLDatabase()
    try:
        run_compose([
            "exec", "-T", "-e", "MYSQL_PWD", "database", "mysql",
            "--user=root", "--default-character-set=utf8mb4", "--batch", "--silent",
        ], values, env_file, sql=bootstrap_sql(values))
    except RootAccessError as error:
        # Un volumen anterior puede tener otra clave root, aunque la cuenta de la
        # aplicacion ya coincida. En ese caso no se necesita cambiar esa cuenta.
        try:
            with database.session() as (_, cursor):
                cursor.execute("SELECT 1 AS conectado")
                cursor.fetchone()
        except DataAccessError:
            raise error
        print("La cuenta de .env ya funciona; se continua sin cambiar la cuenta root.", flush=True)
    print("3/4 Preparando esquema, migraciones y catalogos...", flush=True)
    prepare_schema(database)
    print("4/4 Comprobando la aplicacion y el administrador inicial...", flush=True)
    model = AgencyModel(database)
    model.initialize(values["ADMIN_INITIAL_USERNAME"], values["ADMIN_INITIAL_PASSWORD"])
    model.list_services()
    model.customer_vehicle_data()
    print("Entorno preparado. Inicia la aplicacion con: python main.py", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env", help="Archivo de configuracion a usar.")
    args = parser.parse_args()
    try:
        preparar(args.env_file)
    except (ConfigurationError, DataAccessError, OSError) as error:
        print(f"No se pudo preparar el entorno: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
