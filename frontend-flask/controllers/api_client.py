import requests
from flask import current_app


def api_request(method, path, **kwargs):
    response = requests.request(
        method,
        f"{current_app.config['BACKEND_URL']}{path}",
        timeout=15,
        **kwargs,
    )
    if not response.ok:
        try:
            message = response.json().get("message", "La API rechazó la operación.")
        except ValueError:
            message = "La API rechazó la operación."
        raise ValueError(message)
    if response.status_code == 204:
        return None
    return response.json()
