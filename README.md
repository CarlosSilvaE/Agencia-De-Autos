# Agencia de Automoviles — Parcial 2 (MVC + patrones)

Aplicacion **desktop** de mantenimiento preventivo/correctivo en **Python + PySide6**. El modelo realiza las operaciones en **MySQL 8.4** (contenedor Docker). No utiliza un backend HTTP separado: desde la interfaz, las operaciones pasan por controladores hacia el modelo y la base de datos.

## Ejecutar en Windows (PowerShell)

Necesitas **Docker Desktop** y **Python 3.10 o posterior**. Ejecuta los comandos desde la raiz del proyecto:

```powershell
Copy-Item .env.example .env
notepad .env                  # Cambia las 3 contrasenas por valores propios
# Inicializa Docker Desktop antes de continuar
docker compose up -d
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Los parametros del archivo `.env` definen la conexion. Por defecto MySQL escucha **solo en `127.0.0.1:3307`**. Si ya tienes un volumen Docker creado, `database/init.sql` **no se ejecutara nuevamente**. Al iniciar la aplicacion se renombran la tabla y las columnas antiguas de anios a `anio` e `id_anio`, conservando sus registros y relaciones. `ADMIN_INITIAL_PASSWORD` solamente se utiliza si todavia no existe ningun administrador.

Si Docker falla, revisa `docker compose ps` y `docker compose logs database`. Para detenerlo sin borrar los datos: `docker compose down`. **No uses `docker compose down -v` si quieres conservar la base de datos.**

## Catalogos iniciales

`database/init.sql` incluye 10 marcas con 50 modelos reales, anios de 2015 a 2026 y 30 tipos de refacciones. El poblado solo agrega catalogos; los precios y las existencias son ejemplos, y los SKU son claves internas. El sistema mantiene ademas los tres estados de servicio necesarios para funcionar.

Docker carga estos datos al crear la base por primera vez. Para agregarlos a un volumen existente, consulta [la guia de catalogos](docs/GUIA_DATOS_PRUEBA.md). Repetir los INSERT no duplica registros ni reinicia precios o inventario.

## Modulos

- Login de administradores con contrasenas hasheadas, cierre de sesion, administracion de usuarios.
- Catalogos CRUD de marcas, modelos, anios y refacciones; gestion de clientes y vehiculos.
- Servicios: alta, modificacion, consulta por folio o propietario, tres estados, eliminacion y comprobante imprimible / PDF.
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
