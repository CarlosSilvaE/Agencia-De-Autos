# Agencia de Automóviles — datos de prueba para Parcial 2

Este complemento **no cambia las clases, vistas ni tablas** del proyecto; agrega registros en la base MySQL existente y usa el `.env` de la raíz.

## Requisitos

- Estar en `~/Proyecto-Agencia/Agencia_De_Automoviles` (la carpeta donde funciona `main.py`).
- Docker Desktop y el contenedor MySQL encendidos (`docker compose ps`).
- Entorno virtual activo (`source .venv/bin/activate`).
- Tener `mysql-connector-python` y `python-dotenv` instalados (`pip install -r requirements.txt`).

## Sembrar

```bash
python scripts/cargar_datos_prueba.py
```

Se crean, si aún no existen:

- 5 marcas de prueba (`Demo P2 - *`) y 10 modelos.
- 25 clientes (`p2demo-*@example.invalid`) y 30 vehículos (`P2D-*`).
- 15 refacciones de prueba (`P2D-REF-*`).
- **100 servicios** (`P2-DEMO-0001` al `P2-DEMO-0100`), distribuidos en 34 `En espera`, 33 `En proceso` y 33 `Finalizado`.
- 100 entregas, 133 asignaciones de refacciones y 33 próximos servicios.
- 12 servicios tienen la fecha actual para probar el filtro diario del Dashboard (4 por estado).

La primera carga produce **451 filas** adicionales, sin contar años ya existentes. Los importes y nombres son ficticios. Los administradores existentes no se modifican. La semilla no modifica registros existentes con estos identificadores (lo que hayas editado en la GUI se conserva) y no duplica filas al volver a ejecutarla.

## Consultar

```bash
python scripts/cargar_datos_prueba.py --resumen
```

Consulta adicional desde Docker, sin compartir la contraseña:

```bash
docker compose exec database mysql -u agencia -p agencia_autos -e "SELECT estado, COUNT(*) AS total FROM servicios GROUP BY estado;"
```

En la app pulsa **Actualizar** en la pestaña **Resumen** y selecciona **Total** o **Día** con la fecha de hoy. En **Servicios**, busca `P2-DEMO-0001`. En **Clientes y vehículos**, observa las placas `P2D-0001`, etc.

## Eliminar solo los datos de prueba

```bash
python scripts/cargar_datos_prueba.py --limpiar
```

La limpieza pide escribir **BORRAR DEMO** y trabaja dentro de una sola transacción. Solo borra las filas con los identificadores anteriores y sus registros dependientes, y restaura el inventario asignado a los servicios de prueba. Si hay datos ajenos a esta semilla enlazados a vehículos, marcas o refacciones de prueba, MySQL puede rechazar la limpieza y la transacción se revierte.

> Esta acción borra los datos de prueba permanentemente. Haz un respaldo si has hecho pruebas que quieres conservar. Si cambias manualmente un identificador reservado (folio, placa, SKU, correo o marca), esa fila podría no ser identificada por la limpieza.

## Precauciones

- Ejecutar únicamente en una **base de desarrollo/pruebas**, nunca de producción.
- No subir `.env` ni credenciales reales al repositorio.
- No ejecutar `docker compose down -v`: eso borraría el volumen MySQL completo, incluidos registros ajenos a este complemento.
