"""Pruebas de los servicios sin base de datos: los repositorios se reemplazan por
versiones falsas (monkeypatch). Así se prueban las reglas de HU-07 y HU-09."""
from contextlib import contextmanager
from decimal import Decimal as D

import pytest

from app.servicios import clientes as srv_clientes
from app.servicios import recepcion as srv_recepcion

EMPLEADO = {"id_empleado": 1, "nombre_completo": "Recepcionista", "rol": "RECEPCIONISTA", "activo": True,
            "id_sucursal": 1, "codigo_sucursal": "SCZ", "sucursal": "Sucursal Santa Cruz", "id_ciudad": 1}
CLIENTES = {"1234567": {"id_cliente": 10, "ci": "1234567", "nombres": "Ana", "apellidos": "Pérez"},
            "7654321": {"id_cliente": 11, "ci": "7654321", "nombres": "Luis", "apellidos": "Rojas"}}
TARIFA = {"id_tarifa": 3, "precio_por_kilo": D("3.00"), "umbral_volumen_m3": D("0.050"), "recargo_volumen": D("10.00")}


# ---------------- HU-07 ----------------

def test_hu07_ca1_registra_cliente_nuevo(monkeypatch):
    guardados = []
    monkeypatch.setattr(srv_clientes.cliente_repo, "buscar_por_ci", lambda ci: None)
    monkeypatch.setattr(srv_clientes.cliente_repo, "registrar", lambda *a: guardados.append(a) or 99)
    assert srv_clientes.registrar_cliente(" 1234567 ", " Ana ", "Pérez", "700 12345") == 99
    assert guardados[0][:4] == ("1234567", "Ana", "Pérez", "70012345")


def test_hu07_ca2_no_permite_ci_duplicado(monkeypatch):
    monkeypatch.setattr(srv_clientes.cliente_repo, "buscar_por_ci", lambda ci: CLIENTES.get(ci))
    with pytest.raises(srv_clientes.ErrorDeValidacion) as e:
        srv_clientes.registrar_cliente("1234567", "Ana", "Pérez", "70012345")
    assert "ci" in e.value.errores


def test_hu07_ca4_no_elimina_cliente_con_encomiendas(monkeypatch):
    monkeypatch.setattr(srv_clientes.cliente_repo, "cantidad_encomiendas", lambda i: 2)
    with pytest.raises(srv_clientes.ErrorDeValidacion):
        srv_clientes.eliminar_cliente(10)


# ---------------- HU-09 ----------------

class CursorFalso:
    def __init__(self):
        self.sql = []
    def execute(self, sql, *params):
        self.sql.append((" ".join(sql.split())[:40], params))
    def fetchone(self):
        return [0] if self.sql[-1][0].startswith("SELECT COUNT") else [500]


@pytest.fixture
def bd_falsa(monkeypatch):
    cur = CursorFalso()

    @contextmanager
    def transaccion():
        yield cur

    monkeypatch.setattr(srv_recepcion, "transaccion", transaccion)
    monkeypatch.setattr(srv_recepcion.catalogo_repo, "obtener_empleado", lambda i: EMPLEADO)
    monkeypatch.setattr(srv_recepcion.catalogo_repo, "ciudad_de_sucursal", lambda i: 2)
    monkeypatch.setattr(srv_recepcion.catalogo_repo, "buscar_tarifa_vigente", lambda *a: TARIFA)
    monkeypatch.setattr(srv_recepcion.cliente_repo, "buscar_por_ci", lambda ci: CLIENTES.get(ci))
    return cur


def datos(**cambios):
    d = {"ci_remitente": "1234567", "ci_destinatario": "7654321", "id_sucursal_destino": 2, "id_tipo": 3,
         "forma_envio": "TERRESTRE", "peso_kg": D("4.3"), "volumen_m3": D("0.08"),
         "recargo_manual": D("0"), "contenido": "Ropa"}
    d.update(cambios)
    return d


def test_hu09_ca1_registra_con_codigo_de_guia_y_seguimiento(bd_falsa):
    codigo = srv_recepcion.registrar_encomienda(datos(), 1, declara_no_prohibido=True)
    assert codigo.startswith("SCZ-") and codigo.endswith("-00001")
    sentencias = [s for s, _ in bd_falsa.sql]
    assert any(s.startswith("INSERT INTO Encomienda") for s in sentencias)
    assert any(s.startswith("INSERT INTO Seguimiento") for s in sentencias)   # criterio 3


def test_hu09_guarda_el_costo_calculado(bd_falsa):
    srv_recepcion.registrar_encomienda(datos(), 1, declara_no_prohibido=True)
    params = next(p for s, p in bd_falsa.sql if s.startswith("INSERT INTO Encomienda"))
    assert params[-2] == D("25.00")     # 5 kg x 3 Bs + 10 Bs de recargo (RN-03)


def test_hu09_ca2_datos_invalidos_no_guardan(bd_falsa):
    with pytest.raises(srv_recepcion.ErrorDeNegocio):
        srv_recepcion.registrar_encomienda(datos(peso_kg=D("0")), 1, declara_no_prohibido=True)
    assert bd_falsa.sql == []


def test_hu09_remitente_no_registrado(bd_falsa):
    with pytest.raises(srv_recepcion.ErrorDeNegocio, match="remitente no está registrado"):
        srv_recepcion.registrar_encomienda(datos(ci_remitente="999999"), 1, declara_no_prohibido=True)


def test_hu09_exige_declaracion_del_remitente(bd_falsa):
    with pytest.raises(srv_recepcion.ErrorDeNegocio, match="declaración"):
        srv_recepcion.registrar_encomienda(datos(), 1, declara_no_prohibido=False)
    assert bd_falsa.sql == []
