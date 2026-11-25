"""Pantallas web (capa de presentación = fronteras del diseño).

  FrmCliente               -> clientes.html y cliente_form.html (rutas /clientes...)
  FrmRecepcionEncomienda   -> encomienda_form.html (ruta /encomiendas/nueva)

Solo leen el formulario, arman el DTO, llaman a los controladores y muestran el
resultado: no tienen reglas de negocio ni SQL.
"""
import os
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.datos.catalogo_repo import CatalogoRepositorio, TarifaRepositorio
from app.datos.conexion import consultar
from app.datos.encomienda_repo import EncomiendaRepositorio, SeguimientoRepositorio
from app.servicios.clientes import CtrlCliente, ErrorDeValidacion
from app.servicios.recepcion import CtrlRecepcion, CtrlTarifa, EncomiendaDTO, ErrorDeNegocio

bp = Blueprint("web", __name__)


def numero(texto, defecto="0"):
    """Convierte '4,3' o '4.3' en Decimal. Lanza InvalidOperation si no es número."""
    return Decimal((texto or defecto).strip().replace(",", "."))


def recepcionistaActual():
    # Release 1: no hay inicio de sesión (HU-01 está en el Sprint 4).
    # Se usa el recepcionista de prueba configurado en .env.
    return int(os.getenv("RECEPCIONISTA_ID", "1"))


# ---------------- Inicio y catálogos ----------------

@bp.route("/")
def inicio():
    estado, error = None, None
    try:
        estado = consultar("""
            SELECT (SELECT COUNT(*) FROM Ciudad) AS ciudades,
                   (SELECT COUNT(*) FROM Sucursal) AS sucursales,
                   (SELECT COUNT(*) FROM Tarifa WHERE activa = 1) AS tarifas,
                   (SELECT COUNT(*) FROM Cliente) AS clientes,
                   (SELECT COUNT(*) FROM Encomienda) AS encomiendas
        """)[0]
    except Exception as e:  # se muestra en pantalla para diagnosticar la conexión
        error = str(e)
    return render_template("inicio.html", estado=estado, error=error)


@bp.route("/tarifas")
def tarifas():
    return render_template("tarifas.html", tarifas=TarifaRepositorio().listarVigentes())


@bp.route("/cotizar", methods=["GET", "POST"])
def cotizar_envio():
    """HU-10: calcula el costo entre dos ciudades sin registrar nada."""
    costo, error, form = None, None, request.form
    if request.method == "POST":
        try:
            ctrl = CtrlTarifa()
            dto = EncomiendaDTO(idTipo=int(form["tipo"]), formaEnvio=form["forma"],
                                pesoKg=numero(form["peso"]), volumenM3=numero(form.get("volumen")),
                                recargoManual=numero(form.get("recargo")))
            tarifa = ctrl.obtenerTarifaEntreCiudades(int(form["origen"]), int(form["destino"]),
                                                     dto.idTipo, dto.formaEnvio)
            costo = ctrl.calcularCosto(tarifa, dto)
        except InvalidOperation:
            error = "Revise el peso, el volumen y el recargo: deben ser números."
        except ErrorDeNegocio as e:
            error = str(e)
    catalogo = CatalogoRepositorio()
    return render_template("cotizar.html", ciudades=catalogo.listarCiudades(),
                           tipos=catalogo.listarTipos(), costo=costo, error=error, form=form)


# ---------------- HU-07 Clientes (FrmCliente) ----------------

@bp.route("/clientes")
def clientes():
    q = request.args.get("q", "").strip()
    lista = CtrlCliente().buscarClientes(q, limite=50 if q else 20)
    return render_template("clientes.html", clientes=lista, q=q)


@bp.route("/clientes/nuevo", methods=["GET", "POST"])
def cliente_nuevo():
    form = request.form if request.method == "POST" else request.args
    errores = {}
    if request.method == "POST":
        try:
            CtrlCliente().registrarCliente(form["ci"], form["nombres"], form["apellidos"],
                                           form["telefono"], form.get("email", ""))
            flash(f"Cliente {form['nombres']} {form['apellidos']} registrado.", "ok")
            volver = form.get("volver")
            return redirect(volver if volver and volver.startswith("/") else url_for("web.clientes", q=form["ci"]))
        except ErrorDeValidacion as e:
            errores = e.errores
    return render_template("cliente_form.html", form=form, errores=errores)


@bp.route("/clientes/<int:id_cliente>/eliminar", methods=["POST"])
def cliente_eliminar(id_cliente):
    try:
        CtrlCliente().eliminarCliente(id_cliente)
        flash("Cliente eliminado.", "ok")
    except ErrorDeValidacion as e:
        flash(str(e), "error")
    return redirect(url_for("web.clientes"))


# ---------------- HU-09 Encomiendas (FrmRecepcionEncomienda) ----------------

@bp.route("/encomiendas")
def encomiendas():
    return render_template("encomiendas.html", encomiendas=EncomiendaRepositorio().listarRecientes())


@bp.route("/encomiendas/nueva", methods=["GET", "POST"])
def encomienda_nueva():
    form = request.form
    resumen, error = None, None
    ctrl = CtrlRecepcion()
    if request.method == "POST":
        accion = form.get("accion")
        if accion == "cancelar":                               # HU-09, criterio 4
            flash("Registro cancelado: no se guardó nada.", "ok")
            return redirect(url_for("web.encomienda_nueva"))
        try:
            dto = EncomiendaDTO(
                ciRemitente=form["ci_remitente"], ciDestinatario=form["ci_destinatario"],
                idSucursalDestino=int(form["destino"]), idTipo=int(form["tipo"]),
                formaEnvio=form["forma"], pesoKg=numero(form["peso"], ""),
                volumenM3=numero(form.get("volumen")), recargoManual=numero(form.get("recargo")),
                contenido=form.get("contenido", ""), declaraNoProhibido=form.get("declara") == "si")
            if accion == "confirmar":
                codigo = ctrl.registrarEncomienda(dto, recepcionistaActual())
                flash(f"Encomienda registrada con código de guía {codigo}. El remitente debe pasar a caja.", "ok")
                return redirect(url_for("web.encomienda_detalle", codigo=codigo))
            resumen = ctrl.prepararEncomienda(dto, recepcionistaActual())   # accion == "calcular"
        except InvalidOperation:
            error = "Revise el peso, el volumen y el recargo: deben ser números."
        except ErrorDeNegocio as e:
            error = str(e)
    catalogo = CatalogoRepositorio()
    return render_template("encomienda_form.html", form=form, resumen=resumen, error=error,
                           empleado=catalogo.obtenerEmpleado(recepcionistaActual()),
                           sucursales=catalogo.listarSucursales(), tipos=catalogo.listarTipos())


@bp.route("/encomiendas/<codigo>")
def encomienda_detalle(codigo):
    return render_template("encomienda_detalle.html", codigo=codigo,
                           seguimiento=SeguimientoRepositorio().listarPorCodigo(codigo))
