"""Cálculo del costo de envío (HU-10): clase Costo y regla calcularCosto.

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
    kilosCobrados: int
    precioPorKilo: Decimal
    subtotal: Decimal
    recargo: Decimal
    total: Decimal


def calcularCosto(pesoKg, volumenM3, precioPorKilo, umbralM3,
                  recargoTarifa, formaEnvio, recargoManual=Decimal("0")):
    if pesoKg <= 0:
        raise ValueError("El peso debe ser mayor a 0.")
    if volumenM3 < 0:
        raise ValueError("El volumen no puede ser negativo.")

    kilos = max(1, math.ceil(pesoKg))                       # RN-04
    subtotal = kilos * precioPorKilo

    recargo = Decimal("0")
    if volumenM3 > umbralM3:                                # RN-05
        recargo = recargoTarifa if formaEnvio == TERRESTRE else recargoManual

    return Costo(kilos, precioPorKilo, subtotal, recargo, subtotal + recargo)   # RN-03
