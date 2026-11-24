"""Conexión a SQL Server con pyodbc: clase ConexionBD del diseño (capa de datos).

Los datos se leen del archivo .env (ver .env.example):
  DB_SERVER=.\\SQLEXPRESS       nombre del servidor que aparece en SSMS
  DB_NAME=LaVelozDB
  DB_CONN=...                  (opcional) cadena completa; si existe, se usa tal cual

El controlador ODBC se elige solo: el más nuevo instalado de la lista PREFERIDOS.
Nunca se escribe una contraseña en el código.
"""
import os

import pyodbc
from dotenv import load_dotenv

load_dotenv()

PREFERIDOS = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]


def elegirControlador():
    instalados = pyodbc.drivers()
    for d in PREFERIDOS:
        if d in instalados:
            return d
    raise RuntimeError(
        "No se encontró el ODBC Driver 17 o 18 for SQL Server. "
        "Instale 'ODBC Driver 18 for SQL Server' de Microsoft. Controladores encontrados: "
        + (", ".join(instalados) or "ninguno"))


def cadenaConexion():
    if os.getenv("DB_CONN"):
        return os.getenv("DB_CONN")
    servidor = os.getenv("DB_SERVER", r".\SQLEXPRESS")
    base = os.getenv("DB_NAME", "LaVelozDB")
    return (f"DRIVER={{{elegirControlador()}}};SERVER={servidor};DATABASE={base};"
            "Trusted_Connection=yes;TrustServerCertificate=yes;")


class ConexionBD:
    """Maneja UNA transacción: iniciarTransaccion() -> usar el cursor -> confirmar() o revertir().

    Forma corta (confirma si todo sale bien y revierte si hay un error):
        with ConexionBD() as cur:
            cur.execute("INSERT ...", ...)
            cur.execute("INSERT ...", ...)
    """

    def __init__(self):
        self.conexion = None
        self.cursor = None

    def iniciarTransaccion(self):
        self.conexion = pyodbc.connect(cadenaConexion())
        self.cursor = self.conexion.cursor()
        return self.cursor

    def confirmar(self):
        try:
            self.conexion.commit()
        finally:
            self.conexion.close()

    def revertir(self):
        try:
            self.conexion.rollback()
        finally:
            self.conexion.close()

    def __enter__(self):
        return self.iniciarTransaccion()

    def __exit__(self, tipo, error, traza):
        if error is None:
            self.confirmar()
        else:
            self.revertir()
        return False            # el error sigue su camino hasta el controlador


def consultar(sql, *params):
    """Ejecuta un SELECT y devuelve una lista de diccionarios."""
    with ConexionBD() as cur:
        cur.execute(sql, *params)
        columnas = [c[0] for c in cur.description]
        return [dict(zip(columnas, fila)) for fila in cur.fetchall()]
