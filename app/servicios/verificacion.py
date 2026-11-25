"""Control de productos prohibidos (HU-08 / CU-12): clase CtrlVerificacion del diseño.

CtrlRecepcion le pregunta esProhibido(contenido) antes de calcular el costo,
como en el diagrama de secuencia de CU-11.
"""
from app.datos.producto_repo import ProductoProhibidoRepositorio
from app.dominio.verificacion import buscarProhibido


class CtrlVerificacion:

    def __init__(self, productos=None):
        self.productos = productos or ProductoProhibidoRepositorio()

    def productoProhibido(self, descripcion):
        """El producto prohibido que coincide con la descripción, o None."""
        return buscarProhibido(descripcion, self.productos.listarActivos())

    def esProhibido(self, descripcion):
        return self.productoProhibido(descripcion) is not None
