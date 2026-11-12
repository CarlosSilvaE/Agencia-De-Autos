# Diagnóstico del proyecto — 11 de noviembre de 2026

Revisión estática del arranque, modelos, controladores, formularios, páginas,
gráfica, esquema SQL, Compose, generador y pruebas. No se modificaron datos
existentes ni se ejecutó la aplicación contra MySQL. Los hallazgos sobre datos
son posibilidades derivadas del código; no un inventario de la base instalada.

## Cambios implementados

- Folio automático de 29 caracteres, compatible con `VARCHAR(30)`; validación
  de longitud para folios manuales y normalización de espacios exteriores.
- Eliminación física de administradores activos o inactivos con confirmación
  explícita y transacción. Se conserva la protección del último activo.
  La desactivación sigue disponible en Editar mediante la casilla Activo.
- VIN manual de 17 caracteres ASCII alfanuméricos, sin I, N ni Q, según
  la regla solicitada. Se convierte a mayúsculas y se quitan espacios exteriores.
  Si se deja vacío, se genera automáticamente. Validación en las dos rutas del modelo que guardan vehículos.
- Nuevos vehículos DEMO reciben un VIN que cumple la regla. La semilla no
  reemplaza vehículos existentes; los VIN anteriores quedan intactos.
- La conexión se cierra incluso si falla la creación o el cierre del cursor.
- Edición y eliminación de servicios bloquean su fila con `FOR UPDATE` para
  serializar esas operaciones sobre un mismo servicio. Falta probar concurrencia
  real con MySQL; pueden seguir existiendo interbloqueos entre servicios distintos.

No se cambió el esquema. No hace falta migrar la base para aplicar estos cambios.
La validación del VIN vive en la aplicación; SQL directo puede eludirla.

## Arquitectura y requisitos

Se conserva MVC: `views/` recoge y presenta datos, los controladores delegan y
`AgencyModel` concentra negocio y SQL. `MySQLDatabase` administra las sesiones.
Singleton comparte el proveedor, no conexiones; Strategy construye las consultas
total y diaria. `ServiceReceipt` y `ReceiptPart` construyen el comprobante.

Están implementados login, navegación, cierre de sesión, catálogos, clientes,
vehículos, administradores, servicios con tres estados, búsquedas, comprobante
imprimible/PDF, recepción con historial, próximos servicios y dashboard.
El esquema contiene claves foráneas y la tabla N:M `servicio_refaccion`.
Existen diagramas de clases y de datos y una matriz de cumplimiento.
La presencia en código no sustituye la demostración de cada requisito en MySQL.

El alta de servicios valida, guarda cliente y vehículo, inserta servicio y guarda
relaciones en una transacción. La edición restituye inventario previo y descuenta
el nuevo. La eliminación restituye inventario y borra relaciones antes del servicio.
Las cantidades se descuentan mediante un UPDATE condicionado a existencia suficiente.

Compose ejecuta MySQL 8.4 con volumen persistente, puerto local configurable y
script de inicialización. Editar `init.sql` no modifica un volumen inicializado.
En el diagnóstico anterior el contenedor estaba healthy y la configuración pasó
la validación de Compose; no se repitió una integración SQL en esta revisión.

## Pendientes ordenados por prioridad

| Prioridad | Hallazgo y consecuencia | Ubicación / siguiente acción |
|---|---|---|
| Alta | VIN antiguos vacíos o ficticios pueden impedir guardar vehículos y crear o editar sus servicios. El formulario de servicio reutiliza el VIN almacenado. | Corregir el VIN real desde Clientes y vehículos; no inventar ni reemplazar automáticamente los existentes. |
| Alta | El formulario de servicios solo recibe refacciones activas. Al editar puede omitir una refacción histórica desactivada y quitarla al guardar. | `service_options`, `ServiceDialog`, `_save_service_relations`: conservar explícitamente las relaciones históricas y definir si se permiten cambios de cantidad. |
| Alta | Editar un servicio cuyo vehículo o propietario está desactivado puede seleccionar otro vehículo porque el original no aparece en el combo. | `list_vehicles`, `set_combo_id`, `ServiceDialog`: incluir el registro histórico o bloquear el guardado con mensaje, sin seleccionar un sustituto. |
| Media | Una cuenta eliminada o desactivada en otra sesión conserva acceso en una ventana ya autenticada. Los controladores no vuelven a verificar la identidad. | Definir y aplicar invalidación de sesiones; actualmente el login se valida solo al entrar. |
| Media | Editar servicios actualiza también cliente y vehículo compartidos. Los datos presentados por otros servicios y sus comprobantes pueden cambiar. | `_save_client`, `_save_vehicle`, `list_services`: decidir si el comprobante debe representar datos actuales o una copia histórica. |
| Media | El modelo no valida completamente números de catálogo: por ejemplo precio negativo, valores no finitos o años fuera de rango. Los controles Qt limitan algunos casos, pero SQL/modelo no son equivalentes. | `save_catalog_item`, `_validate_service`: reforzar las reglas de negocio independientemente de la interfaz. |
| Media | Se pueden desactivar marcas y años usados por vehículos; las FK no impiden una baja lógica. Los combos pueden dejar de representar los valores históricos. | `delete_catalog_item`, `VehicleDialog`: definir política coherente para dependencias activas e históricas. |
| Media | Operaciones MySQL y hashes se ejecutan en el hilo de la interfaz; una conexión lenta puede congelarla durante el timeout. | Páginas y login: evaluar trabajo en segundo plano preservando conexiones independientes. |
| Baja | `servicios.fecha_programada` se consulta pero no se guarda desde el formulario; el próximo mantenimiento se almacena separadamente en `proximos_servicios`. | Aclarar el significado del campo antes de ofrecer su edición. |
| Baja | Mensaje genérico de baja dice desactivar o eliminar; algunos módulos solo desactivan. Administradores ya tiene confirmación específica. | Ajustar mensajes por módulo. |

## Git y verificación

La carpeta abierta contiene una entrada `.git` vacía y `git status` no la reconoce
como repositorio. No se pueden comprobar rama, cambios previos ni `git diff --check`.
No se inicializó otro repositorio ni se copiaron versiones de otras carpetas.

Se ejecutó `.venv/bin/python -B -m unittest discover -s tests -v`: 28 pruebas
aprobadas (13 anteriores y 15 nuevas). Cubren folios, VIN, eliminación y protección
de administradores, cierre de conexiones, rollback y las comprobaciones previas.
Las pruebas de SQL nuevas usan dobles; no demuestran ejecución en MySQL.

Se construyeron `VehicleDialog` y `AdminsPage` con Qt offscreen y controlador
simulado para verificar el campo VIN y el botón Eliminar. No es una inspección
visual ni una prueba completa de interacción, impresión o PDF.

Antes de la exposición falta probar con MySQL: alta con folio automático,
rechazo de VIN inválido, VIN válido, eliminación de cuenta activa/inactiva,
protección del último administrador, inventario tras edición/eliminación,
fallo transaccional, dashboard, búsquedas, comprobantes y cierre de sesión.
Las pruebas de escritura deben usar registros dedicados, sin borrar datos ajenos.
