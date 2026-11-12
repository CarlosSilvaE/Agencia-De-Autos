from collections import Counter
from datetime import date
from decimal import Decimal
import unittest
from unittest.mock import Mock

from models import AgencyModel
from scripts.poblar_pruebas import cargar_datos_prueba, plan_servicio


class DemoPopulationTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 11, 12)
        self.parts = [
            {"id_refaccion": index, "precio": Decimal("100.50") + index}
            for index in range(1, 16)
        ]
        self.plans = [plan_servicio(index, self.today, self.parts) for index in range(1, 101)]

    def test_default_population_covers_states_dates_and_unique_folios(self):
        self.assertEqual(Counter(plan["estado"] for plan in self.plans), {
            "En espera": 34, "En proceso": 33, "Finalizado": 33,
        })
        self.assertEqual(sum(plan["fecha_ingreso"].date() == self.today for plan in self.plans), 12)
        self.assertEqual(sum(plan["fecha_ingreso"].date() < self.today for plan in self.plans), 88)
        self.assertEqual(len({plan["folio"] for plan in self.plans}), 100)
        self.assertTrue(all(len(plan["folio"]) <= 30 for plan in self.plans))
        self.assertEqual({plan["tipoServicio"] for plan in self.plans}, {"Preventivo", "Correctivo"})

    def test_parts_cover_empty_single_and_multiple_without_duplicate_keys(self):
        self.assertEqual({len(plan["refacciones"]) for plan in self.plans}, {0, 1, 2, 3})
        for plan in self.plans:
            with self.subTest(folio=plan["folio"]):
                parts = plan["refacciones"]
                self.assertEqual(len(parts), len({part["idRefaccion"] for part in parts}))
                self.assertTrue(all(part["cantidad"] > 0 for part in parts))
                subtotal = sum((part["cantidad"] * part["precioUnitario"] for part in parts), Decimal("0"))
                self.assertGreater(plan["costo"], subtotal)

    def test_upcoming_services_cover_overdue_today_and_future(self):
        appointments = [plan["proximoServicio"] for plan in self.plans if plan["proximoServicio"]]
        self.assertEqual(len(appointments), 50)
        dates = [appointment["fechaProgramada"] for appointment in appointments]
        self.assertTrue(any(day < self.today for day in dates))
        self.assertIn(self.today, dates)
        self.assertTrue(any(day > self.today for day in dates))

    def test_generated_vehicle_identifiers_match_current_vin_validation(self):
        vins = [f"PRBCARABC{index:08d}" for index in range(1, 31)]
        self.assertEqual(len(set(vins)), 30)
        for vin in vins:
            self.assertEqual(AgencyModel._validate_vin(vin), vin)

    def test_invalid_amount_fails_without_connecting(self):
        for count in (0, -1, 1001):
            database = Mock()
            with self.subTest(count=count), self.assertRaises(ValueError):
                cargar_datos_prueba(database, count)
            database.session.assert_not_called()


if __name__ == "__main__":
    unittest.main()
