"""Prueba de la pantalla Cotizar sin base de datos: se reemplazan los repositorios."""
from decimal import Decimal

import pytest

from app import create_app
from app.datos.catalogo_repo import CatalogoRepositorio, TarifaRepositorio


@pytest.fixture
def cliente_web(monkeypatch):
    monkeypatch.setattr(CatalogoRepositorio, "listarCiudades",
                        lambda self: [{"id_ciudad": 1, "nombre": "Santa Cruz"}, {"id_ciudad": 2, "nombre": "La Paz"}])
    monkeypatch.setattr(CatalogoRepositorio, "listarTipos", lambda self: [{"id_tipo": 3, "nombre": "Otros"}])
    monkeypatch.setattr(TarifaRepositorio, "buscarVigente",
                        lambda self, *a: {"id_tarifa": 3, "precio_por_kilo": Decimal("3.00"),
                                          "umbral_volumen_m3": Decimal("0.050"), "recargo_volumen": Decimal("10.00")})
    return create_app().test_client()


def test_cotizar_muestra_el_total(cliente_web):
    r = cliente_web.post("/cotizar", data={"origen": "1", "destino": "2", "tipo": "3",
                                           "forma": "TERRESTRE", "peso": "4,3", "volumen": "0.08"})
    texto = r.get_data(as_text=True)
    assert "5 kg × 3.00 Bs" in texto
    assert "Total: 25.00 Bs" in texto


def test_cotizar_mismo_origen_y_destino(cliente_web):
    r = cliente_web.post("/cotizar", data={"origen": "1", "destino": "1", "tipo": "3",
                                           "forma": "TERRESTRE", "peso": "2"})
    assert "El destino debe ser distinto del origen." in r.get_data(as_text=True)
