"""Prueba rápida de la conexión (spike de la Fase 1).

Uso:  python probar_conexion.py
"""
import sys

import pyodbc

from app.datos.conexion import cadena_conexion, consultar

print("Controladores ODBC de SQL Server instalados:", [d for d in pyodbc.drivers() if "SQL Server" in d])
try:
    print("Conectando con:", cadena_conexion())
    filas = consultar("""
        SELECT t.name AS tabla, SUM(p.rows) AS filas
        FROM sys.tables t JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
        GROUP BY t.name ORDER BY t.name
    """)
except Exception as e:
    print("\nNO se pudo conectar:\n ", e)
    print("\nRevise DB_SERVER en el archivo .env y que exista la base LaVelozDB en SSMS.")
    sys.exit(1)
print("\nConexión correcta. Tablas de LaVelozDB:")
for f in filas:
    print(f"  {f['tabla']:<20} {f['filas']} filas")
