"""Pantallas web (capa de presentación). Solo leen el formulario, llaman a los
servicios y muestran el resultado: no tienen reglas de negocio ni SQL."""
import os
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.datos import catalogo_repo, cliente_repo, encomienda_repo
from app.datos.conexion import consultar
from app.servicios.clientes import ErrorDeValidacion, eliminar_cliente, registrar_cliente
from app.servicios.recepcion import ErrorDeNegocio, cotizar, preparar_encomienda, registrar_encomienda

bp = Blueprint("web", __name__)


def numero(texto, defecto="0"):
    """Convierte '4,3' o '4.3' en Decimal. Lanza InvalidOperation si no es número."""
    return Decimal((texto or defecto).strip().replace(",", "."))


def recepcionista_actual():
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
    return render_template("tarifas.html", tarifas=catalogo_repo.listar_tarifas_vigentes())


@bp.route("/cotizar", methods=["GET", "POST"])
def cotizar_envio():
    costo, error, form = None, None, request.form
    if request.method == "POST":
        try:
            _, costo = cotizar(int(form["origen"]), int(form["destino"]), int(form["tipo"]), form["forma"],
                               numero(form["peso"]), numero(form.get("volumen")), numero(form.get("recargo")))
        except InvalidOperation:
            error = "Revise el peso, el volumen y el recargo: deben ser números."
        except ErrorDeNegocio as e:
            error = str(e)
    return render_template("cotizar.html", ciudades=catalogo_repo.listar_ciudades(),
                           tipos=catalogo_repo.listar_tipos(), costo=costo, error=error, form=form)


# ---------------- HU-07 Clientes ----------------

@bp.route("/clientes")
def clientes():
    q = request.args.get("q", "").strip()
    lista = cliente_repo.buscar(q) if q else cliente_repo.buscar("", limite=20)
    return render_template("clientes.html", clientes=lista, q=q)


@bp.route("/clientes/nuevo", methods=["GET", "POST"])
def cliente_nuevo():
    form = request.form if request.method == "POST" else request.args
    errores = {}
    if request.method == "POST":
        try:
            registrar_cliente(form["ci"], form["nombres"], form["apellidos"], form["telefono"], form.get("email", ""))
            flash(f"Cliente {form['nombres']} {form['apellidos']} registrado.", "ok")
            volver = form.get("volver")
            return redirect(volver if volver and volver.startswith("/") else url_for("web.clientes", q=form["ci"]))
        except ErrorDeValidacion as e:
            errores = e.errores
    return render_template("cliente_form.html", form=form, errores=errores)


@bp.route("/clientes/<int:id_cliente>/eliminar", methods=["POST"])
def cliente_eliminar(id_cliente):
    try:
        eliminar_cliente(id_cliente)
        flash("Cliente eliminado.", "ok")
    except ErrorDeValidacion as e:
        flash(str(e), "error")
    return redirect(url_for("web.clientes"))


# ---------------- HU-09 Encomiendas ----------------

@bp.route("/encomiendas")
def encomiendas():
    return render_template("encomiendas.html", encomiendas=encomienda_repo.listar_recientes())


@bp.route("/encomiendas/nueva", methods=["GET", "POST"])
def encomienda_nueva():
    form = request.form
    resumen, error = None, None
    if request.method == "POST":
        accion = form.get("accion")
        if accion == "cancelar":                               # HU-09, criterio 4
            flash("Registro cancelado: no se guardó nada.", "ok")
            return redirect(url_for("web.encomienda_nueva"))
        try:
            datos = {
                "ci_remitente": form["ci_remitente"], "ci_destinatario": form["ci_destinatario"],
                "id_sucursal_destino": int(form["destino"]), "id_tipo": int(form["tipo"]),
                "forma_envio": form["forma"], "peso_kg": numero(form["peso"], ""),
                "volumen_m3": numero(form.get("volumen")), "recargo_manual": numero(form.get("recargo")),
                "contenido": form.get("contenido", ""),
            }
            if accion == "confirmar":
                codigo = registrar_encomienda(datos, recepcionista_actual(), form.get("declara") == "si")
                flash(f"Encomienda registrada con código de guía {codigo}. El remitente debe pasar a caja.", "ok")
                return redirect(url_for("web.encomienda_detalle", codigo=codigo))
            resumen = preparar_encomienda(datos, recepcionista_actual())   # accion == "calcular"
        except InvalidOperation:
            error = "Revise el peso, el volumen y el recargo: deben ser números."
        except ErrorDeNegocio as e:
            error = str(e)
    empleado = catalogo_repo.obtener_empleado(recepcionista_actual())
    return render_template("encomienda_form.html", form=form, resumen=resumen, error=error,
                           empleado=empleado, sucursales=catalogo_repo.listar_sucursales(),
                           tipos=catalogo_repo.listar_tipos())


@bp.route("/encomiendas/<codigo>")
def encomienda_detalle(codigo):
    return render_template("encomienda_detalle.html", codigo=codigo,
                           seguimiento=encomienda_repo.seguimiento_de(codigo))
