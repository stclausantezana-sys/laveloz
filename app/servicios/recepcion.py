"""Capa de lógica de negocio de la recepción (HU-09 y HU-10, CU-11 del diseño).

  EncomiendaDTO   datos que llegan de la pantalla FrmRecepcionEncomienda
  CtrlTarifa      obtiene la tarifa vigente y calcula el costo (HU-10)
  CtrlRecepcion   coordina el caso de uso y guarda Encomienda + Seguimiento (HU-09);
                  antes de calcular le pregunta a CtrlVerificacion si el contenido es prohibido (HU-08)
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.datos.catalogo_repo import CatalogoRepositorio, TarifaRepositorio
from app.datos.cliente_repo import ClienteRepositorio
from app.datos.conexion import ConexionBD
from app.datos.encomienda_repo import EncomiendaRepositorio, SeguimientoRepositorio
from app.dominio import costo as reglasCosto
from app.dominio.codigo_guia import formatearCodigoGuia
from app.dominio.validaciones import normalizarCi, validarEncomienda
from app.servicios.verificacion import CtrlVerificacion


class ErrorDeNegocio(Exception):
    """Error que se muestra tal cual al usuario."""


@dataclass
class EncomiendaDTO:
    ciRemitente: str = ""
    ciDestinatario: str = ""
    idTipo: int = 0
    formaEnvio: str = reglasCosto.TERRESTRE
    idSucursalOrigen: int = 0          # lo completa CtrlRecepcion con la sucursal del recepcionista
    idSucursalDestino: int = 0
    pesoKg: Decimal = Decimal("0")
    volumenM3: Decimal = Decimal("0")
    recargoManual: Decimal = Decimal("0")
    contenido: str = ""
    declaraNoProhibido: bool = False


class CtrlTarifa:

    def __init__(self, tarifas=None, catalogo=None):
        self.tarifas = tarifas or TarifaRepositorio()
        self.catalogo = catalogo or CatalogoRepositorio()

    def obtenerTarifa(self, dto):
        """Tarifa vigente del trayecto entre la sucursal de origen y la de destino."""
        return self.obtenerTarifaEntreCiudades(self.catalogo.ciudadDeSucursal(dto.idSucursalOrigen),
                                               self.catalogo.ciudadDeSucursal(dto.idSucursalDestino),
                                               dto.idTipo, dto.formaEnvio)

    def obtenerTarifaEntreCiudades(self, idCiudadOrigen, idCiudadDestino, idTipo, formaEnvio):
        if idCiudadOrigen == idCiudadDestino:
            raise ErrorDeNegocio("El destino debe ser distinto del origen.")
        tarifa = self.tarifas.buscarVigente(idCiudadOrigen, idCiudadDestino, idTipo, formaEnvio)
        if tarifa is None:
            raise ErrorDeNegocio("No hay tarifa para este trayecto.")           # HU-10, criterio 4
        return tarifa

    def calcularCosto(self, t, dto):
        """HU-10: aplica RN-03, RN-04 y RN-05 con la tarifa `t`. Devuelve un Costo."""
        try:
            return reglasCosto.calcularCosto(dto.pesoKg, dto.volumenM3,
                                             precioPorKilo=t["precio_por_kilo"],
                                             umbralM3=t["umbral_volumen_m3"],
                                             recargoTarifa=t["recargo_volumen"],
                                             formaEnvio=dto.formaEnvio,
                                             recargoManual=dto.recargoManual)
        except ValueError as e:
            raise ErrorDeNegocio(str(e)) from e


class CtrlRecepcion:

    def __init__(self, clientes=None, encomiendas=None, seguimientos=None, catalogo=None,
                 ctrlTarifa=None, ctrlVerificacion=None, conexion=ConexionBD):
        self.clientes = clientes or ClienteRepositorio()
        self.encomiendas = encomiendas or EncomiendaRepositorio()
        self.seguimientos = seguimientos or SeguimientoRepositorio()
        self.catalogo = catalogo or CatalogoRepositorio()
        self.ctrlTarifa = ctrlTarifa or CtrlTarifa(catalogo=self.catalogo)
        self.ctrlVerificacion = ctrlVerificacion or CtrlVerificacion()
        self.conexion = conexion

    def buscarCliente(self, ci):
        return self.clientes.buscarPorCi(normalizarCi(ci))

    def prepararEncomienda(self, dto, idEmpleado):
        """Valida los datos de la pantalla y calcula el costo, SIN guardar nada.
        Devuelve un diccionario listo para guardar con registrarEncomienda()."""
        emp = self.catalogo.obtenerEmpleado(idEmpleado)
        if emp is None or not emp["activo"] or emp["rol"] != "RECEPCIONISTA":
            raise ErrorDeNegocio("El empleado configurado no es un recepcionista activo "
                                 "(revise RECEPCIONISTA_ID en .env).")
        dto.idSucursalOrigen = emp["id_sucursal"]

        errores = validarEncomienda(dto.pesoKg, dto.volumenM3, dto.idSucursalOrigen,
                                    dto.idSucursalDestino, dto.contenido)
        if errores:
            raise ErrorDeNegocio(" ".join(errores.values()))

        prohibido = self.ctrlVerificacion.productoProhibido(dto.contenido)        # HU-08, RN-02
        if prohibido is not None:
            raise ErrorDeNegocio(f"Producto prohibido: «{prohibido['nombre']}». "
                                 "No se puede recibir esta encomienda.")

        remitente = self.buscarCliente(dto.ciRemitente)
        destinatario = self.buscarCliente(dto.ciDestinatario)
        if remitente is None:                                                    # RN-01
            raise ErrorDeNegocio("El remitente no está registrado: regístrelo primero en Clientes.")
        if destinatario is None:
            raise ErrorDeNegocio("El destinatario no está registrado: regístrelo primero en Clientes.")

        tarifa = self.ctrlTarifa.obtenerTarifa(dto)
        costo = self.ctrlTarifa.calcularCosto(tarifa, dto)
        return {
            "empleado": emp, "remitente": remitente, "destinatario": destinatario, "costo": costo,
            "id_remitente": remitente["id_cliente"], "id_destinatario": destinatario["id_cliente"],
            "id_tipo": dto.idTipo, "id_tarifa": tarifa["id_tarifa"],
            "id_sucursal_origen": dto.idSucursalOrigen, "id_sucursal_destino": dto.idSucursalDestino,
            "id_recepcionista": emp["id_empleado"], "contenido": dto.contenido.strip(),
            "peso_kg": dto.pesoKg, "volumen_m3": dto.volumenM3,
            "kilos_cobrados": costo.kilosCobrados, "precio_por_kilo": costo.precioPorKilo,
            "recargo": costo.recargo, "total": costo.total,
        }

    def cotizar(self, dto, idEmpleado):
        """Botón «Calcular costo» de la pantalla: devuelve el Costo sin guardar."""
        return self.prepararEncomienda(dto, idEmpleado)["costo"]

    def generarCodigoGuia(self, cur, empleado):
        """RN-08: SUCURSAL-AAAAMMDD-correlativo, dentro de la transacción abierta."""
        correlativo = self.encomiendas.siguienteCorrelativo(cur, empleado["id_sucursal"])
        return formatearCodigoGuia(empleado["codigo_sucursal"], date.today(), correlativo)

    def registrarEncomienda(self, dto, idEmpleado):
        """HU-09: guarda la encomienda en estado REGISTRADA y su seguimiento inicial.

        Todo ocurre en UNA transacción (ConexionBD): si algo falla, no se guarda nada.
        Devuelve el código de guía generado.
        """
        if not dto.declaraNoProhibido:                                           # RN-02
            raise ErrorDeNegocio("El remitente debe aceptar la declaración de que el contenido no es prohibido.")
        e = self.prepararEncomienda(dto, idEmpleado)
        with self.conexion() as cur:
            e["codigo_guia"] = self.generarCodigoGuia(cur, e["empleado"])
            idEncomienda = self.encomiendas.guardar(cur, e)
            self.seguimientos.registrar(cur, idEncomienda, idEmpleado, None, "REGISTRADA")    # RN-12
        return e["codigo_guia"]
