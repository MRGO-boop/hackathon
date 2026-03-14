@echo off
echo ============================================================
echo CoreInventory API Setup and Launch
echo ============================================================
echo.

echo Step 1: Deactivating current virtual environment...
call deactivate 2>nul

echo Step 2: Creating new virtual environment (venv_new)...
python -m venv venv_new

echo Step 3: Activating new virtual environment...
call venv_new\Scripts\activate.bat

echo Step 4: Installing dependencies...
pip install -r requirements.txt

echo Step 5: Starting the API server...
echo.
python start_api.py
