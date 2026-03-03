@echo off
chcp 65001 >nul
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo  MR Digital Akquise v2 – http://localhost:5001
echo.
start "" http://localhost:5001
python app.py
pause
