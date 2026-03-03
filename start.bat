@echo off
chcp 65001 >nul
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   MR Digital – Akquise Automatisierung   ║
echo  ║              v2  Setup & Start            ║
echo  ╚══════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: Python suchen
set PYTHON_CMD=
where python >nul 2>&1 && set PYTHON_CMD=python
if "%PYTHON_CMD%"=="" where python3 >nul 2>&1 && set PYTHON_CMD=python3
if "%PYTHON_CMD%"=="" (
  for %%P in (
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
  ) do (
    if exist %%P ( set PYTHON_CMD=%%P & goto :found_python )
  )
)
:found_python
if "%PYTHON_CMD%"=="" (
  echo FEHLER: Python nicht gefunden!
  echo Bitte installiere Python von https://www.python.org/downloads/
  pause & exit /b 1
)
echo [OK] Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

:: .env erstellen falls nicht vorhanden
if not exist ".env" (
  echo [Info] Erstelle .env aus Vorlage...
  copy ".env.example" ".env" >nul
  echo [OK] .env erstellt – bitte App-Passwort in Einstellungen eintragen!
  echo.
)

:: Datenordner
if not exist "data" mkdir data
if not exist "data\backups" mkdir data\backups

:: Virtual Environment
if not exist "venv\Scripts\activate.bat" (
  echo [1/4] Erstelle Virtual Environment...
  %PYTHON_CMD% -m venv venv
  if errorlevel 1 ( echo FEHLER! & pause & exit /b 1 )
  echo [OK] Virtual Environment erstellt.
  echo.
)

call venv\Scripts\activate.bat

:: Pakete
echo [2/4] Installiere Python-Pakete...
pip install flask apscheduler playwright python-dotenv beautifulsoup4 requests --quiet --disable-pip-version-check
if errorlevel 1 ( echo FEHLER beim Installieren! & pause & exit /b 1 )
echo [OK] Pakete installiert.
echo.

:: Playwright Browser
echo [3/4] Installiere Playwright Browser (Chromium)...
playwright install chromium --quiet 2>nul
echo [OK] Playwright bereit.
echo.

:: Starten
echo [4/4] Starte MR Digital Akquise v2...
echo.
echo  ┌─────────────────────────────────────────┐
echo  │  Dashboard: http://localhost:5001        │
echo  │  Ctrl+C zum Beenden                      │
echo  └─────────────────────────────────────────┘
echo.
echo  WICHTIG: Gmail App-Passwort in Einstellungen eintragen!
echo.
start "" http://localhost:5001
python app.py

pause
