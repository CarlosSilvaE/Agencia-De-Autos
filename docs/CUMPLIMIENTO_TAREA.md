# Matriz de cumplimiento — main e2ef677

Evidencia estática; la demostración con MySQL y la evaluación son independientes.

| Requisito | Evidencia |
|---|---|
| POO y modelo de clases | models/controllers/views; [UML](UML/UML_Clases_Completo.svg) y [fuente](UML/UML_Clases_Completo.puml) |
| MVC y comunicación | Páginas → controladores → AgencyModel → MySQLDatabase |
| MySQL y modelo de datos | database/init.sql; diagrama relacional pendiente de la persona encargada |
| Login | LoginDialog, AuthController, authenticate; hash PBKDF2 |
| CRUD de catálogos y marca/modelo/año | CatalogsPage y métodos de catálogo; bajas lógicas, tabla anios |
| Navegación y cierre | MainWindow, logout, sesiones independientes con cierre |
| Dos patrones | DatabaseProvider Singleton; DashboardQueryStrategy y variantes |
| Servicios | ServiceDialog, ServiceController, create/update/delete_service; inventario transaccional |
| Estados y consultas | En espera, En proceso, Finalizado; búsqueda por folio/propietario |
| Comprobante | ServiceReceipt y ReceiptDialog.save_pdf; mano de obra, piezas y total |
| Próximos servicios | ServiceDialog y UpcomingPage; búsqueda/listado |
| Dashboard | StatusBarChart y consultas total/diaria |
| Persona que entrega | Recepción opcional e historial; confirmar con el profesor si debe ser obligatoria |
| Refacciones N:M | servicio_refaccion y _save_service_relations |
| Participación y GitHub | Aportar commits/PR y responsabilidades reales, no inferir autorías |

Validación manual pendiente: login, CRUD, VIN manual/automático, tipos de servicio,
buscador de piezas, importes, PDF, próximos servicios, dashboard, recepción,
consistencia del inventario al editar/eliminar y salida. Usar registros propios.
Completar Entrega_y_responsabilidades.docx con nombres y evidencias reales.
Consultar [el guion](GUION_EXPOSICION.md) y [el despliegue](DESPLIEGUE.md).
