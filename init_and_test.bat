@echo off
echo Initializing database and testing API...
echo.

call venv\Scripts\activate.bat

echo Step 1: Creating database tables...
python init_database.py

echo.
echo Step 2: Installing requests library...
pip install requests

echo.
echo Step 3: Running API tests...
python test_api_calls.py

pause
