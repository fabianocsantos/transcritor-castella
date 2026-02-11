@echo off
chcp 65001 >nul
setlocal

set PROJECT=C:\transcritor
set PY=%PROJECT%\.venv\Scripts\python.exe

echo.
echo ==========================================
echo   TRANSCRITOR - BACKUP DE RELEASE (v2)
echo ==========================================
echo.

cd /d "%PROJECT%"

if not exist "%PY%" (
  echo ❌ Python da venv não encontrado em:
  echo %PY%
  echo.
  echo Verifique se o transcritor está instalado corretamente.
  pause
  exit /b 1
)

echo ✅ Criando backup versionado...
echo.

"%PY%" tools\release_backup.py

echo.
echo ✅ Backup concluído!
echo 📁 Abrindo pasta releases...
explorer "%PROJECT%\releases"

pause
exit /b 0
