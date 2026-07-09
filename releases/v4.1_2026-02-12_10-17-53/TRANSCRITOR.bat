@echo off
setlocal enabledelayedexpansion
title TRANSCRITOR - Castella Studio
cd /d C:\transcritor

echo.
echo ==========================================
echo TRANSCRITOR - Castella Studio
echo ==========================================
echo.

echo Escolha o tipo de entrada:
echo  1 - LINK
echo  2 - ARQUIVO local
set /p tipo="Digite 1 ou 2: "

echo.
echo Escolha o modo:
echo  1 - FAST
echo  2 - ACCURATE
set /p modo="Digite 1 ou 2: "

if "!modo!"=="2" (
    set MODEL_FLAG=--accurate
) else (
    set MODEL_FLAG=
)

if "!tipo!"=="1" (
    echo.
    set /p LINK="Cole o link do video: "
    echo.
    echo [DEBUG] Link capturado: !LINK!
    call .venv\Scripts\python.exe app.py --link "!LINK!" !MODEL_FLAG!
) else (
    call .venv\Scripts\python.exe app.py !MODEL_FLAG!
)

echo.
echo ==========================================
echo Abrindo pasta do ultimo job...
echo ==========================================

if exist "_LAST_JOB_DIR.txt" (
    set /p LAST=<"_LAST_JOB_DIR.txt"
    if not "!LAST!"=="" (
        start "" "!LAST!"
    ) else (
        start "" "C:\transcritor\saida"
    )
) else (
    start "" "C:\transcritor\saida"
)

pause
