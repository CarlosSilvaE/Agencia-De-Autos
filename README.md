# Agencia de Automoviles — Parcial 2 (MVC + patrones)

Aplicacion **desktop** de mantenimiento preventivo/correctivo en **Python + PySide6**. El modelo realiza las operaciones en **MySQL 8.4** (contenedor Docker). No utiliza un backend HTTP separado: desde la interfaz, las operaciones pasan por controladores hacia el modelo y la base de datos.

## Ejecutar en Windows (PowerShell)

Necesitas **Docker Desktop** y **Python 3.10 o posterior**. Ejecuta los comandos desde la raiz del proyecto:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env                  # Completa los valores o usa tu .env privado
# Inicializa Docker Desktop antes de continuar
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/preparar_entorno.py
.\.venv\Scripts\python.exe main.py
```

La aplicacion y el preparador usan el `.env` de la raiz con prioridad sobre variables antiguas de Windows o la terminal. Por defecto MySQL escucha **solo en `127.0.0.1:3307`**. El preparador sincroniza la cuenta MySQL, aplica las migraciones necesarias y carga los catalogos tambien en volumenes existentes. `ADMIN_INITIAL_PASSWORD` solamente se utiliza si todavia no existe ningun administrador. Consulta [el despliegue en otras maquinas](docs/DESPLIEGUE.md).

Si Docker falla, revisa `docker compose ps` y `docker compose logs database`. Para detenerlo sin borrar los datos: `docker compose down`. **No uses `docker compose down -v` si quieres conservar la base de datos.**

## Catalogos iniciales

El archivo `database/init.sql` incluye 10 marcas con 50 modelos, 12 anios y 30 tipos de refacciones. Los textos del poblado no usan acentos. Los precios y existencias son ejemplos; los SKU son internos.

Los INSERT conservan los registros anteriores y permiten repetir la carga sin duplicar el poblado ni reiniciar el inventario. No generan clientes, vehiculos ni servicios. Consulta [la guia de carga y uso de servicios](docs/GUIA_DATOS_PRUEBA.md) para aplicar el archivo en un volumen existente.

## Poblado de pruebas

Para generar 100 servicios ficticios con clientes, vehiculos, recepciones y refacciones de prueba:

```powershell
.\venv\Scripts\python.exe scripts/poblar_pruebas.py
```

Usa `.venv` en lugar de `venv` si corresponde. Los datos tienen identificadores `PRB-*`, usan inventario de prueba y se conservan al repetir la carga sin duplicar registros ni descontar dos veces las mismas piezas. Consulta [los escenarios y opciones del poblado](docs/POBLADO_PRUEBAS.md).

## Modulos

- Login de administradores con contrasenas hasheadas, cierre de sesion, administracion de usuarios.
- Catalogos CRUD de marcas, modelos, anios y refacciones; gestion de clientes y vehiculos.
- Servicios: alta, modificacion, consulta por folio o propietario, tres estados, eliminacion y comprobante imprimible / PDF. Preventivo ofrece mensajes editables; Correctivo requiere descripcion manual.
- Mano de obra editable con valor inicial de 1500, total automatico con refacciones y recepcion opcional. Para bases anteriores, aplicar `database/migrations/002_mano_obra.sql` una sola vez antes de iniciar esta version.
- Control de quien entrego el vehiculo con historial de recepciones.
- Varias refacciones por servicio y la misma refaccion en multiples servicios, con control de existencias.
- Proximos servicios: fecha, kilometraje y busqueda por folio/propietario.
- Dashboard: metricas, tabla y **grafica de barras real** filtrable por total o por dia.

## Arquitectura, patrones y documentacion de la tarea

- MVC: `models/`, `controllers/`, `views/`. `models/domain.py` define `ServiceReceipt` y `ReceiptPart` como objetos de dominio que construyen y dan formato al comprobante.
- **Singleton**: `models/provider.py` (`DatabaseProvider`). Instancia de proveedor compartida; conexiones y transacciones independientes.
- **Strategy**: `models/dashboard_strategy.py`, con dos consultas seleccionables (`TotalDashboardStrategy`, `DailyDashboardStrategy`).
- Diagrama de clases: [`docs/diagrama_clases.png`](docs/diagrama_clases.png).
- Diagrama de base de datos: [`docs/diagrama_bd.png`](docs/diagrama_bd.png).
- Matriz de cumplimiento y pruebas: [`docs/CUMPLIMIENTO_TAREA.md`](docs/CUMPLIMIENTO_TAREA.md).
- Guion de exposicion: [`docs/GUION_EXPOSICION.md`](docs/GUION_EXPOSICION.md).
- Plantilla requerida de integrantes/responsabilidades: `docs/Entrega_y_responsabilidades.docx` (**rellenar con nombres y asignaciones reales**).

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Los tests comprueban la delegacion MVC, hashes, Strategy, Singleton, logout y ediciones sin cambios. **No sustituyen** las pruebas manuales de formularios contra MySQL: seguir los 12 pasos en `docs/CUMPLIMIENTO_TAREA.md`.

## Seguridad y distribucion

El ZIP **no contiene `.env`, `.git`, credenciales reales ni entornos virtuales**. Genera tus propias contrasenas en `.env` y nunca publiques el archivo. Si el ZIP original incluia contrasenas utilizables, cambialas en el entorno real. Usa una cuenta MySQL con permisos adecuados para la practica.

## VIN y actualizacion de bases existentes

En Clientes y vehiculos, dejar el VIN vacio genera un identificador de 17
caracteres. Si se escribe, debe tener 17 caracteres alfanumericos sin I, N ni Q;
se guarda en mayusculas. El valor generado es un identificador de la aplicacion,
no un VIN asignado por el fabricante. Para vehiculos reales, introducir su VIN.

Los folios automaticos caben en el limite SQL de 30 caracteres. Administradores
permite eliminar definitivamente una cuenta, protegiendo al ultimo activo;
la casilla Activo de Editar permite seguir desactivando sin eliminar.

El catalogo de anios utiliza la tabla `anios`, con columnas `id_anio`, `anio`
y `activo`. La columna `vehiculos.id_anio` referencia ese catalogo. El arranque
no renombra tablas ni ejecuta migraciones; el preparador aplica esos cambios de forma explicita. `database/init.sql` utiliza estos
mismos nombres para bases nuevas; no requiere borrar el volumen de Docker.
