"""Conexión a SQL Server con pyodbc.

Los datos se leen del archivo .env (ver .env.example):
  DB_SERVER=.\\SQLEXPRESS       nombre del servidor que aparece en SSMS
  DB_NAME=LaVelozDB
  DB_CONN=...                  (opcional) cadena completa; si existe, se usa tal cual

El controlador ODBC se elige solo: el más nuevo instalado de la lista PREFERIDOS.
Nunca se escribe una contraseña en el código.
"""
import os
from contextlib import contextmanager

import pyodbc
from dotenv import load_dotenv

load_dotenv()

PREFERIDOS = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]


def elegir_controlador():
    instalados = pyodbc.drivers()
    for d in PREFERIDOS:
        if d in instalados:
            return d
    raise RuntimeError(
        "No se encontró el ODBC Driver 17 o 18 for SQL Server. "
        "Instale 'ODBC Driver 18 for SQL Server' de Microsoft. Controladores encontrados: "
        + (", ".join(instalados) or "ninguno"))


def cadena_conexion():
    if os.getenv("DB_CONN"):
        return os.getenv("DB_CONN")
    servidor = os.getenv("DB_SERVER", r".\SQLEXPRESS")
    base = os.getenv("DB_NAME", "LaVelozDB")
    return (f"DRIVER={{{elegir_controlador()}}};SERVER={servidor};DATABASE={base};"
            "Trusted_Connection=yes;TrustServerCertificate=yes;")


def obtener_conexion():
    return pyodbc.connect(cadena_conexion())


@contextmanager
def transaccion():
    """Abre una conexión, hace commit si todo sale bien y rollback si algo falla.

    Uso (por ejemplo en HU-09, para guardar Encomienda + Seguimiento juntos):
        with transaccion() as cur:
            cur.execute("INSERT ...", ...)
            cur.execute("INSERT ...", ...)
    """
    con = obtener_conexion()
    try:
        cur = con.cursor()
        yield cur
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def consultar(sql, *params):
    """Ejecuta un SELECT y devuelve una lista de diccionarios."""
    with transaccion() as cur:
        cur.execute(sql, *params)
        columnas = [c[0] for c in cur.description]
        return [dict(zip(columnas, fila)) for fila in cur.fetchall()]
