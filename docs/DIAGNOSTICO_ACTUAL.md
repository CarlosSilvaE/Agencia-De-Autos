# Diagnostico del proyecto — 11 de noviembre de 2026

Revision estatica del arranque, modelos, controladores, formularios, paginas,
grafica, esquema SQL, Compose, generador y pruebas. No se modificaron datos
existentes ni se ejecuto la aplicacion contra MySQL. Los hallazgos sobre datos
son posibilidades derivadas del codigo; no un inventario de la base instalada.

## Cambios implementados

- Folio automatico de 29 caracteres, compatible con `VARCHAR(30)`; validacion
  de longitud para folios manuales y normalizacion de espacios exteriores.
- Eliminacion fisica de administradores activos o inactivos con confirmacion
  explicita y transaccion. Se conserva la proteccion del ultimo activo.
  La desactivacion sigue disponible en Editar mediante la casilla Activo.
- VIN manual de 17 caracteres ASCII alfanumericos, sin I, N ni Q, segun
  la regla solicitada. Se convierte a mayusculas y se quitan espacios exteriores.
  Si se deja vacio, se genera automaticamente. Validacion en las dos rutas del modelo que guardan vehiculos.
- Nuevos vehiculos DEMO reciben un VIN que cumple la regla. La semilla no
  reemplaza vehiculos existentes; los VIN anteriores quedan intactos.
- La conexion se cierra incluso si falla la creacion o el cierre del cursor.
- Edicion y eliminacion de servicios bloquean su fila con `FOR UPDATE` para
  serializar esas operaciones sobre un mismo servicio. Falta probar concurrencia
  real con MySQL; pueden seguir existiendo interbloqueos entre servicios distintos.

No se cambio el esquema. No hace falta migrar la base para aplicar estos cambios.
La validacion del VIN vive en la aplicacion; SQL directo puede eludirla.

## Arquitectura y requisitos

Se conserva MVC: `views/` recoge y presenta datos, los controladores delegan y
`AgencyModel` concentra negocio y SQL. `MySQLDatabase` administra las sesiones.
Singleton comparte el proveedor, no conexiones; Strategy construye las consultas
total y diaria. `ServiceReceipt` y `ReceiptPart` construyen el comprobante.

Estan implementados login, navegacion, cierre de sesion, catalogos, clientes,
vehiculos, administradores, servicios con tres estados, busquedas, comprobante
imprimible/PDF, recepcion con historial, proximos servicios y dashboard.
El esquema contiene claves foraneas y la tabla N:M `servicio_refaccion`.
Existen diagramas de clases y de datos y una matriz de cumplimiento.
La presencia en codigo no sustituye la demostracion de cada requisito en MySQL.

El alta de servicios valida, guarda cliente y vehiculo, inserta servicio y guarda
relaciones en una transaccion. La edicion restituye inventario previo y descuenta
el nuevo. La eliminacion restituye inventario y borra relaciones antes del servicio.
Las cantidades se descuentan mediante un UPDATE condicionado a existencia suficiente.

Compose ejecuta MySQL 8.4 con volumen persistente, puerto local configurable y
script de inicializacion. Editar `init.sql` no modifica un volumen inicializado.
En el diagnostico anterior el contenedor estaba healthy y la configuracion paso
la validacion de Compose; no se repitio una integracion SQL en esta revision.

## Pendientes ordenados por prioridad

| Prioridad | Hallazgo y consecuencia | Ubicacion / siguiente accion |
|---|---|---|
| Alta | VIN antiguos vacios o ficticios pueden impedir guardar vehiculos y crear o editar sus servicios. El formulario de servicio reutiliza el VIN almacenado. | Corregir el VIN real desde Clientes y vehiculos; no inventar ni reemplazar automaticamente los existentes. |
| Alta | El formulario de servicios solo recibe refacciones activas. Al editar puede omitir una refaccion historica desactivada y quitarla al guardar. | `service_options`, `ServiceDialog`, `_save_service_relations`: conservar explicitamente las relaciones historicas y definir si se permiten cambios de cantidad. |
| Alta | Editar un servicio cuyo vehiculo o propietario esta desactivado puede seleccionar otro vehiculo porque el original no aparece en el combo. | `list_vehicles`, `set_combo_id`, `ServiceDialog`: incluir el registro historico o bloquear el guardado con mensaje, sin seleccionar un sustituto. |
| Media | Una cuenta eliminada o desactivada en otra sesion conserva acceso en una ventana ya autenticada. Los controladores no vuelven a verificar la identidad. | Definir y aplicar invalidacion de sesiones; actualmente el login se valida solo al entrar. |
| Media | Editar servicios actualiza tambien cliente y vehiculo compartidos. Los datos presentados por otros servicios y sus comprobantes pueden cambiar. | `_save_client`, `_save_vehicle`, `list_services`: decidir si el comprobante debe representar datos actuales o una copia historica. |
| Media | El modelo no valida completamente numeros de catalogo: por ejemplo precio negativo, valores no finitos o anios fuera de rango. Los controles Qt limitan algunos casos, pero SQL/modelo no son equivalentes. | `save_catalog_item`, `_validate_service`: reforzar las reglas de negocio independientemente de la interfaz. |
| Media | Se pueden desactivar marcas y anios usados por vehiculos; las FK no impiden una baja logica. Los combos pueden dejar de representar los valores historicos. | `delete_catalog_item`, `VehicleDialog`: definir politica coherente para dependencias activas e historicas. |
| Media | Operaciones MySQL y hashes se ejecutan en el hilo de la interfaz; una conexion lenta puede congelarla durante el timeout. | Paginas y login: evaluar trabajo en segundo plano preservando conexiones independientes. |
| Baja | `servicios.fecha_programada` se consulta pero no se guarda desde el formulario; el proximo mantenimiento se almacena separadamente en `proximos_servicios`. | Aclarar el significado del campo antes de ofrecer su edicion. |
| Baja | Mensaje generico de baja dice desactivar o eliminar; algunos modulos solo desactivan. Administradores ya tiene confirmacion especifica. | Ajustar mensajes por modulo. |

## Git y verificacion

La carpeta abierta contiene una entrada `.git` vacia y `git status` no la reconoce
como repositorio. No se pueden comprobar rama, cambios previos ni `git diff --check`.
No se inicializo otro repositorio ni se copiaron versiones de otras carpetas.

Se ejecuto `.venv/bin/python -B -m unittest discover -s tests -v`: 28 pruebas
aprobadas (13 anteriores y 15 nuevas). Cubren folios, VIN, eliminacion y proteccion
de administradores, cierre de conexiones, rollback y las comprobaciones previas.
Las pruebas de SQL nuevas usan dobles; no demuestran ejecucion en MySQL.

Se construyeron `VehicleDialog` y `AdminsPage` con Qt offscreen y controlador
simulado para verificar el campo VIN y el boton Eliminar. No es una inspeccion
visual ni una prueba completa de interaccion, impresion o PDF.

Antes de la exposicion falta probar con MySQL: alta con folio automatico,
rechazo de VIN invalido, VIN valido, eliminacion de cuenta activa/inactiva,
proteccion del ultimo administrador, inventario tras edicion/eliminacion,
fallo transaccional, dashboard, busquedas, comprobantes y cierre de sesion.
Las pruebas de escritura deben usar registros dedicados, sin borrar datos ajenos.
