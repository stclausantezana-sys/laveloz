"""Pruebas contra SQL Server real. Se saltan si no hay DB_CONN en .env."""
import os

import pytest
from dotenv import load_dotenv

load_dotenv()
pytestmark = pytest.mark.skipif(not (os.getenv("DB_CONN") or os.getenv("DB_SERVER")), reason="sin conexión configurada en .env")


def test_hay_tarifas_cargadas():
    from app.datos.catalogo_repo import listar_tarifas_vigentes
    assert len(listar_tarifas_vigentes()) >= 3


def test_tarifa_terrestre_otros_scz_lpz_es_3_bs():
    from decimal import Decimal
    from app.datos.catalogo_repo import buscar_tarifa_vigente
    t = buscar_tarifa_vigente(1, 2, 3, "TERRESTRE")
    assert t["precio_por_kilo"] == Decimal("3.00")


def test_hu07_y_hu09_flujo_completo_en_sql_server():
    """Registra dos clientes y una encomienda reales (deja datos de prueba en la BD)."""
    import random
    from decimal import Decimal
    from app.datos import encomienda_repo
    from app.servicios.clientes import registrar_cliente
    from app.servicios.recepcion import registrar_encomienda

    ci1, ci2 = str(random.randint(10**6, 10**7)), str(random.randint(10**6, 10**7))
    registrar_cliente(ci1, "Prueba", "Remitente", "70000001")
    registrar_cliente(ci2, "Prueba", "Destinatario", "70000002")
    codigo = registrar_encomienda({
        "ci_remitente": ci1, "ci_destinatario": ci2, "id_sucursal_destino": 2, "id_tipo": 3,
        "forma_envio": "TERRESTRE", "peso_kg": Decimal("4.3"), "volumen_m3": Decimal("0.08"),
        "recargo_manual": Decimal("0"), "contenido": "Ropa (prueba)"}, 1, declara_no_prohibido=True)
    seguimiento = encomienda_repo.seguimiento_de(codigo)
    assert seguimiento[0]["estado_nuevo"] == "REGISTRADA"
