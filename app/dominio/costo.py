"""Cálculo del costo de envío (HU-10).

Reglas de negocio:
  RN-03  Costo = kilos cobrables x precio por kilo + recargo por volumen.
  RN-04  Kilos cobrables = peso redondeado hacia arriba, mínimo 1 kg.
  RN-05  Si el volumen supera el umbral de la tarifa hay recargo:
         terrestre -> el de la tarifa; aéreo -> lo ingresa el recepcionista.

Este módulo NO usa la base de datos: por eso se prueba fácil con TDD.
"""
import math
from dataclasses import dataclass
from decimal import Decimal

TERRESTRE = "TERRESTRE"
AEREO = "AEREO"


@dataclass(frozen=True)
class Costo:
    kilos_cobrados: int
    precio_por_kilo: Decimal
    subtotal: Decimal
    recargo: Decimal
    total: Decimal


def calcular_costo(peso_kg, volumen_m3, precio_por_kilo, umbral_m3,
                   recargo_tarifa, forma_envio, recargo_manual=Decimal("0")):
    if peso_kg <= 0:
        raise ValueError("El peso debe ser mayor a 0.")
    if volumen_m3 < 0:
        raise ValueError("El volumen no puede ser negativo.")

    kilos = max(1, math.ceil(peso_kg))                      # RN-04
    subtotal = kilos * precio_por_kilo

    recargo = Decimal("0")
    if volumen_m3 > umbral_m3:                              # RN-05
        recargo = recargo_tarifa if forma_envio == TERRESTRE else recargo_manual

    return Costo(kilos, precio_por_kilo, subtotal, recargo, subtotal + recargo)  # RN-03
