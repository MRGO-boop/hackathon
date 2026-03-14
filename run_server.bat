@echo off
echo ============================================================
echo CoreInventory API Server
echo ============================================================
echo.

echo Activating correct virtual environment...
call venv\Scripts\activate.bat

echo Starting server...
echo.
venv\Scripts\python.exe run_flask.py
