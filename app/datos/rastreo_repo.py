"""Consulta del rastreo público (HU-19).

A propósito NO trae el CI ni el teléfono de los clientes (HU-19 criterio 3, RNF-08).
"""
from .conexion import consultar


class RastreoRepositorio:

    def buscarPorCodigo(self, codigoGuia):
        filas = consultar("""
            SELECT e.codigo_guia, e.estado, t.nombre AS tipo,
                   so.nombre AS origen, sd.nombre AS destino,
                   e.fecha_hora_recepcion, p.fecha_hora AS fecha_hora_pago,
                   e.fecha_hora_salida, e.fecha_hora_llegada, en.fecha_hora_entrega
            FROM Encomienda e
            JOIN TipoEncomienda t ON t.id_tipo = e.id_tipo
            JOIN Sucursal so ON so.id_sucursal = e.id_sucursal_origen
            JOIN Sucursal sd ON sd.id_sucursal = e.id_sucursal_destino
            LEFT JOIN Pago p ON p.id_encomienda = e.id_encomienda
            LEFT JOIN Entrega en ON en.id_encomienda = e.id_encomienda
            WHERE e.codigo_guia = ?
        """, codigoGuia)
        return filas[0] if filas else None
