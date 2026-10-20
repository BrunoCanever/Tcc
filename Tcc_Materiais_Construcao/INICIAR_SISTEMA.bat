@echo off
setlocal
cd /d "%~dp0"
title Sistema de Gerenciamento

set "PYTHON_EXE=C:\Program Files\Python314\python.exe"
if exist "%PYTHON_EXE%" goto executar

where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_EXE=python"
    goto executar
)

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_EXE=py"
    goto executar
)

echo Python nao encontrado.
echo Execute INSTALAR_TUDO.bat primeiro.
pause
exit /b 1

:executar
"%PYTHON_EXE%" main.py
if errorlevel 1 (
    echo.
    echo O sistema foi encerrado com erro.
    pause
)
