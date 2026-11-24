# Guion de exposición — main e2ef677

Abrir [el UML](UML/UML_Clases_Completo.svg).

1. Presentar la aplicación de escritorio Python/PySide6 y MySQL en Docker.
2. Recorrer MVC: Vista → Controlador → AgencyModel → MySQLDatabase.
3. Explicar Singleton del proveedor (no conexión global) y Strategy total/diaria.
4. Crear cliente y vehículo; mostrar VIN automático o validación del manual.
5. Registrar mantenimiento preventivo con mensaje editable o correctivo con
   descripción manual. La mano de obra inicia en 1500 y es editable.
6. Buscar refacciones por nombre/SKU, seleccionarlas y verificar el total
   automático: mano de obra más cantidades por precio de cada refacción.
7. Mostrar recepción opcional y programación del próximo mantenimiento.
8. Buscar por folio/propietario, editar y cambiar estado. Revisar el dashboard.
9. Abrir comprobante y guardar PDF con mano de obra, piezas y total.
10. Con datos propios, demostrar eliminación y restitución de inventario.
11. Mostrar participación real y cierre de sesión.

La preparación previa usa scripts/preparar_entorno.py; main.py no migra el
esquema completo. La base usa anios/id_anio/anio y servicios.mano_obra.
El modelo relacional es una entrega separada. Las pruebas unitarias no
sustituyen la demostración con MySQL en la máquina del salón.
