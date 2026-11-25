"""Verificación de productos prohibidos (HU-08, RN-02): reglas puras, sin BD.

Se compara la descripción del contenido con las palabras clave de cada producto
prohibido. Se ignoran mayúsculas y tildes (HU-08, criterio 3) y se aceptan plurales.
"""
import re
import unicodedata


def normalizarTexto(texto):
    """'Pólvora GASOLINA' -> 'polvora gasolina'."""
    descompuesto = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn").lower()


def palabrasClave(producto):
    return [normalizarTexto(p).strip() for p in producto["palabras_clave"].split(",") if p.strip()]


def buscarProhibido(descripcion, productos):
    """Devuelve el primer producto prohibido que coincide con la descripción, o None.

    Busca la palabra completa (\\b): «arma» detecta «armas», pero no «armario».
    """
    texto = normalizarTexto(descripcion)
    for producto in productos:
        for palabra in palabrasClave(producto):
            if re.search(rf"\b{re.escape(palabra)}(s|es)?\b", texto):
                return producto
    return None
