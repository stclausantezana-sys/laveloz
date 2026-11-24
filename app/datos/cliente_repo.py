"""Repositorio de clientes (HU-07 Registrar cliente).

Todas las consultas usan parámetros (?): NUNCA se arma el SQL sumando textos,
así se evita la inyección SQL.
"""
from .conexion import consultar, transaccion

COLUMNAS = "id_cliente, ci, nombres, apellidos, telefono, email"


def buscar_por_ci(ci):
    filas = consultar(f"SELECT {COLUMNAS} FROM Cliente WHERE ci = ?", ci)
    return filas[0] if filas else None


def buscar(texto, limite=50):
    """Busca por CI o por parte del nombre o apellido."""
    patron = f"%{texto.strip()}%"
    return consultar(f"""
        SELECT TOP (?) {COLUMNAS} FROM Cliente
        WHERE ci LIKE ? OR nombres LIKE ? OR apellidos LIKE ?
        ORDER BY apellidos, nombres
    """, limite, patron, patron, patron)


def registrar(ci, nombres, apellidos, telefono, email=None):
    """Inserta un cliente y devuelve su id. El CI duplicado lo rechaza la BD (UQ_Cliente_ci)."""
    with transaccion() as cur:
        cur.execute("""
            INSERT INTO Cliente (ci, nombres, apellidos, telefono, email)
            OUTPUT INSERTED.id_cliente
            VALUES (?, ?, ?, ?, ?)
        """, ci, nombres, apellidos, telefono, email or None)
        return cur.fetchone()[0]


def cantidad_encomiendas(id_cliente):
    return consultar("""
        SELECT COUNT(*) AS n FROM Encomienda
        WHERE id_remitente = ? OR id_destinatario = ?
    """, id_cliente, id_cliente)[0]["n"]


def eliminar(id_cliente):
    with transaccion() as cur:
        cur.execute("DELETE FROM Cliente WHERE id_cliente = ?", id_cliente)
