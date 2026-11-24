# UML de clases de main

Base: `e2ef6770cefa2d685fbfbc6f7d3aa782f6cf97d5`, revisada el 23-11-2026.

- [Fuente PlantUML](UML_Clases_Completo.puml).
- [SVG vectorial con zoom](UML_Clases_Completo.svg).

Representa las 34 clases de models/, controllers/, views/ y ConfigurationError
(configuration.py). Se seleccionan atributos y métodos; no es un inventario
exhaustivo de miembros. No incluye librerías, pruebas ni clases de scripts.
Las funciones libres de configuración y migración no se inventan como clases.
Se cotejaron clases y nombres de métodos contra el AST de main.

Incluye MVC, Singleton, Strategy, comprobantes, diálogos y gráfica. ServiceDialog
muestra búsqueda de piezas y cálculo del total; ServiceReceipt incluye labor.
ReceiptDialog solo ofrece guardar PDF: se retiró print_receipt del UML.
Los atributos públicos usan +; los internos por convención, -.
Las asociaciones representan referencias; las dependencias, uso. La composición
expresa contención conceptual en Qt y agrupación de los controladores creados
por from_model; no demuestra propiedad exclusiva de objetos Python.

## Zoom

Extensión VS Code: PlantUML de jebbs, ID jebbs.plantuml.
Abrir el .puml, Alt+D, Ctrl + rueda para zoom, botón derecho para desplazar.
Java y Graphviz permiten generación local. El SVG se abre sin regenerar.

El modelo relacional anterior no se copia: usa anos/id_ano y no refleja
anios/id_anio ni mano_obra de main. Lo actualizará la persona encargada.
Los diagramas anteriores y la carpeta de trabajo original no se modificaron.

## Verificación de esta entrega

Se ejecutó la suite de main con Qt offscreen: 81 pruebas detectadas, 78
aprobadas y 3 de integración MySQL omitidas. No se conectó a la base ni se
aplicaron migraciones. La sintaxis PlantUML, el SVG y los enlaces locales
se validaron. El código, SQL, pruebas y configuración de main se conservaron
byte a byte; únicamente se añadieron documentos y se ajustaron referencias
documentales del README. La plantilla de responsabilidades requiere nombres
y contribuciones reales del equipo.
