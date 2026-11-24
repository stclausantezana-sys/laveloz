"""Casos de uso de recepción (HU-09 y HU-10): es el "CtrlRecepcion" del diseño.

Coordina el dominio (reglas puras) con los repositorios (base de datos).
"""
from datetime import date
from decimal import Decimal

from app.datos import catalogo_repo, cliente_repo, encomienda_repo
from app.datos.conexion import transaccion
from app.dominio.codigo_guia import generar_codigo_guia
from app.dominio.costo import calcular_costo
from app.dominio.validaciones import normalizar_ci, validar_encomienda


class ErrorDeNegocio(Exception):
    """Error que se muestra tal cual al usuario."""


def cotizar(id_ciudad_origen, id_ciudad_destino, id_tipo, forma_envio, peso_kg, volumen_m3,
            recargo_manual=Decimal("0")):
    """HU-10: busca la tarifa vigente y calcula el costo. Devuelve (tarifa, costo)."""
    if id_ciudad_origen == id_ciudad_destino:
        raise ErrorDeNegocio("El destino debe ser distinto del origen.")
    tarifa = catalogo_repo.buscar_tarifa_vigente(id_ciudad_origen, id_ciudad_destino, id_tipo, forma_envio)
    if tarifa is None:
        raise ErrorDeNegocio("No hay tarifa para este trayecto.")          # HU-10, criterio 4
    try:
        costo = calcular_costo(peso_kg, volumen_m3,
                               precio_por_kilo=tarifa["precio_por_kilo"],
                               umbral_m3=tarifa["umbral_volumen_m3"],
                               recargo_tarifa=tarifa["recargo_volumen"],
                               forma_envio=forma_envio,
                               recargo_manual=recargo_manual)
    except ValueError as e:
        raise ErrorDeNegocio(str(e)) from e
    return tarifa, costo


def preparar_encomienda(d, id_recepcionista):
    """Valida los datos de la pantalla y calcula el costo, SIN guardar nada.

    `d` es un diccionario con: ci_remitente, ci_destinatario, id_sucursal_destino,
    id_tipo, forma_envio, peso_kg, volumen_m3, recargo_manual, contenido.
    Devuelve un diccionario listo para guardar con registrar_encomienda().
    """
    emp = catalogo_repo.obtener_empleado(id_recepcionista)
    if emp is None or not emp["activo"] or emp["rol"] != "RECEPCIONISTA":
        raise ErrorDeNegocio("El empleado configurado no es un recepcionista activo (revise RECEPCIONISTA_ID en .env).")

    errores = validar_encomienda(d["peso_kg"], d["volumen_m3"], emp["id_sucursal"],
                                 d["id_sucursal_destino"], d["contenido"])
    if errores:
        raise ErrorDeNegocio(" ".join(errores.values()))

    remitente = cliente_repo.buscar_por_ci(normalizar_ci(d["ci_remitente"]))
    destinatario = cliente_repo.buscar_por_ci(normalizar_ci(d["ci_destinatario"]))
    if remitente is None:
        raise ErrorDeNegocio("El remitente no está registrado: regístrelo primero en Clientes.")    # RN-01
    if destinatario is None:
        raise ErrorDeNegocio("El destinatario no está registrado: regístrelo primero en Clientes.")

    id_ciudad_destino = catalogo_repo.ciudad_de_sucursal(d["id_sucursal_destino"])
    tarifa, costo = cotizar(emp["id_ciudad"], id_ciudad_destino, d["id_tipo"], d["forma_envio"],
                            d["peso_kg"], d["volumen_m3"], d.get("recargo_manual", Decimal("0")))
    return {
        "empleado": emp, "remitente": remitente, "destinatario": destinatario,
        "id_remitente": remitente["id_cliente"], "id_destinatario": destinatario["id_cliente"],
        "id_tipo": d["id_tipo"], "id_tarifa": tarifa["id_tarifa"],
        "id_sucursal_origen": emp["id_sucursal"], "id_sucursal_destino": d["id_sucursal_destino"],
        "id_recepcionista": emp["id_empleado"], "contenido": d["contenido"].strip(),
        "peso_kg": d["peso_kg"], "volumen_m3": d["volumen_m3"],
        "kilos_cobrados": costo.kilos_cobrados, "precio_por_kilo": costo.precio_por_kilo,
        "recargo": costo.recargo, "total": costo.total, "costo": costo,
    }


def registrar_encomienda(d, id_recepcionista, declara_no_prohibido):
    """HU-09: guarda la encomienda en estado REGISTRADA y su seguimiento inicial.

    Todo ocurre en UNA transacción: si algo falla, no se guarda nada.
    Devuelve el código de guía generado.
    """
    if not declara_no_prohibido:
        raise ErrorDeNegocio("El remitente debe aceptar la declaración de que el contenido no es prohibido.")  # RN-02
    e = preparar_encomienda(d, id_recepcionista)
    with transaccion() as cur:
        correlativo = encomienda_repo.siguiente_correlativo(cur, e["id_sucursal_origen"])
        e["codigo_guia"] = generar_codigo_guia(e["empleado"]["codigo_sucursal"], date.today(), correlativo)
        id_encomienda = encomienda_repo.insertar(cur, e)
        encomienda_repo.insertar_seguimiento(cur, id_encomienda, id_recepcionista, None, "REGISTRADA")
    return e["codigo_guia"]
