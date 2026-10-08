@echo off
setlocal
cd /d "%~dp0"
title Instalacao - Sistema de Gerenciamento

echo ==============================================================
echo  INSTALACAO COMPLETA - SISTEMA DE GERENCIAMENTO
echo ==============================================================
echo.

set "PYTHON_EXE=C:\Program Files\Python314\python.exe"
if exist "%PYTHON_EXE%" goto python_ok

where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_EXE=python"
    goto python_ok
)

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_EXE=py"
    goto python_ok
)

echo ERRO: Python nao foi encontrado.
echo Instale Python 3.11 ou superior e execute este arquivo novamente.
pause
exit /b 1

:python_ok
echo [1/3] Instalando/atualizando dependencias Python...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto erro

"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 goto erro

echo.
"%PYTHON_EXE%" -m scripts.instalar_tudo
if errorlevel 1 goto erro

echo.
echo ==============================================================
echo  TUDO PRONTO
echo ==============================================================
echo.
echo Para usar o programa daqui para frente, abra:
echo INICIAR_SISTEMA.bat
echo.
pause
exit /b 0

:erro
echo.
echo A instalacao nao foi concluida.
echo Leia a mensagem de erro acima.
pause
exit /b 1
