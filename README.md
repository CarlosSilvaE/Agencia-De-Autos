# Agencia de Automóviles

Aplicación de escritorio hecha con **Python + PySide6** y organizada con
arquitectura MVC. La app se conecta directamente desde Python a MySQL 8.4, que
se ejecuta en Docker. No requiere API web ni backend en otro lenguaje.

## Requisitos

- Docker Desktop con Docker Compose.
- Python 3.10 o posterior.

## Inicio

1. Copia `.env.example` como `.env` y configura contraseñas propias para MySQL
   y el administrador inicial antes de usar datos reales.
2. Inicia MySQL: `docker compose up -d`.
3. Desde la raíz del proyecto, instala dependencias y ejecuta la aplicación:

   ```powershell
   python -m pip install -r requirements.txt
   python main.py
   ```

4. Inicia sesión con `ADMIN_INITIAL_USERNAME` y `ADMIN_INITIAL_PASSWORD` del
   archivo `.env`. En una instalación nueva, el usuario predeterminado es
   `admin`; cambia la contraseña de ejemplo antes de utilizar la aplicación.

La conexión de la aplicación usa `MYSQL_HOST` y `MYSQL_PORT`; por defecto
MySQL está disponible solo en el equipo local, en el puerto `3307`. Los datos
se conservan en el volumen Docker `mysql_data`.

Para detener los contenedores: `docker compose down`. Para borrar también los
datos guardados, usa `docker compose down -v`.

## Módulos

- Inicio de sesión administrativo.
- Resumen de servicios por estado, total o fecha.
- Alta, consulta, edición, cambio de estado, comprobante y eliminación de
  servicios.
- Captura de entregas, refacciones y próximos servicios asociados; el inventario
  de refacciones se actualiza en una transacción MySQL.
- Consulta de próximos servicios por folio o propietario.
- Administración de clientes y vehículos.
- Catálogos de marcas, modelos, años y refacciones.
- Administración de usuarios administradores.

## Arquitectura

- `main.py`: punto de entrada y composición de dependencias.
- `models/`: operaciones de negocio y acceso directo a MySQL.
- `controllers/`: coordinación de autenticación y módulos de negocio entre
  modelo y vistas.
- `views/`: ventanas, páginas, formularios y tema PySide6.
- `tests/`: pruebas del flujo modelo-controlador.
- `database/`: esquema inicial de MySQL.
- `docker-compose.yml`: contenedor de MySQL.

La aplicación de escritorio sigue MVC: las vistas presentan datos y capturan
acciones; los controladores coordinan los casos de uso; y los modelos validan
las operaciones y persisten en MySQL mediante el componente de base de datos.
El usuario administrador inicial solo se crea cuando la base de datos no
contiene administradores. Cambiar las variables del `.env` después de que ya
exista no cambia la contraseña guardada; usa **Administradores** para
modificarla.

Para ejecutar las pruebas MVC desde la raíz:
`python -m unittest discover -s tests -v`.
