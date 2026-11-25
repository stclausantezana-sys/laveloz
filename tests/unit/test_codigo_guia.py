from datetime import date

import pytest

from app.dominio.codigo_guia import formatearCodigoGuia


def test_formato_del_codigo_de_guia():
    assert formatearCodigoGuia("SCZ", date(2026, 11, 20), 1) == "SCZ-20261120-00001"


def test_sucursal_debe_tener_tres_letras():
    with pytest.raises(ValueError):
        formatearCodigoGuia("SC", date(2026, 11, 20), 1)


def test_hu13_numero_de_comprobante():
    from app.dominio.codigo_guia import formatearNroComprobante
    assert formatearNroComprobante("SCZ", date(2026, 11, 25), 7) == "CSCZ-20261125-00007"
