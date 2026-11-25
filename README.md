# Currier La Veloz – Sistema de gestión de encomiendas

Proyecto final SIS-303 (Scrum + XP) · Python 3 + Flask + SQL Server

## Cómo ejecutarlo en Windows

**Ya hecho en la laptop de Claudio:** la base `LaVelozDB` está creada en `.\SQLEXPRESS`.

1. Instalar **Python** desde <https://www.python.org/downloads/> y marcar
   **"Add python.exe to PATH"** en la primera pantalla del instalador.
2. Descomprimir el proyecto (por ejemplo en Documentos).
3. Hacer **doble clic en `iniciar.bat`**. Crea el entorno, instala las dependencias,
   prueba la conexión, corre las pruebas y abre el sistema en <http://127.0.0.1:5000>.

Si el servidor tiene otro nombre, cambiar `DB_SERVER` en el archivo `.env`.
Si dice que falta el controlador ODBC, instalar **ODBC Driver 18 for SQL Server** de Microsoft.

### En otra computadora (por ejemplo la de Thiago)

Antes del paso 3: en SSMS abrir `db\LaVeloz_crear_bd.sql` y ejecutarlo con **F5**.

### Si la base ya estaba creada con la versión anterior

La primera versión del script solo traía tarifas de Santa Cruz a La Paz. Para agregar las de
todas las rutas (Santa Cruz, La Paz y Cochabamba en los dos sentidos: 36 tarifas), abrir
`db\LaVeloz_tarifas_todas_las_rutas.sql` en SSMS y ejecutarlo con **F5**. No borra nada.

### Comandos a mano (opcional)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python probar_conexion.py
pytest
python -m flask --app app run --debug
```

## Estructura (capas)

```
app/dominio/     reglas de negocio puras, sin BD  → se prueban con TDD
app/datos/       consultas SQL (repositorios)
app/servicios/   casos de uso: unen dominio + datos
app/web/         rutas Flask y plantillas HTML
tests/unit/      pruebas rápidas sin BD
tests/integracion/ pruebas contra SQL Server (se saltan si no hay .env)
db/              script de la base de datos
```

## Estado del Sprint 1

| Historia | Qué hace | Clases y métodos | Pruebas |
|---|---|---|---|
| HU-10 Calcular costo | Kilos cobrables, tarifa vigente y recargo por volumen | `Costo`, `calcularCosto()` (dominio/costo.py); `CtrlTarifa.obtenerTarifa()`, `CtrlTarifa.calcularCosto()`; `TarifaRepositorio.buscarVigente()` → pantalla `/cotizar` | `test_costo.py` (TDD) |
| HU-07 Registrar cliente | Buscar, registrar (sin duplicar CI) y eliminar si no tiene encomiendas | `CtrlCliente.registrarCliente()`, `eliminarCliente()`; `ClienteRepositorio.buscarPorCi()`, `guardar()` → `/clientes` | `test_validaciones.py`, `test_servicios.py` |
| HU-09 Registrar recepción | Calcula, confirma con declaración y guarda Encomienda + Seguimiento en una transacción con código de guía | `EncomiendaDTO`; `CtrlRecepcion.buscarCliente()`, `cotizar()`, `registrarEncomienda()`, `generarCodigoGuia()`; `EncomiendaRepositorio.guardar()`; `SeguimientoRepositorio.registrar()`; `ConexionBD` → `/encomiendas/nueva` | `test_servicios.py`, `test_codigo_guia.py` |

## Estado del Sprint 2

| Historia | Qué hace | Clases y métodos | Pruebas |
|---|---|---|---|
| HU-08 Verificar productos prohibidos | Bloquea la recepción si el contenido tiene una palabra prohibida (sin importar mayúsculas ni tildes) | `CtrlVerificacion.esProhibido()`, `buscarProhibido()` (dominio/verificacion.py), `ProductoProhibidoRepositorio` | `test_verificacion.py` (TDD), `test_servicios.py` |
| HU-13 Cobrar y emitir comprobante | La cajera busca por código de guía, cobra (efectivo, tarjeta o QR), la encomienda pasa a PAGADA y sale el comprobante | `CtrlCaja.buscarEncomienda()`, `cobrarEncomienda()`, `PagoRepositorio`, `formatearNroComprobante()` → `/caja` | `test_caja.py` |
| HU-19 Rastrear encomienda | El cliente consulta su código de guía y ve el estado y la fecha de cada etapa, sin CI ni teléfono | `CtrlRastreo.rastrear()`, `RastreoRepositorio` → `/rastrear` | `test_rastreo.py` |

Para probar el flujo completo: registrar dos clientes en **Clientes**, luego **Nueva encomienda**
(Calcular costo → marcar la declaración → Confirmar), cobrarla en **Caja** y consultarla en **Rastrear**.
Si en el contenido se escribe «gasolina», el sistema bloquea el registro (HU-08).

## Del diseño al código (los nombres coinciden)

| Diagrama (CU-11) | Código |
|---|---|
| FrmRecepcionEncomienda «boundary» | `templates/encomienda_form.html` + ruta `/encomiendas/nueva` (`web/rutas.py`) |
| FrmCliente «boundary» | `templates/clientes.html`, `cliente_form.html` + rutas `/clientes` |
| CtrlRecepcion «control» | `servicios/recepcion.py` → `class CtrlRecepcion` |
| CtrlTarifa «control» | `servicios/recepcion.py` → `class CtrlTarifa` |
| CtrlVerificacion «control» | `servicios/verificacion.py` → `class CtrlVerificacion` (`esProhibido`) |
| CtrlCaja «control» (Sprint 2) | `servicios/caja.py` → `class CtrlCaja` |
| CtrlRastreo «control» (Sprint 2) | `servicios/rastreo.py` → `class CtrlRastreo` |
| Costo | `dominio/costo.py` → `class Costo` |
| EncomiendaDTO | `servicios/recepcion.py` → `class EncomiendaDTO` |
| IClienteRepositorio | `datos/cliente_repo.py` → `class ClienteRepositorio` |
| IEncomiendaRepositorio / ISeguimientoRepositorio | `datos/encomienda_repo.py` → `EncomiendaRepositorio`, `SeguimientoRepositorio` |
| ITarifaRepositorio | `datos/catalogo_repo.py` → `class TarifaRepositorio` |
| IProductoProhibidoRepositorio | `datos/producto_repo.py` → `class ProductoProhibidoRepositorio` |
| IPagoRepositorio | `datos/pago_repo.py` → `class PagoRepositorio` |
| ConexionBD | `datos/conexion.py` → `class ConexionBD` (`iniciarTransaccion`, `confirmar`, `revertir`) |

En Python no hay interfaces: cada clase `XRepositorio` cumple el papel de la interfaz `IXRepositorio` del diseño.

## Convenciones del equipo

- Clases en `PascalCase` y métodos en `camelCase`, **con los mismos nombres de los diagramas UML**
  (así diseño y código cuadran). Variables locales y columnas de la BD en `snake_case`. Nombres en español.
- Pruebas: `test_huXX_caY_descripcion` para la trazabilidad historia → prueba.
- Los controladores reciben sus repositorios en el constructor: en las pruebas se les pasan repositorios falsos.
- Commits: `HU-XX: qué se hizo` y, si se programó en pareja, la línea
  `Co-authored-by: Nombre <correo>` al final del mensaje.
- Ramas: una rama por sprint (`sprint-1`, `sprint-2`), se integra a `main` con una pull request revisada por el compañero.
- Antes de integrar a `main`: `pytest` en verde.
