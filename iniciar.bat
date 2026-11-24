@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Currier La Veloz

python -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo.
  echo  No se encontro Python.
  echo  Instalelo desde https://www.python.org/downloads/ y marque "Add python.exe to PATH".
  echo  Luego vuelva a hacer doble clic en este archivo.
  echo.
  pause
  exit /b 1
)

if not exist .venv (
  echo [1/4] Creando el entorno de Python...
  python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [2/4] Instalando dependencias...
python -m pip install -q --disable-pip-version-check -r requirements.txt
if not exist .env copy .env.example .env >nul

echo [3/4] Probando la conexion a SQL Server...
python probar_conexion.py
if errorlevel 1 ( pause & exit /b 1 )

echo [4/4] Ejecutando las pruebas...
python -m pytest -q

echo.
echo  Abriendo el sistema en http://127.0.0.1:5000  (cierre esta ventana para detenerlo)
start "" http://127.0.0.1:5000
python -m flask --app app run
pause
