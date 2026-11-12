from __future__ import annotations

import unittest
from unittest.mock import Mock

from controllers import AgencyControllers
from models import AgencyModel


class MvcFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = Mock(spec=AgencyModel)
        self.controllers = AgencyControllers.from_model(self.model)

    def test_authentication_controller_delegates_to_model(self) -> None:
        self.model.authenticate.return_value = "admin"

        self.assertEqual(self.controllers.auth.login("admin", "secret"), "admin")
        self.model.authenticate.assert_called_once_with("admin", "secret")

    def test_service_controller_delegates_queries_and_updates(self) -> None:
        self.model.list_services.return_value = [{"folio": "SRV-1"}]
        self.model.service_options.return_value = ([{"id_vehiculo": 1}], [])

        self.assertEqual(self.controllers.services.list("SRV-1")[0]["folio"], "SRV-1")
        self.assertEqual(
            self.controllers.services.options(),
            ([{"id_vehiculo": 1}], []),
        )
        self.controllers.services.change_status("SRV-1", "Finalizado")
        self.controllers.services.delete("SRV-1")

        self.model.list_services.assert_called_once_with("SRV-1", "")
        self.model.update_service_status.assert_called_once_with("SRV-1", "Finalizado")
        self.model.delete_service.assert_called_once_with("SRV-1")

    def test_catalog_controller_delegates_mutations(self) -> None:
        self.controllers.catalogs.save("marcas", {"nombre": "Toyota"})
        self.controllers.catalogs.save("marcas", {"nombre": "Honda"}, 3)
        self.controllers.catalogs.delete("marcas", 3)

        self.assertEqual(
            self.model.save_catalog_item.call_args_list[0].args,
            ("marcas", {"nombre": "Toyota"}, None),
        )
        self.model.save_catalog_item.assert_any_call(
            "marcas", {"nombre": "Honda"}, 3
        )
        self.model.delete_catalog_item.assert_called_once_with("marcas", 3)

    def test_password_hash_round_trip_and_rejects_wrong_password(self) -> None:
        password_hash = AgencyModel.hash_password("correct horse battery staple")

        self.assertTrue(
            AgencyModel.verify_password("correct horse battery staple", password_hash)
        )
        self.assertFalse(AgencyModel.verify_password("incorrect", password_hash))
        self.assertFalse(AgencyModel.verify_password("incorrect", "not-base64"))

    def test_service_validation_and_catalog_allowlist(self) -> None:
        payload = {
            "descripcion": "Cambio de aceite",
            "tipoServicio": "Preventivo",
            "estado": "En espera",
            "costo": 100,
            "cliente": {},
            "vehiculo": {},
            "entrega": {},
        }
        AgencyModel._validate_service(payload)

        with self.assertRaises(ValueError):
            AgencyModel._catalog_definition("marcas; DROP TABLE administradores")
        with self.assertRaises(ValueError):
            AgencyModel._validate_service({**payload, "estado": "Desconocido"})


if __name__ == "__main__":
    unittest.main()
