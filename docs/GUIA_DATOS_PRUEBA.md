# Catálogos y datos de prueba — main

Ejecutar primero `python scripts/preparar_entorno.py`. Prepara el esquema y
catálogos incluidos en database/init.sql también en un volumen existente.

La semilla incluye 10 marcas, 50 modelos, 12 años y 30 refacciones. Conserva
registros anteriores y no reinicia inventario al repetir los INSERT. No crea
por sí sola clientes, vehículos ni servicios. Los nombres vigentes son
anios/id_anio/anio y servicios.mano_obra.

Para servicios ficticios usar [scripts/poblar_pruebas.py](POBLADO_PRUEBAS.md).
El script antiguo cargar_datos_prueba.py no es el flujo recomendado aquí.
Usar una base propia y respaldarla antes de cambios de esquema.
