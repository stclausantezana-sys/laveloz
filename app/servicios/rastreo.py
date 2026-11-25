"""Control del rastreo público (HU-19 / CU-03 Rastrear encomienda): clase CtrlRastreo."""
from app.datos.rastreo_repo import RastreoRepositorio

ETAPAS = [("Recepción", "fecha_hora_recepcion"), ("Pago", "fecha_hora_pago"),
          ("Salida", "fecha_hora_salida"), ("Llegada a destino", "fecha_hora_llegada"),
          ("Entrega", "fecha_hora_entrega")]
CAMPOS_PUBLICOS = ("codigo_guia", "estado", "tipo", "origen", "destino")


class CtrlRastreo:

    def __init__(self, rastreo=None):
        self.rastreo = rastreo or RastreoRepositorio()

    def rastrear(self, codigoGuia):
        """HU-19: estado actual y fecha y hora de cada etapa; None si el código no existe (criterio 2)."""
        fila = self.rastreo.buscarPorCodigo((codigoGuia or "").strip().upper())
        if fila is None:
            return None
        resultado = {campo: fila[campo] for campo in CAMPOS_PUBLICOS}       # criterio 3: sin CI ni teléfono
        resultado["etapas"] = [{"etapa": nombre, "fecha_hora": fila[campo]} for nombre, campo in ETAPAS]
        return resultado
