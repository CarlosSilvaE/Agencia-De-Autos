# Diagnóstico de MySQL — 11 de noviembre de 2026

Se consultó la instancia configurada en `.env`, sin mostrar credenciales ni
datos personales. Base: `agencia_autos`; versión reportada: MySQL 8.4.13.
Se ejecutaron SHOW TABLES, SHOW CREATE TABLE y COUNT(*). La inspección inicial fue de solo lectura. Después, con autorización del usuario,
se respaldó la base y se aplicó la migración indicada al final de este documento.

## Causa confirmada

| Base instalada | Código e init.sql |
|---|---|
| Tabla `anio` | Tabla `anos` |
| `anio.id_anio` | `anos.id_ano` |
| `anio.anio` | `anos.ano` |
| `vehiculos.id_anio` | `vehiculos.id_ano` |

La clave foránea de vehículos apunta correctamente a `anio.id_anio` en el
esquema instalado. No falta el catálogo de años: tiene otro nombre.
El fallo del arranque ocurre cuando initialize intenta insertar en `anos`.
No se puede determinar con estas consultas cuándo o quién cambió los nombres.

## Registros existentes

| Tabla | Filas |
|---|---:|
| administradores | 2 |
| anio | 49 |
| clientes | 25 |
| entregas | 100 |
| estados | 3 |
| marcas | 6 |
| modelos | 11 |
| proximos_servicios | 34 |
| refacciones | 16 |
| servicio_refaccion | 134 |
| servicios | 101 |
| vehiculos | 32 |

El resto de las tablas presenta las columnas requeridas por la aplicación.
`servicios` incluye además `recibido_por` y `tercero_recoge`, ambas opcionales;
se deben conservar. Esta inspección no certifica la validez de cada dato.

## Corrección aplicada con autorización

`database/migrations/001_normalizar_anos.sql` renombra la tabla y sus columnas
para alinearlas con el código y `init.sql`. No copia ni elimina registros.
No basta con crear una tabla anos vacía: los vehículos existentes seguirían
referenciando el catálogo anterior y las consultas no quedarían alineadas.

Antes de aplicar: cerrar las aplicaciones que usan esta base, generar y validar
un respaldo completo con mysqldump (esquema y datos) y comprobar que ninguna otra
copia del proyecto dependa de los nombres `anio` e `id_anio`.
Los ALTER/RENAME hacen commit implícito; si falla un paso, inspeccionar los nombres
actuales antes de continuar. No repetir el archivo completo sin esa comprobación.

Después: comprobar las claves foráneas, conservar las cantidades de esta tabla,
verificar cero vehículos sin año y ejecutar consultas reales del modelo
(servicios, vehículos, catálogos, dashboard y próximos mantenimientos).
Finalmente iniciar `python main.py` para verificar login e interfaz.
La inicialización puede añadir años o estados faltantes, por lo que las cantidades
deben compararse antes de ejecutar el arranque.

La migración fue aplicada el 11 de noviembre de 2026, tras comprobar que no
había otras conexiones a esta base. No se borraron ni recrearon volúmenes.

## Resultado de la aplicación

- Respaldo completo con mysqldump: esquema, datos, triggers, rutinas y eventos.
- Archivo privado: `/tmp/agencia-respaldos/agencia_autos_antes_anos_20261111_220325.sql.gz`.
- SHA256: `27f38e521689329ec27613be550d596f0aab427407f7483806240493e278410e`.
- Se verificó que el volcado terminó, contiene esquema y datos y que el archivo
  comprimido se descomprime al contenido original. No se probó una restauración.
- Se compararon cantidad y hash del contenido completo de las 12 tablas antes y
  después de los cambios de nombres: todas conservaron sus datos.
- La FK de `vehiculos.id_ano` apunta a `anos.id_ano`; cero vehículos sin año.
- Consultas reales: 101 servicios, 31 vehículos activos con propietario activo,
  49 años activos, 3 estados del dashboard y 34 próximos servicios.
  La tabla vehículos conserva 32 filas; el listado filtra los registros inactivos.
- `AgencyModel.initialize()` terminó correctamente contra MySQL después de migrar.
- Falta la comprobación visual del login y navegación por el usuario.

El respaldo está en `/tmp`, que puede limpiarse al reiniciar; debe trasladarse a
un lugar privado y persistente si se necesita conservarlo. No incluirlo en Git.
