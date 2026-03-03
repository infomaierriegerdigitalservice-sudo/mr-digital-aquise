@echo off
TITLE MR Digital – Öffentliches Dashboard
color 0A
cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║       MR Digital – Akquise Automatisierung v2       ║
echo  ║              Öffentlicher Zugang via ngrok           ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ── Python-Pfad prüfen ──────────────────────────────────────────
if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

REM ── ngrok installieren falls nicht vorhanden ─────────────────────
where ngrok >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [*] ngrok nicht gefunden – lade ngrok herunter...
    powershell -Command "Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile '%TEMP%\ngrok.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\ngrok.zip' -DestinationPath '%~dp0' -Force"
    echo  [OK] ngrok installiert!
    echo.
)

REM ── Flask-App im Hintergrund starten ────────────────────────────
echo  [*] Starte Flask-App auf Port 5001...
start /B "" %PYTHON% app.py

REM ── Kurz warten bis Flask startet ───────────────────────────────
timeout /t 3 /nobreak >nul

REM ── ngrok-Tunnel starten ────────────────────────────────────────
echo  [*] Starte ngrok-Tunnel...
echo.
echo  ┌─────────────────────────────────────────────────────┐
echo  │  Die öffentliche URL wird gleich unten angezeigt!   │
echo  │                                                     │
echo  │  Passwort: MaierRieger.1234                        │
echo  │                                                     │ 
echo  │  WICHTIG: URL ändert sich bei jedem Neustart!      │
echo  │  Fenster NICHT schließen – sonst geht URL offline! │
echo  └─────────────────────────────────────────────────────┘
echo.
echo  Drücke STRG+C um zu beenden.
echo.

ngrok http 5001
pause
