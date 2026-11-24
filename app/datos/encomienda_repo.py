"""Repositorio de encomiendas y su seguimiento (HU-09).

Las funciones que reciben `cur` se ejecutan DENTRO de una transacción abierta
por el servicio, para que Encomienda y Seguimiento se guarden juntos o no se
guarde nada.
"""
from .conexion import consultar


def siguiente_correlativo(cur, id_sucursal):
    """Correlativo del día para la sucursal (RN-08).

    UPDLOCK + HOLDLOCK bloquea el rango hasta el commit: si dos recepcionistas
    registran al mismo tiempo, el segundo espera y no se repite el número.
    """
    cur.execute("""
        SELECT COUNT(*) FROM Encomienda WITH (UPDLOCK, HOLDLOCK)
        WHERE id_sucursal_origen = ?
          AND CAST(fecha_hora_recepcion AS DATE) = CAST(SYSDATETIME() AS DATE)
    """, id_sucursal)
    return cur.fetchone()[0] + 1


def insertar(cur, e):
    """Inserta la encomienda (estado REGISTRADA por defecto) y devuelve su id."""
    cur.execute("""
        INSERT INTO Encomienda (
            codigo_guia, id_remitente, id_destinatario, id_tipo, id_tarifa,
            id_sucursal_origen, id_sucursal_destino, id_recepcionista,
            descripcion_contenido, peso_kg, volumen_m3, kilos_cobrados,
            precio_por_kilo_aplicado, recargo_volumen, monto_total, declara_no_prohibido)
        OUTPUT INSERTED.id_encomienda
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, e["codigo_guia"], e["id_remitente"], e["id_destinatario"], e["id_tipo"], e["id_tarifa"],
         e["id_sucursal_origen"], e["id_sucursal_destino"], e["id_recepcionista"],
         e["contenido"], e["peso_kg"], e["volumen_m3"], e["kilos_cobrados"],
         e["precio_por_kilo"], e["recargo"], e["total"], 1)
    return cur.fetchone()[0]


def insertar_seguimiento(cur, id_encomienda, id_empleado, estado_anterior, estado_nuevo,
                         observacion=None):
    """RN-12: cada cambio de estado deja registro con empleado y fecha-hora del servidor."""
    cur.execute("""
        INSERT INTO Seguimiento (id_encomienda, id_empleado, estado_anterior, estado_nuevo, observacion)
        VALUES (?, ?, ?, ?, ?)
    """, id_encomienda, id_empleado, estado_anterior, estado_nuevo, observacion)


def listar_recientes(limite=30):
    return consultar("""
        SELECT TOP (?) e.codigo_guia, e.fecha_hora_recepcion, e.estado, e.monto_total,
               r.nombres + ' ' + r.apellidos AS remitente,
               d.nombres + ' ' + d.apellidos AS destinatario,
               sd.nombre AS destino, emp.nombre_completo AS recepcionista
        FROM Encomienda e
        JOIN Cliente r ON r.id_cliente = e.id_remitente
        JOIN Cliente d ON d.id_cliente = e.id_destinatario
        JOIN Sucursal sd ON sd.id_sucursal = e.id_sucursal_destino
        JOIN Empleado emp ON emp.id_empleado = e.id_recepcionista
        ORDER BY e.id_encomienda DESC
    """, limite)


def seguimiento_de(codigo_guia):
    return consultar("""
        SELECT s.fecha_hora, s.estado_anterior, s.estado_nuevo, emp.nombre_completo AS empleado, s.observacion
        FROM Seguimiento s
        JOIN Encomienda e ON e.id_encomienda = s.id_encomienda
        JOIN Empleado emp ON emp.id_empleado = s.id_empleado
        WHERE e.codigo_guia = ?
        ORDER BY s.fecha_hora, s.id_seguimiento
    """, codigo_guia)
