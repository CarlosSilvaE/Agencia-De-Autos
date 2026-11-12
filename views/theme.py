"""Shared visual theme for PySide6 views."""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QPushButton


def apply_theme(application: QApplication) -> None:
    # Aplica los estilos generales de la aplicación Qt.
    application.setStyle("Fusion")

    palette = application.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f4f6fa"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#182230"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f8fafc"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#182230"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#eef2f6"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#344054"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#dbeafe"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#102a56"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#98a2b3"))
    application.setPalette(palette)

    application.setStyleSheet(
        """
        QWidget {
            color: #182230;
            font-size: 10pt;
        }
        QMainWindow, QDialog {
            background: #f4f6fa;
        }
        QWidget#topBar {
            background: #172b4d;
            border-radius: 10px;
        }
        QLabel#headerTitle {
            color: #ffffff;
            font-size: 18pt;
            font-weight: 700;
        }
        QLabel#headerSession {
            color: #dce5f2;
        }
        QLabel#loginTitle {
            color: #172b4d;
            font-size: 20pt;
            font-weight: 700;
        }
        QTabWidget::pane {
            background: #ffffff;
            border: 1px solid #e3e8ef;
            border-radius: 8px;
            top: -1px;
        }
        QTabBar::tab {
            background: transparent;
            color: #667085;
            padding: 11px 16px;
            border: none;
            border-bottom: 3px solid transparent;
            font-weight: 600;
        }
        QTabBar::tab:hover {
            color: #175cd3;
            background: #f1f6ff;
        }
        QTabBar::tab:selected {
            color: #175cd3;
            border-bottom: 3px solid #2e6ee6;
        }
        QPushButton {
            background: #eef2f6;
            color: #344054;
            border: 1px solid #d0d5dd;
            border-radius: 6px;
            padding: 7px 12px;
            font-weight: 600;
        }
        QPushButton:hover {
            background: #e4eaf2;
            border-color: #b8c2d1;
        }
        QPushButton:pressed {
            background: #dce3ed;
        }
        QPushButton:disabled {
            color: #98a2b3;
            background: #f2f4f7;
            border-color: #eaecf0;
        }
        QPushButton[primary="true"] {
            color: #ffffff;
            background: #2563eb;
            border-color: #2563eb;
        }
        QPushButton[primary="true"]:hover {
            background: #1d4ed8;
            border-color: #1d4ed8;
        }
        QPushButton#headerButton {
            color: #ffffff;
            background: #263d60;
            border-color: #496080;
        }
        QPushButton#headerButton:hover {
            background: #334e75;
        }
        QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
            color: #182230;
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 7px 9px;
            selection-background-color: #2563eb;
            selection-color: #ffffff;
        }
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
            border: 1px solid #528bff;
        }
        QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled,
        QSpinBox:disabled, QDoubleSpinBox:disabled {
            color: #98a2b3;
            background: #f2f4f7;
        }
        QComboBox QAbstractItemView {
            color: #182230;
            background: #ffffff;
            selection-background-color: #eaf2ff;
            selection-color: #1849a9;
            border: 1px solid #d0d5dd;
        }
        QTableWidget {
            color: #344054;
            background: #ffffff;
            alternate-background-color: #f8fafc;
            selection-background-color: #eaf2ff;
            selection-color: #1849a9;
            border: 1px solid #e3e8ef;
            border-radius: 7px;
            gridline-color: #eef2f6;
        }
        QHeaderView::section {
            color: #475467;
            background: #f2f4f7;
            border: none;
            border-bottom: 1px solid #e3e8ef;
            padding: 9px 8px;
            font-weight: 700;
        }
        QTableCornerButton::section {
            background: #f2f4f7;
            border: none;
            border-bottom: 1px solid #e3e8ef;
        }
        QCheckBox {
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        QLabel#metricTitle {
            color: #667085;
            font-size: 10pt;
            font-weight: 600;
        }
        QLabel#metricValue {
            color: #175cd3;
            font-size: 24pt;
            font-weight: 700;
        }
        QWidget#metricCard {
            background: #ffffff;
            border: 1px solid #e3e8ef;
            border-radius: 8px;
        }
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            background: #cbd5e1;
            min-height: 24px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover {
            background: #98a2b3;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent;
            height: 0;
        }
        """
    )


def set_primary_button(button: QPushButton) -> None:
    # Marca un botón como acción principal del formulario.
    button.setProperty("primary", True)
    button.style().unpolish(button)
    button.style().polish(button)
    button.update()
