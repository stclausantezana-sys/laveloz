/* =====================================================================
   Currier La Veloz SRL - Tarifas de todas las rutas
   Para una base LaVelozDB que YA EXISTE (creada con la versión anterior del
   script, que solo traía Santa Cruz -> La Paz).
   Agrega las tarifas que falten entre Santa Cruz, La Paz y Cochabamba,
   en los dos sentidos, para los 3 tipos y las 2 formas de envío.
   No duplica ni cambia las tarifas que ya existen: se puede correr varias veces.
   Uso: abrir en SSMS y pulsar F5.
   ===================================================================== */
USE LaVelozDB;
GO

INSERT INTO Tarifa (id_ciudad_origen, id_ciudad_destino, id_tipo, forma_envio,
                    precio_por_kilo, umbral_volumen_m3, recargo_volumen)
SELECT co.id_ciudad, cd.id_ciudad, te.id_tipo, v.forma, v.precio, 0.050, v.recargo
FROM (VALUES
    (N'Santa Cruz de la Sierra', N'La Paz', N'Sobres-Documentos', 'TERRESTRE', 50.00, 10.00),
    (N'Santa Cruz de la Sierra', N'La Paz', N'Alimentos', 'TERRESTRE', 2.00, 10.00),
    (N'Santa Cruz de la Sierra', N'La Paz', N'Otros', 'TERRESTRE', 3.00, 10.00),
    (N'Santa Cruz de la Sierra', N'La Paz', N'Sobres-Documentos', 'AEREO', 70.00, 0.00),
    (N'Santa Cruz de la Sierra', N'La Paz', N'Alimentos', 'AEREO', 5.00, 0.00),
    (N'Santa Cruz de la Sierra', N'La Paz', N'Otros', 'AEREO', 6.00, 0.00),
    (N'La Paz', N'Santa Cruz de la Sierra', N'Sobres-Documentos', 'TERRESTRE', 50.00, 10.00),
    (N'La Paz', N'Santa Cruz de la Sierra', N'Alimentos', 'TERRESTRE', 2.00, 10.00),
    (N'La Paz', N'Santa Cruz de la Sierra', N'Otros', 'TERRESTRE', 3.00, 10.00),
    (N'La Paz', N'Santa Cruz de la Sierra', N'Sobres-Documentos', 'AEREO', 70.00, 0.00),
    (N'La Paz', N'Santa Cruz de la Sierra', N'Alimentos', 'AEREO', 5.00, 0.00),
    (N'La Paz', N'Santa Cruz de la Sierra', N'Otros', 'AEREO', 6.00, 0.00),
    (N'Santa Cruz de la Sierra', N'Cochabamba', N'Sobres-Documentos', 'TERRESTRE', 40.00, 8.00),
    (N'Santa Cruz de la Sierra', N'Cochabamba', N'Alimentos', 'TERRESTRE', 1.50, 8.00),
    (N'Santa Cruz de la Sierra', N'Cochabamba', N'Otros', 'TERRESTRE', 2.50, 8.00),
    (N'Santa Cruz de la Sierra', N'Cochabamba', N'Sobres-Documentos', 'AEREO', 60.00, 0.00),
    (N'Santa Cruz de la Sierra', N'Cochabamba', N'Alimentos', 'AEREO', 4.00, 0.00),
    (N'Santa Cruz de la Sierra', N'Cochabamba', N'Otros', 'AEREO', 5.00, 0.00),
    (N'Cochabamba', N'Santa Cruz de la Sierra', N'Sobres-Documentos', 'TERRESTRE', 40.00, 8.00),
    (N'Cochabamba', N'Santa Cruz de la Sierra', N'Alimentos', 'TERRESTRE', 1.50, 8.00),
    (N'Cochabamba', N'Santa Cruz de la Sierra', N'Otros', 'TERRESTRE', 2.50, 8.00),
    (N'Cochabamba', N'Santa Cruz de la Sierra', N'Sobres-Documentos', 'AEREO', 60.00, 0.00),
    (N'Cochabamba', N'Santa Cruz de la Sierra', N'Alimentos', 'AEREO', 4.00, 0.00),
    (N'Cochabamba', N'Santa Cruz de la Sierra', N'Otros', 'AEREO', 5.00, 0.00),
    (N'Cochabamba', N'La Paz', N'Sobres-Documentos', 'TERRESTRE', 35.00, 8.00),
    (N'Cochabamba', N'La Paz', N'Alimentos', 'TERRESTRE', 1.20, 8.00),
    (N'Cochabamba', N'La Paz', N'Otros', 'TERRESTRE', 2.00, 8.00),
    (N'Cochabamba', N'La Paz', N'Sobres-Documentos', 'AEREO', 55.00, 0.00),
    (N'Cochabamba', N'La Paz', N'Alimentos', 'AEREO', 3.50, 0.00),
    (N'Cochabamba', N'La Paz', N'Otros', 'AEREO', 4.50, 0.00),
    (N'La Paz', N'Cochabamba', N'Sobres-Documentos', 'TERRESTRE', 35.00, 8.00),
    (N'La Paz', N'Cochabamba', N'Alimentos', 'TERRESTRE', 1.20, 8.00),
    (N'La Paz', N'Cochabamba', N'Otros', 'TERRESTRE', 2.00, 8.00),
    (N'La Paz', N'Cochabamba', N'Sobres-Documentos', 'AEREO', 55.00, 0.00),
    (N'La Paz', N'Cochabamba', N'Alimentos', 'AEREO', 3.50, 0.00),
    (N'La Paz', N'Cochabamba', N'Otros', 'AEREO', 4.50, 0.00)
) AS v(origen, destino, tipo, forma, precio, recargo)
JOIN Ciudad co         ON co.nombre = v.origen
JOIN Ciudad cd         ON cd.nombre = v.destino
JOIN TipoEncomienda te ON te.nombre = v.tipo
WHERE NOT EXISTS (SELECT 1 FROM Tarifa t
                  WHERE t.id_ciudad_origen = co.id_ciudad AND t.id_ciudad_destino = cd.id_ciudad
                    AND t.id_tipo = te.id_tipo AND t.forma_envio = v.forma AND t.activa = 1);

SELECT COUNT(*) AS tarifas_vigentes FROM Tarifa WHERE activa = 1;   -- debe dar 36
GO
