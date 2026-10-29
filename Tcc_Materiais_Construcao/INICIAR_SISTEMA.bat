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
echo.
echo Para a primeira instalacao, abra:
echo sistema\INSTALAR_TUDO.bat
pause
exit /b 1

:executar
"%PYTHON_EXE%" main.py
if errorlevel 1 (
    echo.
    echo O sistema foi encerrado com erro.
    echo Se for a primeira vez neste computador, execute:
    echo sistema\INSTALAR_TUDO.bat
    pause
)
