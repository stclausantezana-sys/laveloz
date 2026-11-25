"""Pruebas de HU-13 Cobrar y emitir comprobante, con repositorios falsos (sin base de datos)."""
from contextlib import contextmanager
from decimal import Decimal as D

import pytest

from app.servicios.caja import CtrlCaja
from app.servicios.recepcion import ErrorDeNegocio

CAJERA = {"id_empleado": 2, "nombre_completo": "Cajera de prueba SCZ", "rol": "CAJERA", "activo": True,
          "id_sucursal": 1, "codigo_sucursal": "SCZ", "sucursal": "Sucursal Santa Cruz", "id_ciudad": 1}


class EncomiendasFalsas:
    def __init__(self, estado="REGISTRADA"):
        self.e = {"id_encomienda": 500, "codigo_guia": "SCZ-20261125-00001", "estado": estado,
                  "monto_total": D("25.00"), "remitente": "Ana Pérez", "destinatario": "Luis Rojas",
                  "destino": "Sucursal La Paz"}
    def buscarPorCodigo(self, codigo):
        return self.e if codigo == self.e["codigo_guia"] else None
    def cambiarEstado(self, cur, idEncomienda, anterior, nuevo):
        if self.e["estado"] != anterior:
            return False
        self.e["estado"] = nuevo
        return True


class PagosFalsos:
    def __init__(self):
        self.guardados = []
    def siguienteCorrelativo(self, cur, idSucursal):
        return 1
    def guardar(self, cur, p):
        self.guardados.append(p)
        return 70


class SeguimientosFalsos:
    def __init__(self):
        self.registros = []
    def registrar(self, cur, idEncomienda, idEmpleado, anterior, nuevo, observacion=None):
        self.registros.append((idEncomienda, idEmpleado, anterior, nuevo))


class CatalogoFalso:
    def __init__(self, empleado=CAJERA):
        self.empleado = empleado
    def obtenerEmpleado(self, idEmpleado):
        return self.empleado


@contextmanager
def conexionFalsa():
    yield "cursor-falso"


def caja(estado="REGISTRADA", empleado=CAJERA):
    return CtrlCaja(EncomiendasFalsas(estado), PagosFalsos(), SeguimientosFalsos(),
                    CatalogoFalso(empleado), conexionFalsa)


def test_hu13_ca1_buscar_muestra_el_monto_de_la_recepcion():
    assert caja().buscarEncomienda(" scz-20261125-00001 ")["monto_total"] == D("25.00")


def test_hu13_ca2_cobrar_pasa_a_pagada_con_comprobante():
    c = caja()
    nro = c.cobrarEncomienda("SCZ-20261125-00001", "QR", 2)
    assert nro.startswith("CSCZ-") and nro.endswith("-00001")
    assert c.encomiendas.e["estado"] == "PAGADA"
    pago = c.pagos.guardados[0]
    assert (pago["monto"], pago["metodo"], pago["id_cajera"]) == (D("25.00"), "QR", 2)


@pytest.mark.parametrize("estado", ["PAGADA", "ANULADA"])
def test_hu13_ca3_no_se_cobra_dos_veces_ni_anulada(estado):
    c = caja(estado)
    with pytest.raises(ErrorDeNegocio, match="no se puede cobrar"):
        c.cobrarEncomienda("SCZ-20261125-00001", "EFECTIVO", 2)
    assert c.pagos.guardados == []


def test_hu13_ca4_seguimiento_registrada_a_pagada_con_la_cajera():
    c = caja()
    c.cobrarEncomienda("SCZ-20261125-00001", "EFECTIVO", 2)
    assert c.seguimientos.registros == [(500, 2, "REGISTRADA", "PAGADA")]


def test_hu13_codigo_inexistente():
    with pytest.raises(ErrorDeNegocio, match="Código de guía no encontrado"):
        caja().buscarEncomienda("SCZ-20990101-00009")


def test_hu13_metodo_de_pago_invalido():
    with pytest.raises(ErrorDeNegocio, match="método de pago"):
        caja().cobrarEncomienda("SCZ-20261125-00001", "BITCOIN", 2)


def test_hu13_solo_una_cajera_puede_cobrar():
    recepcionista = dict(CAJERA, rol="RECEPCIONISTA")
    with pytest.raises(ErrorDeNegocio, match="cajera"):
        caja(empleado=recepcionista).cobrarEncomienda("SCZ-20261125-00001", "EFECTIVO", 1)
