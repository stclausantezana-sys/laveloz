"""Pruebas de HU-07 (criterio 3) y HU-09 (criterio 2)."""
from decimal import Decimal as D

from app.dominio.validaciones import normalizarCi, validarCliente, validarEncomienda


# ---------- HU-07 Registrar cliente ----------

def test_hu07_cliente_valido_no_tiene_errores():
    assert validarCliente("1234567", "Ana", "Pérez", "70012345", "ana@mail.com") == {}


def test_hu07_ca3_campos_obligatorios_vacios():
    errores = validarCliente("", "", "", "")
    assert set(errores) == {"ci", "nombres", "apellidos", "telefono"}


def test_hu07_ca3_correo_con_formato_invalido():
    assert "email" in validarCliente("1234567", "Ana", "Pérez", "70012345", "ana@mail")


def test_hu07_el_correo_es_opcional():
    assert validarCliente("1234567", "Ana", "Pérez", "70012345", "") == {}


def test_hu07_ci_con_extension_y_espacios_se_normaliza():
    assert normalizarCi(" 1234567-1a ") == "1234567-1A"
    assert validarCliente(" 1234567-1a ", "Ana", "Pérez", "70012345") == {}


# ---------- HU-09 Registrar recepción ----------

def test_hu09_datos_validos():
    assert validarEncomienda(D("4.3"), D("0.02"), 1, 2, "Ropa") == {}


def test_hu09_ca2_peso_cero_volumen_negativo_y_mismo_destino():
    errores = validarEncomienda(D("0"), D("-1"), 1, 1, "Ropa")
    assert set(errores) == {"peso", "volumen", "destino"}


def test_hu09_contenido_obligatorio():
    assert "contenido" in validarEncomienda(D("1"), D("0"), 1, 2, "  ")
