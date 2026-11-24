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

| Historia | Qué hace | Código | Pruebas |
|---|---|---|---|
| HU-10 Calcular costo | Kilos cobrables, tarifa vigente y recargo por volumen | `dominio/costo.py`, `servicios/recepcion.py` → pantalla `/cotizar` | `tests/unit/test_costo.py` (TDD) |
| HU-07 Registrar cliente | Buscar, registrar (sin duplicar CI) y eliminar si no tiene encomiendas | `dominio/validaciones.py`, `servicios/clientes.py`, `datos/cliente_repo.py` → `/clientes` | `test_validaciones.py`, `test_servicios.py` |
| HU-09 Registrar recepción | Calcula, confirma con declaración y guarda Encomienda + Seguimiento en una transacción con código de guía | `servicios/recepcion.py`, `datos/encomienda_repo.py`, `dominio/codigo_guia.py` → `/encomiendas/nueva` | `test_servicios.py`, `test_codigo_guia.py` |

Para probar el flujo completo: registrar dos clientes en **Clientes**, luego **Nueva encomienda**
(Calcular costo → marcar la declaración → Confirmar) y ver su seguimiento.

## Convenciones del equipo

- PEP 8: `snake_case` para funciones y variables, `PascalCase` para clases, nombres en español.
- Pruebas: `test_huXX_caY_descripcion` para la trazabilidad historia → prueba.
- Commits: `HU-XX: qué se hizo` y, si se programó en pareja, la línea
  `Co-authored-by: Nombre <correo>` al final del mensaje.
- Antes de integrar a `main`: `pytest` en verde.
