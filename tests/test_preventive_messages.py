import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from views.forms import PREVENTIVE_TEMPLATES, ServiceDialog


class PreventiveMessageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def dialog(self, record=None):
        dialog = ServiceDialog([], [], record)
        self.addCleanup(dialog.close)
        return dialog

    def test_new_preventive_has_default_and_selectable_messages(self):
        dialog = self.dialog()
        self.assertEqual(dialog.description.toPlainText(), PREVENTIVE_TEMPLATES[0][1])
        dialog.preventive_message.setCurrentIndex(2)
        self.assertEqual(dialog.description.toPlainText(), PREVENTIVE_TEMPLATES[1][1])

    def test_corrective_starts_empty_and_keeps_manual_draft_when_switching(self):
        dialog = self.dialog()
        dialog.description.setPlainText("Mi texto preventivo")
        dialog.kind.setCurrentText("Correctivo")
        self.assertEqual(dialog.description.toPlainText(), "")
        self.assertTrue(dialog.preventive_message.isHidden())
        dialog.description.setPlainText("Reparar fuga detectada")
        dialog.kind.setCurrentText("Preventivo")
        self.assertEqual(dialog.description.toPlainText(), "Mi texto preventivo")
        dialog.kind.setCurrentText("Correctivo")
        self.assertEqual(dialog.description.toPlainText(), "Reparar fuga detectada")

    def test_existing_description_is_not_replaced_on_open(self):
        for kind in ("Preventivo", "Correctivo"):
            with self.subTest(kind=kind):
                dialog = self.dialog({"tipo_servicio": kind, "descripcion": "Trabajo ya registrado", "costo": 1500})
                self.assertEqual(dialog.description.toPlainText(), "Trabajo ya registrado")

    def test_typing_custom_preventive_text_marks_it_as_custom(self):
        dialog = self.dialog()
        dialog.description.setPlainText("Revision solicitada por el cliente")
        self.assertEqual(dialog.preventive_message.currentIndex(), 0)
        dialog.preventive_message.setCurrentIndex(1)
        self.assertEqual(dialog.description.toPlainText(), PREVENTIVE_TEMPLATES[0][1])


if __name__ == "__main__":
    unittest.main()
