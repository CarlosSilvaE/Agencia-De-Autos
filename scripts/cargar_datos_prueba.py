#!/usr/bin/env python3
"""Carga datos ficticios en Agencia de Automóviles (MySQL 8.4).

Uso, desde la raíz del proyecto y con .venv activado:
    python scripts/cargar_datos_prueba.py
    python scripts/cargar_datos_prueba.py --resumen
    python scripts/cargar_datos_prueba.py --limpiar

IMPORTANTE: --limpiar borra ÚNICAMENTE registros con identificadores
reservados para esta semilla de pruebas, tras pedir confirmación.
"""
from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
import sys

from dotenv import dotenv_values
import mysql.connector

ROOT = Path(__file__).resolve().parent.parent
PREFIX_FOLIO = "P2-DEMO-"
PREFIX_PLACAS = "P2D-"
PREFIX_SKU = "P2D-REF-"
PREFIX_MARCA = "Demo P2 - "
PREFIX_EMAIL = "p2demo-"

MARCAS_MODELOS = {
    "Toyota": ("Corolla", "RAV4"),
    "Nissan": ("Versa", "Sentra"),
    "Honda": ("Civic", "CR-V"),
    "Volkswagen": ("Jetta", "Virtus"),
    "Mazda": ("Mazda 3", "CX-5"),
}

REFACCIONES = (
    ("Filtro de aceite", "185.00"),
    ("Aceite sintetico 5W-30 (1 L)", "220.00"),
    ("Filtro de aire", "280.00"),
    ("Bujia de encendido", "145.00"),
    ("Balatas delanteras", "850.00"),
    ("Discos de freno", "1450.00"),
    ("Anticongelante (1 L)", "165.00"),
    ("Filtro de cabina", "210.00"),
    ("Bateria 12 V", "2350.00"),
    ("Banda de accesorios", "570.00"),
    ("Amortiguador delantero", "1780.00"),
    ("Liquido de frenos (500 ml)", "135.00"),
    ("Termostato", "420.00"),
    ("Sensor de oxigeno", "1280.00"),
    ("Limpiaparabrisas", "190.00"),
)

NOMBRES = ("Ana", "Luis", "Maria", "Carlos", "Sofia", "Jorge", "Elena", "Pedro", "Lucia", "Hector")
APELLIDOS = ("Lopez", "Garcia", "Martinez", "Ramirez", "Gonzalez", "Torres", "Hernandez", "Flores")
COLORES = ("Blanco", "Negro", "Gris", "Azul", "Rojo", "Plata")
TRABAJOS = (
    "Cambio de aceite y filtro",
    "Revision general y niveles",
    "Diagnostico de frenos y balatas",
    "Alineacion y suspension",
    "Revision de sistema electrico",
    "Servicio preventivo por kilometraje",
    "Correccion de falla de encendido",
    "Inspeccion de enfriamiento y fugas",
)
ESTADOS = ("En espera", "En proceso", "Finalizado")


def conectar():
    if not (ROOT / ".env").is_file():
        raise RuntimeError(f"No existe {ROOT / '.env'}. Configura el archivo antes de continuar.")
    env = dotenv_values(ROOT / ".env")
    needed = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD")
    if any(not env.get(k) for k in needed):
        raise RuntimeError("Faltan variables MYSQL_* en .env.")
    if not str(env["MYSQL_PORT"]).isdigit():
        raise RuntimeError("MYSQL_PORT debe ser un puerto numérico.")
    return mysql.connector.connect(
        host=env["MYSQL_HOST"],
        port=int(env["MYSQL_PORT"]),
        user=env["MYSQL_USER"],
        password=env["MYSQL_PASSWORD"],
        database=env["MYSQL_DATABASE"],
        connection_timeout=10,
        autocommit=False,
        charset="utf8mb4",
    )


def sembrar(connection):
    cursor = connection.cursor()
    cuentas = {"marcas": 0, "modelos": 0, "clientes": 0, "vehiculos": 0,
               "refacciones": 0, "servicios": 0, "entregas": 0,
               "servicio_refaccion": 0, "proximos_servicios": 0}

    def asegurar(nombre_tabla, sql_sel, sql_ins, busca, valores):
        cursor.execute(sql_sel, busca)
        fila = cursor.fetchone()
        if fila:
            return int(fila[0])
        cursor.execute(sql_ins, valores)
        cuentas[nombre_tabla] += 1
        return int(cursor.lastrowid)

    try:
        connection.start_transaction()
        # Catálogos. Marcas con prefijo, para no tocar marcas que ya registraste.
        combinaciones = []
        for nombre_marca, modelos in MARCAS_MODELOS.items():
            marca = PREFIX_MARCA + nombre_marca
            id_marca = asegurar("marcas", "SELECT id_marca FROM marcas WHERE nombre=%s",
                "INSERT INTO marcas (nombre) VALUES (%s)", (marca,), (marca,))
            for modelo in modelos:
                id_modelo = asegurar("modelos",
                    "SELECT id_modelo FROM modelos WHERE id_marca=%s AND nombre=%s",
                    "INSERT INTO modelos (id_marca,nombre) VALUES (%s,%s)",
                    (id_marca, modelo), (id_marca, modelo))
                combinaciones.append((id_marca, id_modelo))

        years = []
        for year in (2022, 2023, 2024, 2025, 2026):
            cursor.execute("SELECT id_ano FROM anos WHERE ano=%s", (year,))
            row = cursor.fetchone()
            if not row:
                # Compartido con el sistema: nunca se borra en --limpiar.
                cursor.execute("INSERT INTO anos (ano) VALUES (%s)", (year,))
                year_id = int(cursor.lastrowid)
            else:
                year_id = int(row[0])
            years.append(year_id)

        parts = []
        for i, (nombre, precio) in enumerate(REFACCIONES, 1):
            sku = f"{PREFIX_SKU}{i:03d}"
            ref_id = asegurar("refacciones", "SELECT id_refaccion FROM refacciones WHERE sku=%s",
                "INSERT INTO refacciones (nombre,sku,cantidad,precio) VALUES (%s,%s,%s,%s)",
                (sku,), (f"[DEMO] {nombre}", sku, 300, Decimal(precio)))
            parts.append((ref_id, Decimal(precio)))

        clientes = []
        for i in range(1, 26):
            nombre = NOMBRES[(i - 1) % len(NOMBRES)]
            paterno = APELLIDOS[(i * 3) % len(APELLIDOS)]
            materno = APELLIDOS[(i * 5 + 1) % len(APELLIDOS)]
            email = f"{PREFIX_EMAIL}{i:03d}@example.invalid"
            cliente = asegurar("clientes", "SELECT id_cliente FROM clientes WHERE email=%s",
                """INSERT INTO clientes
                   (nombre,apellido_paterno,apellido_materno,telefono,email)
                   VALUES (%s,%s,%s,%s,%s)""",
                (email,), (nombre, paterno, materno, f"844000{i:04d}", email))
            clientes.append((cliente, nombre, paterno))

        vehiculos = []
        for i in range(1, 31):
            id_cliente = clientes[(i - 1) % len(clientes)][0]
            id_marca, id_modelo = combinaciones[(i - 1) % len(combinaciones)]
            placas = f"{PREFIX_PLACAS}{i:04d}"
            vin = f"DEMOP2ABC{i:08d}"
            vehiculo = asegurar("vehiculos", "SELECT id_vehiculo FROM vehiculos WHERE placas=%s",
                """INSERT INTO vehiculos
                   (id_cliente,id_marca,id_modelo,id_ano,placas,color,vin)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (placas,), (id_cliente, id_marca, id_modelo,
                             years[(i - 1) % len(years)], placas,
                             COLORES[(i - 1) % len(COLORES)], vin))
            vehiculos.append((vehiculo, (i - 1) % len(clientes)))

        ahora = datetime.now().replace(second=0, microsecond=0)
        for i in range(1, 101):
            folio = f"{PREFIX_FOLIO}{i:04d}"
            cursor.execute("SELECT id_servicio FROM servicios WHERE folio=%s", (folio,))
            if cursor.fetchone():
                # Nunca sobreescribir modificaciones realizadas en la interfaz.
                continue
            id_vehiculo, cliente_pos = vehiculos[(i - 1) % len(vehiculos)]
            # Doce servicios con fecha de hoy para probar el filtro diario del dashboard.
            ingreso = (datetime.combine(ahora.date(), time(hour=8 + i % 11))
                       if i <= 12 else
                       ahora - timedelta(days=1 + (i * 7) % 120, hours=i % 8))
            fecha_programada = ingreso.date() + timedelta(days=1 + i % 12)
            estado = ESTADOS[(i - 1) % len(ESTADOS)]
            tipo = "Preventivo" if i % 2 else "Correctivo"
            descripcion = f"[DEMO] {TRABAJOS[(i - 1) % len(TRABAJOS)]}. Registro de prueba {i:03d}."
            costo = Decimal(450 + (i % 12) * 125)
            cursor.execute("""INSERT INTO servicios
                (folio,id_vehiculo,tipo_servicio,descripcion,fecha_ingreso,fecha_programada,estado,costo)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (folio, id_vehiculo, tipo, descripcion, ingreso,
                 fecha_programada, estado, costo))
            servicio_id = int(cursor.lastrowid)
            cuentas["servicios"] += 1

            cliente = clientes[cliente_pos]
            es_propietario = i % 4 != 0
            nombre_entrega = (f"{cliente[1]} {cliente[2]}" if es_propietario
                              else f"Familiar demo {i:03d}")
            cursor.execute("""INSERT INTO entregas
                (id_servicio,nombre_entrega,telefono,relacion_propietario,fecha,observaciones)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (servicio_id, nombre_entrega, f"844111{i:04d}",
                 "Propietario" if es_propietario else "Familiar",
                 ingreso, "[DEMO] Recepcion para probar seguimiento."))
            cuentas["entregas"] += 1

            indices_partes = [(i * 7) % len(parts)]
            if i % 3 == 0:
                indices_partes.append((i * 7 + 3) % len(parts))
            for indice in indices_partes:
                part_id, precio = parts[indice]
                cantidad = 1 + (i % 3)
                cursor.execute("""UPDATE refacciones SET cantidad=cantidad-%s
                               WHERE id_refaccion=%s AND activo=1 AND cantidad >= %s""",
                               (cantidad, part_id, cantidad))
                if cursor.rowcount != 1:
                    raise RuntimeError(f"Inventario insuficiente en refaccion ID {part_id}.")
                cursor.execute("""INSERT INTO servicio_refaccion
                    (id_servicio,id_refaccion,cantidad,precio_unitario)
                    VALUES (%s,%s,%s,%s)""",
                    (servicio_id, part_id, cantidad, precio))
                cuentas["servicio_refaccion"] += 1

            if i % 3 == 0:
                proxima = ahora.date() + timedelta(days=10 + (i * 5) % 181)
                cursor.execute("""INSERT INTO proximos_servicios
                    (id_servicio,fecha_programada,kilometraje,notas)
                    VALUES (%s,%s,%s,%s)""",
                    (servicio_id, proxima, 20000 + i * 250,
                     f"[DEMO] Recordatorio del folio {folio}"))
                cuentas["proximos_servicios"] += 1

        connection.commit()
        print("\nCarga completada. Registros NUEVOS por tabla:")
        for tabla, cantidad in cuentas.items():
            print(f"  {tabla:22s}: {cantidad}")
        print("\nSe conservaron los registros existentes y los DEMO previamente editados.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def resumen(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("""SELECT estado, COUNT(*) FROM servicios
                          WHERE folio LIKE %s GROUP BY estado ORDER BY estado""",
                       (PREFIX_FOLIO + "%",))
        estadisticas = cursor.fetchall()
        print("\nServicios DEMO por estado:")
        for estado, total in estadisticas:
            print(f"  {estado:15}: {total}")
        cursor.execute("SELECT COUNT(*) FROM servicios WHERE folio LIKE %s",
                       (PREFIX_FOLIO + "%",))
        print(f"  TOTAL: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE email LIKE %s",
                       (PREFIX_EMAIL + "%@example.invalid",))
        print(f"Clientes DEMO: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM vehiculos WHERE placas LIKE %s",
                       (PREFIX_PLACAS + "%",))
        print(f"Vehiculos DEMO: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM refacciones WHERE sku LIKE %s",
                       (PREFIX_SKU + "%",))
        print(f"Refacciones DEMO: {cursor.fetchone()[0]}")
    finally:
        cursor.close()


def limpiar(connection):
    print("ATENCION: se eliminaran permanentemente SOLO datos con prefijo de esta semilla:")
    print(f"  Folios {PREFIX_FOLIO}*, placas {PREFIX_PLACAS}*, SKU {PREFIX_SKU}*,")
    print(f"  marcas {PREFIX_MARCA}*, clientes {PREFIX_EMAIL}*@example.invalid.")
    print("Se restaurará al inventario el material asignado a servicios DEMO.")
    respuesta = input("Escribe BORRAR DEMO para continuar: ").strip()
    if respuesta != "BORRAR DEMO":
        print("Cancelado. No se modificó ningún registro.")
        return

    cursor = connection.cursor()
    try:
        connection.start_transaction()
        # Abortamos sin borrar nada si un servicio NO-DEMO usa un auto de pruebas.
        cursor.execute("""SELECT COUNT(*) FROM servicios s
            JOIN vehiculos v ON v.id_vehiculo=s.id_vehiculo
            WHERE v.placas LIKE %s AND s.folio NOT LIKE %s""",
            (PREFIX_PLACAS + "%", PREFIX_FOLIO + "%"))
        if cursor.fetchone()[0]:
            raise RuntimeError("Hay servicios reales o ajenos a la semilla vinculados a vehiculos DEMO. No se borró nada.")

        cursor.execute("""UPDATE refacciones r
            JOIN (SELECT sr.id_refaccion, SUM(sr.cantidad) AS total
                  FROM servicio_refaccion sr
                  JOIN servicios s ON s.id_servicio=sr.id_servicio
                  WHERE s.folio LIKE %s GROUP BY sr.id_refaccion) suma
            ON suma.id_refaccion=r.id_refaccion
            SET r.cantidad=r.cantidad+suma.total""", (PREFIX_FOLIO + "%",))
        for tabla in ("servicio_refaccion", "entregas", "proximos_servicios"):
            cursor.execute(f"""DELETE t FROM `{tabla}` t
                JOIN servicios s ON s.id_servicio=t.id_servicio
                WHERE s.folio LIKE %s""", (PREFIX_FOLIO + "%",))
        cursor.execute("DELETE FROM servicios WHERE folio LIKE %s", (PREFIX_FOLIO + "%",))
        cursor.execute("DELETE FROM vehiculos WHERE placas LIKE %s", (PREFIX_PLACAS + "%",))
        cursor.execute("DELETE FROM clientes WHERE email LIKE %s", (PREFIX_EMAIL + "%@example.invalid",))
        cursor.execute("DELETE FROM refacciones WHERE sku LIKE %s", (PREFIX_SKU + "%",))
        cursor.execute("DELETE FROM modelos WHERE id_marca IN (SELECT id_marca FROM marcas WHERE nombre LIKE %s)",
                       (PREFIX_MARCA + "%",))
        cursor.execute("DELETE FROM marcas WHERE nombre LIKE %s", (PREFIX_MARCA + "%",))
        connection.commit()
        print("Limpieza completada. Registros ajenos a la semilla conservados.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def main():
    parser = argparse.ArgumentParser(description="Datos de prueba de Agencia de Automoviles")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--resumen", action="store_true", help="Ver cantidad de datos DEMO")
    group.add_argument("--limpiar", action="store_true", help="Borrar datos DEMO con confirmación")
    args = parser.parse_args()
    try:
        connection = conectar()
        try:
            if args.resumen:
                resumen(connection)
            elif args.limpiar:
                limpiar(connection)
            else:
                sembrar(connection)
                resumen(connection)
        finally:
            connection.close()
    except (mysql.connector.Error, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
