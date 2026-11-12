# Despliegue con el mismo .env

La interfaz PySide6 se ejecuta en la maquina del usuario; Docker ejecuta MySQL. El preparador funciona en Windows, Linux y macOS con Python y Docker Compose disponibles. Para abrir la interfaz se necesita un entorno grafico.

## Preparar una maquina

Copiar el proyecto, crear un entorno virtual nuevo e instalar `requirements.txt`. Copiar de forma privada el `.env` que quieres utilizar, o crear uno desde `.env.example` y completar sus claves. Iniciar Docker y ejecutar el preparador antes de abrir la aplicacion.

Windows, desde la raiz del proyecto:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe scripts/preparar_entorno.py
.\venv\Scripts\python.exe main.py
```

Linux/macOS:

```sh
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python scripts/preparar_entorno.py
./venv/bin/python main.py
```

Sustituye los valores `CAMBIA_*` antes de preparar la base. Si el entorno se llama `.venv`, adapta las rutas. No copies un entorno virtual de otra maquina. El `.env` privado no se publica en Git.

## Que hace el preparador

- Lee el `.env` de la raiz con prioridad sobre variables antiguas de la terminal. Los valores son literales: no se expanden referencias `${OTRA_VARIABLE}` dentro de una clave.
- Inicia MySQL y espera disponibilidad.
- Usa root para crear la base y sincronizar la cuenta `MYSQL_USER` con `MYSQL_PASSWORD`. Esa cuenta recibe permisos solo sobre la base configurada. Si root rechaza la clave, pero la cuenta de la aplicacion ya funciona con `.env`, continua con esa cuenta sin cambiar root.
- Alinea los nombres antiguos de anios con `anios`, `id_anio` y `anio`, conservando claves y referencias. Si encuentra varios catalogos de anios, se detiene para evitar mezclarlos.
- Crea tablas y catalogos faltantes y aplica la migracion de `mano_obra` cuando sea necesaria. Puede retomar una migracion de mano de obra que quedo con valores nulos.
- Crea el administrador inicial unicamente si no existe ningun administrador y comprueba las consultas principales.

Se puede repetir el comando al actualizar el proyecto. No elimina tablas ni volumenes, ni restablece inventarios. Los cambios de esquema de MySQL se confirman por separado; si un paso falla, corrige el motivo y vuelve a preparar.

## Variables y casos frecuentes

- `MYSQL_HOST=127.0.0.1`: la aplicacion corre fuera de Docker. El nombre `database` se usa entre contenedores y no sustituye a localhost para esta interfaz desktop.
- `MYSQL_PORT=3307`: puerto publicado en la maquina. MySQL escucha internamente en 3306. Si el puerto local esta ocupado, cambia este valor y vuelve a preparar.
- `MYSQL_DATABASE`: base que se creara o utilizara.
- `MYSQL_USER` y `MYSQL_PASSWORD`: cuenta de conexion. El preparador la sincroniza con el archivo.
- `MYSQL_ROOT_PASSWORD`: para crear o sincronizar cuentas debe coincidir con la clave root almacenada en un volumen existente. Cambiar el archivo no restablece esa clave; si se desconoce y la cuenta de la aplicacion tampoco funciona, se requiere recuperarla por separado. Si la cuenta de la aplicacion ya es valida y tiene permisos sobre su base, el preparador puede continuar sin modificar root.
- `ADMIN_INITIAL_USERNAME` y `ADMIN_INITIAL_PASSWORD`: solo se utilizan en la primera creacion de administradores. Las cuentas existentes y sus cambios desde la interfaz se conservan.
- `COMPOSE_PROJECT_NAME`: por defecto `agencia-automoviles`. Para otra instalacion independiente en la misma maquina, usa un nombre diferente y otro puerto. Otro nombre crea un volumen independiente; no traslada los datos anteriores.

Para usar un archivo alternativo durante una preparacion:

```powershell
.\venv\Scripts\python.exe scripts/preparar_entorno.py --env-file C:\ruta\privada\.env
```

La aplicacion normal sigue leyendo el `.env` de la raiz. Para ejecutar despues con esa configuracion, copia el archivo privado a esa ubicacion.

Copiar el proyecto y `.env` reproduce la configuracion y los catalogos. Los clientes, vehiculos y servicios de un volumen anterior requieren trasladar tambien un respaldo de esa base. El poblado ficticio se carga por separado con `scripts/poblar_pruebas.py`.

## Descripciones de servicios

Preventivo ofrece mensajes para revision general, aceite y filtro, frenos, kilometraje y enfriamiento. Se pueden modificar manualmente. Correctivo comienza sin texto automatico para registrar la falla y el trabajo especificos. Cambiar de tipo conserva el borrador de cada uno durante esa captura; abrir un servicio existente conserva su descripcion guardada.

## Verificacion automatizada

Las pruebas normales no requieren Docker. Las pruebas reales de despliegue se habilitan explicitamente; crean y retiran solo bases y cuentas temporales con prefijo `agencia_verificacion_` / `verificacion_`:

```powershell
$env:AGENCIA_MYSQL_INTEGRATION="1"
.\venv\Scripts\python.exe -m unittest discover -s tests -p test_mysql_deployment_integration.py -v
Remove-Item Env:AGENCIA_MYSQL_INTEGRATION
```

Cubren una base nueva, repeticion conservando datos, migraciones desde nombres antiguos, mano de obra y cambio de claves con caracteres especiales. Usan el contenedor ya iniciado y la clave root del `.env` privado.

## Referencias

- [Precedencia de configuracion de Docker Compose](https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/).
- [Persistencia e inicializacion de MySQL con Docker](https://dev.mysql.com/doc/refman/8.4/en/docker-mysql-more-topics.html).
- [Scripts SQL con Connector/Python 9.2 o posterior](https://dev.mysql.com/doc/connector-python/en/connector-python-multi.html).
