"""Formato del código de guía de la encomienda (RN-08), usado en HU-09.

Formato: SUCURSAL-AAAAMMDD-correlativo de 5 dígitos.
Ejemplo:  SCZ-20261120-00001

CtrlRecepcion.generarCodigoGuia() obtiene el correlativo de la BD y llama a esta función.
"""
from datetime import date


def formatearCodigoGuia(codigoSucursal: str, fecha: date, correlativo: int) -> str:
    if len(codigoSucursal) != 3:
        raise ValueError("El código de sucursal debe tener 3 letras.")
    if correlativo < 1:
        raise ValueError("El correlativo empieza en 1.")
    return f"{codigoSucursal.upper()}-{fecha:%Y%m%d}-{correlativo:05d}"
