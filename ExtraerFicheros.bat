@echo off
rem Lanzador de ExtraerFicheros. Debe estar en la misma carpeta que el .py

set "PYTHONW=C:\Users\alema\AppData\Local\Python\bin\pythonw.exe"

if exist "%PYTHONW%" (
    start "" "%PYTHONW%" "%~dp0ExtraerFicheros.py"
) else (
    start "" pythonw "%~dp0ExtraerFicheros.py"
)
