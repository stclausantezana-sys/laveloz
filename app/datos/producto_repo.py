"""Repositorio de productos prohibidos (HU-08): implementa IProductoProhibidoRepositorio."""
from .conexion import consultar


class ProductoProhibidoRepositorio:

    def listarActivos(self):
        return consultar("""
            SELECT id_producto, nombre, palabras_clave, base_legal
            FROM ProductoProhibido WHERE activo = 1 ORDER BY nombre
        """)
