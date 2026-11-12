# Guion breve para la exposicion

**Introduccion.** Este software desktop, desarrollado en Python con PySide6 y MySQL, administra mantenimientos preventivos y correctivos. Cada intervencion tiene folio, vehiculo, propietario, estado, refacciones, quien entrego el automovil y proximo servicio.

**1. MVC.** La vista (`views`) captura datos y dibuja la interfaz; los controladores (`controllers`) canalizan operaciones; el modelo (`models`) valida las reglas de negocio y ejecuta transacciones SQL. No hay API HTTP externa; en escritorio la comunicacion es Python a MySQL mediante mysql-connector.

**2. Patrones adicionales.** Singleton (`DatabaseProvider`) ofrece una unica instancia del proveedor de datos durante la ejecucion. No mantiene abierta una conexion SQL global; cada transaccion abre y cierra su propia conexion para evitar estados compartidos. Strategy (`DashboardQueryStrategy`) define como construir la consulta: una estrategia calcula el total y otra filtra por fecha. Ambas implementan `build` y son intercambiables sin modificar la vista.

**3. Modelo de clases.** Abrir `diagrama_clases.png`; mostrar `AgencyModel`, los controladores, el proveedor Singleton, las dos estrategias y componentes PySide6. Mencionar la herencia de `DailyDashboardStrategy` y `TotalDashboardStrategy` respecto a `DashboardQueryStrategy`.

**4. Modelo de datos.** Abrir `diagrama_bd.png`; mostrar que `vehiculos` pertenece a un cliente, que servicio guarda el folio y estado y que la relacion servicios/refacciones es muchos a muchos mediante `servicio_refaccion`.

**5. Demo.** Login → cliente → marca/modelo/anio → vehiculo → refaccion → servicio → comprobante → buscar → cambiar estado → dashboard por fecha → proximo servicio → historial de entrega → logout.

**6. Participacion.** Mostrar el documento con nombres, modulos desarrollados y responsabilidades reales. No atribuir tareas no realizadas.

**Nota de evaluacion.** Los tests unitarios revisan parte del comportamiento, pero se debe comprobar el flujo completo con un MySQL real y el escritorio del salon.
