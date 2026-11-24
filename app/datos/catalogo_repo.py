"""Consultas de catálogos: ciudades, sucursales, empleados, tipos y tarifas."""
from .conexion import consultar


def listar_ciudades():
    return consultar("SELECT id_ciudad, nombre FROM Ciudad ORDER BY nombre")


def listar_sucursales():
    return consultar("""
        SELECT s.id_sucursal, s.codigo, s.nombre, c.nombre AS ciudad
        FROM Sucursal s JOIN Ciudad c ON c.id_ciudad = s.id_ciudad
        WHERE s.activa = 1 ORDER BY s.nombre
    """)


def listar_tipos():
    return consultar("SELECT id_tipo, nombre FROM TipoEncomienda WHERE activo = 1 ORDER BY id_tipo")


def obtener_empleado(id_empleado):
    """Empleado con su sucursal (la sucursal de origen de lo que recibe)."""
    filas = consultar("""
        SELECT e.id_empleado, e.nombre_completo, e.rol, e.activo,
               s.id_sucursal, s.codigo AS codigo_sucursal, s.nombre AS sucursal, s.id_ciudad
        FROM Empleado e JOIN Sucursal s ON s.id_sucursal = e.id_sucursal
        WHERE e.id_empleado = ?
    """, id_empleado)
    return filas[0] if filas else None


def ciudad_de_sucursal(id_sucursal):
    filas = consultar("SELECT id_ciudad FROM Sucursal WHERE id_sucursal = ?", id_sucursal)
    return filas[0]["id_ciudad"] if filas else None


def listar_tarifas_vigentes():
    return consultar("""
        SELECT co.nombre AS origen, cd.nombre AS destino, t.nombre AS tipo,
               ta.forma_envio, ta.precio_por_kilo, ta.umbral_volumen_m3, ta.recargo_volumen
        FROM Tarifa ta
        JOIN Ciudad co ON co.id_ciudad = ta.id_ciudad_origen
        JOIN Ciudad cd ON cd.id_ciudad = ta.id_ciudad_destino
        JOIN TipoEncomienda t ON t.id_tipo = ta.id_tipo
        WHERE ta.activa = 1
        ORDER BY co.nombre, cd.nombre, ta.forma_envio, t.id_tipo
    """)


def buscar_tarifa_vigente(id_ciudad_origen, id_ciudad_destino, id_tipo, forma_envio):
    """Devuelve la tarifa vigente (RN-14: hay una sola) o None si no existe."""
    filas = consultar("""
        SELECT id_tarifa, precio_por_kilo, umbral_volumen_m3, recargo_volumen
        FROM Tarifa
        WHERE id_ciudad_origen = ? AND id_ciudad_destino = ?
          AND id_tipo = ? AND forma_envio = ? AND activa = 1
    """, id_ciudad_origen, id_ciudad_destino, id_tipo, forma_envio)
    return filas[0] if filas else None
