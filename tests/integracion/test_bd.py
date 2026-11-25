"""Pruebas contra SQL Server real. Se saltan si no hay DB_SERVER o DB_CONN en .env."""
import os

import pytest
from dotenv import load_dotenv

load_dotenv()
pytestmark = pytest.mark.skipif(not (os.getenv("DB_CONN") or os.getenv("DB_SERVER")),
                                reason="sin conexión configurada en .env")


def test_hay_tarifas_cargadas():
    from app.datos.catalogo_repo import TarifaRepositorio
    assert len(TarifaRepositorio().listarVigentes()) >= 3


def test_tarifa_terrestre_otros_scz_lpz_es_3_bs():
    from decimal import Decimal
    from app.datos.catalogo_repo import TarifaRepositorio
    t = TarifaRepositorio().buscarVigente(1, 2, 3, "TERRESTRE")
    assert t["precio_por_kilo"] == Decimal("3.00")


def test_hu07_y_hu09_flujo_completo_en_sql_server():
    """Registra dos clientes y una encomienda reales (deja datos de prueba en la BD)."""
    import random
    from decimal import Decimal
    from app.datos.encomienda_repo import EncomiendaRepositorio, SeguimientoRepositorio
    from app.servicios.clientes import CtrlCliente
    from app.servicios.recepcion import CtrlRecepcion, EncomiendaDTO

    ci1, ci2 = str(random.randint(10**6, 10**7)), str(random.randint(10**6, 10**7))
    CtrlCliente().registrarCliente(ci1, "Prueba", "Remitente", "70000001")
    CtrlCliente().registrarCliente(ci2, "Prueba", "Destinatario", "70000002")
    codigo = CtrlRecepcion().registrarEncomienda(EncomiendaDTO(
        ciRemitente=ci1, ciDestinatario=ci2, idSucursalDestino=2, idTipo=3, formaEnvio="TERRESTRE",
        pesoKg=Decimal("4.3"), volumenM3=Decimal("0.08"), contenido="Ropa (prueba)",
        declaraNoProhibido=True), 1)
    assert EncomiendaRepositorio().existeCodigo(codigo)
    assert SeguimientoRepositorio().listarPorCodigo(codigo)[0]["estado_nuevo"] == "REGISTRADA"
