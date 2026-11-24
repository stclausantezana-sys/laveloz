"""Pruebas de los controladores sin base de datos.

Los controladores reciben sus repositorios en el constructor, así que en las
pruebas se les pasan repositorios FALSOS (en memoria). Se prueban las reglas de
HU-07 y HU-09 sin tocar SQL Server.
"""
from contextlib import contextmanager
from decimal import Decimal as D

import pytest

from app.servicios.clientes import CtrlCliente, ErrorDeValidacion
from app.servicios.recepcion import CtrlRecepcion, CtrlTarifa, EncomiendaDTO, ErrorDeNegocio

EMPLEADO = {"id_empleado": 1, "nombre_completo": "Recepcionista", "rol": "RECEPCIONISTA", "activo": True,
            "id_sucursal": 1, "codigo_sucursal": "SCZ", "sucursal": "Sucursal Santa Cruz", "id_ciudad": 1}
CLIENTES = {"1234567": {"id_cliente": 10, "ci": "1234567", "nombres": "Ana", "apellidos": "Pérez"},
            "7654321": {"id_cliente": 11, "ci": "7654321", "nombres": "Luis", "apellidos": "Rojas"}}
TARIFA = {"id_tarifa": 3, "precio_por_kilo": D("3.00"), "umbral_volumen_m3": D("0.050"), "recargo_volumen": D("10.00")}


# ---------------- Repositorios falsos ----------------

class ClienteRepositorioFalso:
    def __init__(self, encomiendas=0):
        self.guardados, self.encomiendas = [], encomiendas
    def buscarPorCi(self, ci):
        return CLIENTES.get(ci)
    def guardar(self, c):
        self.guardados.append(c)
        return 99
    def cantidadEncomiendas(self, idCliente):
        return self.encomiendas
    def eliminar(self, idCliente):
        self.guardados.append(("eliminado", idCliente))


class CatalogoFalso:
    def obtenerEmpleado(self, idEmpleado):
        return EMPLEADO
    def ciudadDeSucursal(self, idSucursal):
        return idSucursal          # sucursal 1 -> ciudad 1, sucursal 2 -> ciudad 2


class TarifaRepositorioFalso:
    def buscarVigente(self, origen, destino, tipo, forma):
        return TARIFA


class EncomiendaRepositorioFalso:
    def __init__(self):
        self.guardadas = []
    def siguienteCorrelativo(self, cur, idSucursal):
        return 1
    def guardar(self, cur, e):
        self.guardadas.append(e)
        return 500


class SeguimientoRepositorioFalso:
    def __init__(self):
        self.registros = []
    def registrar(self, cur, idEncomienda, idEmpleado, anterior, nuevo, observacion=None):
        self.registros.append((idEncomienda, idEmpleado, anterior, nuevo))


@contextmanager
def conexionFalsa():
    yield "cursor-falso"


# ---------------- HU-07 ----------------

def test_hu07_ca1_registra_cliente_nuevo():
    repo = ClienteRepositorioFalso()
    repo.buscarPorCi = lambda ci: None            # el CI todavía no existe
    assert CtrlCliente(repo).registrarCliente(" 1234567 ", " Ana ", "Pérez", "700 12345") == 99
    g = repo.guardados[0]
    assert (g["ci"], g["nombres"], g["apellidos"], g["telefono"]) == ("1234567", "Ana", "Pérez", "70012345")


def test_hu07_ca2_no_permite_ci_duplicado():
    with pytest.raises(ErrorDeValidacion) as e:
        CtrlCliente(ClienteRepositorioFalso()).registrarCliente("1234567", "Ana", "Pérez", "70012345")
    assert "ci" in e.value.errores


def test_hu07_ca4_no_elimina_cliente_con_encomiendas():
    repo = ClienteRepositorioFalso(encomiendas=2)
    with pytest.raises(ErrorDeValidacion):
        CtrlCliente(repo).eliminarCliente(10)
    assert repo.guardados == []


# ---------------- HU-09 ----------------

@pytest.fixture
def ctrl():
    catalogo = CatalogoFalso()
    return CtrlRecepcion(clientes=ClienteRepositorioFalso(), encomiendas=EncomiendaRepositorioFalso(),
                         seguimientos=SeguimientoRepositorioFalso(), catalogo=catalogo,
                         ctrlTarifa=CtrlTarifa(TarifaRepositorioFalso(), catalogo),
                         conexion=conexionFalsa)


def dto(**cambios):
    d = EncomiendaDTO(ciRemitente="1234567", ciDestinatario="7654321", idSucursalDestino=2, idTipo=3,
                      formaEnvio="TERRESTRE", pesoKg=D("4.3"), volumenM3=D("0.08"),
                      contenido="Ropa", declaraNoProhibido=True)
    for campo, valor in cambios.items():
        setattr(d, campo, valor)
    return d


def test_hu09_ca1_registra_con_codigo_de_guia_y_seguimiento(ctrl):
    codigo = ctrl.registrarEncomienda(dto(), 1)
    assert codigo.startswith("SCZ-") and codigo.endswith("-00001")
    assert len(ctrl.encomiendas.guardadas) == 1
    assert ctrl.seguimientos.registros == [(500, 1, None, "REGISTRADA")]       # criterio 3


def test_hu09_guarda_el_costo_calculado(ctrl):
    ctrl.registrarEncomienda(dto(), 1)
    assert ctrl.encomiendas.guardadas[0]["total"] == D("25.00")   # 5 kg x 3 Bs + 10 Bs de recargo (RN-03)


def test_hu09_cotizar_no_guarda_nada(ctrl):
    assert ctrl.cotizar(dto(), 1).total == D("25.00")
    assert ctrl.encomiendas.guardadas == []


def test_hu09_ca2_datos_invalidos_no_guardan(ctrl):
    with pytest.raises(ErrorDeNegocio):
        ctrl.registrarEncomienda(dto(pesoKg=D("0")), 1)
    assert ctrl.encomiendas.guardadas == []


def test_hu09_remitente_no_registrado(ctrl):
    with pytest.raises(ErrorDeNegocio, match="remitente no está registrado"):
        ctrl.registrarEncomienda(dto(ciRemitente="999999"), 1)


def test_hu09_exige_declaracion_del_remitente(ctrl):
    with pytest.raises(ErrorDeNegocio, match="declaración"):
        ctrl.registrarEncomienda(dto(declaraNoProhibido=False), 1)
    assert ctrl.encomiendas.guardadas == []


def test_hu10_ca4_sin_tarifa_vigente(ctrl):
    ctrl.ctrlTarifa.tarifas.buscarVigente = lambda *a: None
    with pytest.raises(ErrorDeNegocio, match="No hay tarifa"):
        ctrl.cotizar(dto(), 1)
