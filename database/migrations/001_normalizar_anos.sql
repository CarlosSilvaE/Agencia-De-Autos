-- Aplicar solo a la base inspeccionada, con respaldo y las aplicaciones cerradas.
-- MySQL confirma cada DDL; estas instrucciones no se revierten con ROLLBACK.
-- No ejecutar si ya existe anos o si los nombres originales son diferentes.
USE agencia_autos;

RENAME TABLE anio TO anos;
ALTER TABLE anos RENAME COLUMN id_anio TO id_ano;
ALTER TABLE anos RENAME COLUMN anio TO ano;
ALTER TABLE vehiculos RENAME COLUMN id_anio TO id_ano;

-- MySQL debe conservar y actualizar la referencia de la clave foránea.
SHOW CREATE TABLE anos;
SHOW CREATE TABLE vehiculos;
SELECT COUNT(*) AS anos_conservados FROM anos;
SELECT COUNT(*) AS vehiculos_conservados FROM vehiculos;
SELECT COUNT(*) AS servicios_conservados FROM servicios;
SELECT COUNT(*) AS vehiculos_sin_ano
FROM vehiculos v LEFT JOIN anos a ON a.id_ano=v.id_ano
WHERE a.id_ano IS NULL;
