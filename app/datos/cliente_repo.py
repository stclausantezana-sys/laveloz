"""Repositorio de clientes (HU-07 Registrar cliente): implementa IClienteRepositorio.

Todas las consultas usan parámetros (?): NUNCA se arma el SQL sumando textos,
así se evita la inyección SQL.
"""
from .conexion import ConexionBD, consultar

COLUMNAS = "id_cliente, ci, nombres, apellidos, telefono, email"


class ClienteRepositorio:

    def buscarPorCi(self, ci):
        filas = consultar(f"SELECT {COLUMNAS} FROM Cliente WHERE ci = ?", ci)
        return filas[0] if filas else None

    def buscar(self, texto, limite=50):
        """Busca por CI o por parte del nombre o apellido."""
        patron = f"%{texto.strip()}%"
        return consultar(f"""
            SELECT TOP (?) {COLUMNAS} FROM Cliente
            WHERE ci LIKE ? OR nombres LIKE ? OR apellidos LIKE ?
            ORDER BY apellidos, nombres
        """, limite, patron, patron, patron)

    def guardar(self, c):
        """Inserta el cliente `c` (diccionario) y devuelve su id.
        El CI duplicado también lo rechaza la BD (UQ_Cliente_ci)."""
        with ConexionBD() as cur:
            cur.execute("""
                INSERT INTO Cliente (ci, nombres, apellidos, telefono, email)
                OUTPUT INSERTED.id_cliente
                VALUES (?, ?, ?, ?, ?)
            """, c["ci"], c["nombres"], c["apellidos"], c["telefono"], c.get("email") or None)
            return cur.fetchone()[0]

    def cantidadEncomiendas(self, idCliente):
        return consultar("""
            SELECT COUNT(*) AS n FROM Encomienda
            WHERE id_remitente = ? OR id_destinatario = ?
        """, idCliente, idCliente)[0]["n"]

    def eliminar(self, idCliente):
        with ConexionBD() as cur:
            cur.execute("DELETE FROM Cliente WHERE id_cliente = ?", idCliente)
