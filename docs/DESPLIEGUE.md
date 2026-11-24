# Despliegue de main

Requiere Python compatible con requirements.txt, Docker con Compose y soporte
PySide6. La aplicación se ejecuta fuera de Docker; MySQL, dentro.

1. Crear/activar el entorno virtual e instalar requirements.txt.
2. Copiar .env.example a .env si no existe; completar valores propios.
3. Iniciar Docker y respaldar la base si se reutiliza un volumen existente.
4. Ejecutar `python scripts/preparar_entorno.py`.
5. Ejecutar `python main.py`.

El preparador carga la configuración de .env, inicia MySQL, sincroniza su cuenta
y prepara esquema, migraciones y catálogos. Normaliza los años a anios/id_anio/anio
y aplica mano_obra cuando falta. No usar la migración antigua 001 de otra copia.
El arranque normal no prepara el esquema completo ni renombra sus tablas.

Opcional: `python scripts/preparar_entorno.py --env-file RUTA`.
La contraseña root debe corresponder al volumen existente; recrear el contenedor
no la cambia. Si falla root pero la cuenta de la aplicación funciona, el
preparador permite continuar con esa cuenta.

DDL hace commit implícito: un error puede dejar pasos aplicados. Inspeccionar el
estado antes de una corrección manual. No borrar volúmenes para actualizar.
La contraseña administrativa inicial solo crea la primera cuenta.
No publicar .env, entornos ni respaldos. Ver [README](../README.md).
