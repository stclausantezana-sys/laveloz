"""Control de clientes (HU-07 / CU-10 Registrar cliente): clase CtrlCliente.

La pantalla FrmCliente (plantillas clientes.html y cliente_form.html) solo habla
con este controlador; el controlador usa ClienteRepositorio para llegar a la BD.
"""
from app.datos.cliente_repo import ClienteRepositorio
from app.dominio.validaciones import normalizarCi, validarCliente


class ErrorDeValidacion(Exception):
    def __init__(self, errores):
        super().__init__("; ".join(errores.values()))
        self.errores = errores


class CtrlCliente:

    def __init__(self, clientes=None):
        self.clientes = clientes or ClienteRepositorio()

    def buscarClientes(self, texto="", limite=20):
        return self.clientes.buscar(texto, limite)

    def registrarCliente(self, ci, nombres, apellidos, telefono, email=""):
        """HU-07, criterios 1 a 3. Devuelve el id del cliente registrado."""
        errores = validarCliente(ci, nombres, apellidos, telefono, email)
        if errores:
            raise ErrorDeValidacion(errores)
        ci = normalizarCi(ci)
        if self.clientes.buscarPorCi(ci):                           # criterio 2: no duplicar
            raise ErrorDeValidacion({"ci": f"Ya existe un cliente con el CI {ci}."})
        return self.clientes.guardar({
            "ci": ci, "nombres": nombres.strip(), "apellidos": apellidos.strip(),
            "telefono": telefono.strip().replace(" ", ""), "email": (email or "").strip() or None,
        })

    def eliminarCliente(self, idCliente):
        """HU-07, criterio 4 / RN-13: no se elimina un cliente con encomiendas."""
        if self.clientes.cantidadEncomiendas(idCliente) > 0:
            raise ErrorDeValidacion({"cliente": "No se puede eliminar: el cliente tiene encomiendas registradas."})
        self.clientes.eliminar(idCliente)
