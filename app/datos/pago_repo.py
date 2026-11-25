"""Repositorio de pagos (HU-13): implementa IPagoRepositorio.

Los métodos que reciben `cur` se ejecutan dentro de la transacción de CtrlCaja.
"""
from .conexion import consultar


class PagoRepositorio:

    def siguienteCorrelativo(self, cur, idSucursal):
        """Correlativo del día de los comprobantes de la sucursal (bloquea igual que el código de guía)."""
        cur.execute("""
            SELECT COUNT(*) FROM Pago p WITH (UPDLOCK, HOLDLOCK)
            JOIN Empleado c ON c.id_empleado = p.id_cajera
            WHERE c.id_sucursal = ? AND CAST(p.fecha_hora AS DATE) = CAST(SYSDATETIME() AS DATE)
        """, idSucursal)
        return cur.fetchone()[0] + 1

    def guardar(self, cur, p):
        """Inserta el pago `p` y devuelve su id. Un solo pago por encomienda (UQ_Pago_encomienda, RN-07)."""
        cur.execute("""
            INSERT INTO Pago (id_encomienda, id_cajera, nro_comprobante, monto, metodo)
            OUTPUT INSERTED.id_pago
            VALUES (?, ?, ?, ?, ?)
        """, p["id_encomienda"], p["id_cajera"], p["nro_comprobante"], p["monto"], p["metodo"])
        return cur.fetchone()[0]

    def buscarPorComprobante(self, nroComprobante):
        filas = consultar("""
            SELECT p.nro_comprobante, p.fecha_hora, p.monto, p.metodo, e.codigo_guia,
                   r.nombres + ' ' + r.apellidos AS remitente,
                   d.nombres + ' ' + d.apellidos AS destinatario,
                   sd.nombre AS destino, c.nombre_completo AS cajera, s.nombre AS sucursal
            FROM Pago p
            JOIN Encomienda e ON e.id_encomienda = p.id_encomienda
            JOIN Cliente r ON r.id_cliente = e.id_remitente
            JOIN Cliente d ON d.id_cliente = e.id_destinatario
            JOIN Sucursal sd ON sd.id_sucursal = e.id_sucursal_destino
            JOIN Empleado c ON c.id_empleado = p.id_cajera
            JOIN Sucursal s ON s.id_sucursal = c.id_sucursal
            WHERE p.nro_comprobante = ?
        """, nroComprobante)
        return filas[0] if filas else None
