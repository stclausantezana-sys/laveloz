"""Pruebas de HU-19 Rastrear encomienda (sin base de datos)."""
from datetime import datetime

import pytest

from app import create_app
from app.datos.rastreo_repo import RastreoRepositorio
from app.servicios.rastreo import CtrlRastreo

FILA = {"codigo_guia": "SCZ-20261125-00001", "estado": "PAGADA", "tipo": "Otros",
        "origen": "Sucursal Santa Cruz", "destino": "Sucursal La Paz",
        "fecha_hora_recepcion": datetime(2026, 11, 25, 9, 30), "fecha_hora_pago": datetime(2026, 11, 25, 9, 41),
        "fecha_hora_salida": None, "fecha_hora_llegada": None, "fecha_hora_entrega": None,
        # aunque la consulta trajera datos personales, el control no los debe mostrar:
        "ci_remitente": "1234567", "telefono": "70012345"}


class RastreoFalso:
    def buscarPorCodigo(self, codigo):
        return FILA if codigo == FILA["codigo_guia"] else None


def test_hu19_ca1_estado_y_fecha_de_cada_etapa():
    r = CtrlRastreo(RastreoFalso()).rastrear("scz-20261125-00001")
    assert r["estado"] == "PAGADA"
    assert [e["etapa"] for e in r["etapas"]] == ["Recepción", "Pago", "Salida", "Llegada a destino", "Entrega"]
    assert r["etapas"][1]["fecha_hora"] == datetime(2026, 11, 25, 9, 41)
    assert r["etapas"][2]["fecha_hora"] is None


def test_hu19_ca2_codigo_inexistente():
    assert CtrlRastreo(RastreoFalso()).rastrear("SCZ-20990101-00009") is None


def test_hu19_ca3_no_muestra_ci_ni_telefono():
    r = CtrlRastreo(RastreoFalso()).rastrear("SCZ-20261125-00001")
    assert "ci_remitente" not in r and "telefono" not in r


@pytest.fixture
def web(monkeypatch):
    monkeypatch.setattr(RastreoRepositorio, "buscarPorCodigo", lambda self, c: RastreoFalso().buscarPorCodigo(c))
    return create_app().test_client()


def test_hu19_pantalla_muestra_etapas_sin_datos_personales(web):
    texto = web.get("/rastrear?codigo=SCZ-20261125-00001").get_data(as_text=True)
    assert "Pagada, lista para salir" in texto and "25/11/2026 09:41" in texto and "Pendiente" in texto
    assert "1234567" not in texto and "70012345" not in texto


def test_hu19_pantalla_codigo_no_encontrado(web):
    assert "Código de guía no encontrado." in web.get("/rastrear?codigo=XYZ").get_data(as_text=True)
