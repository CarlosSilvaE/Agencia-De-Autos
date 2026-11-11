# Guion breve para la exposición

**Introducción.** Este software desktop, desarrollado en Python con PySide6 y MySQL, administra mantenimientos preventivos y correctivos. Cada intervención tiene folio, vehículo, propietario, estado, refacciones, quién entregó el automóvil y próximo servicio.

**1. MVC.** La vista (`views`) captura datos y dibuja la interfaz; los controladores (`controllers`) canalizan operaciones; el modelo (`models`) valida las reglas de negocio y ejecuta transacciones SQL. No hay API HTTP externa; en escritorio la comunicación es Python a MySQL mediante mysql-connector.

**2. Patrones adicionales.** Singleton (`DatabaseProvider`) ofrece una única instancia del proveedor de datos durante la ejecución. No mantiene abierta una conexión SQL global; cada transacción abre y cierra su propia conexión para evitar estados compartidos. Strategy (`DashboardQueryStrategy`) define cómo construir la consulta: una estrategia calcula el total y otra filtra por fecha. Ambas implementan `build` y son intercambiables sin modificar la vista.

**3. Modelo de clases.** Abrir `diagrama_clases.png`; mostrar `AgencyModel`, los controladores, el proveedor Singleton, las dos estrategias y componentes PySide6. Mencionar la herencia de `DailyDashboardStrategy` y `TotalDashboardStrategy` respecto a `DashboardQueryStrategy`.

**4. Modelo de datos.** Abrir `diagrama_bd.png`; mostrar que `vehiculos` pertenece a un cliente, que servicio guarda el folio y estado y que la relación servicios/refacciones es muchos a muchos mediante `servicio_refaccion`.

**5. Demo.** Login → cliente → marca/modelo/año → vehículo → refacción → servicio → comprobante → buscar → cambiar estado → dashboard por fecha → próximo servicio → historial de entrega → logout.

**6. Participación.** Mostrar el documento con nombres, módulos desarrollados y responsabilidades reales. No atribuir tareas no realizadas.

**Nota de evaluación.** Los tests unitarios revisan parte del comportamiento, pero se debe comprobar el flujo completo con un MySQL real y el escritorio del salón.
