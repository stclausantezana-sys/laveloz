"""Casos de uso de clientes (HU-07)."""
from app.datos import cliente_repo
from app.dominio.validaciones import normalizar_ci, validar_cliente


class ErrorDeValidacion(Exception):
    def __init__(self, errores):
        super().__init__("; ".join(errores.values()))
        self.errores = errores


def registrar_cliente(ci, nombres, apellidos, telefono, email=""):
    """HU-07, criterios 1 a 3. Devuelve el id del cliente registrado."""
    errores = validar_cliente(ci, nombres, apellidos, telefono, email)
    if errores:
        raise ErrorDeValidacion(errores)
    ci = normalizar_ci(ci)
    if cliente_repo.buscar_por_ci(ci):                        # criterio 2: no duplicar
        raise ErrorDeValidacion({"ci": f"Ya existe un cliente con el CI {ci}."})
    return cliente_repo.registrar(ci, nombres.strip(), apellidos.strip(),
                                  telefono.strip().replace(" ", ""), (email or "").strip() or None)


def eliminar_cliente(id_cliente):
    """HU-07, criterio 4 / RN-13: no se elimina un cliente con encomiendas."""
    if cliente_repo.cantidad_encomiendas(id_cliente) > 0:
        raise ErrorDeValidacion({"cliente": "No se puede eliminar: el cliente tiene encomiendas registradas."})
    cliente_repo.eliminar(id_cliente)
