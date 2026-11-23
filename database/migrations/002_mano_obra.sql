-- Ejecutar una sola vez en bases existentes sin la columna mano_obra.
-- Los cambios DDL confirman por separado; no recrean ni eliminan registros.
ALTER TABLE servicios ADD COLUMN mano_obra DECIMAL(12,2) NULL DEFAULT NULL AFTER costo;

-- Conservar los totales anteriores e inferir la mano de obra desde sus refacciones.
-- Los importes historicos menores al subtotal se conservan, con mano de obra cero.
UPDATE servicios s
LEFT JOIN (
  SELECT id_servicio, SUM(cantidad * precio_unitario) AS subtotal
  FROM servicio_refaccion GROUP BY id_servicio
) piezas ON piezas.id_servicio=s.id_servicio
SET s.mano_obra=GREATEST(0, s.costo-COALESCE(piezas.subtotal,0))
WHERE s.mano_obra IS NULL;

ALTER TABLE servicios MODIFY COLUMN mano_obra DECIMAL(12,2) NOT NULL DEFAULT 1500.00;
