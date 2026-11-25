"""Pruebas de HU-10 Calcular costo de envío (hechas con TDD: la prueba primero).

Cada prueba corresponde a un criterio de aceptación (CA) de la historia:
así queda la trazabilidad HU -> código -> prueba.
"""
from decimal import Decimal as D

import pytest

from app.dominio.costo import AEREO, TERRESTRE, calcularCosto


def costo(peso, vol="0.02", forma=TERRESTRE, recargoManual="0"):
    # Tarifa Santa Cruz -> La Paz, tipo "Otros": 3 Bs/kg, umbral 0,05 m3, recargo 10 Bs
    return calcularCosto(D(peso), D(vol), precioPorKilo=D("3.00"),
                         umbralM3=D("0.05"), recargoTarifa=D("10.00"),
                         formaEnvio=forma, recargoManual=D(recargoManual))


def test_hu10_ca1_kilos_se_redondean_hacia_arriba():
    c = costo("4.3")
    assert c.kilosCobrados == 5
    assert c.total == D("15.00")


def test_hu10_ca2_recargo_terrestre_si_supera_umbral():
    assert costo("4.3", vol="0.08").total == D("25.00")


def test_hu10_ca3_menos_de_un_kilo_se_cobra_uno():
    assert costo("0.3").kilosCobrados == 1


def test_aereo_usa_el_recargo_que_ingresa_el_recepcionista():
    assert costo("2", vol="0.10", forma=AEREO, recargoManual="7.50").recargo == D("7.50")


def test_sin_recargo_si_no_supera_el_umbral():
    assert costo("2", vol="0.05").recargo == D("0")


@pytest.mark.parametrize("peso", ["0", "-1"])
def test_peso_invalido(peso):
    with pytest.raises(ValueError):
        costo(peso)
