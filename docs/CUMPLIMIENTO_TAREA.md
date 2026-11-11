# Matriz de cumplimiento — Agencia de Automóviles (Parcial 2)

**Alcance:** se omite GitHub por indicación del solicitante. Esta matriz identifica implementaciones revisables en el código. Los tests automatizados no sustituyen la demostración manual de la GUI conectada a MySQL.

## Requisitos generales

| Requisito | Evidencia en esta versión | Prueba durante exposición |
|---|---|---|
| Orientado a objetos | `AgencyModel`, `MySQLDatabase`, `DatabaseProvider`, controladores, diálogos, `ServiceReceipt`, `ReceiptPart` y `StatusBarChart` son clases; Strategy usa herencia y polimorfismo | Explicar las responsabilidades de cada clase y mostrar `diagrama_clases.png` |
| MVC | `models/`, `controllers/`, `views/`; `main.py` construye dependencias | Crear un servicio y explicar el flujo Vista → Controlador → Modelo → MySQL |
| Base de datos | MySQL 8.4 y `database/init.sql` | Mostrar esquema y datos registrados en SQL |
| Modelo de clases | `docs/diagrama_clases.png` y su fuente editable `.dot` | Describir asociaciones, Strategy y Singleton |
| Modelo de datos | `docs/diagrama_bd.png`, `.dot` y `database/init.sql` | Explicar `servicio_refaccion` y claves foráneas |
| Comunicación frontend/backend | PySide6 → controladores → modelo → MySQL, sin API HTTP independiente | Guardar registro, volver a abrir y comprobar persistencia |

## Requisitos operacionales

| Ítem | Puntos | Evidencia / archivo |
|---|---:|---|
| Login administrativo | 5 | `LoginDialog`, `AuthController.login`, `AgencyModel.authenticate` con hash PBKDF2 |
| CRUD catálogos | 5 | `CatalogsPage` y `AgencyModel.save_catalog_item/delete_catalog_item` |
| Menú y cierre seguro | 5 | Pestañas en `MainWindow`; `logout`, `closeEvent`, `AuthController.logout`; conexiones cerradas por `MySQLDatabase.session` |
| Dos patrones de diseño | 10 | **Singleton**: `models/provider.py`; **Strategy**: `models/dashboard_strategy.py`; la fábrica de controladores se conserva como mecanismo adicional |
| Registro/edición de servicios + comprobante | 10 | `ServiceDialog`; `ServiceController`; `AgencyModel.create_service/update_service`; `ServicesPage.receipt` y `ReceiptDialog.save_pdf` |
| Consultas por folio/propietario y estados | 10 | `ServicesPage`, `list_services`, `update_service_status`, `delete_service` |
| CRUD marca, modelo y año | 10 | `CatalogsPage`, `CatalogItemDialog`, `list_catalog`, `save_catalog_item` |
| Próximo servicio y búsquedas | 10 | `ServiceDialog`, `AgencyModel.list_upcoming` y `UpcomingPage` |
| Dashboard: gráficas total o por fecha | 10 | `StatusBarChart`, `DashboardPage`, estrategias `TotalDashboardStrategy` y `DailyDashboardStrategy` |
| Quién entregó y relación N:M de refacciones | 10 | `entregas`, `servicio_refaccion`, `AgencyModel.delivery_history`, `ServicesPage.show_delivery_history` |

**Importante:** los 85 puntos operacionales excluyen el punto de GitHub (5). Las penalizaciones generales son independientes. La acreditación depende de la revisión del profesor.

## Prueba manual recomendada (con MySQL real)

1. Ejecutar `docker compose up -d`, instalar dependencias, iniciar `python main.py`.
2. Comprobar login erróneo y correcto. Confirmar que `Cerrar sesión` cierra ventana.
3. Crear marca, modelo asociado y año. Editarlos sin cambiar valores; deben guardar sin error.
4. Crear cliente y vehículo; comprobar modelo asociado a marca.
5. Crear refacción con inventario de 4 unidades.
6. Crear servicio preventivo, con una refacción de cantidad 2, persona que entrega y próximo servicio.
7. Buscar por folio y propietario; generar y abrir el comprobante PDF.
8. Abrir Historial recepción y comprobar la persona entregadora. Editar su nombre y corroborar que haya dos entradas.
9. Cambiar el estado a 'En proceso' y actualizar el dashboard (Total y Por fecha) para verificar valores y barras.
10. Revisar próximos servicios, editar el servicio sin cambios, después eliminarlo y verificar restitución de inventario.
11. Confirmar que las operaciones con datos inválidos muestran aviso sin cerrar inesperadamente la app.
12. Cerrar sesión y verificar que la aplicación finaliza y se liberan las conexiones de MySQL.

## Lo que debe aportar el equipo

- Nombre completo de cada integrante, responsabilidades reales y evidencias de su participación, en `Entrega_y_responsabilidades.docx`.
- Capturas reales de login, servicio, comprobante y dashboard (no se incluyen capturas inventadas).
- Validación práctica en el Windows/MySQL donde se presentará la aplicación.
