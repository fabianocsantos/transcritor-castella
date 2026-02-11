@echo off
title TRANSCRITOR - Castella Studio
color 0A
cd /d C:\transcritor

cls
echo.
echo ==========================================================
echo             TRANSCRITOR DE VIDEO
echo             Castella Studio  v3.6
echo ==========================================================
echo.
echo  Escolha o tipo de entrada:
echo   1 - LINK (YouTube / Drive / IG / TikTok)
echo   2 - ARQUIVO local
echo.
set /p entrada="Digite 1 ou 2: "

echo.
echo  Escolha o modo:
echo   1 - FAST      (rapido)
echo   2 - ACCURATE  (mais preciso)
echo.
set /p modo="Digite 1 ou 2: "

if "%modo%"=="1" (
    set flag=
) else if "%modo%"=="2" (
    set flag=--accurate
) else (
    echo Opcao invalida.
    pause
    exit
)

call .venv\Scripts\activate

if "%entrada%"=="1" (
    echo.
    set /p link="Cole o link do video: "
    echo.
    python app.py --link "%link%" %flag%
) else if "%entrada%"=="2" (
    echo.
    set /p file="Cole o caminho completo do arquivo: "
    echo.
    python app.py --file "%file%" %flag%
) else (
    echo Opcao invalida.
)

echo.
echo ==========================================================
echo Processo finalizado.
echo ==========================================================
echo.
pause
