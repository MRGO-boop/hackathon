@echo off
echo ============================================================
echo CoreInventory - Complete System Startup
echo ============================================================
echo.

echo Step 1: Activating virtual environment...
call venv\Scripts\activate.bat

echo Step 2: Checking database...
if not exist coreinventory.db (
    echo Database not found. Creating tables...
    venv\Scripts\python.exe init_database.py
)

echo.
echo Step 3: Starting API server with frontend...
echo.
echo ============================================================
echo CoreInventory is starting...
echo ============================================================
echo.
echo Frontend: http://localhost:5000
echo API: http://localhost:5000/api
echo Health: http://localhost:5000/health
echo.
echo The browser will open automatically in 3 seconds...
echo Press CTRL+C to stop the server
echo ============================================================
echo.

timeout /t 3 /nobreak >nul
start http://localhost:5000

venv\Scripts\python.exe run_flask.py
