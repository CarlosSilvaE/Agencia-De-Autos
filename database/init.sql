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

CREATE TABLE IF NOT EXISTS anos (
  id_ano INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ano SMALLINT UNSIGNED NOT NULL UNIQUE,
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
  id_ano INT UNSIGNED NOT NULL,
  placas VARCHAR(20) NOT NULL UNIQUE,
  color VARCHAR(50),
  vin VARCHAR(30),
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
  FOREIGN KEY (id_marca) REFERENCES marcas(id_marca),
  FOREIGN KEY (id_modelo) REFERENCES modelos(id_modelo),
  FOREIGN KEY (id_ano) REFERENCES anos(id_ano)
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

INSERT INTO estados (nombre) VALUES ('En espera'), ('En proceso'), ('Finalizado');
INSERT INTO anos (ano) VALUES (2022), (2023), (2024), (2025), (2026);
