"""Validaciones de datos ingresados por el usuario (reglas puras, sin BD).

Cada función devuelve un diccionario {campo: mensaje}. Vacío = todo correcto.
"""
import re
from decimal import Decimal

CI_VALIDO = re.compile(r"^\d{5,10}(-?[0-9A-Z]{1,2})?$")      # 1234567, 1234567-1A
TELEFONO_VALIDO = re.compile(r"^\+?\d{7,15}$")
EMAIL_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def normalizar_ci(ci: str) -> str:
    return (ci or "").strip().upper().replace(" ", "")


def validar_cliente(ci, nombres, apellidos, telefono, email=""):
    """HU-07, criterio 3: campos obligatorios y formatos."""
    errores = {}
    if not CI_VALIDO.match(normalizar_ci(ci)):
        errores["ci"] = "Ingrese un CI válido (solo números, con extensión opcional, p. ej. 1234567-1A)."
    if not (nombres or "").strip():
        errores["nombres"] = "Los nombres son obligatorios."
    if not (apellidos or "").strip():
        errores["apellidos"] = "Los apellidos son obligatorios."
    if not TELEFONO_VALIDO.match((telefono or "").strip().replace(" ", "")):
        errores["telefono"] = "Ingrese un teléfono de 7 a 15 dígitos."
    if email and not EMAIL_VALIDO.match(email.strip()):
        errores["email"] = "El correo no tiene un formato válido."
    return errores


def validar_encomienda(peso_kg: Decimal, volumen_m3: Decimal, id_sucursal_origen: int,
                       id_sucursal_destino: int, contenido: str):
    """HU-09, criterio 2: datos inválidos no se guardan."""
    errores = {}
    if peso_kg is None or peso_kg <= 0:
        errores["peso"] = "El peso debe ser mayor a 0."
    if volumen_m3 is None or volumen_m3 < 0:
        errores["volumen"] = "El volumen no puede ser negativo."
    if id_sucursal_origen == id_sucursal_destino:
        errores["destino"] = "La sucursal de destino debe ser distinta de la de origen."
    if not (contenido or "").strip():
        errores["contenido"] = "Describa el contenido de la encomienda."
    return errores
