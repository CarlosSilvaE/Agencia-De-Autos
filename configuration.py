"""Configuracion comun para la aplicacion y la preparacion de Docker."""
from __future__ import annotations

import os
from pathlib import Path
import re

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent
CONFIG_KEYS = (
    "MYSQL_HOST", "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD",
    "MYSQL_ROOT_PASSWORD", "ADMIN_INITIAL_USERNAME", "ADMIN_INITIAL_PASSWORD", "COMPOSE_PROJECT_NAME",
)


class ConfigurationError(ValueError):
    pass


def load_project_env(path: Path | str = ROOT / ".env", *, deployment: bool = False) -> dict[str, str]:
    path = Path(path).resolve()
    if not path.is_file():
        raise ConfigurationError("No existe .env. Copia .env.example a .env y completa sus valores.")
    parsed = dotenv_values(path, interpolate=False, encoding="utf-8-sig")
    values = {key: parsed[key] for key in CONFIG_KEYS if parsed.get(key) is not None}
    required = list(CONFIG_KEYS[:5])
    if deployment:
        required.extend(("MYSQL_ROOT_PASSWORD", "ADMIN_INITIAL_USERNAME", "ADMIN_INITIAL_PASSWORD"))
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise ConfigurationError("Completa las variables de .env: " + ", ".join(missing))
    try:
        if not 1 <= int(values["MYSQL_PORT"]) <= 65535:
            raise ValueError()
    except ValueError as error:
        raise ConfigurationError("MYSQL_PORT debe ser un numero entre 1 y 65535.") from error
    values["MYSQL_PORT"] = str(int(values["MYSQL_PORT"]))
    if deployment:
        if any(values[key].startswith("CAMBIA_") for key in required):
            raise ConfigurationError("Sustituye los valores CAMBIA_* de .env antes de preparar la base.")
        if values["MYSQL_HOST"] not in ("127.0.0.1", "localhost"):
            raise ConfigurationError("El despliegue Docker local requiere MYSQL_HOST=127.0.0.1 o localhost.")
        if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", values["MYSQL_DATABASE"]):
            raise ConfigurationError("MYSQL_DATABASE debe usar letras, numeros o guion bajo (maximo 64).")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", values["MYSQL_USER"]) or values["MYSQL_USER"].lower() == "root":
            raise ConfigurationError("MYSQL_USER debe ser una cuenta propia de la aplicacion, distinta de root.")
        if len(values["ADMIN_INITIAL_PASSWORD"]) < 8:
            raise ConfigurationError("ADMIN_INITIAL_PASSWORD debe tener al menos 8 caracteres.")
    project = values.get("COMPOSE_PROJECT_NAME", "agencia-automoviles")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", project):
        raise ConfigurationError("COMPOSE_PROJECT_NAME debe usar minusculas, numeros, guiones o guion bajo.")
    values["COMPOSE_PROJECT_NAME"] = project
    # Un solo archivo, con prioridad sobre variables antiguas de la terminal.
    for key in CONFIG_KEYS:
        if key not in values:
            os.environ.pop(key, None)
    os.environ.update(values)
    return values
