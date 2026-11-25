"""Validaciones de datos ingresados por el usuario (reglas puras, sin BD).

Cada función devuelve un diccionario {campo: mensaje}. Vacío = todo correcto.
"""
import re
from decimal import Decimal

CI_VALIDO = re.compile(r"^\d{5,10}(-?[0-9A-Z]{1,2})?$")      # 1234567, 1234567-1A
TELEFONO_VALIDO = re.compile(r"^\+?\d{7,15}$")
EMAIL_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def normalizarCi(ci: str) -> str:
    return (ci or "").strip().upper().replace(" ", "")


def validarCliente(ci, nombres, apellidos, telefono, email=""):
    """HU-07, criterio 3: campos obligatorios y formatos."""
    errores = {}
    if not CI_VALIDO.match(normalizarCi(ci)):
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


def validarEncomienda(pesoKg: Decimal, volumenM3: Decimal, idSucursalOrigen: int,
                      idSucursalDestino: int, contenido: str):
    """HU-09, criterio 2: datos inválidos no se guardan."""
    errores = {}
    if pesoKg is None or pesoKg <= 0:
        errores["peso"] = "El peso debe ser mayor a 0."
    if volumenM3 is None or volumenM3 < 0:
        errores["volumen"] = "El volumen no puede ser negativo."
    if idSucursalOrigen == idSucursalDestino:
        errores["destino"] = "La sucursal de destino debe ser distinta de la de origen."
    if not (contenido or "").strip():
        errores["contenido"] = "Describa el contenido de la encomienda."
    return errores
