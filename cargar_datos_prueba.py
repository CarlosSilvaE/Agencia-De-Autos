#!/usr/bin/env python3
"""Carga datos de ejemplo en Agencia de Automoviles (MySQL 8.4).

Uso, desde la raiz del proyecto y con .venv activado:
    python cargar_datos_prueba.py
    python cargar_datos_prueba.py --resumen
    python cargar_datos_prueba.py --limpiar

IMPORTANTE: --limpiar borra unicamente registros con identificadores
reservados para esta carga, tras pedir confirmacion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
import sys

from dotenv import dotenv_values
import mysql.connector

ROOT = Path(__file__).resolve().parent
PREFIX_FOLIO = "SRV-2026-"
PREFIX_PLACAS = "JAL-"
PREFIX_SKU = "CAT-AUT-"

MARCAS_MODELOS = {
    "Nissan": ("Versa", "Sentra", "March", "Kicks", "Frontier"),
    "Toyota": ("Corolla", "Yaris", "Camry", "RAV4", "Hilux"),
    "Chevrolet": ("Aveo", "Onix", "Tracker", "Captiva", "Silverado"),
    "Volkswagen": ("Jetta", "Virtus", "Polo", "Taos", "Tiguan"),
    "Kia": ("Rio", "K3", "Forte", "Seltos", "Sportage"),
    "Mazda": ("Mazda2", "Mazda3", "CX-3", "CX-30", "CX-5"),
    "Honda": ("City", "Civic", "Accord", "HR-V", "CR-V"),
    "Ford": ("Mustang", "Escape", "Explorer", "Ranger", "Lobo"),
    "Hyundai": ("Grand i10", "Accent", "Elantra", "Creta", "Tucson"),
    "Renault": ("Kwid", "Stepway", "Logan", "Duster", "Oroch"),
}

REFACCIONES = (
    ("Aceite 5W-30 (1 L)", "ACE-5W30-1L", "220.00"),
    ("Filtro de aceite", "FIL-ACE-001", "185.00"),
    ("Filtro de aire", "FIL-AIR-001", "280.00"),
    ("Bujia", "BUJ-ENC-001", "145.00"),
    ("Balatas delanteras", "BAL-DEL-001", "850.00"),
    ("Disco de freno", "DIS-FRE-001", "950.00"),
    ("Anticongelante (1 L)", "ANT-REF-001", "165.00"),
    ("Filtro de cabina", "FIL-CAB-001", "210.00"),
    ("Bateria 12 V", "BAT-12V-001", "2350.00"),
    ("Banda de accesorios", "BAN-ACC-001", "570.00"),
    ("Amortiguador delantero", "AMO-DEL-001", "1780.00"),
    ("Liquido de frenos", "LIQ-FRE-001", "135.00"),
    ("Termostato", "TER-REF-001", "420.00"),
    ("Sensor de oxigeno", "SEN-OXI-001", "1280.00"),
    ("Plumas limpiaparabrisas", "LIM-PAR-001", "190.00"),
)

CLIENTES = (
    ("Ana", "Lopez", "Garcia"),
    ("Luis", "Martinez", "Hernandez"),
    ("Maria Fernanda", "Garcia", "Torres"),
    ("Carlos", "Ramirez", "Flores"),
    ("Sofia", "Gonzalez", "Mendoza"),
    ("Jorge", "Hernandez", "Castillo"),
    ("Elena", "Torres", "Morales"),
    ("Pedro", "Flores", "Ortiz"),
    ("Lucia", "Mendoza", "Cruz"),
    ("Hector", "Castillo", "Reyes"),
    ("Valeria", "Morales", "Ramos"),
    ("Diego", "Ortiz", "Vargas"),
    ("Andrea", "Cruz", "Jimenez"),
    ("Miguel", "Reyes", "Navarro"),
    ("Daniela", "Ramos", "Aguilar"),
    ("Fernando", "Vargas", "Romero"),
    ("Paola", "Jimenez", "Herrera"),
    ("Ricardo", "Navarro", "Medina"),
    ("Gabriela", "Aguilar", "Silva"),
    ("Alejandro", "Romero", "Delgado"),
    ("Natalia", "Herrera", "Rojas"),
    ("Roberto", "Medina", "Cortes"),
    ("Mariana", "Silva", "Molina"),
    ("Eduardo", "Delgado", "Santos"),
    ("Camila", "Rojas", "Guerrero"),
)
COLORES = ("Blanco", "Negro", "Gris", "Azul", "Rojo", "Plata")
TRABAJOS = (
    "Cambio de aceite y filtro",
    "Revision de niveles y puntos de seguridad",
    "Cambio de balatas delanteras",
    "Alineacion y revision de suspension",
    "Diagnostico del sistema electrico",
    "Servicio preventivo por kilometraje",
    "Revision del sistema de encendido",
    "Revision del sistema de enfriamiento",
)
ESTADOS = ("En espera", "En proceso", "Finalizado")
VIN_PREFIX = {
    "Toyota": "2T1",
    "Nissan": "3N1",
    "Chevrolet": "3G1",
    "Volkswagen": "3VW",
    "Kia": "3KP",
    "Mazda": "3MZ",
    "Honda": "3HG",
    "Ford": "3FA",
    "Hyundai": "3KM",
    "Renault": "3FR",
}


def conectar():
    if not (ROOT / ".env").is_file():
        raise RuntimeError(f"No existe {ROOT / '.env'}. Configura el archivo antes de continuar.")
    env = dotenv_values(ROOT / ".env")
    needed = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD")
    if any(not env.get(k) for k in needed):
        raise RuntimeError("Faltan variables MYSQL_* en .env.")
    if not str(env["MYSQL_PORT"]).isdigit():
        raise RuntimeError("MYSQL_PORT debe ser un puerto numerico.")
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


def email_cliente(indice, nombre, paterno):
    nombre_email = nombre.replace(" ", ".").lower()
    return f"{nombre_email}.{paterno.lower()}.{indice:02d}@gmail.com"


def folios_semilla():
    return [f"{PREFIX_FOLIO}{i:04d}" for i in range(1, 101)]


def placas_semilla():
    return [f"{PREFIX_PLACAS}{100 + i:03d}-A" for i in range(1, 31)]


def emails_semilla():
    return [
        email_cliente(i, nombre, paterno)
        for i, (nombre, paterno, _) in enumerate(CLIENTES, 1)
    ]


def lista_sql(valores):
    return ",".join("%s" for _ in valores)


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
        combinaciones = []
        for nombre_marca, modelos in MARCAS_MODELOS.items():
            id_marca = asegurar(
                "marcas", "SELECT id_marca FROM marcas WHERE nombre=%s",
                "INSERT INTO marcas (nombre) VALUES (%s)",
                (nombre_marca,), (nombre_marca,),
            )
            for modelo in modelos:
                id_modelo = asegurar(
                    "modelos",
                    "SELECT id_modelo FROM modelos WHERE id_marca=%s AND nombre=%s",
                    "INSERT INTO modelos (id_marca,nombre) VALUES (%s,%s)",
                    (id_marca, modelo), (id_marca, modelo),
                )
                combinaciones.append((id_marca, id_modelo))

        years = []
        for year in range(2015, 2027):
            cursor.execute("SELECT id_anio FROM anio WHERE anio=%s", (year,))
            row = cursor.fetchone()
            if not row:
                cursor.execute("INSERT INTO anio (anio) VALUES (%s)", (year,))
                year_id = int(cursor.lastrowid)
            else:
                year_id = int(row[0])
            years.append(year_id)

        parts = []
        for nombre, sku_corto, precio in REFACCIONES:
            sku = f"{PREFIX_SKU}{sku_corto}"
            ref_id = asegurar(
                "refacciones",
                "SELECT id_refaccion FROM refacciones WHERE sku=%s",
                "INSERT INTO refacciones (nombre,sku,cantidad,precio) VALUES (%s,%s,%s,%s)",
                (sku,), (nombre, sku, 300, Decimal(precio)),
            )
            parts.append((ref_id, Decimal(precio)))

        clientes = []
        for i, (nombre, paterno, materno) in enumerate(CLIENTES, 1):
            email = email_cliente(i, nombre, paterno)
            cliente = asegurar(
                "clientes", "SELECT id_cliente FROM clientes WHERE email=%s",
                """INSERT INTO clientes
                   (nombre,apellido_paterno,apellido_materno,telefono,email)
                   VALUES (%s,%s,%s,%s,%s)""",
                (email,), (nombre, paterno, materno, f"844{2000000 + i:07d}", email),
            )
            clientes.append((cliente, nombre, paterno))

        vehiculos = []
        for i in range(1, 31):
            id_cliente = clientes[(i - 1) % len(clientes)][0]
            id_marca, id_modelo = combinaciones[(i - 1) % len(combinaciones)]
            placas = f"{PREFIX_PLACAS}{100 + i:03d}-A"
            nombre_marca = list(MARCAS_MODELOS)[(i - 1) % len(MARCAS_MODELOS)]
            vin = f"{VIN_PREFIX[nombre_marca]}{i * 7919:014d}"
            vehiculo = asegurar(
                "vehiculos",
                "SELECT id_vehiculo FROM vehiculos WHERE placas=%s",
                """INSERT INTO vehiculos
                   (id_cliente,id_marca,id_modelo,id_anio,placas,color,vin)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (placas,),
                (id_cliente, id_marca, id_modelo, years[(i - 1) % len(years)],
                 placas, COLORES[(i - 1) % len(COLORES)], vin),
            )
            vehiculos.append((vehiculo, (i - 1) % len(clientes)))

        ahora = datetime.now().replace(second=0, microsecond=0)
        for i, folio in enumerate(folios_semilla(), 1):
            cursor.execute("SELECT id_servicio FROM servicios WHERE folio=%s", (folio,))
            if cursor.fetchone():
                continue
            id_vehiculo, cliente_pos = vehiculos[(i - 1) % len(vehiculos)]
            ingreso = (
                datetime.combine(ahora.date(), time(hour=8 + i % 11))
                if i <= 12
                else ahora - timedelta(days=1 + (i * 7) % 120, hours=i % 8)
            )
            fecha_programada = ingreso.date() + timedelta(days=1 + i % 12)
            estado = ESTADOS[(i - 1) % len(ESTADOS)]
            tipo = "Preventivo" if i % 2 else "Correctivo"
            descripcion = TRABAJOS[(i - 1) % len(TRABAJOS)] + "."
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
            if es_propietario:
                nombre_entrega = f"{cliente[1]} {cliente[2]}"
                telefono_entrega = f"844{2000000 + cliente_pos + 1:07d}"
                relacion = "Propietario"
            else:
                familiar = clientes[(cliente_pos + 1) % len(clientes)]
                nombre_entrega = f"{familiar[1]} {familiar[2]}"
                telefono_entrega = f"844{2000000 + ((cliente_pos + 1) % len(clientes)) + 1:07d}"
                relacion = "Familiar"
            cursor.execute("""INSERT INTO entregas
                (id_servicio,nombre_entrega,telefono,relacion_propietario,fecha,observaciones)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (servicio_id, nombre_entrega, telefono_entrega, relacion,
                 ingreso, "Recepcion y revision inicial del vehiculo."))
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
                     f"Proximo mantenimiento preventivo del vehiculo."))
                cuentas["proximos_servicios"] += 1

        connection.commit()
        print("\nCarga completada. Registros nuevos por tabla:")
        for tabla, cantidad in cuentas.items():
            print(f"  {tabla:22s}: {cantidad}")
        print("\nSe conservaron los registros existentes y sus cambios.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def resumen(connection):
    cursor = connection.cursor()
    folios = folios_semilla()
    emails = emails_semilla()
    placas = placas_semilla()
    skus = [f"{PREFIX_SKU}{sku}" for _, sku, _ in REFACCIONES]
    try:
        cursor.execute(
            f"""SELECT estado, COUNT(*) FROM servicios
                WHERE folio IN ({lista_sql(folios)})
                GROUP BY estado ORDER BY estado""",
            tuple(folios),
        )
        estadisticas = cursor.fetchall()
        print("\nServicios de la carga por estado:")
        for estado, total in estadisticas:
            print(f"  {estado:15}: {total}")
        cursor.execute(
            f"SELECT COUNT(*) FROM servicios WHERE folio IN ({lista_sql(folios)})",
            tuple(folios),
        )
        print(f"  TOTAL: {cursor.fetchone()[0]}")
        cursor.execute(
            f"SELECT COUNT(*) FROM clientes WHERE email IN ({lista_sql(emails)})",
            tuple(emails),
        )
        print(f"Clientes: {cursor.fetchone()[0]}")
        cursor.execute(
            f"SELECT COUNT(*) FROM vehiculos WHERE placas IN ({lista_sql(placas)})",
            tuple(placas),
        )
        print(f"Vehiculos: {cursor.fetchone()[0]}")
        cursor.execute(
            f"SELECT COUNT(*) FROM refacciones WHERE sku IN ({lista_sql(skus)})",
            tuple(skus),
        )
        print(f"Refacciones: {cursor.fetchone()[0]}")
    finally:
        cursor.close()


def limpiar(connection):
    folios = folios_semilla()
    placas = placas_semilla()
    emails = emails_semilla()
    print("ATENCION: se eliminaran los servicios, vehiculos y clientes de esta carga.")
    print("Las refacciones y los catalogos compartidos se conservaran.")
    respuesta = input("Escribe BORRAR CARGA para continuar: ").strip()
    if respuesta != "BORRAR CARGA":
        print("Cancelado. No se modifico ningun registro.")
        return

    cursor = connection.cursor()
    try:
        connection.start_transaction()
        cursor.execute(f"""SELECT COUNT(*) FROM servicios s
            JOIN vehiculos v ON v.id_vehiculo=s.id_vehiculo
            WHERE v.placas IN ({lista_sql(placas)})
              AND s.folio NOT IN ({lista_sql(folios)})""",
            tuple(placas + folios))
        if cursor.fetchone()[0]:
            raise RuntimeError(
                "Hay servicios ajenos a esta carga vinculados a sus vehiculos. No se borro nada."
            )

        cursor.execute(f"""UPDATE refacciones r
            JOIN (SELECT sr.id_refaccion, SUM(sr.cantidad) AS total
                  FROM servicio_refaccion sr
                  JOIN servicios s ON s.id_servicio=sr.id_servicio
                  WHERE s.folio IN ({lista_sql(folios)})
                  GROUP BY sr.id_refaccion) suma
            ON suma.id_refaccion=r.id_refaccion
            SET r.cantidad=r.cantidad+suma.total""", tuple(folios))
        for tabla in ("servicio_refaccion", "entregas", "proximos_servicios"):
            cursor.execute(f"""DELETE t FROM `{tabla}` t
                JOIN servicios s ON s.id_servicio=t.id_servicio
                WHERE s.folio IN ({lista_sql(folios)})""", tuple(folios))
        cursor.execute(
            f"DELETE FROM servicios WHERE folio IN ({lista_sql(folios)})",
            tuple(folios),
        )
        cursor.execute(
            f"DELETE FROM vehiculos WHERE placas IN ({lista_sql(placas)})",
            tuple(placas),
        )
        cursor.execute(
            f"DELETE FROM clientes WHERE email IN ({lista_sql(emails)})",
            tuple(emails),
        )
        connection.commit()
        print("Limpieza completada. Catalogos y refacciones conservados.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def main():
    parser = argparse.ArgumentParser(description="Carga de datos para Agencia de Automoviles")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--resumen", action="store_true", help="Ver cantidad de datos cargados")
    group.add_argument("--limpiar", action="store_true", help="Borrar los datos cargados")
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
