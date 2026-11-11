from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from controllers import AgencyControllers
from models import AgencyModel, DataAccessError
from models.provider import DatabaseProvider
from views.main_window import LoginDialog, MainWindow
from views.theme import apply_theme


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    application = QApplication(sys.argv)
    application.setApplicationName("Agencia de Automoviles")
    apply_theme(application)
    application.setFont(QFont("Segoe UI", 10))
    model = AgencyModel(DatabaseProvider().database)
    try:
        model.initialize(
            os.getenv("ADMIN_INITIAL_USERNAME", "admin"),
            os.getenv("ADMIN_INITIAL_PASSWORD", ""),
        )
    except DataAccessError as error:
        QMessageBox.critical(application.activeWindow(), "Error de base de datos", str(error))
        return 1
    controllers = AgencyControllers.from_model(model)
    login = LoginDialog(controllers.auth)
    if login.exec() != QDialog.DialogCode.Accepted:
        return 0
    window = MainWindow(controllers, login.username)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
