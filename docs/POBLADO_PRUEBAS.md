# Poblado para pruebas funcionales

El script `scripts/poblar_pruebas.py` carga por defecto **100 servicios**. Genera tambien los registros relacionados; no significa 100 filas totales entre todas las tablas.

Requiere la base iniciada, `.env` configurado y los catalogos de `database/init.sql` ya cargados. No recrea tablas ni cambia administradores.

## Ejecutar

Desde la raiz del proyecto:

```powershell
.\venv\Scripts\python.exe scripts/poblar_pruebas.py
```

Si tu entorno se llama `.venv`, sustituye `venv` por `.venv`.

Para consultar solamente los registros de esta semilla:

```powershell
.\venv\Scripts\python.exe scripts/poblar_pruebas.py --resumen
```

Puedes elegir cuantos servicios generar (1 a 1000) y una fecha base:

```powershell
.\venv\Scripts\python.exe scripts/poblar_pruebas.py --cantidad 100 --fecha 2026-11-12
```

La primera carga predeterminada genera:

- 25 clientes ficticios y 30 vehiculos con VIN de prueba compatibles con la validacion actual.
- 15 refacciones de prueba con inventario propio, mas una sin existencias y otra con una sola unidad.
- 100 servicios: 34 En espera, 33 En proceso y 33 Finalizado.
- 12 ingresos en la fecha base (cuatro por estado) y 88 en dias anteriores.
- Servicios preventivos y correctivos, con cero, una, dos o tres refacciones.
- 110 registros de recepcion: 100 recepciones actuales y diez entradas previas para probar el historial.
- 180 asociaciones entre servicios y refacciones, con cantidades descontadas del inventario de prueba.
- 50 proximos servicios: fechas vencidas, de hoy y futuras.

Los datos son ficticios y no contienen acentos. Las placas `PRB-*`, correos `prb.cliente.*@example.invalid`, folios `PRB-SRV-*` y SKU `PRB-REF-*` identifican exclusivamente esta semilla. Los VIN son identificadores de prueba, no numeros asignados por un fabricante. No se agregan telefonos personales.

Los servicios nuevos del poblado usan mano de obra de 1500 y suman automaticamente las refacciones seleccionadas. Los servicios de prueba anteriores conservan sus importes al repetir la carga. Si tu base aun no tiene `servicios.mano_obra`, aplicar primero `database/migrations/002_mano_obra.sql`.

## Repetir la carga

Los identificadores son estables. Los servicios que ya existen se omiten: no se cambian sus estados, fechas, recepciones o refacciones ni se vuelve a descontar inventario. Tambien se conservan las ediciones de los clientes, vehiculos y refacciones existentes. Los registros de prueba eliminados pueden volver a crearse al repetir la carga. Reducir `--cantidad` no elimina servicios anteriores.

La carga usa una sola transaccion. Ante un error se revierten todas las inserciones y los descuentos de esa ejecucion. Un bloqueo de MySQL impide ejecutar dos poblados simultaneamente. Las refacciones de catalogo originales se usan como referencia de nombres y precios; el inventario que se descuenta pertenece a las piezas `PRB-REF-*`.

Las dos piezas especiales para probar existencias no se asignan automaticamente a servicios. Si modificas o agotas inventario de prueba y luego solicitas nuevos servicios, puede aparecer el error de existencia insuficiente; el script no repone cantidades automaticamente.

Si un cliente o vehiculo de prueba esta desactivado, se requiere reactivarlo antes de generar servicios nuevos que lo utilicen.

## Casos para probar en la aplicacion

1. **Busqueda:** consultar `PRB-SRV-0001`, o buscar propietarios como Ana y Luis.
2. **Dashboard:** revisar Total y Por fecha con la fecha base. Comparar los tres estados; los registros anteriores de la base tambien pueden participar en los totales.
3. **Servicios:** editar descripcion, mano de obra o estado, cerrar y buscar de nuevo para comprobar persistencia. El total se calcula automaticamente.
4. **Refacciones:** seleccionar varias piezas y comprobar cantidades. Intentar utilizar `PRB-REF-CERO` o solicitar dos unidades de `PRB-REF-UNO`: debe mostrar error sin guardar ni cerrar el formulario.
5. **Recepcion:** abrir `PRB-SRV-0010`, consultar Historial recepcion y comparar propietario con el familiar que entrega el auto.
6. **Proximos servicios:** consultar todos, filtrar por folio/propietario y revisar casos vencidos, de hoy y futuros.
7. **Comprobantes:** abrir uno con refacciones y otro sin ellas, guardar PDF e imprimir si tienes impresora.
8. **Inventario:** anotar la existencia de una pieza de prueba, modificar su cantidad en un servicio y verificar el ajuste. Eliminar ese servicio y confirmar que se restituyan sus piezas.
9. **Validaciones:** dejar vacia la descripcion o probar cantidades mayores al inventario disponible: debe mostrar error. La recepcion puede dejarse vacia y debe permitir guardar. Cambiar mano de obra, cantidades y precios para comprobar el total automatico.
10. **Clientes y vehiculos:** crear, editar y desactivar registros de prueba desde su modulo. Los servicios relacionados ayudan a comprobar el comportamiento de los datos historicos.

Este poblado prepara escenarios; no sustituye las pruebas manuales ni demuestra por si solo que todos los casos esten resueltos. El script no incluye una limpieza automatica ni elimina datos anteriores.
