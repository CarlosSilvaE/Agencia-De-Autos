"""Grafica real, responsive y sin dependencias extra usando QPainter/Qt."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class StatusBarChart(QWidget):
    STATES = (
        ("En espera", "#E5A53D"),
        ("En proceso", "#3973C6"),
        ("Finalizado", "#299A73"),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._counts: dict[str, int] = {}
        self.setMinimumHeight(215)
        self.setAccessibleName("Grafica de barras de servicios por estado")

    def set_counts(self, counts: dict[str, int]) -> None:
        self._counts = {name: max(0, int(counts.get(name, 0))) for name, _ in self.STATES}
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w = float(self.width())
        h = float(self.height())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f8fbff"))
        painter.drawRoundedRect(QRectF(2, 2, w - 4, h - 4), 10, 10)
        title_font = QFont(self.font())
        title_font.setBold(True)
        title_font.setPointSize(10)
        painter.setFont(title_font)
        painter.setPen(QColor("#203451"))
        painter.drawText(QRectF(20, 12, w - 40, 30), Qt.AlignmentFlag.AlignLeft, "Servicios por estado")
        label_width = 111.0
        right_gap = 80.0
        chart_left = 20.0 + label_width
        chart_width = max(1.0, w - chart_left - right_gap)
        max_count = max((self._counts.get(name, 0) for name, _ in self.STATES), default=0)
        bar_height = 24.0
        region_height = max(48.0, (h - 60.0) / len(self.STATES))
        normal_font = QFont(self.font())
        normal_font.setBold(False)
        normal_font.setPointSize(9)
        painter.setFont(normal_font)
        for idx, (name, color) in enumerate(self.STATES):
            count = self._counts.get(name, 0)
            top = 55.0 + idx * region_height
            painter.setPen(QColor("#344054"))
            painter.drawText(QRectF(14, top, label_width, bar_height), Qt.AlignmentFlag.AlignVCenter, name)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#e6ebf2"))
            painter.drawRoundedRect(QRectF(chart_left, top, chart_width, bar_height), 6, 6)
            if count and max_count:
                filled = chart_width * (count / max_count)
                painter.setBrush(QColor(color))
                painter.drawRoundedRect(QRectF(chart_left, top, filled, bar_height), 6, 6)
            painter.setPen(QPen(QColor("#25364d")))
            painter.drawText(
                QRectF(chart_left + chart_width + 9, top, right_gap - 18, bar_height),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                str(count),
            )
        painter.end()
