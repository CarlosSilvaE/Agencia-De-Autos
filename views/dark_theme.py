
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

DARK_CHART_PALETTE: dict[str, str] = {
    "canvas_bg": "#111827",
    "title": "#f8fafc",
    "label": "#cbd5e1",
    "track_bg": "#1e293b",
    "value": "#e2e8f0",
}

LIGHT_CHART_PALETTE: dict[str, str] = {
    "canvas_bg": "#f8fbff",
    "title": "#203451",
    "label": "#344054",
    "track_bg": "#e6ebf2",
    "value": "#25364d",
}

DARK_STYLESHEET = """
QWidget {
    color: #e5e7eb;
    font-size: 10pt;
}
QMainWindow, QDialog {
    background: #0f172a;
}
QWidget#topBar {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
}
QWidget#themeBar {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
}
QLabel#headerTitle {
    color: #f9fafb;
    font-size: 18pt;
    font-weight: 700;
}
QLabel#headerSession {
    color: #9ca3af;
}
QLabel#loginTitle {
    color: #f9fafb;
    font-size: 20pt;
    font-weight: 700;
}
QTabWidget::pane {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    color: #9ca3af;
    padding: 11px 16px;
    border: none;
    border-bottom: 3px solid transparent;
    font-weight: 600;
}
QTabBar::tab:hover {
    color: #c4b5fd;
    background: #1e1b4b;
}
QTabBar::tab:selected {
    color: #a78bfa;
    border-bottom: 3px solid #7c3aed;
}
QPushButton {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 7px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background: #273549;
    border-color: #475569;
}
QPushButton:pressed {
    background: #162032;
}
QPushButton:disabled {
    color: #64748b;
    background: #111827;
    border-color: #1e293b;
}
QPushButton[primary="true"] {
    color: #ffffff;
    background: #7c3aed;
    border-color: #7c3aed;
}
QPushButton[primary="true"]:hover {
    background: #6d28d9;
    border-color: #6d28d9;
}
QPushButton#headerButton {
    color: #f8fafc;
    background: #1f2937;
    border-color: #374151;
}
QPushButton#headerButton:hover {
    background: #374151;
}
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    color: #f1f5f9;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 7px 9px;
    selection-background-color: #7c3aed;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border: 1px solid #8b5cf6;
}
QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled,
QSpinBox:disabled, QDoubleSpinBox:disabled {
    color: #64748b;
    background: #111827;
}
QComboBox QAbstractItemView {
    color: #f1f5f9;
    background: #1e293b;
    selection-background-color: #4c1d95;
    selection-color: #f5f3ff;
    border: 1px solid #334155;
}
QTableWidget {
    color: #e2e8f0;
    background: #111827;
    alternate-background-color: #162032;
    selection-background-color: #4c1d95;
    selection-color: #f5f3ff;
    border: 1px solid #1f2937;
    border-radius: 7px;
    gridline-color: #1e293b;
}
QHeaderView::section {
    color: #cbd5e1;
    background: #1e293b;
    border: none;
    border-bottom: 1px solid #334155;
    padding: 9px 8px;
    font-weight: 700;
}
QTableCornerButton::section {
    background: #1e293b;
    border: none;
    border-bottom: 1px solid #334155;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QSlider::groove:horizontal {
    height: 8px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
}
QSlider::sub-page:horizontal {
    background: #7c3aed;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background: #f8fafc;
    border: 2px solid #7c3aed;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 9px;
}
QLabel#metricTitle {
    color: #9ca3af;
    font-size: 10pt;
    font-weight: 600;
}
QLabel#metricValue {
    color: #a78bfa;
    font-size: 24pt;
    font-weight: 700;
}
QWidget#metricCard {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0;
}
"""


def repolish_tree(widget: QWidget) -> None:
    """Fuerza a Qt a reaplicar la hoja de estilos en el arbol de widgets."""
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()
    for child in widget.findChildren(QWidget):
        cstyle = child.style()
        cstyle.unpolish(child)
        cstyle.polish(child)
        child.update()


def apply_dark_theme(application: QApplication) -> None:
    """Aplica la paleta y hoja de estilos oscura a la aplicacion PySide6."""
    application.setStyle("Fusion")

    palette = application.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0f172a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#162032"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1e293b"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e2e8f0"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#4c1d95"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#f5f3ff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#64748b"))
    application.setPalette(palette)
    application.setStyleSheet("")
    application.setStyleSheet(DARK_STYLESHEET)
    for top in application.topLevelWidgets():
        repolish_tree(top)