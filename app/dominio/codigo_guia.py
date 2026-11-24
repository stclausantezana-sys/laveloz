"""Código de guía de la encomienda (RN-08), para usar en HU-09.

Formato: SUCURSAL-AAAAMMDD-correlativo de 5 dígitos.
Ejemplo:  SCZ-20261120-00001
"""
from datetime import date


def generar_codigo_guia(codigo_sucursal: str, fecha: date, correlativo: int) -> str:
    if len(codigo_sucursal) != 3:
        raise ValueError("El código de sucursal debe tener 3 letras.")
    if correlativo < 1:
        raise ValueError("El correlativo empieza en 1.")
    return f"{codigo_sucursal.upper()}-{fecha:%Y%m%d}-{correlativo:05d}"
