CREATE TABLE IF NOT EXISTS administradores (
  id_administrador INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  usuario VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS marcas (
  id_marca INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL UNIQUE,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS modelos (
  id_modelo INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_marca INT UNSIGNED NOT NULL,
  nombre VARCHAR(100) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (id_marca) REFERENCES marcas(id_marca)
);

CREATE TABLE IF NOT EXISTS anios (
  id_anio INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  anio SMALLINT UNSIGNED NOT NULL UNIQUE,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS clientes (
  id_cliente INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  apellido_paterno VARCHAR(100) NOT NULL,
  apellido_materno VARCHAR(100),
  telefono VARCHAR(30),
  email VARCHAR(150),
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS vehiculos (
  id_vehiculo INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_cliente INT UNSIGNED NOT NULL,
  id_marca INT UNSIGNED NOT NULL,
  id_modelo INT UNSIGNED NOT NULL,
  id_anio INT UNSIGNED NOT NULL,
  placas VARCHAR(20) NOT NULL UNIQUE,
  color VARCHAR(50),
  vin VARCHAR(30),
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
  FOREIGN KEY (id_marca) REFERENCES marcas(id_marca),
  FOREIGN KEY (id_modelo) REFERENCES modelos(id_modelo),
  FOREIGN KEY (id_anio) REFERENCES anios(id_anio)
);

CREATE TABLE IF NOT EXISTS estados (
  id_estado INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(30) NOT NULL UNIQUE,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS servicios (
  id_servicio INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  folio VARCHAR(30) NOT NULL UNIQUE,
  id_vehiculo INT UNSIGNED NOT NULL,
  tipo_servicio VARCHAR(20) NOT NULL DEFAULT 'Correctivo',
  descripcion TEXT NOT NULL,
  fecha_ingreso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_programada DATE,
  estado VARCHAR(30) NOT NULL,
  costo DECIMAL(12,2) NOT NULL DEFAULT 0,
  mano_obra DECIMAL(12,2) NOT NULL DEFAULT 1500.00,
  FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo),
  CHECK (estado IN ('En espera', 'En proceso', 'Finalizado'))
);

CREATE TABLE IF NOT EXISTS entregas (
  id_entrega INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_servicio INT UNSIGNED NOT NULL,
  nombre_entrega VARCHAR(150) NOT NULL,
  telefono VARCHAR(30),
  relacion_propietario VARCHAR(100),
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  observaciones TEXT,
  FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
);

CREATE TABLE IF NOT EXISTS refacciones (
  id_refaccion INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  sku VARCHAR(50) UNIQUE,
  cantidad INT UNSIGNED NOT NULL DEFAULT 0,
  precio DECIMAL(12,2) NOT NULL DEFAULT 0,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS servicio_refaccion (
  id_servicio INT UNSIGNED NOT NULL,
  id_refaccion INT UNSIGNED NOT NULL,
  cantidad INT UNSIGNED NOT NULL,
  precio_unitario DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (id_servicio, id_refaccion),
  FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio),
  FOREIGN KEY (id_refaccion) REFERENCES refacciones(id_refaccion)
);

CREATE TABLE IF NOT EXISTS proximos_servicios (
  id_proximo_servicio INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_servicio INT UNSIGNED NOT NULL,
  fecha_programada DATE NOT NULL,
  kilometraje INT UNSIGNED,
  notas TEXT,
  FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
);

-- Catalogos iniciales. No generan clientes, vehiculos, servicios ni administradores.

-- Nombres reales. Precios MXN, existencias y SKU internos de ejemplo.

START TRANSACTION;

INSERT INTO estados (nombre)
SELECT seed.nombre
FROM (
  SELECT 'En espera' AS nombre
  UNION ALL
  SELECT 'En proceso'
  UNION ALL
  SELECT 'Finalizado'
) AS seed
LEFT JOIN estados AS existente ON existente.nombre=seed.nombre
WHERE existente.id_estado IS NULL;

INSERT INTO marcas (nombre)
SELECT seed.nombre
FROM (
  SELECT 'Nissan' AS nombre
  UNION ALL
  SELECT 'Toyota'
  UNION ALL
  SELECT 'Chevrolet'
  UNION ALL
  SELECT 'Volkswagen'
  UNION ALL
  SELECT 'Kia'
  UNION ALL
  SELECT 'Mazda'
  UNION ALL
  SELECT 'Honda'
  UNION ALL
  SELECT 'Ford'
  UNION ALL
  SELECT 'Hyundai'
  UNION ALL
  SELECT 'Renault'
) AS seed
LEFT JOIN marcas AS existente ON existente.nombre=seed.nombre
WHERE existente.id_marca IS NULL;

INSERT INTO modelos (id_marca, nombre)
SELECT marca.id_marca, seed.nombre
FROM (
  SELECT 'Nissan' AS marca, 'Versa' AS nombre
  UNION ALL
  SELECT 'Nissan', 'Sentra'
  UNION ALL
  SELECT 'Nissan', 'March'
  UNION ALL
  SELECT 'Nissan', 'Kicks'
  UNION ALL
  SELECT 'Nissan', 'Frontier'
  UNION ALL
  SELECT 'Toyota', 'Corolla'
  UNION ALL
  SELECT 'Toyota', 'Yaris'
  UNION ALL
  SELECT 'Toyota', 'Camry'
  UNION ALL
  SELECT 'Toyota', 'RAV4'
  UNION ALL
  SELECT 'Toyota', 'Hilux'
  UNION ALL
  SELECT 'Chevrolet', 'Aveo'
  UNION ALL
  SELECT 'Chevrolet', 'Onix'
  UNION ALL
  SELECT 'Chevrolet', 'Tracker'
  UNION ALL
  SELECT 'Chevrolet', 'Captiva'
  UNION ALL
  SELECT 'Chevrolet', 'Silverado'
  UNION ALL
  SELECT 'Volkswagen', 'Jetta'
  UNION ALL
  SELECT 'Volkswagen', 'Virtus'
  UNION ALL
  SELECT 'Volkswagen', 'Polo'
  UNION ALL
  SELECT 'Volkswagen', 'Taos'
  UNION ALL
  SELECT 'Volkswagen', 'Tiguan'
  UNION ALL
  SELECT 'Kia', 'Rio'
  UNION ALL
  SELECT 'Kia', 'K3'
  UNION ALL
  SELECT 'Kia', 'Forte'
  UNION ALL
  SELECT 'Kia', 'Seltos'
  UNION ALL
  SELECT 'Kia', 'Sportage'
  UNION ALL
  SELECT 'Mazda', 'Mazda2'
  UNION ALL
  SELECT 'Mazda', 'Mazda3'
  UNION ALL
  SELECT 'Mazda', 'CX-3'
  UNION ALL
  SELECT 'Mazda', 'CX-30'
  UNION ALL
  SELECT 'Mazda', 'CX-5'
  UNION ALL
  SELECT 'Honda', 'City'
  UNION ALL
  SELECT 'Honda', 'Civic'
  UNION ALL
  SELECT 'Honda', 'Accord'
  UNION ALL
  SELECT 'Honda', 'HR-V'
  UNION ALL
  SELECT 'Honda', 'CR-V'
  UNION ALL
  SELECT 'Ford', 'Mustang'
  UNION ALL
  SELECT 'Ford', 'Escape'
  UNION ALL
  SELECT 'Ford', 'Explorer'
  UNION ALL
  SELECT 'Ford', 'Ranger'
  UNION ALL
  SELECT 'Ford', 'Lobo'
  UNION ALL
  SELECT 'Hyundai', 'Grand i10'
  UNION ALL
  SELECT 'Hyundai', 'Accent'
  UNION ALL
  SELECT 'Hyundai', 'Elantra'
  UNION ALL
  SELECT 'Hyundai', 'Creta'
  UNION ALL
  SELECT 'Hyundai', 'Tucson'
  UNION ALL
  SELECT 'Renault', 'Kwid'
  UNION ALL
  SELECT 'Renault', 'Stepway'
  UNION ALL
  SELECT 'Renault', 'Logan'
  UNION ALL
  SELECT 'Renault', 'Duster'
  UNION ALL
  SELECT 'Renault', 'Oroch'
) AS seed
JOIN marcas AS marca ON marca.nombre=seed.marca
LEFT JOIN modelos AS existente ON existente.id_marca=marca.id_marca AND existente.nombre=seed.nombre
WHERE existente.id_modelo IS NULL;

INSERT INTO anios (anio)
SELECT seed.anio
FROM (
  SELECT 2015 AS anio
  UNION ALL
  SELECT 2016
  UNION ALL
  SELECT 2017
  UNION ALL
  SELECT 2018
  UNION ALL
  SELECT 2019
  UNION ALL
  SELECT 2020
  UNION ALL
  SELECT 2021
  UNION ALL
  SELECT 2022
  UNION ALL
  SELECT 2023
  UNION ALL
  SELECT 2024
  UNION ALL
  SELECT 2025
  UNION ALL
  SELECT 2026
) AS seed
LEFT JOIN anios AS existente ON existente.anio=seed.anio
WHERE existente.id_anio IS NULL;

INSERT INTO refacciones (nombre, sku, cantidad, precio)
SELECT seed.nombre, seed.sku, seed.cantidad, seed.precio
FROM (
  SELECT 'Bosch - Filtro de aceite Premium' AS nombre, 'CAT-BOS-001' AS sku, 30 AS cantidad, 180.00 AS precio
  UNION ALL
  SELECT 'Bosch - Filtro de aceite Workshop', 'CAT-BOS-002', 25, 140.00
  UNION ALL
  SELECT 'Bosch - Filtro de combustible', 'CAT-BOS-003', 20, 320.00
  UNION ALL
  SELECT 'Bosch - Bujia de niquel (pieza)', 'CAT-BOS-004', 80, 65.00
  UNION ALL
  SELECT 'Bosch - Bujia de platino (pieza)', 'CAT-BOS-005', 60, 140.00
  UNION ALL
  SELECT 'Bosch - Bujia de iridio (pieza)', 'CAT-BOS-006', 48, 230.00
  UNION ALL
  SELECT 'Bosch - Bobina de encendido', 'CAT-BOS-007', 12, 850.00
  UNION ALL
  SELECT 'Bosch - Juego de cables para bujias', 'CAT-BOS-008', 10, 650.00
  UNION ALL
  SELECT 'Bosch - Sensor de oxigeno', 'CAT-BOS-009', 10, 1150.00
  UNION ALL
  SELECT 'Bosch - Sensor MAP', 'CAT-BOS-010', 8, 780.00
  UNION ALL
  SELECT 'Bosch - Sensor de flujo de aire MAF', 'CAT-BOS-011', 6, 1850.00
  UNION ALL
  SELECT 'Bosch - Sensor de temperatura', 'CAT-BOS-012', 12, 380.00
  UNION ALL
  SELECT 'Bosch - Sensor de detonacion', 'CAT-BOS-013', 8, 620.00
  UNION ALL
  SELECT 'Bosch - Bomba electrica de combustible', 'CAT-BOS-014', 6, 1650.00
  UNION ALL
  SELECT 'Bosch - Alternador', 'CAT-BOS-015', 4, 3900.00
  UNION ALL
  SELECT 'Bosch - Motor de arranque', 'CAT-BOS-016', 4, 2800.00
  UNION ALL
  SELECT 'Bosch - Juego de pastillas de freno delanteras', 'CAT-BOS-017', 15, 890.00
  UNION ALL
  SELECT 'Bosch - Juego de pastillas de freno traseras', 'CAT-BOS-018', 12, 790.00
  UNION ALL
  SELECT 'Bosch - Disco de freno (pieza)', 'CAT-BOS-019', 16, 950.00
  UNION ALL
  SELECT 'Bosch - Pluma limpiaparabrisas Clear Advantage (pieza)', 'CAT-BOS-020', 24, 280.00
  UNION ALL
  SELECT 'Gates - Banda de accesorios Micro-V', 'CAT-GAT-001', 18, 420.00
  UNION ALL
  SELECT 'Gates - Kit de distribucion PowerGrip', 'CAT-GAT-002', 6, 2100.00
  UNION ALL
  SELECT 'Gates - Bomba de agua', 'CAT-GAT-003', 8, 1200.00
  UNION ALL
  SELECT 'Gates - Termostato', 'CAT-GAT-004', 15, 350.00
  UNION ALL
  SELECT 'Gates - Manguera moldeada de radiador', 'CAT-GAT-005', 12, 380.00
  UNION ALL
  SELECT 'Gates - Manguera de calefaccion', 'CAT-GAT-006', 10, 290.00
  UNION ALL
  SELECT 'Gates - Tensor de banda de accesorios', 'CAT-GAT-007', 8, 780.00
  UNION ALL
  SELECT 'Gates - Polea de accesorios', 'CAT-GAT-008', 10, 450.00
  UNION ALL
  SELECT 'Gates - Tapon de radiador', 'CAT-GAT-009', 20, 160.00
  UNION ALL
  SELECT 'Gates - Abrazadera para manguera (pieza)', 'CAT-GAT-010', 60, 35.00
) AS seed
LEFT JOIN refacciones AS existente ON existente.sku=seed.sku
WHERE existente.id_refaccion IS NULL;

-- Quitar acentos de los nombres ya cargados por este poblado, conservando precios y cantidades.
UPDATE refacciones
SET nombre = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(nombre, X'C3A1', 'a'), X'C3A9', 'e'), X'C3AD', 'i'), X'C3B3', 'o'), X'C3BA', 'u')
WHERE sku IN (
  'CAT-BOS-001', 'CAT-BOS-002', 'CAT-BOS-003', 'CAT-BOS-004', 'CAT-BOS-005', 'CAT-BOS-006', 'CAT-BOS-007', 'CAT-BOS-008', 'CAT-BOS-009', 'CAT-BOS-010', 'CAT-BOS-011', 'CAT-BOS-012', 'CAT-BOS-013', 'CAT-BOS-014', 'CAT-BOS-015', 'CAT-BOS-016', 'CAT-BOS-017', 'CAT-BOS-018', 'CAT-BOS-019', 'CAT-BOS-020', 'CAT-GAT-001', 'CAT-GAT-002', 'CAT-GAT-003', 'CAT-GAT-004', 'CAT-GAT-005', 'CAT-GAT-006', 'CAT-GAT-007', 'CAT-GAT-008', 'CAT-GAT-009', 'CAT-GAT-010'
);

COMMIT;
