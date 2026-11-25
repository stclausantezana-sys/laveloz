"""Pruebas de HU-08 Verificar productos prohibidos (hechas con TDD: la prueba primero)."""
from app.dominio.verificacion import buscarProhibido, normalizarTexto

PRODUCTOS = [
    {"nombre": "Armas, municiones y explosivos", "palabras_clave": "arma,pistola,municion,bala,explosivo,dinamita"},
    {"nombre": "Materiales inflamables", "palabras_clave": "gasolina,diesel,combustible,polvora,inflamable"},
]


def test_hu08_ca1_descripcion_con_palabra_prohibida():
    p = buscarProhibido("Bidón de gasolina para el generador", PRODUCTOS)
    assert p["nombre"] == "Materiales inflamables"


def test_hu08_ca2_descripcion_sin_coincidencias():
    assert buscarProhibido("Ropa, zapatos y dos libros", PRODUCTOS) is None


def test_hu08_ca3_mayusculas_y_tildes_igual_se_detectan():
    assert buscarProhibido("GASOLINA", PRODUCTOS) is not None
    assert buscarProhibido("Pólvora para fuegos artificiales", PRODUCTOS) is not None
    assert buscarProhibido("caja de MUNICIÓN", PRODUCTOS)["nombre"].startswith("Armas")


def test_hu08_plural_se_detecta():
    assert buscarProhibido("tres balas", PRODUCTOS) is not None


def test_hu08_palabra_dentro_de_otra_no_es_prohibida():
    # «arma» no debe bloquear «armario»
    assert buscarProhibido("Armario de madera desarmado", PRODUCTOS) is None


def test_normalizar_texto():
    assert normalizarTexto("Pólvora ÑANDÚ") == "polvora nandu"
