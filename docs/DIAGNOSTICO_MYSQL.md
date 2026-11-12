# Diagnostico de MySQL — 11 de noviembre de 2026

Se consulto la instancia configurada en `.env`, sin mostrar credenciales ni
datos personales. Base: `agencia_autos`; version reportada: MySQL 8.4.13.
Se ejecutaron SHOW TABLES, SHOW CREATE TABLE y COUNT(*). La inspeccion inicial fue de solo lectura. Despues, con autorizacion del usuario,
se respaldo la base y se aplico la migracion indicada al final de este documento.

## Causa confirmada

| Base instalada | Codigo e init.sql |
|---|---|
| Tabla `anio` | Tabla `anos` |
| `anio.id_anio` | `anos.id_ano` |
| `anio.anio` | `anos.ano` |
| `vehiculos.id_anio` | `vehiculos.id_ano` |

La clave foranea de vehiculos apunta correctamente a `anio.id_anio` en el
esquema instalado. No falta el catalogo de anios: tiene otro nombre.
El fallo del arranque ocurre cuando initialize intenta insertar en `anos`.
No se puede determinar con estas consultas cuando o quien cambio los nombres.

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

El resto de las tablas presenta las columnas requeridas por la aplicacion.
`servicios` incluye ademas `recibido_por` y `tercero_recoge`, ambas opcionales;
se deben conservar. Esta inspeccion no certifica la validez de cada dato.

## Correccion aplicada con autorizacion

`database/migrations/001_normalizar_anos.sql` renombra la tabla y sus columnas
para alinearlas con el codigo y `init.sql`. No copia ni elimina registros.
No basta con crear una tabla anos vacia: los vehiculos existentes seguirian
referenciando el catalogo anterior y las consultas no quedarian alineadas.

Antes de aplicar: cerrar las aplicaciones que usan esta base, generar y validar
un respaldo completo con mysqldump (esquema y datos) y comprobar que ninguna otra
copia del proyecto dependa de los nombres `anio` e `id_anio`.
Los ALTER/RENAME hacen commit implicito; si falla un paso, inspeccionar los nombres
actuales antes de continuar. No repetir el archivo completo sin esa comprobacion.

Despues: comprobar las claves foraneas, conservar las cantidades de esta tabla,
verificar cero vehiculos sin anio y ejecutar consultas reales del modelo
(servicios, vehiculos, catalogos, dashboard y proximos mantenimientos).
Finalmente iniciar `python main.py` para verificar login e interfaz.
La inicializacion puede anadir anios o estados faltantes, por lo que las cantidades
deben compararse antes de ejecutar el arranque.

La migracion fue aplicada el 11 de noviembre de 2026, tras comprobar que no
habia otras conexiones a esta base. No se borraron ni recrearon volumenes.

## Resultado de la aplicacion

- Respaldo completo con mysqldump: esquema, datos, triggers, rutinas y eventos.
- Archivo privado: `/tmp/agencia-respaldos/agencia_autos_antes_anos_20261111_220325.sql.gz`.
- SHA256: `27f38e521689329ec27613be550d596f0aab427407f7483806240493e278410e`.
- Se verifico que el volcado termino, contiene esquema y datos y que el archivo
  comprimido se descomprime al contenido original. No se probo una restauracion.
- Se compararon cantidad y hash del contenido completo de las 12 tablas antes y
  despues de los cambios de nombres: todas conservaron sus datos.
- La FK de `vehiculos.id_ano` apunta a `anos.id_ano`; cero vehiculos sin anio.
- Consultas reales: 101 servicios, 31 vehiculos activos con propietario activo,
  49 anios activos, 3 estados del dashboard y 34 proximos servicios.
  La tabla vehiculos conserva 32 filas; el listado filtra los registros inactivos.
- `AgencyModel.initialize()` termino correctamente contra MySQL despues de migrar.
- Falta la comprobacion visual del login y navegacion por el usuario.

El respaldo esta en `/tmp`, que puede limpiarse al reiniciar; debe trasladarse a
un lugar privado y persistente si se necesita conservarlo. No incluirlo en Git.
