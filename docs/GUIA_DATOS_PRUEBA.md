# Catalogos iniciales

El poblado esta directamente en `database/init.sql`. Incluye 10 marcas con 50 modelos reales, 12 anios (2015-2026) y 30 tipos de refacciones. El sistema tambien inicializa sus tres estados de servicio.

El archivo no genera clientes, vehiculos, servicios ni administradores. Los precios MXN y las existencias son ejemplos. Los SKU `CAT-BOS-*` y `CAT-GAT-*` son identificadores internos; no representan numeros de parte del fabricante ni compatibilidad con un motor especifico. Referencias: [Bosch](https://www.boschautopartes.mx/products) y [Gates](https://www.gates.com.mx/catalogos_boletines_automotriz.html).

## Base nueva

Con Docker Desktop iniciado y `.env` configurado:

```powershell
docker compose up -d database
```

MySQL ejecuta `init.sql` automaticamente solo cuando inicializa un volumen nuevo.

## Base existente

El metodo recomendado es ejecutar `.\venv\Scripts\python.exe scripts/preparar_entorno.py`. Sincroniza la cuenta con `.env`, comprueba los nombres de anios, aplica las migraciones y carga los catalogos. Consulta [la guia de despliegue](DESPLIEGUE.md).

Para una carga SQL manual, comprueba primero que el catalogo se llame `anios`, con columnas `id_anio`, `anio` y `activo`, y que `vehiculos.id_anio` lo referencie. El inicio normal de la aplicacion no renombra tablas.

Abre el cliente MySQL:

```powershell
docker compose exec database sh -c 'mysql -u"$MYSQL_USER" -p "$MYSQL_DATABASE"'
```

Introduce la clave MySQL configurada en `.env`. Ejecuta en el cliente:

```sql
SOURCE /docker-entrypoint-initdb.d/01-init.sql;
```

Esta ruta corresponde al archivo montado por Compose. Los INSERT agregan solo registros ausentes y se pueden repetir sin duplicar el poblado ni reiniciar precios o cantidades. Los nombres de las refacciones de este poblado se normalizan sin acentos al repetirlo. No se borran datos anteriores ni se recrea el volumen.

## Servicios

El formulario tiene tres pestanas: Servicio, Refacciones y Recepcion. La tabla de refacciones aprovecha el espacio disponible y la ventana se puede maximizar. Marca Usar y ajusta cantidad y precio para cada pieza.

Recepcion identifica a la persona que trae y entrega el vehiculo a la agencia; puede ser su propietario o un tercero. No representa a un empleado receptor. Toda la seccion es opcional. Si se registra informacion, queda disponible en el comprobante e historial. Al vaciar una recepcion existente se conserva el historial anterior y se muestra la recepcion actual como no registrada.

Mano de obra tiene un valor inicial de 1500 para servicios nuevos y puede modificarse. El subtotal de refacciones suma solo las piezas marcadas, considerando cantidad y precio unitario. El total se calcula automaticamente como mano de obra mas subtotal, tanto en la interfaz como al guardar. El comprobante muestra el desglose.

En una base anterior sin `servicios.mano_obra`, aplicar una sola vez `database/migrations/002_mano_obra.sql`. La migracion conserva los totales anteriores y obtiene su mano de obra restando las refacciones, con un minimo de cero. Los servicios historicos con total menor al subtotal conservan su importe almacenado; al editarlos se aplica la nueva regla de calculo.

Los errores de guardado de administradores y servicios conservan abiertos los formularios y sus datos. Al editar un administrador, una clave vacia conserva la anterior.
