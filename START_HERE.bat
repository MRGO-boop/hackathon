@echo off
echo ============================================================
echo CoreInventory - Complete Setup and Start
echo ============================================================
echo.

echo Step 1: Activating virtual environment...
call venv\Scripts\activate.bat

echo Step 2: Creating database tables...
python init_database.py

echo.
echo Step 3: Installing requests library...
pip install requests >nul 2>&1

echo.
echo ============================================================
echo Starting API Server...
echo ============================================================
echo.
echo The server will start in 3 seconds...
echo After it starts, open a NEW terminal and run: test_api_calls.py
echo.
timeout /t 3 /nobreak >nul

python run_flask.py
