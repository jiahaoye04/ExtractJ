@echo off
rem Lanzador de ExtraerFicheros. Debe estar en la misma carpeta que el .py

set "PYTHONW={your_location}\Python\bin\pythonw.exe"

if exist "%PYTHONW%" (
    start "" "%PYTHONW%" "%~dp0ExtraerFicheros.py"
) else (
    start "" pythonw "%~dp0ExtraerFicheros.py"
)
