@echo off
title TRANSCRITOR DE VIDEO - Castella Studio

cd /d C:\transcritor
call .venv\Scripts\activate

cls
echo ==================================================
echo   TRANSCRITOR DE VIDEO
echo   Castella Studio - Faster Engine
echo ==================================================
echo.

echo 1 - LINK (YouTube / Drive / IG / TikTok)
echo 2 - ARQUIVO local (salvar na pasta "entrada")
echo.
set /p tipo=Digite 1 ou 2: 

echo.
echo 1 - FAST
echo 2 - ACCURATE (mais preciso)
echo.
set /p modo=Digite 1 ou 2: 

set ARG_MODO=
if "%modo%"=="2" set ARG_MODO=--accurate

echo.

if "%tipo%"=="1" goto LINK
if "%tipo%"=="2" goto UPLOAD

echo Opcao invalida.
pause
exit

:LINK
set link=
set /p link=Cole o link do video e pressione ENTER: 

if "%link%"=="" (
    echo ERRO: Nenhum link informado.
    pause
    exit
)

echo.
echo Iniciando transcricao...
echo.
python app.py --link "%link%" %ARG_MODO%
goto ABRIR

:UPLOAD
echo.
echo Coloque o video dentro da pasta:
echo C:\transcritor\entrada
echo.

set arquivo=
set /p arquivo=Digite o nome do arquivo (ex: video.mp4): 

if "%arquivo%"=="" (
    echo ERRO: Nenhum arquivo informado.
    pause
    exit
)

echo.
echo Iniciando transcricao...
echo.
python app.py --link "entrada\%arquivo%" %ARG_MODO%
goto ABRIR

:ABRIR
echo.
echo ==========================================
echo Abrindo pasta do ultimo job...
echo ==========================================
echo.

if exist _LAST_JOB_DIR.txt (
    for /f "usebackq delims=" %%i in ("_LAST_JOB_DIR.txt") do (
        start "" "%%i"
    )
) else (
    echo Arquivo _LAST_JOB_DIR.txt nao encontrado.
)

echo.
echo Processo finalizado.
echo.
pause
