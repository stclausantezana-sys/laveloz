"""Control de caja (HU-13 / CU-15 Cobrar y CU-16 Emitir comprobante): clase CtrlCaja.

El cobro cambia la encomienda a PAGADA, guarda el Pago con su comprobante y deja el
seguimiento REGISTRADA -> PAGADA, todo en UNA transacción (ConexionBD).
"""
from datetime import date

from app.datos.catalogo_repo import CatalogoRepositorio
from app.datos.conexion import ConexionBD
from app.datos.encomienda_repo import EncomiendaRepositorio, SeguimientoRepositorio
from app.datos.pago_repo import PagoRepositorio
from app.dominio.codigo_guia import formatearNroComprobante
from app.servicios.recepcion import ErrorDeNegocio

METODOS = ("EFECTIVO", "TARJETA", "QR")


class CtrlCaja:

    def __init__(self, encomiendas=None, pagos=None, seguimientos=None, catalogo=None, conexion=ConexionBD):
        self.encomiendas = encomiendas or EncomiendaRepositorio()
        self.pagos = pagos or PagoRepositorio()
        self.seguimientos = seguimientos or SeguimientoRepositorio()
        self.catalogo = catalogo or CatalogoRepositorio()
        self.conexion = conexion

    def buscarEncomienda(self, codigoGuia):
        """HU-13, criterio 1: la encomienda con el monto calculado en la recepción."""
        e = self.encomiendas.buscarPorCodigo((codigoGuia or "").strip().upper())
        if e is None:
            raise ErrorDeNegocio("Código de guía no encontrado.")
        return e

    def cobrarEncomienda(self, codigoGuia, metodo, idCajera):
        """HU-13, criterios 2 a 4. Devuelve el número de comprobante."""
        cajera = self.catalogo.obtenerEmpleado(idCajera)
        if cajera is None or not cajera["activo"] or cajera["rol"] != "CAJERA":
            raise ErrorDeNegocio("El empleado configurado no es una cajera activa (revise CAJERA_ID en .env).")
        if metodo not in METODOS:
            raise ErrorDeNegocio("Elija el método de pago: efectivo, tarjeta o QR.")
        e = self.buscarEncomienda(codigoGuia)
        if e["estado"] != "REGISTRADA":                                            # criterio 3, RN-07
            raise ErrorDeNegocio(f"La encomienda está {e['estado']}: no se puede cobrar.")

        with self.conexion() as cur:
            if not self.encomiendas.cambiarEstado(cur, e["id_encomienda"], "REGISTRADA", "PAGADA"):
                raise ErrorDeNegocio("La encomienda ya fue cobrada.")             # otra caja cobró primero
            correlativo = self.pagos.siguienteCorrelativo(cur, cajera["id_sucursal"])
            nro = formatearNroComprobante(cajera["codigo_sucursal"], date.today(), correlativo)
            self.pagos.guardar(cur, {"id_encomienda": e["id_encomienda"], "id_cajera": idCajera,
                                     "nro_comprobante": nro, "monto": e["monto_total"], "metodo": metodo})
            self.seguimientos.registrar(cur, e["id_encomienda"], idCajera, "REGISTRADA", "PAGADA",
                                        f"Comprobante {nro} ({metodo})")              # criterio 4, RN-12
        return nro

    def comprobante(self, nroComprobante):
        p = self.pagos.buscarPorComprobante(nroComprobante)
        if p is None:
            raise ErrorDeNegocio("Comprobante no encontrado.")
        return p
