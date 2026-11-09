# Agencia de Automóviles — Mantenimiento

Aplicación MVC para registrar y consultar mantenimiento preventivo y correctivo:
Flask (vistas/controladores) → API MVC ASP.NET Core 8 → MySQL 8.4.

## Inicio con Docker

1. Copia `.env.example` como `.env`.
2. Cambia `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`, `FLASK_SECRET_KEY` y
   `ADMIN_INITIAL_PASSWORD` antes de usar datos reales.
3. Ejecuta `docker compose up -d --build`.
4. Abre <http://localhost:8080>.
5. En una base nueva, el usuario inicial es `admin` y la contraseña es la que
   configuraste en `ADMIN_INITIAL_PASSWORD` (por omisión, `admin123`).

La API C# solo es accesible en la red privada de Compose. La aplicación web se
publica en `8080`; MySQL se publica en el puerto host `3307`. Los datos se
conservan en el volumen `mysql_data`.

## Funcionalidad

- Login administrativo; contraseñas almacenadas con el hasher de ASP.NET Core.
- Administración de usuarios administradores, con contraseña opcional al editar
  y protección contra desactivar al último administrador.
- CRUD de marcas, modelos, años y refacciones. Los estados de servicio se
  mantienen como los tres valores operacionales requeridos.
- CRUD de clientes y vehículos, además de su captura desde el registro del
  servicio.
- Alta, consulta por folio o propietario, modificación, cambio de estado y
  eliminación de servicios.
- Clasificación del mantenimiento como preventivo o correctivo.
- Captura del propietario, vehículo, descripción, costo y persona que entrega.
- Asociación de varias refacciones a un servicio, controlando existencias en la
  misma transacción de base de datos.
- Registro y consulta de próximos servicios por folio o propietario.
- Comprobante HTML imprimible con los datos básicos del registro y recepción.
- Dashboard Chart.js por estado, con filtro por fecha elegida o por el total.
- Sesión Flask con cookies HttpOnly/SameSite, protección CSRF y cierre de sesión.

## Patrones y modelo

- **Singleton:** `DatabaseConnection` registrado como singleton en el contenedor
  de ASP.NET Core.
- **Strategy:** estrategias intercambiables de consulta total y diaria del
  dashboard.
- El esquema relacional está en `database/init.sql`: administradores, clientes,
  vehículos, marcas, modelos, años, servicios, estados, entregas, refacciones,
  relación servicio-refacción y próximos servicios.

El usuario inicial solo se crea cuando no hay administradores; cambiar las
variables del `.env` después de que ya exista no cambia la contraseña existente.
Para cambiarla, inicia sesión y usa la sección **Administradores**.

## Evidencia de entrega por equipo

La participación en GitHub (commits, push y merge de cada integrante) y el
documento con nombres y responsabilidades asignadas deben agregarse al
repositorio real del equipo. No se inventan esos datos dentro de este proyecto.
