@echo off
title Build Portatil - Transcritor

cd /d "%~dp0"

echo ==================================================
echo   TRANSCRITOR - BUILD PORTATIL
echo ==================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo ERRO: Ambiente virtual nao encontrado.
    echo Esperado em: .venv\Scripts\activate.bat
    echo.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Fechando Transcritor.exe, se estiver aberto...
echo.

taskkill /IM Transcritor.exe /F >nul 2>nul

timeout /t 2 /nobreak >nul

echo Limpando builds anteriores...
echo.

if exist build (
    rmdir /s /q build
)

if exist dist\Transcritor (
    rmdir /s /q dist\Transcritor
)

if exist Transcritor.spec (
    del /q Transcritor.spec
)

if exist build (
    echo.
    echo ERRO: Nao foi possivel apagar a pasta build.
    echo Feche janelas abertas, reinicie o computador se necessario e tente novamente.
    echo.
    pause
    exit /b 1
)

if exist dist\Transcritor (
    echo.
    echo ERRO: Nao foi possivel apagar a pasta dist\Transcritor.
    echo Feche o Transcritor, feche o Explorer nessa pasta e tente novamente.
    echo.
    pause
    exit /b 1
)

echo.
echo Gerando executavel...
echo.

python -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name Transcritor ^
    --collect-all customtkinter ^
    --collect-all faster_whisper ^
    --collect-all ctranslate2 ^
    --collect-all tokenizers ^
    interface.py

if errorlevel 1 (
    echo.
    echo ERRO: O PyInstaller encontrou um problema.
    echo.
    pause
    exit /b 1
)

echo.
echo Preparando pasta portatil...
echo.

if not exist dist\Transcritor\tools (
    mkdir dist\Transcritor\tools
)

if not exist dist\Transcritor\entrada (
    mkdir dist\Transcritor\entrada
)

if not exist dist\Transcritor\saida (
    mkdir dist\Transcritor\saida
)

if not exist dist\Transcritor\temp (
    mkdir dist\Transcritor\temp
)

if not exist tools\yt-dlp.exe (
    echo.
    echo ERRO: tools\yt-dlp.exe nao encontrado.
    echo.
    pause
    exit /b 1
)

if not exist tools\ffmpeg.exe (
    echo.
    echo ERRO: tools\ffmpeg.exe nao encontrado.
    echo.
    pause
    exit /b 1
)

if not exist tools\ffprobe.exe (
    echo.
    echo ERRO: tools\ffprobe.exe nao encontrado.
    echo.
    pause
    exit /b 1
)

copy /y tools\yt-dlp.exe dist\Transcritor\tools\yt-dlp.exe >nul
copy /y tools\ffmpeg.exe dist\Transcritor\tools\ffmpeg.exe >nul
copy /y tools\ffprobe.exe dist\Transcritor\tools\ffprobe.exe >nul

echo.
echo ==================================================
echo   BUILD FINALIZADO COM SUCESSO
echo ==================================================
echo.
echo Pasta gerada:
echo %cd%\dist\Transcritor
echo.
echo Observacao:
echo O arquivo cookies.txt NAO foi copiado por seguranca.
echo.

start "" "%cd%\dist\Transcritor"

pause