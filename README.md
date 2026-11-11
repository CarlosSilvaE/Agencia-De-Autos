# Agencia de Automóviles — Parcial 2 (MVC + patrones)

Aplicación **desktop** de mantenimiento preventivo/correctivo en **Python + PySide6**. El modelo realiza las operaciones en **MySQL 8.4** (contenedor Docker). No utiliza un backend HTTP separado: desde la interfaz, las operaciones pasan por controladores hacia el modelo y la base de datos.

## Ejecutar en Windows (PowerShell)

Necesitas **Docker Desktop** y **Python 3.10 o posterior**. Ejecuta los comandos desde la raíz del proyecto:

```powershell
Copy-Item .env.example .env
notepad .env                  # Cambia las 3 contraseñas por valores propios
# Inicializa Docker Desktop antes de continuar
docker compose up -d
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Los parámetros del archivo `.env` definen la conexión. Por defecto MySQL escucha **solo en `127.0.0.1:3307`**. Si ya tienes un volumen Docker creado, `database/init.sql` **no se ejecutará nuevamente**; esta versión no modifica el esquema existente. `ADMIN_INITIAL_PASSWORD` solamente se utiliza si todavía no existe ningún administrador.

Si Docker falla, revisa `docker compose ps` y `docker compose logs database`. Para detenerlo sin borrar los datos: `docker compose down`. **No uses `docker compose down -v` si quieres conservar la base de datos.**

## Módulos

- Login de administradores con contraseñas hasheadas, cierre de sesión, administración de usuarios.
- Catálogos CRUD de marcas, modelos, años y refacciones; gestión de clientes y vehículos.
- Servicios: alta, modificación, consulta por folio o propietario, tres estados, eliminación y comprobante imprimible / PDF.
- Control de quién entregó el vehículo con historial de recepciones.
- Varias refacciones por servicio y la misma refacción en múltiples servicios, con control de existencias.
- Próximos servicios: fecha, kilometraje y búsqueda por folio/propietario.
- Dashboard: métricas, tabla y **gráfica de barras real** filtrable por total o por día.

## Arquitectura, patrones y documentación de la tarea

- MVC: `models/`, `controllers/`, `views/`. `models/domain.py` define `ServiceReceipt` y `ReceiptPart` como objetos de dominio que construyen y dan formato al comprobante.
- **Singleton**: `models/provider.py` (`DatabaseProvider`). Instancia de proveedor compartida; conexiones y transacciones independientes.
- **Strategy**: `models/dashboard_strategy.py`, con dos consultas seleccionables (`TotalDashboardStrategy`, `DailyDashboardStrategy`).
- Diagrama de clases: [`docs/diagrama_clases.png`](docs/diagrama_clases.png).
- Diagrama de base de datos: [`docs/diagrama_bd.png`](docs/diagrama_bd.png).
- Matriz de cumplimiento y pruebas: [`docs/CUMPLIMIENTO_TAREA.md`](docs/CUMPLIMIENTO_TAREA.md).
- Guion de exposición: [`docs/GUION_EXPOSICION.md`](docs/GUION_EXPOSICION.md).
- Plantilla requerida de integrantes/responsabilidades: `docs/Entrega_y_responsabilidades.docx` (**rellenar con nombres y asignaciones reales**).

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Los tests comprueban la delegación MVC, hashes, Strategy, Singleton, logout y ediciones sin cambios. **No sustituyen** las pruebas manuales de formularios contra MySQL: seguir los 12 pasos en `docs/CUMPLIMIENTO_TAREA.md`.

## Seguridad y distribución

El ZIP **no contiene `.env`, `.git`, credenciales reales ni entornos virtuales**. Genera tus propias contraseñas en `.env` y nunca publiques el archivo. Si el ZIP original incluía contraseñas utilizables, cámbialas en el entorno real. Usa una cuenta MySQL con permisos adecuados para la práctica.
