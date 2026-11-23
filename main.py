from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from controllers import AgencyControllers
from models import AgencyModel, DataAccessError
from models.provider import DatabaseProvider
from views.main_window import LoginDialog, MainWindow
from views.theme import apply_theme
from configuration import ConfigurationError, load_project_env

""""
Fragmento central de arranque
"""
def main() -> int:
    application = QApplication(sys.argv)
    application.setApplicationName("Agencia de Automoviles")
    apply_theme(application)
    application.setFont(QFont("Segoe UI", 10))
    try:
        load_project_env()
        model = AgencyModel(DatabaseProvider().database)
        model.initialize(
            os.getenv("ADMIN_INITIAL_USERNAME", "admin"),
            os.getenv("ADMIN_INITIAL_PASSWORD", ""),
        )
    except (DataAccessError, ConfigurationError) as error:
        QMessageBox.critical(application.activeWindow(), "Error de base de datos", str(error))
        return 1
    
    controllers = AgencyControllers.from_model(model)
    """"
    Ventana principal solo se abre cuando el inicio de sesion ha sido aceptado
    """
    login = LoginDialog(controllers.auth)
    if login.exec() != QDialog.DialogCode.Accepted:
        return 0
    window = MainWindow(controllers, login.username)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
