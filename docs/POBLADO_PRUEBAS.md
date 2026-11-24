# Poblado de pruebas — main

Después de preparar el entorno y sus catálogos:

```bash
python scripts/poblar_pruebas.py
python scripts/poblar_pruebas.py --resumen
```

Genera por defecto 100 servicios con identificadores PRB-SRV-*, clientes,
vehículos, refacciones, recepciones y próximos servicios dedicados. Repetir
omite servicios ya registrados sin descontar sus piezas por segunda vez.

- `--cantidad N`: de 1 a 1000 servicios; predeterminado 100.
- `--fecha AAAA-MM-DD`: fecha base; predeterminada la fecha de ejecución.
- `--resumen`: consulta datos de prueba sin generar nuevos registros.

Los casos incluyen estados y tipos distintos, servicios con/sin piezas y
próximos mantenimientos en diferentes fechas. Ejemplo:
`python scripts/poblar_pruebas.py --cantidad 100 --fecha 2026-11-23`.

Este script escribe datos: usar una base propia. No se ejecutó durante la
preparación documental ni se alteró ninguna base de datos.
