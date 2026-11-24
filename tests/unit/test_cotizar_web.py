"""Prueba de la pantalla Cotizar sin base de datos: se reemplazan los repositorios."""
from decimal import Decimal

import pytest

from app import create_app
from app.datos import catalogo_repo


@pytest.fixture
def cliente_web(monkeypatch):
    monkeypatch.setattr(catalogo_repo, "listar_ciudades",
                        lambda: [{"id_ciudad": 1, "nombre": "Santa Cruz"}, {"id_ciudad": 2, "nombre": "La Paz"}])
    monkeypatch.setattr(catalogo_repo, "listar_tipos", lambda: [{"id_tipo": 3, "nombre": "Otros"}])
    monkeypatch.setattr(catalogo_repo, "buscar_tarifa_vigente",
                        lambda *a: {"id_tarifa": 3, "precio_por_kilo": Decimal("3.00"),
                                    "umbral_volumen_m3": Decimal("0.050"), "recargo_volumen": Decimal("10.00")})
    return create_app().test_client()


def test_cotizar_muestra_el_total(cliente_web):
    r = cliente_web.post("/cotizar", data={"origen": "1", "destino": "2", "tipo": "3",
                                           "forma": "TERRESTRE", "peso": "4,3", "volumen": "0.08"})
    assert "Total: 25.00 Bs" in r.get_data(as_text=True)


def test_cotizar_mismo_origen_y_destino(cliente_web):
    r = cliente_web.post("/cotizar", data={"origen": "1", "destino": "1", "tipo": "3",
                                           "forma": "TERRESTRE", "peso": "2"})
    assert "El destino debe ser distinto del origen." in r.get_data(as_text=True)
